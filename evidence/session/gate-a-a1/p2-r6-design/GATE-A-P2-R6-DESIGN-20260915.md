# Gate A P2 R6 — design-complete cross-operation ownership

Date: 2026-09-15

## Status

```text
DESIGN REVIEW: COMPLETE
IMPLEMENTATION: AUTHORIZED 2026-09-15 / SOURCE ON qualification/gatea-r6-20260915
BUILD / CI / APK: PASS run 34926730189 / ARTIFACT QUALIFIED (device 9369553)
INSTALL / RUNTIME: D1 PASS retry5 / D2-INFLIGHT-retry1 FAIL / D2-OOM NOT RUN
D2 COMPLETED ROOT CAUSE: PROVEN — GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md
SOURCE FIX: COMMITTED 54ff35b then wait-or-fatal (local; see HANDOFF HEAD)
D2 HOLD: host remaining CLOSED; wait C implemented; do not push until CI
ROLLBACK SHA: 37d839323255b4830d657da3bcbf7f616bc78ad3 (device APK unchanged)
R6 bounded client 37d8393: FROZEN CLIENT_OK / DO NOT OVERWRITE
  cell runtime-37d8393/r6-cross-op/  X 11495
R7: NOT STARTED / still source-blocked (TERMUX_X11_GATEA_TEST_FAULT absent)
Production Gate A: BLOCKED
Stable / HDMI: UNTOUCHED
```

This document finishes the R6 architecture that
`GATE-A-P2-RUNTIME-QUALIFICATION-DESIGN-20260913.md` §R6 required and that the
bounded client cell explicitly did not claim. It does not rewrite that frozen
20260913 text. Additive errata are in §2.

It does not authorize C/C++ edits, fixtures, CI, install, or a design-complete
R6 runtime.

## 1. Authority and inspected state

| Item | Authority |
|---|---|
| Installed worktree | `/root/projects/GPU加速/src/f8-ahb-gatea-r5-fix` |
| Branch | `fix/gatea-r5-backpressure-20260915` |
| Source HEAD | `37d839323255b4830d657da3bcbf7f616bc78ad3` clean |
| Frozen control | `/root/projects/GPU加速/src/f8-ahb-gatea-a1` `88e3f17` clean |
| Qualification design §R6 | `../GATE-A-P2-RUNTIME-QUALIFICATION-DESIGN-20260913.md` lines 350–366 |
| Bounded R6 cell | `../p2-r3-xpump-runtime/runtime-37d8393/GATE-A-P2-R6-RUNTIME-20260915.md` |
| Runtime handoff | `../p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md` |
| B3 quiescence (source) | `InitOutput.c` `gateADirectTryPrepare` + `gateAQueueSemanticallyQuiescent` |
| Present early-ACK (source) | `xserver/present/present_execute.c` lines 111–135 |
| Dispatch choke point | `xserver/dix/dispatch.c` lines 519–553 |
| Terminal wait | `InitOutput.c` `gateAWaitTerminal` (usleep + shared `completedSerial`, 2000 ms) |

Frozen invariants remain:

- Stable `com.termux.x11` / `:1` is never touched.
- Experimental work remains default OFF and isolated to `com.waydefu.x11gpu` / `:3`.
- Queue entry ABI remains 168 bytes.
- Gate A frame header remains 40 bytes.
- P0 result sideband remains 40 bytes.
- Direct side metadata remains 48 bytes.
- `LORIE_GATEA_COUNTER_MAX` and `struct LorieGateATelemetry` layout stay unchanged.
- READY / UNREGISTER_ACK / GENERATION_CLOSED / `gateAWaitTerminal` budgets remain 2000 ms.
- Ownership, completion, fence, replay, predicate, D0a, D0b, and Gate H semantics are not reopened here.
- Telemetry remains default OFF (`TERMUX_X11_GATEA_TELEMETRY` exact `"1"` publishes the enable word).
- R7 fault hook `TERMUX_X11_GATEA_TEST_FAULT` stays absent and unused.

## 2. Additive errata on the 20260913 R6 text

The 20260913 gate is still the product requirement. Three premises in that
paragraph are now source-narrowed.

### 2.1 B3 no longer source-blocks R6

20260913 said R6 was source-blocked until symmetric prior-work admission.
On `37d8393`, `gateADirectTryPrepare()` always calls
`gateAQueueSemanticallyQuiescent()` before taking a lease. The historical
`!gateAUsed` first-use hole is gone. R6 is **observability-blocked** and
**Present-OOM-untested**, not B3-blocked.

### 2.2 Do not add a renderer delay

20260913 asked to hold renderer completion “below the 2 s bound” so a second
client could submit during the window. On this DDX that window is already the
synchronous `gateAWaitTerminal()` / `lorieGpuCopyWait()` inside `DoneComposite`
/ `DoneCopy` / `DoneSolid`. Those waits run on the only Dispatch thread.

A synthetic renderer sleep would change fence/completion timing without adding
proof. **Rejected.** The 2000 ms figure stays a fatal timeout, not a delay
target.

### 2.3 Timing alone is still not proof; COPY/SOLID-first in-flight is N/A

Client `clock_gettime` on send/reply remains insufficient (bounded cell B
already printed this).

EXA COPY and SOLID wait inside `DoneCopy` / `DoneSolid` before Dispatch can
run another request. A second client **cannot** observe those GPU copies as
in-flight prior work. Sequential COPY-then-direct is already proven by bounded
cell A (`runtime-37d8393/r6-cross-op/`). Design-complete R6 does not invent a
COPY/SOLID in-flight reverse-admission cell.

The only GPU copy that returns to Dispatch while the renderer may still be
working is **Present** (`present_execute_copy` requeues a vblank instead of
waiting). Reverse admission (direction 2) is a Present problem.

### 2.4 Present GPU copies publish `completedSerial` without EVENT_COMPLETED

D2-INFLIGHT-retry1 (X 20856) **PROVED** CALLBACK serial 6 then REJECT
reason=1, then later Composite PUBLISH serial 8. EVENT_COMPLETED serial 6
was **ABSENT**. Present copies are `LORIE_GPU_OP_COPY` (`gateASeen=0`).
Admission uses `completedSerial` (`gateAQueueSemanticallyQuiescent`); the
judge uses telemetry event 14. Those are not the same signal.

User grant 2026-09-15 (2+1): trace COMPLETED on the existing legacy
`PublishCompleted` sites. Fence order unchanged. Packet:
`GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md`. Source `54ff35b`.
Device remains `9369553` until a new CI APK.

Official Present CompleteNotify **client serial** is not GPU serial S.
Wait CompleteNotify only **after** the racing Composite.

### 2.5 HOLD 2026-09-15 — do not push `54ff35b` into D2

Review: telemetry-only `54ff35b` is clean but insufficient. Blocking:

1. D2-OOM early ACK drops pending/extra refs while GPU may still run
   (`present_execute.c` ~132–153). Conflicts with 20260913 “no early ACK”.
2. Judge could PASS with no COMPLETED; `serial == S` misses batch watermark
   `serial >= S`; logcat order ≠ telemetry `seq`.

Corrected oracles and chosen OOM wait are in
`GATE-A-P2-R6-D2-HOLD-20260915.md`. Host judge + bind tests updated.
**C wait not implemented. No fork push / CI / install.**

§6.3 `PRESENT_EARLY_ACK` as a PASS premise is **withdrawn**.

## 3. Thread model that R6 must prove, not change

```text
X main thread = dix Dispatch = lorie EXA/Present callbacks = conn_fd pump
```

There is still no `InputThreadPreInit()` (R3 design). Consequences:

1. While `gateAWaitTerminal()` is in `usleep`, Dispatch does not call
   `ReadRequestFromClient`. A second client's bytes sit in the AF_UNIX buffer.
   `ProcCopyArea` / `ProcRenderComposite` / `ProcPresentPixmap` / `ProcGetImage`
   cannot run until the wait returns SUCCESS or FATAL.
2. **Forbidden:** pumping X client fds, `WaitForSomething()`, or
   `ReadRequestFromClient` from inside `gateAWaitTerminal`, `lorieGpuCopyWait`,
   or any Gate A lease. The R3 conn_fd pump during REGISTER/UNREGISTER waiters
   stays; it is not a license to dispatch X11 clients during a terminal wait.
   If a later change pumps clients during wait, R6-D1 must FAIL.
3. Present is the exception that makes direction 2 real: after
   `lorieTryScheduleGpuCopy` it can `queue_vblank` and return, leaving
   `writeIndex != readIndex` and `completedSerial < gpuCopySerialCounter`
   while Dispatch continues.

`loriePrepareAccess` refuse-on-lease (`InitOutput.c` ~3434) is same-thread
reentrancy inside one Prepare→Done. A second client cannot hit it unless (2)
is violated. D1-GETIMAGE therefore proves **queued until SUCCESS**, not
lease-refuse.

## 4. Proven vs missing

| Claim | Status |
|---|---|
| Sequential COPY then direct Over, exact 64 px `00804000` | PROVEN (bounded A) |
| Two connections, Composite then CopyArea, exact pixels, X alive | PROVEN (bounded B, CLIENT_OK only) |
| Direct N=2 counters match, no fatal | PROVEN |
| Request-arrived vs callback on the X trace | NOT PRODUCED (`LORIE_GATEA_EVENT_MAX` follows `GENERATION_CLOSED`) |
| Second-client CALLBACK after direct SUCCESS, never before | NOT PRODUCED |
| Present in-flight → direct reject until `completedSerial` quiescence | NOT RUN |
| Present `queue_vblank` fail after GPU schedule → `lorieGpuCopyAck` (early ACK) → direct still rejects | NOT RUN (path exists at `present_execute.c:128-135`) |
| Design-complete R6 | NOT CLAIMED |

`lorieGpuCopyAck()` itself emits no GATEA event. Gate A `EVENT_ACK` is only
the direct Done path. Present early ACK is currently silent.

## 5. Observability — append events, do not grow counters

Existing event numbers `1..28` stay frozen. Append before `MAX`:

```text
LORIE_GATEA_EVENT_REQUEST_ARRIVED     = 29
LORIE_GATEA_EVENT_CALLBACK_EXECUTED   = 30
LORIE_GATEA_EVENT_DIRECT_ADMIT_REJECT = 31
LORIE_GATEA_EVENT_PRESENT_EARLY_ACK   = 32  # frozen; forbidden on D2-OOM
LORIE_GATEA_EVENT_PRESENT_REQUEUE_FAILED = 33
LORIE_GATEA_EVENT_PRESENT_ACK_AFTER_COMPLETED = 34
LORIE_GATEA_EVENT_MAX                 = 35
```

`lorieGateACounterForEvent` maps 29–34 to `LORIE_GATEA_COUNTER_MAX` (no
increment). Ring + `gatea-telemetry` logcat are the evidence. R6 cells are
tiny; `LORIE_GATEA_TRACE_CAPACITY` 512 must not overflow (`overflow==0`).

Default OFF. Emit only when `lorieGateATelemetryPublished()` is true.

Do not include full `lorie.h` from `dix/dispatch.c` (EGL/Android). Declare a
C ABI:

```text
void lorieGateATraceXRequest(int major, int minor, uint32_t clientSeq);
void lorieGateATraceXCallback(uint32_t xop, uint64_t gpuSerial, uint32_t clientSeq);
int  lorieGateAPresentRequeueShouldFail(void); /* one-shot, see §7 */
```

### 5.1 Record packing

| Event | `serial` | `srcId` | `dstId` |
|---|---|---|---|
| REQUEST_ARRIVED | 0 | `(uint64_t)major << 32 \| (uint32_t)minor` | `client->sequence` |
| CALLBACK_EXECUTED | GPU serial or 0 | `xop` kind | `currentClient->sequence` or 0 |
| DIRECT_ADMIT_REJECT | `pvfb->gpuCopySerialCounter` | reason (below) | destination buffer id or 0 |
| PRESENT_EARLY_ACK | `vblank->gpu_copy_serial` | 0 | destination buffer id or 0 |
| PRESENT_REQUEUE_FAILED | GPU serial S | 0 | destination buffer id |
| PRESENT_ACK_AFTER_COMPLETED | GPU serial S | 0 | destination buffer id |

`xop` kinds:

```text
1 COPYAREA     X_CopyArea=62
2 SOLID        X_PolyFillRectangle=70
3 COMPOSITE    Render major, X_RenderComposite=8
4 PRESENT      Present major, X_PresentPixmap=1
5 PREPARE_ACCESS  from loriePrepareAccess (not a core opcode)
```

REQUEST_ARRIVED filter in `dispatch.c`, after `majorOp`/`minorOp` are set and
**before** `requestVector[]`: CopyArea, PolyFillRectangle, GetImage (73),
Render Composite (minor 8), PresentPixmap (minor 1). No other opcodes.

CALLBACK sites (all `LORIE_GATEA_ROLE_X`):

- `lorieExaPrepareCopy` / first scheduled `lorieExaCopy` (`xop=1`)
- `lorieExaPrepareSolid` / first scheduled `lorieExaSolid` (`xop=2`)
- `lorieExaPrepareComposite` (whether direct or legacy) (`xop=3`)
- `present_execute_copy` when `lorieTryScheduleGpuCopy` returns TRUE (`xop=4`)
- `loriePrepareAccess` entry (`xop=5`); `serial=1` if lease-refuse, else 0

### 5.2 DIRECT_ADMIT_REJECT (positive, not “no LEASE”)

Emit only when the pictures are otherwise direct-eligible (proto on, formats
BGRA→RGBX, `lorieCanAccelCompositePictures`, no mask, READY path would be
legal) and admission fails because:

```text
reason 1 = !gateAQueueSemanticallyQuiescent()
reason 2 = gateAPairActive()
```

Do not emit for ordinary software Composite (mask, transform, etc.). Negative
proof “no LEASE_RESERVED in logcat” is not enough (R5 already showed drop).

## 6. Cells

Do **not** overwrite `runtime-37d8393/r6-cross-op/` or any R5 cell.

Three fresh experimental `:3` cells, display 0 only, PROTO=1, TELEMETRY=1,
one X PID per cell, no XFCE, no HDMI.

### 6.1 R6-D1 — direct in flight, second client queued

Fixture `patches/p_r6_d1_queued.c` (new). One session, four second operations
on the same destination after client 1 has flushed a direct Over Composite
that is still waiting in `DoneComposite` from the server’s point of view
(client 2 sends before client 1’s Composite reply):

1. CopyArea
2. PolyFillRectangle
3. GetImage / CPU PrepareAccess
4. PresentPixmap (do not require CompleteNotify before the Composite reply)

PASS iff, for each second op, the X trace (ring or follow logcat, overflow=0)
shows:

```text
SEMANTIC_SUCCESS(composite_N)
  < REQUEST_ARRIVED(second_op)
  < CALLBACK_EXECUTED(second_op)
```

and **no** `CALLBACK_EXECUTED` for that second op appears before that
`SEMANTIC_SUCCESS`. Pixels of the Composite destinations remain exact
(`00804000` family as in bounded R6). No fatal. `NO_X3_RESIDUE`. Stable
untouched.

Client send/reply ns may be logged as commentary only.

### 6.2 R6-D2-INFLIGHT — Present still in queue, then direct

Fixture `patches/p_r6_d2_present.c` subtest A. **Do not** set the OOM env.

PresentPixmap onto a window whose backing pixmap will be the Composite
destination; **do not** wait CompleteNotify; immediately Composite Over on
that destination (same or second connection).

PASS iff one of two transaction-bound branches is proven:

```text
COMMON:
CALLBACK_EXECUTED(PRESENT) generation=G gpu serial=S
  < immediate Composite REQUEST/CALLBACK pair
completion cover = COMPLETED(role=RENDERER, generation=G, serial>=S)
cover is a watermark: its src/dst describe T and are not bound to Present S
LEASE_RESERVED uses the frozen production schema serial=0

BUSY-REJECT:
immediate Composite CALLBACK
  < DIRECT_ADMIT_REJECT reason=1 generation=G dst=D
  < completion cover
  < later Composite REQUEST/CALLBACK pair
  < LEASE(serial=0, pair=P, dst=D)
  < PUBLISH / COMPLETED / SUCCESS for P

QUIESCENT-ADMIT:
completion cover
  < immediate target LEASE(serial=0)
  < PUBLISH / COMPLETED / SUCCESS
  < later Composite REQUEST/CALLBACK pair
  < a second target LEASE / PUBLISH / COMPLETED / SUCCESS
```

No direct LEASE, PUBLISH, or SUCCESS may occur between the Present callback and
its completion cover. In the quiescent branch, the complete immediate lifecycle
must finish before the later Composite request; otherwise a later transaction
could be mistaken for the immediate one. Every REQUEST/CALLBACK is paired by
client sequence, and every direct lifecycle is bound by generation and buffer
pair.

Post-quiescence Composite pixels exact. The Present frame itself is not an
R6 pixel oracle.

### 6.3 R6-D2-OOM — requeue fail must not early-ACK

Same fixture subtest B, **new X PID**, env from §7 armed.

**Withdrawn:** treating `PRESENT_EARLY_ACK` + `lorieGpuCopyAck` as PASS.
That path drops pending refs while the GPU copy may still run.

Chosen (C not in this revision): keep refs, `lorieGpuCopyWait` until
`completedSerial >= S` or fail-stop.

PASS iff:

```text
PRESENT REQUEST(clientSeq=C)
  < PRESENT CALLBACK(C, G, S)
PRESENT CALLBACK < PRESENT_REQUEUE_FAILED(G,S)
PRESENT CALLBACK < COMPLETED(role=RENDERER, G, T>=S)
max(REQUEUE_FAILED, COMPLETED) < PRESENT_ACK_AFTER_COMPLETED(G,S)
ACK_AFTER_COMPLETED < later target Composite REQUEST/CALLBACK pair
later target LEASE(serial=0) < PUBLISH < COMPLETED < SUCCESS
all later lifecycle records: same generation and target buffer pair, publish serial>S
PRESENT_EARLY_ACK → FAIL
```

C (authorized 2026-09-15): exported `lorieGpuCopyWaitForPresentOrFatal`.
Timeout/renderer loss: `GATEA_FATAL_HALT what=x-present-copy-wait`.

## 7. Present requeue one-shot (not R7)

```text
TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL
```

- Default unset / not `"1"` = OFF.
- Exact `"1"` arms **one** fail for the **post-schedule** requeue in
  `present_execute_copy` after `lorieTryScheduleGpuCopy` returned TRUE.
- First consumption disarms for the rest of that X process.
- Must not fail the pre-copy MSC requeue at the top of `present_execute_copy`.
- Must not be read by renderer/Activity (X getenv only, like other X-side
  test knobs).
- Must not be named `TERMUX_X11_GATEA_TEST_FAULT` and must not implement R7
  faults.

R6-D1 and R6-D2-INFLIGHT launchers must prove this env is unset.

## 8. Implementation file bound (when later authorized)

Allowed files, nothing else without a new boundary:

| File | Change |
|---|---|
| `lorie/src/main/cpp/lorie/lorie.h` | append events 29–34; no new counters; tiny C prototypes |
| `lorie/src/main/cpp/lorie/InitOutput.c` | request/callback/reject helpers; env one-shot; `lorieGpuCopyWaitForPresentOrFatal` |
| `lorie/src/main/cpp/xserver/dix/dispatch.c` | one filtered call after opcode decode, before `ProcVector` |
| `lorie/src/main/cpp/xserver/present/present_execute.c` | set pending immediately after schedule; already-pending and post-schedule requeue failures use one completion-before-ACK retirement helper; renderer loss fail-stops |
| `lorie/src/main/cpp/xserver/present/present_vblank.c` | sole `present_gpu_copy_retire_or_fatal`; all raw ACK/pending clear; scrap/destroy retire before idle/drop |
| `lorie/src/main/cpp/xserver/present/present_priv.h` | retirement helper + wait-or-fatal + requeue/ACK traces; do not export raw `lorieGpuCopyWait` |
| `lorie/src/main/cpp/lorie/renderer.cpp` | **telemetry only** (2026-09-15 D2): `gateATraceLegacyCompleted` after existing legacy `PublishCompleted`; fill `lastSrcId`/`lastDstId` on legacy consume. **No** fence-order / `EGL_FOREVER` / ABI change. |

New fixtures and harness live under `patches/` and
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/`. Do not edit
`patches/p_r6_cross_op.c`.

Not in scope: `renderer.cpp` **fence order**, `cmdentrypoint.cpp` pump, generic
`lorie_mutex_lock`, queue/protocol/direct ABI, predicate, D0a/D0b, R7, R8.

Affected requalification after a future authorized implementation:

- PROTO unset and PROTO=0 must still emit **zero** new events.
- R3/R4/R5 are not rerun unless the grant says so.
- Design-complete R6 is three cells above, not a rewrite of bounded `r6-cross-op`.
- R7 stays source-blocked even if all three cells PASS.

## 9. PASS / FAIL / stop

Design-complete R6 PASS only if all three cells PASS.

Any of these is FAIL and stops the session:

```text
CALLBACK_EXECUTED(second_op) before SEMANTIC_SUCCESS of the in-flight direct op (D1)
LEASE_RESERVED / PUBLISH of a direct op whose dst overlaps Present serial S
  before COMPLETED_SERIAL covers S (D2)
missing REQUEST_ARRIVED or CALLBACK for a fixture op when TELEMETRY=1
D2 has neither a bound busy-reject branch nor a bound quiescent-admit branch
quiescent immediate lifecycle crosses the later Composite request boundary
busy branch lacks a paired later Composite and target direct lifecycle
OOM later SUCCESS/lifecycle occurs before its paired later callback
PRESENT_EARLY_ACK present on the OOM cell (early ownership return)
gateATelemetry.overflow != 0
missing COMPLETED cover (renderer, same generation, serial>=S)
pixel mismatch on any Composite that this design marks as an oracle
fatal / firstFailed / X death / watchdog
env hook armed on a non-OOM cell
X client dispatch from inside a Gate A terminal wait
artifact / display / Stable / HDMI mismatch
```

Script exit 2 due to follow-logcat drop is **not** automatic PASS (R5 special
case does not apply). R6 N is small; require the events in the captured
follow. If follow is short, dump the 512-ring from shared mapping; do not
silent-retry.

## 10. Decisions (frozen by this review)

1. No renderer delay hook.
2. No X-client pump during terminal wait.
3. No new shared-memory counters; append-only events 29–32.
4. COPY/SOLID-first in-flight reverse admission is N/A; Present is the reverse
   path.
5. Present-OOM uses a dedicated one-shot env, not `TERMUX_X11_GATEA_TEST_FAULT`.
6. Bounded `r6-cross-op/` stays historical CLIENT_OK.
7. Implementation / CI / install / runtime of this design needs a **new**
   explicit user grant. The R5-static line “R6–R8 conditionally authorized
   after R5 PASS” was consumed by the bounded client cell and does not cover
   these source edits.

## 11. Authorization (2026-09-15)

User grant: implement this design **and keep it revertible**.

```text
R6 DESIGN-COMPLETE IMPLEMENTATION: AUTHORIZED
REGRESSION TESTS / FIXTURES: AUTHORIZED (host compile only this session)
ARM64 BUILD / FORK PUSH / CI / ARTIFACT: PASS 2026-09-15 (run 34926730189)
INSTALL / ADB / DEVICE / RUNTIME: NOT AUTHORIZED
R7 / R8 / PRODUCTION / PR / ORIGIN / STABLE / HDMI: NOT AUTHORIZED
```

Rollback: new linked worktree + branch from exact `37d8393`. Installed
`src/f8-ahb-gatea-r5-fix` and the experimental APK stay on that SHA. Static
implementation record:
`GATE-A-P2-R6-STATIC-IMPLEMENTATION-20260915.md`.

Any need to change wire/shared/queue ABI, timeout duration, ownership/fence
semantics, predicate, fallback, or to pump X clients during wait is a new
architecture boundary and must stop.

## 12. Fork push + CI (2026-09-15)

User grant: fork push + CI. No PR, no origin, no force, no install.

```text
FORK: waydefu/termux-x11 qualification/gatea-r6-20260915
HEAD: 936955397619091b48c8e717f28b2cd187d79065
CI: 34926730189 workflow_dispatch first attempt PASS
ARTIFACT: QUALIFIED (1.03.01-9369553-15.09.26, SHA256 02baccbf…af7f)
INSTALL: NOT DONE
```

Provenance: `../p2-r6-ci-34926730189/P2-R6-CI-ARTIFACT-PROVENANCE-20260915.md`.
Later install of that APK is recorded in
`../p2-r3-xpump-runtime/runtime-9369553/`.

## 13. D2 COMPLETED telemetry (2026-09-15)

```text
HEAD: 54ff35bd2e47a250c88b5c19391c22b0f6af5700
FILE: lorie/src/main/cpp/lorie/renderer.cpp only
STATIC: verify_r6_design_impl.py PASS
FORK PUSH / CI / INSTALL: not in this design-doc revision
DEVICE: still 9369553
```

`GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md`.

## 14. HOLD 2026-09-15 — do not push `54ff35b`

Review accepted. Telemetry-only is insufficient for a new D2 cell.

```text
FORK PUSH / CI / INSTALL / D2 DEVICE: NOT AUTHORIZED
PRESENT WAIT C: DESIGN CHOSEN, NOT CODED
JUDGE / BIND: UPDATED (host tests PASS)
```

Authority: `GATE-A-P2-R6-D2-HOLD-20260915.md`.

## 15. Present retirement writer lane (2026-09-15 22:00) — uncommitted

Errata on §14: wait-or-fatal C and the concentrated retirement helper **are
coded** on worktree `src/f8-ahb-gatea-r6-retire` (base `95e6f96`), not on the
installed APK. Host gates PASS. Not committed. Not R6 PASS.

See:

- `GATE-A-P2-R6-PRESENT-RETIREMENT-IMPLEMENTATION-20260915.md`
- `GATE-A-P2-R6-D2-INFLIGHT-ORACLE-ADJUDICATION-20260915.md`
- `/root/projects/GPU加速/PLANNER-BRIEF-20260915.md`

Do not treat this section as HANDOFF/TEST-MATRIX/AGENTS authority. Parent
updates those after independent review. D2-OOM, timeout/loss, and teardown
runtime remain unproven. R7 stays source-blocked.
