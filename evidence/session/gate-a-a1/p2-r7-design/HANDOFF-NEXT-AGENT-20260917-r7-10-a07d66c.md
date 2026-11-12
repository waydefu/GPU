# Gate A P2 R7 — 2026-09-17 `a07d66c` R7-10 **FAIL**; R7 **IN PROGRESS** (10/13); next RCA only

```
STATUS: a07d66c INSTALLED
        R7-05 PASS frozen
        R7-01 PASS frozen
        R7-02 PASS frozen
        R7-03 PASS frozen
        R7-06 PASS frozen
        R7-07 PASS frozen
        R7-08 PASS frozen
        R7-09 PASS / DEVICE-QUALIFIED / frozen
        R7-11 PASS / DEVICE-QUALIFIED / frozen
        R7-10 FAIL frozen (x-direct-not-success/4; expected x-hup/6)
        R7 IN PROGRESS / NOT YET PASS / still 10/13
        next is NEXT-037 RCA only
        do not start R7-P1
        do not retry this cell
Stable :1: PID 20146 UNTOUCHED
Production Gate A: BLOCKED
```

Device packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-a07d66c/GATE-A-P2-R7-10-A07D66C-20260917.md`

Cell:
`.../runtime-a07d66c/r7-10/`  (X 12568; last halt `x-direct-not-success/4`)

## Summary

Construction PUBLISH→CONSUME_DIRECT→event35 enum=10 side=2 is present.
Renderer exited without its own GATEA_FATAL_HALT (`r-exit-after-consume` SUMMARY).
X did **not** emit `x-hup/6`. Last HALT is `x-direct-not-success reason=4`.
Frozen judge FAIL `halt_mismatch`. VALID FAIL. Not INVALID. Not BLOCKED.

## Next

NEXT-037 RCA only. Do **not** execute it from this packet.
Do **not** retry `runtime-a07d66c/r7-10`.
Do **not** start R7-P1.
Do **not** retry R7-11 / R7-09 / R7-08 / R7-07 / R7-06 / R7-03 / R7-02 / R7-01 / R7-05 / R7-04 / B-2.
Production Gate A remains BLOCKED.
