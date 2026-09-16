# Gate A P2 R7 — 2026-09-17 `fdfb1ce` R7-04 **PASS**; R7 overall **IN PROGRESS**; B-2 remains PASS

```
STATUS: R6 PASS on frozen 0f1e546 remains historical
        Repair 0d72332 COMMITTED+CI; RCA-1 timeout→Done FIXED / DEVICE-PROVEN
        Historical B-2 FAIL on 0d72332 FROZEN
        CASE_LOOP DEVICE-PROVEN on feeaa56 stall-obs-01 (frozen)
        327b028 SUPERSEDED
        device SHA fdfb1ce INSTALLED (R7-04 PASS)
        historical 7549e36 R7-04 FAIL FROZEN
        B-2 = PASS on 7549e36 (not rerun)
        R7-04 requalification-01 PASS (X 9891)
        R7 overall IN PROGRESS / NOT YET PASS
        r7-05..P2 NOT RUN
        R8–R10 NOT AUTHORIZED
DEVICE HEAD: fdfb1ce44b429897eda17c43bf33fbd37afe67f3 INSTALLED
REPAIR WT: src/f8-ahb-gatea-case-loop HEAD fdfb1ce
REPAIR CI: 35103216566 QUALIFIED / INSTALLED experimental-only
APK: 1.03.01-fdfb1ce-16.09.26
  SHA256 5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c
  Build ID 1d6bf3cd0eb06d12804e690679211ee7f34f998e
  lastUpdateTime 2026-09-17 00:54:07
R7 WORKTREE: src/f8-ahb-gatea-r7 HEAD a7528bd (historical, not installed)
R6 WORKTREE: src/f8-ahb-gatea-r6-retire HEAD 0f1e546 (UNCHANGED)
Stable :1: PID 24999 UNTOUCHED
HDMI: UNTOUCHED observe-only
Production Gate A: BLOCKED
```

R7-04 PASS packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/GATE-A-P2-R7-04-REQUALIFICATION-01-20260917.md`

Install packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r0/INSTALL-FDFB1CE-20260917.md`

Historical R7 FAIL packet remains:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-7549e36/GATE-A-P2-R7-QUALIFICATION-01-20260916.md`.
Do **not** overwrite it.

B-2 PASS packet remains:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-7549e36/GATE-A-P2-B2-REQUALIFICATION-02-20260916.md`.

R6 runtime brief remains:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260916.md`.
Do not rewrite it.

## Summary

1. Installed `fdfb1ce` experimental-only. Binding MATCH.
2. One fresh R7-04: X **9891**, env EXACT_R7_04_ENV, trigger ×1.
3. LOOKUP_OK → event 35 once serial=9 → last halt `r-gatea-DIRECT_LOOKUP_FAIL` reason=2.
4. `x-direct-not-success reason=4` = **0**. Preserve dump `x-observe-fatal` is not a halt.
5. Frozen `judge-r7.py` → `R7_PASS fbo-incomplete`. Forbidden-success zeros. `NO_X3_RESIDUE`.
6. Historical `7549e36` R7-04 still judges FAIL. Do not relabel it PASS.
7. Do **not** run R7-05 from this packet. Do **not** retry this cell.

## Next

Separately authorized R7 continuation beginning with **R7-05** `post-draw-gl` on **installed `fdfb1ce`**.
Do **not** retry `runtime-fdfb1ce/r7-04-requalification-01`.
Do **not** retry `runtime-7549e36/r7-qualification-01`.
Do **not** overwrite B-2 cells. Do **not** start R8–R10.
Do **not** execute R7-05 from this packet.
