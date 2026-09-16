# Gate A P2 CASE_LOOP — 2026-09-16 `feeaa56` INSTALLED stall-obs-01 **CASE_LOOP**; source fix **not installed**

```
STATUS: R6 PASS on frozen 0f1e546 remains historical
        Repair 0d72332 COMMITTED+CI; superseded on device
        B-2 R1 unset FAIL (serial 2370) + rerun1 FAIL REPRODUCED (serial 1810)
        stall RCA: CASE_LOOP CONFIRMED on feeaa56 stall-obs-01
        inner NOTIFY/SWAP/NEXT_FENCE waits FALSIFIED as the 2 s blocker
        timeout→Done ABSENT (repair held)
        stall-phase 27d8d1b stall-obs-01 STALL_NOT_OBSERVED historical
        notify-phase 1f85b80 stall-obs-01 STALL_NOT_OBSERVED historical
        function-coverage diagnostic feeaa56 CI 35076884763 INSTALLED
        stall-obs-01 CASE_LOOP (X 23034; timeout serial=86; NOTIFY 86/86 max 0.105 ms)
        CASE_LOOP source fix on src/f8-ahb-gatea-case-loop (parent 0d72332)
          waitWhileIdle: sticky writeIndex recheck + 8 ms timedwait
          EXA 2000 unchanged; host RED hang / GREEN 5 ms; NOT INSTALLED
        not B-2; do not retry stall-obs-01; do not install fix without new auth
        historical a7528bd B-2 FAIL / diagnostic-02 RCA FROZEN
        R7 support artifact a7528bd exists
        R7 qualification cells NOT STARTED
        R8–R10 NOT AUTHORIZED
DEVICE HEAD: feeaa569b86216126116c9bd99037a014efe0b79 INSTALLED
CASE_LOOP WT: src/f8-ahb-gatea-case-loop HEAD 327b028 branch fix/gatea-case-loop-wakeup-20260916
NOTIFY FN CI: 35076884763
NOTIFY FN APK: 1.03.01-feeaa56-16.09.26 INSTALLED
APK SHA256: a2d92ff9ecb948c5b3ac3c424727d12e97b9991f3b1b68d068a6828d744f3210
Build ID: 62d4a3f66adf3326513b7b79868c21c3ad8310f2
lastUpdateTime: 2026-09-16 17:21:53
NOTIFY FN WORKTREE: src/f8-ahb-gatea-notify-fn HEAD feeaa56
NOTIFY DIAG WORKTREE: src/f8-ahb-gatea-notify-diag HEAD 1f85b80
STALL DIAG WORKTREE: src/f8-ahb-gatea-stall-diag HEAD 27d8d1b
R7 WORKTREE: src/f8-ahb-gatea-r7 HEAD a7528bd (historical, not installed)
R6 WORKTREE: src/f8-ahb-gatea-r6-retire HEAD 0f1e546 (UNCHANGED)
Stable :1: PID 14604 UNTOUCHED
HDMI: UNTOUCHED
Last ADB: 10.191.48.13:37077
Production Gate A: BLOCKED
```

R6 runtime brief remains:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260916.md`.
Do not rewrite it. Do not silent-retry its cells.

Observation packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-feeaa56/GATE-A-P2-STALL-OBS-01-20260916.md`.

Fix packet:
`evidence/session/gate-a-a1/p2-r7-design/GATE-A-P2-CASE-LOOP-FIX-20260916.md`.

## Summary

1. Device is `feeaa56` experimental-only. Stable PID **14604** untouched.
2. One observational `p_b2_stress 1000` **CASE_LOOP**. X PID **23034**
   timeout serial **86** then fatal `x-exa-composite-wait` reason=4.
3. After serial 85 `NEXT_FENCE_EXIT`, X published serial 86. GLES tid 22960
   did not apply before 2000 ms. NOTIFY/SWAP/NEXT_FENCE were fast.
4. Cause: infinite `cond_wait` while `waitForNextFrame`, X cannot take
   Activity `stateLock`, Choreographer does not run during `lorieGpuCopyWait`.
5. Source fix: `waitWhileIdle` rechecks writeIndex and uses 8 ms timedwait
   while `waitForNextFrame`. Host test: legacy hangs 150 ms without signal;
   fixed wakes in 5 ms without signal. EXA 2000 verifier PASS.
6. Fix is **not installed**. B-2 remains BLOCKED. R7 not started.

## Next

Do **not** install the CASE_LOOP fix without **new explicit authorization**.
Do **not** retry `runtime-feeaa56/stall-obs-01`.
Do **not** retry `runtime-1f85b80/stall-obs-01` or `runtime-27d8d1b/stall-obs-01`.
Do **not** start B-2. Do **not** start R7 qualification. Do **not** change 2000 ms.
Do **not** mutate frozen R6.
