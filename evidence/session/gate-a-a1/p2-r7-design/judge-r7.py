#!/usr/bin/env python3
"""Judge one Gate A R7 fault-injection cell.

Order authority is telemetry seq. Event 35 must fire exactly once after the
frozen construction chain. Event 32 is always forbidden.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EV_PUBLISH = 6
EV_CONSUME = 7
EV_LOOKUP_OK = 8
EV_DRAW = 10
EV_COMPLETED = 14
EV_FAILED = 15
EV_FATAL = 16
EV_SUCCESS = 17
EV_RELOCK_SRC = 18
EV_RELOCK_DST = 19
EV_REPAIR = 20
EV_ACK = 21
EV_PENDING_DEC = 22
EV_LEASE_RELEASE = 23
EV_CALLBACK = 30
EV_EARLY_ACK = 32
EV_ACK_AFTER = 34
EV_FAULT = 35
EV_RETIRE = 36
ROLE_X = 1
ROLE_RENDERER = 2
XOP_PRESENT = 4
FORBIDDEN_AFTER_35 = {
    EV_SUCCESS, EV_RELOCK_SRC, EV_RELOCK_DST, EV_REPAIR,
    EV_ACK, EV_PENDING_DEC, EV_LEASE_RELEASE,
}

CELLS = {
    "src-ready-miss": {"cell": 1, "side": 2, "what": "r-gatea-DIRECT_LOOKUP_FAIL", "reason": 2, "need": ("publish", "consume")},
    "dst-ready-miss": {"cell": 2, "side": 2, "what": "r-gatea-DIRECT_LOOKUP_FAIL", "reason": 2, "need": ("publish", "consume")},
    "tuple-mismatch": {"cell": 3, "side": 2, "what": "r-gatea-direct-identity", "reason": 5, "need": ("publish", "consume")},
    "fbo-incomplete": {"cell": 4, "side": 2, "what": "r-gatea-DIRECT_LOOKUP_FAIL", "reason": 2, "need": ("publish", "lookup_ok")},
    "post-draw-gl": {"cell": 5, "side": 2, "what": "x-direct-not-success", "reason": 2, "need": ("publish", "draw"), "quiesced": True},
    "fence-create-fail": {"cell": 6, "side": 2, "what": "r-gatea-fence-create", "reason": 3, "need": ("publish", "draw")},
    "fence-timeout": {"cell": 7, "side": 2, "what": "r-gatea-fence-wait", "reason": 3, "need": ("publish", "draw"), "no_complete": True},
    "renderer-fatal-pre-fence": {"cell": 8, "side": 2, "what": "r-test-fatal-pre-fence", "reason": 6, "need": ("publish", "consume")},
    "wrong-generation-frame": {"cell": 9, "side": 1, "what": "x-wrong-generation", "reason": 6, "need": ()},
    "renderer-exit-after-consume": {"cell": 10, "side": 2, "what": "x-hup", "reason": 6, "need": ("publish", "consume"), "hup": True},
    "serial-wrap": {"cell": 11, "side": 1, "what": "x-serial-wrap", "reason": 6, "need": (), "no_serial0": True},
    "present-hold-complete": {"cell": 12, "side": 2, "what": "x-present-copy-wait", "reason": 4, "need": ("present_cb",), "present": True},
    "present-renderer-exit": {"cell": 13, "side": 2, "what": "x-hup", "reason": 6, "need": ("present_cb",), "present": True, "hup": True},
    "destroy-while-gpu-owned": {"cell": 14, "side": 1, "what": "x-destroy-in-lease", "reason": 7, "need": ("lease",)},
    "close-while-lease": {"cell": 15, "side": 1, "what": "x-close-in-lease", "reason": 8, "need": ("lease",)},
    "stale-ready-replay": {"cell": 16, "side": 2, "what": "x-wrong-generation", "reason": 6, "need": ()},
}

PAT = re.compile(
    r"GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) "
    r"serial=(\d+) src=(\d+) dst=(\d+)"
)
SUMMARY_PAT = re.compile(r"GATEA_SUMMARY where=")
HALT_PAT = re.compile(r"GATEA_FATAL_HALT what=(\S+) reason=(\d+)")


class JudgeFail(Exception):
    def __init__(self, code: str, extra: str = "") -> None:
        super().__init__(code if not extra else f"{code} {extra}")
        self.code = code
        self.extra = extra


def parse(text: str) -> list[dict]:
    events = []
    for m in PAT.finditer(text):
        seq, role, event, gen, serial, src, dst = (int(x) for x in m.groups())
        events.append({
            "seq": seq, "role": role, "event": event, "gen": gen,
            "serial": serial, "src": src, "dst": dst,
        })
    return events


def merge_by_seq(follow_events: list[dict], ring_events: list[dict]) -> list[dict]:
    by_seq: dict[int, dict] = {}
    for e in follow_events + ring_events:
        prev = by_seq.get(e["seq"])
        if prev is not None and prev != e:
            raise JudgeFail("telemetry_seq_conflict", f"seq={e['seq']}")
        by_seq[e["seq"]] = e
    return list(by_seq.values())


def order_events(events: list[dict]) -> list[dict]:
    if not events:
        raise JudgeFail("telemetry_empty")
    seqs = [e["seq"] for e in events]
    if len(seqs) != len(set(seqs)):
        raise JudgeFail("telemetry_seq_duplicate")
    ordered = sorted(events, key=lambda e: e["seq"])
    lo, hi = ordered[0]["seq"], ordered[-1]["seq"]
    if hi - lo + 1 != len(ordered):
        missing = [i for i in range(lo, hi + 1) if i not in set(seqs)]
        raise JudgeFail("telemetry_seq_gap", f"missing={missing[:16]}")
    if lo != 0:
        raise JudgeFail("telemetry_seq_prefix", f"lo={lo}")
    return ordered


def first_after(events: list[dict], after_seq: int, pred) -> dict | None:
    return next((e for e in events if e["seq"] > after_seq and pred(e)), None)


def halt_from(text: str) -> tuple[str | None, int | None]:
    matches = list(HALT_PAT.finditer(text))
    if not matches:
        return None, None
    last = matches[-1]
    return last.group(1), int(last.group(2))


def judge(
    cell: str,
    follow: str,
    *,
    ring: str = "",
    summary: str = "",
    halt_what: str | None = None,
    halt_reason: int | None = None,
    x_alive: int = 0,
    exit_signal: int = 0,
) -> str:
    spec = CELLS.get(cell)
    if spec is None:
        raise JudgeFail("unknown_cell", cell)
    blob = follow + "\n" + ring + "\n" + summary
    events = order_events(merge_by_seq(parse(follow), parse(ring)))
    if any(e["event"] == EV_EARLY_ACK for e in events):
        raise JudgeFail("event_32_present")
    faults = [e for e in events if e["event"] == EV_FAULT]
    if len(faults) == 0:
        raise JudgeFail("fault_missing")
    if len(faults) != 1:
        raise JudgeFail("fault_not_one_shot", f"count={len(faults)}")
    fired = faults[0]
    if fired["src"] != spec["cell"] or fired["dst"] != spec["side"] or fired["role"] != spec["side"]:
        raise JudgeFail(
            "fault_cell_or_side",
            f"src={fired['src']} dst={fired['dst']} role={fired['role']}",
        )
    serial_s = fired["serial"]
    gen = fired["gen"]

    def before(pred) -> dict | None:
        return next((e for e in events if e["seq"] < fired["seq"] and pred(e)), None)

    for kind in spec["need"]:
        found = None
        if kind == "publish":
            found = before(lambda e: e["event"] == EV_PUBLISH and e["role"] == ROLE_X)
        elif kind == "consume":
            found = before(lambda e: e["event"] == EV_CONSUME and e["role"] == ROLE_RENDERER)
        elif kind == "lookup_ok":
            found = before(lambda e: e["event"] == EV_LOOKUP_OK and e["role"] == ROLE_RENDERER)
        elif kind == "draw":
            found = before(lambda e: e["event"] == EV_DRAW)
        elif kind == "present_cb":
            found = before(lambda e: e["event"] == EV_CALLBACK and e["src"] == XOP_PRESENT)
        elif kind == "lease":
            found = before(lambda e: e["event"] == 2 and e["role"] == ROLE_X)
        if found is None:
            raise JudgeFail(f"missing_construction_{kind}")
        if found["gen"] != 0 and gen != 0 and found["gen"] != gen:
            raise JudgeFail(f"construction_gen_{kind}")

    after = [e for e in events if e["seq"] > fired["seq"]]
    for e in after:
        if e["event"] in FORBIDDEN_AFTER_35:
            raise JudgeFail("progress_after_fault", f"event={e['event']} seq={e['seq']}")
        if e["event"] == EV_PUBLISH and e["serial"] > serial_s and serial_s != 0:
            raise JudgeFail("later_publish_after_fault", f"serial={e['serial']}")
    if spec.get("present") and any(e["event"] == EV_ACK_AFTER for e in events):
        raise JudgeFail("event_34_on_present_cell")
    if spec.get("no_serial0") and any(
        e["event"] == EV_PUBLISH and e["serial"] == 0 for e in events
    ):
        raise JudgeFail("publish_serial_zero")
    if spec.get("no_complete") and any(
        e["event"] == EV_COMPLETED and e["serial"] >= serial_s and serial_s != 0
        for e in after
    ):
        raise JudgeFail("completed_after_fence_timeout")

    terminal = any(
        e["event"] in (EV_FAILED, EV_FATAL) and (e["gen"] == gen or gen == 0)
        for e in after
    ) or spec.get("hup") or spec.get("quiesced")
    if not terminal and not any(e["event"] in (EV_FAILED, EV_FATAL) for e in events):
        raise JudgeFail("missing_terminal")

    what = halt_what
    reason = halt_reason
    parsed_what, parsed_reason = halt_from(blob)
    if what is None:
        what = parsed_what
    if reason is None:
        reason = parsed_reason
    if what != spec["what"] or reason != spec["reason"]:
        raise JudgeFail("halt_mismatch", f"what={what} reason={reason}")
    if x_alive:
        raise JudgeFail("x_still_alive")
    if exit_signal:
        raise JudgeFail("exit_was_signal", f"sig={exit_signal}")
    if not (SUMMARY_PAT.search(blob) or SUMMARY_PAT.search(summary) or SUMMARY_PAT.search(follow)):
        raise JudgeFail("missing_summary")
    return f"R7_PASS {cell}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("cell")
    p.add_argument("follow")
    p.add_argument("--ring", default="")
    p.add_argument("--summary", default="")
    p.add_argument("--halt-what")
    p.add_argument("--halt-reason", type=int)
    p.add_argument("--x-alive", type=int, default=0)
    p.add_argument("--exit-signal", type=int, default=0)
    args = p.parse_args()
    follow = Path(args.follow).read_text()
    ring = Path(args.ring).read_text() if args.ring else ""
    summary = Path(args.summary).read_text() if args.summary else ""
    try:
        print(judge(
            args.cell, follow, ring=ring, summary=summary,
            halt_what=args.halt_what, halt_reason=args.halt_reason,
            x_alive=args.x_alive, exit_signal=args.exit_signal,
        ))
        return 0
    except JudgeFail as exc:
        print(f"R7_FAIL {exc.code} {exc.extra}".rstrip())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
