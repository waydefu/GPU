# Gate A P1 review — generation + REGISTER/READY — 2026-09-12

Scope: design/implementation-boundary review only. No code/build/CI/APK/ADB/
device/Stable/HDMI operation. P0 (`97401bc`) types are taken as frozen; this
review does not redesign them. Out of scope (later phases): CPU→GPU unlock
transition, queue submission, direct sampling, DoneComposite, UNREGISTER
lifecycle, CloseScreen drain, runtime.

## 1. GENERATION — PASS

Identity: `(sessionNonce: u64, generation: u64)`.

- `sessionNonce` comes from `getrandom` once per X process inside `OsVendorInit`
  (which already runs once per process: re-entry guard `InitOutput.c:426-427`).
  `getrandom` failure disables Gate A for the process lifetime — no timestamp/PID
  fallback, no weak identity.
- `generation` starts at 1 and increments on every share: `lorieActivityConnected`
  (`InitOutput.c:479-483`) writes `(nonce, ++generation)` via
  `lorieGateAProtocolInit` **before** `lorieSendSharedServerState`. Renderer binds
  the tuple only on `EVENT_SHARED_SERVER_STATE` receipt and echoes it in every
  Gate A frame.
- Rotation: new connection/share → `generation++`; clean `GENERATION_CLOSE` →
  next bind uses `generation++`; any fatal → poison, never reuse; X server reset
  (CloseScreen path) closes admissibility — post-reset Gate A needs a fresh
  re-share handshake, otherwise stays closed on D0a; `u64` wrap → FATAL.
- Stale acceptance is impossible by construction: a restarted X process has a new
  nonce; a restarted activity is HUP, which fatally terminates both sides (R3
  containment); same-process reshare always bumps generation. Renderer never
  invents identity and accepts frames only for the bound tuple.
- Frame with mismatched tuple while a generation is ACTIVE → FATAL (never
  "resync"). Frame arriving with no bound generation (teardown race) →
  deterministic drop + log, no state change.

## 2. REGISTER — PASS

One writer-locked logical transaction on the X server thread: 40-byte frame
(header + `REGISTER` body) followed by the AHB handle on the existing SCM_RIGHTS
channel, all under a process-local Gate A send mutex (leaf — never held across
blocking calls).

Renderer receive (`activity.cpp::xcallback`, looper thread — never GL here):

```text
exact 40B read (short → §7) → magic/version/length/nonce/generation checks
→ AHB handle recv → AHardwareBuffer_describe → fingerprint compare
→ enqueue dedicated pending-import list (dedicated mutex, NOT bufferLock)
→ arm done at X side BEFORE send (see §6; no lost wakeup by construction)
```

Renderer GL thread (the single renderer pthread, `Renderer::initThread` →
`threadLoop`; EGL context lives here):

```text
dequeue → revalidate generation still active → extension gate
(lorieEglHasNativeClientBuffer) → EGLClientBuffer → EGLImage → texture create
→ bind → glGetError clean → insert READY registry → send READY (renderer send
mutex, GL thread is the SOLE renderer-side Gate A writer)
```

Failure at any step releases partials in reverse (texture → EGLImage → AHB ref),
inserts nothing, and sends `REGISTER_FAILED`. No renderer CPU-upload fallback is
reachable: Gate A candidates never enter the legacy `addedBuffers` path
(`LorieBuffer_attachToGL` BGRA branch stays for legacy only), and P2 sampling
uses the generation-scoped registry exclusively.

## 3. READY — PASS

READY means exactly one thing: renderer-side persistent import resources exist
and are valid for `(nonce, generation, bufferId, fingerprint)`.

READY explicitly does **not** mean: CPU ownership released, GPU owns the buffer,
or any particular Composite is safe. The per-Composite checked unlock stays in
its later phase; READY without a fresh unlock admits nothing.

Duplicate rules (deterministic, no new work): same tuple re-emits the current
state (READY / REGISTERING / FAILED); same ID with different fingerprint or
generation → FATAL.

## 4. REGISTRY — PASS

X-side entry (extends P0 `LorieGateABufferMeta`): nonce, generation, bufferId,
fingerprint, `lastSubmittedSerial` (0 until first use), pendingCount, ownerRef,
cpuLocked mirror, state (`UNREGISTERED/REGISTERING/READY/RETIRING/DEAD`),
unregisterAcked, plus one armed `LorieGateAWaiter` for the in-flight REGISTER.
Keyed by bufferId; guarded by a dedicated leaf mutex.

Renderer-side entry (extends P0 `LorieGateAImportEntry`): id, nonce, generation,
fingerprint, AHB ref, EGLClientBuffer, EGLImage, texture, ready, tombstone.
Pending-import nodes and the READY registry are NEW lists — legacy
`addedBuffers`/`buffers`/`findBufferWithRetry` never observe Gate A objects, so
legacy attach/consume cannot race Gate A imports.

`UNREGISTER` for an unknown ID → FATAL (X only unregisters what it registered).
Tombstone survives ACK; no resurrection. Late READY for a poisoned/closed
generation is dropped by tuple check.

## 5. CONTROL PATH — PASS

```text
X server thread: arm waiter → REGISTER frame + AHB handle (send mutex)
  → signal rendererCond (existing fire-and-forget wakeup)
activity looper (xcallback): exact frame read → tuple checks → AHB recv →
  describe → enqueue pending-import → (no GL, no Gate A send)
renderer GL thread: dequeue → validate → import → READY / REGISTER_FAILED
  (renderer send mutex)
X input thread (handleLorieEvents): exact frame read → tuple checks →
  registry update → dedicated condvar signal (direct; never WorkProc)
X server thread waiter: bounded wait + fatal-first loop → proceed / FATAL
```

Legacy clipboard/input frames are byte-identical and untouched; Gate A frames
are selected by header magic. No protocol rewrite.

## 6. THREADING — PASS

Thread map: activity main/looper (`xcallback`, `connect_`, JNI) · renderer
pthread = GL thread (`initThread` → `threadLoop`) · X server thread (EXA ops) ·
X input thread (socket reads → WorkProc for legacy only).

- Single writer per direction: X server thread (X→renderer, send mutex);
  renderer GL thread (renderer→X, send mutex). `xcallback` sends no Gate A
  frames. No cross-thread socket-write race.
- No lock inversion: Gate A send/registry/waiter mutexes are leaves, never held
  across socket I/O, cond waits, or `state->lock`. Verified no opposite nesting:
  renderer takes `state->lock → cursor.lock` (`redrawLocked`); X takes
  `cursor.lock` alone (`InitOutput.c:749-761`).
- No blocking rendezvous cycle: X waiters use dedicated condvars signaled from
  the input thread (never a WorkProc the waiter needs); X waiters never hold
  `state->lock` while blocked; renderer waits only on its GPU (bounded per R3)
  and on `stateCond` while holding nothing X needs; `setSharedState` blocking
  rendezvous is excluded from every fatal path.
- GL-thread wakeup for pending imports: `xcallback` enqueues under the Gate A
  mutex, then `pthread_mutex_trylock(stateLock)` — on success sets a hint,
  signals `stateCond`, unlocks; on busy, signals `stateCond` best-effort. The
  loop drains pending imports at loop top. Liveness bound: Gate A fence waits
  are bounded (R3), so a pending import is always visited promptly; a legacy
  GPU hang delays it until the 2000 ms READY budget expires → FATAL (safe,
  never a false READY). No missed *fatal* wakeup: fatal uses atomics plus
  waiter broadcast on paths independent of this hint.
- Missed ordinary wakeup cannot cause unsafety: worst case is a bounded delay
  ending in FATAL, never an unvalidated READY.

## 7. FAILURE MODEL — PASS

2000 ms budgets match the `lorieGpuCopyWait` precedent. Every item is terminal-
classified; nothing is log-and-continue:

| Failure | Verdict |
|---|---|
| short frame read/write (Gate A active) | FATAL (stream desync / unproven delivery) |
| bad magic/version/length | FATAL (active) / deterministic drop (no bound generation) |
| wrong generation/nonce | FATAL (active) / drop (unbound) |
| AHB handle recv failure | REGISTER_FAILED (S4 fail-closed recv retains nothing) |
| descriptor/fingerprint mismatch | REGISTER_FAILED + release AHB ref |
| EGLClientBuffer null / extension absent | REGISTER_FAILED |
| EGLImage null | REGISTER_FAILED + release AHB ref |
| texture/bind/GL error | REGISTER_FAILED + reverse-order destroy + release AHB |
| duplicate REGISTER, same tuple | re-emit current state (no new work) |
| duplicate REGISTER, conflicting tuple | FATAL |
| READY timeout | FATAL (late READY dropped by tuple check; renderer destroys on unbind) |
| renderer death / HUP | both sides poison + terminate (HUP bypasses blocking `setSharedState`) |
| X-side HUP (`handleLorieEvents` ERROR branch) | existing tracking drop stays; Gate A supplement: poison + signal all waiters FAILED + terminate, no normal cleanup |
| `getrandom` failure | Gate A off for the process |
| `UNREGISTER` unknown ID | FATAL |

REGISTER_FAILED carries proof of no-retention (registry insertion happens only
after all import steps succeed), so it doubles as the cleanup ACK the R3
admission rule requires. D0a fallback is reachable only after explicit
REGISTER_FAILED + cleanup ACK with CPU ownership intact — never from timeout,
mismatch, or any uncertain state.

## IMPLEMENTATION BOUNDARY (P1 diff, minimal)

Files: `InitOutput.c` (nonce at `OsVendorInit`, generation bump + protocol init
in the share path, X registry + waiter instances, framed REGISTER send);
`cmdentrypoint.cpp` (Gate A send mutex discipline note — sends stay on server
thread; no legacy framing changes); `activity.cpp` (`xcallback` Gate A dispatch
+ pending-import enqueue); `renderer.cpp` (pending drain, GL-thread validation,
READY/FAILED send, ready registry + tombstones); `lorie.h` (registry structs
with list linkage + mutexes; waiter instances live with entries).

New: per-direction send mutexes (leaf), X + renderer registries, pending-import
queue, waiter instances, frame handlers, exact `getrandom` + generation setup.

```text
P1 WILL NOT CHANGE:
queue entry ABI, completedSerial semantics, CPU lock/unlock behavior,
Composite submission, DoneComposite, production direct sampling,
imported AHB behavior (still rejected), D0a/D0b/Gate H, Stable/HDMI.
```

## VERDICT

```text
# GATE A P1 REVIEW

GENERATION:
PASS

REGISTER:
PASS

READY:
PASS

REGISTRY:
PASS

CONTROL PATH:
PASS

THREADING:
PASS

FAILURE MODEL:
PASS

IMPLEMENTATION BOUNDARY:
InitOutput.c + activity.cpp + renderer.cpp + cmdentrypoint discipline +
lorie.h registry/waiter instantiation; no legacy path, ABI, or lifecycle change

P1 IMPLEMENTATION:
AUTHORIZED

Production Gate A:
BLOCKED

NEXT:
ONE ACTION ONLY — implement exactly the P1 boundary above behind
TERMUX_X11_GATEA_PROTO=1 (default OFF); stop at static review + native compile,
no CI/runtime until that review passes
```
