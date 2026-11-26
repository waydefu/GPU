#!/data/data/com.termux/files/usr/bin/python3
"""Restart the Stable XFCE session on :1 without touching the X server.

Reusable successor of the one-shot restart-desktop.py (2026-11-27): every pid and
identity is discovered at run time instead of being hard-coded.

Run natively (TracerPid 0), e.g. through termux-bg-run from a session whose env
still has the Android runtime vars:
  restart-stable-desktop.py --dry-run                           # preflight only, sends no signal
  restart-stable-desktop.py --apply --confirm-stable-restart    # real restart (maintenance only)

Never touches the termux-x11 server, the X1 socket or lock, or any other PRoot
tracer (shards such as Claude Desktop survive). Fails closed on any mismatch.
"""
import argparse
import ctypes
import hashlib
import os
import re
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

PREFIX = Path("/data/data/com.termux/files/usr")
TERMUX_HOME = Path("/data/data/com.termux/files/home")
OUT = TERMUX_HOME / "build/proot-fast/out8"
NATIVE_EXE = OUT / "bin/proot-fast8"
X_SOCKET = PREFIX / "tmp/.X11-unix/X1"
X_LOCK = PREFIX / "tmp/.X1-lock"
# termux-x11 packs its whole command line into argv[0]; compare with NULs as spaces.
STABLE_X_CMD = b"termux-x11 com.termux.x11 :1 -legacy-drawing"
TRACER_COMM = "proot-fast8"
AM_REQUIRED_ENV = (
    "ANDROID_ART_ROOT", "ANDROID_I18N_ROOT", "ANDROID_TZDATA_ROOT",
    "ANDROID_ROOT", "ANDROID_DATA", "BOOTCLASSPATH", "DEX2OATBOOTCLASSPATH",
)
LAUNCH = [
    str(PREFIX / "bin/proot-distro"), "login", "ubuntu", "--shared-tmp", "--",
    "/bin/bash", "-lc", "export DISPLAY=:1; exec /usr/local/bin/f8-xfce-session",
]

libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
PIDFD_OPEN_NR, PIDFD_SEND_SIGNAL_NR = 434, 424  # arm64; Termux Python lacks os.pidfd_open


def checked_syscall(number, *args):
    result = libc.syscall(ctypes.c_long(number), *args)
    if result == -1:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return result


def pidfd_open(pid):
    return checked_syscall(PIDFD_OPEN_NR, ctypes.c_int(pid), ctypes.c_uint(0))


def pidfd_signal(fd, sig):
    checked_syscall(PIDFD_SEND_SIGNAL_NR, ctypes.c_int(fd), ctypes.c_int(sig),
                    ctypes.c_void_p(), ctypes.c_uint(0))


def fields(pid):
    return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()


def start_time(pid):
    return int(fields(pid)[19])


def active(pid):
    try:
        return fields(pid)[0] not in ("Z", "X")
    except FileNotFoundError:
        return False


def tracer(pid):
    data = Path(f"/proc/{pid}/status").read_text()
    return int(re.search(r"^TracerPid:\s+(\d+)$", data, re.M)[1])


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cmdline(pid):
    return Path(f"/proc/{pid}/cmdline").read_bytes().rstrip(b"\0").replace(b"\0", b" ")


def members(name=None, trace_id=None, cmd=None):
    pids = []
    for p in Path("/proc").iterdir():
        if not p.name.isdecimal():
            continue
        pid = int(p.name)
        try:
            if not active(pid):
                continue
            if name is not None and (p / "comm").read_text().strip() != name:
                continue
            if trace_id is not None and tracer(pid) != trace_id:
                continue
            if cmd is not None and cmdline(pid) != cmd:
                continue
            pids.append(pid)
        except (OSError, TypeError, ValueError):
            continue
    return sorted(pids)


def wait(predicate, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.15)
    return None


def launch_env(environ):
    """Allowlist: Android runtime vars from the caller + launch overrides. Never os.environ wholesale."""
    missing = [k for k in AM_REQUIRED_ENV if not environ.get(k)]
    if missing:
        raise SystemExit(f"FAIL caller env lacks Android runtime vars: {' '.join(missing)}")
    env = {k: environ[k] for k in AM_REQUIRED_ENV}
    env.update(PATH=f"{PREFIX}/bin:/system/bin", HOME=str(TERMUX_HOME), PREFIX=str(PREFIX),
               TMPDIR=str(PREFIX / "tmp"), PD_PROOT_BIN=str(OUT / "auto/proot-fast8"))
    return env


def env_names(pid):
    data = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
    return {item.split(b"=", 1)[0].decode(errors="replace") for item in data if b"=" in item}


def preflight(environ):
    """Read-only discovery and checks. Sends no signal and writes nothing."""
    assert tracer("self") == 0, "must run natively (TracerPid 0), e.g. via termux-bg-run"
    assert not (TERMUX_HOME / ".f8-proot-stock").exists(), "desktop requested stock proot"
    env = launch_env(environ)
    live_sha = digest(NATIVE_EXE)

    servers = members(cmd=STABLE_X_CMD)
    assert len(servers) == 1, ("expected one Stable X server", servers)
    server = servers[0]
    assert tracer(server) == 0, "Stable X server is traced"
    info = X_SOCKET.stat()
    assert stat.S_ISSOCK(info.st_mode), "X1 socket missing"
    assert int(X_LOCK.read_text().strip()) == server, "X1 lock does not name the server"

    sessions = members(name="xfce4-session")
    assert len(sessions) == 1, ("expected one xfce4-session", sessions)
    session = sessions[0]
    old_tracer = tracer(session)
    assert old_tracer not in (0, server), ("session tracer unexpected", old_tracer)
    survivors = [p for p in members(name=TRACER_COMM) if p != old_tracer]
    tracees = members(trace_id=old_tracer)
    identity = {pid: start_time(pid) for pid in [server, session, old_tracer, *survivors]}
    return dict(env=env, live_sha=live_sha, server=server, x_socket=(info.st_dev, info.st_ino),
                session=session, old_tracer=old_tracer, old_tracer_sha=digest(f"/proc/{old_tracer}/exe"),
                survivors=survivors, old_tracees=len(tracees), identity=identity)


def assert_same(plan, pid):
    assert active(pid) and start_time(pid) == plan["identity"][pid], ("process identity changed", pid)


def assert_stable(plan):
    assert_same(plan, plan["server"])
    assert tracer(plan["server"]) == 0
    assert cmdline(plan["server"]) == STABLE_X_CMD, "Stable command changed"
    info = X_SOCKET.stat()
    assert (info.st_dev, info.st_ino) == plan["x_socket"] and stat.S_ISSOCK(info.st_mode)
    assert int(X_LOCK.read_text().strip()) == plan["server"]


def lost_survivors(plan):
    # Not asserted: a shard (e.g. a terminal opened from the old session) may exit on its own
    # when that session ends. This script only ever signals the session and its own tracer.
    return [p for p in plan["survivors"] if not active(p) or start_time(p) != plan["identity"][p]]


def signal_checked(plan, pid, sig):
    fd = pidfd_open(pid)
    try:
        assert_same(plan, pid)
        pidfd_signal(fd, sig)
    finally:
        os.close(fd)


def restart(plan, run_dir):
    session, old_tracer = plan["session"], plan["old_tracer"]
    signal_checked(plan, session, signal.SIGTERM)
    assert wait(lambda: not active(session), 12), "old XFCE session did not exit"
    if not wait(lambda: not members(trace_id=old_tracer), 10):
        left = []
        for pid in members(trace_id=old_tracer):
            try:
                left.append(f"{pid}:{Path(f'/proc/{pid}/comm').read_text().strip()}")
            except OSError:
                continue
        raise SystemExit(f"FAIL old tracees remain under {old_tracer}: {' '.join(left)}; "
                         f"close them, then relaunch manually: {' '.join(LAUNCH)}")
    assert_stable(plan)
    if active(old_tracer):
        # The idle previous tracer may be the X server's parent; reap only it, bound by pidfd.
        assert digest(f"/proc/{old_tracer}/exe") == plan["old_tracer_sha"]
        signal_checked(plan, old_tracer, signal.SIGKILL)
        assert wait(lambda: not active(old_tracer), 8), "idle previous tracer did not exit"
    assert_stable(plan)

    with (run_dir / "stable-desktop-session.log").open("wb") as log:
        proc = subprocess.Popen(LAUNCH, cwd=TERMUX_HOME, env=plan["env"], stdin=subprocess.DEVNULL,
                                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    print(f"STABLE_DESKTOP_LAUNCH launcher_pid={proc.pid}", flush=True)

    def ready():
        pids = members(name="xfce4-session")
        if len(pids) != 1 or pids[0] == session:
            return None
        try:
            new_tracer = tracer(pids[0])
            if new_tracer in (0, old_tracer, *plan["survivors"]):
                return None
            if digest(f"/proc/{new_tracer}/exe") != plan["live_sha"]:
                return None
            if not members(name="xfwm4", trace_id=new_tracer):
                return None
            env = Path(f"/proc/{pids[0]}/environ").read_bytes().split(b"\0")
            if b"DISPLAY=:1" not in env and b"DISPLAY=:1.0" not in env:
                return None
            return pids[0], new_tracer
        except (OSError, TypeError, ValueError):
            return None

    pair = wait(ready, 24)
    assert pair, f"new Stable XFCE not ready; launcher rc={proc.poll()}"
    new_session, new_tracer = pair
    assert_stable(plan)
    missing = [k for k in AM_REQUIRED_ENV if k not in env_names(new_tracer)]
    (run_dir / "stable-runtime.txt").write_text(
        f"x11_server={plan['server']}\nx1_inode={plan['x_socket'][1]}\nold_xfce_tracer={old_tracer}\n"
        f"new_xfce_session={new_session}\nnew_xfce_tracer={new_tracer}\n"
        f"survivors={','.join(map(str, plan['survivors']))}\n"
        f"survivors_gone={','.join(map(str, lost_survivors(plan))) or 'none'}\nsha256={plan['live_sha']}\n"
        f"android_env_missing={','.join(missing) or 'none'}\n")
    print(f"STABLE_DESKTOP_RESTART_PASS xfce={new_session} tracer={new_tracer} sha256={plan['live_sha']}", flush=True)
    print(f"ANDROID_ENV_IN_NEW_TRACER {'PASS' if not missing else 'FAIL missing=' + ','.join(missing)}", flush=True)
    return 0 if not missing else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="preflight only; sends no signal")
    mode.add_argument("--apply", action="store_true", help="really restart the Stable XFCE session")
    ap.add_argument("--confirm-stable-restart", action="store_true", help="required with --apply")
    ap.add_argument("--run-dir", type=Path, help="where logs go (default: $PREFIX/tmp/stable-restart-<ts>)")
    args = ap.parse_args(argv)
    if args.apply and not args.confirm_stable_restart:
        print("FAIL --apply needs --confirm-stable-restart", file=sys.stderr)
        return 2

    plan = preflight(os.environ)
    print(f"STABLE_BASELINE xserver={plan['server']} socket_inode={plan['x_socket'][1]} "
          f"session={plan['session']} desktop_tracer={plan['old_tracer']} "
          f"survivor_tracers={','.join(map(str, plan['survivors'])) or 'none'} "
          f"old_tracees={plan['old_tracees']} live_sha256={plan['live_sha']} "
          f"desktop_tracer_sha256={plan['old_tracer_sha']}", flush=True)
    test_fd = pidfd_open(os.getpid())
    try:
        pidfd_signal(test_fd, 0)
    finally:
        os.close(test_fd)
    print("NATIVE_PIDFD_PROBE_PASS", flush=True)
    if args.dry_run:
        print("STABLE_RESTART_DRYRUN_PASS (no signal sent)", flush=True)
        return 0

    run_dir = args.run_dir or PREFIX / f"tmp/stable-restart-{time.strftime('%Y%m%d-%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return restart(plan, run_dir)


if __name__ == "__main__":
    sys.exit(main())
