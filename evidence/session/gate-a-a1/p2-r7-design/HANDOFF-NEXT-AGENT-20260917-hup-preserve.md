# Gate A P2 R7 — 2026-09-17 `a07d66c` HUP-preserve **ARTIFACT QUALIFIED**; device still `fdfb1ce`; R7 **BLOCKED at R7-05**

```
STATUS: R6 PASS on frozen 0f1e546 remains historical
        B-2 PASS on 7549e36 remains frozen
        fdfb1ce R7-04 PASS remains frozen
        R7-05 VALID FAIL halt_mismatch r-hup/6 remains frozen
        NEXT-037 source/host/CI/artifact QUALIFIED on a07d66c
        a07d66c NOT INSTALLED / NOT DEVICE-VALIDATED
        R7 BLOCKED at R7-05
        do not retry runtime-fdfb1ce/r7-05
        do not start R7-01+
DEVICE HEAD: fdfb1ce44b429897eda17c43bf33fbd37afe67f3 INSTALLED
REPAIR CANDIDATE: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82 NOT INSTALLED
CI: 35171333149
APK: 1.03.01-a07d66c-17.09.26
Stable :1: UNTOUCHED this task
HDMI: UNTOUCHED
Production Gate A: BLOCKED
```

Repair packet:
`evidence/session/gate-a-a1/p2-r7-design/GATE-A-P2-R7-HUP-PRESERVE-REPAIR-20260917.md`

Artifact packet:
`evidence/session/gate-a-a1/p2-r7-hup-preserve-ci-35171333149/P2-R7-HUP-PRESERVE-CI-ARTIFACT-PROVENANCE-20260917.md`

Historical R7-05 FAIL cell (immutable):
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-05/`

Do **not** overwrite it. Do **not** retry it.

R7-04 PASS packet remains:
`.../runtime-fdfb1ce/GATE-A-P2-R7-04-REQUALIFICATION-01-20260917.md`.

Prior R7-05 FAIL next-agent brief remains historical context:
`HANDOFF-NEXT-AGENT-20260917.md` (written before NEXT-037). This file supersedes its **Next**.

## Summary

1. NEXT-037 RCA proven: QUIESCED → X `PublishFatal(2)` → `x-direct-not-success/2` `_exit` → Activity HUP while bound emitted duplicate `r-hup/6`.
2. Narrow Activity HUP classifier: publishedFatal!=0 → `GATEA_HUP_PRESERVE` + `_exit(127)` without second halt; published==0 bound → `r-hup/6`; unbound → legacy cleanup.
3. No ABI / timeout / judge / X `x-hup` change.
4. Host + static + frozen judge 16/16 + historical rejudge unchanged.
5. Fork CI **35171333149** exact-head PASS. APK SHA256 `a25861b4…ace5` Build ID `ad3509c0…43f2`.
6. **Not installed. Not device-validated. Not R7-05 PASS. Not R7 PASS.**

## Next

Separately authorized **single fresh R7-05 device requalification** on **`a07d66c`** only.

Must verify:

- `post-draw-gl` → FAILED_QUIESCED → `x-direct-not-success reason=2` → X exit
- renderer HUP → no later `GATEA_FATAL_HALT r-hup reason=6`
- renderer still fail-stops → no normal poisoned cleanup
- forbidden success = 0
- frozen judge: `R7_PASS post-draw-gl`

Use a **fresh** candidate-specific evidence directory. Do **not** reuse
`runtime-fdfb1ce/r7-05/`.

Then **STOP before R7-01**.

Do **not** install without that grant.
Do **not** retry historical `runtime-fdfb1ce/r7-05`.
Do **not** retry R7-04 / B-2 / CASE_LOOP / historical cells.
Do **not** start R7-01+.
Do **not** start R8–R10.
Production Gate A remains BLOCKED.

Baseline row: fault-only classification → **R7-05 only**; do not automatically rerun B-2.
