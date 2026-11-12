# Gate A P2 R7 — 2026-09-17 `a07d66c` R7-05 **PASS**; R7 **IN PROGRESS** (next frozen cell R7-01)

```
STATUS: R6 PASS on frozen 0f1e546 remains historical
        B-2 PASS on 7549e36 remains frozen
        fdfb1ce R7-04 PASS remains frozen
        historical fdfb1ce R7-05 VALID FAIL r-hup/6 remains frozen
        a07d66c R7-05 PASS (requalification-01)
        R7 IN PROGRESS / NOT YET PASS
        next frozen cell is R7-01
        do not start R7-01 from this packet
        do not retry r7-05 on a07d66c or fdfb1ce
DEVICE HEAD: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82 INSTALLED
CI: 35171333149
APK: 1.03.01-a07d66c-17.09.26
Stable :1: PID 20146 UNTOUCHED
HDMI: UNTOUCHED observe-only
Production Gate A: BLOCKED
```

R7-05 PASS packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-a07d66c/GATE-A-P2-R7-05-A07D66C-REQUALIFICATION-01-20260917.md`

Cell (immutable):
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-a07d66c/r7-05-requalification-01/`

Historical FAIL cell remains immutable:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-05/`

Do **not** overwrite either. Do **not** retry either.

R7-04 PASS packet remains:
`.../runtime-fdfb1ce/GATE-A-P2-R7-04-REQUALIFICATION-01-20260917.md`.

Prior HUP-preserve artifact brief remains historical:
`HANDOFF-NEXT-AGENT-20260917-hup-preserve.md`. This file supersedes its **Next**.

## Summary

1. Installed `a07d66c` experimental-only. SHA/signer/Build ID MATCH CI **35171333149**.
2. One fresh R7-05: X **8418**, Activity **27372**, `EXACT_R7_05_ENV`.
3. PUBLISH serial=5 → DRAW → event 35 once src=5 dst=2 → FAILED_QUIESCED.
4. Authoritative halt `x-direct-not-success reason=2`. Then `GATEA_HUP_PRESERVE published=2`.
5. `r-hup reason=6` HALT count = 0. Frozen judge: `R7_PASS post-draw-gl`.
6. Forbidden-success zeros. No reason=4. No crash signal. Pre-cleanup X dead / Activity absent. `NO_X3_RESIDUE`. Stable 20146 unchanged.
7. Historical fdfb1ce R7-05 still FAILs frozen judge (`r-hup/6`).

## Next

Separately authorized **R7-01** only (`src-ready-miss` on installed `a07d66c`).
Do **not** execute R7-01 from this packet.
Do **not** retry `runtime-a07d66c/r7-05-requalification-01`.
Do **not** retry `runtime-fdfb1ce/r7-05`.
Do **not** retry R7-04 / B-2 / CASE_LOOP / historical cells.
Do **not** start R7-02+.
Do **not** start R8–R10.
Production Gate A remains BLOCKED.
