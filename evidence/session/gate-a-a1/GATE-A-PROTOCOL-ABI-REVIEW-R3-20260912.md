# GATE A PROTOCOL ABI REVIEW R3 — 2026-09-12

Scope: close the six R2 gaps at design level against `qualification/d0a-narrow-20260912` /
`a6cc795`. DESIGN ONLY. No code/build/CI/APK/ADB/device/Stable/HDMI operation.
Decisions frozen here: READY per-buffer; first use checked-unlock → REGISTER →
READY → publish; imported excluded; queue-entry ABI unchanged; completedSerial
meaning unchanged; no native fence FD; no transparent replay; no D0b/H.

## 1. ABI — PASS

### 1.1 Frozen shared-state sideband

Appended at the end of `lorie_shared_server_state` (sized dynamically by
`sizeof(*state)` at `InitOutput.c:430-435`, so one-build offsets are consistent;
`protocolVersion` guards anything else):

```c
struct LorieGateAProtocol {      // align 8, size 40
    uint32_t protocolVersion;    // +0
    uint32_t generationFatal;    // +4
    uint64_t sessionNonce;       // +8
    uint64_t generation;         // +16
    uint64_t firstFailedSerial;  // +24
    uint32_t firstFailureCode;   // +32
    uint32_t fatalReason;        // +36
};
```

Per-field contract:

| Field | Width/align | Atomicity + lock-free | Writer → reader / edge | Init | Wrap |
|---|---|---|---|---|---|
| protocolVersion | u32/4 | `__atomic` always-lock-free; runtime `__atomic_is_lock_free` gate before ACTIVE | X once before sharing → renderer plain load after socket-recv edge | 1 | never changes |
| generationFatal | u32/4 | same; CAS 0→1 release | either side CAS → both sides acquire-check | 0 | sticky, never clears |
| sessionNonce | u64/8 | same; single writer before sharing | X `getrandom` → renderer echo/bind | nonzero random | new nonce per X restart |
| generation | u64/8 | same; single writer (X) | X → renderer, echoed in every frame | 1 | wrap → FATAL |
| firstFailedSerial | u64/8 | same; renderer once-CAS 0→S release | renderer → X acquire | 0 | sticky; serials start at 1 |
| firstFailureCode | u32/4 | same; plain write **before** the CAS above | ordered by the CAS release | 0 | valid iff failed != 0 |
| fatalReason | u32/4 | same; plain write **before** fatal CAS | ordered by the CAS release | 0 | valid iff fatal != 0 |

Upgraded existing fields (same layout, new access rules):

| Field | Writer → reader / edge | Init / wrap |
|---|---|---|
| writeIndex u32 | X release-store → renderer acquire-load | 0; unsigned `writeIndex - readIndex` delta stays wrap-safe |
| readIndex u32 | renderer release-store → X acquire-load | 0; means slot copied/dequeued only, never completion |
| completedSerial u64 | renderer release-store after fence/quiescence → X acquire-load | 0; serials start at 1 (`++counter` at publish); u64 wrap → FATAL |

P0 entry criteria: `_Static_assert` on every offset/size/alignment and unchanged
`LorieGpuCopyEntry` layout; compile-time `__atomic_always_lock_free(4/8)`; runtime
`__atomic_is_lock_free` on all shared 32/64-bit fields (false disables Gate A
before REGISTER); zero `volatile`-only publication/consumption/completion paths
for Gate A serials.

### 1.2 Lossless SUCCESS derivation under strict in-order execution

Strict order holds and is enforceable:

- (i) One publisher: all queue publishers (Composite/Copy/Solid/Present) run on
  the single X server thread; serials are dense from 1 in publish order.
- (ii) One consumer: `Renderer::threadLoop` drains ring order with one fence per
  consumed prefix; fence satisfaction proves the whole prefix quiesced.
- (iii) Renderer checks fatal acquire **before each entry** and halts all
  consumption at the first Gate A failure.
- (iv) A skipped/unready Gate A entry becomes `FAILED_QUIESCED` + halt — never
  silent consume (required renderer change; legacy non-Gate-A skips keep legacy
  behavior and live in a separate failure domain that cannot affect Gate A
  derivation because ring order is preserved).
- (v) Renderer distinguishes Gate A serials by READY-registry membership
  (`srcBufferId` ∈ Gate A ready set), so **no queue-entry ABI change** is needed.

Derivation for Gate A serial S (all loads acquire):

```text
fatal observed (before terminal for S)                    → FATAL
firstFailed != 0 AND S > firstFailed                      → never executed; poisoned
completed >= S AND firstFailed == S                       → FAILED_QUIESCED
completed >= S AND (firstFailed == 0 OR S < firstFailed)  → SUCCESS
```

Observation-order rule: X checks fatal first each waiter iteration; a SUCCESS
fully derived before fatal is observed stays credible, anything terminal-observed
after is poisoned. No per-entry result ring is needed; nothing is overwritten
because `firstFailedSerial` is once-CAS and `completedSerial` is monotonic.

## 2. DESTINATION OWNERSHIP — PASS

Destination during GPU work is owned **exclusively by the renderer** (draw target
of the same serial's fence). X must not CPU-access it, exactly like the source.

- Same completion boundary: one serial's fence covers source sample **and**
  destination draw, so source safe-to-relock and destination safe-to-access are
  the **same** terminal RESULT. One RESULT covers both; no second channel.
- X may repair/relock/reuse the destination only after terminal SUCCESS for that
  serial, while still holding pending ownership (before ack). Current
  wait→repair→release shape (`InitOutput.c:2353-2375`) is kept but gated on SUCCESS.
- Timeout / FAILED_QUIESCED / FATAL: no X-byte repair, no relock, no reuse.
  FAILED_QUIESCED retires refs then terminates the generation (no replay).
- Non-root destinations need READY + retirement metadata identical to sources;
  root needs an equivalent generation-bound `ROOT_READY` state (same struct,
  root bufferId).
- Current `lorieEnsureGpuSampleable(dst)` can leave the destination CPU-locked, so
  P4's checked-unlock rule covers **both** source and destination before publish.
- Resize (`lorieRRScreenSetSize` destroys the root pixmap without drain,
  `InitOutput.c:1134+`): with any unterminal Gate A serial, resize must drain
  first; drain failure → FATAL.
- Cross-op interference is closed by admission rule: a buffer is admissible only
  if its `lastSubmittedSerial` is terminal (completed ≥ lastSubmitted with no
  covering failure). This also covers the Present OOM early-ack path
  (`present_execute.c:133-135`), which may release a still-in-flight copy: a
  later Gate A admission on that buffer is rejected until terminal state proves
  quiescence.

## 3. FATAL ATOMIC EDGE — PASS

Single atomic edge: release-CAS of the sticky flag; first detail wins.

- `firstFailedSerial`: renderer once-CAS `0→S` (release) after writing
  `firstFailureCode`; unexpected CAS failure = protocol corruption → FATAL.
- `generationFatal`: either side CAS `0→1` (release) after writing reason.
- Renderer checks fatal acquire before **each** entry and after fence wait before
  publishing `completedSerial`; on fatal it abandons publication and exits
  consumption.
- X checks fatal acquire before admission, inside every waiter loop iteration,
  and before every ownership release.
- Credible sets: serials with SUCCESS fully derived before fatal observation stay
  credible; every serial `>= firstFailedSerial` (when set) and every serial whose
  terminal state is first observed after fatal is poisoned.
- `completedSerial` vs fatal race is ordered by construction: renderer-side
  failure detail → CAS → completed-store happen on one thread in that order; X
  applies the observation-order rule above. Multiple simultaneous failures
  collapse to the first CAS winner; losers observe the sticky flag and stop.
- Renderer death/HUP, context loss, fence create/wait failure, result timeout,
  malformed generation: all FATAL, never SUCCESS or FAILED_QUIESCED.

## 4. WAITER DEADLOCK — PASS

Wait-for graph (all waits bounded + fatal-wakeable; no cycle):

| Waiter | Waits on | Wake | Fatal wake | Terminal behavior |
|---|---|---|---|---|
| DoneComposite (`lorieGpuCopyWait`, `InitOutput.c:1723-1736`) | completedSerial/RESULT poll, `usleep(200)`, 2000 ms budget, alive checks; holds **no lock** | RESULT terminal | fatal acquire-check each iteration → immediate FALSE | SUCCESS→release; else fail-stop |
| READY / UNREGISTER_ACK / GENERATION_CLOSED (new) | dedicated process-local condvar, bounded budget | input-thread registry update + signal | fatal signal + budget expiry | proceed / FATAL; never hold `state->lock` while waiting |
| Renderer EGL fence waits | own GPU only | fence satisfied | **must become bounded**: finite wait for Gate A, timeout → FATAL (replaces `EGL_FOREVER` in the Gate A path) | publish terminal or FATAL-exit |
| Renderer `stateCond` idle wait | X signals; `pthread_cond_wait` releases `stateLock` atomically | X signal | n/a (holds no X-needed resource while waiting) | process work |
| `setSharedState`/`setWindow` cross-thread rendezvous | render-loop progress | loop iteration | **fatal path bypasses** (terminate, never blocking rendezvous) | — |
| Present vblank requeue | MSC poll + stall detection (`present_execute.c:92-98`) | re-execute or scrap; never blocks | stall → scrap, never false-present | — |
| Control socket | event-driven looper, `FIONREAD` drain; no blocking wait | fd events | HUP → fatal path | — |
| CloseScreen drain (new) | terminal RESULTs via poll loop | all terminal | fatal → fatal teardown | GENERATION_CLOSED or terminate |

Cycle-freedom: X waiters never hold `state->lock` and never block on the X
server thread itself (wakeup comes from the input thread directly, never via
WorkProc round-trip — required, closes R2 waiter-delivery gap). Renderer waits
only on its GPU (bounded) and on X signals while holding nothing X needs.
`setSharedState` blocking rendezvous is excluded from every fatal path. No
`X→renderer→X`, `control→GL→control` cycle exists. Pre-existing
`lorie_mutex_lock` infinite-while-connected behavior is never on a Gate A
correctness path: all Gate A waits are lock-free atomic polls or dedicated
condvars.

## 5. ACTIVITY FATAL CONTAINMENT — PASS

Exact `activity.cpp::xcallback` rules for an active Gate A generation (legacy
clipboard/input frames byte-identical and untouched; Gate A frames identified by
header magic):

- Short/partial control read: currently ignored → stream desync. New rule: any
  short read while a Gate A generation is ACTIVE → poison + terminate (no
  resumption on a desynchronized stream).
- Unknown frame type with Gate A magic → FATAL. Unknown legacy types keep legacy
  ignore behavior.
- Generation/nonce mismatch on any Gate A frame → FATAL (never accept, never
  “resync”).
- REGISTER receive failure → renderer emits REGISTER_FAILED; X input thread marks
  the registry entry failed and wakes the waiter (no relock, D0a only after
  explicit REGISTER_FAILED + cleanup ACK).
- Socket HUP / renderer disappearance with active Gate A generation → poison
  generation atomically, close control endpoint, terminate the Experimental
  activity/renderer process. The current HUP path's blocking `setSharedState(NULL)`
  (`activity.cpp:156-160`, blocks on `stateChangeFinishCond` until the renderer
  loop iterates, `renderer.cpp:562-572`) **must be bypassed** here: a renderer
  stuck in a fence wait would hang activity teardown instead of containing it.
- Renderer-thread death inside a live process is contained by bounded waits +
  fatal timeouts → process exit. No thread-recovery, no shared-mutex
  reinitialization on the Gate A path (pre-existing L1 recovery is never used to
  continue a Gate A generation).
- Fatal containment bottoms out at process termination on both sides; EGL-context
  and driver cleanup follow process teardown. New generation only after old X PID
  and renderer process/context liveness are gone.

## 6. RETIREMENT METADATA — PASS

X-side per registered buffer (minimal; nothing more is needed for correctness):

```text
sessionNonce, generation, bufferId
state: UNREGISTERED / REGISTERING / READY / RETIRING / DEAD
descriptorFingerprint (w,h,stride,format)
lastSubmittedSerial (0 = none; updated on every source AND destination use)
pendingCount
ownerRef (X wrapper reference)
cpuLocked (protocol mirror of priv->locked)
unregisterAcked
```

Renderer-side per import: `{id, nonce, generation, ahbRef, eglClientBuffer,
image, texture, ready, tombstone}`.

Dropped as unnecessary: per-buffer `lastCompletedSerial`/`lastFailedSerial`
(global watermarks + `lastSubmittedSerial` derive everything); X-side renderer-ref
mirror (ACK covers it); `unregisterSent` (implied by RETIRING).

DestroyPixmap:

```text
ACTIVE → RETIRING → block new submissions → wait lastSubmittedSerial terminal
(bounded, fatal-checked, no state->lock held) → pendingCount == 0
→ UNREGISTER(id, generation, lastSubmittedSerial)
→ renderer GL thread: delete texture → destroy EGLImage → release AHB ref
→ tombstone → UNREGISTER_ACK → X releases ownerRef → free driverPriv
```

Duplicate/idempotency rules: matching duplicate REGISTER re-emits current state;
same ID with different fingerprint/generation → FATAL; duplicate UNREGISTER after
ACK → deterministic tombstone ACK without resurrection; ACK timeout or mismatch →
FATAL, `driverPriv`/AHB/ID never reused. Fatal generation never runs normal
retirement. Root follows the same registry with `ROOT_READY`; resize obeys the
drain-or-FATAL rule from §2.

## CONTROL WIRE ABI (frozen)

Fixed 40-byte little-endian header, no raw padded-struct writes:

```text
+0  uint32 magic          +4  uint16 protocolVersion
+6  uint16 messageType     +8  uint32 messageLength
+12 uint32 reserved (=0)   +16 uint64 sessionNonce
+24 uint64 generation     +32 uint64 bufferId (0 if n/a)
```

Fixed bodies: REGISTER `{w,h,stride,format}` + AHB handle via existing SCM_RIGHTS
(one writer-locked logical transaction with the frame); READY `{fingerprint}`;
REGISTER_FAILED `{code}`; UNREGISTER `{lastSubmittedSerial}`; UNREGISTER_ACK `{}`;
GENERATION_CLOSE `{lastPublishedSerial}`; GENERATION_CLOSED `{}`;
FATAL_NOTIFY `{reason}` (hint only — atomics carry correctness). RESULT travels
exclusively via the shared sideband, never the socket.

## SYMBOL MAP (verified decisive ranges)

```text
InitOutput.c PrepareComposite/Composite/DoneComposite  2145-2208 / 2270-2345 / 2347-2389
InitOutput.c PrepareAccess/FinishAccess                 2497-2529
InitOutput.c DestroyPixmap / CloseScreen / resize       2470-2479 / 1080-1097 / 1134-1187
InitOutput.c schedule/publish/wait/ack                  1581-1702 / 1704-1736
InitOutput.c promotion lock left held                   200-235 (225-230)
InitOutput.c imported marking vs admission               2567 vs 2101-2121
renderer.cpp consume/fence/publish                       745-768 / 770-926 / 931-968
renderer.cpp redraw fence + next-buffer fence            1115-1178
renderer.cpp threadLoop / setSharedState rendezvous      1214-1279 / 562-572
renderer.cpp notifyGpuCopyDone (wake hint)               136-141
buffer.c attach/bind/import                              635-674
buffer.c unlock contract / free ordering                 459-484 / 373-401
cmdentrypoint.cpp register/unregister framing            468-493
cmdentrypoint.cpp GPU_COPY_DONE → WorkProc               406-413
activity.cpp xcallback ADD/HUP paths                     147-240 (151-163, 211-227)
lorie.h shared struct + mutex recovery                   193-259 / 52-92
present_execute.c poll/scrap/OOM-ack                     66-148 (92-135)
present_scmd.c recheck / present_vblank.c scrap-ack      255-268 / 189-220
```

## REMAINING BLOCKERS

```text
NONE at design level.
```

All six R2 gaps close with the mechanisms above. What remains is implementation
risk, gated by the required static / fault-injection / runtime gates — not
further protocol design.

## REQUIRED OUTPUT FORMAT

```text
# GATE A PROTOCOL ABI REVIEW R3

ABI:
PASS

DESTINATION OWNERSHIP:
PASS

FATAL ATOMIC EDGE:
PASS

WAITER DEADLOCK:
PASS

ACTIVITY FATAL CONTAINMENT:
PASS

RETIREMENT METADATA:
PASS

REMAINING BLOCKERS:
NONE at design level; implementation risk remains behind static/fault/runtime gates

P0 IMPLEMENTATION:
AUTHORIZED

PRODUCTION GATE A:
BLOCKED

NEXT:
ONE ACTION ONLY — write the P0 exact-ABI implementation diff (frozen structs,
asserts, atomic accessors, input-thread registry + dedicated condvars, bounded
Gate A fence waits, fatal bypass of blocking rendezvous) for static review;
no build/runtime until that review passes
```
