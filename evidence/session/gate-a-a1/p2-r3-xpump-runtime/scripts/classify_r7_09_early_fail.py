#!/usr/bin/env python3
"""R7-09 early-fail classifier.

Host-only helper used by run-r7-09-a07d66c.sh. Does not ADB, install, or launch.
Does not treat arbitrary early X death as PASS. Expected evidence must exist.

Frozen contract:
  event35 count=1 enum=9 side=1 role=X
  last GATEA_FATAL_HALT what=x-wrong-generation reason=6
  no PUBLISH/CONSUME/DRAW prerequisite
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EV_PUBLISH = 6
EV_SUCCESS = 17
EV_RELOCK_SRC = 18
EV_RELOCK_DST = 19
EV_REPAIR = 20
EV_ACK = 21
EV_PENDING_DEC = 22
EV_LEASE_RELEASE = 23
EV_EARLY_ACK = 32
EV_ACK_AFTER = 34
EV_FAULT = 35
EXPECTED_ENUM = 9
EXPECTED_SIDE = 1
EXPECTED_ROLE = 1
EXPECTED_WHAT = "x-wrong-generation"
EXPECTED_REASON = 6

PAT = re.compile(
    r"GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) "
    r"serial=(\d+) src=(\d+) dst=(\d+)"
)
HALT_PAT = re.compile(r"GATEA_FATAL_HALT what=(\S+) reason=(\d+)")
FORBIDDEN_AFTER_35 = {
    EV_SUCCESS, EV_RELOCK_SRC, EV_RELOCK_DST, EV_REPAIR,
    EV_ACK, EV_PENDING_DEC, EV_LEASE_RELEASE,
}

EXPECTED_EARLY_FAIL = "EXPECTED_EARLY_FAIL"
UNRELATED_EARLY_DEATH = "UNRELATED_EARLY_DEATH"
INVALID_ENV = "INVALID_ENV"
CONTINUE_TO_JUDGE = "CONTINUE_TO_JUDGE"
TRACE_INCOMPLETE = "TRACE_INCOMPLETE"


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


def last_halt(text: str) -> tuple[str | None, int | None]:
    matches = list(HALT_PAT.finditer(text))
    if not matches:
        return None, None
    last = matches[-1]
    return last.group(1), int(last.group(2))


def classify(
    *,
    follow: str,
    dump: str = "",
    ring: str = "",
    summary: str = "",
    x_alive: int = 0,
    env_captured: int = 0,
    env_exact: int = 0,
    died_before_startup_deadline: int = 0,
) -> dict:
    """Return a fail-closed classification. Never upgrades missing evidence to PASS."""
    blob = "\n".join([follow, dump, ring, summary])
    result = {
        "classification": TRACE_INCOMPLETE,
        "died_during_8s_invalid": "NO",
        "continue_judge": "NO",
        "runner_invalid": "NO",
        "fixture_required": "NO",
        "holder_required": "NO",
        "event35_count": 0,
        "event35_enum": None,
        "event35_side": None,
        "event35_role": None,
        "event35_gen": None,
        "event35_serial": None,
        "last_halt_what": None,
        "last_halt_reason": None,
        "expected_event35": "NO",
        "expected_halt": "NO",
        "forbidden_after_35": 0,
        "event32": 0,
        "later_publish": 0,
        "conflicts": [],
        "note": "",
    }
    if not env_captured or not env_exact:
        result["classification"] = INVALID_ENV
        result["runner_invalid"] = "YES"
        result["note"] = "cannot fabricate ENV_EXACT; environ must be captured from live /proc/X"
        return result

    events, conflicts = merge_by_seq(
        parse_events(follow) + parse_events(dump),
        parse_events(ring),
    )
    result["conflicts"] = conflicts
    faults = [e for e in events if e["event"] == EV_FAULT]
    result["event35_count"] = len(faults)
    what, reason = last_halt(blob)
    result["last_halt_what"] = what
    result["last_halt_reason"] = reason
    result["expected_halt"] = (
        "YES" if what == EXPECTED_WHAT and reason == EXPECTED_REASON else "NO"
    )
    result["event32"] = len([e for e in events if e["event"] == EV_EARLY_ACK])

    if len(faults) == 1:
        f = faults[0]
        result["event35_enum"] = f["src"]
        result["event35_side"] = f["dst"]
        result["event35_role"] = f["role"]
        result["event35_gen"] = f["gen"]
        result["event35_serial"] = f["serial"]
        result["expected_event35"] = (
            "YES"
            if f["src"] == EXPECTED_ENUM
            and f["dst"] == EXPECTED_SIDE
            and f["role"] == EXPECTED_ROLE
            else "NO"
        )
        after = [e for e in events if e["seq"] > f["seq"]]
        result["forbidden_after_35"] = len(
            [e for e in after if e["event"] in FORBIDDEN_AFTER_35]
        )
        result["later_publish"] = len(
            [e for e in after if e["event"] == EV_PUBLISH and e["serial"] > f["serial"] and f["serial"] != 0]
        )
        result["event32"] = len([e for e in events if e["event"] == EV_EARLY_ACK])

    expected = (
        result["expected_event35"] == "YES"
        and result["expected_halt"] == "YES"
        and len(faults) == 1
        and not conflicts
        and result["event32"] == 0
        and result["forbidden_after_35"] == 0
        and result["later_publish"] == 0
    )

    if died_before_startup_deadline and x_alive:
        result["classification"] = TRACE_INCOMPLETE
        result["runner_invalid"] = "YES"
        result["note"] = "died_before_startup_deadline=1 but x_alive=1 is inconsistent"
        return result

    if died_before_startup_deadline and not x_alive:
        if expected:
            result["classification"] = EXPECTED_EARLY_FAIL
            result["died_during_8s_invalid"] = "NO"
            result["continue_judge"] = "YES"
            result["note"] = (
                "X died during READY/first-inbound-frame window with frozen "
                "event35 enum=9 side=1 and x-wrong-generation/6; not DIED_DURING_8S INVALID"
            )
            return result
        result["classification"] = UNRELATED_EARLY_DEATH
        result["died_during_8s_invalid"] = "YES"
        result["runner_invalid"] = "YES"
        result["continue_judge"] = "NO"
        result["note"] = (
            "early X death without expected event35 enum=9 side=1 + "
            "x-wrong-generation/6 is fail-closed INVALID"
        )
        return result

    result["classification"] = CONTINUE_TO_JUDGE
    result["continue_judge"] = "YES"
    result["note"] = "X survived startup window; continue observation/judge; fixture still not required"
    return result


def format_result(r: dict) -> str:
    lines = [
        f"classification={r['classification']}",
        f"died_during_8s_invalid={r['died_during_8s_invalid']}",
        f"continue_judge={r['continue_judge']}",
        f"runner_invalid={r['runner_invalid']}",
        f"fixture_required={r['fixture_required']}",
        f"holder_required={r['holder_required']}",
        f"event35_count={r['event35_count']}",
        f"event35_enum={r['event35_enum']}",
        f"event35_side={r['event35_side']}",
        f"event35_role={r['event35_role']}",
        f"event35_gen={r['event35_gen']}",
        f"event35_serial={r['event35_serial']}",
        f"last_halt_what={r['last_halt_what']}",
        f"last_halt_reason={r['last_halt_reason']}",
        f"expected_event35={r['expected_event35']}",
        f"expected_halt={r['expected_halt']}",
        f"forbidden_after_35={r['forbidden_after_35']}",
        f"event32={r['event32']}",
        f"later_publish={r['later_publish']}",
        f"conflicts={r['conflicts']}",
        f"note={r['note']}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--follow", default="")
    p.add_argument("--dump", default="")
    p.add_argument("--ring", default="")
    p.add_argument("--summary", default="")
    p.add_argument("--x-alive", type=int, default=0)
    p.add_argument("--env-captured", type=int, default=0)
    p.add_argument("--env-exact", type=int, default=0)
    p.add_argument("--died-before-startup-deadline", type=int, default=0)
    p.add_argument("--out", default="")
    args = p.parse_args()
    follow = Path(args.follow).read_text(errors="replace") if args.follow else ""
    dump = Path(args.dump).read_text(errors="replace") if args.dump else ""
    ring = Path(args.ring).read_text(errors="replace") if args.ring else ""
    summary = Path(args.summary).read_text(errors="replace") if args.summary else ""
    r = classify(
        follow=follow, dump=dump, ring=ring, summary=summary,
        x_alive=args.x_alive, env_captured=args.env_captured,
        env_exact=args.env_exact,
        died_before_startup_deadline=args.died_before_startup_deadline,
    )
    text = format_result(r)
    if args.out:
        Path(args.out).write_text(text)
    sys.stdout.write(text)
    if r["runner_invalid"] == "YES":
        return 9
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
