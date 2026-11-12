#!/usr/bin/env python3
"""R7-P1 abb27a65 present-hold-complete / Present-target-arm classifier.

Host-only helper for run-r7-p1-abb27a65.sh. Does not ADB, install,
launch, or write runtime-abb27a65/r7-p1. Historical classify_r7_p1_present_hold.py
and runtime-8545b26/r7-p1 remain frozen.

R7-P1 cell contract (frozen judge unchanged):
  CALLBACK(30) src=4 → event35 enum=12 side=2 once
  renderer/Activity remains alive through the Present wait
  last GATEA_FATAL_HALT what=x-present-copy-wait reason=4
  no peer HUP before that terminal
  no target event34 / CompleteNotify / semantic retirement

Present-target arm (abb27a65):
  event35 serial/generation must match Present CALLBACK(30) src=4
  CopyArea CALLBACK(30) src=1 matching serial before Present = EARLY_COPY_CONSUME

This is NOT R7-10:
  renderer dies → peer HUP → x-hup/6

Architecture (8545b26 wait-wake ancestry, not rewritten here):
  SUCCESS (completedSerial) wins
  published generationFatal wins
  peer HUP + no success + no published fatal → x-hup/6
  live peer + genuine elapsed timeout → FAIL_TIMEOUT / x-present-copy-wait/4

event36 is Present helper-entry / waited-sample evidence, not standalone
completion proof. waited=1 is used only as wait-entry for elapsed proof.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

EV_CALLBACK = 30
EV_ACK_AFTER = 34
EV_FAULT = 35
EV_RETIRE = 36
EV_SUCCESS = 17
EV_EARLY_ACK = 32
XOP_PRESENT = 4
EXPECTED_ENUM = 12
EXPECTED_SIDE = 2
EXPECTED_WHAT = "x-present-copy-wait"
EXPECTED_REASON = 4
PRODUCT_TIMEOUT_MS = 2000
# usleep(200) loop plus logcat/threadtime granularity. Not WAIT_S=12.
ELAPSED_MIN_MS = 1500
ELAPSED_MAX_MS = 4500

PAT = re.compile(
    r"GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) "
    r"serial=(\d+) src=(\d+) dst=(\d+)"
)
HALT_PAT = re.compile(r"GATEA_FATAL_HALT what=(\S+) reason=(\d+)")
TS_PAT = re.compile(r"^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")
SUMMARY_FATAL_PAT = re.compile(r"generationFatal=(\d+)")

XOP_COPYAREA = 1
EXPECTED_PRESENT_TIMEOUT = "EXPECTED_PRESENT_TIMEOUT"
PEER_DIED = "PEER_DIED"
WRONG_REASON4_IDENTITY = "WRONG_REASON4_IDENTITY"
TARGET_COMPLETED = "TARGET_COMPLETED"
NO_PRESENT_CALLBACK = "NO_PRESENT_CALLBACK"
NO_EVENT35 = "NO_EVENT35"
REPEATED_FAULT = "REPEATED_FAULT"
WRONG_TERMINAL = "WRONG_TERMINAL"
TRACE_INCOMPLETE = "TRACE_INCOMPLETE"
INVALID_ENV = "INVALID_ENV"
WAIT_ARCHITECTURE_HUP = "WAIT_ARCHITECTURE_HUP"
WAIT_ARCHITECTURE_TIMEOUT = "WAIT_ARCHITECTURE_TIMEOUT"
EARLY_COPY_CONSUME = "EARLY_COPY_CONSUME"
SERIAL_MISMATCH = "SERIAL_MISMATCH"


def parse_events(text: str) -> list[dict]:
    out = []
    for m in PAT.finditer(text):
        seq, role, event, gen, serial, src, dst = (int(x) for x in m.groups())
        out.append({
            "seq": seq, "role": role, "event": event, "gen": gen,
            "serial": serial, "src": src, "dst": dst,
        })
    return out


def merge_by_seq(a: list[dict], b: list[dict]) -> tuple[list[dict], list[int]]:
    by: dict[int, dict] = {}
    conflicts: list[int] = []
    keys = ("seq", "role", "event", "gen", "serial", "src", "dst")
    for e in a + b:
        prev = by.get(e["seq"])
        if prev is not None and {k: prev[k] for k in keys} != {k: e[k] for k in keys}:
            conflicts.append(e["seq"])
        by[e["seq"]] = e
    return sorted(by.values(), key=lambda e: e["seq"]), conflicts


def unique_halts(text: str) -> list[tuple[str, str]]:
    seen: list[tuple[str, str]] = []
    for what, reason in HALT_PAT.findall(text):
        rec = (what, reason)
        if rec not in seen:
            seen.append(rec)
    return seen


def last_halt(text: str) -> tuple[str, str] | None:
    all_h = HALT_PAT.findall(text)
    if not all_h:
        return None
    return all_h[-1]


def parse_ts(line: str) -> dt.datetime | None:
    m = TS_PAT.match(line.strip())
    if not m:
        return None
    try:
        return dt.datetime.strptime("2026-" + m.group(1), "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return None


def elapsed_from_event36_to_halt(follow: str) -> tuple[int | None, str]:
    start = None
    end = None
    for line in follow.splitlines():
        if "GATEA_EVENT" in line and "event=36" in line:
            m = PAT.search(line)
            if m and int(m.group(6)) == 1:
                ts = parse_ts(line)
                if ts is not None:
                    start = ts
        if "GATEA_FATAL_HALT what=x-present-copy-wait reason=4" in line:
            ts = parse_ts(line)
            if ts is not None:
                end = ts
    if start is None:
        return None, "no_event36_waited1_ts"
    if end is None:
        return None, "no_present_timeout_halt_ts"
    ms = int((end - start).total_seconds() * 1000)
    if ms < 0:
        ms += 24 * 60 * 60 * 1000
    return ms, "ok"


def rec_base(**kw) -> dict:
    out = {
        "classification": TRACE_INCOMPLETE,
        "runner_invalid": "NO",
        "product_fail": "NO",
        "continue_judge": "NO",
        "reason4_globally_forbidden": "NO",
        "timeout_ms": PRODUCT_TIMEOUT_MS,
        "elapsed_min_ms": ELAPSED_MIN_MS,
        "elapsed_max_ms": ELAPSED_MAX_MS,
    }
    out.update(kw)
    return out


def construction(events: list[dict]) -> tuple[str | None, dict]:
    faults = [e for e in events if e["event"] == EV_FAULT]
    present_cbs = [e for e in events if e["event"] == EV_CALLBACK and e["src"] == XOP_PRESENT]
    copy_cbs = [e for e in events if e["event"] == EV_CALLBACK and e["src"] == XOP_COPYAREA]
    if len(faults) == 0:
        return NO_EVENT35, {"note": "no_event35"}
    if len(faults) != 1:
        return REPEATED_FAULT, {"note": f"event35_count={len(faults)}"}
    f = faults[0]
    if f["src"] != EXPECTED_ENUM or f["dst"] != EXPECTED_SIDE or f["role"] != EXPECTED_SIDE:
        return WRONG_TERMINAL, {"note": f"event35_enum_or_side src={f['src']} dst={f['dst']} role={f['role']}"}
    copy_before = [
        e for e in copy_cbs
        if e["seq"] < f["seq"] and e["serial"] == f["serial"] and e["serial"] != 0
    ]
    present_before = [
        e for e in present_cbs
        if e["seq"] < f["seq"] and e["serial"] != 0
    ]
    present_match = [
        e for e in present_before
        if e["serial"] == f["serial"] and e["gen"] == f["gen"]
    ]
    if not present_before:
        if copy_before:
            return EARLY_COPY_CONSUME, {
                "note": "event35 serial matches CopyArea CALLBACK before Present target",
                "fault_serial": f["serial"],
            }
        return NO_PRESENT_CALLBACK, {"note": "missing CALLBACK event30 src=4 before event35"}
    if not present_match:
        if copy_before:
            return EARLY_COPY_CONSUME, {
                "note": "event35 serial matches CopyArea, not Present CALLBACK",
                "fault_serial": f["serial"],
            }
        return SERIAL_MISMATCH, {
            "note": "event35 serial/generation does not match Present CALLBACK",
            "fault_serial": f["serial"],
            "present_serial": present_before[-1]["serial"],
        }
    return None, {"fault": f, "callback": present_match[-1]}


def classify_r7_p1_cell(
    blob: str,
    events: list[dict],
    follow: str,
    env_captured: int,
    env_exact: int,
    renderer_alive: int,
    activity_pre_cleanup: int,
) -> dict:
    if env_captured != 1 or env_exact != 1:
        return rec_base(
            classification=INVALID_ENV,
            runner_invalid="YES",
            note="cannot fabricate ENV_EXACT",
        )
    kind, extra = construction(events)
    if kind is not None:
        return rec_base(
            classification=kind,
            runner_invalid="YES",
            continue_judge="NO",
            **extra,
        )

    halts = unique_halts(blob)
    last = last_halt(blob)
    xhup = sum(1 for w, r in unique_halts(blob) if w == "x-hup")
    rhup = sum(1 for w, r in unique_halts(blob) if w == "r-hup")
    present4 = sum(1 for w, r in unique_halts(blob) if w == EXPECTED_WHAT and r == str(EXPECTED_REASON))
    direct4 = sum(1 for w, r in unique_halts(blob) if w == "x-direct-not-success" and r == "4")
    exa4 = sum(1 for w, r in unique_halts(blob) if w == "x-exa-composite-wait" and r == "4")
    hup_preserve = re.findall(r"GATEA_HUP_PRESERVE[^\n]*", blob)
    event34 = [e for e in events if e["event"] == EV_ACK_AFTER]
    event32 = [e for e in events if e["event"] == EV_EARLY_ACK]
    success = [e for e in events if e["event"] == EV_SUCCESS]
    retires = [e for e in events if e["event"] == EV_RETIRE]
    waited1 = [e for e in retires if e["src"] == 1]
    waited0 = [e for e in retires if e["src"] == 0]
    published = 0
    for m in SUMMARY_FATAL_PAT.finditer(blob):
        published = max(published, int(m.group(1)))

    if renderer_alive != 1:
        if last and last[0] in ("x-hup", "r-hup"):
            return rec_base(
                classification=PEER_DIED,
                runner_invalid="YES",
                product_fail="NO",
                continue_judge="NO",
                note="renderer/Activity not alive; HUP is not a valid P1 timeout",
                last_halt=f"{last[0]}/{last[1]}",
                renderer_alive=renderer_alive,
            )
        return rec_base(
            classification=PEER_DIED,
            runner_invalid="YES",
            product_fail="NO",
            continue_judge="NO",
            note="renderer/Activity not proven alive through Present wait",
            renderer_alive=renderer_alive,
        )

    if activity_pre_cleanup != 1:
        return rec_base(
            classification=PEER_DIED,
            runner_invalid="YES",
            product_fail="NO",
            continue_judge="NO",
            note="Activity not ALIVE at pre-cleanup; not a live-peer Present timeout",
            renderer_alive=renderer_alive,
            activity_pre_cleanup=activity_pre_cleanup,
        )

    if xhup or rhup or hup_preserve:
        if last and last[0] in ("x-hup", "r-hup"):
            return rec_base(
                classification=PEER_DIED if activity_pre_cleanup != 1 else WRONG_TERMINAL,
                runner_invalid="NO" if activity_pre_cleanup == 1 else "YES",
                product_fail="YES" if activity_pre_cleanup == 1 else "NO",
                continue_judge="YES" if activity_pre_cleanup == 1 else "NO",
                note="peer HUP observed; not intended P1 live-peer timeout"
                + ("; repair must not emit x-hup/6 while renderer is alive" if activity_pre_cleanup == 1 else ""),
                last_halt=f"{last[0]}/{last[1]}" if last else "",
                x_hup=xhup,
                r_hup=rhup,
                hup_preserve_count=len(hup_preserve),
            )
        return rec_base(
            classification=PEER_DIED,
            runner_invalid="YES",
            note="HUP marker present before Present timeout terminal",
            x_hup=xhup,
            r_hup=rhup,
        )

    if event32:
        return rec_base(
            classification=WRONG_TERMINAL,
            product_fail="YES",
            continue_judge="YES",
            note="event32 forbidden on Present cell",
        )
    if event34 or waited0:
        return rec_base(
            classification=TARGET_COMPLETED,
            product_fail="YES",
            continue_judge="YES",
            note="target Present retired/acked before timeout",
            event34_count=len(event34),
            event36_waited0=len(waited0),
        )
    if success:
        return rec_base(
            classification=TARGET_COMPLETED,
            product_fail="YES",
            continue_judge="YES",
            note="semantic SUCCESS on withheld Present copy",
        )
    if re.search(r"CompleteNotify|present_pixmap_idle|CLIENT_OK mode=", blob):
        if "RESULT p_r6_d2_present CLIENT_OK" in blob:
            return rec_base(
                classification=TARGET_COMPLETED,
                product_fail="YES",
                continue_judge="YES",
                note="fixture CompleteNotify/CLIENT_OK means target retired",
            )

    if direct4 or exa4:
        return rec_base(
            classification=WRONG_REASON4_IDENTITY,
            product_fail="YES",
            continue_judge="YES",
            note="reason=4 is not x-present-copy-wait",
            last_halt=f"{last[0]}/{last[1]}" if last else "",
            x_direct_not_success_reason4=direct4,
            x_exa_composite_wait_reason4=exa4,
        )

    if published != 0:
        first = HALT_PAT.findall(blob)[0] if HALT_PAT.findall(blob) else ("", "")
        if first[0] != EXPECTED_WHAT:
            return rec_base(
                classification=WRONG_TERMINAL,
                product_fail="YES",
                continue_judge="YES",
                note="published generationFatal must win; later Present timeout cannot overwrite",
                first_halt=f"{first[0]}/{first[1]}",
                last_halt=f"{last[0]}/{last[1]}" if last else "",
                generation_fatal=published,
            )

    if not last or last[0] != EXPECTED_WHAT or last[1] != str(EXPECTED_REASON):
        return rec_base(
            classification=WRONG_TERMINAL,
            product_fail="YES",
            continue_judge="YES",
            note="construction present but terminal is not x-present-copy-wait/4",
            last_halt=f"{last[0]}/{last[1]}" if last else "",
        )

    elapsed_ms, why = elapsed_from_event36_to_halt(follow)
    if elapsed_ms is None:
        if not waited1:
            return rec_base(
                classification=TRACE_INCOMPLETE,
                runner_invalid="YES",
                note="event36 waited=1 missing; cannot prove Present wait entry",
                last_halt=f"{last[0]}/{last[1]}",
            )
        return rec_base(
            classification=TRACE_INCOMPLETE,
            runner_invalid="YES",
            note=f"cannot measure genuine Present wait elapsed: {why}",
            last_halt=f"{last[0]}/{last[1]}",
        )
    if not (ELAPSED_MIN_MS <= elapsed_ms <= ELAPSED_MAX_MS):
        return rec_base(
            classification=WRONG_TERMINAL,
            product_fail="YES",
            continue_judge="YES",
            note="elapsed is not a genuine 2000ms Present wait",
            elapsed_ms=elapsed_ms,
            last_halt=f"{last[0]}/{last[1]}",
        )

    return rec_base(
        classification=EXPECTED_PRESENT_TIMEOUT,
        runner_invalid="NO",
        product_fail="NO",
        continue_judge="YES",
        note="live-peer genuine x-present-copy-wait/4; HUP=0; reason4 identity exact",
        last_halt=f"{last[0]}/{last[1]}",
        x_present_copy_wait_reason4=present4,
        x_hup=0,
        r_hup=0,
        event36_waited1=len(waited1),
        elapsed_ms=elapsed_ms,
        renderer_alive=renderer_alive,
        activity_pre_cleanup=activity_pre_cleanup,
    )


def classify_wait_architecture(blob: str, events: list[dict]) -> dict:
    """Host regression: peer-dead HUP vs live-peer timeout remain distinct."""
    last = last_halt(blob)
    xhup6 = sum(1 for w, r in unique_halts(blob) if w == "x-hup" and r == "6")
    present4 = sum(
        1 for w, r in unique_halts(blob)
        if w == EXPECTED_WHAT and r == str(EXPECTED_REASON)
    )
    if last and last[0] == "x-hup" and last[1] == "6" and present4 == 0:
        return rec_base(
            classification=WAIT_ARCHITECTURE_HUP,
            note="peer dead + no fatal → HUP path still works",
            last_halt=f"{last[0]}/{last[1]}",
            x_hup_reason6=xhup6,
        )
    if last and last[0] == EXPECTED_WHAT and last[1] == "4" and xhup6 == 0:
        faults = [e for e in events if e["event"] == EV_FAULT]
        if faults and faults[0]["src"] == 10:
            return rec_base(
                classification=WRONG_TERMINAL,
                product_fail="YES",
                note="R7-10 construction must not be labeled Present timeout",
            )
        return rec_base(
            classification=WAIT_ARCHITECTURE_TIMEOUT,
            note="peer alive + genuine Present timeout → timeout/4 still works",
            last_halt=f"{last[0]}/{last[1]}",
            x_present_copy_wait_reason4=present4,
        )
    return rec_base(
        classification=TRACE_INCOMPLETE,
        runner_invalid="YES",
        note="wait-architecture mock missing HUP or Present timeout identity",
        last_halt=f"{last[0]}/{last[1]}" if last else "",
    )


def write_out(path: Path | None, rec: dict) -> None:
    lines = [f"{k}={v}" for k, v in rec.items()]
    text = "\n".join(lines) + "\n"
    if path:
        path.write_text(text)
    sys.stdout.write(text)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=("r7-p1-cell", "wait-architecture"))
    p.add_argument("--follow", required=True)
    p.add_argument("--dump", default="")
    p.add_argument("--ring", default="")
    p.add_argument("--summary", default="")
    p.add_argument("--out", default="")
    p.add_argument("--env-captured", type=int, default=1)
    p.add_argument("--env-exact", type=int, default=1)
    p.add_argument("--renderer-alive", type=int, default=1)
    p.add_argument("--activity-pre-cleanup", type=int, default=1)
    args = p.parse_args()

    def readp(s: str) -> str:
        if not s:
            return ""
        path = Path(s)
        return path.read_text(errors="replace") if path.exists() else ""

    follow = readp(args.follow)
    dump = readp(args.dump)
    ring = readp(args.ring)
    summary = readp(args.summary)
    blob = "\n".join((follow, dump, ring, summary))
    events, conflicts = merge_by_seq(parse_events(follow + "\n" + dump), parse_events(ring))
    if conflicts:
        rec = rec_base(
            classification=TRACE_INCOMPLETE,
            runner_invalid="YES",
            note=f"seq conflicts {conflicts}",
        )
    elif args.mode == "r7-p1-cell":
        rec = classify_r7_p1_cell(
            blob, events, follow + "\n" + dump,
            args.env_captured, args.env_exact,
            args.renderer_alive, args.activity_pre_cleanup,
        )
    else:
        rec = classify_wait_architecture(blob, events)

    rec.setdefault("x_present_copy_wait_reason4", sum(
        1 for w, r in unique_halts(blob) if w == EXPECTED_WHAT and r == str(EXPECTED_REASON)))
    rec.setdefault("x_direct_not_success_reason4", sum(
        1 for w, r in unique_halts(blob) if w == "x-direct-not-success" and r == "4"))
    rec.setdefault("x_hup", sum(1 for w, r in unique_halts(blob) if w == "x-hup"))
    rec["reason4_globally_forbidden"] = "NO"
    rec["mode"] = args.mode
    write_out(Path(args.out) if args.out else None, rec)

    if rec.get("runner_invalid") == "YES":
        return 9
    if rec.get("product_fail") == "YES":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
