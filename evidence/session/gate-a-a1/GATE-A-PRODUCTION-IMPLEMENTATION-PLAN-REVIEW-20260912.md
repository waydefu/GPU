# Gate A default-off prototype implementation-plan review — 2026-09-12

## VERDICT

```text
HOLD — NEEDS NARROW PROTOCOL REVIEW
P0 IMPLEMENTATION: NOT AUTHORIZED
```

The plan has the right phase structure and redlines, but P0 types currently
encode an ambiguous/lossy result channel, and P1–P4 contain an unsafe first-use
ordering and an over-broad fallback rule. Those are protocol-definition defects,
not implementation details; starting P0 now would freeze the wrong ABI.

Scope: review only against `qualification/d0a-narrow-20260912` / `a6cc795` and
`GATE-A-PRODUCTION-PROTOCOL-DESIGN-20260912.md`. No source/build/CI/APK/ADB/
device/Stable/HDMI operation.

## ACCEPTED PARTS

- Experimental flag default OFF and OFF-path D0a equivalence.
- Existing narrow R3 predicate; `priv->imported == false`; no external fence,
  replay, D0b, Gate H, Stable, or HDMI work.
- READY is per-buffer, not per-draw.
- Queue-entry layout remains unchanged.
- `completedSerial` is separated from semantic result.
- Checked blocking `AHardwareBuffer_unlock(NULL)` and no native fence transport.
- Lazy relock only on actual future CPU access.
- Texture → EGLImage → renderer AHB → ACK → X owner release ordering.
- Phase-gated small diffs and fault-injection-before-runtime intent.

## MUST-FIX BEFORE P0

### 1. P0 result sideband is a lossy “latest result” slot

**Severity: HIGH / Confidence: HIGH**

The proposed fields:

```text
result_serial / result_generation / result_state
```

cannot represent multiple in-flight queue serials. The renderer can overwrite
`SUCCESS(s1)` with `SUCCESS(s2)` before X observes `s1`; `DoneComposite` then has
no durable `RESULT(s1)`. A per-entry ring would require its own consumption/ack
protocol and would widen P0 unnecessarily.

Use the authorized minimal representation instead:

```text
protocol_version
generation
completedSerial       // existing, highest contiguous GPU-quiesced serial
firstFailedSerial     // sticky; 0 means none
firstFailureCode      // written before firstFailedSerial release-store
generationFatal       // sticky, with reason
```

Logical results are derived:

```text
completed >= s && (failed == 0 || s < failed) → SUCCESS
completed >= s && failed == s                 → FAILED_QUIESCED
failed != 0 && s > failed                     → generation failed; never executed
fatal before completed reaches s              → FATAL
```

On first failure, renderer stops consuming later entries. Remove ambiguous
`result_serial/result_state/sticky_failure` names from P0 or define them exactly
as the sticky model above.

### 2. P3 incorrectly sends fatal/uncertain states to D0a

**Severity: HIGH / Confidence: HIGH**

P3 says any failed admission condition—including sticky failure or fatal
generation—uses D0a. That violates the fail-closed contract: after a fatal or an
uncertain READY timeout, ownership may be unresolved. D0a would relock/read the
same AHB and may race renderer/GPU work.

Required decision table:

| Condition | Action |
|---|---|
| flag OFF, predicate miss, imported source, or no registration attempted while CPU ownership is intact | unchanged D0a |
| explicit REGISTER_FAILED **and** UNREGISTER_ACK, no GPU use | relock, then unchanged D0a |
| READY timeout/drop after REGISTER, malformed message, generation mismatch | FATAL; no D0a |
| sticky failure or fatal generation | FATAL; no new Composite path |
| queue full before any publish and no renderer use | checked relock, then D0a |
| any failure after publish | terminal RESULT or generation fail-stop; never D0a/replay |

### 3. P2 READY currently precedes the first CPU release

**Severity: HIGH / Confidence: HIGH**

The plan orders P2 REGISTER/READY before P4 unlock. The authorized model requires
the AHB to be outside CPU access before first REGISTER/import validation. Current
source leaves the promoted source in `priv->locked` (`InitOutput.c:225-230`).

Split implementation order from runtime transition:

```text
P2 may add message/registry machinery only
first actual direct use:
  checked unlock(NULL)
  → clear CPU state only on success
  → REGISTER
  → READY
  → queue publish
```

If REGISTER explicitly fails and renderer ACKs that it released all resources,
X may relock and use D0a. A READY timeout is FATAL because import ownership is
uncertain.

### 4. P1 treats death/context loss as a normal terminal generation

**Severity: HIGH / Confidence: HIGH**

`renderer reconnect/context loss → old generation terminal → generation++` is not
safe. Renderer death or context loss does not prove its GPU work quiesced.

Define two disjoint closures:

```text
CLEAN CLOSE:
all serials terminal
→ all UNREGISTER_ACK
→ GENERATION_CLOSED
→ old generation may be released

FATAL CLOSE:
renderer death/HUP/context loss/result timeout
→ generation poisoned
→ no relock/normal unregister/resource reuse
→ X and renderer session terminate
→ new generation only after old process/context liveness is gone
```

Generation must be a non-repeating 64-bit nonce or boot/session-epoch sequence;
a process-local counter that resets is insufficient for the “generation reuse
rejected” test.

### 5. Fatal/session termination is not mapped to a safe cleanup path

**Severity: HIGH / Confidence: HIGH**

P8 says “terminate generation/session” but P10/P11 still describe normal cleanup.
On unquiesced FATAL, ordinary `DestroyPixmap`/`CloseScreen` would free or
unregister the uncertain AHB—the exact behavior the protocol forbids.

The plan must name a separate fatal path:

- no `pending--`, relock, CPU repair/replay, UNREGISTER, or normal ACK;
- no same-process generation recovery and no shared-mutex reinitialization;
- X exits without running resource cleanup that assumes quiescence;
- activity discards the whole renderer context/generation;
- a new session is permitted only after both old process/context lifetimes end.

`FAILED_QUIESCED` may safely retire resources, but because replay is forbidden it
still cannot return normal Composite success; it closes the whole session after
recording the exact failure.

### 6. Cross-process atomic requirements are underspecified

**Severity: HIGH / Confidence: HIGH**

“atomic release/acquire” is insufficient for an ABI review. P0 must specify:

- naturally aligned fixed-width fields and static layout assertions;
- process-shared, lock-free atomic operations (for example checked `__atomic_*`
  builtins), not an implementation that can fall back to a process-local lock;
- exact directions:
  - X release-stores `writeIndex`; renderer acquire-loads it;
  - renderer release-stores `readIndex`; X acquire-loads it for slot reuse;
  - renderer writes failure detail, release-publishes `firstFailedSerial`, then
    release-stores `completedSerial` after quiescence;
  - X acquire-loads terminal fields before releasing ownership;
- `readIndex` means slot copied/dequeued only—never completion or success.

### 7. Control-path file/symbol map is incomplete and risks a broad rewrite

**Severity: MEDIUM-HIGH / Confidence: HIGH**

AHB receive is not in `cmdentrypoint.cpp`; it is
`activity.cpp::xcallback(EVENT_ADD_BUFFER)`, then `Renderer::addBuffer`, then GL
attach in `Renderer::threadLoop`/`findBufferWithRetry`. READY can only be emitted
after the renderer-thread GL attach validation. Reverse messages are read by
`cmdentrypoint.cpp::handleLorieEvents`.

Add exact mappings:

```text
activity.cpp::xcallback / connect_          X→activity REGISTER receive
renderer.cpp::addBuffer / threadLoop        GL-thread import and READY decision
renderer.cpp::notifyGpuCopyDone replacement renderer→X wake/result hint
cmdentrypoint.cpp::handleLorieEvents         READY/ACK/FATAL reception
cmdentrypoint.cpp::lorieRegisterBuffer       framed REGISTER send
```

Do not retrofit framing across unrelated clipboard/input traffic. Scope framing,
checked full writes, and the writer lock to new Gate A control transactions (the
REGISTER event + handle send must be serialized as one logical transaction).

### 8. Direct renderer symbols and readiness checks are missing

**Severity: HIGH / Confidence: HIGH**

P6 names only `renderer.cpp`, but current BGRA behavior is controlled by:

- `buffer.c::LorieBuffer_attachToGL`—explicitly rejects BGRA EGLImage and returns
  no status (`buffer.c:635-663`);
- `buffer.c::LorieBuffer_bindTexture`—CPU-locks/uploads BGRA (`665-673`);
- `renderer.cpp::findBufferWithRetry`—moves a buffer to the ready list even if
  attach failed (`745-767`).

The plan must map these exact changes: a checked GL-thread direct-import result;
no renderer CPU lock/upload for ready direct BGRA; descriptor validation; texture
and EGLImage existence; GL error/FBO checks; and READY publication only after all
checks. An import-ready registry must be distinct from the current generic
`buffers` list.

### 9. UNREGISTER lacks per-buffer drain evidence

**Severity: HIGH / Confidence: HIGH**

“wait all buffer serials terminal” is not implementable from the existing
`gpuCopyPending` count alone. P0/P2 must define X-side per-buffer metadata:

```text
generation
state = UNREGISTERED / REGISTERING / READY / RETIRING / DEAD
lastSubmittedSerial
pendingCount
owner reference
```

Every source and non-root destination submission updates
`lastSubmittedSerial`; RETIRING rejects new submissions. `DestroyPixmap` is void,
so ACK timeout must take the fatal path and must not free `driverPriv`.
Duplicate REGISTER/UNREGISTER rules also need exact idempotency:

- duplicate matching REGISTER → re-emit current READY/FAILED state;
- same ID with different descriptor/generation → FATAL;
- duplicate UNREGISTER after ACK → deterministic stale/ACK response without
  resurrecting the object.

### 10. Runtime acceptance checks the microprobe, not enough production path

**Severity: MEDIUM / Confidence: HIGH**

“A1 pixel oracle remains exact” only rechecks isolated capability. The later
runtime plan must explicitly require:

- flag-OFF equivalence to qualified D0a;
- production-path 1514-case oracle: `fail=0`, `maxΔ=0`, `Xnz=0`;
- CONTROL/BGRA direct-path telemetry proving zero staging clone/upload;
- repeated same-AHB CPU unlock → GPU sample → terminal result → lazy relock cycles;
- imported-buffer rejection and unchanged software fallback matrix;
- one isolated launch per fatal fault-injection cell, no automatic retry;
- exact teardown evidence for FAILED_QUIESCED, FATAL, DestroyPixmap, CloseScreen,
  reconnect/new generation, AHB/EGLImage/FD/RSS residue.

## PHASE ORDER CORRECTION

Keep the phase-gated structure, but revise dependencies to:

```text
P0 exact version/generation/sticky-result ABI + lock-free atomic proof
→ P1 clean-vs-fatal generation state machine
→ P2 control framing + per-buffer registry (no live use yet)
→ P3 checked first-use CPU release + REGISTER/READY handshake
→ P4 admission decision table
→ P5 queue/result atomic publication
→ P6 checked direct import/sample
→ P7 fence/result production
→ P8 DoneComposite terminal handling + fatal path
→ P9 lazy relock and FinishAccess ordering
→ P10 RETIRING/UNREGISTER/ACK
→ P11 clean CloseScreen vs fatal teardown
→ static/fault-injection review
→ only then build/runtime authorization
```

P0 review must freeze exact field widths, alignment, result derivation and clean/
fatal generation semantics. No source phase should begin while these remain
ambiguous.

## REDLINE REVIEW

```text
Queue-entry ABI unchanged: PASS-CANDIDATE
completedSerial meaning unchanged: PASS-CANDIDATE after exact atomic rules
Transparent replay absent: PASS
Imported/external fence excluded: PASS after P3 fallback correction
D0b / Gate H untouched: PASS
Default-off D0a equivalence: PASS-CANDIDATE; must be tested later
Renderer lifecycle scope: REQUIRED but bounded to generation close/fatal path
Global control protocol rewrite: REJECTED; Gate A framing only
```

The plan does not yet cross into `BLOCKED — TOO BROAD / UNSAFE`; its architecture
can remain bounded after the ten corrections. It is nevertheless not safe to
start P0 because P0's current result fields would define the wrong contract.

## NEXT

One action only: revise P0–P4 and the fatal/UNREGISTER sections to incorporate
the ten must-fix items above, then resubmit the plan for a protocol ABI review.
No code/build/runtime is authorized.
