# GPU Research Handoff — 2026-09-18 device `5a782f6` INSTALLED; GATE A P2 R7 **PASS / COMPLETE 13/13**; R8-C1 attempt-05 **R8_INVALID POST_END_OBSERVATION** frozen; C2–P2 **NOT RUN**; Production Gate A **BLOCKED**

> Device experimental is **`5a782f6`** on `com.waydefu.x11gpu` only
> (CI **35321447455**). Repair is **R8_INSTALL_BIND_PASS**. Fresh C1
> `runtime-5a782f6/r8-c1/attempt-05-obs-terminal/` is **R8_INVALID**
> `POST_END_OBSERVATION` (X 14186; frozen; no attempt-06). Historical
> `65938a4` (CI **35311343984**) is superseded on device. Historical `a4c8177` (CI **35295094951**) is superseded on device. Historical `abb27a65` (CI **35253641841**) is superseded on device. Historical `8545b26` (CI **35225593518**) is superseded on device. Historical `a07d66c` (CI **35171333149**) remains superseded. Repair-validation **CASE_LOOP_REPAIR_VALIDATED** remains
> frozen (X 19887; not B-2). B-2 requalification-01 is frozen **INVALID** (no TLS).
> B-2 requalification-02 is **B2_REQUALIFICATION_PASS** (X 32228; oracle 1514/1514;
> stress 100/100/1000; timeout=0; fatal=0; timeout→Done=0; pixels exact).
> Do **not** overwrite `b2-requalification-01` or `b2-requalification-02`.
> Historical `feeaa56` stall-obs-01 **CASE_LOOP** remains frozen. CASE_LOOP hardened
> SHA **`7549e36`** remains DEVICE-VALIDATED (superseded on device).
> Worktree `src/f8-ahb-gatea-case-loop` HEAD **`fdfb1ce`** (parent `7549e36`).
> Initial `327b028` is **SUPERSEDED**. Frozen R6 worktree
> `src/f8-ahb-gatea-r6-retire` HEAD **`0f1e54699d0b11a781f2c044fbc77505f8a53bd8`**
> — **do not mutate**. Historical **R6 PASS** on `0f1e546` remains last qualified R6.
> EXA Composite timeout repair remains **COMMITTED**
> `0d72332c0e591b2137262d06d7dcab704be49383`. Historical B-2 FAIL on `0d72332`
> (serial 2370 / rerun1 1810) stays frozen. Do **not** retry
> `runtime-feeaa56/stall-obs-01`, `runtime-1f85b80/stall-obs-01`,
> `runtime-27d8d1b/stall-obs-01`, `runtime-7549e36/repair-validation-01`,
> `runtime-7549e36/b2-requalification-01`, or historical `0d72332`/`a7528bd` cells.
> R7 **support artifact** `a7528bd` exists. Historical R7 qualification-01 is
> **BLOCKED** (r7-04 FAIL `halt_mismatch`; remaining cells NOT RUN; **do not overwrite**).
> Fatal-propagation repair **`fdfb1ce`** remains historical INSTALLED then superseded.
> R7-04 requalification-01 **R7_04_REQUALIFICATION_PASS** (X 9891). Historical R7-05
> **R7_05_QUALIFICATION_FAIL** (X 22704; last halt `r-hup reason=6`; frozen).
> HUP-preserve **`a07d66c`** INSTALLED. R7-05 requalification-01
> **R7_05_A07D66C_REQUALIFICATION_PASS** (X 8418; last halt `x-direct-not-success/2`;
> `GATEA_HUP_PRESERVE published=2`; r-hup/6 HALT=0). R7-01
> **R7_01_A07D66C_QUALIFICATION_PASS** (X 15029; last halt
> `r-gatea-DIRECT_LOOKUP_FAIL/2`). R7-02
> **R7_02_A07D66C_QUALIFICATION_PASS** (X 28625; event35 enum=2;
> last halt `r-gatea-DIRECT_LOOKUP_FAIL/2`). R7-03
> **R7_03_A07D66C_QUALIFICATION_PASS** (X 28326; event35 enum=3;
> last halt `r-gatea-direct-identity/5`). R7-06
> **R7_06_A07D66C_QUALIFICATION_PASS** (X 21795; DRAW then event35 enum=6;
> last halt `r-gatea-fence-create/3`). R7-07
> **R7_07_A07D66C_QUALIFICATION_PASS** (X 31938; DRAW then event35 enum=7;
> last halt `r-gatea-fence-wait/3`). R7-08
> **R7_08_A07D66C_QUALIFICATION_PASS** (X 14424; CONSUME then event35 enum=8;
> last halt `r-test-fatal-pre-fence/6`; DRAW absent). R7-09
> **R7_09_A07D66C_QUALIFICATION_PASS** (X 22076; event35 enum=9 side=1;
> last halt `x-wrong-generation/6`; PUBLISH absent). R7-11
> **R7_11_A07D66C_QUALIFICATION_PASS** (X 31764; event35 enum=11 side=1;
> last halt `x-serial-wrap/6`; PUBLISH serial=0=0). R7-10
> **R7_10_A07D66C_QUALIFICATION_FAIL** (X 12568; event35 enum=10 side=2;
> last halt `x-direct-not-success/4`; expected `x-hup/6`; **FROZEN**). R7-10 RCA
> **PROVEN**. Repair SHA **`8545b26`** is **INSTALLED** (CI **35225593518**).
> Dedicated 8545b26 R7-10 runner is **R7_10_8545B26_RUNNER_QUALIFIED**.
> 8545b26 R7-10 device requal is **R7_10_8545B26_REQUALIFICATION_PASS**
> (X 13115; last halt `x-hup/6`; reason4=0; classifier `EXPECTED_HUP`;
> judge `R7_PASS renderer-exit-after-consume`). Historical R7-P1 device
> **R7_P1_8545B26_QUALIFICATION_INVALID** (X 14331; classifier
> `NO_PRESENT_CALLBACK`; frozen). abb27a65 R7-P1 device
> **R7_P1_ABB27A65_QUALIFICATION_INVALID** (X 19686; classifier
> `PEER_DIED`; frozen). a4c8177 R7-P1 device
> **R7_P1_A4C8177_QUALIFICATION_INVALID** (X 24284; classifier
> `PEER_DIED` / `activity_pre_cleanup=ABSENT`; frozen). a4c8177 P1 validity-02 **R7_P1_A4C8177_QUALIFICATION_PASS** (X 1892). a4c8177 P2 **R7_P2_A4C8177_QUALIFICATION_PASS** (X 12663). R7 **COMPLETE 13/13**.
> Canonical next-agent brief:
> `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-05-invalid.md`.
> Historical install-blocked brief remains
> `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-obs-terminal-install-blocked.md`.
> Historical C1 attempt-04 INVALID brief remains
> `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-04-invalid.md`.
> Historical header-escalation brief remains:
> `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-header-escalation.md`.
> Historical d382c0a CI fail brief remains `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-ci-fail-d382c0a.md`.
> Historical prototype-era R8 CI fail brief remains `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-ci-fail.md`.
> Historical R7 complete brief remains `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-complete-a4c8177.md`.
> Historical INVALID brief remains `HANDOFF-NEXT-AGENT-20260918-r7-p1-a4c8177.md`.
> Historical abb27a65 INVALID brief `HANDOFF-NEXT-AGENT-20260918-r7-p1-abb27a65.md` remains historical.
> Historical validity brief `HANDOFF-NEXT-AGENT-20260918-r7-p1-validity.md` remains historical.
> Historical INVALID device brief `HANDOFF-NEXT-AGENT-20260917-r7-p1-8545b26.md` remains historical.
> Historical R7-P1 runner brief `HANDOFF-NEXT-AGENT-20260917-r7-p1-8545b26-runner.md` remains historical.
> Historical R7-10 PASS brief `HANDOFF-NEXT-AGENT-20260917-r7-10-8545b26.md` remains historical.
> Historical BLOCKED brief `HANDOFF-NEXT-AGENT-20260917-r7-10-8545b26-blocked.md` remains historical.
> Historical runner brief `HANDOFF-NEXT-AGENT-20260917-r7-10-8545b26-runner.md` remains historical.
> Historical RCA brief `HANDOFF-NEXT-AGENT-20260917-r7-10-rca.md` remains historical.
> Historical R7-10 FAIL brief `HANDOFF-NEXT-AGENT-20260917-r7-10-a07d66c.md` remains historical.
> RCA packet `GATE-A-P2-R7-10-RCA-REPAIR-20260917.md`.
> Historical R7-11 PASS brief `HANDOFF-NEXT-AGENT-20260917-r7-11-a07d66c.md` remains historical.
> Historical R7-11 BLOCKED brief `HANDOFF-NEXT-AGENT-20260917-r7-11-a07d66c-blocked.md` remains historical.
> Historical R7-11 runner brief `HANDOFF-NEXT-AGENT-20260917-r7-11-a07d66c-runner.md` remains historical.
> Historical R7-09 device brief `HANDOFF-NEXT-AGENT-20260917-r7-09-a07d66c.md` remains historical.
> Historical R7-09 runner brief `HANDOFF-NEXT-AGENT-20260917-r7-09-a07d66c-runner.md` remains historical.
> Historical R7-08 PASS brief `HANDOFF-NEXT-AGENT-20260917-r7-08-a07d66c.md` remains historical.
> Historical R7-07 PASS brief `HANDOFF-NEXT-AGENT-20260917-r7-07-a07d66c.md` remains historical.
> Historical R7-06 PASS brief `HANDOFF-NEXT-AGENT-20260917-r7-06-a07d66c.md` remains historical.
> Historical R7-03 PASS brief `HANDOFF-NEXT-AGENT-20260917-r7-03-a07d66c.md` remains historical.
> Historical R7-02 PASS brief `HANDOFF-NEXT-AGENT-20260917-r7-02-a07d66c.md` remains historical.
> Historical R7-01 PASS brief `HANDOFF-NEXT-AGENT-20260917-r7-01-a07d66c.md` remains historical.
> Historical runner brief `HANDOFF-NEXT-AGENT-20260917-r7-a07d66c-runner.md` remains historical.
> Historical R7-01 BLOCKED brief `HANDOFF-NEXT-AGENT-20260917-r7-01-blocked.md` remains historical.
> R7-05 PASS brief `HANDOFF-NEXT-AGENT-20260917-r7-05-a07d66c.md` remains historical.
> Prior HUP-preserve brief `HANDOFF-NEXT-AGENT-20260917-hup-preserve.md` remains historical.
> R7-05 FAIL brief `HANDOFF-NEXT-AGENT-20260917.md` remains historical.
> Prior R7-04 brief `HANDOFF-NEXT-AGENT-20260916.md` remains historical.
> Stable `:1` PID **20146** untouched. HDMI untouched. R8 CI **35304122983** / **35305368742** FAIL frozen; header grant **SCOPE_ESCALATION**.
> Production Gate A **BLOCKED**. Do **not** retry `runtime-a07d66c/r7-09`,
> `runtime-a07d66c/r7-08`,
> `runtime-a07d66c/r7-07`,
> `runtime-a07d66c/r7-06`,
> `runtime-a07d66c/r7-03`,
> `runtime-a07d66c/r7-02`,
> `runtime-a07d66c/r7-01`,
> `runtime-fdfb1ce/r7-05`, `runtime-a07d66c/r7-05-requalification-01`,
> `runtime-a07d66c/r7-11`, or `runtime-a07d66c/r7-10`.
> Do **not** retry `runtime-8545b26/r7-10` or `runtime-8545b26/r7-10-preflight`.
> Do **not** retry `runtime-8545b26/r7-p1`, `runtime-abb27a65/r7-p1`, or `runtime-a4c8177/r7-p1`.
> a07d66c reusable one-cell R7 runner remains **R7_A07D66C_RUNNER_QUALIFIED**
> (still `REVIEW_REQUIRED` for r7-09 and r7-11; do **not** lift; do **not** modify).
> a07d66c R7-09 dedicated early-fault runner remains **R7_09_A07D66C_RUNNER_QUALIFIED**.
> a07d66c R7-11 dedicated serial-wrap runner is **R7_11_A07D66C_RUNNER_QUALIFIED**
> (`run-r7-11-a07d66c.sh` SHA256 `74385947…c453`). R7-09 device cell is
> **PASS / DEVICE-QUALIFIED**. R7-11 device cell is **PASS / DEVICE-QUALIFIED**.
> Historical R7-10 device cell is **FAIL** (frozen). 8545b26 R7-10 runner is
> **R7_10_8545B26_RUNNER_QUALIFIED** (`run-r7-10-8545b26.sh` SHA256 `690a865d…54cd`).
> 8545b26 R7-10 device cell is **PASS / DEVICE-QUALIFIED**.
> 8545b26 R7-P1 dedicated runner is **R7_P1_8545B26_RUNNER_QUALIFIED**
> (`run-r7-p1-8545b26.sh` SHA256 `46c2289d…16ba7`). Historical R7-P1 device cell is
> **R7_P1_8545B26_QUALIFICATION_INVALID** (`runtime-8545b26/r7-p1/` X 14331;
> last halt none; classifier `NO_PRESENT_CALLBACK`; frozen). Validity RCA
> **PROVEN**; support **COMMITTED** `abb27a65` then superseded. Hold support
> **`a4c8177` INSTALLED** (CI **35295094951**). abb27a65 P1/P2 runners **QUALIFIED**
> (historical INVALID generation). a4c8177 P1/P2 runners **QUALIFIED**.
> abb27a65 R7-P1 device is
> **R7_P1_ABB27A65_QUALIFICATION_INVALID** (`runtime-abb27a65/r7-p1/` X 19686;
> classifier `PEER_DIED`; frozen). a4c8177 R7-P1 device is
> **R7_P1_A4C8177_QUALIFICATION_INVALID** (`runtime-a4c8177/r7-p1/` X 24284;
> classifier `PEER_DIED`; frozen). a4c8177 P1 validity-02 is
> **R7_P1_A4C8177_QUALIFICATION_PASS** (`runtime-a4c8177/r7-p1-validity-02/` X 1892).
> a4c8177 P2 is **R7_P2_A4C8177_QUALIFICATION_PASS** (`runtime-a4c8177/r7-p2/` X 12663).
> R7 **COMPLETE 13/13**. Next is **stop**; do not silent-retry.
> Do **not** retry `runtime-8545b26/r7-p1`, `runtime-abb27a65/r7-p1`, `runtime-a4c8177/r7-p1`,
> `runtime-a4c8177/r7-p1-validity-02`, or `runtime-a4c8177/r7-p2`.
> Do **not** retry `runtime-a07d66c/r7-10`.
> Do **not** retry `runtime-8545b26/r7-10`. Do **not** retry `runtime-8545b26/r7-10-preflight`.
> Do **not** retry `runtime-a07d66c/r7-11`. Do **not** silent-retry R8 CI **35304122983**, **35305368742**, **35311343984**, or **35321447455**. Do **not** install `bc25170` or `d382c0a`. Device is **`5a782f6` INSTALLED**. R8-C1 attempt-05 is **R8_INVALID** `POST_END_OBSERVATION` frozen. Do **not** retry C1 attempts 01–05. Do **not** start R8-C2.

```
P0 CLOSED
P1 CLOSED
GPU PRESENT QUALIFIED
FENCE QUALIFIED
FRAMETIMELINE BASELINE RECORDED
EXA COPY PASS
EXA SOLID PASS
P2-A CLOSED
P2-B.1 CLOSED / PASS
P2-B.2 PASS (R3)
S3 LINK / S3-Q1 / S3-E1b / S3-X1 CLOSED
S3 RUNTIME CLOSED — PASS WITH OBSERVABILITY LIMITATION
BUILD RECOVERY CLOSED
B3a C2 EXACT PROTOCOL QUALIFIED
PRODUCTION GATE A BLOCKED — OWNERSHIP/RESULT/LIFECYCLE PROTOCOL REQUIRED
GATE D ARCHITECTURE PASS-CANDIDATE / D0 DESIGN COMPLETE
S4 PRE-D0a HYGIENE PASS / RUNTIME PASS / D0a PASS (PERFORMANCE-POSITIVE)
GATE H HOLD
A1 MICROPROBE PASS (9/9 EXACT) / PRODUCTION GATE A NOT PASS
GATE A PROTOCOL DESIGN COMPLETE / PROTOTYPE AUTHORIZED (NO CODE YET)
GATE A IMPLEMENTATION PLAN REVIEW HOLD / P0 NOT AUTHORIZED
GATE A PROTOCOL ABI REVIEW R3 PASS / P0 AUTHORIZED (NO CODE YET)
GATE A P0 STATIC+COMPILE PASS / 2844a18 (NO PACKAGING/RUNTIME YET)
GATE A P0 CI PASS / 97401bc / ARTIFACT QUALIFIED (NO RUNTIME YET)
GATE A P1 REVIEW PASS / IMPLEMENTATION AUTHORIZED (BOUNDED, NO CODE YET)
GATE A P1 STATIC+COMPILE PASS / 5e9eb2a (NO CI/RUNTIME YET)
GATE A P1 CI PASS / 5e9eb2a / ARTIFACT QUALIFIED (NO RUNTIME YET)
GATE A P2 OWNERSHIP ARCHITECTURE PASS / IMPLEMENTATION AUTHORIZED (NO CODE YET)
GATE A P2 STATIC+COMPILE PASS / 82a87f4 (NO CI/RUNTIME YET)
GATE A P2 CI PASS / 82a87f4 / ARTIFACT QUALIFIED (NO RUNTIME YET)
GATE A P2 RUNTIME DESIGN BLOCKED / EXECUTION NOT AUTHORIZED (SOURCE+OBSERVABILITY DEFECTS)
GATE A P2 B1-B4 STATIC+COMPILE PASS / 15caa00
GATE A P2 B1-B4 CI PASS / 15caa00 / ARTIFACT QUALIFIED
GATE A P2 RUNTIME PHASE 1 FAIL / NEW SIGSEGV PID 31807 (R1 PROTO=0 STARTUP)
GATE A P2 R1 DIAGNOSTIC CI PASS / dd81ac0 / ARTIFACT QUALIFIED
GATE A P2 R1 DIAGNOSTIC RUNTIME PASS / dd81ac0 (T2 6/6 + OFF oracle/stress; 15caa00 SIGSEGV NON-REPRODUCED)
GATE A P2 R2 IMPORTED-AHB REJECTION PASS / dd81ac0
GATE A P2 R3 FAIL / dd81ac0 x-ready-timeout (Activity getenv)
GATE A P2 R3 REPAIR CI PASS / 98b0011 / ARTIFACT QUALIFIED
GATE A P2 R1 REQUAL PASS / 98b0011
GATE A P2 R2 REQUAL PASS / 98b0011
GATE A P2 R3 FAIL / 98b0011 x-ready-timeout (bind live, no REGISTER_READY)
GATE A P2 R3 PEEK-DIAG CI PASS / 6c7ee6f / ARTIFACT QUALIFIED
GATE A P2 R3 PEEK-DIAG INSTALLED / 6c7ee6f
GATE A P2 R1 T2 FAIL / 6c7ee6f SIGSEGV PID 21977 (dalvik-jit, OBSERVED)
GATE A P2 R1 T2 RERUN 6/6 PASS / 6c7ee6f (21977 NON-REPRODUCED)
GATE A P2 R1 OFF ORACLE/STRESS PASS / 6c7ee6f
GATE A P2 R2 IMPORTED-AHB REJECTION PASS / 6c7ee6f
GATE A P2 R3 FAIL / 6c7ee6f x-ready-timeout (HANDLE live, GL drain never ran)
GATE A P2 R3 DRAIN-WAIT CI PASS / 8479997 / ARTIFACT QUALIFIED
GATE A P2 R3 DRAIN-WAIT INSTALLED / 8479997
GATE A P2 R1 REQUAL PASS / 8479997 (oracle/stress; T2 6/6 not rerun)
GATE A P2 R2 REQUAL PASS / 8479997
GATE A P2 R3 FAIL / 8479997 x-ready-timeout (DRAIN ran, no READY)
GATE A P2 RUNTIME PAUSED 2026-09-14 (user stop)
GATE A P2 R3 TERMINAL/OBSERVABILITY CI PASS / 88e3f17 / ARTIFACT QUALIFIED
GATE A P2 R1 REQUAL PASS / 88e3f17 (oracle/stress; T2 6/6 not rerun)
GATE A P2 R2 REQUAL PASS / 88e3f17 (imported-AHB rejection, indirect evidence)
GATE A P2 R3 FAIL / 88e3f17 (VALIDATE_TERMINAL_READY then x-ready-timeout)
GATE A P2 RUNTIME STOP AFTER R3 2026-09-14
GATE A P2 R3 ROOT CAUSE PROVEN / X MAIN-THREAD SELF-WAIT
GATE A P2 R3 RECORD-AWARE XPUMP DESIGN PASS / IMPLEMENTATION AUTHORIZED
GATE A P2 R3 XPUMP CI PASS / d9b7f60 / ARTIFACT QUALIFIED
GATE A P2 R3 XPUMP INSTALLED / d9b7f60
GATE A P2 R1 UNSET PASS / d9b7f60
GATE A P2 R1 PROTO=0 FAIL / d9b7f60 SIGSEGV PID 21639
GATE A P2 R1 PROTO=0 RERUN PASS / d9b7f60 (21639 NON-REPRODUCED, ROOT CAUSE NOT PROVEN)
GATE A P2 R3 PASS / d9b7f60 (X consumed READY; 88e3f17 timeout falsified on this APK)
GATE A P2 R1 PROTO=0 21639 FORENSICS / dalvik-jit class (same family as 21977)
GATE A P2 R2 IMPORTED-AHB REJECTION PASS / d9b7f60 (GATEA_EVENT=0, modifier 1255 ×2)
GATE A P2 R4 PRODUCTION ORACLE PASS / d9b7f60 (1514/1514, N=8 counters match)
GATE A P2 R5 SAME-AHB CYCLES FAIL / d9b7f60 (hang after serial 819 RELOCK_DST; 1024/4096 not reached)
GATE A P2 R5 BOUNDED RERUN FAIL REPRODUCED / d9b7f60 (X 31265 hang after serial 1283 RELOCK_DST; 1/16/64/256/1024 pixel PASS; 4096 not reached)
GATE A P2 R5 ROOT CAUSE PROVEN / AF_UNIX TINY-RECORD BACKPRESSURE + LOCK-ACROSS-WRITE CYCLE
GATE A P2 R5 SOURCE STATIC+COMPILE PASS / 37d8393
GATE A P2 R5 CI PASS / 37d8393 / ARTIFACT QUALIFIED
GATE A P2 R5 CORRECTED INSTALLED / 37d8393
GATE A P2 R5 HANG FALSIFIED / 37d8393 (4096 PIXEL PASS; HARNESS COUNTERS FAIL LOGCAT-DROP)
GATE A P2 R5 COUNTER RECAPTURE FAIL / 37d8393 (publish/fence=4096; ack=4095 logcat-drop)
GATE A P2 R5 PASS / 37d8393 (hang FALSIFIED; 4096 PIXEL PASS; logcat ack-drop not blocking)
GATE A P2 R6 BOUNDED CLIENT PASS / 37d8393 (CLIENT_OK; NOT DESIGN-COMPLETE)
GATE A P2 R6 DESIGN COMPLETE / SOURCE COMMITTED 9369553 (ROLLBACK 37d8393)
GATE A P2 R6 CI PASS / 9369553 / ARTIFACT QUALIFIED
GATE A P2 R6 INSTALLED / 9369553
GATE A P2 R6-D1 FAIL / 9369553 (pixels fail=1; in-flight queue NOT CONSTRUCTED)
GATE A P2 R6-D1 retry1 FAIL / 9369553 (schedule PROVEN; pixels fail=1 got0=00000001)
GATE A P2 R6-D1 retry2 OBSERVED / 9369553 (X 28170 ART JIT SIGSEGV during 8s; fixture never ran)
GATE A P2 R6-D1 retry3 FAIL / 9369553 (pixels PASS; CopyArea BadGC=13; 28170 NON-REPRODUCED)
GATE A P2 R6-D1 retry4 FAIL / 9369553 (CLIENT_OK; pixels PASS; wait-pump FALSIFIED; missing Present CALLBACK xop=4)
GATE A P2 R6-D1 PASS / 9369553 (retry5 X 16168; Present ASYNC|COPY; pixels exact; CALLBACK xop=4)
GATE A P2 R6-D2-INFLIGHT FAIL / 9369553 (X 17596; missing DIRECT_ADMIT_REJECT)
GATE A P2 R6-D2-INFLIGHT retry1 FAIL / 9369553 (X 20856; reject PROVEN; PUBLISH serial=8 before COMPLETED serial=6; D2-OOM NOT RUN)
GATE A P2 R6-D2 COMPLETED ROOT CAUSE PROVEN / LEGACY COPY NO EVENT_COMPLETED
GATE A P2 R6-D2 COMPLETED TELEMETRY COMMITTED / 54ff35b
GATE A P2 R6-D2 WAIT-OR-FATAL COMMITTED / 7092d0c then 95e6f96
GATE A P2 R6 WAIT-OR-FATAL CI FAIL / 7092d0c / KEEP malformed xserver.patch
GATE A P2 R6 WAIT-OR-FATAL CI PASS / 95e6f96 / ARTIFACT QUALIFIED
GATE A P2 R6 WAIT-OR-FATAL INSTALLED / 95e6f96
GATE A P2 R6-D2-INFLIGHT FAIL / 95e6f96 (COMPLETED serial 6 PROVEN; reject overlap NOT CONSTRUCTED)
GATE A P2 R6-D2-INFLIGHT retry1-4 FAIL REPRODUCED / 95e6f96 (X 24492/7952/13797/19332; GPU < CPU dispatch; COMPLETED PROVEN)
GATE A P2 R6-D2-INFLIGHT PHYSICAL RACE ANALYZED / 95e6f96 (5 cells kept; native code 100% sound)
GATE A P2 R6 RETIREMENT CI PASS / 0f1e546 / ARTIFACT QUALIFIED
GATE A P2 R6 RETIREMENT INSTALLED / 0f1e546
GATE A P2 R6-D1 PASS / 0f1e546 (X 29152; first attempt)
GATE A P2 R6-D2-INFLIGHT PASS / 0f1e546 (X 31369; QUIESCENT-ADMIT)
GATE A P2 R6-D2-OOM PASS / 0f1e546 (X 2638; event 33 executed; ACK after cover)
GATE A P2 R6 PASS / 0f1e546
R7 SUPPORT ARTIFACT COMMITTED / a7528bd (termux-x11 fork CI; NOT qualification)
B-2 PASS / 7549e36 requalification-02
R7 QUALIFICATION-01 BLOCKED / r7-04 halt_mismatch (remaining cells NOT RUN)
R7 FATAL-PROPAGATION REPAIR / fdfb1ce CI 35103216566 ARTIFACT QUALIFIED / INSTALLED
R7-04 REQUALIFICATION-01 / R7_04_REQUALIFICATION_PASS (fdfb1ce X 9891)
R7-05 QUALIFICATION / R7_05_QUALIFICATION_FAIL (fdfb1ce X 22704 halt_mismatch r-hup/6; frozen)
R7-05 HUP-PRESERVE REQUAL / R7_05_A07D66C_REQUALIFICATION_PASS (a07d66c X 8418; R7 IN PROGRESS)
R7-10 HUP CONTAINMENT / 8545b26 INSTALLED / R7_10_8545B26_REQUALIFICATION_PASS (X 13115; last halt x-hup/6)
R7-P1 DEVICE QUALIFICATION / R7_P1_8545B26_QUALIFICATION_INVALID (X 14331; NO_PRESENT_CALLBACK; FROZEN)
R7-P1 TARGET-ARM / abb27a65 SUPERSEDED / R7_P1_ABB27A65_QUALIFICATION_INVALID (X 19686; PEER_DIED; FROZEN)
R7-P1 HOLD SUPPORT / a4c8177 INSTALLED CI 35295094951 / R7_P1_A4C8177_QUALIFICATION_INVALID (X 24284; PEER_DIED; FROZEN)
R7-P1 LIVENESS-V2 / R7_P1_A4C8177_QUALIFICATION_PASS (validity-02 X 1892 EXPECTED_PRESENT_TIMEOUT)
R7-P2 / R7_P2_A4C8177_QUALIFICATION_PASS (X 12663 EXPECTED_PRESENT_RENDERER_EXIT)
GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
R8 PR #8 AUTHORITY RECONCILED DOCS-ONLY / still PROPOSED / NOT STARTED
R8 DESIGN ACCEPTED ON A4C8177 / DESIGN_FROZEN (this implementation generation)
R8 SUPPORT HOST VERIFIED
R8 CI FAIL / bc25170 CI 35304122983 (InitOutput.c undeclared lorieExaDestroyPixmap; frozen; no rerun)
R8 PROTOTYPE REPAIR / d382c0a (InitOutput.c +1; parent bc25170)
R8 CI FAIL / d382c0a CI 35305368742 (lorie_r8_test.c PixmapPtr/XMD; frozen; no rerun)
R8 HEADER REPAIR SCOPE ESCALATION / pixmap.h not pointer-only; checkpoint sizeof 72 != sz 64; no commit
NOTIFY STALL DIAGNOSTIC INSTALLED / 1f85b80 (stall-obs-01 STALL_NOT_OBSERVED; NOT B-2; superseded on device)
NOTIFY FN DIAGNOSTIC INSTALLED then superseded / feeaa56 (stall-obs-01 CASE_LOOP serial 86; NOT B-2; frozen)
CASE_LOOP SOURCE FIX / 327b028 SUPERSEDED; hardened 7549e36 CI 35084701124 QUALIFIED INSTALLED
CASE_LOOP REPAIR-VALIDATION / CASE_LOOP_REPAIR_VALIDATED (not B-2)
B-2 REQUALIFICATION-01 / B2_REQUALIFICATION_INVALID (frozen; no TLS)
B-2 REQUALIFICATION-02 / B2_REQUALIFICATION_PASS
PRODUCTION GATE A BLOCKED
```

Do not reopen P0/P1/P2-A/P2-B.1/P2-B.2. Do not treat ±1 UNORM as PASS. Do not open a `termux/termux-x11` origin PR. Docs-only PRs on `waydefu/GPU` are records, not qualification. Do not touch stable `:1`. Do not leave XFCE/xfwm running on experimental `:3` as a daily session; the R3 bounded window already passed and was stopped.

## Current Gate A P2 runtime (2026-09-18 device 5a782f6 INSTALLED; GATE A P2 R7 PASS / COMPLETE 13/13; R8-C1 attempt-05 INVALID frozen; C2–P2 NOT RUN; Production BLOCKED)

Next-agent brief:
`evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-05-invalid.md`.
Historical install-blocked brief remains:
`evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-obs-terminal-install-blocked.md`.
Historical attempt-04 INVALID brief remains:
`evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-04-invalid.md`.
Historical attempt-02 BLOCKED brief remains:
`evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-02-blocked.md`.
Historical C1 INVALID brief remains:
`evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-invalid.md`.
Historical install-blocked brief remains:
`evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-install-blocked.md`.
Historical header-escalation brief remains:
`evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-header-escalation.md`.
Historical d382c0a CI fail brief remains:
`evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-ci-fail-d382c0a.md`.
Historical prototype-era R8 CI fail brief remains:
`evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-ci-fail.md`.
Historical R7 complete brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-complete-a4c8177.md`.
Historical first-P1 INVALID brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-p1-a4c8177.md`.
Historical abb27a65 INVALID brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-p1-abb27a65.md`.
Historical validity brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-p1-validity.md`.
Historical INVALID device brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-p1-8545b26.md`.
Historical R7-P1 runner brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-p1-8545b26-runner.md`.
Historical R7-10 PASS brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-10-8545b26.md`.
Historical BLOCKED brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-10-8545b26-blocked.md`.
Historical R7-10 FAIL brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-10-a07d66c.md`.
Historical R7-11 PASS brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-11-a07d66c.md`.
Historical R7-11 BLOCKED brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-11-a07d66c-blocked.md`.
Historical R7-11 runner brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-11-a07d66c-runner.md`.
Historical R7-09 device brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-09-a07d66c.md`.
Historical R7-09 runner brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-09-a07d66c-runner.md`.
Historical R7-08 PASS brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-08-a07d66c.md`.
Historical R7-07 PASS brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-07-a07d66c.md`.
Historical R7-06 PASS brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-06-a07d66c.md`.
Historical R7-03 PASS brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-03-a07d66c.md`.
Historical R7-02 PASS brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-02-a07d66c.md`.
Historical R7-01 PASS brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-01-a07d66c.md`.
Historical runner brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-a07d66c-runner.md`.
Historical R7-01 BLOCKED brief remains:
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-01-blocked.md`.
Frozen R6 runtime brief remains:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260916.md`.
Prior `95e6f96` D2 physical-race brief remains historical:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md`.
Prior `88e3f17` R3 FAIL remains historical:
`evidence/session/gate-a-a1/p2-r3-terminal-runtime/HANDOFF-NEXT-AGENT-20260914.md`.

| | |
|---|---|
| Worktree (installed source) | Device **`5a782f6`** INSTALLED (`feat/gatea-r8-lifecycle-support-20260918`, parent `65938a4`); historical `65938a4` superseded on device; historical `a4c8177` superseded on device; historical Present-target-arm `abb27a65` superseded on device; historical HUP-containment `8545b26` superseded on device; historical HUP-preserve `a07d66c` superseded on device; CASE_LOOP repair **DEVICE-VALIDATED** (historical); B-2 **PASS** (`runtime-7549e36/b2-requalification-02/`); `b2-requalification-01` INVALID frozen; historical notify-fn `feeaa56` **superseded on device**; historical R7 **BLOCKED** (`runtime-7549e36/r7-qualification-01/r7-04/` X 31122 halt_mismatch, frozen); R7-04 requal **PASS** (`runtime-fdfb1ce/r7-04-requalification-01/` X 9891); historical R7-05 **FAIL** (`runtime-fdfb1ce/r7-05/` X 22704 r-hup/6, frozen); a07d66c R7-05 **PASS** (`runtime-a07d66c/r7-05-requalification-01/` X 8418); a07d66c R7-01 **PASS** (`runtime-a07d66c/r7-01/` X 15029); a07d66c R7-02 **PASS** (`runtime-a07d66c/r7-02/` X 28625); a07d66c R7-03 **PASS** (`runtime-a07d66c/r7-03/` X 28326); a07d66c R7-06 **PASS** (`runtime-a07d66c/r7-06/` X 21795); a07d66c R7-07 **PASS** (`runtime-a07d66c/r7-07/` X 31938); a07d66c R7-08 **PASS** (`runtime-a07d66c/r7-08/` X 14424); R7 **support** worktree `a7528bd` (not installed); frozen R6 `src/f8-ahb-gatea-r6-retire` **`0f1e546`** clean |
| R6 implementation worktree | `/root/projects/GPU加速/src/f8-ahb-gatea-r6-retire` branch `fix/gatea-r6-present-retirement-20260915` HEAD **`0f1e546`** (fork in sync; origin ABSENT) |
| Historical R6 source | `/root/projects/GPU加速/src/f8-ahb-gatea-r6` HEAD **`95e6f96`** clean; do not overwrite its cells |
| Control | `/root/projects/GPU加速/src/f8-ahb-gatea-a1` HEAD **`88e3f17`** clean |
| Installed APK | `com.waydefu.x11gpu` `1.03.01-5a782f6-18.09.26` CI **35321447455** |
| APK SHA256 | `43590412d5537339bb6822d0157e135b5fc00a7cca80570d987adc87c15ba78e` MATCH on-device |
| Build ID | `d032a8188b4f768a523b4c06cfe62a813950b02a` MATCH |
| lastUpdateTime | 2026-09-18 16:19:04 |
| Stable | `com.termux.x11` `1.03.01-11b82d9-06.09.26` PID **20146** `:1` UNTOUCHED (package lastUpdateTime 2026-09-07 22:55:03 unchanged) |
| Last ADB | `10.191.48.13:38361` live-fetched `_adb-tls-connect._tcp.local.` (5a782f6 install + C1 attempt-05; isolated 5038 PID 3065) |
| R1 unset | PASS (X 19391; 1514/1514; stress 100/100/1000; GATEA_EVENT=0) |
| R1 PROTO=0 first | FAIL SIGSEGV X PID **21639** (`si_addr=0`, Uctx PC `0x4800229c` in `dalvik-jit-code-cache`) OBSERVED |
| R1 PROTO=0 rerun | PASS X PID **27435**; 1514/1514; stress 100/100/1000; GATEA_EVENT=0; **21639 NON-REPRODUCED** |
| R3 | **PASS** X PID **8034**; pixels 64 exact `got0=00804000`; X `role=1 event=1` consumed READY; no `x-ready-timeout` |
| R2 | **PASS** X PID **28042**; both imported cells exact `got0=00804000`; unique DRI3 modifier 1255 ×2; GATEA_EVENT=0 |
| R4 | **PASS** X PID **29807**; 1514/1514 fail=0 maxΔ=0 Xnz=0; N=8 publish=consume=lookup=draw=fence=completed=success=ack |
| R5 first | **FAIL** X PID **14858**; checkpoints 1/16/64/256 exact; hang after serial **819** RELOCK_DST (no ACK/lease); 1024/4096 not reached; fixture SIGTERM 143 |
| R5 rerun | **FAIL REPRODUCED** X PID **31265**; checkpoints 1/16/64/256/1024 exact; hang after serial **1283** RELOCK_DST (no ACK/lease); 4096 not reached; watchdog 45 s SIGTERM 143 |
| Historical R3 | FAIL on `88e3f17` VALIDATE_TERMINAL_READY then `x-ready-timeout`; `8479997` unchanged |
| R5 corrected | hang **FALSIFIED** X PID **14598**; fixture 4096 exact PASS; harness **FAIL** publish=4095 fence=4094 (logcat-drop; serial 3539 still consume/ack). Script exit 2. Cell `runtime-37d8393/r5-ahb-cycles/`. |
| R5 counters recapture | X PID **24498**; 4096 exact PASS; publish=fence=completed=success=lease=4096; **ack=4095** (serial 766 still has lease, capture-drop). Cell `runtime-37d8393/r5-ahb-cycles-counters1/`. |
| R5 PASS | **PASS** (user 2026-09-15): hang FALSIFIED, 4096 exact ×2. Follow-logcat ack-drop not blocking. `runtime-37d8393/GATE-A-P2-R5-PASS-20260915.md`. |
| R6 bounded | **PASS** X PID **11495**; A+B exact `got0=00804000`; N_publish=2 counters match; no fatal. CLIENT_OK only. `runtime-37d8393/r6-cross-op/`. |
| R6 design | **COMPLETE** 2026-09-15. Events 29–32, D1 queued + D2 Present in-flight/OOM cells. `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-DESIGN-20260915.md`. |
| R6 source | **COMMITTED** wait-or-fatal **`95e6f96`** (includes `54ff35b` COMPLETED telemetry). Historical installed APK; superseded on device by `0f1e546`. |
| R6 CI | **PASS** run **34944171114** after KEEP FAIL **34943831800**. Artifact QUALIFIED. Historical `9369553` CI **34926730189** remains frozen. |
| R6 install | **DONE** experimental only. SHA/Build ID MATCH. `runtime-95e6f96/r0/`. Historical `runtime-9369553/r0/` frozen. |
| R6-D1 | **FAIL** X PID **24748**; schedule not constructed. Cell `runtime-9369553/r6-d1/` **kept**. |
| R6-D1 retry1 | **FAIL** X PID **22068**; Composite REQUEST then SUCCESS then second REQUEST **PROVEN**; pixels fail=1 `got0=00000001` (PolyFill vs oracle race). Cell `runtime-9369553/r6-d1-retry1/`. |
| R6-D1 retry2 | **OBSERVED** ART JIT SIGSEGV X PID **28170** during 8 s wait; PC `0x48000478` in `dalvik-jit-code-cache`; fixture ELF `63433803…70a8` **never ran**. Cell `runtime-9369553/r6-d1-retry2/`. |
| R6-D1 retry3 | **FAIL** X PID **2555**; pixels PASS `got0=00804000`; `CopyArea err=13` BadGC. Cell `runtime-9369553/r6-d1-retry3/`. |
| R6-D1 retry4 | **FAIL** X PID **7648**; CLIENT_OK; pixels PASS; SUCCESS before second REQUEST; missing Present CALLBACK xop=4. ELF `8a3b8509…a953`. Cell `runtime-9369553/r6-d1-retry4/`. |
| R6-D1 retry5 | **PASS** X PID **16168**; CLIENT_OK; pixels `got0=00804000`; Present CALLBACK xop=4 serial 9 after SUCCESS. ELF `e74776f3…1197`. Cell `runtime-9369553/r6-d1-retry5/`. |
| R6-D2-INFLIGHT | **FAIL** X PID **17596**; CLIENT_OK later pixels PASS; missing event 31 reason=1 (Present CALLBACK after Composite SUCCESS). Cell `runtime-9369553/r6-d2-inflight/`. |
| R6-D2-INFLIGHT retry1 | **FAIL** X PID **20856**; Present CALLBACK serial 6 then REJECT reason=1 **PROVEN**; PUBLISH serial 8 before COMPLETED serial 6 (COMPLETED of 6 **ABSENT**). ELF `ffce3910…b068`. Cell `runtime-9369553/r6-d2-inflight-retry1/`. |
| R6-D2 COMPLETED root cause | **PROVEN**: legacy `LORIE_GPU_OP_COPY` publishes `completedSerial` without event 14. Official Present CompleteNotify serial ≠ GPU serial S. Packet `p2-r6-design/GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md`. |
| R6-D2 COMPLETED fix | **COMMITTED** `54ff35b` then wait-or-fatal **`95e6f96`**. On-device COMPLETED serial 6 **PROVEN** (X 21317 seq 27). CI **34944171114** QUALIFIED. KEEP FAIL **34943831800**. ELF `2ca0957f…68a3`. |
| R6-D2-INFLIGHT `95e6f96` | **FAIL** X PID **21317**; Present-before-Composite **PROVEN**; COMPLETED serial 6 **PROVEN**; event 31 **ABSENT** (GPU terminal during Composite). Cell `runtime-95e6f96/r6-d2-inflight/` **kept**. |
| R6-D2-INFLIGHT `95e6f96` retry1-4 | **FAIL REPRODUCED** across 4 variants (X 24492/7952/13797/19332; pipelined, warm AHB, 8×8 to 1024×1024); event 31 **ABSENT** (GPU execution <0.5ms vs Xorg CPU dispatch 2.5ms). All 5 cells **kept**. |
| R6-D2-INFLIGHT root cause | **PROVEN**: Adreno 830 GPU finishes before Xorg single-threaded dispatch reaches `gateADirectTryPrepare()`. COMPLETED event 14 is 100% reliable. Direct composite admission under quiescent queue is correct and safe. Analysis: `p2-r6-design/GATE-A-P2-R6-D2-INFLIGHT-PHYSICAL-RACE-ANALYSIS-20260915.md`. |
| R6-D2-OOM | **NOT RUN** on `95e6f96`. |
| R6 retirement source | **COMMITTED** `0f1e546` on `src/f8-ahb-gatea-r6-retire`. Present ACK centralized in `present_gpu_copy_retire_or_fatal`. Patch Present hunks normalized. |
| R6 retirement CI | **PASS** run **34999213228** `workflow_dispatch` exact headSha `0f1e546`. Artifact QUALIFIED. |
| R6 retirement install | **DONE** experimental only. SHA/Build ID MATCH. `runtime-0f1e546/r0/`. |
| R6-D1 `0f1e546` | **PASS** first attempt X PID **29152**; CLIENT_OK; pixels 64 exact `got0=00804000`; Present CALLBACK xop=4 serial 9 after Composite SUCCESS. Cell `runtime-0f1e546/r6-d1/`. |
| R6-D2-INFLIGHT `0f1e546` | **PASS** first attempt X PID **31369**; **QUIESCENT-ADMIT**; cover T=S=7; later Composite + second lifecycle serial 9; event 31=0 event 32=0. Cell `runtime-0f1e546/r6-d2-inflight/`. |
| R6-D2-OOM `0f1e546` | **PASS** first attempt X PID **2638**; env armed **and** event 33 serial 7 executed; COMPLETED seq=56 then ACK event 34 seq=57; event 32=0; later SUCCESS serial 8. Cell `runtime-0f1e546/r6-d2-oom/`. |
| R6 | **PASS** design-complete three cells on `0f1e546`. Timeout/loss/scrap/destroy/CloseScreen-with-pending remain SOURCE-PROVEN not DEVICE-PROVEN. |
| R7 support artifact source | **COMMITTED** `a7528bd` on `src/f8-ahb-gatea-r7` (events 35/36). This is a **support artifact**, not an R7 qualification PASS. Frozen R6 tree untouched. Host verifiers PASS. **R7 qualification-01 BLOCKED** on installed `7549e36`. |
| Artifact B termux-x11 CI | **PASS** fork `debug_build.yml` run **35007764673** exact headSha `a7528bd`. Artifact QUALIFIED. SHA256 `c29b1c68…4c2c` Build ID `aa1d23e7…3b9c`. This is **not** a `waydefu/GPU` PR status check and **not** R7 qualification. |
| Artifact B historical install | **DONE then superseded.** Experimental-only `runtime-a7528bd/r0/`; SHA/Build ID MATCH at that time. **Not R7 qualification.** Current installed experimental is `feeaa56`. |
| B-2 R1 unset on `a7528bd` | **FAIL** X PID **17192**; oracle 1514/1514; stress 100/100 PASS; 1000 **ok=999 fail=1 alive=1**; event 35=0; SUMMARY `x-close-screen` counters 0. Cell `runtime-a7528bd/r1-unset-oracle/`. Do not silent-retry. **Authoritative historical FAIL.** **Not R7.** |
| B-2 diagnostic-01 on `a7528bd` | **DID NOT REPRODUCE** X PID **29184**; `ok=1000 fail=0`; no `B2_DIAG_FAIL`; EXA timeout **0**. Cell `runtime-a7528bd/r1-unset-diagnostic-01/`. Do **not** overwrite. Not a B-2 PASS. Not R7. |
| B-2 diagnostic-02 on `a7528bd` | **RCA IDENTIFIED** X PID **10903**; `ok=997 fail=3`; 3× timeout then `Gcomp Done`. Cell `runtime-a7528bd/r1-unset-diagnostic-02/`. Do **not** overwrite. Not a B-2 PASS. Not R7. |
| EXA Composite timeout repair | **COMMITTED+CI** `0d72332` CI **35049545631**; **superseded on device** by `27d8d1b`. B-2 R1 unset **FAIL** X PID **11212** serial **2370**; authorized rerun1 **FAIL REPRODUCED** X PID **8172** serial **1810** (`ok=90 fail=910 alive=0`); both fail-stop `x-exa-composite-wait` reason=4; **no timeout→Done**. Cells `runtime-0d72332/r1-unset-oracle/` and `r1-unset-oracle-rerun1/`. Historical `runtime-a7528bd/` frozen. Do **not** silent-retry. Do **not** start R7. |
| Stall-phase diagnostic | Historical **INSTALLED then superseded** `27d8d1b` CI **35056388284**. Cell `runtime-27d8d1b/r0/`. Observation **STALL_NOT_OBSERVED** X PID **16420**; stress 1000/1000 timeout=0; `STALL_PHASE` 3712; SWAP max 1.468 ms; NEXT_FENCE max 4.806 ms; CASE_A/B/C **NOT CLASSIFIED**. Packet `runtime-27d8d1b/GATE-A-P2-STALL-OBS-01-20260916.md`. **Not B-2.** Do **not** retry `stall-obs-01`. |
| Notify-phase diagnostic | Historical **STALL_NOT_OBSERVED** on `1f85b80` (X 28893; 1000/1000; `NOTIFY_*` NOT OBSERVED = coverage gap). Packet `runtime-1f85b80/GATE-A-P2-STALL-OBS-01-20260916.md`. Superseded on device by `feeaa56`. Do **not** retry. |
| Notify function-coverage diagnostic | Historical **INSTALLED then superseded** `feeaa56` CI **35076884763**. Observation **CASE_LOOP** X PID **23034**; timeout serial **86**; timeout→Done=0. Packet `runtime-feeaa56/GATE-A-P2-STALL-OBS-01-20260916.md`. **Not B-2.** Do **not** retry `runtime-feeaa56/stall-obs-01`. |
| CASE_LOOP source fix | **COMMITTED+CI+INSTALLED** hardened **`7549e36`** CI **35084701124** QUALIFIED on `src/f8-ahb-gatea-case-loop` (parent `0d72332`). Initial `327b028` **SUPERSEDED**. APK `1.03.01-7549e36-16.09.26` SHA256 `45500894…4bc3` Build ID `4c5b7b86…8f81`. 8 ms CLOCK_MONOTONIC idle recheck ≠ 2000 ms EXA fail-stop. |
| CASE_LOOP repair-validation | **CASE_LOOP_REPAIR_VALIDATED** X PID **19887**; `p_b2_stress 1000` ok=1000 fail=0 alive=1 RC=0; Gcomp 1000/1000/1000; RECT→Done max 22 ms; timeout=0; fatal=0; timeout→Done=0; pixels exact; Stable PID **14604** UNTOUCHED. Cell `runtime-7549e36/repair-validation-01/`. Packet `runtime-7549e36/GATE-A-P2-CASE-LOOP-REPAIR-VALIDATION-20260916.md`. **Not B-2.** Do **not** retry. |
| B-2 requalification-01 on `7549e36` | **B2_REQUALIFICATION_INVALID** (no live ADB TLS; stages NOT RUN). Cell `runtime-7549e36/b2-requalification-01/` **frozen**. Packet `runtime-7549e36/GATE-A-P2-B2-REQUALIFICATION-01-20260916.md`. Do **not** overwrite. |
| B-2 requalification-02 on `7549e36` | **B2_REQUALIFICATION_PASS** X PID **32228**; Activity **10703**; `NO_GATEA_ENV`; provenance MATCH; oracle 1514/1514 fail=0 maxΔ=0 ±1=0 Xnz=0; stress100 `ok=100 fail=0 alive=1`; mixed100 `mixed=1 ok=100 fail=0 alive=1`; stress1000 `ok=1000 fail=0 n=1000 alive=1`; Gcomp 2715/2715/2715; RECT→Done max 0.111 s ≥2000=0; timeout=0; fatal=0; timeout→Done=0; pixels exact; Stable PID **16485** UNTOUCHED; `NO_X3_RESIDUE`. Cell `runtime-7549e36/b2-requalification-02/`. Packet `runtime-7549e36/GATE-A-P2-B2-REQUALIFICATION-02-20260916.md`. **Not R7.** Do **not** overwrite. |
| R7 qualification-01 on `7549e36` | **R7_QUALIFICATION_BLOCKED**. Cell `r7-04` `fbo-incomplete` X PID **31122**; env exact PROTO=1 TELEMETRY=1 TEST_FAULT=fbo-incomplete TEST_ARM=1; event 35 once seq=31 serial=5 src=4 dst=2 after LOOKUP_OK; renderer halt `r-gatea-DIRECT_LOOKUP_FAIL` reason=2; last halt `x-direct-not-success` reason=4; judge `halt_mismatch`; Gcomp Done=0; event 32=0; timeout→Done=0; no signal; Stable **16485** UNCHANGED; `NO_X3_RESIDUE`. Remaining mandatory cells **NOT RUN** (fail-fast). Packet `runtime-7549e36/GATE-A-P2-R7-QUALIFICATION-01-20260916.md`. Do **not** retry this cell. Do **not** overwrite `r7-qualification-01`. Frozen judge still FAILs this evidence. |
| R7 fatal-propagation repair | **COMMITTED+CI+INSTALLED** `fdfb1ce` parent `7549e36` CI **35103216566**. APK `1.03.01-fdfb1ce-16.09.26` SHA256 `5313fc9a…915c` Build ID `1d6bf3cd…998e` signer continuity PASS. Packets `p2-r7-design/GATE-A-P2-R7-FATAL-PROPAGATION-REPAIR-20260916.md` and `p2-r7-fatal-propagation-ci-35103216566/`. |
| R7-04 requalification-01 on `fdfb1ce` | **R7_04_REQUALIFICATION_PASS** X PID **9891**; Activity **23139** TID 8877; env EXACT_R7_04_ENV; event 35 once seq=45 serial=9 src=4 dst=2 after LOOKUP_OK; last halt `r-gatea-DIRECT_LOOKUP_FAIL` reason=2; `x-direct-not-success reason=4`=0; preserve dump `x-observe-fatal`; judge `R7_PASS fbo-incomplete`; Gcomp Done=0; event 32=0; timeout→Done=0; Stable **24999** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-fdfb1ce/r7-04-requalification-01/`. Packet `runtime-fdfb1ce/GATE-A-P2-R7-04-REQUALIFICATION-01-20260917.md`. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-05 qualification on `fdfb1ce` | **R7_05_QUALIFICATION_FAIL** X PID **22704**; Activity **30140**; env EXACT_R7_05_ENV; fixture `p_r3_single_direct` ×1; PUBLISH serial=5 → DRAW → event 35 once seq=32 src=5 dst=2; first halt `x-direct-not-success reason=2`; last halt `r-hup reason=6`; judge `R7_FAIL halt_mismatch what=r-hup reason=6`; reason=4=0; forbidden-success zeros; no crash signal; Stable **843** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-fdfb1ce/r7-05/`. Packet `runtime-fdfb1ce/GATE-A-P2-R7-05-QUALIFICATION-20260917.md`. VALID FAIL. Do **not** retry. Do **not** overwrite. |
| R7-05 HUP duplicate-fatal repair | **COMMITTED+CI+INSTALLED** `a07d66c` parent `fdfb1ce` CI **35171333149**. APK `1.03.01-a07d66c-17.09.26` SHA256 `a25861b4…ace5` Build ID `ad3509c0…43f2` signer continuity PASS. Packets `p2-r7-design/GATE-A-P2-R7-HUP-PRESERVE-REPAIR-20260917.md` and `p2-r7-hup-preserve-ci-35171333149/`. |
| R7-05 requalification-01 on `a07d66c` | **R7_05_A07D66C_REQUALIFICATION_PASS** X PID **8418**; Activity **27372** TID 8356; env EXACT_R7_05_ENV; fixture `p_r3_single_direct` ×1; PUBLISH serial=5 → DRAW → event 35 once seq=32 src=5 dst=2; last halt `x-direct-not-success reason=2`; `GATEA_HUP_PRESERVE published=2`; `r-hup/6` HALT=0; judge `R7_PASS post-draw-gl`; Gcomp Done=0; event 32=0; timeout→Done=0; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-05-requalification-01/`. Packet `runtime-a07d66c/GATE-A-P2-R7-05-A07D66C-REQUALIFICATION-01-20260917.md`. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-01 on `a07d66c` | **R7_01_A07D66C_QUALIFICATION_PASS** X PID **15029**; Activity **31259** TID **14945**; env EXACT_R7_01; fixture `p_r3_single_direct` ×1; PUBLISH seq=28 serial=5 → CONSUME_DIRECT seq=29 → event35 once seq=30 src=1 dst=2 role=2 → LOOKUP_FAIL seq=31; last halt `r-gatea-DIRECT_LOOKUP_FAIL reason=2`; HUP_PRESERVE=0; r-hup/x-hup/x-direct-not-success HALT=0; judge `R7_PASS src-ready-miss`; Gcomp Done=0; event 32=0; timeout→Done=0; DRAW after miss=0; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-01/`. Packet `runtime-a07d66c/GATE-A-P2-R7-01-A07D66C-20260917.md`. Historical BLOCKED packet stays frozen. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-02 on `a07d66c` | **R7_02_A07D66C_QUALIFICATION_PASS** X PID **28625**; Activity **18285** TID **28550**; env EXACT_R7_02 `TEST_FAULT=dst-ready-miss`; fixture `p_r3_single_direct` ×1; PUBLISH seq=28 serial=5 → CONSUME_DIRECT seq=29 → event35 once seq=30 **src=2 dst=2** role=2 → LOOKUP_FAIL seq=31; last halt `r-gatea-DIRECT_LOOKUP_FAIL reason=2`; not src-enum=1; HUP_PRESERVE=0; judge `R7_PASS dst-ready-miss`; Gcomp Done=0; DRAW after miss=0; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-02/`. Packet `runtime-a07d66c/GATE-A-P2-R7-02-A07D66C-20260917.md`. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-03 on `a07d66c` | **R7_03_A07D66C_QUALIFICATION_PASS** X PID **28326**; Activity **28714** TID **28226**; env EXACT_R7_03 `TEST_FAULT=tuple-mismatch`; fixture `p_r3_single_direct` ×1; PUBLISH seq=28 serial=5 src=6 dst=7 → CONSUME_DIRECT seq=29 → event35 once seq=30 **src=3 dst=2** role=2 → GENERATION_FATAL seq=31; last halt `r-gatea-direct-identity reason=5` PROTOCOL; reason6=0; LOOKUP_FAIL=0; pre-fault `TUPLE_MATCH result=1` on buffers 6 and 7; judge `R7_PASS tuple-mismatch`; Gcomp Done=0; DRAW after=0; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-03/`. Packet `runtime-a07d66c/GATE-A-P2-R7-03-A07D66C-20260917.md`. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-06 on `a07d66c` | **R7_06_A07D66C_QUALIFICATION_PASS** X PID **21795**; Activity **11758** TID **21709**; env EXACT_R7_06 `TEST_FAULT=fence-create-fail`; fixture `p_r3_single_direct` ×1; PUBLISH seq=28 serial=5 → LOOKUP_OK seq=30 → DRAW seq=31 event=10 → event35 once seq=32 **src=6 dst=2** → FENCE_ERROR seq=33; last halt `r-gatea-fence-create reason=3`; fence-wait=0; COMPLETED serial 5=0; FENCE_SATISFIED=0; judge `R7_PASS fence-create-fail`; Gcomp Done=0; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-06/`. Packet `runtime-a07d66c/GATE-A-P2-R7-06-A07D66C-20260917.md`. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-07 on `a07d66c` | **R7_07_A07D66C_QUALIFICATION_PASS** X PID **31938**; Activity **24621** TID **31858**; env EXACT_R7_07 `TEST_FAULT=fence-timeout`; fixture `p_r3_single_direct` ×1; PUBLISH seq=28 serial=5 → LOOKUP_OK seq=30 → DRAW seq=31 event=10 → event35 once seq=32 **src=7 dst=2** → FENCE_TIMEOUT seq=33; last halt `r-gatea-fence-wait reason=3`; fence-create HALT=0; FENCE_ERROR=0; FENCE_SATISFIED=0; COMPLETED serial 5=0; reason4=0; judge `R7_PASS fence-timeout`; Gcomp Done=0; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-07/`. Packet `runtime-a07d66c/GATE-A-P2-R7-07-A07D66C-20260917.md`. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-08 on `a07d66c` | **R7_08_A07D66C_QUALIFICATION_PASS** X PID **14424**; Activity **7683** TID **14366**; env EXACT_R7_08 `TEST_FAULT=renderer-fatal-pre-fence`; fixture `p_r3_single_direct` ×1; PUBLISH seq=28 serial=5 → CONSUME_DIRECT seq=29 → event35 once seq=30 **src=8 dst=2** → GENERATION_FATAL seq=31; DRAW absent (not required); last halt `r-test-fatal-pre-fence reason=6`; fence-create/fence-wait HALT=0; FENCE_SATISFIED=0 FENCE_TIMEOUT=0 FENCE_ERROR=0; COMPLETED serial 5=0; reason4=0; judge `R7_PASS renderer-fatal-pre-fence`; Gcomp Done=0; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-08/`. Packet `runtime-a07d66c/GATE-A-P2-R7-08-A07D66C-20260917.md`. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-09 on `a07d66c` | **R7_09_A07D66C_QUALIFICATION_PASS** X PID **22076**; Activity **31018**; env EXACT_R7_09 `TEST_FAULT=wrong-generation-frame`; dedicated runner `run-r7-09-a07d66c.sh`; classifier `EXPECTED_EARLY_FAIL` (died elapsed=2, not DIED_DURING_8S INVALID); first REGISTER_READY seq=20 then event35 once seq=21 **src=9 dst=1** role=1 serial=0 generation=1; last halt `x-wrong-generation reason=6`; PUBLISH/CONSUME/DRAW=0; HUP_PRESERVE diagnostic only; judge `R7_PASS wrong-generation-frame`; Gcomp Done=0; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-09/`. Packet `runtime-a07d66c/GATE-A-P2-R7-09-A07D66C-20260917.md`. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-11 on `a07d66c` | **R7_11_A07D66C_QUALIFICATION_PASS** X PID **31764**; Activity **10191**; env EXACT_R7_11 `TEST_FAULT=serial-wrap`; dedicated runner `run-r7-11-a07d66c.sh`; classifier `EXPECTED_WRAP`; event35 once seq=28 **src=11 dst=1** role=1 serial_arg=0 generation=1; last halt `x-serial-wrap reason=6`; PUBLISH event6=0; PUBLISH serial=0=0; seed UINT64_MAX SOURCE-PROVEN / not device-observed; HUP_PRESERVE diagnostic only; judge `R7_PASS serial-wrap`; Gcomp Done=0; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-11/`. Packet `runtime-a07d66c/GATE-A-P2-R7-11-A07D66C-20260917.md`. Historical ADB BLOCKED packet stays frozen. **Not full R7 PASS.** Do **not** retry this cell. |
| R7-10 on `a07d66c` | **R7_10_A07D66C_QUALIFICATION_FAIL** X PID **12568**; Activity **28497** TID **12463**; env EXACT_R7_10 `TEST_FAULT=renderer-exit-after-consume`; generic runner; PUBLISH seq=28 serial=5 → CONSUME_DIRECT seq=29 → event35 once seq=30 **src=10 dst=2** role=2; renderer SUMMARY `r-exit-after-consume` no own HALT; last halt `x-direct-not-success reason=4`; `x-hup/6`=0; judge `R7_FAIL halt_mismatch`; waitpid 127 NOT OBSERVED; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a07d66c/r7-10/`. Packet `runtime-a07d66c/GATE-A-P2-R7-10-A07D66C-20260917.md`. VALID FAIL. RCA **PROVEN** (`GATE-A-P2-R7-10-RCA-REPAIR-20260917.md`). Repair **INSTALLED** as `8545b26`. Dedicated 8545b26 R7-10 runner **QUALIFIED**. Do **not** retry. Do **not** overwrite. |
| a07d66c reusable one-cell R7 runner | **R7_A07D66C_RUNNER_QUALIFIED** (tooling only; no device cell). Path `p2-r3-xpump-runtime/run-r7-one-cell-a07d66c.sh` SHA256 `36d66f17…8ded` size 20529. Binds `1.03.01-a07d66c-17.09.26` / versionCode 15 / `runtime-a07d66c`. R7-01 `src-ready-miss`/`direct` ENABLED. R7-04/R7-05 REFUSE. r7-09 and r7-11 remain **REVIEW_REQUIRED** / live REFUSE. WAIT_S=12. Frozen judge SHA `fba3c10f…cc17` 16/16. VALIDATE_ONLY host tests 18/18. Packet `p2-r3-xpump-runtime/r7-a07d66c-runner-qualification-20260917/`. Historical runners unmodified. Do **not** modify this runner. |
| a07d66c R7-09 dedicated early-fault runner | **R7_09_A07D66C_RUNNER_QUALIFIED**. Path `p2-r3-xpump-runtime/run-r7-09-a07d66c.sh` SHA256 `d6ec76c1…f60d` size 22582. Device cell **PASS**. Packet `p2-r3-xpump-runtime/r7-09-a07d66c-runner-qualification-20260917/`. |
| a07d66c R7-11 dedicated serial-wrap runner | **R7_11_A07D66C_RUNNER_QUALIFIED**. Path `p2-r3-xpump-runtime/run-r7-11-a07d66c.sh` SHA256 `74385947…c453` size 25716. Device cell **PASS**. Packet `p2-r3-xpump-runtime/r7-11-a07d66c-runner-qualification-20260917/`. Historical ADB BLOCKED preflight remains `runtime-a07d66c/r7-11-preflight/`. |
| 8545b26 R7-10 dedicated HUP-containment runner | **R7_10_8545B26_RUNNER_QUALIFIED**. Path `p2-r3-xpump-runtime/run-r7-10-8545b26.sh` SHA256 `690a865d…54cd` size 22480. Device cell **PASS**. Packet `p2-r3-xpump-runtime/r7-10-8545b26-runner-qualification-20260917/`. Do **not** use the generic a07d66c runner for 8545b26. |
| 8545b26 R7-10 device requal | **R7_10_8545B26_REQUALIFICATION_PASS** X PID **13115** TID **13536**; Activity **6495** renderer TID **12901**; env EXACT `TEST_FAULT=renderer-exit-after-consume`; dedicated runner; PUBLISH seq=28 serial=5 src=6 dst=7 → CONSUME_DIRECT seq=29 → event35 once seq=30 **src=10 dst=2** role=2; renderer SUMMARY `r-exit-after-consume` generationFatal=0 no own HALT; last halt `x-hup reason=6`; `x-direct-not-success/4`=0; classifier `EXPECTED_HUP`; judge `R7_PASS renderer-exit-after-consume`; waitpid 127 NOT AVAILABLE; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-8545b26/r7-10/`. Packet `runtime-8545b26/GATE-A-P2-R7-10-8545B26-20260917.md`. Historical BLOCKED preflight remains `runtime-8545b26/r7-10-preflight/`. **Not full R7 PASS.** Progress **11/13**. Do **not** retry this cell. Do **not** retry `runtime-a07d66c/r7-10`. |
| 8545b26 R7-P1 dedicated present-hold runner | **R7_P1_8545B26_RUNNER_QUALIFIED**. Path `p2-r3-xpump-runtime/run-r7-p1-8545b26.sh` SHA256 `46c2289d…16ba7` size 24458. Classifier `classify_r7_p1_present_hold.py` SHA256 `07de408b…3908`. Present fixture ELF `p_r6_d2_present` SHA256 `fec8f46d…ba86` size 72536. Host tests 30/30. Judge 16/16. Wait-wake host PASS. Packet `p2-r3-xpump-runtime/r7-p1-8545b26-runner-qualification-20260917/` remains historical tooling QUALIFIED. Generic a07d66c r7-p1 remains **REVIEW_REQUIRED**. Do **not** use the generic runner for 8545b26. Do **not** modify this runner. |
| 8545b26 R7-P1 device | **R7_P1_8545B26_QUALIFICATION_INVALID** X PID **14331**; Activity **30332** renderer TID **14251**; env EXACT `TEST_FAULT=present-hold-complete`; dedicated runner invoke once rc=**9**; holder ×1 pid 14819; fixture ×1 pid 14839 SHA `fec8f46d…ba86` CLIENT_OK; event35 once seq=2 **src=12 dst=2** serial=1 on CopyArea CALLBACK src=1; Present CALLBACK src=4 serial=7 seq=54 **after** consume; event36 serial=7 waited=0; last halt **NONE**; `x-present-copy-wait/4`=0; `x-hup/6`=0; classifier `NO_PRESENT_CALLBACK`; frozen judge **not invoked**; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-8545b26/r7-p1/`. Packet `runtime-8545b26/GATE-A-P2-R7-P1-8545B26-20260917.md`. Preflight remains `runtime-8545b26/r7-p1-preflight/`. INVALID construction (fault12 one-shot consumed on bring-up CopyArea). Progress **still 11/13**. Do **not** retry this cell. Do **not** start R7-P2. |
| abb27a65 Present-target-arm artifact | **R7_P1_VALIDITY_ARTIFACT_QUALIFIED** CI **35253641841** headSha `abb27a65`. APK SHA256 `b7baa1df…9d99` size 15300558 signer continuity PASS Build ID `7362d978…f452`. Packet `p2-r7-p1-arm-ci-35253641841/P2-R7-P1-ARM-CI-ARTIFACT-PROVENANCE-20260918.md`. |
| abb27a65 R7-P1 dedicated runner | **R7_P1_ABB27A65_RUNNER_QUALIFIED**. Path `p2-r3-xpump-runtime/run-r7-p1-abb27a65.sh` SHA256 `95900a2d…7098` size 24482. Classifier `classify_r7_p1_abb27a65.py` SHA256 `e741867f…efe7`. Host tests 30/30. Packet `p2-r3-xpump-runtime/r7-p1-abb27a65-runner-qualification-20260918/`. Historical 8545b26 P1 runner unmodified. |
| abb27a65 R7-P2 dedicated runner | **R7_P2_ABB27A65_RUNNER_QUALIFIED** (tooling only; device **NOT RUN**). Path `p2-r3-xpump-runtime/run-r7-p2-abb27a65.sh` SHA256 `d36a4ccca7…d8cc` size 24501. Host tests 27/27. Packet `p2-r3-xpump-runtime/r7-p2-abb27a65-runner-qualification-20260918/`. |
| abb27a65 R7-P1 device | **R7_P1_ABB27A65_QUALIFICATION_INVALID** X PID **19686**; Activity **19659** ADB-ALIVE at pre-cleanup; env EXACT `TEST_FAULT=present-hold-complete`; dedicated runner invoke once rc=**9**; Present CALLBACK seq=54 src=4 serial=7 then event35 seq=56 enum=12 once; early CopyArea did not consume enum12; host `/proc` liveness `renderer_alive_during=0`; classifier `PEER_DIED`; last halt **NONE**; fixture CLIENT_OK; frozen judge **not invoked**; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-abb27a65/r7-p1/`. Packet `runtime-abb27a65/GATE-A-P2-R7-P1-ABB27A65-20260918.md`. Progress **still 11/13**. Do **not** retry this cell. Do **not** start R7-P2. |
| a4c8177 Present-hold artifact | **R7_P1_HOLD_ARTIFACT_QUALIFIED** CI **35295094951** headSha `a4c8177`. APK SHA256 `91a4b74e…a55c` size 15317074 signer continuity PASS Build ID `dcd82974…ba60`. Packet `p2-r7-p1-hold-ci-35295094951/P2-R7-P1-HOLD-CI-ARTIFACT-PROVENANCE-20260918.md`. |
| a4c8177 R7-P1 dedicated runner | **R7_P1_A4C8177_RUNNER_QUALIFIED**. Path `p2-r3-xpump-runtime/run-r7-p1-a4c8177.sh` SHA256 `4cbb1394…1b47`. Classifier `classify_r7_p1_a4c8177.py` SHA256 `232892b2…27c4`. Host tests 38/38. Packet `p2-r3-xpump-runtime/r7-p1-a4c8177-runner-qualification-20260918/`. Historical abb27a65 P1 runner unmodified. |
| a4c8177 R7-P2 dedicated runner | **R7_P2_A4C8177_RUNNER_QUALIFIED** (tooling only; device **NOT RUN**). Path `p2-r3-xpump-runtime/run-r7-p2-a4c8177.sh` SHA256 `6b0a9bdb…d55e`. Host tests 31/31. Packet `p2-r3-xpump-runtime/r7-p2-a4c8177-runner-qualification-20260918/`. |
| a4c8177 R7-P1 device | **R7_P1_A4C8177_QUALIFICATION_INVALID** X PID **24284**; Activity **14349**; env EXACT `TEST_FAULT=present-hold-complete`; dedicated runner invoke once rc=**9**; Present CALLBACK seq=54 src=4 serial=7 then event35 seq=56 enum=12 side=2 once; later event14 serial=8; event36 seq=65 serial=7 **src=1 waited=1**; halt `x-present-copy-wait/4` at 09:39:40.200 (~2003 ms); fixture CompleteNotify FAIL; during-wait ADB Activity ALIVE (`activity_alive_during_wait=1`); pre-cleanup Activity ABSENT; classifier `PEER_DIED`; frozen judge **not invoked**; Stable **20146** UNCHANGED; `NO_X3_RESIDUE`. Cell `runtime-a4c8177/r7-p1/`. Packet `runtime-a4c8177/GATE-A-P2-R7-P1-A4C8177-20260918.md`. Observed hold path is **not** a PASS. **FROZEN**. Do **not** retry this cell. |
| a4c8177 liveness-v2 P1/P2 runners | **R7_P1_A4C8177_V2_RUNNER_QUALIFIED** `run-r7-p1-a4c8177-v2.sh` SHA256 `63e3d8a2…d20c`. **R7_P2_A4C8177_V2_RUNNER_QUALIFIED** `run-r7-p2-a4c8177-v2.sh` SHA256 `3fca2553…d622`. Classifiers target-serial-scoped SHA `d287d361…bd14` / `3c6bb8a2…d43c`. Historical v1 runners unmodified (`4cbb1394…1b47` / `6b0a9bdb…d55e`). |
| a4c8177 R7-P1 validity-02 | **R7_P1_A4C8177_QUALIFICATION_PASS** X PID **1892**; Activity **19391**; CALLBACK30 src=4 serial=7 seq=54; event35 enum=12 side=2 seq=56; during-wait ADB ALIVE; event36 waited=1; elapsed 2007 ms; terminal `x-present-copy-wait/4`; post-terminal Activity ABSENT observational; classifier `EXPECTED_PRESENT_TIMEOUT`; judge `R7_PASS present-hold-complete`. Cell `runtime-a4c8177/r7-p1-validity-02/`. Do **not** retry. |
| a4c8177 R7-P2 device | **R7_P2_A4C8177_QUALIFICATION_PASS** X PID **12663**; Activity **27910**; CALLBACK30 src=4 serial=7 seq=54; event35 enum=13 side=2 seq=56; pre-fault ALIVE; post-fault ABSENT expected; terminal `x-hup/6`; classifier `EXPECTED_PRESENT_RENDERER_EXIT`; judge `R7_PASS present-renderer-exit`. Cell `runtime-a4c8177/r7-p2/`. Waitpid `_exit(127)` not available (not fabricated). Do **not** retry. |
| 8545b26 R7-P1 validity support | **R7_P1_VALIDITY_RCA_PROVEN** + **R7_P1_VALIDITY_SUPPORT_COMMITTED** as `abb27a65`. Dual RCA **P1_LIVENESS_PROBE_RCA_PROVEN** + **P1_COMPLETION_RCA_PROVEN_HIGH_WATERMARK**. Hold support **COMMITTED** as `a4c8177`. Worktree `src/f8-ahb-gatea-r7-p1-arm` HEAD `a4c8177` clean. Do **not** retry `runtime-8545b26/r7-p1`, `runtime-abb27a65/r7-p1`, `runtime-a4c8177/r7-p1`, `runtime-a4c8177/r7-p1-validity-02`, or `runtime-a4c8177/r7-p2`. |
| Next | Device **`5a782f6` INSTALLED**. C1 attempt-05 **R8_INVALID POST_END_OBSERVATION** frozen. Do **not** retry attempts 01–05. Do **not** create attempt-06. Do **not** start C2 or R9. Production Gate A remains BLOCKED. |
| R8 design acceptance | **R8_DESIGN_ACCEPTED_ON_A4C8177** / DESIGN_FROZEN for this generation. Packet `p2-r8-design/GATE-A-P2-R8-DESIGN-ACCEPTANCE-20260918.md`. Historical PR #8 docs remain PROPOSED as written. A11 CloseScreen **SPLIT** (no live client registry at CloseScreen). |
| R8 API/protocol amendment | **R8_TEST_API_PROTOCOL_AMENDMENT_ACCEPTED**. Packet `p2-r8-design/GATE-A-P2-R8-TEST-API-PROTOCOL-AMENDMENT-20260918.md`. Host **R8_API_PROTOCOL_AMENDMENT_HOST_QUALIFIED** (`p2-r8-design/GATE-A-P2-R8-API-PROTOCOL-AMENDMENT-HOST-QUALIFIED-20260918.md`). Shared header process-neutral; X-only `lorie_r8_test_x.h`; protocol v1 QV=32 Register=72 Checkpoint=72. |
| R8 host support | **R8_SUPPORT_HOST_VERIFIED** plus amendment host QUALIFIED. Packet `p2-r8-design/GATE-A-P2-R8-SUPPORT-HOST-VERIFIED-20260918.md`. judge_vectors=53 (host); device_cells=10 (not run). |
| R8 CI | Historical **R8_CI_FAIL** run **35304122983** headSha `bc25170` frozen (`InitOutput.c` undeclared dtor). Packet `p2-r8-design/GATE-A-P2-R8-CI-FAIL-20260918.md`. Repair **`d382c0a`**. Historical **R8_CI_FAIL** run **35305368742** headSha `d382c0a` (`lorie_r8_test.c` PixmapPtr/XMD). Packet `p2-r8-design/GATE-A-P2-R8-CI-FAIL-D382C0A-20260918.md`. Historical **R8_CI_PASS** run **35311343984** headSha `65938a4`. Packet `p2-r8-design/GATE-A-P2-R8-CI-PASS-65938A4-20260918.md`. Fresh **R8_CI_PASS** run **35321447455** headSha `5a782f6`. Packet `p2-r8-design/GATE-A-P2-R8-CI-PASS-5A782F6-20260918.md`. Do **not** rerun any of the four. |
| R8 artifact | Historical **R8_ARTIFACT_QUALIFIED** APK `1.03.01-65938a4-18.09.26` SHA256 `b88f12ec…1a6c` Build ID `21770f73…cfa7` (superseded on device). Current **R8_OBS_TERMINAL_ARTIFACT_QUALIFIED** APK `1.03.01-5a782f6-18.09.26` SHA256 `43590412…a78e` Build ID `d032a818…b02a` signer `b6da0148…e5e1` **INSTALLED**. Packet `p2-r8-design/GATE-A-P2-R8-OBS-TERMINAL-ARTIFACT-QUALIFIED-20260918.md`. |
| R8 runtime tooling | **R8_RUNTIME_TOOLING_QUALIFIED** VALIDATE_ONLY. Packet `p2-r8-design/GATE-A-P2-R8-RUNTIME-TOOLING-QUALIFIED-20260918.md`. Runner `p2-r8-runtime/run-r8-one-cell-65938a4.sh`. |
| R8 install | **R8_INSTALL_BIND_PASS**. SERIAL `10.191.48.13:37861` live mDNS. Experimental `1.03.01-65938a4-18.09.26` SHA256 `b88f12ec…1a6c` Build ID `21770f73…cfa7`. Stable PID **20146** UNCHANGED. Packet `p2-r8-design/GATE-A-P2-R8-INSTALL-BIND-PASS-20260918.md`. Historical `R8_INSTALL_BIND_BLOCKED` remains frozen. |
| R8 orchestration v2 | **R8_RUNTIME_ORCHESTRATION_V2_QUALIFIED**. Runner SHA256 `ea05aaa5…5db5`. Helper `r8_orchestration_v2.py` `21f97d9f…94cc`. Host tests 14/14. Judge 53/53 unchanged. Packet `p2-r8-design/GATE-A-P2-R8-RUNTIME-ORCHESTRATION-V2-QUALIFIED-20260918.md`. RCA `p2-r8-design/GATE-A-P2-R8-CLEAN-CELL-ORCHESTRATION-RCA-20260918.md`. |
| R8-C1 device | Historical **R8_INVALID** `MISSING_END_x` X PID **14713**; Cell `runtime-65938a4/r8-c1/attempt-01/`. **FROZEN**. |
| R8-C1 attempt-02 | **R8_BLOCKED SCREEN_NOT_AWAKE**. Cell `runtime-65938a4/r8-c1/attempt-02-orchestration-v2/`. **FROZEN**. |
| R8-C1 attempt-03 | **R8_BLOCKED TOOLING_EMIT_JSON** X 18823; fixture never run. Cell `runtime-65938a4/r8-c1/attempt-03-orchestration-v2/`. **FROZEN**. |
| R8-C1 attempt-04 | **R8_INVALID END_COUNT_MISMATCH_x** X PID **21246**; CLIENT_OK; TERM owned PID; X_CLOSE_ENTER/RESULT; both ENDs present; X recs 52 vs actual_count 42 (destructors after ObsEnd); renderer recs after END. Cell `runtime-65938a4/r8-c1/attempt-04-orchestration-v2/`. Packet `p2-r8-design/GATE-A-P2-R8-C1-ATTEMPT-04-INVALID-20260918.md`. **FROZEN**. C2–P2 **NOT RUN**. |
| R8 OBS terminal repair | **R8_OBS_TERMINAL_RCA_PROVEN** + **R8_OBS_TERMINAL_REPAIR_HOST_QUALIFIED** + commit **`5a782f6`** parent `65938a4` + CI **35321447455** PASS + **R8_OBS_TERMINAL_ARTIFACT_QUALIFIED**. Host 53/53 + obs-terminal C/Python PASS. X END after saved CloseScreen return; renderer END after unbind+surface+loop drain; `R8_OBS_POST_END` detector. Packet `p2-r8-design/GATE-A-P2-R8-OBS-TERMINAL-REPAIR-HOST-QUALIFIED-20260918.md`. |
| R8 5a782f6 install | **R8_INSTALL_BIND_PASS**. SERIAL `10.191.48.13:38361`. Experimental `1.03.01-5a782f6-18.09.26` SHA256 `43590412…a78e` Build ID `d032a818…b02a`. Stable PID **20146** UNCHANGED. Cell `runtime-5a782f6/r0/`. Packet `p2-r8-design/GATE-A-P2-R8-INSTALL-BIND-PASS-5A782F6-20260918.md`. Historical ADB-empty `R8_INSTALL_BIND_BLOCKED` packet remains frozen. |
| R8 runtime tooling 5a782f6 | **R8_RUNTIME_TOOLING_5A782F6_BOUND**. Manifest `runtime-5a782f6/r8-runtime-tooling-manifest.json`. Runner `p2-r8-runtime/run-r8-one-cell-5a782f6.sh` SHA256 `992ea257…8216` (v2 not overwritten; live v2 SHA `6c5bfbd0…246d`; original v2 `ea05aaa5…5db5` preserved). Judge/spec/collector/fixture hashes unchanged. VALIDATE_ONLY created no device evidence. |
| R8-C1 attempt-05 | **R8_INVALID POST_END_OBSERVATION** X PID **14186**; CLIENT_OK; SIGTERM owned PID; X END=1 renderer END=1; X `R8_OBS_POST_END`=8 after saved CloseScreen return; judge not invoked. Cell `runtime-5a782f6/r8-c1/attempt-05-obs-terminal/`. Packet `p2-r8-design/GATE-A-P2-R8-C1-ATTEMPT-05-INVALID-20260918.md`. **FROZEN**. Do **not** retry. Do **not** create attempt-06. C2–P2 **NOT RUN**. |
| Renderer blocking audit | Historical `27d8d1b` read-only packet remains; SWAP/NEXT_FENCE as 2 s blocker **FALSIFIED** on `feeaa56` stall-obs-01. Remaining was infinite `cond_wait` + lost wakeup / no Choreographer during `lorieGpuCopyWait`. |
| waydefu/GPU docs PRs | `#1` **MERGED** (`0c353dd`, R6 PASS). `#3` **MERGED** (`2ab76b30`, historical stall-obs). `#2` **MERGED** (historical EXA timeout snapshot). `#4` **closed without merge** (stale CASE_LOOP snapshot). `#5` **MERGED** (`6c83338`, B-2 PASS `7549e36`). `#6` **MERGED** (`c95b893`, `fdfb1ce` R7-04 PASS continuation kit; not qualification). `#7` **MERGED** (V1-Core plan; not qualification). `#8` **MERGED** ([PR](https://github.com/waydefu/GPU/pull/8), R8 design/plan). `#9` **OPEN** ([PR](https://github.com/waydefu/GPU/pull/9), `5a782f6` INSTALLED + R8-C1 attempt-05 INVALID; not qualification). This repo still has **no GitHub status checks**. Map: `p2-r7-design/WAYDEFU-GPU-PR-MAP-20260916.md`. Docs merge is **not** qualification. |

## Runtime (S3 qualification snapshot; B3a current state is recorded below)

| | Stable daily driver | Experimental |
|---|---|---|
| Package | `com.termux.x11` `1.03.01-11b82d9-06.09.26` | `com.waydefu.x11gpu` `1.03.01-9b6420d-09.09.26` |
| Display | `:1` PID **26474** ppid=4718 `-legacy-drawing` | `:3` E1b qualified on displayId=0; latest PID **15885**, cleanly stopped |
| Session | XFCE on `:1` — do not touch | X3 teardown complete after qualification |
| SHA256 | control `aad3d433…ea98e9` | `cd61a50e8c0bce90550e23dcd9bdd001c23d68e14145682346a7f89afb297988` |

- Fork: `waydefu/termux-x11` branch `f8-p2-b2-over` HEAD **`98224356e40913dcf2188d18748eba9401639850`**
- Tree: `/root/projects/GPU加速/src/f8-ahb`
- Activity: waydefu MainActivity Display0
- Qualification ADB: `10.56.180.219:42761`, fresh `device`, F8 identity verified; pre-fix round stopped with no retry after launch crash, then E1b `9b6420d0` installed/launched PASS and tore down cleanly
- Never install experimental/CI APKs over `com.termux.x11`. Kill experimental X only if cmdline starts with `termux-x11gpu com.waydefu.x11gpu :3`. No `pkill -f f8-x11gpu`. No `logcat -c`.
- Persistent `:3` = Display0 waydefu activity, then double-fork + `setsid` so X **ppid=1**. Stop `:3` + `am force-stop com.waydefu.x11gpu` before `pm install-commit` or the session hangs.
- A.3/A.4 stamps stay on. Do not change `sys_ptr` / `PixmapIsOffscreen` / Damage / depth-bailout.

## Closed (do not reopen)

| Gate | Result | Evidence |
|---|---|---|
| P0 non-legacy drawing | CLOSED | experimental `:3` |
| P1 DRI3 `BuffersFromPixmap` | CLOSED | experimental `:3` |
| GPU Present / Fence / FrameTimeline | QUALIFIED / baseline | `evidence/present/`, `evidence/fence/` |
| EXA Copy / Solid | PASS | `evidence/exa/` |
| P2-A XRender probe crash | CLOSED | install-once probe; not pitch/`sys_ptr`. `evidence/session/p2-a4/` |
| P2-B.1 Composite census | CLOSED / PASS | B.1 census recorded GPU Composite 0 at that time; first candidate was Over ARGB→XRGB no-mask. The later P2-B.2 narrow slice is covered below. `evidence/session/p2-b1/` |

## Historical P2-B.2 d7de868 result (superseded)

Fail-closed GPU Over (ARGB→XRGB, no mask, no transform/CA/repeat). Path is taken; pixels are not exact RGB.

Oracle on all three APKs: tests=1514 **fail=1094** exact_px=389108 ±1_px=320972 Xnz=0 **maxΔ=255** got==dst. ±1 not PASS.

| APK | What it tested | Result |
|---|---|---|
| `42d2e3b` CI **34163118589** `:3` 29619 | first GPU Over | BGRA AHB EGLImage samples black (`swizzle=1`) |
| `15a4be3` CI **34165324258** `:3` 27379 | skip EGLImage; GLES RGBA upload | `swizzle=0`; dest still unchanged |
| **`d7de868` CI 34166400010 `:3` 13655** | FD clone of locked BGRA src | FDCLONE=1515, **px0=00000000 ×1515** |

Client pixmaps are `LORIEBUFFER_REGULAR`. `lorieEnsureGpuSampleable` converts to BGRA AHB; PrepareComposite snapshots that mapping and it is empty. PutImage pixels are not what the GPU read.

Evidence: `evidence/session/p2-b2/GATE-P2-B.2.md`, `PROVENANCE.txt`, `retry-15a4be3/`, `retry-d7de868/`.

## P2-B.2 PASS (R3)

- Commit `98224356e40913dcf2188d18748eba9401639850`, CI `34168546084`.
- APK `1.03.01-9822435-07.09.26`, SHA256
  `cb5dbb8909c09d83bf92512792966bc7060153421829a99d52cafbc115ca197c`.
- Stable `:1` PID 26474 remained untouched; experimental `:3` PID 29225.
- Valid per-pixmap-GC PutImage writes were correct in REGULAR S0. S1 AHB
  before copy was zero, S2 after copy matched S0, and S3 FD staging matched.
- Smoke exact RGB: `00ff0000`, `00800000`, `00807f00`.
- Corrected oracle: `tests=1514 fail=0 exact_px_acc=1396616 ±1_px=0
  Xnz=0 maxΔ=0`; `src-op`, `mask-a8`, `dst-argb`, `bilinear`, and `repeat`
  remained software.
- The prior 1094-fail result was caused by the tester using a root depth-24
  GC for depth-32 source PutImage (`BadMatch` 8), not by the GPU slice.
- Post-pass stress passed: x100 `100/100`, mixed100 `100/100`, x1000
  `1000/1000`, all with X alive.
- Bounded isolated XFCE passed for 45s on `:3`: D0/D1/D2/D3
  `1637/1637/1637/1638`, Probe ENTER/RETURN `1638/1638`, no fatal/SIGSEGV/
  SIGILL. Experimental XFCE children were stopped; X3 PID 29225 remained.

## B3a latest snapshot (2026-09-11)

- Artifact `10160961032`, run `34498279213`, exact head
  `1954f82cda9b548ab88f420e428f7296a2d3c72c` was downloaded and verified.
  ZIP SHA256/digest: `7edf7776eba65bbf9cbdf1ffabbd2e9c5e79ebf65e6a41c35f9ef9df8e721da5`.
- ARM64 unstripped `libXlorie.so` SHA256:
  `2d555d13b97b1554cc37574f2e0541d0afd1a98b361c7b572c7d9c9739fb9ba6`;
  Build ID `b15d75a5a3d4217eb736208f18d5a1aa84280bf9`, matching the installed
  APK embedded library exactly by Build ID.
- U4 C2 exact batch16 contract completed: 3 ×
  `CPU-A → R3-A → CPU-B → R3-B`, 12/12 sessions PASS, exact oracle/cell,
  telemetry `11119/11119` per session, CPU fallback=1, R3 fallback=0, no new
  signal, and every teardown `NO_X3_RESIDUE`.
- Aggregate measured-only R3/CPU median=`1.299246x` (CPU
  `2.625000ms`, R3 `3.410521ms`); GPU execution and queue remain
  `not_observable`. This qualifies only the declared exact protocol and does
  not prove a shader speedup or architecture-wide win.
- Historical U4 batch16 R3-B startup SIGSEGV remains
  `observed / non-reproduced`; C2 replay reproduced it `0/3`, so root cause is
  still unknown. Matching unstripped ELF is retained for any later forensic
  work. Stable remains untouched.
- Evidence: `evidence/session/p2-b3a/B3A-T2-U4-C2-20260911.md`,
  `B3A-U4-C2-ARTIFACT-PROVENANCE-20260911.md`,
  `t2-u4-c2-exact-sequence/`.

## 2026-09-11 ARM64 host Android Build Tools / AIDL blocker

This is a new dated S4 observation of an already-known class of ARM64-host
build boundary. The earlier exact `:lorie:compileDebugAidl` / x86-64 AIDL case
is retained in `evidence/session/s3/GATE-S3-RUNTIME.md:215-228` and
`:386-407`; this section binds the current S4 source and commands separately.

### ARM64 host Android Build Tools / AIDL blocker

Observed:

- F8 Ultra / Ubuntu PRoot host: `aarch64`.
- Native `:lorie:buildCMakeDebug[arm64-v8a]`: PASS.
- `:lorie-app:assembleStandaloneDebug`: BLOCKED at
  `:lorie:compileDebugAidl`.
- Installed Android Build Tools `35.0.0/aidl` and `36.0.0/aidl` are
  x86-64 ELF executables with interpreter `/lib64/ld-linux-x86-64.so.2`.
- No usable ARM64 `aidl`, `qemu-x86_64`, or `box64` is present.

Interpretation:

```text
source/native build failure: NO
S4 code regression evidence: NO
APK packaging host-tool incompatibility: YES
```

This records the observed local tool execution boundary only; it does not
claim that Android officially lacks ARM64 support in general.

Policy:

- do not install random or unverified ARM64 Build Tools replacements;
- do not modify Gradle/build semantics merely to bypass qualification;
- do not reuse an old APK or repack an old artifact;
- prefer an exact-source GitHub Actions x64 build;
- preserve commit/source diff identity, APK, unstripped ELF, artifact IDs,
  hashes, and Build ID provenance;
- Stable `com.termux.x11` / `:1` remains forbidden.

Recovery:

```text
exact S4 source
→ x64 CI build
→ APK + unstripped libXlorie.so
→ verify source SHA / artifact / APK hash / native hash / Build ID
→ Experimental :3 only
→ existing S4 runtime gates
```

The current S4 source evidence is
`evidence/session/p2-b3a/S4-PRE-D0A-HYGIENE-20260911.md`. CI recovery completed
on the exact source branch:

```text
branch: qualification/s4-pre-d0a-20260911
head: fd988c45e51692c6cae4420f84466872bedf9bf6
workflow: waydefu/termux-x11 / Build / debug_build.yml
run: 34606849337 (PASS)
APK artifact: 10267113234
unstripped artifact: 10266793366
package: com.waydefu.x11gpu / versionCode 15
ARM64 Build ID: 5c50d21dd8c4610ac6ed031c5a6c765dfd28b9f0
```

The current runtime boundary is ADB, not packaging. The PRoot wrapper
`/usr/local/bin/f8-adb-port` remains invalid because it runs the Termux helper
with Ubuntu `/usr/bin/python3`; the direct helper previously failed with
`dlopen failed: library "libc.so.6" not found`. A native ARM64 adb server was
then isolated on `tcp:5038`; `server-status` passed with version 35.0.2 and
OPENSCREEN mDNS backend. The client does not support `mdns check`,
`track-services`, or `services`. The supplied candidate
`10.56.180.219:46761` failed TLS authentication with
`SSLV3_ALERT_CERTIFICATE_UNKNOWN` and was rejected. Update 2026-09-12: ADB
Gate A later passed on the Termux-home key lane (`10.56.180.219:39929`,
`device`/`25102PCBEG`/`myron`); S4 runtime is CLOSED (see
`evidence/session/p2-b3a/S4-PRE-D0A-HYGIENE-20260911.md`) and D0a is
authorized.

## Gate A A1 latest snapshot (2026-09-12)

- Worktree `src/f8-ahb-gatea-a1`, branch `qualification/gatea-a1-microprobe-20260912`,
  HEAD `3db76baa15c0a6c13460349060485d863102dc86`, committed clean. D0a worktree
  (`qualification/d0a-narrow-20260912` / `a6cc795`) clean, untouched.
- CI run `34688831275` (success, exact checkpoint). APK SHA256
  `5a241f1fb726ecd709ecd601d80f607cbe3413a061d9c1cec66fd27009603583`;
  unstripped ARM64 ELF SHA256
  `6612aa2ee2888d32a3892cad9edb807e90dd21f524557e7af83188b08252a79f`;
  Build ID `8036f683d110370a7a39dfd719cae9a6ee0adee3` embedded==unstripped;
  signer cert `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1`
  exact match with experimental P2-B.2 APK. Formal host zipalign blocked
  (x86-64 tool on aarch64). Artifact evidence: QUALIFIED PASS (provenance only,
  not runtime qualification).
- Runtime STOPPED before oracle: experimental `:3` startup SIGSEGV, PID 21238,
  `signo=11 si_code=1 si_addr=0x0`. Handler frame `+0xeccf8` proven to be the
  pre-existing P2-A.3 handler epilogue, not the original fault. Probe-body entry
  NOT PROVEN; root cause UNKNOWN; oracle `0/9 NOT TESTED`; no Gate A verdict.
- Teardown: experimental force-stop exit 0, `:3` absent afterwards, no restart.
  Stable `:1` PID 14862 cmdline unchanged (live re-scan 2026-09-12 20:29 CST:
  Stable present, experimental empty). HDMI untouched.
- Verdict: A1 byte/import/shader-sampling microprobe PASS (marker run 34694695463,
  HEAD 4196798): PRECALL+ENTRY present, PROBE_BODY_CONFIRMED YES, CONTROL/BGRA/RGBA
  3/3 each SHADER_SAMPLE_EXACT, aggregate runs=9, zero error counters,
  state_restore 0x0000, no Fatal signal, X survived probe, teardown complete.
  Production Gate A: BLOCKED (ownership/result/lifecycle review completed below).
  Earlier PID 21238 startup SIGSEGV root cause STILL UNKNOWN, not merged.
  Not Case A/B/C/D. BGRA-black history superseded for the isolated microprobe path only.
- Production ownership review (read-only, `a6cc795`): direct BGRA capability is
  no longer the blocker, but staging-removal-only is unsafe. Current source has
  contradictory/missing ownership invariants: Composite source remains CPU-locked,
  import has no ready acknowledgment, renderer can skip/fail then still consume a
  serial, timeout paths release pending ownership, completion lacks per-serial
  result/replay and formal acquire/release, imported AHB has no producer fence,
  and teardown has no generation-bound drain/unregister acknowledgment.
  Verdict: Production Gate A BLOCKED; safe server-owned/non-imported design is
  feasible only with a new ownership/result/lifecycle protocol. Evidence:
  `GATE-A-PRODUCTION-DIRECT-AHB-ARCHITECTURE-REVIEW-20260912.md`.
- Evidence: `evidence/session/gate-a-a1/GATE-A-A1-ARTIFACT-PROVENANCE-20260912.md`,
  `runtime/GATE-A-A1-MICROPROBE-EXECUTION-20260912.md`,
  `runtime/GATE-A-A1-CRASH-FORENSICS-20260912.md`,
  `marker/GATE-A-A1-MARKER-EXECUTION-20260912.md`,
  `marker/AUTHORITY-CHECKSUM-A1-MARKER-20260912.md`,
  `marker/apk-elf-verification/marker-apk-elf-report.json`.

## Next (when resuming)

Current next (2026-09-18, **device `5a782f6` INSTALLED; GATE A P2 R7 PASS / COMPLETE 13/13; R8-C1 attempt-05 INVALID frozen; C2–P2 NOT RUN; Production BLOCKED**):
**STOP.** `R8_INVALID POST_END_OBSERVATION` on C1 attempt-05. Do **not** retry C1 attempts 01–05. Do **not** create attempt-06. Do **not** start R8-C2 or R9. Do **not** silent-retry R8 CI **35304122983**, **35305368742**, **35311343984**, or **35321447455**. Do **not** install `bc25170` or `d382c0a`. Do **not** retry `runtime-a4c8177/r7-p1`. Do **not** retry `runtime-a4c8177/r7-p1-validity-02`. Do **not** retry `runtime-a4c8177/r7-p2`. Do **not** retry `runtime-abb27a65/r7-p1`. Do **not** retry `runtime-8545b26/r7-p1`. Do **not** retry `runtime-8545b26/r7-10`. Do **not** retry `runtime-8545b26/r7-10-preflight`. Do **not** retry `runtime-a07d66c/r7-10`. Do **not** retry `runtime-a07d66c/r7-11`. Do **not** use `run-r7-one-cell-a07d66c.sh` for r7-11 or for 8545b26. Do **not** retry `runtime-a07d66c/r7-09`. Do **not** retry `runtime-a07d66c/r7-08`. Do **not** retry `runtime-a07d66c/r7-07`. Do **not** retry `runtime-a07d66c/r7-06`. Do **not** retry `runtime-a07d66c/r7-03`. Do **not** retry `runtime-a07d66c/r7-02`. Do **not** retry `runtime-a07d66c/r7-01`. Do **not** retry `runtime-a07d66c/r7-05-requalification-01`. Do **not** retry `runtime-fdfb1ce/r7-05`. Do **not** retry `runtime-fdfb1ce/r7-04-requalification-01`. Do **not** retry `runtime-7549e36/r7-qualification-01`. Do **not** overwrite `runtime-7549e36/b2-requalification-01` or `b2-requalification-02`. Do **not** retry `runtime-7549e36/repair-validation-01`. Do **not** install `327b028`. Do **not** retry `runtime-feeaa56/stall-obs-01` or `runtime-1f85b80/stall-obs-01` or `runtime-27d8d1b/stall-obs-01`.
Do **not** silent-retry `runtime-0d72332/r1-unset-oracle` or `r1-unset-oracle-rerun1`.
Do **not** silent-retry `runtime-a7528bd/r1-unset-oracle`.
Do **not** overwrite diagnostic-01/02. Do **not** start R2–R6-D1. Do **not** silent-retry PROTO=0. Do **not** second-retry R5 on
`d9b7f60`. Do **not** retry R3 on `88e3f17`, `8479997`, `6c7ee6f`, or
`98b0011`. Do **not** silent-retry historical R6 cells. Production Gate A
BLOCKED.
Authority: `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-05-invalid.md`.

1. Keep P0/P1/P2-A/P2-B.1/P2-B.2 closed and keep the Over predicate narrow.
2. Gate A/D 2026-09-11 architecture review is superseded for Gate A's byte/import
   premise by A1 9/9 exact. The 2026-09-12 production ownership review now governs:
   direct BGRA sampling capability PASS on this F8, but Production Gate A remains
   BLOCKED because current source lacks a checked CPU-release transition,
   import-ready acknowledgment, per-serial success/failure + quiesced replay,
   acquire/release publication, and generation-bound drain/unregister lifecycle.
   Imported/client-owned AHB remains excluded until it has an acquire-fence contract.
   Authority: `evidence/session/gate-a-a1/GATE-A-PRODUCTION-DIRECT-AHB-ARCHITECTURE-REVIEW-20260912.md`.
   The Gate D/D0a decision remains unchanged.
3. S4 PRE-D0a is CLOSED. Gate D0a is CLOSED PASS / PERFORMANCE-POSITIVE:
   one-slot persistent FD staging (`a6cc795`), oracle 4/4 exact incl.
   flag-off equivalence, ON cache 1985 hits/session with 0 violations,
   lifecycle 4/4 NO_X3_RESIDUE, no new fatal signal, Stable untouched.
   Evidence: `evidence/session/p2-b3a/GATE-D0A-DESIGN-20260912.md`.
4. Gate D0b-R1 implementation is REJECTED. D0b-R2 design eliminated the need
   for a cross-process D0b mode flag by identifying a universal existing
   `op==COMPOSITE` region-upload class, and proved stale texels outside the exact
   sampled region harmless under narrow in-bounds R3. However upload success is
   not total: renderer mapping/texture/GL failure has no same-transaction replay,
   and adding a renderer→X result channel is forbidden. D0b-R3 architecture closure
   confirms upload totality is IMPOSSIBLE UNDER CURRENT CONTRACT; stale draw is
   UNSAFE; skip-draw and full-upload fallback are UNSAFE; no existing X replay/fallback;
   new result/replay protocol required. D0b is BLOCKED UNDER CURRENT NO-NEW-PROTOCOL
   REDLINES. Do not implement, build CI/APK, install, or runtime-test it.
   Authority: `evidence/session/p2-b3a/GATE-D0B-R3-FINAL-20260912.md`.
5. If investigating the historical crash, use the retained matching
   unstripped ELF and crash-forensic workflow; do not retry a crash cell
   silently or treat the three clean replays as a fix.
6. Keep Experimental teardown complete and Stable `:1` untouched. Gate H stays
   HOLD. Live re-scan 2026-09-12 20:29 CST: Stable PID 14862 `:1
   -legacy-drawing` present, experimental empty.
7. A1 marker iteration CLOSED 2026-09-12 20:59 CST: single PRECALL/ENTRY commit
   (`4196798`), exact-source CI, artifact re-verified, ONE bounded experimental
   `:3` runtime with full 9/9 exact oracle, immediate teardown, Stable untouched.
8. Production Gate A ownership/result/lifecycle review CLOSED read-only on
   `a6cc795`: current direct-live-AHB contract is BLOCKED.
9. Minimal generation-bound protocol design CLOSED / PROTOTYPE AUTHORIZED, design
   only; no code/build/CI/APK/ADB/device operation. READY is per-buffer within one
   connection+EGL-context generation. Existing queue-entry ABI and
   `completedSerial` quiescence meaning stay unchanged. A versioned shared-state
   result sideband plus READY/UNREGISTER lifecycle messages is required; no native
   fence transport, replay, imported-buffer fence, D0b, or Gate H change. Any
   post-publication failure is generation fail-stop. Authority:
   `evidence/session/gate-a-a1/GATE-A-PRODUCTION-PROTOCOL-DESIGN-20260912.md`.
   Next one action: revise P0–P4 and fatal/UNREGISTER sections per the review,
   then resubmit the implementation plan; do not write code.
10. Protocol ABI review R3 PASS 2026-09-12; P0 implementation is AUTHORIZED
    (design only, still no code/build/runtime). All six R2 gaps closed: frozen
    40-byte result sideband + 40-byte wire header with exact atomic edges and
    lossless SUCCESS derivation; destination ownership on the same terminal
    boundary with SUCCESS-gated repair and drain-or-FATAL resize; single CAS
    fatal edge with credible/poisoned serial sets; cycle-free waiter graph with
    bounded Gate A EGL waits and input-thread-direct wakeup; xcallback fatal
    containment bypassing the blocking rendezvous; minimal both-side retirement
    metadata with exact UNREGISTER/CloseScreen paths. Authority:
    `evidence/session/gate-a-a1/GATE-A-PROTOCOL-ABI-REVIEW-R3-20260912.md`.
    Next one action completed 2026-09-12: P0 exact-ABI diff written as
    `2844a18` (lorie.h +395/-0, additive only) and STATIC PASS — ABI/atomics/
    fatal/waiter/framing/metadata/default-off/entry/completedSerial all PASS,
    `git diff --check` PASS, D0a untouched. Evidence:
    `evidence/session/gate-a-a1/GATE-A-P0-STATIC-IMPLEMENTATION-20260912.md`.
    Native compile qualification completed 2026-09-12:
    `:lorie:buildCMakeDebug[arm64-v8a]` BUILD SUCCESSFUL (exit 0); zero new
    warnings (9 total, all pre-existing incl. shifted keycode-table lines);
    worktree clean, build outputs gitignored. APK packaging NOT attempted
    (known ARM64 AIDL blocker, out of scope).
    P0 CI qualification completed 2026-09-12: first run 34705593764 FAILED on
    x86 with a real defect (align-8 asserts false on LP32); fixed in 97401bc
    (member-8-alignment asserts, no layout change); re-run 34705873575 success
    with headSha=97401bc=remote. APK `75068288…f703` (v15/`1.03.01-97401bc`),
    testzip PASS, STORED 259/259, Build ID `cb87eb7f…` both ends MATCH, signer
    continuity PASS. Evidence: `evidence/session/gate-a-a1/p0-ci-34705873575/`.
11. Gate A P1 boundary review PASS 2026-09-12; P1 IMPLEMENTATION AUTHORIZED
    within the frozen boundary (generation/REGISTER/READY/registry/framing/
    fatal containment; no unlock/queue/sampling/Done/unregister/CloseScreen/
    runtime work). Authority:
    `evidence/session/gate-a-a1/GATE-A-P1-REVIEW-20260912.md`.
12. Gate A P1 implementation CLOSED 2026-09-12 as `5e9eb2a` (+933/-0, 7 files,
    additive only): X nonce/share/registry/framed-send/input-dispatch, renderer
    bind/receive/validate/READY-send, waiter/fatal-wake/HUP containment, guarded
    buffer wrappers. STATIC PASS (checklist incl. 4 self-found fixes) and native
    full-clean compile PASS with zero new warnings. Evidence:
    `evidence/session/gate-a-a1/GATE-A-P1-STATIC-IMPLEMENTATION-20260912.md`.
    P1 CI qualification completed: run 34709782426 success, headSha=5e9eb2a=
    local=remote, first attempt, no defect. APK `645127f8…b7d1fd`
    (v15/`1.03.01-5e9eb2a`), testzip PASS, STORED 259/259, Build ID
    `6f3e1933…` both ends MATCH, signer continuity PASS, P0 markers intact,
    full P1 symbol surface present in unstripped ELF. Evidence:
    `evidence/session/gate-a-a1/p1-ci-34709782426/`.
13. Gate A P2 ownership/direct-submission architecture review PASS 2026-09-13
    against exact clean `5e9eb2a`; P2 IMPLEMENTATION AUTHORIZED, bounded and
    default-off only. Source+destination use one pair lease and one terminal
    fence; first publish performs checked pair unlock under a bounded shared-lock
    transition; success-only pair relock/repair occurs before Done returns.
    Queue ABI and completedSerial meaning stay frozen; all queue users must move
    to P0 accessors. Direct path uses P1 READY textures only (no legacy lookup,
    lock/clone/upload); BGRA source uses direct `.bgra` swizzle into RGBX dest.
    Missing lookup/FBO before GL touch is FAILED_QUIESCED; draw failure is so
    only after a satisfied finite fence; every uncertain completion is FATAL.
    Cross-op admission additionally requires semantic SUCCESS, CPU_LOCKED and
    pendingCount=0; pre-first-submit global queue quiescence closes Present's
    existing early-ACK cell. P2 must also gate ACTIVE on actual-address atomics,
    accept exact BGRA-source/RGBX-destination descriptors without changing P1
    framing, and fail-stop reshare with live P2 imports before sideband reset.
    Authority:
    `evidence/session/gate-a-a1/GATE-A-P2-OWNERSHIP-ARCHITECTURE-REVIEW-20260913.md`.
    Production Gate A stays BLOCKED; no source/build/CI/APK/ADB/runtime/device/
    Stable/HDMI operation; D0a untouched, D0b blocked, Gate H HOLD.
14. Gate A P2 implementation CLOSED 2026-09-13 as `82a87f4` (+868/-39, 4 files):
    pair lease + bounded READY/admission/publish/terminal/SUCCESS-only release
    (X), READY-registry direct draw + finite fences + terminal publication
    (renderer), full P0 accessor wiring, ACTIVE lock-free gate, cross-op
    guards. STATIC PASS (3 self-found fixed incl. RGBX import gate that would
    have dead-ended direct) and native incremental + full-clean compile PASS
    with zero new warnings (41 pre-existing). Evidence:
    `evidence/session/gate-a-a1/GATE-A-P2-STATIC-IMPLEMENTATION-20260913.md`.
    P2 CI qualification completed: run 34716168485 success, headSha=82a87f4=
    local=remote, first attempt, no defect. APK `f9fce1b3…28adba`
    (v15/`1.03.01-82a87f4`), testzip PASS, STORED 259/259, Build ID
    `6a69205c…` both ends MATCH, signer continuity PASS, P0/A1/P1 markers
    intact, all 5 P2 fail-stop literals in both binaries, 6/14 P2 text
    symbols in unstripped ELF (8 absent = inlined single-call-site statics,
    code proven retained by the literals — not a failure per round rule).
    Evidence: `evidence/session/gate-a-a1/p2-ci-34716168485/`.
    Production Gate A stays BLOCKED; D0a untouched, D0b blocked, Gate H HOLD.
15. Gate A P2 runtime qualification design/source review BLOCKED 2026-09-13
    against exact clean `82a87f4`; runtime execution is NOT AUTHORIZED. Decisive
    source defect: the direct branch in `Renderer::applyPendingGpuCopiesLocked`
    does not set `out.lastSerial` or advance `readIndex` because both statements
    remain inside the legacy `else`, so the first direct slot cannot reach the
    finite fence/completed terminal. Additional blockers: direct identity is
    inferred from successful source READY lookup, so a source miss/tuple loss
    falls into legacy CPU-upload handling; reverse Present/COPY/SOLID ordering
    is not closed after first Gate A use; normal UNREGISTER/generation cleanup
    remains absent. Success-path ownership events and registry/ref balance are
    also not observable. Required next work is a separately authorized narrow
    source-correction/observability review and implementation, followed by full
    ARM64+CI+artifact requalification before any runtime authorization.
    Evidence:
    `evidence/session/gate-a-a1/GATE-A-P2-RUNTIME-QUALIFICATION-DESIGN-20260913.md`.
    This review performed no source/build/CI/APK/ADB/runtime/device/Stable/HDMI
    action; Production Gate A remains BLOCKED.
16. Gate A P2 B1–B4 source correction CLOSED 2026-09-14 as `15caa00`
    (+1248/-156, 5 files) on `82a87f4`: direct slot consume (B1), 48-byte
    per-slot identity with lookup-miss FATAL (B2), every-reserve semantic
    quiescence (B3), UNREGISTER/GENERATION_CLOSE lifecycle with GL reverse
    destroy (B4), Experimental default-OFF telemetry. STATIC PASS against
    the four 82a87f4 runtime-design blockers. Native incremental +
    full-clean `:lorie:buildCMakeDebug[arm64-v8a]` BUILD SUCCESSFUL, 0
    errors, 0 new warnings (41 pre-existing fingerprints unchanged).
    `git diff --check` PASS. No ADB/runtime/device/Stable/HDMI.
    Queue ABI 168 B and P0 sideband 40 B unchanged (compiled asserts).
    Evidence: `evidence/session/gate-a-a1/GATE-A-P2-B1-B4-IMPLEMENTATION-20260914.md`.
    P2 CI qualification completed 2026-09-14: run 34772571553 success,
    headSha=15caa00=local=remote fork, first attempt, no defect. APK
    `d69aff2c…0e8d` (v15/`1.03.01-15caa00`), testzip PASS, STORED 259/259,
    Build ID `33a3b67f…` both ends MATCH, signer continuity PASS, all four
    ABIs linked and packaged, B1–B4 fail-stop literals in both binaries.
    Evidence: `evidence/session/gate-a-a1/p2-b1b4-ci-34772571553/`.
    P2 runtime Phase 1 was user-authorized 2026-09-14 against this exact
    artifact. R0 PASS; R1 PROTO-unset PASS (1514/1514, x100/mixed100/x1000,
    Gate A events 0). R1 PROTO=0 FAIL: Experimental `:3` PID **31807**
    SIGSEGV `signo=11 si_code=1 si_addr=0x0` during startup after init
    probes, before holder connect. Handler frame is `p2a3CrashHandler`
    (`InitOutput.c:378` / `+0xeea70`); original fault not proven.
    Classified NEW OBSERVATION. No retry. R2/R3 NOT RUN. Stable `:1` PID
    16085 unchanged. HDMI untouched. Production Gate A stays BLOCKED.
    Evidence: `evidence/session/gate-a-a1/p2-runtime-phase1/`.
    P2 R1 startup SIGSEGV triage T1 diagnostic closed 2026-09-14 as
    `dd81ac0` (`chore(gatea): capture raw crash ucontext`, InitOutput.c
    +48/−1): AS-safe `Upid` + 512-byte `Uraw` dump after existing `Uctx`.
    Native incremental + full-clean PASS, 0 new warnings (41 baseline).
    CI run 34781139248 success, headSha=dd81ac0=local=remote fork, first
    attempt. APK `cc0058d8…d459` (v15/`1.03.01-dd81ac0`), testzip PASS,
    STORED 259/259, Build ID `0892201d…` both ends MATCH, signer continuity
    PASS. Evidence: `evidence/session/gate-a-a1/GATE-A-P2-R1-DIAG-IMPLEMENTATION-20260914.md`,
    `evidence/session/gate-a-a1/p2-r1-diag-ci-34781139248/`.
    This diagnostic artifact is the only T2-authorized APK. Historical
    Phase 1 SIGSEGV on `15caa00`/`d69aff2c…`/`33a3b67f…` remains OBSERVED /
    NON-REPRODUCED ON `dd81ac0` / ROOT CAUSE NOT YET PROVEN.
    T2 startup 6/6 PASS; R1 OFF oracle/stress PASS both unset and PROTO=0;
    R2 imported-AHB rejection PASS (modifier 1255 ×2, GATEA_EVENT=0, exact
    pixels). Evidence: `evidence/session/gate-a-a1/p2-r1-diag-runtime/` and
    `…/r2-imported-reject/GATE-A-P2-R2-RUNTIME-20260914.md`.
    Next: R3 failed on `dd81ac0` (`x-ready-timeout` / reason=4) because the
    Activity process does not inherit `TERMUX_X11_GATEA_PROTO`; bind/peek/drain
    were getenv-gated. Repair `98b0011` (`fix(gatea): bind Activity Gate A from
    shared tuple, not getenv`) CI run 34786907985 success, headSha=98b0011=
    local=remote fork, first attempt. APK `e547eadb…1760` (v15/`1.03.01-98b0011`),
    testzip PASS, STORED 259/259, Build ID `52053312…66cf` both ends MATCH,
    signer continuity PASS. Evidence:
    `evidence/session/gate-a-a1/p2-r3-bound-ci-34786907985/`.
    This repair artifact was installed and requalified 2026-09-14:
    R1 T2 6/6 + OFF oracle/stress PASS; R2 imported-AHB PASS; R3 FAIL
    `x-ready-timeout` on both a reused Activity PID and a fresh COLD
    Activity (`r-hup` proves bind, `GATEA_EVENT=0` means no READY).
    Do not run R3 again on `98b0011`. Peek-diag `6c7ee6f` CI 34789717269
    PASS, APK `d20e6091…4e8a`, Build ID `49be84ea…ae00` MATCH, installed
    over experimental only. T2 FAIL B2 PROTO=0 SIGSEGV PID **21977**
    `PC=0x4800226c` (same class as B3a U4). Do not silent-retry B2.
    R1 oracle / R2 / R3 not authorized until dispositioned. Evidence:
    `evidence/session/gate-a-a1/p2-r3-diag-runtime/GATE-A-P2-R1-T2-FAIL-20260914.md`.
    No Production enable. Do not install superseded `dd81ac0` or
    `15caa00`. Stable / HDMI untouched.
    Drain-wait repair `8479997` CI 34791993198 PASS, APK `0a9d91f6…23a2`,
    Build ID `b072c9d2…654a` MATCH, installed over experimental only
    2026-09-14 12:06:59. R1 oracle/stress PASS (unset X 26155, PROTO=0
    X 27458; 1514/1514 fail=0 maxΔ=0; stress 100/100/1000; GATEA_EVENT=0).
    T2 6/6 was not rerun. R2 PASS (X 28794, modifier 1255 ×2,
    exact_px=64 got0=`00804000`). R3 FAIL: Activity 27805 / X 31408,
    HANDLE type=1 id=6 then `GATEA_DRAIN imports=1` on tid 31188, then
    2s `x-ready-timeout` / `r-hup`; `GATEA_EVENT=0`. Drain-wait is
    proven; READY publish after validate is not. User paused 12:17 CST.
    Do not retry R3 on `8479997`. Evidence:
    `evidence/session/gate-a-a1/p2-r3-drain-runtime/`.
    Terminal/observability repair `88e3f17` CI 34822381586 PASS, first
    attempt, headSha match. APK `7e5540a2…8616` (v15/`1.03.01-88e3f17`),
    testzip PASS, STORED 259/259, Build ID `e91c7683…be12` both ends
    MATCH, signer continuity PASS. Installed over experimental only
    2026-09-14 16:51:37. R1 oracle/stress PASS (unset X 12959, PROTO=0
    X 19530; 1514/1514 fail=0 maxΔ=0; stress 100/100/1000; GATEA_EVENT=0).
    T2 6/6 was not rerun. R2 PASS (X 26140, modifier 1255 ×2,
    exact_px=64 got0=`00804000`). R3 FAIL: Activity 18496 / X 31868,
    HANDLE type=1 id=6 then `GATEA_DRAIN imports=1`, full VALIDATE
    through `VALIDATE_TERMINAL_READY` + renderer REGISTER_READY, then
    2s `x-ready-timeout` / `r-hup`. Silent-validate drop is falsified;
    X never consumed READY. Do not retry R3 on `88e3f17`. Evidence:
    `evidence/session/gate-a-a1/p2-r3-terminal-ci-34822381586/` and
    `evidence/session/gate-a-a1/p2-r3-terminal-runtime/runtime-88e3f17/`.
