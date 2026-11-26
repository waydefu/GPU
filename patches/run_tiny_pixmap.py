#!/usr/bin/env python3
"""Fresh 3/3 tiny-pixmap ladder on experimental :3. Never starts xfwm. Never touches Stable."""
import datetime
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVDIR = None
TESTER = "/tmp/p-tiny-pixmap"
XLOG = "/tmp/x11gpu-tiny-x.log"
LCLOG = "/tmp/x11gpu-tiny-logcat.txt"
LAUNCHER = "/data/data/com.termux/files/usr/bin/f8-x11gpu"
ADB = "/data/data/com.termux/files/usr/bin/adb"
ADB_LANE = (ADB, "-H", "127.0.0.1", "-P", "5038")
STABLE_X = (b"termux-x11", b"com.termux.x11", b":1", b"-legacy-drawing")
STABLE_DESKTOP = (b"xfce4-session", b"xfwm4")
STAGES = ("register", "solid", "copy", "multi")


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def log(msg):
    line = f"{now()} {msg}"
    print(line, flush=True)
    os.makedirs(EVDIR, exist_ok=True)
    with open(os.path.join(EVDIR, "run.txt"), "a") as f:
        f.write(line + "\n")


def find_x3():
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode().strip()
        except Exception:
            continue
        if cmd.split()[:3] == ["termux-x11gpu", "com.waydefu.x11gpu", ":3"]:
            return int(pid)
    return None


def find_xfwm3():
    hits = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode().strip()
        except Exception:
            continue
        if cmd.startswith("xfwm4") and (":3" in cmd or "--display=:3" in cmd or "--display :3" in cmd):
            hits.append((int(pid), cmd))
    return hits


def ppid_of(pid):
    try:
        return int(open(f"/proc/{pid}/stat").read().split()[3])
    except Exception:
        return None


def process_identity(process):
    fields = (process / "stat").read_bytes().rsplit(b")", 1)[1].split()
    if fields[0] == b"Z":
        return None
    return int(process.name), int(fields[19])


def stable_snapshot(proc=Path("/proc"), lock=Path("/tmp/.X1-lock"), socket=Path("/tmp/.X11-unix/X1")):
    try:
        pid = int(lock.read_text().strip())
        server = proc / str(pid)
        argv = (server / "cmdline").read_bytes().replace(b"\0", b" ").split()
        sock = socket.stat()
        if tuple(argv[:4]) != STABLE_X or not stat.S_ISSOCK(sock.st_mode):
            return None
        x11 = process_identity(server)
        desktop = {name: [] for name in STABLE_DESKTOP}
        for process in proc.iterdir():
            if not process.name.isdecimal():
                continue
            try:
                command = (process / "cmdline").read_bytes().split(b"\0", 1)[0]
                name = os.path.basename(command)
                if name not in desktop:
                    continue
                env = (process / "environ").read_bytes().split(b"\0")
                if b"DISPLAY=:1" in env or b"DISPLAY=:1.0" in env:
                    identity = process_identity(process)
                    if identity:
                        desktop[name].append(identity)
            except (OSError, IndexError, ValueError):
                continue
        if not x11 or any(len(identities) != 1 for identities in desktop.values()):
            return None
        return x11, tuple(desktop[name][0] for name in STABLE_DESKTOP), (sock.st_dev, sock.st_ino)
    except (OSError, IndexError, ValueError):
        return None


def xdpy_ok():
    env = os.environ.copy()
    env["DISPLAY"] = ":3"
    r = subprocess.run(["xdpyinfo"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def kill_x3():
    pid = find_x3()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        for _ in range(20):
            if find_x3() is None:
                break
            time.sleep(0.1)
        if find_x3():
            try:
                os.kill(find_x3(), signal.SIGKILL)
            except (ProcessLookupError, TypeError):
                pass
            time.sleep(0.2)
    for p in ("/tmp/.X11-unix/X3", "/tmp/.X3-lock"):
        try:
            os.remove(p)
        except FileNotFoundError:
            pass


def daemonize_exec(log_path, argv, env=None):
    pid = os.fork()
    if pid > 0:
        os.waitpid(pid, 0)
        return
    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)
    os.chdir("/")
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)
    nulfd = os.open("/dev/null", os.O_RDONLY)
    os.dup2(nulfd, 0)
    os.close(nulfd)
    env = os.environ.copy() if env is None else env.copy()
    env.pop("DISPLAY", None)
    env.pop("MESA_LOADER_DRIVER_OVERRIDE", None)
    env.pop("VK_ICD_FILENAMES", None)
    os.execvpe(argv[0], argv, env)


def start_activity(adb, env):
    subprocess.run(
        [
            *adb,
            "shell",
            "cmd",
            "activity",
            "start-activity",
            "--display",
            "0",
            "--windowingMode",
            "1",
            "-f",
            "0x20020000",
            "-n",
            "com.waydefu.x11gpu/com.termux.x11.MainActivity",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=8,
    )


def start_x3(adb, env):
    kill_x3()
    start_activity(adb, env)
    time.sleep(0.8)
    daemonize_exec(XLOG, [LAUNCHER, ":3"])
    deadline = time.time() + 15
    while time.time() < deadline:
        pid = find_x3()
        if pid and ppid_of(pid) == 1 and xdpy_ok():
            time.sleep(1.0)
            return pid
        time.sleep(0.2)
    return None


def snapshot_logcat(tag, adb, env):
    path = os.path.join(EVDIR, f"{tag}.logcat.txt")
    try:
        out = subprocess.check_output(
            [*adb, "logcat", "-d", "-v", "threadtime", "-t", "200"],
            env=env, stderr=subprocess.STDOUT, timeout=8,
        )
    except Exception as e:
        with open(path, "w") as f:
            f.write(f"logcat dump failed: {e}\n")
        return path
    text = out.decode("utf-8", "replace")
    with open(path, "w") as f:
        f.write(text)
    return path


def classify_logcat(path, xpid):
    sent1 = False
    segsv = False
    lines = []
    try:
        data = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except Exception:
        data = []
    needle = str(xpid) if xpid else ""
    for ln in data:
        if needle and needle not in ln and "Fatal signal" not in ln and "Sent shared buffer" not in ln:
            continue
        if "Sent shared buffer width 1" in ln:
            sent1 = True
            lines.append(ln)
        if "Fatal signal 11" in ln or "SIGSEGV" in ln or "handling signal: 11" in ln:
            segsv = True
            lines.append(ln)
        if "Sent shared buffer" in ln:
            lines.append(ln)
    return sent1, segsv, lines[-20:]


def run_tester(stage):
    env = os.environ.copy()
    env["DISPLAY"] = ":3"
    env.pop("CPATH", None)
    env.pop("C_INCLUDE_PATH", None)
    env.pop("PKG_CONFIG_PATH", None)
    env.pop("MESA_LOADER_DRIVER_OVERRIDE", None)
    env.pop("VK_ICD_FILENAMES", None)
    try:
        p = subprocess.run([TESTER, stage], env=env, capture_output=True, text=True, timeout=15)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
        return 124, out + "\nTIMEOUT\n"


def write_trial(stage, trial, body):
    path = os.path.join(EVDIR, f"{stage}-t{trial}.txt")
    with open(path, "w") as f:
        f.write(body)
    return path


def network_serial(serial):
    host, _, port = serial.rpartition(":")
    return (
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*|\[[A-Fa-f0-9:]+\]", host)
        and re.fullmatch(r"[0-9]{1,5}", port)
        and 0 < int(port) <= 65535
    )


def adb_target():
    env = os.environ.copy()
    serial = (env.get("ADB_SERIAL") or env.get("ANDROID_SERIAL") or "").strip()
    for key in ("ADB_SERVER_SOCKET", "ANDROID_ADB_SERVER_ADDRESS", "ANDROID_ADB_SERVER_PORT", "ANDROID_SERIAL"):
        env.pop(key, None)

    if not serial:
        devices = subprocess.check_output([*ADB_LANE, "devices"], env=env, text=True, timeout=8)
        candidates = [
            parts[0] for line in devices.splitlines()
            if len(parts := line.split()) >= 2 and parts[1] == "device" and network_serial(parts[0])
        ]
        if len(candidates) != 1:
            raise RuntimeError("Expected one online network device on the isolated ADB server")
        serial = candidates[0]
    if not network_serial(serial):
        raise RuntimeError("Expected network ADB serial in host:port form")
    adb = (*ADB_LANE, "-s", serial)
    if subprocess.check_output([*adb, "get-state"], env=env, text=True, timeout=8).strip() != "device":
        raise RuntimeError("Selected device is not online on the isolated ADB server")
    device = subprocess.check_output(
        [*adb, "shell", "getprop", "ro.product.device"], env=env, text=True, timeout=8,
    ).strip()
    if device != "myron":
        raise RuntimeError("Selected device is not the POCO F8 Ultra")
    return adb, env


def main():
    global EVDIR
    requested = os.environ.get("TINY_PIXMAP_EVDIR")
    if requested:
        Path(requested).mkdir(parents=True, exist_ok=False)
        EVDIR = requested
    else:
        session = ROOT / "evidence/session"
        session.mkdir(parents=True, exist_ok=True)
        EVDIR = tempfile.mkdtemp(prefix="tiny-pixmap-", dir=session)
    if find_xfwm3():
        log("REFUSE: xfwm already on :3 — abort, do not start another")
        return 2
    stable = stable_snapshot()
    if stable is None:
        log("FATAL cannot identify Stable :1")
        return 2
    try:
        adb, env = adb_target()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        log(f"REFUSE: isolated ADB preflight failed ({type(error).__name__})")
        return 2
    daemonize_exec(LCLOG, [*adb, "logcat", "-v", "threadtime"], env=env)
    log("tiny-pixmap ladder start (no xfwm)")

    results = {}
    for stage in STAGES:
        wins = 0
        for trial in range(1, 4):
            if stable_snapshot() != stable:
                log("FATAL stable died — freeze")
                return 2
            if find_xfwm3():
                log("REFUSE xfwm appeared — freeze")
                return 2
            log(f"=== {stage} trial {trial}/3 fresh X ===")
            try:
                xpid = start_x3(adb, env)
            except (OSError, subprocess.SubprocessError) as error:
                log(f"FATAL experimental activity failed ({type(error).__name__})")
                return 2
            alive_before = bool(xpid and os.path.isdir(f"/proc/{xpid}") and xdpy_ok())
            proto = "DOWN"
            if alive_before:
                rc, out = run_tester(stage)
                proto = "PASS" if rc == 0 else "FAIL"
            else:
                rc, out = -1, "X did not come up\n"
            x_after = find_x3()
            x_alive = bool(x_after and os.path.isdir(f"/proc/{x_after}") and xdpy_ok())
            lcpath = snapshot_logcat(f"{stage}-t{trial}", adb, env)
            sent1, segsv, hits = classify_logcat(lcpath, xpid)
            stable_unchanged = stable_snapshot() == stable
            verdict = "PASS" if proto == "PASS" and x_alive and stable_unchanged else "FAIL"
            if verdict == "PASS":
                wins += 1
            body = (
                f"stage={stage} trial={trial}\n"
                f"T={now()}\n"
                f"xpid={xpid} ppid={ppid_of(xpid) if xpid else None}\n"
                f"x_before={alive_before} x_after={x_alive} after_pid={x_after}\n"
                f"tester_rc={rc} proto={proto} verdict={verdict}\n"
                f"sent_shared_1x1={sent1} sigsegv={segsv}\n"
                f"xfwm={find_xfwm3()}\n"
                f"stable={stable_unchanged}\n"
                f"--- tester ---\n{out}\n"
                f"--- logcat hits ---\n" + "\n".join(hits) + "\n"
            )
            write_trial(stage, trial, body)
            log(f"{stage} t{trial} {verdict} proto={proto} x_alive={x_alive} sent1={sent1} segsv={segsv} xpid={xpid}")
            if not x_alive and xpid:
                freeze = os.path.join(EVDIR, f"freeze-{stage}-t{trial}.txt")
                with open(freeze, "w") as f:
                    f.write(body)
                    f.write(f"freeze logcat={lcpath}\nNO RESTART of this X instance\n")
                log(f"FROZE first-failure of this instance → {freeze}")
            if not stable_unchanged or not alive_before or not x_alive:
                log("FATAL display identity or experimental lifecycle changed — no retry")
                return 2
            # A completed trial permits teardown of this experimental X only.
            kill_x3()
            if stable_snapshot() != stable:
                log("FATAL stable after kill_x3")
                return 2
        results[stage] = wins
        log(f"STAGE {stage} {wins}/3")
        if wins < 3:
            log(f"STOP ladder at {stage} ({wins}/3)")
            break

    summary = os.path.join(EVDIR, "summary.txt")
    with open(summary, "w") as f:
        f.write(f"T={now()}\nno_xfwm=1\n")
        for st in STAGES:
            f.write(f"{st}={results.get(st, 'not-run')}/3\n")
    log(f"done {results}")
    return 0 if all(results.get(st, 0) == 3 for st in STAGES) else 1


if __name__ == "__main__":
    sys.exit(main())
