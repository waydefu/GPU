#!/usr/bin/env python3
"""R7-11 serial-wrap / no-serial0 classifier.

Host-only helper used by run-r7-11-a07d66c.sh. Does not ADB, install, or launch.
Does not treat missing event35 as PASS. Does not accept PUBLISH serial=0.

Frozen contract:
  event35 count=1 enum=11 side=1 role=X
  last GATEA_FATAL_HALT what=x-serial-wrap reason=6
  need=()  (prior PUBLISH is not required)
  no_serial0=true  (event=6 serial=0 is product FAIL even if halt is correct)
  seed after event35; next ++ wraps; PUBLISH of wrapping serial is unreachable
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
EXPECTED_ENUM = 11
EXPECTED_SIDE = 1
EXPECTED_ROLE = 1
EXPECTED_WHAT = "x-serial-wrap"
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

EXPECTED_WRAP = "EXPECTED_WRAP"
SERIAL0_LEAKED = "SERIAL0_LEAKED"
WRONG_TERMINAL = "WRONG_TERMINAL"
NO_EVENT35 = "NO_EVENT35"
REPEATED_SEED = "REPEATED_SEED"
UNRELATED_EARLY_DEATH = "UNRELATED_EARLY_DEATH"
INVALID_ENV = "INVALID_ENV"
CONTINUE_TO_JUDGE = "CONTINUE_TO_JUDGE"
TRACE_INCOMPLETE = "TRACE_INCOMPLETE"
FIXTURE_NOT_BOUND = "FIXTURE_NOT_BOUND"


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
    fixture_reached: int = 0,
    holder_reached: int = 0,
) -> dict:
    """Fail-closed serial-wrap classification. Never upgrades missing evidence to PASS."""
    blob = "\n".join([follow, dump, ring, summary])
    result = {
        "classification": TRACE_INCOMPLETE,
        "died_during_8s_invalid": "NO",
        "continue_judge": "NO",
        "runner_invalid": "NO",
        "product_fail": "NO",
        "fixture_required": "YES",
        "holder_required": "YES",
        "fixture_reached": int(fixture_reached),
        "holder_reached": int(holder_reached),
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
        "publish_serial0": 0,
        "pre_fault_publish": 0,
        "later_publish_after_35": 0,
        "forbidden_after_35": 0,
        "event32": 0,
        "conflicts": [],
        "counter_value_device_observed": "NOT_AVAILABLE",
        "seed_value_device_observed": "NOT_AVAILABLE",
        "seed_ordering": "source-proven consume-then-event35-then-UINT64_MAX-then-next-plus-plus",
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
    serial0 = [e for e in events if e["event"] == EV_PUBLISH and e["serial"] == 0]
    result["publish_serial0"] = len(serial0)

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
        before = [e for e in events if e["seq"] < f["seq"]]
        after = [e for e in events if e["seq"] > f["seq"]]
        result["pre_fault_publish"] = len(
            [e for e in before if e["event"] == EV_PUBLISH]
        )
        result["later_publish_after_35"] = len(
            [e for e in after if e["event"] == EV_PUBLISH]
        )
        result["forbidden_after_35"] = len(
            [e for e in after if e["event"] in FORBIDDEN_AFTER_35]
        )
        result["event32"] = len([e for e in events if e["event"] == EV_EARLY_ACK])

    if conflicts:
        result["classification"] = TRACE_INCOMPLETE
        result["runner_invalid"] = "YES"
        result["note"] = "seq conflict; fail-closed"
        return result

    if died_before_startup_deadline and x_alive:
        result["classification"] = TRACE_INCOMPLETE
        result["runner_invalid"] = "YES"
        result["note"] = "died_before_startup_deadline=1 but x_alive=1 is inconsistent"
        return result

    if len(faults) > 1:
        result["classification"] = REPEATED_SEED
        result["runner_invalid"] = "YES"
        result["note"] = "event35 count>1; one-shot seed rearmed; fail-closed INVALID"
        return result

    if result["publish_serial0"] > 0:
        result["classification"] = SERIAL0_LEAKED
        result["product_fail"] = "YES"
        result["continue_judge"] = "YES"
        result["note"] = (
            "PUBLISH event=6 serial=0 observed; wrap was not fail-stopped before "
            "publication; product FAIL even if last halt is x-serial-wrap/6"
        )
        return result

    if len(faults) == 0:
        if died_before_startup_deadline and not x_alive:
            result["classification"] = UNRELATED_EARLY_DEATH
            result["died_during_8s_invalid"] = "YES"
            result["runner_invalid"] = "YES"
            result["note"] = (
                "early X death without event35 enum=11; serial-wrap cannot fire "
                "before gateADirectPublishRect; fail-closed INVALID"
            )
            return result
        if what == EXPECTED_WHAT and reason == EXPECTED_REASON:
            result["classification"] = NO_EVENT35
            result["runner_invalid"] = "YES"
            result["note"] = "x-serial-wrap/6 without expected event35 hook; fail-closed INVALID"
            return result
        result["classification"] = NO_EVENT35
        result["runner_invalid"] = "YES"
        result["note"] = "missing event35 enum=11 side=1; fail-closed INVALID"
        return result

    if result["expected_event35"] != "YES":
        result["classification"] = NO_EVENT35
        result["runner_invalid"] = "YES"
        result["note"] = (
            f"event35 present but not enum=11 side=1 role=1 "
            f"src={result['event35_enum']} dst={result['event35_side']} "
            f"role={result['event35_role']}"
        )
        return result

    if fixture_reached != 1:
        result["classification"] = FIXTURE_NOT_BOUND
        result["runner_invalid"] = "YES"
        result["note"] = (
            "event35 enum=11 observed but the dedicated one-shot fixture was not "
            "reached; cannot bind wrap to p_r3_single_direct ×1; fail-closed INVALID"
        )
        return result

    if result["later_publish_after_35"] > 0 or result["forbidden_after_35"] > 0 or result["event32"] > 0:
        result["classification"] = SERIAL0_LEAKED if result["publish_serial0"] else WRONG_TERMINAL
        result["product_fail"] = "YES"
        result["continue_judge"] = "YES"
        result["note"] = (
            "progress after event35 (later PUBLISH / forbidden success / event32); "
            "product FAIL"
        )
        return result

    if result["expected_halt"] != "YES":
        result["classification"] = WRONG_TERMINAL
        result["product_fail"] = "YES"
        result["continue_judge"] = "YES"
        result["note"] = (
            f"expected event35 enum=11 side=1 but last halt is "
            f"{what}/{reason}; not x-serial-wrap/6; product FAIL"
        )
        return result

    if died_before_startup_deadline and not x_alive:
        # Fixture-required cell: wrap during the generic 8s window is only
        # valid if the one-shot fixture already ran (checked above).
        result["classification"] = EXPECTED_WRAP
        result["died_during_8s_invalid"] = "NO"
        result["continue_judge"] = "YES"
        result["note"] = (
            "X died after fixture-triggered wrap with event35 enum=11 side=1 "
            "and x-serial-wrap/6; no PUBLISH serial=0; not DIED_DURING_8S INVALID"
        )
        return result

    result["classification"] = EXPECTED_WRAP
    result["continue_judge"] = "YES"
    result["note"] = (
        "one-shot event35 enum=11 side=1 + x-serial-wrap/6 + publish_serial0=0; "
        "continue frozen judge; prior PUBLISH not required"
    )
    return result


def format_result(r: dict) -> str:
    keys = [
        "classification", "died_during_8s_invalid", "continue_judge",
        "runner_invalid", "product_fail", "fixture_required", "holder_required",
        "fixture_reached", "holder_reached", "event35_count", "event35_enum",
        "event35_side", "event35_role", "event35_gen", "event35_serial",
        "last_halt_what", "last_halt_reason", "expected_event35", "expected_halt",
        "publish_serial0", "pre_fault_publish", "later_publish_after_35",
        "forbidden_after_35", "event32", "conflicts",
        "counter_value_device_observed", "seed_value_device_observed",
        "seed_ordering", "note",
    ]
    return "".join(f"{k}={r[k]}\n" for k in keys)


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
    p.add_argument("--fixture-reached", type=int, default=0)
    p.add_argument("--holder-reached", type=int, default=0)
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
        fixture_reached=args.fixture_reached,
        holder_reached=args.holder_reached,
    )
    text = format_result(r)
    if args.out:
        Path(args.out).write_text(text)
    sys.stdout.write(text)
    if r["runner_invalid"] == "YES":
        return 9
    if r["product_fail"] == "YES":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
