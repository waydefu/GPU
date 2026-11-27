#!/data/data/com.termux/files/usr/bin/python3
"""Stage 6.3 Candidate 2 bounded, reversible A/B experiment:
  2A: V8 --max-old-space-size (default vs 512 MB) on Electron/Node workstation workload + OOM compatibility probes
  2B: Worker concurrency cap (2x vs 4x parallel Electron+Python workers) on ZRAM/major-fault/PSS/wall impact

Runs natively (TracerPid=0) via termux-bg-run, uses live fast9+09c binary (read-only),
reads /proc/vmstat via ADB -H 127.0.0.1 -P 5038, and mutates zero Android settings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import statistics as st
import subprocess as sp
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stage6_adb as A  # noqa: E402

PREFIX = Path("/data/data/com.termux/files/usr")
TERMUX_HOME = Path("/data/data/com.termux/files/home")
LIVE_PROOT = TERMUX_HOME / "build/proot-fast/out8/bin/proot-fast8"
UBU = PREFIX / "var/lib/proot-distro/containers/ubuntu/rootfs"
SHM = UBU.parent / "shm"
SYSD = UBU.parent / "sysdata"


def check_native() -> None:
    txt = Path("/proc/self/status").read_text()
    if not re.search(r"(?m)^TracerPid:\s+0$", txt):
        raise SystemExit("FAIL: must run natively with TracerPid=0")


def adb_shell(cmd: str, port: int = 5038, serial: str | None = None, timeout: float = 10.0) -> tuple[int, str]:
    return A.run_adb(port, ["shell", cmd], serial=serial, timeout=timeout)


def read_vmstat_adb(port: int = 5038, serial: str | None = None) -> dict[str, int] | None:
    rc, out = adb_shell("grep -E '^(pswpin|pswpout|pgmajfault|allocstall|compact_stall)' /proc/vmstat",
                        port=port, serial=serial)
    if rc != 0:
        return None
    return A.parse_vmstat(out)


def read_psi_adb(port: int = 5038, serial: str | None = None) -> str:
    rc, out = adb_shell("cat /proc/pressure/memory 2>&1 || true", port=port, serial=serial)
    if rc == 0 and "some " in out:
        raise RuntimeError(f"Unexpected readable PSI: {out}")
    return "UNAVAILABLE_DUE_TO_PERMISSION"


def read_zram_mm_stat_adb(port: int = 5038, serial: str | None = None) -> str:
    rc, out = adb_shell("cat /sys/block/zram0/mm_stat 2>&1 || true", port=port, serial=serial)
    if rc == 0 and out.strip() and "Permission denied" not in out:
        raise RuntimeError(f"Unexpected readable zram0/mm_stat: {out}")
    return "UNAVAILABLE_DUE_TO_PERMISSION"


def diff_vmstat(a: dict[str, int] | None, b: dict[str, int] | None) -> dict[str, int | None] | None:
    if not a or not b:
        return None
    return {k: b[k] - a[k] for k in sorted(set(a) & set(b))}


def read_mem_avail_mb() -> float:
    txt = Path("/proc/meminfo").read_text()
    return round(int(re.search(r"MemAvailable:\s+(\d+)", txt).group(1)) / 1024.0, 1)


def sample_tree_kb(root_pid: int) -> tuple[int, int]:
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
    pss_kb = rss_kb = 0
    for pid in seen:
        try:
            sr = Path(f"/proc/{pid}/smaps_rollup").read_text()
            mp = re.search(r"(?m)^Pss:\s+(\d+)", sr)
            mr = re.search(r"(?m)^Rss:\s+(\d+)", sr)
            if mp:
                pss_kb += int(mp.group(1))
            if mr:
                rss_kb += int(mr.group(1))
        except OSError:
            pass
    return pss_kb, rss_kb


def run_proot_guest(wtmp: Path, guest_cmd: list[str], extra_env: dict[str, str] | None = None,
                    timeout: float = 90.0, port: int = 5038, serial: str | None = None) -> dict:
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
        "LC_ALL=C",
    ]
    for k, v in (extra_env or {}).items():
        env_args.append(f"{k}={v}")
    cmd = [
        str(LIVE_PROOT), "-0", "-l", "-r", str(UBU), "-w", "/",
        "-b", "/proc", "-b", "/dev", "-b", "/sys",
        "-b", f"{SHM}:/dev/shm",
        "-b", f"{SYSD / 'sysctl_inotify_max_user_watches'}:/proc/sys/fs/inotify/max_user_watches",
        "-b", f"{wtmp}:/tmp",
        *env_args, *guest_cmd,
    ]
    out_p = wtmp / "run.out"
    err_p = wtmp / "run.err"
    av0 = read_mem_avail_mb()
    box = {"peak_pss_kb": 0, "peak_rss_kb": 0, "min_avail_mb": av0}
    stop_evt = threading.Event()

    def mon(pid: int) -> None:
        while not stop_evt.is_set():
            pss, rss = sample_tree_kb(pid)
            box["peak_pss_kb"] = max(box["peak_pss_kb"], pss)
            box["peak_rss_kb"] = max(box["peak_rss_kb"], rss)
            box["min_avail_mb"] = min(box["min_avail_mb"], read_mem_avail_mb())
            stop_evt.wait(0.25)

    vm0 = read_vmstat_adb(port=port, serial=serial)
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
    vm1 = read_vmstat_adb(port=port, serial=serial)
    vmd = diff_vmstat(vm0, vm1)
    return {
        "rc": rc,
        "wall_ms": wall_ms,
        "peak_pss_mb": round(box["peak_pss_kb"] / 1024.0, 1),
        "peak_rss_mb": round(box["peak_rss_kb"] / 1024.0, 1),
        "mem_avail_min_mb": box["min_avail_mb"],
        "pgmajfault_delta": vmd["pgmajfault"] if vmd else None,
        "pswpin_delta": vmd["pswpin"] if vmd else None,
        "pswpout_delta": vmd["pswpout"] if vmd else None,
        "psi": None,
        "stdout_tail": out_p.read_text(errors="replace").strip()[-300:],
        "stderr_tail": err_p.read_text(errors="replace").strip()[-300:],
    }


def write_scripts(wtmp: Path) -> None:
    for d in (wtmp, wtmp / "home", wtmp / "xdg_cfg", wtmp / "xdg_cache", wtmp / "xdg_run"):
        d.mkdir(parents=True, exist_ok=True)
    os.chmod(wtmp / "xdg_run", 0o700)

    # Realistic Electron/Node worker: V8 heap churn + live retention up to targetMb, plus repo tree walk
    (wtmp / "js_worker.js").write_text(r'''
const fs = require("fs"), path = require("path"), v8 = require("v8");
const targetMb = Number(process.argv[2] || "180");
// Short-lived allocation churn (~120 MB) to exercise GC under different heap limits
for (let r = 0; r < 6; r++) {
  const tmp = [];
  for (let i = 0; i < 40; i++) tmp.push(new Array(65536).fill(r + i));
}
// Retain live V8 heap up to targetMb
const bufs = [];
while (v8.getHeapStatistics().used_heap_size < targetMb * 1048576) {
  const arr = new Array(65536).fill(1);
  arr[0] = bufs.length;
  bufs.push(arr);
}
let files = 0, bytes = 0;
function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const f = path.join(d, e.name);
    if (e.isDirectory()) { if (e.name !== ".git") walk(f); }
    else { bytes += fs.statSync(f).size; files++; }
  }
}
for (let k = 0; k < 3; k++) walk("/root/projects/GPU加速/src/f8-proot-fast");
const hs = v8.getHeapStatistics();
console.log(JSON.stringify({
  files, bytes, retained: bufs.length,
  heap_limit_mb: Math.round(hs.heap_size_limit / 1048576),
  used_heap_mb: Math.round(hs.used_heap_size / 1048576),
}));
''')

    (wtmp / "multi_worker.py").write_text(r'''
import os, subprocess as sp, sys
waves = int(sys.argv[1])
n_elec = int(sys.argv[2])
n_py = int(sys.argv[3])
hold_mb = sys.argv[4]
e_env = dict(os.environ, ELECTRON_RUN_AS_NODE="1")
py_code = (
    "import hashlib,pathlib;"
    "files=sorted(pathlib.Path('/root/projects/GPU加速/evidence/session/proot').glob('*.md'));"
    "h=hashlib.sha256();[h.update(f.read_bytes()) for _ in range(4) for f in files];"
    "print('PY',len(files),h.hexdigest()[:10])"
)
for _ in range(waves):
    procs = [sp.Popen(["/opt/antigravity-hub/antigravity", "/tmp/js_worker.js", hold_mb],
                      env=e_env, stdout=sp.PIPE, stderr=sp.PIPE, text=True) for _ in range(n_elec)]
    procs += [sp.Popen(["/usr/bin/python3", "-c", py_code], stdout=sp.PIPE, stderr=sp.PIPE, text=True) for _ in range(n_py)]
    for p in procs:
        out, err = p.communicate(timeout=60)
        assert p.returncode == 0, f"worker rc={p.returncode} out={out} err={err}"
print("MULTI_OK", waves, n_elec, n_py)
''')


def summarize(rows: list[dict]) -> dict:
    return {
        "n": len(rows),
        "rc_ok": sum(1 for r in rows if r["rc"] == 0),
        "wall_ms_median": round(st.median(r["wall_ms"] for r in rows), 2),
        "peak_pss_mb_median": round(st.median(r["peak_pss_mb"] for r in rows), 1),
        "peak_rss_mb_median": round(st.median(r["peak_rss_mb"] for r in rows), 1),
        "mem_avail_min_mb": min(r["mem_avail_min_mb"] for r in rows),
        "pgmajfault_median": round(st.median(r["pgmajfault_delta"] for r in rows if r["pgmajfault_delta"] is not None), 1),
        "pswpin_median": round(st.median(r["pswpin_delta"] for r in rows if r["pswpin_delta"] is not None), 1),
        "pswpout_median": round(st.median(r["pswpout_delta"] for r in rows if r["pswpout_delta"] is not None), 1),
        "psi": None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stage 6.3 Candidate 2 controlled benchmark")
    ap.add_argument("--adb-port", type=int, default=5038)
    args = ap.parse_args(argv)
    port = args.adb_port

    check_native()
    serial = A.detect_myron_serial(port)
    device_identity = A.verify_device_identity(port, serial)
    proot_sha = hashlib.sha256(LIVE_PROOT.read_bytes()).hexdigest()
    psi_status = read_psi_adb(port=port, serial=serial)
    zram_mm_stat_status = read_zram_mm_stat_adb(port=port, serial=serial)

    out_dir = TERMUX_HOME / "build/proot-fast/stage6_3_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    wtmp = TERMUX_HOME / "build/proot-fast/stage6_3_tmp" / f"c2_{int(time.time())}"
    write_scripts(wtmp)

    try:
        # Warmup
        run_proot_guest(wtmp, ["/usr/bin/python3", "/tmp/multi_worker.py", "1", "2", "2", "180"],
                        port=port, serial=serial)

        # 2A: ABBA (default 4192 MB vs NODE_OPTIONS=--max-old-space-size=512), 2x Electron + 2x Python, 3 cycles = 6 pairs
        exp_2a = {"default": [], "cap_512": []}
        for c in range(3):
            for seq in (("default", "cap_512"), ("cap_512", "default")):
                for arm in seq:
                    env = {} if arm == "default" else {"NODE_OPTIONS": "--max-old-space-size=512"}
                    r = run_proot_guest(wtmp, ["/usr/bin/python3", "/tmp/multi_worker.py", "1", "2", "2", "200"],
                                        extra_env=env, port=port, serial=serial)
                    assert r["rc"] == 0, (arm, r)
                    exp_2a[arm].append(r)
                    print(f"2A c={c} {arm:7s} wall={r['wall_ms']}ms pss={r['peak_pss_mb']}MB rss={r['peak_rss_mb']}MB maj={r['pgmajfault_delta']}", flush=True)

        # 2A-compat: heavy live JS allocation probe (250 MB vs 650 MB live heap) across cap_512 / cap_1024 / default
        compat = []
        for cap_label, opt in (("cap_512", "--max-old-space-size=512"),
                               ("cap_1024", "--max-old-space-size=1024"),
                               ("default", "")):
            for payload_mb in (250, 650):
                env = {"NODE_OPTIONS": opt} if opt else {}
                r = run_proot_guest(wtmp, ["/usr/bin/node", "/tmp/js_worker.js", str(payload_mb)],
                                    extra_env=env, port=port, serial=serial)
                compat.append({
                    "cap": cap_label, "payload_mb": payload_mb,
                    "rc": r["rc"], "wall_ms": r["wall_ms"],
                    "peak_pss_mb": r["peak_pss_mb"], "pgmajfault": r["pgmajfault_delta"],
                    "oom_hit": "out of memory" in r["stderr_tail"].lower(),
                })
                print(f"COMPAT {cap_label:8s} payload={payload_mb}MB rc={r['rc']} pss={r['peak_pss_mb']}MB oom={'out of memory' in r['stderr_tail'].lower()}", flush=True)

        # 2B: Work-normalized concurrency cap ABBA (2 waves of 2+2 vs 1 wave of 4+4), 3 cycles = 6 pairs
        exp_2b = {"seq_2x2": [], "par_4x4": []}
        for c in range(3):
            for seq in (("par_4x4", "seq_2x2"), ("seq_2x2", "par_4x4")):
                for arm in seq:
                    w_args = ("2", "2", "2", "200") if arm == "seq_2x2" else ("1", "4", "4", "200")
                    r = run_proot_guest(wtmp, ["/usr/bin/python3", "/tmp/multi_worker.py", *w_args],
                                        port=port, serial=serial)
                    assert r["rc"] == 0, (arm, r)
                    exp_2b[arm].append(r)
                    print(f"2B c={c} {arm:7s} wall={r['wall_ms']}ms pss={r['peak_pss_mb']}MB rss={r['peak_rss_mb']}MB maj={r['pgmajfault_delta']} av_min={r['mem_avail_min_mb']}MB", flush=True)

        report = {
            "device_identity": device_identity,
            "proot_sha256": proot_sha,
            "psi_status": psi_status,
            "zram_mm_stat_status": zram_mm_stat_status,
            "2A_v8_cap": {
                "summary": {k: summarize(v) for k, v in exp_2a.items()},
                "runs": exp_2a,
            },
            "2A_compat_probe": compat,
            "2B_concurrency_cap": {
                "summary": {k: summarize(v) for k, v in exp_2b.items()},
                "runs": exp_2b,
            },
        }
        out_p = out_dir / "candidate2_result.json"
        out_p.write_text(json.dumps(report, indent=2) + "\n")
        print("C2_DONE", out_p, flush=True)
        print("SUMMARY_2A:", json.dumps(report["2A_v8_cap"]["summary"]), flush=True)
        print("SUMMARY_2B:", json.dumps(report["2B_concurrency_cap"]["summary"]), flush=True)
        return 0
    finally:
        shutil.rmtree(wtmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
