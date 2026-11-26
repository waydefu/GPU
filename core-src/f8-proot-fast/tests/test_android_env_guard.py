#!/usr/bin/env python3
"""Local guard test for the 2026-11-27 Termux `am` env bug (run on the F8, inside PRoot).

termux-bg-run must refuse (exit 4) before launching anything when the Android
runtime env is missing, and restart-desktop.py must inherit the caller env and
check it before it signals the running desktop. Never launches TermuxService.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "scripts"
BG_RUN = HERE / "termux-bg-run"
RESTART = HERE / "restart-desktop.py"
TERMUX_TMP = Path("/data/data/com.termux/files/usr/tmp")
REQUIRED = ("ANDROID_ART_ROOT", "ANDROID_I18N_ROOT", "ANDROID_TZDATA_ROOT",
            "ANDROID_ROOT", "ANDROID_DATA", "BOOTCLASSPATH", "DEX2OATBOOTCLASSPATH")


def bg_run(env):
    with tempfile.NamedTemporaryFile("w", dir=TERMUX_TMP, suffix=".sh", delete=False) as f:
        f.write("#!/bin/sh\nexit 0\n")
    try:
        return subprocess.run([sys.executable, str(BG_RUN), "--timeout", "5", f.name],
                              env=env, capture_output=True, text=True, timeout=20)
    finally:
        os.unlink(f.name)


def main():
    if not TERMUX_TMP.is_dir():
        print("SKIP: not on the Termux host")
        return 0
    base = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}

    r = bg_run(base)
    assert r.returncode == 4, (r.returncode, r.stderr)
    assert all(k in r.stderr for k in REQUIRED), r.stderr

    partial = dict(base, BOOTCLASSPATH="x", ANDROID_ROOT="/system", ANDROID_DATA="/data")
    r = bg_run(partial)
    assert r.returncode == 4, (r.returncode, r.stderr)
    listed = set(r.stderr.split("missing env:")[1].split(".")[0].split())
    assert listed == {"ANDROID_ART_ROOT", "ANDROID_I18N_ROOT", "ANDROID_TZDATA_ROOT",
                      "DEX2OATBOOTCLASSPATH"}, listed

    src = RESTART.read_text()
    assert "dict(\n    os.environ," in src, "restart-desktop.py must inherit os.environ"
    guard = src.index("assert not missing_env")
    assert guard < src.index("pidfd_signal(fd, signal.SIGTERM)"), "env check must precede SIGTERM"
    assert guard < src.index("subprocess.Popen("), "env check must precede launch"
    print("ANDROID_ENV_GUARD_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
