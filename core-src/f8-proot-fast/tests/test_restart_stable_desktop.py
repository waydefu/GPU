#!/usr/bin/env python3
"""Non-destructive test for scripts/restart-stable-desktop.py (run on the F8, inside PRoot).

Never sends a signal and never launches a desktop. --apply is only exercised without
its confirmation flag, which must be refused before any discovery.
"""
import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
SCRIPT = SCRIPTS / "restart-stable-desktop.py"
REQUIRED = ("ANDROID_ART_ROOT", "ANDROID_I18N_ROOT", "ANDROID_TZDATA_ROOT",
            "ANDROID_ROOT", "ANDROID_DATA", "BOOTCLASSPATH", "DEX2OATBOOTCLASSPATH")
OVERRIDES = {"PATH", "HOME", "PREFIX", "TMPDIR", "PD_PROOT_BIN"}
STABLE_X = b"termux-x11 com.termux.x11 :1 -legacy-drawing"
DANGEROUS = {"pidfd_signal", "Popen", "kill", "killpg", "system", "signal_checked", "restart"}


def load():
    spec = importlib.util.spec_from_file_location("restart_stable_desktop", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # module level only defines constants and functions
    return mod


def calls(node):
    return {getattr(c.func, "id", getattr(c.func, "attr", None))
            for c in ast.walk(node) if isinstance(c, ast.Call)}


def func(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def test_env(mod):
    caller = {k: f"v-{k}" for k in REQUIRED}
    caller.update(SECRET_TOKEN="x", LD_PRELOAD="/x.so", PROOT_NO_SECCOMP="1", DISPLAY=":9")
    env = mod.launch_env(caller)
    assert set(env) == set(REQUIRED) | OVERRIDES, sorted(env)
    for drop in REQUIRED:
        try:
            mod.launch_env({k: v for k, v in caller.items() if k != drop})
        except SystemExit as e:
            assert drop in str(e), e
        else:
            raise AssertionError(f"missing {drop} accepted")


def test_cli_guards(mod):
    assert mod.main(["--apply"]) == 2, "--apply without confirmation must be refused"
    try:
        mod.main([])
    except SystemExit as e:
        assert e.code == 2
    else:
        raise AssertionError("no mode accepted")


def test_structure(tree):
    for name in ("preflight", "launch_env", "lost_survivors", "assert_stable"):
        bad = calls(func(tree, name)) & DANGEROUS
        assert not bad, (f"{name} must stay read-only", bad)
    main = func(tree, "main")
    dry = next(n for n in ast.walk(main) if isinstance(n, ast.If)
               and ast.unparse(n.test) == "args.dry_run")
    assert any(isinstance(s, ast.Return) for s in dry.body), "dry-run branch must return"
    def harmless(c):  # pidfd_signal(test_fd, 0): signal 0 to our own pidfd, only probes support
        return (getattr(c.func, "id", None) == "pidfd_signal" and len(c.args) == 2
                and ast.unparse(c.args[0]) == "test_fd" and ast.unparse(c.args[1]) == "0")
    first_danger = min(c.lineno for c in ast.walk(main) if isinstance(c, ast.Call) and not harmless(c)
                       and (getattr(c.func, "id", None) in DANGEROUS
                            or getattr(c.func, "attr", None) == "mkdir"))
    assert dry.lineno < first_danger, ("dry-run must return before any mutation", dry.lineno, first_danger)
    targets = {ast.unparse(c.args[1]) for c in ast.walk(func(tree, "restart"))
               if isinstance(c, ast.Call) and getattr(c.func, "id", None) == "signal_checked"}
    assert targets == {"session", "old_tracer"}, targets


def stable_identity():
    out = {}
    for p in Path("/proc").iterdir():
        if not p.name.isdecimal():
            continue
        try:
            cmd = (p / "cmdline").read_bytes().rstrip(b"\0").replace(b"\0", b" ")
            comm = (p / "comm").read_text().strip()
            start = (p / "stat").read_text().rsplit(")", 1)[1].split()[19]
        except OSError:
            continue
        if cmd == STABLE_X or comm == "xfce4-session":
            out[p.name] = (comm, start)
    return out


def test_traced_dry_run_fails_closed():
    before = stable_identity()
    assert any(c == "xfce4-session" for c, _ in before.values()), "no XFCE session; refusing to judge"
    r = subprocess.run([sys.executable, str(SCRIPT), "--dry-run"], capture_output=True, text=True, timeout=60)
    assert r.returncode != 0 and "TracerPid 0" in r.stderr, (r.returncode, r.stderr[-300:])
    assert "STABLE_BASELINE" not in r.stdout
    assert stable_identity() == before, "Stable identity changed"


def main():
    if not Path("/data/data/com.termux/files/usr").is_dir():
        print("SKIP: not on the Termux host")
        return 0
    tree = ast.parse(SCRIPT.read_text())
    mod = load()
    test_env(mod)
    test_cli_guards(mod)
    test_structure(tree)
    test_traced_dry_run_fails_closed()
    print("RESTART_STABLE_DESKTOP_TEST_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
