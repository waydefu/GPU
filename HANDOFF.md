# GPU Research Handoff — 2026-09-16 Gate A P2 R7 **BLOCKED** (B-2 R1 FAIL on `a7528bd`)

> Device experimental is **`a7528bd`** on `com.waydefu.x11gpu` only
> (CI **35007764673**). Frozen R6 worktree `src/f8-ahb-gatea-r6-retire` HEAD
> **`0f1e54699d0b11a781f2c044fbc77505f8a53bd8`** still clean vs fork — **do not mutate**.
> Historical **R6 PASS** on `0f1e546` remains the last qualified R6 runtime.
> R7 Artifact B is **COMMITTED+CI+INSTALLED**
> `a7528bd25b89d0408bc15002e10bccefaeef3028`. Host PASS; CI PASS; install PASS.
> B-2 R1 unset first attempt **FAIL** (stress 999/1000). Diagnostic-01
> **DID NOT REPRODUCE**. Diagnostic-02 **RCA IDENTIFIED**. EXA Composite
> timeout repair is **local dirty** on
> `src/f8-ahb-gatea-exa-timeout` /
> `fix/gatea-exa-composite-timeout-20260916` (uncommitted). Device run
> **not authorized**. R7 cells **not started**.
> Canonical next-agent brief:
> `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md`.
> Stable `:1` PID **17922** untouched. HDMI untouched. Stop before R8.
> Production Gate A **BLOCKED**.

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
PRODUCTION GATE A BLOCKED
```

Do not reopen P0/P1/P2-A/P2-B.1/P2-B.2. Do not treat ±1 UNORM as PASS. Do not open a PR. Do not touch stable `:1`. Do not leave XFCE/xfwm running on experimental `:3` as a daily session; the R3 bounded window already passed and was stopped.

## Current Gate A P2 runtime (2026-09-16 device a7528bd INSTALLED; B-2 R1 FAIL; R7 BLOCKED)

Next-agent brief:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260916.md`.
Prior `95e6f96` D2 physical-race brief remains historical:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md`.
Prior `88e3f17` R3 FAIL remains historical:
`evidence/session/gate-a-a1/p2-r3-terminal-runtime/HANDOFF-NEXT-AGENT-20260914.md`.

| | |
|---|---|
| Worktree (installed source) | Device **`a7528bd`**; R7 worktree HEAD **`a7528bd25b89d0408bc15002e10bccefaeef3028`**; frozen R6 `src/f8-ahb-gatea-r6-retire` **`0f1e546`** clean |
| R6 implementation worktree | `/root/projects/GPU加速/src/f8-ahb-gatea-r6-retire` branch `fix/gatea-r6-present-retirement-20260915` HEAD **`0f1e546`** (fork in sync; origin ABSENT) |
| Historical R6 source | `/root/projects/GPU加速/src/f8-ahb-gatea-r6` HEAD **`95e6f96`** clean; do not overwrite its cells |
| Control | `/root/projects/GPU加速/src/f8-ahb-gatea-a1` HEAD **`88e3f17`** clean |
| Installed APK | `com.waydefu.x11gpu` `1.03.01-a7528bd-15.09.26` CI **35007764673** |
| APK SHA256 | `c29b1c68df613d40d8bfd93b44887ffd389419d8ca5f36661d1a48b3f03f4c2c` MATCH on-device |
| Build ID | `aa1d23e7fc88048f40c450ca5bacf0506cb93b9c` MATCH |
| lastUpdateTime | 2026-09-16 02:40:28 |
| Stable | `com.termux.x11` `1.03.01-11b82d9-06.09.26` PID **17922** `:1` UNTOUCHED (package lastUpdateTime 2026-09-07 22:55:03 unchanged) |
| Last ADB | `10.191.48.13:43399` live-fetched `_adb-tls-connect._tcp.local.` |
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
| R7 Artifact B source | **COMMITTED** `a7528bd` on `src/f8-ahb-gatea-r7`. Events 35/36, shared-state fault tail, SUMMARY/ring dump, present retire trace. Frozen R6 tree untouched. Host verifiers PASS. |
| R7 CI | **PASS** run **35007764673** `workflow_dispatch` exact headSha `a7528bd`. Artifact QUALIFIED. SHA256 `c29b1c68…4c2c` Build ID `aa1d23e7…3b9c`. |
| R7 install | **DONE** experimental only. SHA/Build ID MATCH. Stable PID **17922** UNTOUCHED. `runtime-a7528bd/r0/`. |
| R7 B-2 R1 unset | **FAIL** first attempt X PID **17192**; oracle 1514/1514; stress 100/100 PASS; 1000 **ok=999 fail=1 alive=1**; event 35=0; SUMMARY `x-close-screen` counters 0. Cell `runtime-a7528bd/r1-unset-oracle/`. Do not silent-retry. **Authoritative FAIL unchanged.** |
| R7 B-2 R1 diagnostic-01 | **DID NOT REPRODUCE** X PID **29184**; diagnostic `p_b2_stress` 1000 **ok=1000 fail=0 alive=1** exit 0; no `B2_DIAG_FAIL`; EXA timeout count **0**; Gcomp Done **1000**; SF `fromDequeueTime: 1709ms` once (frame 2). Cell `runtime-a7528bd/r1-unset-diagnostic-01/`. Do **not** overwrite. Not a B-2 PASS. |
| R7 B-2 R1 diagnostic-02 | **RCA IDENTIFIED** X PID **10903**; `ok=997 fail=3 n=1000 alive=1`; 3× `B2_DIAG_FAIL` `PIXEL_RGB_MISMATCH` (`got==dst`); 3× `EXA GPU composite wait timeout` serial 206/488/941 then same-ms `Gcomp Done`; Probe enter 202/484/937; RECT→timeout 2001–2002 ms. Cell `runtime-a7528bd/r1-unset-diagnostic-02/`. Do **not** overwrite. Not a B-2 PASS. Not R7. |
| EXA Composite timeout repair | **READY FOR B-2 REQUALIFICATION — DEVICE RUN NOT AUTHORIZED**. Worktree `src/f8-ahb-gatea-exa-timeout` branch `fix/gatea-exa-composite-timeout-20260916` HEAD still `a7528bd` + dirty `InitOutput.c` + untracked `scripts/verify_exa_composite_wait.py`. Wait-false → `gateAXFatal("x-exa-composite-wait", TIMEOUT)`. Verifier RED on `a7528bd` / GREEN on repair. Do **not** mutate frozen R6. Do **not** start R7. |
| Next | Device B-2 requalification of this repair requires **new explicit authorization** (build/install APK, then R1-unset). Do **not** silent-retry `r1-unset-oracle`. Do **not** overwrite diagnostic-01/02. Do **not** start R7. Stop before R8. Production Gate A remains BLOCKED. |

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

Current next (2026-09-16, **device `a7528bd` INSTALLED; B-2 R1 FAIL; EXA timeout repair local-only**):
Do **not** start R7 cells. Do **not** silent-retry `runtime-a7528bd/r1-unset-oracle`.
Do **not** overwrite diagnostic-01/02. B-2 requalification of
`src/f8-ahb-gatea-exa-timeout` requires **new explicit authorization**
(build/install; no silent device run). Do **not** start R8. Do **not** silent-retry PROTO=0. Do **not** second-retry R5 on
`d9b7f60`. Do **not** retry R3 on `88e3f17`, `8479997`, `6c7ee6f`, or
`98b0011`. Do **not** silent-retry historical R6 cells. Production Gate A
BLOCKED.
Authority: `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md`.

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
