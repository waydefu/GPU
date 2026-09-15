# Gate D0b Architecture Verdict — 2026-09-12

## STATUS

```text
D0b: HOLD
Sampling invariant: NOT PROVEN for the current R3 predicate
Staging overwrite boundary: GL upload return at API level; no current producer-visible consumed ack
Existing synchronization sufficient: NO as implemented for all paths
New ownership semantics required: NO for conservative completedSerial reuse;
                                  YES for any pre-GPU-completion reuse
Implementation: NOT AUTHORIZED
```

Source binding:

```text
branch: qualification/d0a-narrow-20260912
HEAD: a6cc7952861b8a63740d42bf78553573cfa0eec0
tracked worktree diff: clean
```

Read-only scouts used three independent GPT-5.6 Luna Max sessions:

```text
A sampling: 20260912_023758_69aac1
B lifetime: 20260912_023804_4a0292
C synchronization: 20260912_023811_68644f
```

Sol performed the final source/API verification below. No device, APK, Stable,
build, benchmark, source, queue, fence, ownership, or renderer mutation occurred.

## Sampling invariant — NOT PROVEN

The in-bounds, non-transformed subcase has the required one-to-one geometry:

1. `exaTryDriverComposite` computes the destination composite region, applies
   pixmap storage deltas, and emits one `Composite` callback per region box with
   translated source coordinates (`exa_render.c:688-772`).
2. `lorieExaComposite` converts each callback into the source rectangle
   `[srcX,srcX+width) x [srcY,srcY+height)` and queues the destination offset
   `dst-src` (`InitOutput.c:2288-2305`).
3. The renderer derives UV endpoints from the same queued rectangle and the FD
   texture stride, and forces `GL_NEAREST` for Composite
   (`renderer.cpp:885-907,1352-1374`). Fragment centers therefore map one-to-one
   to texels inside that half-open rectangle for an in-bounds integer rectangle.

That is not yet a proof for every operation admitted by the current predicate:

- `lorieCanAccelCompositePictures` rejects mask, transform, repeat, non-nearest,
  componentAlpha, alpha maps, and same-drawable cases, but it has no source
  geometry/bounds condition (`InitOutput.c:2077-2098`).
- `lorieCanAccelComposite` adds format/buffer/runtime checks, not bounds checks
  (`InitOutput.c:2101-2121`).
- `miClipPictureSrc` intersects only an optional source client clip; it does not
  establish that translated source coordinates are wholly within the source
  drawable (`mipict.c:264-283,314-386`).
- The renderer texture uses `GL_CLAMP_TO_EDGE` (`buffer.c:635-662`). Thus an
  admitted negative/right/bottom-overflow source rectangle can sample an edge
  texel outside the direct unbounded rectangle description, and a naive partial
  CPU copy/upload would also require an explicit in-bounds/clamping rule.
- No checked-in D0b definition says whether “dirty region” means the exact union
  of queued source rectangles, a source DamageRegion, or retained-validity
  state. Destination Damage (`damageComposite`) is not a source refresh proof.

Therefore Invariant A is not derivable from the current predicate and source.
Runtime oracle success cannot close this source-level gap.

## Staging-consumption boundary

The current path is:

```text
X thread full memcpy to cached FD
→ queue entry publish (__sync_synchronize + writeIndex)
→ renderer finds FD mapping
→ glTexSubImage2D(client pointer)
→ drawRegion / glDrawArrays
→ readIndex++
→ EGL fence wait
→ completedSerial publish
→ DoneComposite wait/release
```

Direct evidence:

- FD staging is mmap-backed in both processes and passed as client memory to
  `glTexSubImage2D` (`buffer.c:665-673`). No pixel-unpack buffer is used.
- OpenGL ES 2.0.25 §2.1 states that data binding occurs on call: pointer data are
  interpreted when the call is made, and subsequent changes have no effect on
  that GL command. Therefore the staging bytes for that upload are no longer
  needed after `glTexSubImage2D` returns. This is distinct from texture/draw GPU
  completion.
- The renderer advances `readIndex` only after upload return and draw submission
  (`renderer.cpp:781-918`), but the current protocol publishes no per-entry
  renderer-consumed serial/ack with a demonstrated producer acquire operation.
- `completedSerial` is deliberately published only after an EGL fence confirms
  GPU completion (`renderer.cpp:738-742,931-967,1101-1156`). It is later than
  the true client-memory boundary, but is sufficient on a successful wait.
- `lorieExaDoneComposite` logs a failed/timed-out `lorieGpuCopyWait` and still
  releases pending/caller references and resets transaction state
  (`InitOutput.c:2347-2388`). `lorieGpuCopyWait` returns false on timeout,
  connection loss, or renderer unavailability (`InitOutput.c:1723-1735`). A
  later cache hit can therefore overwrite staging without a proven boundary.

## Architecture decision

### Existing synchronization sufficient

```text
NO — as implemented for all paths.
YES — only on the successful completedSerial path.
```

The existing GPU-completion serial is a conservative sufficient boundary and may
be reused by a future D0b design. It is not the earliest boundary. The current
false-wait path must not be interpreted as completion or overwrite permission.

### New ownership semantics required

```text
NO for a conservative design that overwrites only after proven completedSerial.
YES if D0b tries to overwrite after upload consumption but before GPU completion.
```

Any early-reuse design would need a formally published renderer-consumed token
(or equivalent lock/ack with generation and acquire/release semantics) and a
separate lifecycle review. It is outside the narrow prototype.

## Allowed implementation scope

None under this verdict. To request re-authorization, submit a revised design
that remains default-off and proves all of the following without widening R3:

1. Define the refreshed set as the exact union of queued source rectangles in FD
   staging coordinates; do not substitute destination Damage.
2. Add a fail-closed per-rectangle source-bounds condition before any partial
   copy/upload. Out-of-bounds/edge cases remain software.
3. Prove all source rectangles written while entries are in flight are disjoint,
   or finish the complete CPU dirty copy set before publishing any entry.
4. Reuse/overwrite the cache only after a successful existing completion proof.
   Timeout/disconnect/renderer loss must preserve or quarantine the old bytes;
   no false release/overwrite.
5. Implement stride-safe subupload using row uploads or a proven tightly packed
   path; do not assume ES2 `GL_UNPACK_ROW_LENGTH`.

## Forbidden changes

- queue ABI/layout or completedSerial meaning
- new fence or renderer-consumed ack in the narrow prototype
- AHardwareBuffer/FD ownership or refcount transfer rules
- renderer/X-server cross-thread teardown or mutex recovery semantics
- blend, shader, X-byte repair, DoneComposite completion contract
- predicate widening; mask/transform/bilinear/repeat/componentAlpha stay software
- Gate A or Gate H reopening

## Acceptance tests for any revised design

1. **Static geometry proof:** every scheduled rectangle satisfies
   `0 <= x1 < x2 <= source_width` and `0 <= y1 < y2 <= source_height` after all
   drawable/pixmap offsets; queued rect == copied rect == uploaded rect == sampled
   nearest-neighbour footprint.
2. **Edge/fallback oracle:** negative source origin, right/bottom overflow, zero
   extent, fragmented clip, pixmap offsets, and multi-box clip; unsupported cells
   must take software fallback and remain exact.
3. **Dirty-byte accounting:** per entry record full-source, staged, uploaded bytes,
   rect count, and upload-call count. Expected staged/uploaded logical bytes equal
   the programmatically computed union area x 4; unavailable GPU time stays null.
4. **Overlap/order stress:** fragmented multi-box Composite with deterministic
   exact pixels; prove no CPU write overlaps a renderer-read region in flight.
5. **Consumption failure injection:** timeout, renderer unavailable, and fence
   failure must show zero unsafe cache overwrites/releases. Absence of a crash is
   not sufficient.
6. **Regression gates:** flag-off equivalence, oracle exact, batch16 with R3
   fallback=0 for supported cells, lifecycle recreate/FD baseline, fatal-signal
   scan, NO_X3_RESIDUE, and Stable untouched, all per `TEST-MATRIX.md`.

## Final verdict

```text
D0b: HOLD
```

Gate A remains `BLOCKED FOR CURRENT BGRA DIRECT-SAMPLING CONTRACT`.
Gate H remains `HOLD`. `HANDOFF.md` Next remains authoritative and unchanged.
