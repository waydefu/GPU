#!/usr/bin/env python3
"""Double-fork + setsid launcher for experimental f8-x11gpu :3 only.
Does not touch Stable :1. Parent reaps the intermediate child and exits.
"""
import os
import sys

LOG = os.environ.get(
    "GATEA_X3_LAUNCHER_LOG",
    "/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/r0/x3-launcher.raw.log",
)
ARGV = [
    "/data/data/com.termux/files/usr/bin/bash",
    "-lc",
    "exec /data/data/com.termux/files/usr/bin/f8-x11gpu :3",
]

pid = os.fork()
if pid > 0:
    os.waitpid(pid, 0)
    print(f"launcher_intermediate_reaped={pid}")
    raise SystemExit(0)
os.setsid()
pid2 = os.fork()
if pid2 > 0:
    os._exit(0)
os.chdir("/")
os.makedirs(os.path.dirname(LOG), exist_ok=True)
fd = os.open(LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
os.dup2(fd, 1)
os.dup2(fd, 2)
os.close(fd)
nulfd = os.open("/dev/null", os.O_RDONLY)
os.dup2(nulfd, 0)
os.close(nulfd)
env = os.environ.copy()
env.update(
    {
        "HOME": "/data/data/com.termux/files/home",
        "PATH": "/data/data/com.termux/files/usr/bin:/system/bin:/system/xbin",
        "DISPLAY": ":3",
        "TMPDIR": "/data/data/com.termux/files/usr/tmp",
    }
)
# Never force PROTO here. Caller may export TERMUX_X11_GATEA_PROTO / TELEMETRY.
os.execvpe(ARGV[0], ARGV, env)
