#!/usr/bin/env python3
"""R7-10 renderer-exit-after-consume / HUP-containment classifier.

Host-only helper for run-r7-10-8545b26.sh and runner qualification mocks.
Does not ADB, install, launch, or write runtime-8545b26/r7-10.

R7-10 cell contract (frozen judge unchanged):
  PUBLISH(6) → CONSUME_DIRECT(7) → event35 enum=10 side=2
  last GATEA_FATAL_HALT what=x-hup reason=6
  x-direct-not-success/4 count must be 0 on this constructed cell

Architecture (not this cell):
  live peer + no completion + no published fatal + genuine timeout
  may still halt x-direct-not-success/4. This classifier must NOT treat
  every reason=4 as an R7-10 product failure.

HUP precedence (not a rewrite of published fatals):
  published generationFatal != 0 must remain authoritative if a later
  peer HUP arrives.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EV_PUBLISH = 6
EV_CONSUME = 7
EV_SUCCESS = 17
EV_FAULT = 35
EXPECTED_ENUM = 10
EXPECTED_SIDE = 2
EXPECTED_WHAT = "x-hup"
EXPECTED_REASON = 6
BUG_WHAT = "x-direct-not-success"
BUG_REASON = 4

PAT = re.compile(
    r"GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) "
    r"serial=(\d+) src=(\d+) dst=(\d+)"
)
HALT_PAT = re.compile(r"GATEA_FATAL_HALT what=(\S+) reason=(\d+)")

EXPECTED_HUP = "EXPECTED_HUP"
HISTORICAL_REASON4 = "HISTORICAL_REASON4"
WRONG_TERMINAL = "WRONG_TERMINAL"
NO_CONSTRUCTION = "NO_CONSTRUCTION"
REPEATED_FAULT = "REPEATED_FAULT"
TRACE_INCOMPLETE = "TRACE_INCOMPLETE"
INVALID_ENV = "INVALID_ENV"
GENUINE_TIMEOUT_NOT_R7_10 = "GENUINE_TIMEOUT_NOT_R7_10"
HUP_PRECEDENCE_PRESERVE = "HUP_PRECEDENCE_PRESERVE"
HUP_PRECEDENCE_OVERWRITE = "HUP_PRECEDENCE_OVERWRITE"
HUP_PRECEDENCE_NOT_APPLICABLE = "HUP_PRECEDENCE_NOT_APPLICABLE"


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


def construction_ok(events: list[dict]) -> tuple[bool, str]:
    pubs = [e for e in events if e["event"] == EV_PUBLISH]
    cons = [e for e in events if e["event"] == EV_CONSUME]
    faults = [e for e in events if e["event"] == EV_FAULT]
    if len(faults) == 0:
        return False, "no_event35"
    if len(faults) != 1:
        return False, "repeated_event35"
    f = faults[0]
    if f["src"] != EXPECTED_ENUM or f["dst"] != EXPECTED_SIDE:
        return False, "event35_enum_or_side"
    if f["role"] != 2:
        return False, "event35_role"
    if not pubs:
        return False, "no_publish"
    if not cons:
        return False, "no_consume"
    pub = pubs[-1]
    con = cons[-1]
    if not (pub["seq"] < con["seq"] < f["seq"]):
        return False, "order"
    if pub["serial"] != con["serial"] or pub["src"] != con["src"] or pub["dst"] != con["dst"]:
        return False, "tuple"
    return True, "ok"


def classify_r7_10_cell(blob: str, events: list[dict], env_captured: int, env_exact: int) -> dict:
    if env_captured != 1:
        return {
            "classification": INVALID_ENV,
            "runner_invalid": "YES",
            "product_fail": "NO",
            "continue_judge": "NO",
            "note": "cannot fabricate ENV_EXACT",
        }
    if env_exact != 1:
        return {
            "classification": INVALID_ENV,
            "runner_invalid": "YES",
            "product_fail": "NO",
            "continue_judge": "NO",
            "note": "env set mismatch",
        }
    ok, why = construction_ok(events)
    faults = [e for e in events if e["event"] == EV_FAULT]
    if len(faults) > 1:
        return {
            "classification": REPEATED_FAULT,
            "runner_invalid": "YES",
            "product_fail": "NO",
            "continue_judge": "NO",
            "note": why,
        }
    if not ok:
        return {
            "classification": NO_CONSTRUCTION,
            "runner_invalid": "YES",
            "product_fail": "NO",
            "continue_judge": "NO",
            "note": why,
        }
    halts = unique_halts(blob)
    last = last_halt(blob)
    xhup6 = sum(1 for w, r in halts if w == EXPECTED_WHAT and r == str(EXPECTED_REASON))
    reason4 = sum(1 for w, r in halts if w == BUG_WHAT and r == str(BUG_REASON))
    success = any(e["event"] == EV_SUCCESS for e in events)
    if success:
        return {
            "classification": WRONG_TERMINAL,
            "runner_invalid": "NO",
            "product_fail": "YES",
            "continue_judge": "YES",
            "note": "semantic success after peer-exit construction",
            "x_hup_reason6": xhup6,
            "x_direct_not_success_reason4": reason4,
        }
    if reason4 > 0 or (last and last[0] == BUG_WHAT and last[1] == str(BUG_REASON)):
        return {
            "classification": HISTORICAL_REASON4,
            "runner_invalid": "NO",
            "product_fail": "YES",
            "continue_judge": "YES",
            "note": "peer-exit construction classified as timeout reason=4",
            "x_hup_reason6": xhup6,
            "x_direct_not_success_reason4": reason4,
            "last_halt": f"{last[0]}/{last[1]}" if last else "",
        }
    if last and last[0] == EXPECTED_WHAT and last[1] == str(EXPECTED_REASON) and reason4 == 0:
        return {
            "classification": EXPECTED_HUP,
            "runner_invalid": "NO",
            "product_fail": "NO",
            "continue_judge": "YES",
            "note": "x-hup/6 after consume-exit; reason4=0",
            "x_hup_reason6": xhup6,
            "x_direct_not_success_reason4": 0,
            "last_halt": f"{last[0]}/{last[1]}",
        }
    return {
        "classification": WRONG_TERMINAL,
        "runner_invalid": "NO",
        "product_fail": "YES",
        "continue_judge": "YES",
        "note": "construction present but terminal is not x-hup/6",
        "x_hup_reason6": xhup6,
        "x_direct_not_success_reason4": reason4,
        "last_halt": f"{last[0]}/{last[1]}" if last else "",
    }


def classify_timeout_architecture(blob: str, events: list[dict]) -> dict:
    ok, why = construction_ok(events)
    last = last_halt(blob)
    reason4 = sum(1 for w, r in unique_halts(blob) if w == BUG_WHAT and r == str(BUG_REASON))
    if ok:
        return {
            "classification": HISTORICAL_REASON4 if reason4 else WRONG_TERMINAL,
            "runner_invalid": "NO",
            "product_fail": "YES" if reason4 else "NO",
            "continue_judge": "YES",
            "reason4_globally_forbidden": "NO",
            "r7_10_construction": "YES",
            "note": "timeout-architecture mode saw R7-10 construction; not a genuine-timeout fixture",
        }
    if last and last[0] == BUG_WHAT and last[1] == str(BUG_REASON) and reason4 > 0:
        return {
            "classification": GENUINE_TIMEOUT_NOT_R7_10,
            "runner_invalid": "NO",
            "product_fail": "NO",
            "continue_judge": "NO",
            "reason4_globally_forbidden": "NO",
            "r7_10_construction": "NO",
            "note": f"live-peer timeout/4 remains valid architecture; construction={why}",
            "x_direct_not_success_reason4": reason4,
        }
    return {
        "classification": TRACE_INCOMPLETE,
        "runner_invalid": "YES",
        "product_fail": "NO",
        "continue_judge": "NO",
        "reason4_globally_forbidden": "NO",
        "note": why,
    }


def classify_hup_precedence(blob: str) -> dict:
    halts = HALT_PAT.findall(blob)
    preserve = re.findall(r"GATEA_HUP_PRESERVE[^\n]*", blob)
    if not halts:
        return {
            "classification": HUP_PRECEDENCE_NOT_APPLICABLE,
            "runner_invalid": "YES",
            "product_fail": "NO",
            "continue_judge": "NO",
            "note": "no GATEA_FATAL_HALT",
        }
    first = halts[0]
    last = halts[-1]
    unique = unique_halts(blob)
    published_renderer = first[0].startswith("r-") or first[0].startswith("x-direct-not-success")
    later_hup = any(w in ("x-hup", "r-hup") and r == "6" for w, r in unique[1:]) if len(unique) > 1 else (
        last[0] in ("x-hup", "r-hup") and last[1] == "6" and (first[0], first[1]) != last
    )
    if later_hup and (last[0], last[1]) != (first[0], first[1]) and last[0] in ("x-hup", "r-hup"):
        return {
            "classification": HUP_PRECEDENCE_OVERWRITE,
            "runner_invalid": "NO",
            "product_fail": "YES",
            "continue_judge": "NO",
            "note": f"later HUP {last[0]}/{last[1]} overwrote first {first[0]}/{first[1]}",
            "first_halt": f"{first[0]}/{first[1]}",
            "last_halt": f"{last[0]}/{last[1]}",
            "hup_preserve_count": len(preserve),
        }
    if published_renderer and preserve:
        return {
            "classification": HUP_PRECEDENCE_PRESERVE,
            "runner_invalid": "NO",
            "product_fail": "NO",
            "continue_judge": "NO",
            "note": "published fatal retained; HUP preserve diagnostic only",
            "first_halt": f"{first[0]}/{first[1]}",
            "last_halt": f"{last[0]}/{last[1]}",
            "hup_preserve_count": len(preserve),
        }
    if len(unique) == 1:
        return {
            "classification": HUP_PRECEDENCE_PRESERVE,
            "runner_invalid": "NO",
            "product_fail": "NO",
            "continue_judge": "NO",
            "note": "single authoritative halt; no later HUP overwrite",
            "first_halt": f"{first[0]}/{first[1]}",
            "last_halt": f"{last[0]}/{last[1]}",
            "hup_preserve_count": len(preserve),
        }
    return {
        "classification": HUP_PRECEDENCE_NOT_APPLICABLE,
        "runner_invalid": "NO",
        "product_fail": "NO",
        "continue_judge": "NO",
        "note": "no later HUP overwrite of published fatal",
        "first_halt": f"{first[0]}/{first[1]}",
        "last_halt": f"{last[0]}/{last[1]}",
        "hup_preserve_count": len(preserve),
    }


def write_out(path: Path | None, rec: dict) -> None:
    lines = [f"{k}={v}" for k, v in rec.items()]
    text = "\n".join(lines) + "\n"
    if path:
        path.write_text(text)
    sys.stdout.write(text)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True,
                   choices=("r7-10-cell", "timeout-architecture", "hup-precedence"))
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
        rec = {
            "classification": TRACE_INCOMPLETE,
            "runner_invalid": "YES",
            "product_fail": "NO",
            "continue_judge": "NO",
            "note": f"seq conflicts {conflicts}",
        }
    elif args.mode == "r7-10-cell":
        rec = classify_r7_10_cell(blob, events, args.env_captured, args.env_exact)
    elif args.mode == "timeout-architecture":
        rec = classify_timeout_architecture(blob, events)
    else:
        rec = classify_hup_precedence(blob)

    rec.setdefault("x_hup_reason6", sum(
        1 for w, r in unique_halts(blob) if w == EXPECTED_WHAT and r == str(EXPECTED_REASON)))
    rec.setdefault("x_direct_not_success_reason4", sum(
        1 for w, r in unique_halts(blob) if w == BUG_WHAT and r == str(BUG_REASON)))
    rec["reason4_globally_forbidden"] = rec.get("reason4_globally_forbidden", "NO")
    rec["mode"] = args.mode
    write_out(Path(args.out) if args.out else None, rec)

    if rec.get("runner_invalid") == "YES":
        return 9
    if rec.get("product_fail") == "YES":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
