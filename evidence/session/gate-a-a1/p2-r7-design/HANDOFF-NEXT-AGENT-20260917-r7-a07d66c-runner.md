# Gate A P2 R7 — 2026-09-17 `a07d66c` reusable one-cell runner **QUALIFIED** (tooling only); R7-01 still **NOT RUN**; R7 **IN PROGRESS**

```
STATUS: R6 PASS on frozen 0f1e546 remains historical
        B-2 PASS on 7549e36 remains frozen
        fdfb1ce R7-04 PASS remains frozen
        historical fdfb1ce R7-05 VALID FAIL r-hup/6 remains frozen
        a07d66c R7-05 PASS remains frozen
        a07d66c one-cell R7 runner TOOLING QUALIFIED
        a07d66c R7-01 NOT RUN
        R7 IN PROGRESS / NOT YET PASS
        next frozen cell is still R7-01 / src-ready-miss
        do not execute R7-01 from this packet
DEVICE HEAD: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82 INSTALLED
CI: 35171333149
APK: 1.03.01-a07d66c-17.09.26
Stable :1: PID 20146 UNTOUCHED (this task did not read/kill/restart it)
HDMI: UNTOUCHED observe-only
Production Gate A: BLOCKED
```

Tooling packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/r7-a07d66c-runner-qualification-20260917/`

Runner:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-a07d66c.sh`
SHA256 `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded` size 20529

Historical R7-01 BLOCKED packet remains:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-a07d66c/GATE-A-P2-R7-01-A07D66C-BLOCKED-20260917.md`

Legal cell `.../runtime-a07d66c/r7-01/` is **ABSENT**. Keep it that way until a new single-cell device grant.

## Summary

1. Trusted a07d66c reusable one-cell R7 runner now exists. Host/static mapping tests PASS. Frozen judge 16/16 PASS. Judge SHA unchanged.
2. R7-01 is fully enabled as `r7-01|src-ready-miss|direct`. Completed R7-04 / R7-05 are REFUSE. No retry. No auto-next. Fresh destination required before mkdir.
3. This task did **not** install, start Activity, start X3, run a fixture, or create `runtime-a07d66c/r7-01/`.
4. Runner QUALIFIED ≠ R7-01 PASS. R7-01 remains NOT RUN.

## Next

Separately authorized **one** `a07d66c` R7-01 `src-ready-miss` `direct` device qualification using this frozen runner, destination `runtime-a07d66c/r7-01`, WAIT_S=12, one attempt.
Do **not** execute it from this packet.
Do **not** retry R7-05 / R7-04 / B-2.
Do **not** start R7-02+ from an R7-01 grant.
Production Gate A remains BLOCKED.
