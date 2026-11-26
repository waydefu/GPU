#!/usr/bin/env python3
"""Non-destructive guard test for the 2026-11-27 Termux `am` env bug (run on the F8, inside PRoot).

Never restarts or signals the Stable desktop and never launches TermuxService:
1. termux-bg-run refuses with exit 4 before creating a wrapper or calling `am`.
2. restart-desktop.py's env block, executed alone from the parsed source:
   passes exactly the 7 Android vars + 5 overrides (no caller secrets, LD_*, PROOT_*),
   and asserts when any Android var is missing.
3. That check runs before the first pidfd_open/SIGTERM/Popen in the script.
4. Run whole outside its run dir, the script exits non-zero and the Stable X server
   and XFCE session keep the same pid and start time.
"""
import ast
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "scripts"
BG_RUN = HERE / "termux-bg-run"
RESTART = HERE / "restart-desktop.py"
TERMUX_TMP = Path("/data/data/com.termux/files/usr/tmp")
REQUIRED = ("ANDROID_ART_ROOT", "ANDROID_I18N_ROOT", "ANDROID_TZDATA_ROOT",
            "ANDROID_ROOT", "ANDROID_DATA", "BOOTCLASSPATH", "DEX2OATBOOTCLASSPATH")
OVERRIDES = {"PATH", "HOME", "PREFIX", "TMPDIR", "PD_PROOT_BIN"}
# termux-x11 packs its whole command line into argv[0] with spaces; normalize NULs first.
STABLE_X = b"termux-x11 com.termux.x11 :1 -legacy-drawing"


def bg_run(env):
    with tempfile.NamedTemporaryFile("w", dir=TERMUX_TMP, suffix=".sh", delete=False) as f:
        f.write("#!/bin/sh\nexit 0\n")
    try:
        return subprocess.run([sys.executable, str(BG_RUN), "--timeout", "5", f.name],
                              env=env, capture_output=True, text=True, timeout=20)
    finally:
        os.unlink(f.name)


def test_bg_run():
    base = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    r = bg_run(base)
    assert r.returncode == 4, (r.returncode, r.stderr)
    assert all(k in r.stderr for k in REQUIRED), r.stderr
    r = bg_run(dict(base, BOOTCLASSPATH="x", ANDROID_ROOT="/system", ANDROID_DATA="/data"))
    assert r.returncode == 4, (r.returncode, r.stderr)
    listed = set(r.stderr.split("missing env:")[1].split(".")[0].split())
    assert listed == {"ANDROID_ART_ROOT", "ANDROID_I18N_ROOT", "ANDROID_TZDATA_ROOT",
                      "DEX2OATBOOTCLASSPATH"}, listed


def env_block(tree):
    body = tree.body
    start = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign)
                 and any(getattr(t, "id", None) == "AM_REQUIRED_ENV" for t in n.targets))
    # Take only the consecutive assignments/asserts/env.update() that follow.
    block = []
    for n in body[start:]:
        is_update = (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                     and getattr(n.value.func, "attr", None) == "update")
        if not (isinstance(n, (ast.Assign, ast.Assert)) or is_update):
            break
        block.append(n)
    module = ast.Module(body=block, type_ignores=[])
    called = {getattr(c.func, "id", getattr(c.func, "attr", None))
              for c in ast.walk(module) if isinstance(c, ast.Call)}
    assert not called & {"Popen", "run", "pidfd_open", "pidfd_signal", "kill", "system"}, called
    return module


def run_env_block(block, caller_env):
    ns = {"os": types.SimpleNamespace(environ=caller_env), "prefix": Path("/p"),
          "termux_home": Path("/h"), "out": Path("/o")}
    exec(compile(block, str(RESTART), "exec"), ns)
    return ns["env"]


def test_restart_env(tree):
    block = env_block(tree)
    android = {k: f"v-{k}" for k in REQUIRED}
    caller = dict(android, SECRET_TOKEN="do-not-leak", LD_PRELOAD="/x.so",
                  PROOT_NO_SECCOMP="1", DISPLAY=":9")
    env = run_env_block(block, caller)
    assert set(env) == set(REQUIRED) | OVERRIDES, sorted(env)
    assert all(env[k] == android[k] for k in REQUIRED)
    assert env["PD_PROOT_BIN"] == "/o/auto/proot-fast8"
    for drop in REQUIRED:
        try:
            run_env_block(block, {k: v for k, v in caller.items() if k != drop})
        except AssertionError as e:
            assert drop in str(e), e
        else:
            raise AssertionError(f"missing {drop} was not rejected")


def first_call(tree, name, arg_attr=None):
    lines = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
             and getattr(n.func, "id", getattr(n.func, "attr", None)) == name
             and (arg_attr is None or any(getattr(a, "attr", None) == arg_attr for a in n.args))]
    return min(lines)


def test_restart_order(tree):
    guard = next(n.lineno for n in tree.body if isinstance(n, ast.Assert)
                 and "missing_env" in ast.unparse(n.test))
    session_open = min(n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                       and getattr(n.func, "id", None) == "pidfd_open"
                       and ast.unparse(n.args[0]) == "session")
    assert guard < session_open, ("env check after pidfd_open(session)", guard, session_open)
    assert guard < first_call(tree, "pidfd_signal", "SIGTERM"), "env check after SIGTERM"
    assert guard < first_call(tree, "Popen"), "env check after launch"


def stable_identity():
    found = {}
    for p in Path("/proc").iterdir():
        if not p.name.isdecimal():
            continue
        try:
            cmd = (p / "cmdline").read_bytes().rstrip(b"\0").replace(b"\0", b" ")
            comm = (p / "comm").read_text().strip()
            start = (p / "stat").read_text().rsplit(")", 1)[1].split()[19]
        except OSError:
            continue
        if cmd == STABLE_X:
            found.setdefault("x1", []).append((p.name, start))
        elif comm == "xfce4-session":
            found.setdefault("xfce", []).append((p.name, start))
    return found


def test_restart_fails_closed():
    # Safety: refuse if this copy sits in a real run dir.
    assert not (HERE / "live-candidate-sha256").exists(), "refusing: looks like a live run dir"
    before = stable_identity()
    assert before.get("x1"), "Stable X server not found; refusing to judge"
    r = subprocess.run([sys.executable, str(RESTART)], capture_output=True, text=True,
                       timeout=30, cwd=tempfile.gettempdir())
    after = stable_identity()
    assert r.returncode != 0, ("restart-desktop.py ran outside its run dir", r.stdout)
    assert "STABLE_DESKTOP_LAUNCH" not in r.stdout and "NATIVE_PIDFD_PROBE_PASS" not in r.stdout, r.stdout
    assert before == after, ("Stable identity changed", before, after)


def main():
    if not TERMUX_TMP.is_dir():
        print("SKIP: not on the Termux host")
        return 0
    tree = ast.parse(RESTART.read_text())
    test_bg_run()
    test_restart_env(tree)
    test_restart_order(tree)
    test_restart_fails_closed()
    print("ANDROID_ENV_GUARD_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
