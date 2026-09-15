# Production Gate A minimal generation-bound protocol design — 2026-09-12

## VERDICT

```text
PROTOTYPE AUTHORIZED
```

This authorizes only a later Experimental, default-off, server-owned/non-imported
prototype. It does **not** pass Production Gate A and does not authorize code in
this architecture-only round.

Why it remains narrow enough:

- A1 already proved the F8 BGRA byte/import/sampler contract 3/3 exact.
- Existing queue entry fields (`serial`, source/destination IDs, rects, op) are
  sufficient; the `LorieGpuCopyEntry` layout need not change.
- `completedSerial` keeps its original GPU-quiescence meaning.
- No native fence FD crosses processes: checked blocking AHB unlock handles
  CPU→GPU; the existing renderer-side EGL fence + CPU wait handles GPU→X.
- Imported AHB, external producer fences, transparent replay, and D0b remain out.
- The required new surface is bounded to a versioned shared-state result sideband
  plus low-rate READY/UNREGISTER lifecycle messages on the existing socket.

Production Gate A remains `BLOCKED` until such a prototype passes static,
fault-injection, exact-pixel, lifecycle, and teardown gates.

## MINIMAL PROTOCOL

### 1. Generation

One nonzero 64-bit `generation` identifies exactly one:

```text
X process connection
+ shared-state mapping
+ renderer EGL context lifetime
```

It is immutable after the shared state is published. A reconnect or EGL context
loss creates a new generation; no READY, RESULT, buffer ID, or ACK from an old
generation is accepted. Surface-only recreation under the same healthy EGL
context does not change generation.

The shared state gains a protocol version and generation. Buffer IDs need only be
unique inside the generation; all control messages carry `(version, generation)`.

### 2. Per-buffer registration and READY

Logical messages on the existing AF_UNIX control socket:

```text
REGISTER(version, generation, buffer_id, immutable_descriptor, AHB handle)
READY(version, generation, buffer_id, descriptor_fingerprint)
REGISTER_FAILED(version, generation, buffer_id, reason)
UNREGISTER(version, generation, buffer_id)
UNREGISTER_ACK(version, generation, buffer_id)
GENERATION_FATAL(version, generation, reason)
```

Rules:

1. X only offers server-owned buffers: `priv->imported == false` is mandatory.
2. Before first REGISTER, X ends CPU access with checked
   `AHardwareBuffer_unlock(buffer, NULL) == 0`.
3. Renderer receives its own AHB reference, validates descriptor identity, and on
   its GL thread creates and validates EGLClientBuffer → EGLImage → texture.
4. Renderer emits READY only after import, texture bind, and GL error checks pass.
5. READY is **per-buffer**, not per-draw. The AHB descriptor and EGLImage binding
   are immutable; later content changes are ordered by per-draw CPU unlock and
   GPU completion. READY stays valid until UNREGISTER, generation close, or EGL
   context loss.
6. An un-READY buffer never enters the direct queue. Before publication it may
   use the unchanged D0a path. REGISTER timeout is not assumed failure-safe: it
   poisons the generation unless a definite REGISTER_FAILED followed by
   UNREGISTER_ACK proves the renderer holds no resource.
7. Socket writes are framed, checked, and serialized inside each process; a
   partial write, malformed frame, version mismatch, or HUP is generation-fatal.

### 3. Per-Composite ownership transfer

For each admitted narrow R3 Composite:

```text
X_CPU_OWNED
→ finish all CPU writes
→ checked AHardwareBuffer_unlock(NULL)
→ X drops all CPU pointer use
→ per-entry refs + pending ownership acquired
→ publish existing queue entry using release semantics
→ renderer acquire-loads entry
→ GPU sample + destination draw
→ renderer fence create + glFlush + wait
→ publish logical RESULT
→ X acquire-loads RESULT
→ only then pending-- / release / future relock
```

The first prototype retains the current R3 predicate and adds:

```text
source type = AHB
source owner = server
priv->imported = false
buffer state = READY(current_generation)
Gate A Experimental flag = enabled
```

`COMPOSITE + source type AHB` identifies the direct path; no new queue-entry mode
bit is required. Staging remains the default/off path.

### 4. Result channel

A new result channel is mandatory, but a per-entry result ring is unnecessary for
the first fail-stop prototype. Add a versioned sideband to shared state:

```text
generation                 immutable
completedSerial            existing field, release/acquire atomic access
firstFailedSerial          0 or sticky first failure
firstFailureCode           valid before firstFailedSerial is release-published
generationFatal            sticky flag + reason
```

The existing `EVENT_GPU_COPY_DONE` remains only a wakeup hint. Correctness comes
from acquire-loading the shared result state, not from event delivery.

Logical result for serial `s`:

```text
firstFailedSerial != 0 AND s > firstFailedSerial
    → no later serial is executed; generation is failed/FATAL for that waiter

completedSerial >= s AND firstFailedSerial == s
    → RESULT(s, generation, FAILED_QUIESCED)

completedSerial >= s AND (firstFailedSerial == 0 OR s < firstFailedSerial)
    → RESULT(s, generation, SUCCESS)

generationFatal set before completedSerial reaches s
    → RESULT(s, generation, FATAL)
```

On first failure the renderer stops consuming later entries in that generation.
The sticky failure cannot be overwritten. This works because the first prototype
has no replay and therefore no legal continuation after a semantic failure.

### 5. `completedSerial` semantics

`completedSerial` remains:

```text
highest contiguous serial for which the GPU can no longer access the source or
destination
```

It is **not** a success flag. It may advance over `FAILED_QUIESCED`, because that
status proves no GPU access remains; `firstFailedSerial` separately prevents X
from treating the operation as successful. It never advances for `FATAL` where
GPU quiescence is unknown.

Required publication order:

```text
renderer writes failure detail if any
→ release-publishes firstFailedSerial when failed
→ release-stores completedSerial only after fence/quiescence
→ wakeup event

X acquire-loads completedSerial / firstFailedSerial
→ validates generation
→ derives RESULT
```

`writeIndex`, `readIndex`, and terminal fields must use explicit release/acquire
atomics. `volatile` alone is not protocol synchronization. `readIndex` retains its
slot-dequeued meaning; it does not release ownership and does not imply success.

### 6. Fence model

#### CPU→GPU

No new fence transport is needed. A successful
`AHardwareBuffer_unlock(buffer, NULL)` is the release boundary: NDK 29 specifies
that NULL makes unlock block until work/content update completes. If it returns
nonzero, ownership is unknown and the generation fails closed; X must not publish.

#### GPU→X

GPU completion is sufficient to make the source safe to relock **only if all are
true**:

1. every command that samples that AHB precedes the fence in the same EGL context;
2. EGL fence creation succeeds;
3. `glFlush` is issued;
4. `eglClientWaitSyncKHR(..., EGL_FOREVER)` returns
   `EGL_CONDITION_SATISFIED_KHR`;
5. draw/FBO/GL status is successful, or failure is explicitly classified but the
   same fence proves all possibly submitted work quiesced;
6. terminal result is release-published and acquire-observed for the same
   generation;
7. no other renderer path holds an untracked sample of that buffer.

After those conditions, future `AHardwareBuffer_lock(..., fence=-1)` is valid:
X has already proved prior GPU access complete. Fence creation/wait/context loss
is not completion and becomes FATAL.

## INVARIANTS

1. **Single access owner:** CPU pointer valid ⇒ no GPU access; GPU pending ⇒ no CPU
   pointer use or relock.
2. **READY is resource readiness, not content readiness:** per-buffer READY proves
   a persistent import; every draw still requires a fresh checked CPU unlock.
3. **No direct admission without READY:** timing/retry delay never substitutes for
   renderer acknowledgment.
4. **One generation:** every entry, result, READY, unregister and ACK must match the
   active shared-state generation.
5. **Lifetime:** X owner ref + per-entry refs and renderer AHB/EGLImage/texture refs
   survive through terminal result.
6. **Completion ≠ success:** `completedSerial` proves quiescence only; RESULT proves
   semantic success.
7. **No release on uncertainty:** timeout, HUP, context loss, malformed protocol,
   or unsatisfied fence cannot decrement pending ownership or permit relock.
8. **First failure is sticky:** no later queue entry executes after the first
   failed serial in that generation.
9. **Imported exclusion:** `priv->imported` is rejected before REGISTER/direct
   admission; no external acquire/idle fence is invented.
10. **GL-thread destruction:** texture delete → EGLImage destroy → renderer AHB
    release occurs on the owning current-context thread after no pending serial.
11. **No ID resurrection:** an old-generation buffer ID can never satisfy READY or
    lookup in a new generation.
12. **Default-off isolation:** disabling Gate A returns exactly to qualified D0a;
    no queue/router/predicate behavior changes for other paths.

## FAILURE MODEL

### Before queue publication

| Failure | Required action |
|---|---|
| AHB promotion/allocation/lock failure | no direct admission; retain existing safe path only if ownership is known, otherwise FATAL |
| CPU unlock returns nonzero | no publish, no relock assumption; FATAL |
| REGISTER_FAILED + UNREGISTER_ACK | renderer holds nothing; relock and use unchanged D0a path |
| READY absent/timeout, socket partial write, generation mismatch | FATAL; renderer ownership is uncertain |
| queue full before any direct entry | relock only after proving no GPU use; use unchanged D0a path |

Pre-publication use of D0a is not replay: no direct operation was published.

### After queue publication

| Result | Meaning | X action in first prototype |
|---|---|---|
| `SUCCESS` | GL path succeeded and fence proved quiescence | release per-entry ownership; future relock allowed |
| `FAILED_QUIESCED` | semantic failure, but fence proved no GPU access remains | record exact reason, safely retire refs, then terminate generation; **no replay and no normal success return** |
| `FATAL` | renderer death/HUP, context loss, malformed state, fence create/wait failure, or result timeout; quiescence unknown | do not ack/relock/unregister/reuse; terminate X generation and renderer generation |

A timeout is never converted to SUCCESS or FAILED_QUIESCED. Renderer death causes
X to terminate rather than recover the process-shared mutex and continue. X death
causes renderer to abandon the generation/context; no automatic same-generation
reconnect is permitted.

The fatal path must not run ordinary CloseScreen cleanup that assumes GPU
quiescence. X exits without reusing the affected mappings; the activity discards
its renderer generation/context, allowing process/driver teardown to release its
references. A later session starts with a fresh generation only after old process
liveness is gone.

### Draw/import checks

- READY checks native-client-buffer, EGLImage, texture creation/binding, descriptor
  identity, and GL errors.
- Every direct draw checks current generation/context, source READY state,
  destination lookup, FBO completeness, and GL errors around bind/draw.
- Failure before command submission is immediately quiesced.
- Failure after any possible submission becomes FAILED_QUIESCED only after a valid
  fence wait; otherwise FATAL.

## LIFECYCLE

### UNREGISTER

```text
X marks buffer RETIRING
→ rejects new direct submissions
→ waits until every submitted serial using it has terminal RESULT
→ sends UNREGISTER(generation, id)
→ renderer verifies no queue/in-flight reference
→ GL thread deletes texture
→ destroys EGLImage
→ releases renderer AHB reference
→ sends UNREGISTER_ACK(generation, id)
→ X removes registration and releases owner/pixmap reference
```

UNREGISTER timeout or mismatched ACK is FATAL, not permission to free.

### CloseScreen / normal generation close

```text
mark generation CLOSING
→ reject all new queue publication
→ snapshot lastPublishedSerial
→ wait terminal RESULT through that serial
→ UNREGISTER + ACK every registered buffer
→ request renderer generation close
→ renderer confirms queue empty, no in-flight fence, all GL resources destroyed,
  state pointer detached
→ renderer sends GENERATION_CLOSED(generation)
→ only then destroy root pixmap and unmap/reset shared state
```

If any wait or ACK fails, switch to the fatal process-termination path; do not
resume, reinitialize the shared mutex, or reuse the mapping. EGL context loss is
whole-generation FATAL rather than per-buffer re-READY in the first prototype.

## REDLINE CHANGES

### Required internal changes in a later prototype

```text
shared-state ABI: YES — version/generation + atomic sticky result sideband
control protocol: YES — READY/REGISTER_FAILED/UNREGISTER_ACK/generation close/fatal
result channel: YES — mandatory shared sideband, existing wake event only hints
DoneComposite semantics: YES — wait for RESULT; failure cannot return normally
DestroyPixmap/CloseScreen lifecycle: YES — RETIRING, drain, ACK, generation close
CPU lock ordering: YES — checked unlock before publish and before releasing access guard
```

### Explicitly not required

```text
LorieGpuCopyEntry queue layout: NO CHANGE
completedSerial meaning: NO CHANGE (quiescence, not success)
native fence FD transport: NO
transparent CPU replay: NO
external/imported producer fence: NO — imported buffers excluded
D0b protocol/path: NO
Gate H/router: NO
predicate expansion: NO
Stable/HDMI: NO
```

The shared-state ABI and lifecycle changes are real architecture changes, but the
broad stop condition is not met: the design avoids queue-entry ABI replacement,
completedSerial redefinition, replay, external fences, and D0b. It is therefore
bounded enough for one isolated prototype, not production deployment.

## PROTOTYPE BOUNDARY AND GATES

A later prototype must be:

```text
Experimental-only / default OFF
one isolated worktree and one writer
server-owned, non-imported BGRA source only
existing narrow R3 Over predicate only
D0a exact fallback when direct admission never published
post-publication failure = generation fail-stop
no Stable / HDMI / D0b / Gate H / external producer path
```

Before any runtime, static/fault-injection gates must prove:

1. READY invalidates on generation/context close;
2. queue/result atomics form release/acquire edges;
3. missing source, import failure, GL error, fence create/wait failure, timeout,
   HUP, and malformed generation never produce normal success or early relock;
4. unregister deletion order is texture → EGLImage → renderer AHB → ACK → X ref;
5. CloseScreen cannot destroy root/state before GENERATION_CLOSED.

Runtime qualification remains a separate authorization and must include repeated
same-AHB CPU↔GPU cycles, exact 1514 oracle, narrow R3 stress, forced pre-publish
failure, forced FAILED_QUIESCED, fatal teardown, resize/recreate, no residue, and
unchanged flag-off D0a. No runtime is authorized here.

## NEXT

One action only: create a written implementation plan for this exact default-off
prototype, mapping each protocol transition to existing symbols and tests. Do not
write code until that plan is reviewed against this design.
