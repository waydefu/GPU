#!/usr/bin/python3 -B
"""Client-agnostic launcher for the deployed Hybrid 2.0 relay (Claude, Codex, Antigravity, Hermes).

Every MCP client config runs only this file. It supplies the governance environment from one
place (budget directory, trusted Git roots next to this file) and, because desktop apps strip
the Android runtime variables that ``--auto-start`` needs for ``am``, copies only those missing
variables from the Termux app process. Then it execs the relay with ``--auto-start``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TERMUX_HOME = "/data/data/com.termux/files/home"
BUDGET_DIR = f"{TERMUX_HOME}/.f8hyb2-budget"
SOCKET = f"{TERMUX_HOME}/.f8hyb2/m.sock"
AM_REQUIRED_ENV = ("ANDROID_ART_ROOT", "ANDROID_I18N_ROOT", "ANDROID_TZDATA_ROOT", "ANDROID_ROOT",
                   "ANDROID_DATA", "BOOTCLASSPATH", "DEX2OATBOOTCLASSPATH")


def termux_app_environ() -> dict[str, str]:
    """Environment of the running Termux app process (same uid), or {} if not found/readable."""
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        try:
            with open(f"/proc/{entry.name}/cmdline", "rb") as fh:
                if fh.read(64).split(b"\0", 1)[0] != b"com.termux":
                    continue
            with open(f"/proc/{entry.name}/environ", "rb") as fh:
                raw = fh.read(1 << 20)
        except OSError:
            continue
        out = {}
        for item in raw.split(b"\0"):
            key, sep, value = item.partition(b"=")
            if sep:
                out[key.decode(errors="replace")] = value.decode(errors="replace")
        return out
    return {}


def prepare_env(env: dict[str, str], termux_env: dict[str, str] | None, trusted_roots: str) -> dict[str, str]:
    """Governance variables are fixed here; only missing Android runtime variables are borrowed."""
    out = dict(env)
    out["F8_HYBRID2_BUDGET_DIR"] = BUDGET_DIR
    out["F8_HYBRID2_TRUSTED_GIT_ROOTS"] = trusted_roots
    out["PYTHONDONTWRITEBYTECODE"] = "1"
    missing = [k for k in AM_REQUIRED_ENV if not out.get(k)]
    if missing and termux_env is None:
        termux_env = termux_app_environ()
    for key in missing:
        value = (termux_env or {}).get(key, "")
        if value and "\0" not in value:
            out[key] = value
    return out


def main() -> None:
    roots = (HERE / "trusted-git-roots.json").read_text(encoding="utf-8").strip()
    env = prepare_env(dict(os.environ), None, roots)
    relay = str(HERE / "f8_hybrid2_relay.py")
    os.execve("/usr/bin/python3", ["/usr/bin/python3", "-B", relay, "--socket", SOCKET, "--auto-start", *sys.argv[1:]], env)


if __name__ == "__main__":
    main()
