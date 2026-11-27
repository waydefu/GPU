#!/usr/bin/env python3
"""Apply the frozen Stage 7.5 tiered gates (G1-G5, verdict) to one mode's run directory.

Usage: stage75_judge.py RUN_DIR MODE ENVELOPE_JSON [ENVELOPE_JSON ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f8_hybrid2_budget as budget  # noqa: E402

ENFORCED_EXEC_WORST_KIB = 26 * 1024
CEIL = {"memory_total_kib": 256 * 1024, "threads_total": 64, "fds_total": 192}


def judge(run: Path, mode: int, envelopes: list[dict]) -> dict:
    rows = [json.loads(x) for x in (run / f"matrix-{mode}.jsonl").read_text().splitlines()]
    cells = [r for r in rows if "cell" in r]
    final = {}
    for c in cells:  # a rerun (attempt 2) supersedes attempt 1 of the same cell
        final[c["cell"]] = c
    done = [r for r in rows if r.get("event") == "done"]
    aborted = [r for r in rows if r.get("event") == "abort"]
    g1 = "PASS" if done and not aborted and done[-1].get("route_audit") == "PASS" else "FAIL"
    g2_values = {c["G2"] for c in final.values()}
    g2 = "PASS" if g2_values == {"PASS"} else ("INVALID" if "INVALID" in g2_values and "FAIL" not in g2_values else "FAIL")

    idle = next(r["idle"] for r in rows if r.get("event") == "idle")
    c1 = sorted((c for c in final.values() if c["cell"].startswith("C1-")), key=lambda c: c["cycle"])
    relay_idle = median(c["relay_idle_pss_kib"] for c in c1) if c1 else None
    exec_fixture = max(e["max_peak_kib"] for e in envelopes)
    child_env = max([c["child_peak_pss_kib"] for c in final.values()]
                    + [max(e.get("child_peak_pss_kib", {}).values(), default=0) for e in envelopes])
    exec_env = max(int(exec_fixture * 1.25), ENFORCED_EXEC_WORST_KIB)
    theory = budget.budget_report(mode, daemon_idle_kib=int(idle["pss_kib"]), relay_idle_kib=int(relay_idle or 0),
                                  exec_envelope_kib=exec_env, child_envelope_kib=int(child_env))
    g3 = "PASS" if c1 and all(theory[k] <= v for k, v in CEIL.items()) else "FAIL"

    g4 = "PASS" if c1 and all(c["G4"] == "PASS" for c in c1) else "FAIL"
    idle_ret = idle["pss_kib"] + idle["swap_pss_kib"]
    rets = [c["retained_kib"] for c in c1]
    rising = len(rets) == 3 and rets[0] < rets[1] < rets[2] and rets[2] - rets[0] > 0.02 * idle_ret
    g5 = "PASS" if rets and all(r <= 1.10 * idle_ret for r in rets) and not rising else "FAIL"

    soak = final.get("SOAK")
    soak_ok = soak is None or soak.get("thermal") == "PASS"
    if g1 != "PASS" or g2 == "FAIL":
        verdict = "NO-GO"
    elif g2 == "INVALID":
        verdict = "INVALID"
    elif g3 == "PASS" and g4 == "PASS" and soak_ok:
        verdict = "GO"
    elif g4 == "FAIL" and g5 == "PASS" and g3 == "PASS":
        verdict = "HOLD (pending adoption of G5)"
    else:
        verdict = "HOLD"
    peaks = {k: max(c["peak"].get(k, 0) for c in final.values()) for k in ("pss_kib", "rss_kib", "threads", "fds",
                                                                          "swap_pss_kib", "private_dirty_kib")}
    return {
        "mode": mode, "candidate": (run / "candidate").read_text().strip(), "run": str(run),
        "G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "soak_thermal": soak and soak.get("thermal"),
        "verdict": verdict, "measured_peak": peaks,
        "g3_inputs": {"daemon_idle_pss_kib": idle["pss_kib"], "relay_idle_pss_kib": relay_idle,
                      "exec_fixture_peak_kib": exec_fixture, "exec_envelope_kib": exec_env, "child_envelope_kib": child_env},
        "theory": theory,
        "rss": {"idle_rss_kib": idle["rss_kib"], "drift_pct": [c["rss_drift_pct"] for c in c1],
                "idle_retained_kib": idle_ret, "retained_kib": rets},
        "attempts": {name: c["attempt"] for name, c in final.items()},
    }


def main() -> int:
    run, mode = Path(sys.argv[1]), int(sys.argv[2])
    envelopes = [json.loads(Path(p).read_text()) for p in sys.argv[3:]]
    print(json.dumps(judge(run, mode, envelopes), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
