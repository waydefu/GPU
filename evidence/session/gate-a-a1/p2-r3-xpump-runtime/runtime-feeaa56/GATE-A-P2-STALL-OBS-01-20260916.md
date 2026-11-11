# Gate A P2 stall observation-01 — 2026-09-16 `feeaa56` **CASE_LOOP**

One authorized device observation. **Not B-2.** **Not R7.** Timeout stayed **2000 ms**. No retry.

ADB had been off; the operator restarted it. Reconnect used TLS port **37077** (install had used **45645**). This is infrastructure recovery of the **same** authorized cell, not a second stress. `stall-stress1000.out` did not exist before this run.

| Field | Value |
|---|---|
| HEAD / APK | `feeaa569b86216126116c9bd99037a014efe0b79` / `1.03.01-feeaa56-16.09.26` CI **35076884763** |
| SHA256 / Build ID | `a2d92ff9…3210` / `62d4a3f6…10f2` MATCH install cell `runtime-feeaa56/r0/` |
| lastUpdateTime | 2026-09-16 17:21:53 (unchanged by this observation) |
| serial | `10.191.48.13:37077` live-fetched after ADB restart |
| Screen | Awake, `isKeyguardShowing=false` |
| X3 | PID **23034** cmdline `termux-x11gpu com.waydefu.x11gpu :3` mode=unset `NO_GATEA_ENV` |
| Renderer | Activity pid **7175**; GLES tid **22960** (`STALL_PHASE`) |
| Stress | `p_b2_stress` SHA256 `3e79b5cf…3c56` `1000` **ok=81 fail=919 alive=0** RC=1 (trigger only; X fatal-halted) |
| Window | 2026-09-16T17:29:50 → 17:29:53 +08 |
| Gcomp Done | **81** |
| EXA wait timeout | **1** `serial=86 scheduled=1` at 17:29:53.583 |
| Fatal | `GATEA_FATAL_HALT what=x-exa-composite-wait reason=4` at 17:29:53.587 |
| timeout→Done | **0** (repair held) |
| pixel_mismatch | **0** (GETIMAGE_NO_REPLY is X death, not a pixel fail) |
| `STALL_PHASE` | **468** follow: NOTIFY 86/86, SWAP 74/74, NEXT_FENCE 74/74 |
| NOTIFY_ENTER / EXIT | **86 / 86** follow **and** unfiltered — **OBSERVED** (function-body wrap valid) |
| apply | **83** follow = unfiltered (`gles-renderer`) |
| NOTIFY max | **0.105 ms** (gt2000ms=0; unmatched=0) |
| SWAP max | **1.479 ms** (EGL_TRUE; gt2000ms=0) |
| NEXT_FENCE max | **1.751 ms** (EGL_CONDITION_SATISFIED 12534; gt2000ms=0) |
| fromDequeueTime | **OBSERVED** 2048 ms at 17:29:53.616 frameNumber 75 (teardown window; not a proven GLES wait site) |
| HDMI | observe-only; activity `display=0` |
| Stable | PID **14604** `1.03.01-11b82d9-06.09.26` lastUpdateTime **2026-09-07 22:55:03** UNTOUCHED |
| Teardown | X dead after fatal; **NO_X3_RESIDUE**; Stable PID unchanged |

Classifier: `stall-obs-01/stall-phase-classify.txt` `verdict=CASE_LOOP`.
Durations: `stall-obs-01/stall-phase-durations.txt`.

Instrumentation is **valid**. apply≥10 and NOTIFY>0, so this is **not** `DIAGNOSTIC_RUN_INVALID`.
The parent `1f85b80` coverage gap (apply without NOTIFY) is **closed** on this APK.

## Serial 86 timeline (wall clock +08)

| t | Who | Event |
|---|---|---|
| 17:29:51.566 | GLES 22960 | apply 5×24 (serial **85**) |
| 17:29:51.567 | GLES 22960 | `NOTIFY_*` cs=rd=wr=**85** (0.023 ms) |
| 17:29:51.568 | GLES 22960 | `SWAP_*` result=1 (0.102 ms) |
| 17:29:51.568 | X 23034 | `Gcomp Done` (serial 85) |
| 17:29:51.569 | GLES 22960 | `NEXT_FENCE_EXIT` result=12534 cs=rd=wr=**85** lag=0 |
| 17:29:51.579 | X 23034 | `Gcomp Prepare TRUE` (serial **86**) |
| 17:29:51.581 | X + Activity 7175 | `Gcomp RECT` 17×17; shared buffers id 251/250 **received** on pid 7175 **main** |
| 17:29:51.581–53.583 | GLES 22960 | **NO** apply / NOTIFY / SWAP / NEXT_FENCE for serial 86 |
| 17:29:53.583 | X 23034 | `EXA GPU composite wait timeout serial=86 scheduled=1` (RECT→timeout **2002 ms**) |
| 17:29:53.587 | X 23034 | `GATEA_FATAL_HALT` |
| 17:29:53.616 | SurfaceFlinger | `fromDequeueTime: 2048ms` frame 75 (after halt) |
| 17:29:53.620 | GLES 22960 | `rendererSetWindow 0x0` then teardown `NOTIFY_*` cs=0 |

GLES tid **22960** logged no `LorieNative` / `gles-renderer` line from `NEXT_FENCE_EXIT` of 85 until teardown. Activity main thread **did** register the serial-86 buffers. X published; GLES did not consume.

## Classification

- **CASE_NOTIFY** FALSIFIED on this stall: NOTIFY pairs matched, max 0.105 ms.
- **CASE_SWAP** FALSIFIED: SWAP max 1.479 ms, last SWAP_EXIT of 85 at 51.568.
- **CASE_NEXT_FENCE** FALSIFIED: NEXT_FENCE max 1.751 ms, last EXIT of 85 at 51.569.
- **CASE_LOOP** OBSERVED: after S-1 completed with empty queue (cs=rd=wr=85), serial 86 was published and sat unconsumed until the 2000 ms EXA wait expired.

`fromDequeueTime: 2048ms` is **OBSERVED** and time-aligned with the gap, but it is a SurfaceFlinger teardown-window line. Do **not** promote it to a proven GLES dequeue site. No `waitForNextFrame` marker exists.

Source binding (read after this cell): `waitForNextFrame` is set in `redrawLocked` and cleared only on the X thread by `lorieRedraw` (AChoreographer). `lorieGpuCopyWait` is `usleep(200)` with no event pump, so that clear is deferred for the whole wait. GLES `threadLoop` used infinite `pthread_cond_wait`. X signals `rendererCond` without Activity `stateLock` (process-private). Lost wakeup + no Choreographer pump matches this 2 s silence.

## Verdict

```
CASE_LOOP
CASE_NOTIFY FALSIFIED
CASE_SWAP FALSIFIED
CASE_NEXT_FENCE FALSIFIED
not a B-2 PASS
not a B-2 FAIL
B-2 remains BLOCKED (0d72332 serial 2370 + rerun1 serial 1810)
timeout→Done ABSENT (repair held)
R7 NOT STARTED
timeout 2000 UNCHANGED
RCA: consume-delay CONFIRMED on this cell
     (X published S=86; GLES tid 22960 did not apply before 2000 ms)
     inner NOTIFY/SWAP/NEXT_FENCE waits are not the 2 s blocker
```

This cell **DID REPRODUCE** a >2 s EXA Composite stall. Historical `runtime-1f85b80/` / `runtime-27d8d1b/` STALL_NOT_OBSERVED cells stay frozen and are **not** contradicted (those runs did not hit this stall). Do **not** retry this cell (`stall-stress1000.out` exists).

Install evidence: `runtime-feeaa56/r0/INSTALL-feeaa56-20260916.md`.
Frozen `runtime-1f85b80/` / `runtime-27d8d1b/` / `runtime-0d72332/` / `runtime-a7528bd/` unchanged.

Follow-up source fix (not this APK): `src/f8-ahb-gatea-case-loop` / `GATE-A-P2-CASE-LOOP-FIX-20260916.md`.
