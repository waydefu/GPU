#!/data/data/com.termux/files/usr/bin/python3
import ctypes
import hashlib
import os
import re
import signal
import stat
import subprocess
import time
from pathlib import Path

run = Path(__file__).resolve().parent
prefix = Path("/data/data/com.termux/files/usr")
termux_home = Path("/data/data/com.termux/files/home")
out = termux_home / "build/proot-fast/out8"
native_exe = out / "bin/proot-fast8"
old_sha = "2524856b351a740021c189a32bbf94c7393af51e5ef4f6dcb304833c8e313af3"
new_sha = (run / "live-candidate-sha256").read_text().strip()
old_tracer, session, server, codex_tracer = 30164, 30336, 30202, 22266
identity = {old_tracer: 210452300, session: 210452614, server: 210452373, codex_tracer: 210666965}
socket = prefix / "tmp/.X11-unix/X1"


# Termux Python omits pidfd wrappers, but the native ARM64 headers expose
# these syscalls. Probe both with signal 0 before touching the desktop.
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
pidfd_open_nr = 434
pidfd_send_signal_nr = 424


def checked_syscall(number, *args):
    result = libc.syscall(ctypes.c_long(number), *args)
    if result == -1:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return result


def pidfd_open(pid):
    return checked_syscall(pidfd_open_nr, ctypes.c_int(pid), ctypes.c_uint(0))


def pidfd_signal(fd, sig):
    checked_syscall(pidfd_send_signal_nr, ctypes.c_int(fd), ctypes.c_int(sig),
                    ctypes.c_void_p(), ctypes.c_uint(0))


def process_fields(pid):
    return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()


def active(pid):
    try:
        return process_fields(pid)[0] not in ("Z", "X")
    except FileNotFoundError:
        return False


def assert_original(pid):
    assert active(pid) and int(process_fields(pid)[19]) == identity[pid], ("process identity changed", pid)


def tracer(pid):
    data = Path(f"/proc/{pid}/status").read_text()
    return int(re.search(r"^TracerPid:\s+(\d+)$", data, re.M)[1])


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def members(name=None, trace_id=None):
    pids = []
    for p in Path("/proc").iterdir():
        if not p.name.isdecimal():
            continue
        try:
            if not active(int(p.name)):
                continue
            if name is not None and (p / "comm").read_text().strip() != name:
                continue
            if trace_id is not None and tracer(int(p.name)) != trace_id:
                continue
            pids.append(int(p.name))
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


def assert_server():
    assert_original(server)
    assert tracer(server) == 0
    cmd = Path(f"/proc/{server}/cmdline").read_bytes().split(b"\0", 1)[0]
    assert cmd == b"termux-x11 com.termux.x11 :1 -legacy-drawing", "Stable command changed"
    info = socket.stat()
    assert (info.st_dev, info.st_ino) == x_socket_id and stat.S_ISSOCK(info.st_mode)
    assert int((prefix / "tmp/.X1-lock").read_text().strip()) == server


def ready():
    pids = members(name="xfce4-session")
    if len(pids) != 1 or pids[0] == session:
        return None
    try:
        new_session = pids[0]
        target_tracer = tracer(new_session)
        if target_tracer == 0 or target_tracer in (old_tracer, codex_tracer):
            return None
        if digest(f"/proc/{target_tracer}/exe") != new_sha:
            return None
        if not members(name="xfwm4", trace_id=target_tracer):
            return None
        env = Path(f"/proc/{new_session}/environ").read_bytes().split(b"\0")
        if b"DISPLAY=:1" not in env and b"DISPLAY=:1.0" not in env:
            return None
        return new_session, target_tracer
    except (OSError, TypeError, ValueError):
        return None


assert tracer("self") == 0
assert digest(native_exe) == new_sha
assert not (termux_home / ".f8-proot-stock").exists(), "desktop requested stock proot"
for pid in identity:
    assert_original(pid)
assert tracer(session) == old_tracer
assert tracer(codex_tracer) == 0
assert digest(f"/proc/{old_tracer}/exe") == old_sha
assert digest(f"/proc/{codex_tracer}/exe") == old_sha
assert Path(f"/proc/{session}/comm").read_text().strip() == "xfce4-session"
x = socket.stat()
x_socket_id = x.st_dev, x.st_ino
assert_server()

# Pass through only the Android runtime vars from the caller (a TermuxService
# child), plus the launch overrides. A fresh dict without them on 2026-11-27 made
# Termux `am` inside the new desktop exit 0 without sending intents. An allowlist,
# not os.environ, keeps caller secrets and LD_*/PROOT_* out of the Stable desktop.
# Checked before touching the running desktop.
AM_REQUIRED_ENV = (
    "ANDROID_ART_ROOT", "ANDROID_I18N_ROOT", "ANDROID_TZDATA_ROOT",
    "ANDROID_ROOT", "ANDROID_DATA", "BOOTCLASSPATH", "DEX2OATBOOTCLASSPATH",
)
missing_env = [k for k in AM_REQUIRED_ENV if not os.environ.get(k)]
assert not missing_env, ("caller env lacks Android runtime vars", missing_env)
env = {k: os.environ[k] for k in AM_REQUIRED_ENV}
env.update(
    PATH=f"{prefix}/bin:/system/bin",
    HOME=str(termux_home),
    PREFIX=str(prefix),
    TMPDIR=str(prefix / "tmp"),
    PD_PROOT_BIN=str(out / "auto/proot-fast8"),
)

print(f"STABLE_BASELINE xserver={server} socket_inode={x.st_ino} desktop_tracer={old_tracer} codex_tracer={codex_tracer}", flush=True)

test_fd = pidfd_open(os.getpid())
try:
    pidfd_signal(test_fd, 0)
finally:
    os.close(test_fd)
print("NATIVE_PIDFD_PROBE_PASS", flush=True)
fd = pidfd_open(session)
try:
    assert_original(session)
    pidfd_signal(fd, signal.SIGTERM)
finally:
    os.close(fd)
assert wait(lambda: not active(session), 12), "old XFCE session did not exit"
assert wait(lambda: not members(trace_id=old_tracer), 10), "unexpected old tracees remain"
assert_server()

if active(old_tracer):
    # The previous PRoot was also the parent of the untraced X11 server.
    # Reap only this now-idle tracer, with identity bound by its pidfd.
    fd = pidfd_open(old_tracer)
    try:
        assert_original(old_tracer)
        assert digest(f"/proc/{old_tracer}/exe") == old_sha
        assert not members(trace_id=old_tracer)
        pidfd_signal(fd, signal.SIGKILL)
    finally:
        os.close(fd)
    assert wait(lambda: not active(old_tracer), 8), "idle previous tracer did not exit"
assert_server()
assert_original(codex_tracer)

command = [
    str(prefix / "bin/proot-distro"), "login", "ubuntu", "--shared-tmp", "--",
    "/bin/bash", "-lc", "export DISPLAY=:1; exec /usr/local/bin/f8-xfce-session",
]
with (run / "stable-desktop-session.log").open("wb") as log:
    proc = subprocess.Popen(command, cwd=termux_home, env=env, stdin=subprocess.DEVNULL,
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    print(f"STABLE_DESKTOP_LAUNCH launcher_pid={proc.pid}", flush=True)
    pair = wait(ready, 24)
    assert pair, f"new stable XFCE not ready; launcher rc={proc.poll()}"
new_session, new_tracer = pair
assert_server()
assert_original(codex_tracer)
(run / "stable-runtime.txt").write_text(
    f"x11_server={server}\nx1_inode={x.st_ino}\nold_xfce_tracer={old_tracer}\n"
    f"new_xfce_session={new_session}\nnew_xfce_tracer={new_tracer}\n"
    f"codex_tracer={codex_tracer}\nsha256={new_sha}\n"
)
print(f"STABLE_DESKTOP_RESTART_PASS xfce={new_session} tracer={new_tracer} sha256={new_sha}", flush=True)
