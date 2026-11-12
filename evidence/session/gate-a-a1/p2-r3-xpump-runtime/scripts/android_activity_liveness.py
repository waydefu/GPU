#!/usr/bin/env python3
"""Bind Android Activity liveness from device evidence only.

Workstation /proc must never classify an Android Activity as dead.
X3 (same-user Termux/PRoot child) may still use host /proc.

The classifier consumes the already-bound activity_alive_during_wait
bit. It must not reopen /proc itself.
"""
from __future__ import annotations

from typing import Any
from pathlib import Path


AUTHORITY = "adb-device-proc-and-ps"


def classify_android_activity_liveness(
    *,
    device_proc_exists: bool,
    device_ps_identity_ok: bool,
    host_proc_exists: bool | None = None,
    activity_pid: int | None = None,
    renderer_tid: int | None = None,
    package: str = "com.waydefu.x11gpu",
) -> dict[str, Any]:
    """Return a bound liveness record.

    host_proc_exists is commentary only. A False host /proc sample cannot
    force dead when the device probe is alive. A True host sample cannot
    force alive when the device probe is dead.
    """
    del host_proc_exists  # never a death/life authority
    alive = bool(device_proc_exists) and bool(device_ps_identity_ok)
    return {
        "activity_alive_during_wait": 1 if alive else 0,
        "authority": AUTHORITY,
        "device_proc_exists": 1 if device_proc_exists else 0,
        "device_ps_identity_ok": 1 if device_ps_identity_ok else 0,
        "host_proc_used_as_death": 0,
        "host_proc_used_as_life": 0,
        "activity_pid": activity_pid if activity_pid is not None else 0,
        "renderer_tid": renderer_tid if renderer_tid is not None else 0,
        "package": package,
    }


def format_record(rec: dict[str, Any]) -> str:
    order = (
        "activity_alive_during_wait",
        "authority",
        "device_proc_exists",
        "device_ps_identity_ok",
        "host_proc_used_as_death",
        "host_proc_used_as_life",
        "activity_pid",
        "renderer_tid",
        "package",
    )
    lines = [f"{k}={rec[k]}" for k in order]
    extra = [f"{k}={v}" for k, v in rec.items() if k not in order]
    return "\n".join(lines + extra) + "\n"


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--device-proc-exists", type=int, required=True)
    p.add_argument("--device-ps-identity-ok", type=int, required=True)
    p.add_argument("--host-proc-exists", type=int, default=0)
    p.add_argument("--activity-pid", type=int, default=0)
    p.add_argument("--renderer-tid", type=int, default=0)
    p.add_argument("--package", default="com.waydefu.x11gpu")
    p.add_argument("--out", default="")
    args = p.parse_args()
    rec = classify_android_activity_liveness(
        device_proc_exists=bool(args.device_proc_exists),
        device_ps_identity_ok=bool(args.device_ps_identity_ok),
        host_proc_exists=bool(args.host_proc_exists),
        activity_pid=args.activity_pid or None,
        renderer_tid=args.renderer_tid or None,
        package=args.package,
    )
    text = format_record(rec)
    if args.out:
        Path(args.out).write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
