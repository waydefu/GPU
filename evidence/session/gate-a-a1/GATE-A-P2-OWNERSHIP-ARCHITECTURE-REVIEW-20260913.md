# Gate A P2 CPU→GPU ownership / direct-submission architecture review — 2026-09-13

## Scope and source authority

Read-only design/source review. No source code, build, CI, APK, ADB, runtime,
Stable, or HDMI operation.

```text
P1 worktree: src/f8-ahb-gatea-a1
branch: qualification/gatea-a1-microprobe-20260912
HEAD: 5e9eb2a6f2a05a0c8d50c49727519b61b2477302
status: clean; diff-check PASS
D0a: qualification/d0a-narrow-20260912 / a6cc795... / clean
Production Gate A: BLOCKED
```

Governing design: `GATE-A-PROTOCOL-ABI-REVIEW-R3-20260912.md` and
`GATE-A-P1-REVIEW-20260912.md`. This review does not reopen A1 sampling,
change the 168-byte queue entry, redefine `completedSerial`, admit imported
AHBs, add native fence-FD transport, or add replay.

Environment matrix: Android/ARM64 target, local NDK
`29.0.14206865` (`source.properties`); all four target ABIs previously compile
in P1 CI 34709782426. Android's current AHardwareBuffer reference and the exact
NDK r29 header both say `unlock(buf, NULL)` blocks until unlocking and content
update complete; `lock(..., fence=-1)` requires the caller to have proved prior
writes complete. Khronos `EGL_KHR_fence_sync` says a satisfied
`EGL_SYNC_PRIOR_COMMANDS_COMPLETE_KHR` fence proves the fence command and all
preceding context commands have fully realized their effects. A finite timeout
is supported; `EGL_FOREVER_KHR` does not time out.

## Verdict basis: current source vs authorized architecture

`5e9eb2a` is **not** already safe for direct submission. Decisive existing gaps:

1. `InitOutput.c:2224-2237` always snapshots BGRA into FD staging; source stays
   CPU-mapped. Direct admission does not exist.
2. `InitOutput.c:1695-1751`, `renderer.cpp:1075-1081,1216-1217,1262,1450`
   still access queue indices/watermark ordinarily; the P0 accessors are not
   wired. Mixed atomic/ordinary use is forbidden.
3. `renderer.cpp:1093-1096,1216-1217` skips missing buffers but consumes the
   serial; `InitOutput.c:2410-2432` repairs and releases even after wait failure.
4. `renderer.cpp:1250,1438,1471` uses `EGL_FOREVER`; Gate A must never do so.
5. Legacy `LorieBuffer_attachToGL/bindTexture` at `buffer.c:635-674` sends BGRA
   through CPU lock/upload. Gate A must bypass both.
6. P1 receive/import validation currently accepts BGRA only
   (`activity.cpp:143-148`, `renderer.cpp:301-309`), while the narrow destination
   is RGBX (`InitOutput.c:209-212`). P2 must permit exactly BGRA source plus RGBX
   destination; framing/fingerprint stay unchanged.
7. `lorieGateAAtomicsLockFree()` is defined but has no call site. It must gate
   ACTIVE before the first REGISTER.
8. A same-mapping generation re-share currently clears/reinitializes sticky
   state (`InitOutput.c:497-518`). Once any P2 READY/import exists, P2 cannot
   prove a clean rotation without UNREGISTER/GENERATION_CLOSED. P2 therefore
   fail-stops any such reshare **before** clearing the old fatal/tuple. Clean
   rotation remains a later lifecycle phase.

These gaps fit a bounded P2 diff without altering frozen wire/queue ABI. The
architecture below is therefore PASS; code remains absent until a separate
implementation action.

## 1. Source ownership — PASS

Per direct Composite transaction, source moves through:

```text
CPU_LOCKED
  → Prepare verifies server-owned, !imported, BGRA AHB, READY/current tuple
  → reserve source+destination in one X registry transaction
  → bounded acquire of shared state->lock (excludes renderer GL access)
  → recheck active tuple/fatal/READY/retiring/queue quiescence
  → finish all CPU writes
  → checked LorieBuffer_unlock(source), return == 0 required
  → clear priv->locked and pixmap->devPrivate.ptr immediately
  → READY/tuple/fatal recheck while transaction remains RESERVED
  → fill entry → release-publish writeIndex
  → state = GPU_OWNED; release state->lock
```

While `CPU_LOCKED`, renderer must not select the Gate A registry texture. The
shared lock closes any previous renderer use before unlock. After successful
`unlock(NULL)`, the NDK contract makes the CPU mapping invalid and completes the
content update before return; no native acquire-fence transport is needed.

After publication, only renderer owns active access. X retains process-local
references but no valid CPU pointer. Any code path that writes `priv->locked` or
`devPrivate.ptr` before terminalization is fatal. On terminal SUCCESS, X takes
the shared lock with a finite Gate A budget, checks fatal again, calls
`LorieBuffer_lock(...,-1)`, restores both pointers, then returns ownership. A
lock failure is FATAL, not a false success.

`PrepareComposite → Composite(s) → DoneComposite` is synchronous on the single
X server thread (`exa_render.c:434-493`), so Present/resize/destroy cannot run
between callbacks. Input-thread fatal can race; it only sets sticky fatal and
halts, never relocks.

## 2. Destination ownership — PASS

Source and destination are reserved and unlocked as one pair before the first
publish. Destination uses the P1 persistent RGBX EGLImage texture as FBO color
attachment; renderer owns its GPU writes until the same serial fence completes.

One fence after the draw prefix covers both source sampling and destination
writes, so their safe-to-relock boundary is identical. `completedSerial` alone
is not semantic success. X may lock/repair/read/write/reuse destination only
when the R3-derived result is SUCCESS and a final fatal check remains clear.

Depth-24 X-byte repair is legal only after SUCCESS, under the shared lock,
while X still owns transaction refs and before the transaction is released.
FAILED_QUIESCED or FATAL performs no repair and no relock.

Root destination is safe within this transaction: bounded acquisition of
`state->lock` waits for the prior redraw fence; unlock+publish occurs while the
renderer cannot enter; renderer then processes queue and optional root redraw
in one GL context/order; the terminal fence covers both. Non-root destination
uses the same pair state. Present/resize/destroy cannot interleave on the X
thread; defensive guards must reject/fatal any impossible early entry.

## 3. First use and reuse — PASS

First use:

```text
CPU remains locked during REGISTER/READY
→ REGISTER both source and destination if absent
→ READY must match (nonce,generation,id,fingerprint)
→ reserve pair
→ bounded shared-lock acquire
→ checked unlock source then destination
→ revalidate tuple/READY/no fatal
→ publish
```

REGISTER_FAILED is pre-publish cleanup ACK, so existing D0a/CPU fallback remains
safe while CPU ownership never left X. READY timeout/mismatch is FATAL per R3.

Reuse keeps P1 resources persistent. After terminal SUCCESS, both AHBs are
relocked before `DoneComposite` returns; subsequent CPU writes use the fresh
mapping. The next direct transaction repeats checked unlock. No texture is
recreated, no stale pointer survives unlock, and no overlapping CPU/GPU owner
exists. Descriptor/fingerprint change cannot reuse READY.

Multiple rectangles inside one EXA operation share one pair lease. The first
Composite performs ownership transfer; later Composite callbacks only append
in-order entries while ownership stays GPU-side. Queue-full after first publish
may wait for SUCCESS and retry; it may not switch to CPU. `DoneComposite` waits
the last serial and restores CPU ownership exactly once.

## 4. Queue publication — PASS

`LorieGpuCopyEntry` remains exactly 168 bytes and gains no mode bit. Gate A is
identified by `op==COMPOSITE` plus both IDs in the active READY registry and the
X-side pair lease.

All queue users—not only the new branch—must use P0 accessors, otherwise C has
mixed atomic/non-atomic accesses to the same fields:

```text
X: initialize every entry byte and assign dense nonzero serial
 → lorieGateAPublishWriteIndex(release)
renderer: lorieGateAObserveWriteIndex(acquire)
 → copy slot to process-local entry
 → lorieGateAPublishReadIndex(release)
X: lorieGateAObserveReadIndex(acquire) before slot reuse
```

`readIndex` means only “slot copied”; it never unlocks, ACKs, derives success,
or repairs. Renderer processes local entries strictly in ring order. Serial is
incremented only for an entry that will be published; wrap is FATAL.

## 5. Direct sampling — PASS

P2 must add a GL-thread-only lookup into `gateAReady`, returning immutable
process-local descriptor/texture data while resources remain generation-lived.
It must not call `findBufferWithRetry`, `LorieBuffer_attachToGL`, or
`LorieBuffer_bindTexture` for Gate A: all three belong to the legacy registry,
and BGRA `bindTexture` re-enters `AHardwareBuffer_lock` + `glTexSubImage2D`.

Direct path:

```text
READY source lookup + READY destination lookup
→ exact tuple/fingerprint/role/format checks
→ bind destination registry texture to FBO
→ glCheckFramebufferStatus == COMPLETE + GL_NO_ERROR
→ bind source registry texture directly
→ direct shader draw
```

A1 established BGRA EGLImage sampling returns logical RGBA. The existing D0a
Composite uploads physical X11 BGRA bytes as GL_RGBA, so its current
`composite ? 0` swizzle decision cannot be reused. Direct BGRA source must use
the `.bgra` shader (B/G/R reorder, alpha unchanged) when writing the RGBX FBO;
this follows A1's byte result plus the already-qualified destination FBO byte
contract—it does not reopen A1.

No CPU lock/clone, FD staging, `glTexSubImage2D`, or legacy buffer lookup is
reachable from this branch.

## 6. GPU completion — PASS

`applyPendingGpuCopiesLocked` must return a batch outcome, not only last serial:
`{lastSerial, gateASeen, firstFailure, gpuCommandsIssued}`. Both standalone and
redraw-shared fence sites consume it.

For any Gate A batch:

```text
draw/FBO commands issued
→ create EGL_SYNC_FENCE_KHR
→ glFlush + GL error check
→ finite eglClientWaitSyncKHR deadline, with fatal checks between quanta
→ EGL_CONDITION_SATISFIED_KHR
→ verify no context loss/fatal
→ firstFailed CAS if semantic failure
→ release-store completedSerial for contiguous prefix
→ wake X
```

The satisfied fence covers all prior commands and both source/destination.
Gate A never reaches any existing `EGL_FOREVER` call. Fence creation failure,
timeout, EGL error, context loss, HUP, or fatal during wait is FATAL and ends the
process without normal ownership cleanup.

If a lookup/FBO check rejects an entry before any GPU command for that entry,
that serial is vacuously quiesced. Publish `firstFailedSerial=S`, then
`completedSerial=S`, stop consuming, and wake X: FAILED_QUIESCED. If draw was
attempted, FAILED_QUIESCED is allowed only after a satisfied fence; otherwise
FATAL.

## 7. SUCCESS derivation — PASS

Loads are acquire and fatal is checked first:

```text
completed >= S
AND (firstFailed == 0 OR S < firstFailed)
AND fatal == 0
→ SUCCESS
```

Proof premises remain enforceable:

- single X publisher; serials dense and nonzero;
- single renderer GL consumer; local-copy ring order;
- one fence completes a contiguous consumed prefix;
- first semantic failure once-CASes `firstFailedSerial`, stops consumption, and
  never executes any later serial;
- missing/unready/invalid direct entry is never silently skipped;
- renderer checks fatal before each entry and immediately before completed
  publication; X checks fatal before derivation and before relock/release.

A success fully derived before a later unrelated fatal stays a credible
quiesced serial; X's final fatal check prevents normal ownership release once
fatal is visible.

## 8. Pre-publish race — PASS

The state pair is process-local and guarded by the X registry mutex:

```text
READY → RESERVED (source+destination atomically)
→ release registry mutex
→ bounded state->lock acquire
→ revalidate RESERVED + tuple + fatal + descriptors + queue capacity
→ unlock both
→ revalidate again
→ publish while lease remains RESERVED
→ GPU_OWNED
```

`lorieActivityConnected` and all pixmap/EXA lifecycle callbacks run on the same
X server thread, so clean generation rotation/retirement cannot interleave.
The input thread can only publish fatal; if it wins at any point after unlock,
X does not relock or fallback—it fail-stops. P2 reshare with any READY/import or
reserved/submitted entry halts before sideband reinitialization; it never clears
an old sticky fatal. Full clean rotation awaits UNREGISTER/GENERATION_CLOSED.

Thus “unlock succeeded, then READY retired/generation changed, then publish” is
not a valid transition. If detected despite the lease, it is protocol
corruption → FATAL. Safe relock fallback is intentionally unnecessary. Only a
failure before either unlock may fall back.

## 9. Cross-operation admission — PASS

The proposed user rule is necessary but insufficient. It must be strengthened:

```text
new CPU/Present/Composite/resize/destroy operation allowed IFF
  lastSubmittedSerial is semantically SUCCESS (not just completed)
  AND ownership == CPU_LOCKED (or no Gate A history)
  AND pendingCount == 0
  AND state not RESERVED/GPU_OWNED/RETIRING/DEAD
  AND current tuple active
  AND no fatal
```

Before the first direct transfer, require global prior queue quiescence
`completedSerial == gpuCopySerialCounter` plus `readIndex == writeIndex`. This
conservative barrier closes the existing Present OOM/early-ACK problem
(`present_execute.c:92-135`, `present_vblank.c:191-215`): dropping its ref cannot
make an unfinished older queue write admissible.

During Prepare→Done, the single X thread cannot enter Present, resize, destroy,
or another request. Defensive checks in `PrepareAccess`, `DestroyPixmap`,
resize, and CloseScreen make any impossible overlap FATAL rather than CPU
fallback. Normal Destroy/resize after SUCCESS is safe because CPU ownership was
restored; P2 leaves renderer resources/tombstones generation-lived (bounded
registry leak), and any re-share with them is fail-stop. Full release is later
UNREGISTER work, so Production Gate A remains blocked.

## 10. Failure model — PASS

| Cell | Classification | Required action |
|---|---|---|
| Predicate/format/imported/registry-full before REGISTER | SAFE PRE-PUBLISH FALLBACK | Existing D0a/software; CPU remains locked |
| REGISTER_FAILED after complete renderer cleanup | SAFE PRE-PUBLISH FALLBACK | Cleanup ACK; keep CPU mapping |
| Queue unavailable before either unlock and before any direct entry | SAFE PRE-PUBLISH FALLBACK | D0a/software |
| unlock source or destination failure | FATAL | Ownership ambiguous; no fallback/relock |
| generation/fatal/READY change after unlock | FATAL | Lease violation or async fatal; no publish fallback |
| renderer lookup miss before GL touch | FAILED_QUIESCED | firstFailed=S, completed=S, stop generation |
| destination FBO incomplete before draw | FAILED_QUIESCED | no GPU touch; terminalize and stop |
| bind/GL/context error | FATAL | Unless a narrow no-command error is later proven; conservative classification |
| draw semantic/GL failure + satisfied fence | FAILED_QUIESCED | firstFailed then completed; stop; X does not relock |
| draw failure without proven satisfied fence | FATAL | GPU touch uncertain |
| fence creation failure | FATAL | No quiescence proof |
| finite fence timeout/wait error | FATAL | No quiescence proof |
| context loss | FATAL | Registry/context generation invalid |
| renderer death/HUP | FATAL | Sticky poison + waiter wake + process halt |
| fatal racing with completion | FATAL if observed before X release | Renderer checks before publish; X checks before derive and relock |
| destination failure after commands | FAILED_QUIESCED only after fence; otherwise FATAL | Never repair on failure |
| slot copied/consumed but no GPU command | FAILED_QUIESCED | Vacuously quiesced, never SUCCESS |
| relock after SUCCESS fails | FATAL | Cannot return CPU ownership |
| later rect queue-full after prior direct publish | neither fallback nor failure yet | Wait prior SUCCESS and retry; wait failure → FATAL |

No post-publish path reaches CPU fallback, replay, X-byte repair, normal ACK, or
normal owner release unless SUCCESS is derived.

## P2 minimum implementation boundary

### `InitOutput.c`

- Add direct mode to existing `exaGpuComp` transaction; preserve narrow
  predicate and D0a fallback when admission fails pre-unlock.
- Register/wait source+destination READY while CPU remains locked.
- Pair reservation, bounded shared-lock acquire, checked pair unlock, pointer
  invalidation, revalidation, direct queue publish, Gate A waiter/result,
  success-only pair relock and X-byte repair.
- Rewire all queue index/completed accesses in this TU to P0 accessors.
- Add fail-stop guards for impossible CPU access/destroy/resize/Close overlap;
  no UNREGISTER or normal CloseScreen drain.
- Make any reshare after P2 registry/import use fail-stop before sideband reset.

### `cmdentrypoint.cpp` + `lorie.h`

- Add process-local pair ownership state/token and atomic registry APIs:
  reserve, validate-for-publish, mark-submitted, derive/wait terminal,
  restore-CPU, abort-before-unlock, query-busy.
- Extend metadata only process-locally; no wire or queue layout change.
- Wire actual-address lock-free gate into ACTIVE before first REGISTER.

### `activity.cpp` + P1 import validation in `renderer.cpp`

- Accept exactly server-owned candidate formats needed here: BGRA source and
  RGBX destination. Keep descriptor/fingerprint/tuple checks and 40-byte
  REGISTER framing unchanged.

### `renderer.cpp`

- Add READY-registry direct lookup for both IDs; no legacy lookup/attach/bind.
- Add direct FBO/source binding, BGRA direct swizzle, actionable GL/FBO errors.
- Return batch outcome, stop on first Gate A failure, finite Gate A fence waits,
  first-failure/fatal/completion atomic publication.
- Rewire all queue index/completed accesses in this TU to P0 accessors.
- Preserve legacy non-Gate-A draw/fence behavior outside the new branch.

### Explicitly unchanged

```text
LorieGpuCopyEntry layout / capacity / operation values
completedSerial meaning (highest contiguous GPU-quiesced serial)
P1 Gate A 40-byte framing and REGISTER/READY bodies
legacy CPU lock/unlock behavior outside direct Gate A transaction
imported/client AHB behavior (never Gate A)
external producer fences
transparent replay
D0a / D0b / Gate H
Stable / HDMI
UNREGISTER full lifecycle / clean CloseScreen drain
```

## Final verdict

```text
# GATE A P2 OWNERSHIP ARCHITECTURE REVIEW

SOURCE OWNERSHIP: PASS
DESTINATION OWNERSHIP: PASS
FIRST-USE / REUSE: PASS
QUEUE PUBLICATION: PASS
DIRECT SAMPLING: PASS
GPU COMPLETION: PASS
SUCCESS DERIVATION: PASS
PRE-PUBLISH RACE: PASS
CROSS-OP ADMISSION: PASS (strengthened rule required)
FAILURE MODEL: PASS

P2 IMPLEMENTATION: AUTHORIZED
Production Gate A: BLOCKED
NEXT: implement exactly this bounded P2 diff and stop at static review + native
compile; no CI/runtime until separately authorized
```

The authorization is for default-off prototype foundation only. Any need for a
queue-entry ABI change, completedSerial redefinition, normal same-session
recovery, native fence transport, imported AHB support, replay, UNREGISTER, or
clean CloseScreen lifecycle cancels it and returns P2 to review.
