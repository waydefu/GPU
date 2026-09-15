# U4-C1 Crash Forensic — preflight checkpoint

- Timestamp: `2026-09-10T17:00:38+08:00`
- Scope: Experimental `com.waydefu.x11gpu`, `DISPLAY=:3` only; no workload; no source mutation.
- Stable `com.termux.x11` / `DISPLAY=:1`: not queried or touched in this round.
- Source worktree: pre-existing modifications observed; no file was changed by C1.
- Local frozen-artifact paths referenced by prior evidence were absent from the current filesystem:
  - `/tmp/s3-q1-artifact-34396950445/termux-x11-universal-debug.apk`
  - `/tmp/s3-q1-artifact-34396950445/lib/arm64-v8a/libXlorie.so`
  - `/tmp/ci-r3-libs/01x55434/obj/arm64-v8a/libXlorie.so`
  - `/tmp/s3-qualification-snapshot/lorie/build/intermediates/cxx/Debug/01x55434/obj/arm64-v8a/libXlorie.so`
- Fresh ADB preflight attempt was blocked before any device query. Command:

```text
PATH=/data/data/com.termux/files/usr/bin:/system/bin:/system/xbin HOME=/data/data/com.termux/files/home /data/data/com.termux/files/usr/bin/f8-adb-port
```

- Command exit code: `1`.
- Captured terminal output ended with:

```text
File "/data/data/com.termux/files/usr/lib/python3.14/site-packages/ifaddr/_posix.py", line 47, in <module>
  libc = ctypes.CDLL(ctypes.util.find_library("socket" if os.uname()[0] == "SunOS" else "c"), use_errno=True)
File "/data/data/com.termux/files/usr/lib/python3.14/ctypes/__init__.py", line 433, in __init__
  self._handle = _dlopen(name, mode, handle, winmode)
OSError: dlopen failed: library "libc.so.6" not found
```

Status: `ADB_FRESH_PREFLIGHT_BLOCKED`; do not use the remembered `192.168.1.101:45279` as fresh evidence, do not launch, and do not run `debuggerd` until a native-Termux fresh endpoint is returned.
