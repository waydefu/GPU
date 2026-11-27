#!/data/data/com.termux/files/usr/bin/python3
"""Stage 6.2 Power Mode Controlled Benchmark Runner (STAGE6-2-POWER-MODE-FREEZE-20261127.md).

Runs natively (TracerPid=0) using the live fast9+09c binary (/build/proot-fast/out8/bin/proot-fast8).
Never mutates Android settings (read-only ADB via -H 127.0.0.1 -P 5038) and never logs private IPs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess as sp
import sys
import threading
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stage6_2_judge as J  # noqa: E402
import stage6_adb as A  # noqa: E402

PREFIX = Path("/data/data/com.termux/files/usr")
TERMUX_HOME = Path("/data/data/com.termux/files/home")
LIVE_PROOT = TERMUX_HOME / "build/proot-fast/out8/bin/proot-fast8"
UBU = PREFIX / "var/lib/proot-distro/containers/ubuntu/rootfs"
SHM = UBU.parent / "shm"
SYSD = UBU.parent / "sysdata"
CLK_TCK = os.sysconf("SC_CLK_TCK")


def check_native_tracer0() -> None:
    st_txt = Path("/proc/self/status").read_text()
    if not re.search(r"(?m)^TracerPid:\s+0$", st_txt):
        raise SystemExit("FAIL: must run natively with TracerPid=0 (use termux-bg-run)")


adb_env = A.adb_env
run_adb = A.run_adb
detect_myron_serial = A.detect_myron_serial
verify_device_identity = A.verify_device_identity


def read_local_thermal() -> tuple[float | None, dict[str, float]]:
    zones: dict[str, float] = {}
    cpu_vals: list[float] = []
    for tz in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        try:
            tname = (tz / "type").read_text().strip()
            if "hw-trip" in tname:
                continue
            raw = int((tz / "temp").read_text().strip())
            if raw == -273000:
                continue
            c = round(raw / 1000.0, 2)
            if any(k in tname.lower() for k in ("cpu", "gpu", "ddr", "battery", "quiet_therm", "display_therm")):
                zones[tname] = c
            if tname.startswith("cpu-"):
                cpu_vals.append(c)
        except (OSError, ValueError):
            continue
    return (round(max(cpu_vals), 2) if cpu_vals else None), zones


def read_local_cpufreq_khz() -> tuple[dict[str, int], dict[str, int]]:
    cur: dict[str, int] = {}
    mx: dict[str, int] = {}
    for c in range(8):
        base = Path(f"/sys/devices/system/cpu/cpu{c}/cpufreq")
        try:
            cur[f"cpu{c}"] = int((base / "scaling_cur_freq").read_text().strip())
            mx[f"cpu{c}"] = int((base / "scaling_max_freq").read_text().strip())
        except (OSError, ValueError):
            continue
    return cur, mx


def read_local_meminfo_mb() -> tuple[float | None, float | None]:
    try:
        txt = Path("/proc/meminfo").read_text()
        av = int(re.search(r"MemAvailable:\s+(\d+)", txt).group(1)) / 1024.0
        st_kb = int(re.search(r"SwapTotal:\s+(\d+)", txt).group(1))
        sf_kb = int(re.search(r"SwapFree:\s+(\d+)", txt).group(1))
        return round(av, 1), round((st_kb - sf_kb) / 1024.0, 1)
    except (OSError, AttributeError, ValueError):
        return None, None


def _parse_int_or_none(s: str) -> int | None:
    s = s.strip()
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return None


parse_zram_line = A.parse_zram_line
parse_vmstat = A.parse_vmstat


def parse_battery_fields(out: str) -> dict[str, int | float | None]:
    """Parse dumpsys battery output with line-anchored regexes (avoids Max charging voltage: 0)."""
    m_cc = re.search(r"(?m)^\s*Charge counter:\s*(-?\d+)", out)
    m_st = re.search(r"(?m)^\s*status:\s*(\d+)", out)
    m_lv = re.search(r"(?m)^\s*level:\s*(\d+)", out)
    m_vt = re.search(r"(?m)^\s*voltage:\s*(\d+)", out)
    m_tp = re.search(r"(?m)^\s*temperature:\s*(-?\d+)", out)
    return {
        "charge_counter_uah": int(m_cc.group(1)) if m_cc else None,
        "battery_status": int(m_st.group(1)) if m_st else None,
        "battery_level": int(m_lv.group(1)) if m_lv else None,
        "battery_voltage_mv": int(m_vt.group(1)) if m_vt else None,
        "battery_temp_c": round(int(m_tp.group(1)) / 10.0, 1) if m_tp else None,
    }


def collect_sample(port: int, serial: str, t_s: float | None = None,
                   include_heavy: bool = False) -> dict[str, Any]:
    cpu_real_max_c, thermal_zones = read_local_thermal()
    cur_khz, max_khz = read_local_cpufreq_khz()
    mem_avail_mb, swap_used_mb = read_local_meminfo_mb()

    script = (
        "echo __LP__ $(settings get global low_power 2>/dev/null); "
        "echo __PPM__ $(settings get system POWER_PERFORMANCE_MODE_OPEN 2>/dev/null); "
        "echo __SPD__ $(settings get system speed_mode 2>/dev/null); "
        "echo __WAKE__ $(dumpsys power 2>/dev/null | grep mWakefulness= | head -n 1); "
        "echo __TH__ $(dumpsys thermalservice 2>/dev/null | grep 'Thermal Status:' | head -n 1); "
        "dumpsys battery 2>/dev/null | grep -E 'Charge counter:|status:|level:|voltage:|temperature:'"
    )
    if include_heavy:
        script += (
            "; echo __VMSTAT__; grep -E '^(pswpin|pswpout|pgmajfault|allocstall|compact_stall)' /proc/vmstat 2>/dev/null; "
            "echo __ZRAM__; dumpsys meminfo 2>/dev/null | grep -i 'ZRAM:' | head -n 2; "
            "echo __EVENTS__; logcat -d -b events 2>/dev/null | grep -E 'am_kill|lmk'"
        )
    rc, out = run_adb(port, ["shell", script], serial=serial, timeout=15.0 if include_heavy else 8.0)
    adb_ok = rc == 0

    power_flags: dict[str, int | None] | None = None
    wakefulness: str | None = None
    thermal_status: int | None = None
    bat: dict[str, int | float | None] = {
        "charge_counter_uah": None, "battery_status": None,
        "battery_level": None, "battery_voltage_mv": None, "battery_temp_c": None,
    }
    vmstat: dict[str, int] | None = None
    zram: dict[str, int] | None = None
    event_lines: list[str] = []

    if adb_ok:
        lp = re.search(r"__LP__\s+(\S+)", out)
        ppm = re.search(r"__PPM__\s+(\S+)", out)
        spd = re.search(r"__SPD__\s+(\S+)", out)
        power_flags = {
            "low_power": _parse_int_or_none(lp.group(1)) if lp else None,
            "POWER_PERFORMANCE_MODE_OPEN": _parse_int_or_none(ppm.group(1)) if ppm else None,
            "speed_mode": _parse_int_or_none(spd.group(1)) if spd else None,
        }
        wk = re.search(r"mWakefulness=(\S+)", out)
        wakefulness = wk.group(1) if wk else None
        th = re.search(r"Thermal Status:\s*(\d+)", out)
        thermal_status = int(th.group(1)) if th else None
        bat = parse_battery_fields(out)

        if include_heavy:
            m_vm = re.search(r"__VMSTAT__\n(.*?)\n__ZRAM__", out, re.S)
            m_zr = re.search(r"__ZRAM__\n(.*?)\n__EVENTS__", out, re.S)
            m_ev = re.search(r"__EVENTS__\n(.*)\Z", out, re.S)
            if m_vm:
                vmstat = parse_vmstat(m_vm.group(1))
            if m_zr:
                zram = parse_zram_line(m_zr.group(1))
            if m_ev:
                event_lines = [ln for ln in m_ev.group(1).splitlines() if ln.strip()]

    data: dict[str, Any] = {
        "adb_ok": adb_ok,
        "power_flags": power_flags,
        "scaling_max_freq_khz": max_khz,
        "scaling_cur_freq_khz": cur_khz,
        "cpu_real_max_c": cpu_real_max_c,
        "thermal_zones_c": thermal_zones,
        "battery_status": bat["battery_status"],
        "battery_level": bat["battery_level"],
        "battery_temp_c": bat["battery_temp_c"],
        "battery_voltage_mv": bat["battery_voltage_mv"],
        "charge_counter_uah": bat["charge_counter_uah"],
        "wakefulness": wakefulness,
        "thermal_status": thermal_status,
        "mem_avail_mb": mem_avail_mb,
        "swap_used_mb": swap_used_mb,
    }
    if t_s is not None:
        data["t_s"] = round(t_s, 2)
    if include_heavy:
        data["vmstat"] = vmstat
        data["zram"] = zram
        data["psi"] = None
        data["event_lines"] = event_lines
    return data


def diff_events(before: list[str], after: list[str]) -> tuple[list[str], list[str]]:
    if not after:
        return [], []
    new_lines = after
    if before:
        anchor = before[-1]
        for idx in range(len(after) - 1, -1, -1):
            if after[idx] == anchor:
                new_lines = after[idx + 1:]
                break
    termux_lines = [ln for ln in new_lines if "com.termux" in ln]
    return new_lines, termux_lines


def diff_vmstat(before: dict[str, int] | None, after: dict[str, int] | None) -> dict[str, int | None] | None:
    if not before or not after:
        return None
    keys = sorted(set(before) | set(after))
    return {k: (after[k] - before[k] if k in before and k in after else None) for k in keys}


def write_guest_scripts(wtmp: Path) -> None:
    for d in (wtmp, wtmp / "home", wtmp / "xdg_cfg", wtmp / "xdg_cache", wtmp / "xdg_run"):
        d.mkdir(parents=True, exist_ok=True)
    os.chmod(wtmp / "xdg_run", 0o700)

    (wtmp / "pw_stress.js").write_text(r'''
const http = require("http");
const { chromium } = require("/root/projects/world-unbound/node_modules/playwright");
(async () => {
  const html = `<!doctype html><html><body>
    <canvas id="c" width="640" height="360"></canvas>
    <button id="btn">Click</button><span id="cnt">0</span>
    <script>
      const ctx = document.getElementById("c").getContext("2d");
      let clicks = 0;
      document.getElementById("btn").addEventListener("click", () => {
        clicks++;
        document.getElementById("cnt").textContent = String(clicks);
      });
      window.runRaf = function(nFrames) {
        return new Promise(resolve => {
          const ts = [];
          let i = 0;
          function step(now) {
            ts.push(now);
            ctx.fillStyle = "rgb(" + (i % 255) + ",110,190)";
            ctx.fillRect((i * 11) % 600, (i * 7) % 320, 40, 40);
            i++;
            if (i <= nFrames) requestAnimationFrame(step);
            else resolve(ts);
          }
          requestAnimationFrame(step);
        });
      };
    </script></body></html>`;
  const srv = http.createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(html);
  });
  await new Promise(r => srv.listen(0, "127.0.0.1", r));
  const url = "http://127.0.0.1:" + srv.address().port + "/";
  const tLaunch = performance.now();
  const browser = await chromium.launch({
    headless: true,
    ignoreDefaultArgs: ["--enable-unsafe-swiftshader"],
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-software-rasterizer", "--disable-gpu-compositing"],
  });
  const launchMs = performance.now() - tLaunch;
  const ctx = await browser.newContext();
  const pageMs = [];
  const allDeltas = [];
  const clickRtts = [];
  await Promise.all([0, 1, 2].map(async () => {
    const p0 = performance.now();
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: "load" });
    pageMs.push(performance.now() - p0);
    const ts = await page.evaluate(() => window.runRaf(60));
    for (let i = 1; i < ts.length; i++) allDeltas.push(ts[i] - ts[i - 1]);
    for (let k = 0; k < 5; k++) {
      const c0 = performance.now();
      await page.click("#btn");
      clickRtts.push(performance.now() - c0);
    }
    const cnt = await page.textContent("#cnt");
    if (cnt !== "5") throw new Error("click mismatch " + cnt);
    await page.close();
  }));
  await ctx.close();
  await browser.close();
  srv.close();
  allDeltas.sort((a, b) => a - b);
  clickRtts.sort((a, b) => a - b);
  const pct = (a, q) => Math.round(a[Math.min(a.length - 1, Math.floor((a.length - 1) * q))] * 100) / 100;
  const drop20 = allDeltas.filter(x => x > 20.0).length;
  const drop33 = allDeltas.filter(x => x > 33.33).length;
  console.log("PW_STRESS " + JSON.stringify({
    launch_ms: Math.round(launchMs * 100) / 100,
    page_p50_ms: pct(pageMs.slice().sort((a,b)=>a-b), 0.5),
    raf_frames: allDeltas.length,
    raf_p50_ms: pct(allDeltas, 0.5),
    raf_p95_ms: pct(allDeltas, 0.95),
    raf_p99_ms: pct(allDeltas, 0.99),
    drop_gt20ms: drop20,
    drop_gt33ms: drop33,
    click_p50_ms: pct(clickRtts, 0.5),
    click_p95_ms: pct(clickRtts, 0.95),
  }));
})().catch(e => { console.error("PW_STRESS_ERR", String(e)); process.exit(1); });
''')

    (wtmp / "workstation_batch.py").write_text(r'''
import json, os, re, subprocess as sp, time

t0 = time.perf_counter_ns()
electron_js = (
    'const fs=require("fs"),p=require("path");'
    'let n=0,b=0;'
    'function walk(d){for(const e of fs.readdirSync(d,{withFileTypes:true})){'
    'const f=p.join(d,e.name);if(e.isDirectory()){if(e.name!==".git")walk(f);}'
    'else{const s=fs.statSync(f);n++;b+=s.size;}}}'
    'for(let k=0;k<3;k++)walk("/root/projects/GPU加速/src/f8-proot-fast");'
    'console.log(JSON.stringify({e:process.versions.electron,n,b}));'
)
py_code = (
    'import hashlib,pathlib;'
    'files=sorted(pathlib.Path("/root/projects/GPU加速/evidence/session/proot").glob("*.md"));'
    'h=hashlib.sha256();'
    '[h.update(f.read_bytes()) for _ in range(4) for f in files];'
    'print("PY_OK",len(files),h.hexdigest()[:12])'
)
git_sh = 'i=0; while [ $i -lt 10 ]; do git -C /root/projects/GPU加速/src/f8-proot-fast status --short >/dev/null && git -C /root/projects/GPU加速/src/f8-proot-fast log -n 10 --oneline >/dev/null; i=$((i+1)); done; echo GIT_OK'

e_env = dict(os.environ, ELECTRON_RUN_AS_NODE="1")
pw_env = dict(os.environ, LD_PRELOAD="/root/build/electron-probe/nopci/libnopci.so")

procs = [
    ("playwright", sp.Popen(["/usr/bin/node", "/tmp/pw_stress.js"], env=pw_env, stdout=sp.PIPE, stderr=sp.PIPE, text=True)),
    ("electron_1", sp.Popen(["/opt/antigravity-hub/antigravity", "-e", electron_js], env=e_env, stdout=sp.PIPE, stderr=sp.PIPE, text=True)),
    ("electron_2", sp.Popen(["/opt/antigravity-hub/antigravity", "-e", electron_js], env=e_env, stdout=sp.PIPE, stderr=sp.PIPE, text=True)),
    ("py_1", sp.Popen(["/usr/bin/python3", "-c", py_code], stdout=sp.PIPE, stderr=sp.PIPE, text=True)),
    ("py_2", sp.Popen(["/usr/bin/python3", "-c", py_code], stdout=sp.PIPE, stderr=sp.PIPE, text=True)),
    ("git_1", sp.Popen(["/bin/sh", "-c", git_sh], stdout=sp.PIPE, stderr=sp.PIPE, text=True)),
    ("git_2", sp.Popen(["/bin/sh", "-c", git_sh], stdout=sp.PIPE, stderr=sp.PIPE, text=True)),
]

pw_data = None
for kind, p in procs:
    out, err = p.communicate(timeout=120)
    assert p.returncode == 0, f"{kind} rc={p.returncode} out={out} err={err}"
    if kind == "playwright":
        m = re.search(r"PW_STRESS (\{.*\})", out)
        assert m, out
        pw_data = json.loads(m.group(1))
tot_ms = round((time.perf_counter_ns() - t0) / 1e6, 2)
print("BATCH_RESULT", json.dumps({"inner_total_ms": tot_ms, "pw": pw_data}))
''')


def sample_tree_pss_kb(root_pid: int) -> int:
    children: dict[int, list[int]] = {}
    tracer_pids: list[int] = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        pid = int(p.name)
        try:
            st_txt = (p / "stat").read_text()
            ppid = int(st_txt[st_txt.rfind(")") + 2:].split()[1])
            children.setdefault(ppid, []).append(pid)
            status = (p / "status").read_text()
            m = re.search(r"(?m)^TracerPid:\s+(\d+)", status)
            if m and int(m.group(1)) == root_pid:
                tracer_pids.append(pid)
        except OSError:
            continue
    seen = {root_pid, *tracer_pids}
    stack = list(seen)
    while stack:
        cur = stack.pop()
        for ch in children.get(cur, ()):
            if ch not in seen:
                seen.add(ch)
                stack.append(ch)
    pss_kb = 0
    for pid in seen:
        try:
            sr = Path(f"/proc/{pid}/smaps_rollup").read_text()
            mp = re.search(r"(?m)^Pss:\s+(\d+)", sr)
            if mp:
                pss_kb += int(mp.group(1))
        except OSError:
            pass
    return pss_kb


def read_tracer_cpu_ms(pid: int) -> float | None:
    try:
        st_txt = Path(f"/proc/{pid}/stat").read_text()
        fields = st_txt[st_txt.rfind(")") + 2:].split()
        return (int(fields[11]) + int(fields[12])) * 1000.0 / CLK_TCK
    except OSError:
        return None


def count_orphans(root_pid: int) -> int:
    orph = 0
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            status = (p / "status").read_text()
            m = re.search(r"(?m)^TracerPid:\s+(\d+)", status)
            if m and int(m.group(1)) == root_pid:
                orph += 1
        except OSError:
            continue
    return orph


def run_single_batch(wtmp: Path, start_offset_s: float, timeout: float = 120.0) -> dict[str, Any]:
    host_env = {
        "PATH": f"{PREFIX}/bin:/system/bin",
        "HOME": str(wtmp), "TMPDIR": str(wtmp),
        "PREFIX": str(PREFIX), "LC_ALL": "C",
    }
    env_args = [
        "/usr/bin/env", "-i",
        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME=/tmp/home", "TMPDIR=/tmp",
        "XDG_CONFIG_HOME=/tmp/xdg_cfg", "XDG_CACHE_HOME=/tmp/xdg_cache", "XDG_RUNTIME_DIR=/tmp/xdg_run",
        "PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright",
        "NODE_PATH=/root/projects/world-unbound/node_modules",
        "GIT_OPTIONAL_LOCKS=0", "LC_ALL=C",
    ]
    cmd = [
        str(LIVE_PROOT), "-0", "-l", "-r", str(UBU), "-w", "/",
        "-b", "/proc", "-b", "/dev", "-b", "/sys",
        "-b", f"{SHM}:/dev/shm",
        "-b", f"{SYSD / 'sysctl_inotify_max_user_watches'}:/proc/sys/fs/inotify/max_user_watches",
        "-b", f"{wtmp}:/tmp",
        *env_args, "/usr/bin/python3", "/tmp/workstation_batch.py",
    ]
    out_p = wtmp / "batch.out"
    err_p = wtmp / "batch.err"
    stop_evt = threading.Event()
    box: dict[str, Any] = {"peak_pss_kb": 0, "tr_cpu_ms": None}

    def mon(pid: int) -> None:
        while not stop_evt.is_set():
            box["peak_pss_kb"] = max(box["peak_pss_kb"], sample_tree_pss_kb(pid))
            cpu = read_tracer_cpu_ms(pid)
            if cpu is not None:
                box["tr_cpu_ms"] = cpu
            stop_evt.wait(0.4)

    t0 = time.perf_counter_ns()
    with out_p.open("w") as fo, err_p.open("w") as fe:
        proc = sp.Popen(cmd, env=host_env, stdin=sp.DEVNULL, stdout=fo, stderr=fe)
        mt = threading.Thread(target=mon, args=(proc.pid,), daemon=True)
        mt.start()
        try:
            rc = proc.wait(timeout=timeout)
        except sp.TimeoutExpired:
            proc.kill()
            proc.wait()
            rc = -999
        finally:
            stop_evt.set()
            mt.join(timeout=3)
    wall_ms = round((time.perf_counter_ns() - t0) / 1e6, 2)
    time.sleep(0.1)
    orph = count_orphans(proc.pid)

    out = out_p.read_text(errors="replace").strip()
    m = re.search(r"BATCH_RESULT (\{.*\})", out)
    batch = json.loads(m.group(1)) if m else {}
    pw = batch.get("pw") or {}
    return {
        "start_offset_s": round(start_offset_s, 3),
        "rc": rc,
        "orphan_pids": orph,
        "wall_ms": wall_ms,
        "inner_total_ms": batch.get("inner_total_ms"),
        "tracer_cpu_ms": round(box["tr_cpu_ms"], 1) if box["tr_cpu_ms"] is not None else None,
        "launch_ms": pw.get("launch_ms"),
        "click_p50_ms": pw.get("click_p50_ms"),
        "click_p95_ms": pw.get("click_p95_ms"),
        "raf_p50_ms": pw.get("raf_p50_ms"),
        "raf_p95_ms": pw.get("raf_p95_ms"),
        "raf_p99_ms": pw.get("raf_p99_ms"),
        "drop_gt20ms": pw.get("drop_gt20ms"),
        "drop_gt33ms": pw.get("drop_gt33ms"),
        "peak_pss_mb": round(box["peak_pss_kb"] / 1024.0, 1),
    }


def wait_for_start_conditions(port: int, serial: str, mode: str, wait_cool: bool,
                              cool_timeout: float = 900.0, skip_temp_check: bool = False) -> dict[str, Any]:
    deadline = time.monotonic() + (cool_timeout if wait_cool else 0.0)
    while True:
        pre = collect_sample(port, serial, include_heavy=True)
        errs: list[str] = []
        J._check_flags(pre.get("power_flags"), mode, "precheck", errs)
        J._check_freqs(pre.get("scaling_max_freq_khz"), mode, "precheck", errs)
        if not skip_temp_check:
            ct = pre.get("cpu_real_max_c")
            bt = pre.get("battery_temp_c")
            if ct is None or ct > 55.0:
                errs.append(f"cpu_real_max_c={ct} > 55.0")
            if bt is None or bt > 36.0:
                errs.append(f"battery_temp_c={bt} > 36.0")
        if pre.get("battery_status") != 3:
            errs.append(f"battery_status={pre.get('battery_status')} != 3")
        lvl = pre.get("battery_level")
        if lvl is None or lvl < 40 or lvl > 90:
            errs.append(f"battery_level={lvl} outside [40,90]")
        if pre.get("wakefulness") != "Awake":
            errs.append(f"wakefulness={pre.get('wakefulness')} != Awake")
        if not errs:
            return pre
        if time.monotonic() >= deadline:
            raise SystemExit(f"PRECHECK_TIMEOUT: {'; '.join(errs)}")
        print(f"WAIT_COOL ({int(deadline - time.monotonic())}s left): {'; '.join(errs)}", flush=True)
        time.sleep(30.0)


def run_block(slot: str, attempt: int, duration_s: float, port: int, out_dir: Path,
              wait_cool: bool, is_dryrun: bool, cool_timeout: float = 900.0,
              dryrun_skip_v3: bool = False) -> int:
    check_native_tracer0()
    mode = "balanced" if is_dryrun else J.SLOT_MODES[slot]
    serial = detect_myron_serial(port)
    device_identity = verify_device_identity(port, serial)
    proot_sha = hashlib.sha256(LIVE_PROOT.read_bytes()).hexdigest()

    wtmp = TERMUX_HOME / "build/proot-fast/stage6_2_tmp" / f"{slot}_a{attempt}_{int(time.time())}"
    write_guest_scripts(wtmp)
    out_dir.mkdir(parents=True, exist_ok=True)

    pre = wait_for_start_conditions(port, serial, mode, wait_cool, cool_timeout,
                                    skip_temp_check=(is_dryrun and dryrun_skip_v3))
    pre_events = pre.pop("event_lines", [])
    pre_vmstat = pre.pop("vmstat", None)

    samples: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    stop_evt = threading.Event()
    t0 = time.monotonic()

    def sampler() -> None:
        next_t = 5.0
        while not stop_evt.is_set():
            rem = next_t - (time.monotonic() - t0)
            if rem > 0 and stop_evt.wait(rem):
                break
            now_off = time.monotonic() - t0
            samples.append(collect_sample(port, serial, t_s=now_off, include_heavy=False))
            next_t += 5.0

    st_thread = threading.Thread(target=sampler, daemon=True)
    st_thread.start()
    try:
        while (time.monotonic() - t0) < duration_s:
            off = time.monotonic() - t0
            b = run_single_batch(wtmp, off)
            batches.append(b)
            print(f"BATCH {slot}#a{attempt} idx={len(batches)} t={b['start_offset_s']}s wall={b['wall_ms']}ms rc={b['rc']} orph={b['orphan_pids']}", flush=True)
    finally:
        stop_evt.set()
        st_thread.join(timeout=10)
        shutil.rmtree(wtmp, ignore_errors=True)

    actual_dur = round(time.monotonic() - t0, 2)
    post = collect_sample(port, serial, include_heavy=True)
    post_events = post.pop("event_lines", [])
    post_vmstat = post.pop("vmstat", None)

    new_events, termux_kills = diff_events(pre_events, post_events)
    block_data = {
        "slot": slot,
        "attempt": attempt,
        "mode": mode,
        "is_dryrun": is_dryrun,
        "device_identity": device_identity,
        "proot_sha256": proot_sha,
        "duration_s": actual_dur,
        "pre": pre,
        "post": post,
        "samples": samples,
        "batches": batches,
        "vmstat_delta": diff_vmstat(pre_vmstat, post_vmstat),
        "new_event_lines": new_events,
        "termux_kills": termux_kills,
    }
    verdict = J.validate_block(block_data, is_dryrun=is_dryrun)
    block_data["validation"] = verdict
    out_path = out_dir / f"{slot}_attempt{attempt}.json"
    out_path.write_text(json.dumps(block_data, indent=2, ensure_ascii=False) + "\n")
    tag = "BLOCK_VALID" if verdict["valid"] else "BLOCK_INVALID"
    print(f"{tag} slot={slot} attempt={attempt} dur={actual_dur}s batches={len(batches)} samples={len(samples)} out={out_path}", flush=True)
    if not verdict["valid"]:
        print("WHY:", "; ".join(verdict["why"]), flush=True)
        return 1
    return 0


def resolve_auto_attempt(out_dir: Path, slot: str) -> int:
    a1 = out_dir / f"{slot}_attempt1.json"
    if not a1.exists():
        return 1
    d1 = json.loads(a1.read_text())
    if d1.get("validation", {}).get("valid") is True:
        raise SystemExit(f"FAIL: {slot}_attempt1.json is already VALID (do not re-run valid slots)")
    a2 = out_dir / f"{slot}_attempt2.json"
    if a2.exists():
        raise SystemExit(f"FAIL: {slot}_attempt2.json already exists (max 1 retry per slot)")
    return 2


def judge_out_dir(out_dir: Path) -> int:
    blocks = []
    for slot in J.SCHEDULE:
        for att in (1, 2):
            p = out_dir / f"{slot}_attempt{att}.json"
            if p.exists():
                blocks.append(json.loads(p.read_text()))
    res = J.judge_series({"blocks": blocks})
    (out_dir / "series_verdict.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: res.get(k) for k in ("verdict", "why", "aa_noise", "spread_b", "spread_p",
                                              "red_slowdown", "imp_late_median", "wins_ge_2pct",
                                              "v_gates", "g_gates")}, indent=2, ensure_ascii=False))
    return 1 if res["verdict"] == "INVALID" else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stage 6.2 controlled power-mode benchmark")
    ap.add_argument("--mode", choices=("dryrun", "block", "judge"), required=True)
    ap.add_argument("--slot", default="DRYRUN", help="Schedule slot B1..B4, P1..P4, S1, or DRYRUN")
    ap.add_argument("--attempt", type=int, default=None)
    ap.add_argument("--auto-attempt", action="store_true", help="Pick attempt 1 or 2 automatically, refusing to overwrite valid blocks")
    ap.add_argument("--duration", type=float, default=None, help="Override block duration (default 30s dryrun, 180s block)")
    ap.add_argument("--adb-port", type=int, default=5038)
    ap.add_argument("--out-dir", type=Path, default=TERMUX_HOME / "build/proot-fast/stage6_2_runs")
    ap.add_argument("--wait-cool", action="store_true", help="Wait up to cool-timeout for V1-V5 precheck/cooling")
    ap.add_argument("--cool-timeout", type=float, default=900.0, help="Cooling wait limit in seconds")
    ap.add_argument("--dryrun-skip-v3", action="store_true", help="Allow dryrun to proceed above V3 temperature limits (never allowed for block)")
    args = ap.parse_args(argv)

    if args.mode == "judge":
        return judge_out_dir(args.out_dir)

    is_dryrun = args.mode == "dryrun"
    if not is_dryrun and args.dryrun_skip_v3:
        raise SystemExit("FAIL: --dryrun-skip-v3 is forbidden in --mode block")
    if not is_dryrun and args.slot not in J.SLOT_MODES:
        raise SystemExit(f"Invalid slot {args.slot!r}; expected one of {J.SCHEDULE}")
    attempt = resolve_auto_attempt(args.out_dir, args.slot) if args.auto_attempt else (args.attempt or 1)
    dur = args.duration if args.duration is not None else (30.0 if is_dryrun else 180.0)
    return run_block(args.slot, attempt, dur, args.adb_port, args.out_dir, args.wait_cool, is_dryrun, args.cool_timeout, args.dryrun_skip_v3)


if __name__ == "__main__":
    sys.exit(main())
