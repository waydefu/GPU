# Gate A protocol ABI review R2 — 2026-09-12

## RESULT ABI

The watermark + sticky-first-failure model is logically lossless **if and only if**
all three declared conditions remain hard invariants:

```text
one X queue producer
one renderer queue consumer / one EGL context
strict serial-order dequeue and fence publication
stop consumption at first failure
```

Current renderer topology is compatible: `Renderer::threadLoop` is one consumer;
`applyPendingGpuCopiesLocked` copies entries and increments `readIndex` in ring
order; one fence is inserted after all commands in the processed prefix. The
prototype must not add parallel dequeue or out-of-order fence publication.

Required derivation is accepted:

```text
fatal => no success
firstFailed != 0 && S >= firstFailed => no success
otherwise completed >= S => SUCCESS
```

`completedSerial` remains highest contiguous **GPU-quiesced** serial; it is not
semantic success. On FAILED_QUIESCED it may advance exactly to the failed serial;
no later entry executes. On FATAL it does not advance through the uncertain
serial.

However, P0 physical fields are not frozen yet; generic
`result_serial/result_state` must remain deleted.

## ATOMIC ABI

The plan states memory orders but does not yet fix widths, offsets, alignment, or
a lock-free gate. P0 must freeze at least this equivalent physical ABI:

```text
existing gpuCopyQueue header (relative offsets):
  +0   uint32 writeIndex       align 4
  +4   uint32 readIndex        align 4
  +8   uint64 completedSerial  align 8
  +16  entries[]               (entry layout unchanged)

new sideband, align 8, size 40:
  +0   uint32 protocolVersion
  +4   uint32 generationFatal
  +8   uint64 sessionNonce
  +16  uint64 generation
  +24  uint64 firstFailedSerial
  +32  uint32 firstFailureCode
  +36  uint32 reserved (=0)
```

Required gates in both binaries:

- `sizeof(uint32_t)==4`, `sizeof(uint64_t)==8`;
- `_Static_assert`/`static_assert` for every offset, alignment, sideband size, and
  unchanged `LorieGpuCopyEntry` size/offsets;
- compile assertion `__atomic_always_lock_free(4, 0)` and
  `__atomic_always_lock_free(8, 0)`;
- before ACTIVE, both processes run `__atomic_is_lock_free` against every actual
  shared 32/64-bit field; false disables Gate A before REGISTER (safe D0a miss);
- all shared scalar accesses use `__atomic_*`; no process-shared mutex supplies
  publication ordering.

Edges:

```text
X entry writes → release writeIndex; renderer acquire writeIndex
renderer local entry copy → release readIndex; X acquire readIndex
renderer write failureCode → CAS firstFailedSerial 0→S with release
GPU quiesced → renderer release completedSerial; X acquire completedSerial
fatal setter (X or renderer) CAS generationFatal 0→1 release;
  X checks acquire before admission/release, renderer checks acquire before each entry
```

Single renderer writer makes “write code then CAS serial” once-only; unexpected
CAS failure is protocol corruption and sets fatal. Serial starts at 1; zero is
reserved; uint64 wrap is FATAL.

Because the submitted plan has not yet incorporated this concrete layout and
bidirectional fatal edge, atomic ABI status is **OPEN**.

## GENERATION IDENTITY

Required identity:

```text
(sessionNonce: uint64, generation: uint64)
```

- X obtains `sessionNonce` from `getrandom`; failure disables Gate A before any
  registration—no weak timestamp/PID fallback.
- Generation starts at 1 and increments for each clean shared mapping/context
  lifetime; wrap is FATAL.
- Renderer never invents identity; it only binds/echoes the X tuple.
- X restart generates a new nonce, so a reset counter cannot accept stale events.
- The tuple is in the shared sideband and every Gate A control frame.

The revised plan asks for a scheme but does not choose one; this exact choice must
be inserted before P0 implementation.

## CLEAN CLOSE

The proposed sequence is correct after two refinements:

1. stop admission and snapshot `lastPublishedSerial`;
2. wait terminal state through it;
3. retire and ACK every source **and destination** READY object;
4. send `GENERATION_CLOSE(nonce,generation,lastPublishedSerial)`;
5. renderer verifies queue empty, no in-flight work, GL registry empty, shared
   state detached;
6. receive `GENERATION_CLOSED`;
7. only then destroy root and unmap shared state.

A clean close is the only path that can free/reuse objects in-process.

## FATAL CLOSE

Intent is correct but containment is not yet executable from the plan. In the
current activity HUP path, `activity.cpp::xcallback` calls blocking
`Renderer::setSharedState(NULL)`; if the renderer is stuck in `EGL_FOREVER`, this
can deadlock instead of terminating the renderer generation.

R3 must specify:

- either process may atomically poison generation;
- X closes its control endpoint and exits without normal Gate A
  Done/Destroy/Close cleanup;
- activity HUP/protocol-fatal path for an active Gate A generation bypasses
  blocking clean `setSharedState(NULL)`/`removeAllBuffers` and terminates the
  Experimental activity/renderer process, forcing EGL-context/driver cleanup;
- renderer death/HUP causes X to exit, not reinitialize the shared mutex;
- no new generation until old X PID and renderer process/context are confirmed
  gone.

Without that exact activity-side fatal branch, “OS reclamation” is an intention,
not a complete containment path.

## REGISTER / READY

Per-buffer READY remains correct. READY must be keyed by
`(sessionNonce,generation,bufferId,descriptorFingerprint)` and invalidated by
UNREGISTER, clean generation close, or context loss/FATAL.

Two unresolved points remain:

1. **Destination readiness:** Gate A draws into a destination AHB. Current
   `lorieEnsureGpuSampleable(dst)` can leave it CPU-locked, while renderer binds it
   as the destination FBO. P2/P3 currently require READY only ambiguously for
   “the buffer”. Both direct source and non-root destination must be READY; root
   requires an equivalent generation-bound `ROOT_READY` state.
2. **Waiter delivery:** `PrepareComposite`/`DestroyPixmap` run on the X server
   thread and may wait for READY/ACK. If `cmdentrypoint.cpp::handleLorieEvents`
   only queues a WorkProc back to that same thread, the waiter deadlocks. Gate A
   READY/FAILED/ACK/FATAL frames must update a thread-safe protocol registry
   directly on the input thread and signal a dedicated local condition/event;
   ordinary X-object mutations remain on WorkProc.

Control wire ABI also needs freezing. Required minimal fixed little-endian header
(no raw padded struct writes):

```text
+0  uint32 magic
+4  uint16 protocolVersion
+6  uint16 messageType
+8  uint32 messageLength
+12 uint32 reserved (=0)
+16 uint64 sessionNonce
+24 uint64 generation
+32 uint64 bufferId (0 when not applicable)
size 40 bytes
```

Gate A frames only use checked full read/write. REGISTER header+descriptor+AHB
handle is one writer-locked logical transaction. Do not retrofit clipboard/input
framing.

## FIRST-USE ORDER

The revised source order is correct for the source:

```text
checked CPU unlock → REGISTER → READY → publish
```

It is incomplete for the destination. Before the first GPU FBO write, any active
destination CPU mapping must also end with checked unlock; destination/root READY
must be current. REGISTER/READY may persist per-buffer, but every later CPU→GPU
transition independently unlocks each CPU-owned resource.

A READY timeout remains FATAL. Only explicit REGISTER_FAILED followed by renderer
cleanup ACK permits relock and D0a.

## ADMISSION / FALLBACK

The normal-miss versus fatal/uncertain distinction is accepted. Add these hard
conditions before publication:

```text
source READY and CPU-unlocked
non-root destination READY and CPU-unlocked, or root ROOT_READY and CPU-unlocked
both objects match active nonce/generation
both retirement states are false
per-buffer pending/lastSubmittedSerial metadata updated atomically with publication
```

Flag OFF, predicate miss, imported source, and never-attempted registration while
CPU ownership is intact may use D0a. Sticky failure, fatal, timeout, mismatch,
REGISTERING uncertainty, or cleanup-ACK loss never may.

## CPU→GPU HANDOFF

Source handling is correct: successful blocking AHB unlock, clear CPU pointer only
on return 0, then release-publish. Unlock failure is fatal and cannot fallback.

**Remaining correctness gap:** the same ownership rule must cover the destination
AHB. GPU draw is a write, so an active destination CPU lock cannot coexist merely
because a process-shared mutex excludes active CPU instructions. P4 must define:

```text
finish source CPU access + checked unlock
finish destination CPU access + checked unlock (when locked)
verify source/destination READY and generation
acquire per-entry ownership for both
publish
```

After terminal success, source and destination both relock lazily on actual CPU
access. This is required even though the optimization target is source staging.

## UNREGISTER

The revised RETIRING/ACK sequence is sound after extending metadata to every
renderer-visible source/destination/root resource:

```text
state, nonce/generation, bufferId, descriptor fingerprint,
lastSubmittedSerial, pendingCount, owner ref
```

`lastSubmittedSerial` updates for every source and destination use. RETIRING blocks
publication before drain begins. DestroyPixmap waits via the input-thread protocol
registry—not an X-thread WorkProc. ACK is valid only after renderer GL-thread
texture deletion, EGLImage destruction, AHB release, and registry tombstone.

Duplicate rules must be fixed:

- matching duplicate REGISTER re-emits current READY/FAILED state;
- same ID with different identity/descriptor is FATAL;
- duplicate UNREGISTER after ACK returns deterministic tombstone ACK without
  resurrecting the object;
- ACK timeout is FATAL; `driverPriv`, owner AHB, and ID are not reused.

## SYMBOL MAP

```text
activity.cpp::xcallback
  → receive REGISTER/control frames; detect HUP; enqueue renderer add;
    on Gate A fatal HUP use nonblocking process-level containment, not clean wait

renderer.cpp::Renderer::addBuffer / threadLoop
  → GL-thread import validation; populate READY registry; send READY or
    REGISTER_FAILED; process UNREGISTER and clean generation close

cmdentrypoint.cpp::handleLorieEvents
  → receive READY/REGISTER_FAILED/UNREGISTER_ACK/GENERATION_CLOSED/FATAL;
    update thread-safe protocol registry directly and wake X waiter

cmdentrypoint.cpp::lorieRegisterBuffer / lorieUnregisterBuffer
  → checked, framed, generation-bound control transactions; no unchecked legacy
    send for Gate A objects

buffer.c::LorieBuffer_attachToGL
  → split/return checked direct-import outcome; no READY on null client buffer,
    EGLImage, texture, descriptor mismatch, or GL error

buffer.c::LorieBuffer_bindTexture
  → direct READY BGRA binds persistent EGLImage texture only; never CPU-lock/upload

renderer.cpp::Renderer::findBufferWithRetry
  → no timing heuristic for Gate A; require exact current-generation READY registry

InitOutput.c::lorieExaPrepareComposite / lorieExaComposite
  → both-resource admission, checked unlock, refs/pending, atomic publication

InitOutput.c::lorieExaDoneComposite
  → acquire terminal state; release both resources only on SUCCESS;
    FAILED_QUIESCED/FATAL close session, no replay

InitOutput.c::loriePrepareAccess / lorieFinishAccess
  → lazy relock only after terminal ownership; AHB unlock completes before exposing
    any guard that lets renderer proceed

InitOutput.c::lorieExaDestroyPixmap / lorieCloseScreen
  → RETIRING/drain/ACK and clean close; fatal path never uses normal cleanup
```

## REMAINING BLOCKERS

1. P0 exact shared and wire ABI has not been inserted into the plan.
2. P4 transfers source ownership only; destination/root CPU→GPU ownership is
   missing.
3. X-originated fatal publication and renderer acquire-before-next-entry edge is
   absent.
4. READY/ACK waiter delivery can deadlock if routed through an X-thread WorkProc.
5. Activity-side fatal HUP/context-wait containment is not defined; current clean
   callback can block on a hung renderer.
6. Source/destination/root per-buffer retirement and last-serial tracking is not
   explicit.

These are correctness gaps inside P0–P4/FATAL/UNREGISTER, so the authorization
standard is not met.

## P0 IMPLEMENTATION

```text
NOT AUTHORIZED
```

## NEXT

One action only: issue an R3 plan incorporating the exact shared/wire ABI above,
bidirectional fatal atomics, source+destination ownership/READY, direct
input-thread READY/ACK wakeup, and activity-side fatal process containment; then
resubmit P0 for final ABI approval. No code/build/runtime.
