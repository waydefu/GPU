# Gate A P2 stall-phase diagnostic — 2026-09-16 `27d8d1b` INSTALLED; stall-obs **STALL_NOT_OBSERVED**

```
STATUS: R6 PASS on frozen 0f1e546 remains historical
        Repair 0d72332 COMMITTED+CI; superseded on device by 27d8d1b
        B-2 R1 unset FAIL (serial 2370) + rerun1 FAIL REPRODUCED (serial 1810)
        stall RCA NARROWED BUT NOT PROVEN (consume delay after S-1)
        stall-phase diagnostic 27d8d1b CI 35056388284 INSTALLED
        stall-obs-01 STALL_NOT_OBSERVED (1000/1000; timeout=0; CASE_A/B/C NOT CLASSIFIED)
        not B-2; do not retry stall-obs-01
        timeout→Done ABSENT on 0d72332 fail-stop cells (repair held)
        historical a7528bd B-2 FAIL / diagnostic-02 RCA FROZEN
        R7 cells NOT STARTED
        R8–R10 NOT AUTHORIZED
DEVICE HEAD: 27d8d1b4fcfc5456bac8720d36110eeeb7cbc9d3
DIAGNOSTIC CI: 35056388284
DIAGNOSTIC APK: 1.03.01-27d8d1b-16.09.26 INSTALLED experimental only
APK SHA256: 142b6e1fc6856c87c8dac0a006dd13a97c963bd480f8c2ac548d88325c0a45b0
Build ID: e8d859dd25120e21d5be13f72ffc0a7dcf385e2c
R7 WORKTREE: src/f8-ahb-gatea-r7 HEAD a7528bd (historical, not installed)
STALL DIAG WORKTREE: src/f8-ahb-gatea-stall-diag HEAD 27d8d1b
R6 WORKTREE: src/f8-ahb-gatea-r6-retire HEAD 0f1e546 (UNCHANGED)
Stable :1: PID 17922 UNTOUCHED
HDMI: UNTOUCHED
Production Gate A: BLOCKED
```

R6 runtime brief remains:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260916.md`.
Do not rewrite it. Do not silent-retry its cells.

## Summary

1. Device is `27d8d1b` experimental-only. Stable PID **17922** untouched.
2. Observe-only `STALL_PHASE` markers live on device. Install cell
   `runtime-27d8d1b/r0/`.
3. One authorized observation **STALL_NOT_OBSERVED** X PID **16420**:
   stress 1000/1000, EXA timeout 0, SWAP max 1.468 ms, NEXT_FENCE max
   4.806 ms, 3712 markers. Packet
   `runtime-27d8d1b/GATE-A-P2-STALL-OBS-01-20260916.md`.
4. CASE_A / CASE_B / CASE_C **not classified** (no 2s wait this cell).
   This does **not** falsify `0d72332` fail-stop cells.
5. B-2 remains BLOCKED. R7 not started. Timeout 2000 unchanged.

## Next

Do **not** retry `runtime-27d8d1b/stall-obs-01`. Do **not** start B-2.
Do **not** start R7. Do **not** change 2000 ms. Do **not** mutate frozen R6.
Further stall observation requires **new explicit authorization**.
