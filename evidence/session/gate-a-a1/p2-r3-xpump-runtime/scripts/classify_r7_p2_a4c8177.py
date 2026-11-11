#!/usr/bin/env python3
"""R7-P2 a4c8177 present-renderer-exit / Present-target-arm classifier.

Host-only helper for run-r7-p2-a4c8177.sh. Does not ADB, install,
launch, or write runtime-a4c8177/r7-p2. Historical runtime-8545b26/r7-p1
remains INVALID/FROZEN.

R7-P2 cell contract (frozen judge unchanged):
  CALLBACK(30) src=4 → event35 enum=13 side=2 once
  matching Present COPY consume, then renderer intentional exit
  last GATEA_FATAL_HALT what=x-hup reason=6
  no x-present-copy-wait/4
  no target event34 / CompleteNotify / ACK / idle / semantic completion

Present-target arm (abb27a65):
  event35 serial/generation must match Present CALLBACK(30) src=4
  CopyArea CALLBACK(30) src=1 matching serial before Present = EARLY_COPY_CONSUME
  startup CopyArea must not consume enum13

Architecture (8545b26 wait-wake ancestry, not rewritten here):
  SUCCESS wins
  published generationFatal wins
  peer HUP + no success + no published fatal → x-hup/6
  live peer timeout → x-present-copy-wait/4 (FAIL for this cell)
"""
from __future__ import annotations

import argparse
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
XOP_COPYAREA = 1
EXPECTED_ENUM = 13
EXPECTED_SIDE = 2
EXPECTED_WHAT = "x-hup"
EXPECTED_REASON = 6
FORBIDDEN_TIMEOUT_WHAT = "x-present-copy-wait"
PRODUCT_TIMEOUT_MS = 2000

PAT = re.compile(
    r"GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) "
    r"serial=(\d+) src=(\d+) dst=(\d+)"
)
HALT_PAT = re.compile(r"GATEA_FATAL_HALT what=(\S+) reason=(\d+)")
SUMMARY_FATAL_PAT = re.compile(r"generationFatal=(\d+)")

EXPECTED_PRESENT_RENDERER_EXIT = "EXPECTED_PRESENT_RENDERER_EXIT"
WRONG_REASON4_IDENTITY = "WRONG_REASON4_IDENTITY"
TARGET_COMPLETED = "TARGET_COMPLETED"
NO_PRESENT_CALLBACK = "NO_PRESENT_CALLBACK"
NO_EVENT35 = "NO_EVENT35"
REPEATED_FAULT = "REPEATED_FAULT"
WRONG_TERMINAL = "WRONG_TERMINAL"
TRACE_INCOMPLETE = "TRACE_INCOMPLETE"
INVALID_ENV = "INVALID_ENV"
EARLY_COPY_CONSUME = "EARLY_COPY_CONSUME"
SERIAL_MISMATCH = "SERIAL_MISMATCH"
RHUP_SUBSTITUTE = "RHUP_SUBSTITUTE"


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


def rec_base(**kw) -> dict:
    out = {
        "classification": TRACE_INCOMPLETE,
        "runner_invalid": "NO",
        "product_fail": "NO",
        "continue_judge": "NO",
        "reason4_globally_forbidden": "NO",
        "timeout_ms": PRODUCT_TIMEOUT_MS,
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
                "note": "startup CopyArea consumed enum13 before Present target",
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


def classify_r7_p2_cell(
    blob: str,
    events: list[dict],
    env_captured: int,
    env_exact: int,
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

    last = last_halt(blob)
    xhup6 = sum(1 for w, r in unique_halts(blob) if w == "x-hup" and r == "6")
    rhup6 = sum(1 for w, r in unique_halts(blob) if w == "r-hup" and r == "6")
    present4 = sum(
        1 for w, r in unique_halts(blob)
        if w == FORBIDDEN_TIMEOUT_WHAT and r == "4"
    )
    direct4 = sum(1 for w, r in unique_halts(blob) if w == "x-direct-not-success" and r == "4")
    exa4 = sum(1 for w, r in unique_halts(blob) if w == "x-exa-composite-wait" and r == "4")
    event34 = [e for e in events if e["event"] == EV_ACK_AFTER]
    event32 = [e for e in events if e["event"] == EV_EARLY_ACK]
    success = [e for e in events if e["event"] == EV_SUCCESS]
    waited0 = [e for e in events if e["event"] == EV_RETIRE and e["src"] == 0]
    published = 0
    for m in SUMMARY_FATAL_PAT.finditer(blob):
        published = max(published, int(m.group(1)))

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
            note="target Present retired/acked after renderer-exit construction",
            event34_count=len(event34),
            event36_waited0=len(waited0),
        )
    if success:
        return rec_base(
            classification=TARGET_COMPLETED,
            product_fail="YES",
            continue_judge="YES",
            note="semantic SUCCESS after Present renderer-exit construction",
        )
    if re.search(r"CompleteNotify|present_pixmap_idle|CLIENT_OK mode=", blob):
        if "RESULT p_r6_d2_present CLIENT_OK" in blob:
            return rec_base(
                classification=TARGET_COMPLETED,
                product_fail="YES",
                continue_judge="YES",
                note="fixture CompleteNotify/CLIENT_OK means target retired",
            )

    if present4 or (last and last[0] == FORBIDDEN_TIMEOUT_WHAT and last[1] == "4"):
        return rec_base(
            classification=WRONG_TERMINAL,
            product_fail="YES",
            continue_judge="YES",
            note="renderer-exit construction classified as live-peer Present timeout",
            last_halt=f"{last[0]}/{last[1]}" if last else "",
            x_present_copy_wait_reason4=present4,
        )
    if direct4 or exa4:
        return rec_base(
            classification=WRONG_REASON4_IDENTITY,
            product_fail="YES",
            continue_judge="YES",
            note="reason=4 is not allowed as P2 terminal",
            last_halt=f"{last[0]}/{last[1]}" if last else "",
            x_direct_not_success_reason4=direct4,
            x_exa_composite_wait_reason4=exa4,
        )

    if last and last[0] == "r-hup" and last[1] == "6":
        return rec_base(
            classification=RHUP_SUBSTITUTE,
            product_fail="YES",
            continue_judge="YES",
            note="r-hup/6 is not an X containment substitute for x-hup/6",
            last_halt=f"{last[0]}/{last[1]}",
            r_hup_reason6=rhup6,
        )

    if published != 0:
        first = HALT_PAT.findall(blob)[0] if HALT_PAT.findall(blob) else ("", "")
        if first[0] != EXPECTED_WHAT:
            return rec_base(
                classification=WRONG_TERMINAL,
                product_fail="YES",
                continue_judge="YES",
                note="published generationFatal must win; later HUP cannot overwrite",
                first_halt=f"{first[0]}/{first[1]}",
                last_halt=f"{last[0]}/{last[1]}" if last else "",
                generation_fatal=published,
            )

    if last and last[0] == EXPECTED_WHAT and last[1] == str(EXPECTED_REASON) and present4 == 0:
        return rec_base(
            classification=EXPECTED_PRESENT_RENDERER_EXIT,
            runner_invalid="NO",
            product_fail="NO",
            continue_judge="YES",
            note="Present-target enum13 then X x-hup/6; timeout/4=0",
            last_halt=f"{last[0]}/{last[1]}",
            x_hup_reason6=xhup6,
            x_present_copy_wait_reason4=0,
            event34_count=0,
        )

    return rec_base(
        classification=WRONG_TERMINAL,
        product_fail="YES",
        continue_judge="YES",
        note="construction present but terminal is not x-hup/6",
        last_halt=f"{last[0]}/{last[1]}" if last else "",
        x_hup_reason6=xhup6,
        x_present_copy_wait_reason4=present4,
    )


def write_out(path: Path | None, rec: dict) -> None:
    lines = [f"{k}={v}" for k, v in rec.items()]
    text = "\n".join(lines) + "\n"
    if path:
        path.write_text(text)
    sys.stdout.write(text)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=("r7-p2-cell",))
    p.add_argument("--follow", required=True)
    p.add_argument("--dump", default="")
    p.add_argument("--ring", default="")
    p.add_argument("--summary", default="")
    p.add_argument("--out", default="")
    p.add_argument("--env-captured", type=int, default=1)
    p.add_argument("--env-exact", type=int, default=1)
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
    else:
        rec = classify_r7_p2_cell(blob, events, args.env_captured, args.env_exact)

    rec.setdefault("x_present_copy_wait_reason4", sum(
        1 for w, r in unique_halts(blob) if w == FORBIDDEN_TIMEOUT_WHAT and r == "4"))
    rec.setdefault("x_direct_not_success_reason4", sum(
        1 for w, r in unique_halts(blob) if w == "x-direct-not-success" and r == "4"))
    rec.setdefault("x_hup", sum(1 for w, r in unique_halts(blob) if w == "x-hup"))
    rec.setdefault("x_hup_reason6", sum(
        1 for w, r in unique_halts(blob) if w == "x-hup" and r == "6"))
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
