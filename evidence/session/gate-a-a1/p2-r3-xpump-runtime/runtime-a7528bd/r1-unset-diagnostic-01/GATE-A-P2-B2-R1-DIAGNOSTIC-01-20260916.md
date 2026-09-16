# Gate A P2 B-2 R1-unset diagnostic-01 — 2026-09-16

```
STATUS: DIAGNOSTIC REPRODUCTION DID NOT REPRODUCE
CANDIDATE: a7528bd25b89d0408bc15002e10bccefaeef3028
APK: 1.03.01-a7528bd-15.09.26  CI 35007764673
X PID: 29184  DISPLAY :3
MODE: TEST/PROTO/TELEMETRY/R6-OOM unset (proven /proc/environ)
STRESS: ok=1000 fail=0 n=1000 alive=1  exit=0
B2_DIAG_FAIL: NONE
EXA GPU composite wait timeout: 0
Gcomp Prepare/Done: 1000/1000
AUTHORITATIVE B-2 FAIL UNCHANGED: runtime-a7528bd/r1-unset-oracle/
```

This is **not** B-2 requalification. This is **not** R7. Do not treat
`1000/1000` as qualification PASS.

## Preflight

- R7 worktree HEAD `a7528bd25b89d0408bc15002e10bccefaeef3028`
- Frozen R6 HEAD `0f1e54699d0b11a781f2c044fbc77505f8a53bd8` (untouched)
- Diagnostic ELF
  `p2-r1-diag-runtime/fixtures/p_b2_stress`
  SHA256 `3e79b5cf875f5d7d05a25634983a44d9acfe67dfb885bf11f19b2cdb70e43c56`
- Opaque preserved
  `p_b2_stress.opaque-20260916`
  SHA256 `d020d4531e004f4051b19b6b5ae9c1e92b7352aadfbd82891c4f18d3cc3504f9`
- Cell `r1-unset-diagnostic-01/` was **absent** before this run
- Old cell `r1-unset-oracle/` still contains
  `STRESS mixed=0 ok=999 fail=1 n=1000 alive=1`
- Installed experimental `1.03.01-a7528bd-15.09.26` lastUpdateTime
  `2026-09-16 02:40:28`
- Screen Awake, keyguard false
- No APK rebuild/install; harness not modified this run

## Stable-before / after

| | PID | cmdline | package |
|---|---|---|---|
| before | **17922** | `termux-x11 com.termux.x11 :1 -legacy-drawing` | `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03 |
| after | **17922** | same | same |

No Stable restart/kill/install. Contamination: **none**.

## Experimental cleanliness / env

- Pre: no `:3` process, no X3 socket
- Launch: `start-x3.py` → X PID **29184** `termux-x11gpu com.waydefu.x11gpu :3`
- `/proc/29184/environ`: **NO_GATEA_ENV** (no TEST_FAULT, TEST_ARM,
  R6_PRESENT_REQUEUE_FAIL, PROTO, TELEMETRY)
- Holder `p_b3a_hold` HOLD READY (session keep-alive only; not a
  qualification cell)
- Post: `NO_X3_RESIDUE`; Stable 17922

## Exact command

```
/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_b2_stress 1000
```

- DISPLAY=:3
- start wall `2026-09-16T09:57:45+08:00`
- end wall `2026-09-16T09:58:01+08:00`
- stdout: `STRESS mixed=0 ok=1000 fail=0 n=1000 alive=1`
- stderr: empty
- exit code: **0**
- `B2_DIAG_FAIL`: **did not appear**

Host `command.txt` field `start_mono_ns` is `date +%s%N` (wall-clock ns),
**not** CLOCK_MONOTONIC. No client monotonic fail timestamp exists because
there was no failure. Do not invent a monotonic mapping onto logcat.

One-run rule: **this cell must not be overwritten; do not rerun
diagnostic-01.**

## Failure detail

本次未重現，無 Failure detail。

## Server / renderer correlation

Logcat capture: tagged existing Android logs only
(`LorieNative:I`, `Layer:W`, `SurfaceFlinger:W`, …). Bounded file
`logcat-follow.txt` (42162 lines).

| Signal | Count / evidence |
|---|---|
| `EXA GPU composite wait timeout` | **0** |
| `Gcomp Prepare TRUE` | **1000** |
| `Gcomp Done` | **1000** |
| `GATEA_EVENT` | **0** |
| fatal / SIGSEGV / SIGILL | **0** |
| SUMMARY | `where=x-close-screen` all 28 counters = 0 |
| waydefu `fromDequeueTime` | **1** line, **1709ms**, frameNumber **2**, `09:57:45.818` |

First composite: `09:57:45.811` Gcomp 1×1 `px0=01010000` then Done `09:57:45.814`.
The SurfaceFlinger stall at `09:57:45.818` is **after** that first Done, on
display frame 2 — compositor dequeue, not an EXA wait-timeout.

Last Done: `09:58:01.247`. Stress lifetime ~16 s. X remained alive through
the client (`X3_ALIVE=yes`).

Original authoritative cell had timeout `serial=2704` + SF `2146ms` **and**
`fail=1`. This diagnostic lifetime had SF `1709ms` **without** timeout and
**without** fail.

## Correlation verdict

**NO CORRELATION**

There is no `B2_DIAG_FAIL` and no EXA timeout to bind. The single SF stall
did not coincide with a client pixel/X error.

## RCA verdict

**DIAGNOSTIC REPRODUCTION DID NOT REPRODUCE**

Original `runtime-a7528bd/r1-unset-oracle/` remains the authoritative B-2
R1-unset FAIL. This cell does **not** invalidate that FAIL, does **not**
qualify `a7528bd`, and does **not** start R7.

## Existing hypothesis impact

**UNCHANGED**

Leading hypothesis remains: `lorieGpuCopyWait` 2000 ms timeout → Done
without completion proof → GetImage stale/incomplete. This run never
entered the timeout path (`timeout_count=0`, every Prepare has a Done).
A non-reproducing 1000/1000 therefore neither supports nor refutes that
chain. It does show that a ~1.7 s SurfaceFlinger dequeue stall at session
start is **not sufficient** by itself to produce `fail=1`.

## Cleanup

- killed X 29184 (cmdline matched `termux-x11gpu com.waydefu.x11gpu :3`)
- `am force-stop com.waydefu.x11gpu`
- sockets/locks removed
- `NO_X3_RESIDUE`
- Stable 17922 unchanged
- HDMI untouched
- `r1-unset-oracle/` not modified

## Project status after this run

- R6 = PASS frozen `0f1e546`
- B-2 = **BLOCKED** at first R1-unset baseline (authoritative FAIL)
- R7 = **NOT STARTED**
- R8+ = unauthorized
- Production Gate A = **BLOCKED**

## Recommended next action (do not execute here)

Authorize a **second** diagnostic reproduction in a **new** cell
`runtime-a7528bd/r1-unset-diagnostic-02/` using the same diagnostic
`p_b2_stress`, still TEST/PROTO/TELEMETRY unset, still no APK/server
mutation, still no silent-retry of `r1-unset-oracle`. Goal: obtain one
`fail≠0` plus `B2_DIAG_FAIL` so iteration/stage/pixel can be bound to
any contemporaneous EXA timeout serial.

Do **not** reuse or overwrite `r1-unset-diagnostic-01/`.
