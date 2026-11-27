#!/usr/bin/env python3
"""Unified start/stop/status/disable controller for Stage 7.2 Native Hybrid 2.0.

Client-agnostic lifecycle control for Hermes, Codex CLI, Claude Code,
Claude Desktop, Antigravity, OpenCode, or standalone probes:
- Single-flight cross-process `flock` prevents thundering-herd launches
- Never requires client configs to duplicate Android's 7 ART env vars; gracefully
  reports `auto-start-env-stripped` when stripped inside PRoot so relay falls back
- `stop` verifies PID ownership via `pidfile` + `/proc/<pid>/cmdline` before SIGTERM
- `client-config` prints non-destructive config snippets without mutating live configs
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import shlex
import signal
import subprocess as sp
import sys
import time
from pathlib import Path
from typing import Any

from f8_hybrid2_policy import (
    DEFAULT_DAEMON_MAPS,
    DEFAULT_RUNTIME_DIR,
    parse_map_specs,
    proc_matches_cmdline,
    read_tracer_pid,
    validate_unix_sock_path,
)
from f8_hybrid2_relay import probe_daemon

AM_REQUIRED_ENV = (
    "ANDROID_ART_ROOT",
    "ANDROID_I18N_ROOT",
    "ANDROID_TZDATA_ROOT",
    "ANDROID_ROOT",
    "ANDROID_DATA",
    "BOOTCLASSPATH",
    "DEX2OATBOOTCLASSPATH",
)
AM_BIN = "/data/data/com.termux/files/usr/bin/am"
TERMUX_SVC = "com.termux/com.termux.app.TermuxService"
TERMUX_BASH = "/data/data/com.termux/files/usr/bin/bash"
TERMUX_PYTHON = "/data/data/com.termux/files/usr/bin/python3"
TERMUX_GIT = "/data/data/com.termux/files/usr/bin/git"
DAEMON_SCRIPT = str(Path(__file__).resolve().parent / "f8_hybrid2_daemon.py")
RELAY_SCRIPT = str(Path(__file__).resolve().parent / "f8_hybrid2_relay.py")


def missing_am_env() -> list[str]:
    return [k for k in AM_REQUIRED_ENV if not os.environ.get(k)]


def runtime_paths(runtime_dir: Path) -> dict[str, Path]:
    return {
        "dir": runtime_dir,
        "sock": runtime_dir / "m.sock",
        "pid": runtime_dir / "d.pid",
        "ready": runtime_dir / "ready",
        "disabled": runtime_dir / "disabled.flag",
        "ctl_lock": runtime_dir / "ctl.lock",
        "log": runtime_dir / "audit.jsonl",
        "out": runtime_dir / "daemon.out",
        "home": runtime_dir / "hhome",
        "tmp": runtime_dir / "htmp",
        "bootstrap": runtime_dir / "native-bootstrap.sh",
    }


def _read_live_pid(pidfile: Path) -> int | None:
    if not pidfile.exists():
        return None
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    if not proc_matches_cmdline(pid, "f8_hybrid2_daemon.py"):
        return None
    return pid


def _wait_ready(sock_path: Path, ready_path: Path, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if sock_path.exists() and ready_path.exists():
            ok, _ = probe_daemon(sock_path, timeout_s=1.5)
            if ok:
                return True
        time.sleep(0.05)
    return False


def get_status(runtime_dir: Path) -> dict[str, Any]:
    paths = runtime_paths(runtime_dir)
    pid = _read_live_pid(paths["pid"])
    sock_exists = paths["sock"].exists()
    ready_exists = paths["ready"].exists()
    probe_ok, probe_detail = probe_daemon(paths["sock"], timeout_s=1.0) if sock_exists else (False, "socket-missing")
    tpid = read_tracer_pid(pid) if pid is not None else -1
    fds = -1
    if pid is not None:
        try:
            fds = len(os.listdir(f"/proc/{pid}/fd"))
        except OSError:
            pass
    return {
        "runtime_dir": str(runtime_dir),
        "socket": str(paths["sock"]),
        "disabled": paths["disabled"].exists() or os.environ.get("F8_NO_HYBRID") == "1",
        "running": pid is not None and probe_ok,
        "pid": pid,
        "tracer_pid": tpid,
        "ready": ready_exists,
        "probe_ok": probe_ok,
        "probe_detail": probe_detail,
        "fds": fds,
        "caller_tracer_pid": read_tracer_pid(),
        "missing_am_env": missing_am_env(),
    }


def _start_native_direct(
    paths: dict[str, Path],
    daemon_py: str,
    maps: list[str],
    idle_timeout: float,
    max_clients: int,
    max_inflight: int,
    skip_tracer_check: bool,
) -> None:
    for d in (paths["dir"], paths["home"], paths["tmp"]):
        d.mkdir(parents=True, exist_ok=True)
    os.chmod(paths["dir"], 0o700)
    py_bin = sys.executable if skip_tracer_check else (TERMUX_PYTHON if os.path.exists(TERMUX_PYTHON) else sys.executable)
    cmd = [
        py_bin,
        daemon_py,
        "--socket",
        str(paths["sock"]),
        "--home",
        str(paths["home"]),
        "--tmp",
        str(paths["tmp"]),
        "--pidfile",
        str(paths["pid"]),
        "--ready",
        str(paths["ready"]),
        "--log",
        str(paths["log"]),
        "--git-bin",
        TERMUX_GIT if os.path.exists(TERMUX_GIT) else "git",
        "--idle-timeout",
        str(idle_timeout),
        "--max-clients",
        str(max_clients),
        "--max-inflight",
        str(max_inflight),
    ]
    for g, h in parse_map_specs(maps, DEFAULT_DAEMON_MAPS):
        cmd.extend(["--map", f"{g}={h}"])
    if skip_tracer_check:
        cmd.append("--skip-tracer-check")
    with open(paths["out"], "ab") as out_fh:
        sp.Popen(cmd, stdin=sp.DEVNULL, stdout=out_fh, stderr=out_fh, start_new_session=True)


def _start_via_termux_service(
    paths: dict[str, Path],
    daemon_py: str,
    maps: list[str],
    idle_timeout: float,
    max_clients: int,
    max_inflight: int,
) -> tuple[bool, str]:
    missing = missing_am_env()
    if missing:
        return False, "auto-start-env-stripped"
    if not str(paths["dir"]).startswith("/data/data/com.termux/"):
        return False, "runtime-dir-outside-termux"
    for d in (paths["dir"], paths["home"], paths["tmp"]):
        d.mkdir(parents=True, exist_ok=True)
    os.chmod(paths["dir"], 0o700)

    map_flags = " ".join(f"--map {shlex.quote(f'{g}={h}')}" for g, h in parse_map_specs(maps, DEFAULT_DAEMON_MAPS))
    script_body = (
        f"#!{TERMUX_BASH}\n"
        "set -euo pipefail\n"
        "export PATH=/data/data/com.termux/files/usr/bin\n"
        "export HOME=/data/data/com.termux/files/home\n"
        "export TMPDIR=/data/data/com.termux/files/usr/tmp\n"
        f"{shlex.quote(TERMUX_PYTHON)} {shlex.quote(daemon_py)} "
        f"--socket {shlex.quote(str(paths['sock']))} {map_flags} "
        f"--home {shlex.quote(str(paths['home']))} --tmp {shlex.quote(str(paths['tmp']))} "
        f"--pidfile {shlex.quote(str(paths['pid']))} --ready {shlex.quote(str(paths['ready']))} "
        f"--log {shlex.quote(str(paths['log']))} "
        f"--idle-timeout {idle_timeout} --max-clients {max_clients} --max-inflight {max_inflight} "
        f"> {shlex.quote(str(paths['out']))} 2>&1 &\n"
    )
    paths["bootstrap"].write_text(script_body, encoding="utf-8")
    os.chmod(paths["bootstrap"], 0o755)
    r = sp.run(
        [
            AM_BIN,
            "startservice",
            "--user",
            "0",
            "-n",
            TERMUX_SVC,
            "-a",
            "com.termux.service_execute",
            "-d",
            f"file://{paths['bootstrap']}",
            "--ez",
            "com.termux.execute.background",
            "true",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode != 0:
        return False, f"am-failed:{r.returncode}"
    return True, "launched"


def ensure_running(
    runtime_dir: Path | str = DEFAULT_RUNTIME_DIR,
    *,
    daemon_py: str = DAEMON_SCRIPT,
    maps: list[str] | None = None,
    idle_timeout: float = 300.0,
    max_clients: int = 32,
    max_inflight: int = 16,
    timeout_s: float = 6.0,
    skip_tracer_check: bool = False,
) -> dict[str, Any]:
    """Single-flight ensure daemon is running natively (or cleanly explain why unavailable)."""
    rdir = Path(runtime_dir)
    paths = runtime_paths(rdir)
    validate_unix_sock_path(paths["sock"])

    if paths["disabled"].exists() or os.environ.get("F8_NO_HYBRID") == "1":
        return {"ok": False, "reason": "global-disabled"}

    rdir.mkdir(parents=True, exist_ok=True)
    os.chmod(rdir, 0o700)
    with open(paths["ctl_lock"], "a+", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        if paths["disabled"].exists():
            return {"ok": False, "reason": "global-disabled"}
        if paths["sock"].exists() and paths["ready"].exists():
            ok, _ = probe_daemon(paths["sock"], timeout_s=1.0)
            if ok:
                return {"ok": True, "action": "already-running", "pid": _read_live_pid(paths["pid"])}

        caller_tracer = read_tracer_pid()
        if caller_tracer == 0 or skip_tracer_check:
            _start_native_direct(
                paths,
                daemon_py,
                maps or [],
                idle_timeout,
                max_clients,
                max_inflight,
                skip_tracer_check,
            )
            ok = _wait_ready(paths["sock"], paths["ready"], timeout_s)
            return {
                "ok": ok,
                "action": "started-direct" if ok else "start-timeout",
                "pid": _read_live_pid(paths["pid"]),
            }

        launched, reason = _start_via_termux_service(
            paths,
            daemon_py,
            maps or [],
            idle_timeout,
            max_clients,
            max_inflight,
        )
        if not launched:
            return {"ok": False, "reason": reason}
        ok = _wait_ready(paths["sock"], paths["ready"], timeout_s)
        return {
            "ok": ok,
            "action": "started-termux-service" if ok else "start-timeout",
            "pid": _read_live_pid(paths["pid"]),
        }


def _with_ctl_lock(runtime_dir: Path, fn):
    paths = runtime_paths(runtime_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(runtime_dir, 0o700)
    with open(paths["ctl_lock"], "a+", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        return fn(paths)


def stop_daemon(runtime_dir: Path, timeout_s: float = 8.0) -> dict[str, Any]:
    def _do(paths: dict[str, Path]) -> dict[str, Any]:
        pid = _read_live_pid(paths["pid"])
        if pid is None:
            return {"ok": True, "action": "not-running"}
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as exc:
            return {"ok": False, "reason": f"kill-failed:{exc}"}
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if _read_live_pid(paths["pid"]) is None and not paths["sock"].exists():
                return {"ok": True, "action": "stopped", "pid": pid}
            time.sleep(0.05)
        return {"ok": False, "action": "stop-timeout", "pid": pid}

    return _with_ctl_lock(runtime_dir, _do)


def set_disabled(runtime_dir: Path, disabled: bool, timeout_s: float = 8.0) -> dict[str, Any]:
    def _do(paths: dict[str, Path]) -> dict[str, Any]:
        if not disabled:
            paths["disabled"].unlink(missing_ok=True)
            return {"ok": True, "disabled": False}
        paths["disabled"].write_text("disabled\n", encoding="utf-8")
        pid = _read_live_pid(paths["pid"])
        if pid is None:
            stop_res = {"ok": True, "action": "not-running"}
        else:
            try:
                os.kill(pid, signal.SIGTERM)
                deadline = time.monotonic() + timeout_s
                stop_res = {"ok": False, "action": "stop-timeout", "pid": pid}
                while time.monotonic() < deadline:
                    if _read_live_pid(paths["pid"]) is None and not paths["sock"].exists():
                        stop_res = {"ok": True, "action": "stopped", "pid": pid}
                        break
                    time.sleep(0.05)
            except OSError as exc:
                stop_res = {"ok": False, "reason": f"kill-failed:{exc}"}
        return {"ok": True, "disabled": True, "stop": stop_res}

    return _with_ctl_lock(runtime_dir, _do)


def client_config_snippets(sock_path: str, relay_path: str = RELAY_SCRIPT) -> dict[str, str]:
    """Generate non-destructive copy-paste config snippets for all supported MCP clients."""
    return {
        "hermes": (
            f"# $HERMES_HOME/config.yaml\nmcp_servers:\n  hybrid2:\n"
            f"    command: /usr/bin/python3\n    args: [{relay_path}, --socket, {sock_path}]\n    enabled: true\n"
        ),
        "codex": (
            f"# $CODEX_HOME/config.toml\n[mcp_servers.hybrid2]\n"
            f'command = "/usr/bin/python3"\nargs = ["{relay_path}", "--socket", "{sock_path}"]\n'
        ),
        "claude-code": (
            f"# Isolated or project MCP registration:\n"
            f"claude mcp add hybrid2 -- /usr/bin/python3 {relay_path} --socket {sock_path}\n"
        ),
        "claude-desktop": json.dumps(
            {"mcpServers": {"hybrid2": {"command": "/usr/bin/python3", "args": [relay_path, "--socket", sock_path]}}},
            indent=2,
        ),
        "antigravity": json.dumps(
            {"mcpServers": {"hybrid2": {"command": "/usr/bin/python3", "args": [relay_path, "--socket", sock_path]}}},
            indent=2,
        ),
        "opencode": json.dumps(
            {"mcp": {"hybrid2": {"type": "local", "command": ["/usr/bin/python3", relay_path, "--socket", sock_path]}}},
            indent=2,
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stage 7.2 universal Native Hybrid 2.0 controller")
    ap.add_argument("--dir", default=os.environ.get("F8_HYBRID2_DIR", DEFAULT_RUNTIME_DIR), help="Runtime directory")
    ap.add_argument("--daemon-py", default=DAEMON_SCRIPT, help="Path to f8_hybrid2_daemon.py")
    ap.add_argument("--map", action="append", default=[], help="Path map GUEST=HOST")
    ap.add_argument("--idle-timeout", type=float, default=300.0, help="Idle auto-shutdown seconds")
    ap.add_argument("--max-clients", type=int, default=32)
    ap.add_argument("--max-inflight", type=int, default=16)
    ap.add_argument("--wait", type=float, default=6.0)
    ap.add_argument("--skip-tracer-check", action="store_true")
    ap.add_argument("--soft", action="store_true", help="Exit 0 even if stripped env prevents PRoot->Termux launch")
    ap.add_argument("--client", default="all", help="Client name for client-config")
    ap.add_argument(
        "action",
        choices=("start", "stop", "restart", "status", "probe", "enable", "disable", "ensure-running", "client-config"),
    )
    args = ap.parse_args(argv)
    rdir = Path(args.dir)
    paths = runtime_paths(rdir)

    if args.action == "status":
        print(json.dumps(get_status(rdir), indent=2))
        return 0
    if args.action == "probe":
        if paths["disabled"].exists() or os.environ.get("F8_NO_HYBRID") == "1":
            print(json.dumps({"ok": False, "detail": "global-disabled"}))
            return 3
        ok, detail = probe_daemon(paths["sock"], timeout_s=min(args.wait, 3.0))
        print(json.dumps({"ok": ok, "detail": detail}))
        return 0 if ok else 2
    if args.action == "enable":
        print(json.dumps(set_disabled(rdir, False, timeout_s=args.wait)))
        return 0
    if args.action == "disable":
        print(json.dumps(set_disabled(rdir, True, timeout_s=args.wait)))
        return 0
    if args.action == "stop":
        res = stop_daemon(rdir, timeout_s=args.wait)
        print(json.dumps(res))
        return 0 if res.get("ok") else 1
    if args.action == "restart":
        def _restart(_paths):
            pid = _read_live_pid(_paths["pid"])
            if pid is not None:
                try:
                    os.kill(pid, signal.SIGTERM)
                    deadline = time.monotonic() + args.wait
                    while time.monotonic() < deadline and (_read_live_pid(_paths["pid"]) is not None or _paths["sock"].exists()):
                        time.sleep(0.05)
                except OSError:
                    pass
            return None

        _with_ctl_lock(rdir, _restart)
        res = ensure_running(
            rdir,
            daemon_py=args.daemon_py,
            maps=args.map,
            idle_timeout=args.idle_timeout,
            max_clients=args.max_clients,
            max_inflight=args.max_inflight,
            timeout_s=args.wait,
            skip_tracer_check=args.skip_tracer_check,
        )
        print(json.dumps(res))
        return 0 if res.get("ok") else 1
    if args.action in ("start", "ensure-running"):
        res = ensure_running(
            rdir,
            daemon_py=args.daemon_py,
            maps=args.map,
            idle_timeout=args.idle_timeout,
            max_clients=args.max_clients,
            max_inflight=args.max_inflight,
            timeout_s=args.wait,
            skip_tracer_check=args.skip_tracer_check,
        )
        print(json.dumps(res))
        if res.get("ok"):
            return 0
        if args.soft and res.get("reason") in ("auto-start-env-stripped", "global-disabled"):
            return 0
        return 1
    if args.action == "client-config":
        snips = client_config_snippets(str(paths["sock"]))
        if args.client == "all":
            print(json.dumps(snips, indent=2))
        elif args.client in snips:
            print(snips[args.client])
        else:
            print(f"unknown client {args.client!r}", file=sys.stderr)
            return 2
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
