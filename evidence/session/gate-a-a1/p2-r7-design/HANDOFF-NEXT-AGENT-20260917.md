# Gate A P2 R7 — 2026-09-17 `fdfb1ce` R7-05 **FAIL**; R7 **BLOCKED at R7-05**

```
STATUS: R6 PASS on frozen 0f1e546 remains historical
        B-2 PASS on 7549e36 remains frozen
        fdfb1ce R7-04 PASS remains frozen
        R7-05 VALID FAIL halt_mismatch r-hup/6
        R7 BLOCKED at R7-05
        do not retry r7-05
        do not start R7-01+
        NEXT-037 not executed from this packet
DEVICE HEAD: fdfb1ce44b429897eda17c43bf33fbd37afe67f3 INSTALLED
CI: 35103216566
APK: 1.03.01-fdfb1ce-16.09.26
Stable :1: PID 843 UNTOUCHED
HDMI: UNTOUCHED observe-only
Production Gate A: BLOCKED
```

R7-05 FAIL packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/GATE-A-P2-R7-05-QUALIFICATION-20260917.md`

Cell (immutable):
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-05/`

Do **not** overwrite it. Do **not** retry it.

R7-04 PASS packet remains:
`.../runtime-fdfb1ce/GATE-A-P2-R7-04-REQUALIFICATION-01-20260917.md`.

Prior R7-04 next-agent brief remains historical:
`HANDOFF-NEXT-AGENT-20260916.md`. Do not rewrite it.

## Summary

1. One fresh R7-05 on installed `fdfb1ce`: X **22704**, Activity **30140**, `EXACT_R7_05_ENV`.
2. PUBLISH serial=5 → DRAW → event 35 once src=5 dst=2.
3. Expected halt `x-direct-not-success reason=2` **did fire**, then last halt `r-hup reason=6`.
4. Frozen judge: `R7_FAIL halt_mismatch what=r-hup reason=6`.
5. Forbidden-success zeros. No reason=4. No crash signal. `NO_X3_RESIDUE`. Stable 843 unchanged.
6. Construction VALID. Product last-halt FAIL.

## Next

PR #7 **NEXT-037** (failure → RCA → narrow repair → artifact → fresh requalification) requires a **new** grant.
Do **not** execute NEXT-037 from this packet.
Do **not** retry `runtime-fdfb1ce/r7-05`.
Do **not** retry R7-04 / B-2 / CASE_LOOP / historical cells.
Do **not** start R7-01+.
Do **not** start R8–R10.
Production Gate A remains BLOCKED.
