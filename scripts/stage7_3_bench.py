#!/usr/bin/env python3
"""Stage 7.3 controlled ABBA workstation benchmark for Native Hybrid 2.0 MCP.

Compares:
- Arm A1 (PRoot_Resident_MCP): persistent PRoot fast9+09c python3 + f8_hybrid2_relay (F8_NO_HYBRID=1)
- Arm B  (Native_Hybrid2):     persistent Termux Native Daemon (TracerPid == 0) + PRoot thin relay (--no-fallback)
- Arm A2 (PRoot_PerCall_CLI):  one-shot per-call subprocesses inside PRoot fast9+09c (separates residency vs ptrace)

Also measures:
- 4-client concurrent mixed throughput (4x PRoot Fallback vs 4x PRoot Relay -> 1 Shared Native Daemon)
- Cold-start end-to-end latency with `--auto-start` (n=10 keeping 7 Android env vars vs n=5 stripped-7-env fallback)
- Exact output SHA-256 parity across every pair, tracer CPU (schedstat ns + stat ticks), total PSS+SwapPss,
  pgmajfault (ADB -P 5038 vmstat + /proc/<pid>/stat), FD leak checks, and thermal/MemAvailable guardrails.

Must be run natively in Termux (TracerPid == 0), e.g. via termux-bg-run.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
import shutil
import signal
import statistics
import subprocess as sp
import sys
import threading
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
HYB_DIR = Path(os.environ.get("F8_HYBRID2_DIR", str(HERE)))
if str(HYB_DIR) not in sys.path:
    sys.path.insert(0, str(HYB_DIR))

UBU = Path("/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs")
SHM = UBU.parent / "shm"
SYSD = UBU.parent / "sysdata"
PROOT_FAST8 = Path("/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8")
TERMUX_HOME = Path("/data/data/com.termux/files/home")
TERMUX_USR = Path("/data/data/com.termux/files/usr")
CLK_TCK = os.sysconf("SC_CLK_TCK")

PROJ_SCRIPTS = UBU / "root/projects/GPU加速/scripts"
if str(PROJ_SCRIPTS) not in sys.path:
    sys.path.append(str(PROJ_SCRIPTS))

from f8_hybrid2_ctl import AM_REQUIRED_ENV, get_status
from f8_hybrid2_policy import DEFAULT_DAEMON_MAPS, read_tracer_pid
import stage6_adb as s6adb


def wait_for_ready(runtime_dir: Path, timeout_s: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        st = get_status(runtime_dir)
        if st.get("running") and st.get("probe_ok"):
            return True
        time.sleep(0.05)
    return False

RUNTIME_DIR = TERMUX_HOME / ".f8hyb2-b73"
SOCK_PATH = RUNTIME_DIR / "m.sock"
BENCH_WS = TERMUX_HOME / ".f8hyb2_b73_ws"
PROOT_TMP = RUNTIME_DIR / "proot_tmp"
GUEST_HOME = TERMUX_HOME / ".f8hyb2_b73_ghome"
AUTOSTART_DIR = TERMUX_HOME / ".f8hyb2-b73-as"

DAEMON_PY = HYB_DIR / "f8_hybrid2_daemon.py"
RELAY_PY = HYB_DIR / "f8_hybrid2_relay.py"
CTL_PY = HYB_DIR / "f8_hybrid2_ctl.py"

OUT_DIR = UBU / "root/projects/GPU加速/evidence/session/proot/stage7-3-runs-20261127"
OUT_JSON = OUT_DIR / "stage7-3-abba.json"

WS_MAPS = [
    f"{g}={h}" for g, h in DEFAULT_DAEMON_MAPS
] + [f"/bench_ws={BENCH_WS}"]
GUEST_MAPS = ["/root/projects=/root/projects", f"/bench_ws={BENCH_WS}"]


def canonical_digest(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def two_sided_sign_p(wins_b: int, n_pairs: int) -> float:
    if n_pairs <= 0:
        return 1.0
    k = min(wins_b, n_pairs - wins_b)
    cdf = sum(math.comb(n_pairs, i) for i in range(k + 1)) / (2**n_pairs)
    return min(1.0, round(2.0 * cdf, 6))


def percentile(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    if len(s) == 1:
        return round(s[0], 3)
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return round(s[lo], 3)
    frac = pos - lo
    return round(s[lo] * (1.0 - frac) + s[hi] * frac, 3)


def summarize_num(vals: list[float]) -> dict[str, float]:
    s = sorted(vals)
    return {
        "n": len(s),
        "min": round(s[0], 3),
        "median": round(statistics.median(s), 3),
        "p95": percentile(s, 0.95),
        "max": round(s[-1], 3),
        "iqr": round(percentile(s, 0.75) - percentile(s, 0.25), 3),
        "mean": round(statistics.fmean(s), 3),
    }


def read_cpu_temp_max() -> float | None:
    vals: list[float] = []
    for tz in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        try:
            tname = (tz / "type").read_text(encoding="utf-8", errors="replace").strip()
            if "hw-trip" in tname:
                continue
            raw = int((tz / "temp").read_text().strip())
            if raw == -273000:
                continue
            if tname.lower().startswith("cpu-"):
                vals.append(raw / 1000.0)
        except (OSError, ValueError):
            pass
    return round(max(vals), 2) if vals else None


def read_meminfo() -> dict[str, float]:
    out: dict[str, float] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8", errors="replace").splitlines():
            k, v = line.split(":", 1)
            if k in ("MemAvailable", "SwapTotal", "SwapFree"):
                out[k] = round(int(v.strip().split()[0]) / 1024.0, 2)
    except (OSError, ValueError):
        pass
    if "SwapTotal" in out and "SwapFree" in out:
        out["SwapUsed"] = round(out["SwapTotal"] - out["SwapFree"], 2)
    return out


def read_proc_cpu_majflt(pid: int) -> dict[str, float] | None:
    try:
        st_txt = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8", errors="replace")
        fields = st_txt[st_txt.rfind(")") + 2 :].split()
        tick_ms = (int(fields[11]) + int(fields[12])) * 1000.0 / CLK_TCK
        majflt = int(fields[9]) + int(fields[10])
    except (OSError, ValueError, IndexError):
        return None
    sched_ms: float | None = None
    try:
        sched_fields = Path(f"/proc/{pid}/schedstat").read_text(encoding="utf-8", errors="replace").split()
        sched_ms = int(sched_fields[0]) / 1e6
    except (OSError, ValueError, IndexError):
        pass
    return {
        "stat_cpu_ms": tick_ms,
        "sched_cpu_ms": sched_ms if sched_ms is not None else tick_ms,
        "majflt": float(majflt),
    }


def collect_tree_pids(roots: list[int]) -> set[int]:
    valid_roots = {r for r in roots if r and Path(f"/proc/{r}").exists()}
    if not valid_roots:
        return set()
    children: dict[int, list[int]] = {}
    tracer_links: dict[int, list[int]] = {}
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        pid = int(p.name)
        try:
            st = (p / "stat").read_text(encoding="utf-8", errors="replace")
            ppid = int(st[st.rfind(")") + 2 :].split()[1])
            children.setdefault(ppid, []).append(pid)
            status = (p / "status").read_text(encoding="utf-8", errors="replace")
            m = re.search(r"(?m)^TracerPid:\s+(\d+)", status)
            if m:
                tp = int(m.group(1))
                if tp > 0:
                    tracer_links.setdefault(tp, []).append(pid)
        except (OSError, ValueError, IndexError):
            continue
    seen = set(valid_roots)
    stack = list(valid_roots)
    while stack:
        cur = stack.pop()
        for nxt in children.get(cur, []) + tracer_links.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def sample_group_pss_mb(proot_roots: list[int], daemon_roots: list[int]) -> dict[str, float]:
    proot_pids = collect_tree_pids(proot_roots)
    daemon_pids = collect_tree_pids(daemon_roots)
    all_pids = proot_pids | daemon_pids
    pss_map: dict[int, tuple[int, int]] = {}
    for pid in all_pids:
        try:
            sr = Path(f"/proc/{pid}/smaps_rollup").read_text(encoding="utf-8", errors="replace")
            mp = re.search(r"(?m)^Pss:\s+(\d+)", sr)
            ms = re.search(r"(?m)^SwapPss:\s+(\d+)", sr)
            pss_map[pid] = (int(mp.group(1)) if mp else 0, int(ms.group(1)) if ms else 0)
        except OSError:
            pass
    tot_pss = sum(v[0] for v in pss_map.values())
    tot_swap = sum(v[1] for v in pss_map.values())
    pr_pss = sum(pss_map.get(p, (0, 0))[0] for p in proot_pids)
    dm_pss = sum(pss_map.get(p, (0, 0))[0] for p in daemon_pids - proot_pids)
    return {
        "total_pss_mb": tot_pss / 1024.0,
        "total_swappss_mb": tot_swap / 1024.0,
        "proot_pss_mb": pr_pss / 1024.0,
        "daemon_pss_mb": dm_pss / 1024.0,
    }


def read_adb_pgmajfault(adb_port: int, serial: str | None) -> int | None:
    if not serial:
        return None
    rc, out = s6adb.run_adb(adb_port, ["shell", "awk '/^pgmajfault /{print $2}' /proc/vmstat"], serial=serial, timeout=8.0)
    if rc != 0:
        return None
    try:
        return int(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def android_system_binds() -> list[str]:
    binds: list[str] = []
    for path in (
        "/apex", "/odm", "/product", "/system", "/system_ext", "/vendor",
        "/linkerconfig/ld.config.txt",
        "/linkerconfig/com.android.art/ld.config.txt",
        "/plat_property_contexts", "/property_contexts",
    ):
        try:
            real = os.path.realpath(path)
        except OSError:
            continue
        if not os.path.exists(real):
            continue
        if os.path.isdir(real) or os.path.isfile(real):
            binds.extend(["-b", real])
    return binds


def proot_cmd_for_guest(
    guest_argv: list[str],
    extra_env: dict[str, str] | None = None,
    include_android_binds: bool = False,
) -> tuple[list[str], dict[str, str]]:
    host_env = {
        "PATH": f"{TERMUX_USR}/bin:/system/bin",
        "HOME": str(TERMUX_HOME),
        "TMPDIR": str(PROOT_TMP),
        "PREFIX": str(TERMUX_USR),
        "PROOT_TMP_DIR": str(PROOT_TMP),
        "LC_ALL": "C",
    }
    if extra_env:
        host_env.update(extra_env)
    cmd = [
        str(PROOT_FAST8),
        "-0",
        "-l",
        "-r",
        str(UBU),
        "-w",
        "/",
        "-b",
        "/proc",
        "-b",
        "/dev",
        "-b",
        "/sys",
        "-b",
        f"{SHM}:/dev/shm",
        "-b",
        f"{SYSD / 'sysctl_inotify_max_user_watches'}:/proc/sys/fs/inotify/max_user_watches",
        "-b",
        f"{PROOT_TMP}:/tmp",
        "-b",
        f"{TERMUX_HOME}:{TERMUX_HOME}",
        "-b",
        f"{TERMUX_USR}:{TERMUX_USR}",
        *(android_system_binds() if include_android_binds else []),
        "/usr/bin/env",
        "-i",
        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        f"HOME={GUEST_HOME}",
        "TMPDIR=/tmp",
        "LC_ALL=C",
        "GIT_OPTIONAL_LOCKS=0",
    ]
    if extra_env:
        for k, v in extra_env.items():
            cmd.append(f"{k}={v}")
    cmd.extend(guest_argv)
    return cmd, host_env


class PersistentMcpClient:
    """Persistent PRoot relay MCP stdio client with direct tracer PID handle."""

    def __init__(self, mode: str, sock_path: Path) -> None:
        self.mode = mode  # "A1" (F8_NO_HYBRID=1) or "B" (--no-fallback)
        self.sock_path = sock_path
        self._next_id = 1
        guest_argv = [
            "/usr/bin/python3",
            str(RELAY_PY),
            "--socket",
            str(sock_path),
            "--default-timeout",
            "60",
        ]
        for m in GUEST_MAPS:
            guest_argv.extend(["--map", m])
        extra_env: dict[str, str] = {}
        if mode == "A1":
            extra_env["F8_NO_HYBRID"] = "1"
        else:
            guest_argv.append("--no-fallback")

        cmd, host_env = proot_cmd_for_guest(guest_argv, extra_env=extra_env)
        self.proc = sp.Popen(
            cmd,
            env=host_env,
            stdin=sp.PIPE,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            text=True,
            bufsize=1,
        )
        self._init_handshake()

    def _send(self, msg: dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def _recv(self) -> dict[str, Any]:
        assert self.proc.stdout is not None
        line = self.proc.stdout.readline()
        if not line:
            err = self.proc.stderr.read() if self.proc.stderr else ""
            raise RuntimeError(f"MCP client EOF ({self.mode}), rc={self.proc.poll()}, stderr={err[:500]}")
        return json.loads(line)

    def _init_handshake(self) -> None:
        rid = self._next_id
        self._next_id += 1
        self._send(
            {
                "jsonrpc": "2.0",
                "id": rid,
                "method": "initialize",
                "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "b73", "version": "1"}},
            }
        )
        resp = self._recv()
        if resp.get("id") != rid or "result" not in resp:
            raise RuntimeError(f"initialize failed ({self.mode}): {resp}")
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def call_tool(self, name: str, arguments: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        rid = self._next_id
        self._next_id += 1
        t0 = time.perf_counter_ns()
        self._send({"jsonrpc": "2.0", "id": rid, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
        resp = self._recv()
        t1 = time.perf_counter_ns()
        if resp.get("id") != rid or "result" not in resp or resp["result"].get("isError"):
            raise RuntimeError(f"tools/call {name} failed ({self.mode}): {resp}")
        content = resp["result"].get("content")
        if not isinstance(content, list) or not content or not isinstance(content[0], dict) or "text" not in content[0]:
            raise RuntimeError(f"tools/call {name} missing content text ({self.mode}): {resp}")
        sc = json.loads(content[0]["text"])
        if not isinstance(sc, dict) or not sc:
            raise RuntimeError(f"tools/call {name} empty parsed payload ({self.mode}): {sc!r}")
        if name == "git_ro" and sc.get("returncode") != 0:
            raise RuntimeError(f"git_ro nonzero rc ({self.mode}): {sc}")
        return (t1 - t0) / 1e6, sc

    def close(self) -> None:
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
        except OSError:
            pass
        try:
            self.proc.wait(timeout=5)
        except sp.TimeoutExpired:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except sp.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        for pipe in (self.proc.stdout, self.proc.stderr):
            try:
                if pipe:
                    pipe.close()
            except OSError:
                pass


def build_synth_jsonl(path: Path, n_lines: int = 50000) -> dict[str, Any]:
    rng = random.Random(20261127)
    modes = ("balanced", "hybrid2", "fallback", "soak")
    statuses = ("ok", "ok", "ok", "warn", "cached")
    lines: list[str] = []
    for i in range(n_lines):
        rec = {
            "seq": i,
            "mode": modes[i % len(modes)],
            "status": statuses[rng.randrange(len(statuses))],
            "wall_ms": round(1.5 + rng.random() * 48.5, 3),
            "files": rng.randint(10, 4500),
            "bytes": rng.randint(256, 65536),
            "tag": f"node-{i % 17:02d}",
        }
        lines.append(json.dumps(rec, separators=(",", ":")))
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    path.write_bytes(payload)
    return {"path": str(path), "lines": n_lines, "bytes": len(payload)}


def build_workloads() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    layer_a = [
        {
            "id": "A_git_rev_parse",
            "layer": "A_short",
            "category": "git_subprocess",
            "repeat": 30,
            "calls": [("git_ro", {"cwd": "/root/projects/GPU加速/src/f8-proot-fast", "args": ["rev-parse", "HEAD"]})],
        },
        {
            "id": "A_git_status_short",
            "layer": "A_short",
            "category": "git_subprocess",
            "repeat": 30,
            "calls": [("git_ro", {"cwd": "/root/projects/GPU加速/src/f8-proot-fast", "args": ["status", "--short"]})],
        },
        {
            "id": "A_tree_scan_small",
            "layer": "A_short",
            "category": "io_syscall",
            "repeat": 30,
            "calls": [("repo_tree_scan", {"root": "/root/projects/GPU加速/src/f8-proot-fast", "max_entries": 500, "compute_sha256": True, "exclude_git": True})],
        },
        {
            "id": "A_json_summary_small",
            "layer": "A_short",
            "category": "python_cpu",
            "repeat": 30,
            "calls": [("python_json_summary", {"path": "/root/projects/GPU加速/evidence/session/proot/tracer-shard-01/shard-s-02/samples.jsonl", "limit_records": 5000})],
        },
        {
            "id": "A_text_search_small",
            "layer": "A_short",
            "category": "io_syscall",
            "repeat": 30,
            "calls": [("repo_text_search", {"root": "/root/projects/GPU加速/src/f8-proot-fast", "pattern": "proot-fast8", "fixed_string": True, "max_matches": 200})],
        },
    ]

    layer_b = [
        {
            "id": "B_tree_scan_cpp",
            "layer": "B_heavy",
            "category": "io_syscall",
            "repeat": 1,
            "calls": [("repo_tree_scan", {"root": "/root/projects/GPU加速/src/upstream/lorie/src/main/cpp", "max_entries": 5000, "compute_sha256": True, "exclude_git": True})],
        },
        {
            "id": "B_text_search_fixed",
            "layer": "B_heavy",
            "category": "io_syscall",
            "repeat": 1,
            "calls": [("repo_text_search", {"root": "/root/projects/GPU加速/src/upstream/lorie/src/main/cpp", "pattern": "loriePresentFlip", "fixed_string": True, "include_ext": [".c", ".h"], "max_matches": 500})],
        },
        {
            "id": "B_text_search_regex_worker",
            "layer": "B_heavy",
            "category": "io_syscall_subproc",
            "repeat": 1,
            "calls": [("repo_text_search", {"root": "/root/projects/GPU加速/src/upstream/lorie/src/main/cpp", "pattern": "lorie_mutex|loriePresent", "fixed_string": False, "include_ext": [".c", ".h"], "max_matches": 500})],
        },
        {
            "id": "B_git_log_stat",
            "layer": "B_heavy",
            "category": "git_subprocess",
            "repeat": 1,
            "calls": [("git_ro", {"cwd": "/root/projects/GPU加速/src/upstream", "args": ["log", "-n", "500", "--stat", "--no-renames"]})],
        },
        {
            "id": "B_git_blame",
            "layer": "B_heavy",
            "category": "git_subprocess",
            "repeat": 1,
            "calls": [("git_ro", {"cwd": "/root/projects/GPU加速/src/upstream", "args": ["blame", "--line-porcelain", "lorie/src/main/cpp/lorie/InitOutput.c"]})],
        },
        {
            "id": "B_git_ls_files",
            "layer": "B_heavy",
            "category": "git_subprocess",
            "repeat": 1,
            "calls": [("git_ro", {"cwd": "/root/projects/GPU加速/src/termux-proot-upstream", "args": ["ls-files"]})],
        },
        {
            "id": "B_git_grep",
            "layer": "B_heavy",
            "category": "git_subprocess",
            "repeat": 1,
            "calls": [("git_ro", {"cwd": "/root/projects/GPU加速/src/termux-proot-upstream", "args": ["grep", "-n", "seccomp"]})],
        },
        {
            "id": "B_json_summary_real_doc",
            "layer": "B_heavy",
            "category": "python_cpu",
            "repeat": 1,
            "calls": [("python_json_summary", {"path": "/root/projects/GPU加速/evidence/session/p2-b3a/t2-u4-c2-exact-sequence/c2-s3-r3-a.json"})],
        },
        {
            "id": "B_json_summary_synth_50k",
            "layer": "B_heavy",
            "category": "python_cpu",
            "repeat": 1,
            "calls": [("python_json_summary", {"path": "/bench_ws/synth_50k.jsonl", "limit_records": 50000})],
        },
        {
            "id": "B_mixed_ai_turn",
            "layer": "B_heavy",
            "category": "mixed_turn",
            "repeat": 1,
            "calls": [
                ("git_ro", {"cwd": "/root/projects/GPU加速/src/termux-proot-upstream", "args": ["status", "--short"]}),
                ("git_ro", {"cwd": "/root/projects/GPU加速/src/termux-proot-upstream", "args": ["log", "-n", "200", "--oneline"]}),
                ("repo_tree_scan", {"root": "/root/projects/GPU加速/src/upstream/lorie/src/main/cpp", "max_entries": 5000, "compute_sha256": True, "exclude_git": True}),
                ("repo_text_search", {"root": "/root/projects/GPU加速/src/upstream/lorie/src/main/cpp", "pattern": "loriePresentFlip", "fixed_string": True, "include_ext": [".c", ".h"], "max_matches": 500}),
                ("git_ro", {"cwd": "/root/projects/GPU加速/src/upstream", "args": ["blame", "--line-porcelain", "lorie/src/main/cpp/lorie/InitOutput.c"]}),
                ("python_json_summary", {"path": "/bench_ws/synth_50k.jsonl", "limit_records": 50000}),
            ],
        },
    ]
    return layer_a, layer_b


def execute_run_monitored(
    client: PersistentMcpClient,
    daemon_pid: int,
    spec: dict[str, Any],
) -> dict[str, Any]:
    tracer_pid = client.proc.pid
    daemon_roots = [daemon_pid] if client.mode == "B" else []
    stop_evt = threading.Event()
    peak = sample_group_pss_mb([tracer_pid], daemon_roots)
    sampler_errs: list[str] = []

    def sampler() -> None:
        try:
            while not stop_evt.is_set():
                snap = sample_group_pss_mb([tracer_pid], daemon_roots)
                for k, v in snap.items():
                    if v > peak[k]:
                        peak[k] = v
                stop_evt.wait(0.025)
        except Exception as exc:
            sampler_errs.append(repr(exc))

    t = threading.Thread(target=sampler, daemon=True)
    c0 = read_proc_cpu_majflt(tracer_pid)
    d0 = read_proc_cpu_majflt(daemon_pid) if client.mode == "B" else None
    t.start()
    call_lats: list[float] = []
    digests: list[str] = []
    run_t0 = time.perf_counter_ns()
    try:
        for _ in range(int(spec["repeat"])):
            for tool_name, tool_args in spec["calls"]:
                ms, sc = client.call_tool(tool_name, tool_args)
                call_lats.append(round(ms, 3))
                digests.append(canonical_digest(sc))
    finally:
        run_t1 = time.perf_counter_ns()
        stop_evt.set()
        t.join(timeout=2.0)
        c1 = read_proc_cpu_majflt(tracer_pid)
        d1 = read_proc_cpu_majflt(daemon_pid) if client.mode == "B" else None
    if sampler_errs:
        raise RuntimeError(f"PSS sampler error ({client.mode}): {sampler_errs[0]}")

    sched_cpu_ms = max(0.0, round((c1["sched_cpu_ms"] - c0["sched_cpu_ms"]), 3)) if c0 and c1 else None
    stat_cpu_ms = max(0.0, round((c1["stat_cpu_ms"] - c0["stat_cpu_ms"]), 3)) if c0 and c1 else None
    proc_majflt = int(max(0, round(c1["majflt"] - c0["majflt"]))) if c0 and c1 else None
    daemon_majflt = int(max(0, round(d1["majflt"] - d0["majflt"]))) if d0 and d1 else 0
    return {
        "wall_ms": round((run_t1 - run_t0) / 1e6, 3),
        "call_p50_ms": percentile(call_lats, 0.50),
        "call_p95_ms": percentile(call_lats, 0.95),
        "digest": hashlib.sha256("|".join(digests).encode("ascii")).hexdigest(),
        "tracer_sched_cpu_ms": sched_cpu_ms,
        "tracer_stat_cpu_ms": stat_cpu_ms,
        "tracer_proc_majflt": proc_majflt,
        "daemon_proc_majflt": daemon_majflt,
        "peak_pss_total_mb": round(peak["total_pss_mb"], 2),
        "peak_swappss_total_mb": round(peak["total_swappss_mb"], 2),
        "peak_pss_proot_mb": round(peak["proot_pss_mb"], 2),
        "peak_pss_daemon_mb": round(peak["daemon_pss_mb"], 2),
    }


def run_abba_suite(
    client_a1: PersistentMcpClient,
    client_b: PersistentMcpClient,
    daemon_pid: int,
    workloads: list[dict[str, Any]],
    n_pairs: int,
    adb_port: int,
    adb_serial: str | None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    # Pair pattern: n_pairs pairs = n_pairs/2 ABBA blocks = ("A1","B","B","A1")
    order: list[tuple[str, str]] = []
    for p in range(n_pairs):
        if p % 2 == 0:
            order.append(("A1", "B"))
        else:
            order.append(("B", "A1"))

    for spec in workloads:
        # Warmup once on each arm (untimed)
        warm_a1 = execute_run_monitored(client_a1, daemon_pid, spec)
        warm_b = execute_run_monitored(client_b, daemon_pid, spec)
        if warm_a1["digest"] != warm_b["digest"]:
            raise RuntimeError(f"Parity mismatch during warmup for {spec['id']}: {warm_a1['digest']} vs {warm_b['digest']}")

        pg0 = read_adb_pgmajfault(adb_port, adb_serial)
        temp0 = read_cpu_temp_max()
        mem0 = read_meminfo()

        pairs_data: list[dict[str, Any]] = []
        a1_walls: list[float] = []
        b_walls: list[float] = []
        a1_cpus: list[float] = []
        b_cpus: list[float] = []
        a1_pss: list[float] = []
        b_pss: list[float] = []
        b_wins = 0

        for idx, (first_arm, second_arm) in enumerate(order):
            arm_res: dict[str, Any] = {}
            for arm in (first_arm, second_arm):
                cli = client_a1 if arm == "A1" else client_b
                arm_res[arm] = execute_run_monitored(cli, daemon_pid, spec)
            ra = arm_res["A1"]
            rb = arm_res["B"]
            parity_ok = ra["digest"] == rb["digest"]
            if not parity_ok:
                raise RuntimeError(f"Parity mismatch at pair {idx} for {spec['id']}")
            speedup = round(ra["wall_ms"] / rb["wall_ms"], 3) if rb["wall_ms"] > 0 else 0.0
            delta_pct = round(100.0 * (rb["wall_ms"] - ra["wall_ms"]) / ra["wall_ms"], 2) if ra["wall_ms"] > 0 else 0.0
            if rb["wall_ms"] < ra["wall_ms"]:
                b_wins += 1
            a1_walls.append(ra["wall_ms"])
            b_walls.append(rb["wall_ms"])
            if ra["tracer_sched_cpu_ms"] is not None:
                a1_cpus.append(ra["tracer_sched_cpu_ms"])
            if rb["tracer_sched_cpu_ms"] is not None:
                b_cpus.append(rb["tracer_sched_cpu_ms"])
            a1_pss.append(ra["peak_pss_total_mb"])
            b_pss.append(rb["peak_pss_total_mb"])
            pairs_data.append(
                {
                    "pair_idx": idx,
                    "order": f"{first_arm}->{second_arm}",
                    "parity_ok": parity_ok,
                    "A1": ra,
                    "B": rb,
                    "speedup": speedup,
                    "delta_pct": delta_pct,
                }
            )

        pg1 = read_adb_pgmajfault(adb_port, adb_serial)
        temp1 = read_cpu_temp_max()
        mem1 = read_meminfo()
        med_a1 = statistics.median(a1_walls)
        med_b = statistics.median(b_walls)
        med_cpu_a1 = round(statistics.median(a1_cpus), 3) if a1_cpus else None
        med_cpu_b = round(statistics.median(b_cpus), 3) if b_cpus else None
        cpu_red_pct = (
            round(100.0 * (med_cpu_b - med_cpu_a1) / med_cpu_a1, 2)
            if med_cpu_a1 and med_cpu_a1 > 0 and med_cpu_b is not None
            else None
        )
        pg_delta: int | str
        if pg0 is not None and pg1 is not None:
            pg_delta = max(0, pg1 - pg0)
        else:
            pg_delta = "UNAVAILABLE_ADB_OFFLINE"

        results.append(
            {
                "id": spec["id"],
                "layer": spec["layer"],
                "category": spec["category"],
                "repeat": spec["repeat"],
                "n_pairs": n_pairs,
                "parity_100pct": True,
                "digest_sha256": warm_a1["digest"],
                "b_wins": b_wins,
                "sign_p": two_sided_sign_p(b_wins, n_pairs),
                "median_speedup": round(med_a1 / med_b, 3) if med_b > 0 else 0.0,
                "median_delta_pct": round(100.0 * (med_b - med_a1) / med_a1, 2) if med_a1 > 0 else 0.0,
                "A1_wall_ms": summarize_num(a1_walls),
                "B_wall_ms": summarize_num(b_walls),
                "A1_call_p50_ms": round(statistics.median([p["A1"]["call_p50_ms"] for p in pairs_data]), 3),
                "A1_call_p95_ms": round(statistics.median([p["A1"]["call_p95_ms"] for p in pairs_data]), 3),
                "B_call_p50_ms": round(statistics.median([p["B"]["call_p50_ms"] for p in pairs_data]), 3),
                "B_call_p95_ms": round(statistics.median([p["B"]["call_p95_ms"] for p in pairs_data]), 3),
                "A1_tracer_sched_cpu_ms_med": med_cpu_a1,
                "B_tracer_sched_cpu_ms_med": med_cpu_b,
                "tracer_cpu_delta_pct": cpu_red_pct,
                "A1_peak_pss_total_mb_max": round(max(a1_pss), 2),
                "B_peak_pss_total_mb_max": round(max(b_pss), 2),
                "adb_pgmajfault_delta": pg_delta,
                "env_temp_c": {"start": temp0, "end": temp1},
                "mem_avail_mb": {"start": mem0.get("MemAvailable"), "end": mem1.get("MemAvailable")},
                "pairs": pairs_data,
            }
        )
    return results


def run_percall_a2_reference(n_pairs: int = 5) -> list[dict[str, Any]]:
    """Measure one-shot per-call PRoot CLI invocations (Arm A2) on 3 representative heavy tasks."""
    cases = [
        (
            "A2_tree_scan_cpp_oneshot",
            [
                "/usr/bin/python3",
                "-c",
                f"import sys; sys.path.insert(0, '{HYB_DIR}'); "
                "from f8_hybrid2_policy import DEFAULT_FALLBACK_MAPS, Policy; "
                "from f8_hybrid2_tools import MCPToolEngine, RequestContext; "
                "pol = Policy(DEFAULT_FALLBACK_MAPS, '/tmp', '/tmp'); "
                "eng = MCPToolEngine(pol, '/usr/bin/git', 60.0); "
                "res = eng.call_tool(1, {'name': 'repo_tree_scan', 'arguments': {'root': '/root/projects/GPU加速/src/upstream/lorie/src/main/cpp', 'max_entries': 5000, 'compute_sha256': True, 'exclude_git': True}}, RequestContext('a2', 60.0)); "
                "assert not res['result'].get('isError'), res; "
                "print(len(res['result']['content'][0]['text']))",
            ],
        ),
        (
            "A2_git_log_stat_oneshot",
            ["/usr/bin/git", "-C", "/root/projects/GPU加速/src/upstream", "--no-pager", "log", "-n", "500", "--stat", "--no-renames"],
        ),
        (
            "A2_json_synth_50k_oneshot",
            [
                "/usr/bin/python3",
                "-c",
                f"import sys; sys.path.insert(0, '{HYB_DIR}'); "
                "from f8_hybrid2_policy import Policy; "
                "from f8_hybrid2_tools import MCPToolEngine, RequestContext; "
                f"pol = Policy([('/bench_ws', '{BENCH_WS}')], '/tmp', '/tmp'); "
                "eng = MCPToolEngine(pol, '/usr/bin/git', 60.0); "
                "res = eng.call_tool(1, {'name': 'python_json_summary', 'arguments': {'path': '/bench_ws/synth_50k.jsonl', 'limit_records': 50000}}, RequestContext('a2', 60.0)); "
                "assert not res['result'].get('isError'), res; "
                "print(len(res['result']['content'][0]['text']))",
            ],
        ),
    ]
    out: list[dict[str, Any]] = []
    for cid, argv in cases:
        cmd, host_env = proot_cmd_for_guest(argv)
        # 1 warmup
        sp.run(cmd, env=host_env, stdout=sp.PIPE, stderr=sp.PIPE, check=True, timeout=60)
        walls: list[float] = []
        for _ in range(n_pairs):
            t0 = time.perf_counter_ns()
            r = sp.run(cmd, env=host_env, stdout=sp.PIPE, stderr=sp.PIPE, check=True, timeout=60)
            t1 = time.perf_counter_ns()
            if r.returncode != 0:
                raise RuntimeError(f"{cid} failed")
            walls.append(round((t1 - t0) / 1e6, 3))
        out.append({"id": cid, "n": n_pairs, "wall_ms": summarize_num(walls)})
    return out


def run_concurrent_4x_benchmark(sock_path: Path, daemon_pid: int, n_pairs: int = 5) -> dict[str, Any]:
    """4 concurrent PRoot clients (4x fallback vs 4x relay -> shared native daemon)."""
    seq = [
        ("repo_tree_scan", {"root": "/root/projects/GPU加速/src/upstream/lorie/src/main/cpp", "max_entries": 5000, "compute_sha256": True, "exclude_git": True}),
        ("repo_text_search", {"root": "/root/projects/GPU加速/src/upstream/lorie/src/main/cpp", "pattern": "loriePresentFlip", "fixed_string": True, "include_ext": [".c", ".h"], "max_matches": 500}),
        ("git_ro", {"cwd": "/root/projects/GPU加速/src/upstream", "args": ["log", "-n", "500", "--stat", "--no-renames"]}),
        ("python_json_summary", {"path": "/bench_ws/synth_50k.jsonl", "limit_records": 50000}),
    ]

    def one_group(mode: str) -> dict[str, Any]:
        clients = [PersistentMcpClient(mode, sock_path) for _ in range(4)]
        tracer_pids = [c.proc.pid for c in clients]
        daemon_roots = [daemon_pid] if mode == "B" else []
        try:
            # Warmup 1 call on each
            for c in clients:
                c.call_tool(seq[0][0], seq[0][1])

            stop_evt = threading.Event()
            init_snap = sample_group_pss_mb(tracer_pids, daemon_roots)
            peak = {k: init_snap[k] for k in ("total_pss_mb", "proot_pss_mb", "daemon_pss_mb")}
            sampler_errs: list[str] = []

            def sampler() -> None:
                try:
                    while not stop_evt.is_set():
                        snap = sample_group_pss_mb(tracer_pids, daemon_roots)
                        for k in ("total_pss_mb", "proot_pss_mb", "daemon_pss_mb"):
                            if snap[k] > peak[k]:
                                peak[k] = snap[k]
                        stop_evt.wait(0.025)
                except Exception as exc:
                    sampler_errs.append(repr(exc))

            barrier = threading.Barrier(4)
            all_lats: list[float] = []
            lat_lock = threading.Lock()
            errs: list[str] = []

            def worker(idx: int, cli: PersistentMcpClient) -> None:
                try:
                    barrier.wait(timeout=10.0)
                    local_lats: list[float] = []
                    for step in range(len(seq)):
                        tname, targs = seq[(idx + step) % len(seq)]
                        ms, _ = cli.call_tool(tname, targs)
                        local_lats.append(round(ms, 3))
                    with lat_lock:
                        all_lats.extend(local_lats)
                except Exception as exc:
                    with lat_lock:
                        errs.append(f"worker-{idx}: {exc}")

            c0 = [read_proc_cpu_majflt(p) for p in tracer_pids]
            st = threading.Thread(target=sampler, daemon=True)
            st.start()
            t0 = time.perf_counter_ns()
            threads = [threading.Thread(target=worker, args=(i, c)) for i, c in enumerate(clients)]
            for th in threads:
                th.start()
            for th in threads:
                th.join(timeout=120.0)
            t1 = time.perf_counter_ns()
            stop_evt.set()
            st.join(timeout=2.0)
            c1 = [read_proc_cpu_majflt(p) for p in tracer_pids]
            if sampler_errs:
                raise RuntimeError(f"4x PSS sampler error ({mode}): {sampler_errs[0]}")
            if errs:
                raise RuntimeError(f"4x concurrent error ({mode}): {errs}")

            makespan_ms = round((t1 - t0) / 1e6, 3)
            tracer_cpu_sum = sum(
                max(0.0, b["sched_cpu_ms"] - a["sched_cpu_ms"])
                for a, b in zip(c0, c1)
                if a is not None and b is not None
            )
            return {
                "makespan_ms": makespan_ms,
                "throughput_calls_per_s": round(len(all_lats) / (makespan_ms / 1000.0), 3),
                "call_p50_ms": percentile(all_lats, 0.50),
                "call_p95_ms": percentile(all_lats, 0.95),
                "tracer_sched_cpu_sum_ms": round(tracer_cpu_sum, 3),
                "peak_pss_total_mb": round(peak["total_pss_mb"], 2),
                "peak_pss_proot_mb": round(peak["proot_pss_mb"], 2),
                "peak_pss_daemon_mb": round(peak["daemon_pss_mb"], 2),
            }
        finally:
            for c in clients:
                c.close()

    # Run ABBA pairs
    a_makespans: list[float] = []
    b_makespans: list[float] = []
    pairs: list[dict[str, Any]] = []
    b_wins = 0
    for p in range(n_pairs):
        order = ("A1", "B") if p % 2 == 0 else ("B", "A1")
        res = {}
        for m in order:
            res[m] = one_group(m)
        if res["B"]["makespan_ms"] < res["A1"]["makespan_ms"]:
            b_wins += 1
        a_makespans.append(res["A1"]["makespan_ms"])
        b_makespans.append(res["B"]["makespan_ms"])
        pairs.append({"pair_idx": p, "order": f"{order[0]}->{order[1]}", "A1": res["A1"], "B": res["B"]})

    med_a = statistics.median(a_makespans)
    med_b = statistics.median(b_makespans)
    return {
        "n_pairs": n_pairs,
        "b_wins": b_wins,
        "sign_p": two_sided_sign_p(b_wins, n_pairs),
        "median_speedup": round(med_a / med_b, 3) if med_b > 0 else 0.0,
        "A1_makespan_ms": summarize_num(a_makespans),
        "B_makespan_ms": summarize_num(b_makespans),
        "A1_throughput_med_ops_s": round(statistics.median([x["A1"]["throughput_calls_per_s"] for x in pairs]), 3),
        "B_throughput_med_ops_s": round(statistics.median([x["B"]["throughput_calls_per_s"] for x in pairs]), 3),
        "A1_tracer_cpu_sum_med_ms": round(statistics.median([x["A1"]["tracer_sched_cpu_sum_ms"] for x in pairs]), 3),
        "B_tracer_cpu_sum_med_ms": round(statistics.median([x["B"]["tracer_sched_cpu_sum_ms"] for x in pairs]), 3),
        "A1_peak_pss_total_mb_max": round(max(x["A1"]["peak_pss_total_mb"] for x in pairs), 2),
        "B_peak_pss_total_mb_max": round(max(x["B"]["peak_pss_total_mb"] for x in pairs), 2),
        "pairs": pairs,
    }


def run_autostart_cold_benchmark(n_native: int = 10, n_stripped: int = 5) -> dict[str, Any]:
    """Measure end-to-end cold-start latency via TermuxService --auto-start vs stripped-7-env fallback."""
    if AUTOSTART_DIR.exists():
        shutil.rmtree(AUTOSTART_DIR, ignore_errors=True)
    AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
    as_sock = AUTOSTART_DIR / "m.sock"

    def stop_as_daemon() -> None:
        sp.run(
            [sys.executable, str(CTL_PY), "--dir", str(AUTOSTART_DIR), "stop"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            timeout=15,
        )
        for fn in ("d.pid", "m.sock", "ready"):
            p = AUTOSTART_DIR / fn
            if p.exists():
                p.unlink()

    am_env = {k: os.environ[k] for k in AM_REQUIRED_ENV if k in os.environ}
    if len(am_env) != len(AM_REQUIRED_ENV):
        raise RuntimeError(f"Missing AM_REQUIRED_ENV in runner: {set(AM_REQUIRED_ENV) - set(am_env)}")

    am_env["PREFIX"] = str(TERMUX_USR)
    for k in ("ANDROID_RUNTIME_ROOT",):
        if k in os.environ:
            am_env[k] = os.environ[k]

    native_e2e_ms: list[float] = []
    fallback_e2e_ms: list[float] = []
    verified_tracer0 = 0

    try:
        for i in range(n_native):
            stop_as_daemon()
            guest_argv = [
                "/usr/bin/python3",
                str(RELAY_PY),
                "--socket",
                str(as_sock),
                "--auto-start",
                "--no-fallback",
                "--default-timeout",
                "30",
            ]
            for m in GUEST_MAPS:
                guest_argv.extend(["--map", m])
            cmd, host_env = proot_cmd_for_guest(guest_argv, extra_env=am_env, include_android_binds=True)
            t0 = time.perf_counter_ns()
            proc = sp.Popen(cmd, env=host_env, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, text=True, bufsize=1)
            try:
                assert proc.stdin and proc.stdout
                proc.stdin.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "initialize",
                            "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "cs", "version": "1"}},
                        }
                    )
                    + "\n"
                )
                proc.stdin.flush()
                r_init = json.loads(proc.stdout.readline())
                if "result" not in r_init:
                    raise RuntimeError(f"cold init failed: {r_init}")
                proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}) + "\n")
                proc.stdin.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/call",
                            "params": {"name": "git_ro", "arguments": {"cwd": "/root/projects/GPU加速/src/f8-proot-fast", "args": ["rev-parse", "HEAD"]}},
                        }
                    )
                    + "\n"
                )
                proc.stdin.flush()
                r_call = json.loads(proc.stdout.readline())
                t1 = time.perf_counter_ns()
                if r_call.get("result", {}).get("isError"):
                    raise RuntimeError(f"cold tool failed: {r_call}")
                native_e2e_ms.append(round((t1 - t0) / 1e6, 3))
            finally:
                try:
                    if proc.stdin:
                        proc.stdin.close()
                except OSError:
                    pass
                proc.wait(timeout=5)
                for pipe in (proc.stdout, proc.stderr):
                    if pipe:
                        pipe.close()

            st = get_status(AUTOSTART_DIR)
            if st.get("running") and st.get("tracer_pid") == 0:
                verified_tracer0 += 1

        stop_as_daemon()
        for _ in range(n_stripped):
            guest_argv = [
                "/usr/bin/python3",
                str(RELAY_PY),
                "--socket",
                str(as_sock),
                "--auto-start",
                "--default-timeout",
                "30",
            ]
            for m in GUEST_MAPS:
                guest_argv.extend(["--map", m])
            cmd, host_env = proot_cmd_for_guest(guest_argv, extra_env=None)
            t0 = time.perf_counter_ns()
            proc = sp.Popen(cmd, env=host_env, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, text=True, bufsize=1)
            try:
                assert proc.stdin and proc.stdout
                proc.stdin.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "initialize",
                            "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "cs-fb", "version": "1"}},
                        }
                    )
                    + "\n"
                )
                proc.stdin.flush()
                json.loads(proc.stdout.readline())
                proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}) + "\n")
                proc.stdin.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/call",
                            "params": {"name": "git_ro", "arguments": {"cwd": "/root/projects/GPU加速/src/f8-proot-fast", "args": ["rev-parse", "HEAD"]}},
                        }
                    )
                    + "\n"
                )
                proc.stdin.flush()
                r_call = json.loads(proc.stdout.readline())
                t1 = time.perf_counter_ns()
                if r_call.get("result", {}).get("isError"):
                    raise RuntimeError(f"stripped fallback call failed: {r_call}")
                fallback_e2e_ms.append(round((t1 - t0) / 1e6, 3))
            finally:
                try:
                    if proc.stdin:
                        proc.stdin.close()
                except OSError:
                    pass
                proc.wait(timeout=5)
                for pipe in (proc.stdout, proc.stderr):
                    if pipe:
                        pipe.close()
    finally:
        stop_as_daemon()
        shutil.rmtree(AUTOSTART_DIR, ignore_errors=True)

    return {
        "n_native_autostart": n_native,
        "verified_tracer0_count": verified_tracer0,
        "native_autostart_e2e_ms": summarize_num(native_e2e_ms),
        "n_stripped_fallback": n_stripped,
        "stripped_fallback_e2e_ms": summarize_num(fallback_e2e_ms),
    }


def main() -> int:
    self_tp = read_tracer_pid(os.getpid())
    if self_tp != 0:
        print(f"ERROR: stage7_3_bench.py must run natively (TracerPid=0), got {self_tp}", file=sys.stderr)
        return 2
    if not PROOT_FAST8.exists():
        print(f"ERROR: missing {PROOT_FAST8}", file=sys.stderr)
        return 2

    n_pairs = int(os.environ.get("STAGE73_N_PAIRS", "10"))
    n_conc_pairs = int(os.environ.get("STAGE73_CONC_PAIRS", "5"))

    # Setup clean isolated benchmark directories
    for d in (RUNTIME_DIR, BENCH_WS, PROOT_TMP, GUEST_HOME):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)
    os.chmod(RUNTIME_DIR, 0o700)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    synth_meta = build_synth_jsonl(BENCH_WS / "synth_50k.jsonl", n_lines=50000)

    # Probe ADB -P 5038 safely
    adb_port = 5038
    adb_serial: str | None = None
    try:
        adb_serial = s6adb.detect_myron_serial(adb_port)
    except SystemExit:
        adb_serial = None

    # Start isolated native daemon
    daemon_home = RUNTIME_DIR / "home"
    daemon_tmp = RUNTIME_DIR / "tmp"
    daemon_home.mkdir(parents=True, exist_ok=True)
    daemon_tmp.mkdir(parents=True, exist_ok=True)
    daemon_log_path = RUNTIME_DIR / "daemon.err.log"
    daemon_log_fh = open(daemon_log_path, "wb")
    daemon_cmd = [
        sys.executable,
        str(DAEMON_PY),
        "--socket",
        str(SOCK_PATH),
        "--home",
        str(daemon_home),
        "--tmp",
        str(daemon_tmp),
        "--pidfile",
        str(RUNTIME_DIR / "d.pid"),
        "--ready",
        str(RUNTIME_DIR / "ready"),
        "--log",
        str(RUNTIME_DIR / "audit.jsonl"),
        "--idle-timeout",
        "0",
        "--max-clients",
        "16",
        "--max-inflight",
        "16",
    ]
    for m in WS_MAPS:
        daemon_cmd.extend(["--map", m])
    daemon_proc = sp.Popen(daemon_cmd, stdin=sp.DEVNULL, stdout=daemon_log_fh, stderr=daemon_log_fh)

    client_a1: PersistentMcpClient | None = None
    client_b: PersistentMcpClient | None = None
    try:
        if not wait_for_ready(RUNTIME_DIR, timeout_s=10.0):
            err_tail = daemon_log_path.read_text(encoding="utf-8", errors="replace")[-1000:] if daemon_log_path.exists() else ""
            raise RuntimeError(f"Native daemon failed to reach ready state: rc={daemon_proc.poll()} log={err_tail}")
        st0 = get_status(RUNTIME_DIR)
        if not st0.get("running") or st0.get("tracer_pid") != 0:
            raise RuntimeError(f"Daemon failed native verification: {st0}")
        daemon_pid = int(st0["pid"])
        base_fds = len(os.listdir(f"/proc/{daemon_pid}/fd"))

        layer_a, layer_b = build_workloads()
        client_a1 = PersistentMcpClient("A1", SOCK_PATH)
        client_b = PersistentMcpClient("B", SOCK_PATH)

        layer_a_res = run_abba_suite(client_a1, client_b, daemon_pid, layer_a, n_pairs, adb_port, adb_serial)
        layer_b_res = run_abba_suite(client_a1, client_b, daemon_pid, layer_b, n_pairs, adb_port, adb_serial)

        client_a1.close()
        client_b.close()
        client_a1 = None
        client_b = None

        a2_ref = run_percall_a2_reference(n_pairs=5)
        conc_4x = run_concurrent_4x_benchmark(SOCK_PATH, daemon_pid, n_pairs=n_conc_pairs)

        final_fds = len(os.listdir(f"/proc/{daemon_pid}/fd"))
        # Close daemon cleanly before cold-start benchmark
        daemon_proc.send_signal(signal.SIGTERM)
        daemon_rc = daemon_proc.wait(timeout=10)

        cold_autostart = run_autostart_cold_benchmark(n_native=10, n_stripped=5)

        # Count orphan processes with TracerPid == any of our terminated PIDs? Zero should remain.
        report = {
            "meta": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "runner_tracer_pid": self_tp,
                "proot_binary": str(PROOT_FAST8),
                "native_python": sys.version.split()[0],
                "adb_serial": adb_serial or "OFFLINE",
                "n_pairs": n_pairs,
                "n_conc_pairs": n_conc_pairs,
                "synth_50k_meta": synth_meta,
                "daemon_base_fds": base_fds,
                "daemon_final_fds": final_fds,
                "daemon_fd_delta": final_fds - base_fds,
                "daemon_exit_rc": daemon_rc,
            },
            "layer_a_short": layer_a_res,
            "layer_b_heavy": layer_b_res,
            "arm_a2_percall_reference": a2_ref,
            "concurrent_4x": conc_4x,
            "cold_autostart": cold_autostart,
        }
        OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"STAGE7_3_BENCH_DONE output={OUT_JSON} fd_delta={final_fds - base_fds} daemon_rc={daemon_rc}")
        return 0
    finally:
        if client_a1:
            client_a1.close()
        if client_b:
            client_b.close()
        if daemon_proc.poll() is None:
            daemon_proc.terminate()
            try:
                daemon_proc.wait(timeout=5)
            except sp.TimeoutExpired:
                daemon_proc.kill()
                daemon_proc.wait()
        try:
            daemon_log_fh.close()
        except OSError:
            pass
        for d in (RUNTIME_DIR, BENCH_WS, PROOT_TMP, GUEST_HOME):
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
