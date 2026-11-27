#!/usr/bin/env python3
"""Shared isolated ADB (-H 127.0.0.1 -P 5038) helpers and device identity checks for Stage 6."""
from __future__ import annotations

import os
import re
import subprocess as sp
from pathlib import Path
from typing import Any

PREFIX = Path("/data/data/com.termux/files/usr")
TERMUX_HOME = Path("/data/data/com.termux/files/home")
ADB_BIN = PREFIX / "bin/adb"
ADB_STRIP_ENV = ("ADB_SERVER_SOCKET", "ANDROID_ADB_SERVER_ADDRESS", "ANDROID_ADB_SERVER_PORT")
EXPECTED_DEVICE = "myron"
EXPECTED_MODELS = ("25102PCBEG", "F8")


def adb_env(home: Path | str = TERMUX_HOME, base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return an isolated ADB client env: strip overriding socket/port vars and pin HOME."""
    env = dict(os.environ if base_env is None else base_env)
    for k in ADB_STRIP_ENV:
        env.pop(k, None)
    env["HOME"] = str(home)
    return env


def run_adb(port: int, args: list[str], serial: str | None = None, timeout: float = 10.0,
            adb_bin: Path | str = ADB_BIN, home: Path | str = TERMUX_HOME) -> tuple[int, str]:
    cmd = [str(adb_bin), "-H", "127.0.0.1", "-P", str(port)]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)
    try:
        r = sp.run(cmd, env=adb_env(home=home), capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (sp.SubprocessError, OSError) as exc:
        return -1, str(exc)


def detect_myron_serial(port: int, adb_bin: Path | str = ADB_BIN, home: Path | str = TERMUX_HOME) -> str:
    """Discover the single authorized myron device on isolated ADB port; fail closed otherwise."""
    rc, out = run_adb(port, ["devices", "-l"], timeout=8.0, adb_bin=adb_bin, home=home)
    if rc != 0:
        raise SystemExit(f"FAIL: adb -P {port} devices failed: {out}")
    candidates: list[tuple[str, str]] = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            candidates.append((parts[0], line))
    myron_tagged = [ser for ser, line in candidates if "device:myron" in line or "model:25102PCBEG" in line]
    if len(myron_tagged) == 1:
        return myron_tagged[0]
    if len(myron_tagged) > 1:
        raise SystemExit(f"FAIL: multiple myron transports attached on ADB -P {port}: {len(myron_tagged)}")
    if len(candidates) == 1:
        ser = candidates[0][0]
        rc2, dev = run_adb(port, ["shell", "getprop", "ro.product.device"], serial=ser, adb_bin=adb_bin, home=home)
        if rc2 == 0 and dev.strip() == EXPECTED_DEVICE:
            return ser
    raise SystemExit(f"FAIL: no authorized {EXPECTED_DEVICE} device on ADB -P {port}")


def _extract_pkg_meta(block: str) -> dict[str, str | None]:
    ver = re.search(r"versionName=(\S+)", block)
    ins = re.search(r"firstInstallTime=([^\r\n]+)", block)
    return {
        "versionName": ver.group(1) if ver else None,
        "firstInstallTime": ins.group(1).strip() if ins else None,
    }


def verify_device_identity(port: int, serial: str, adb_bin: Path | str = ADB_BIN,
                           home: Path | str = TERMUX_HOME) -> dict[str, Any]:
    """Verify ro.product.device/model and record X11 package versions per ADB-CONNECT.md §2."""
    script = (
        "echo __MODEL__=$(getprop ro.product.model); "
        "echo __DEVICE__=$(getprop ro.product.device); "
        "echo __X11__; dumpsys package com.termux.x11 2>/dev/null | grep -iE 'versionName|firstInstallTime'; "
        "echo __X11GPU__; dumpsys package com.waydefu.x11gpu 2>/dev/null | grep -iE 'versionName|firstInstallTime'"
    )
    rc, out = run_adb(port, ["shell", script], serial=serial, timeout=10.0, adb_bin=adb_bin, home=home)
    if rc != 0:
        raise SystemExit(f"FAIL: identity verification failed on ADB -P {port}: {out}")
    m_mod = re.search(r"__MODEL__=([^\r\n]*)", out)
    m_dev = re.search(r"__DEVICE__=([^\r\n]*)", out)
    model = m_mod.group(1).strip() if m_mod else ""
    device = m_dev.group(1).strip() if m_dev else ""
    if device != EXPECTED_DEVICE or model not in EXPECTED_MODELS:
        raise SystemExit(f"FAIL: unexpected device identity model={model!r} device={device!r}")

    m_x11 = re.search(r"__X11__\n(.*?)\n__X11GPU__", out, re.S)
    m_gpu = re.search(r"__X11GPU__\n(.*)\Z", out, re.S)
    pkg_x11 = _extract_pkg_meta(m_x11.group(1) if m_x11 else "")
    pkg_gpu = _extract_pkg_meta(m_gpu.group(1) if m_gpu else "")
    if not pkg_x11["versionName"]:
        raise SystemExit("FAIL: com.termux.x11 package versionName missing")
    return {
        "model": model,
        "device": device,
        "adb_port": port,
        "serial_redacted": "<redacted-adb-endpoint>",
        "packages": {
            "com.termux.x11": pkg_x11,
            "com.waydefu.x11gpu": pkg_gpu,
        },
    }


def parse_zram_line(text: str) -> dict[str, int] | None:
    m = re.search(r"ZRAM:\s*([\d,]+)K\s+physical used for\s*([\d,]+)K\s+in swap\s*\(([\d,]+)K\s+total swap\)", text)
    if not m:
        return None
    return {
        "physical_kb": int(m.group(1).replace(",", "")),
        "swap_kb": int(m.group(2).replace(",", "")),
        "total_swap_kb": int(m.group(3).replace(",", "")),
    }


def parse_vmstat(text: str) -> dict[str, int] | None:
    out: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].isdigit():
            out[parts[0]] = int(parts[1])
    return out or None
