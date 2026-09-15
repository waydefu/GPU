# D0b-R1 Architecture Re-authorization — 2026-09-12

> **SUPERSEDED / AUTHORIZATION REVOKED:** post-implementation Sol review found
> a cross-process D0b mode-selection gap and a renderer stale-texture draw path,
> plus native compile errors. Current authority is
> `GATE-D0B-R1-POST-IMPLEMENTATION-REVIEW-20260912.md`; D0b is `HOLD`.

## SOURCE

```text
branch: qualification/d0a-narrow-20260912
HEAD: a6cc7952861b8a63740d42bf78553573cfa0eec0
tracked worktree: clean
device/runtime operations: none
```

Five read-only GPT-5.6 Luna Max scouts were run in independent sessions with
Hermes `--reasoning max`, never more than two concurrently. Sol reviewed only
the decisive source slices and owns this verdict.

## VERDICT

```text
Sampling invariant:                  PROVEN for the approved bounded path
Bounds gate:                         VALID
Refreshed region definition:         PROVEN
Copy-before-publish:                 PROVEN by delayed transaction publication
Queue ABI change required:           NO
Conservative completedSerial reuse:  PROVEN by approved cache guard
Failure-path reuse safety:           PROVEN by quarantine/fallback rule
New ownership semantics required:    NO
New fence semantics required:        NO
Stride-safe partial upload:          PROVEN by per-row upload design
High-risk lifecycle semantics touched: NO

D0b: AUTHORIZED FOR NARROW PROTOTYPE
```

This is source implementation authorization only. Runtime PASS is not implied.

## Approved narrow architecture

### 1. Feature gate

D0b is default-off and active only when both the existing D0a cache and a new
D0b flag are explicitly enabled:

```text
TERMUX_X11_D0A=1
TERMUX_X11_D0B=1
```

D0b-off must retain the current D0a full-clone/full-upload behavior exactly.

### 2. Bounds and sampling proof

`exaTryDriverComposite` converts each canonical destination region box to source
pixmap-storage coordinates before invoking the driver Composite callback
(`exa_render.c:670-772`). `lorieExaComposite` is the first narrow point where the
post-offset `srcX/srcY/width/height` and authoritative source pixmap dimensions
coexist (`InitOutput.c:2270-2305`).

Every D0b rectangle must be checked there, before BoxRec casts or any staging
copy, with overflow-safe arithmetic:

```text
width > 0
height > 0
0 <= srcX
0 <= srcY
srcX + width  <= exaGpuComp.src->drawable.width
srcY + height <= exaGpuComp.src->drawable.height
```

A rejected rectangle makes the whole prepared transaction software-only; no GPU
entry from that transaction may be published. Predicate support is narrowed, not
widened.

For an accepted rectangle, the source storage rectangle is passed unchanged to
the existing queue entry. Renderer UV endpoints use that same rectangle and FD
stride, and Composite forces nearest sampling (`renderer.cpp:885-907,1352-1374`).
With integer 1:1 geometry and in-bounds coordinates, fragment centers map exactly
to texels in the half-open source rectangle. No mask, transform, repeat,
bilinear, componentAlpha, or alphaMap is admitted.

### 3. Exact refreshed set

The D0b refreshed set is:

```text
exact union of accepted SOURCE rectangles in FD staging coordinates
```

It is not destination Damage, screen Damage, or guessed source Damage.

Use transaction-private Region state under `exaGpuComp` (or an equivalent
private representation). The X/pixman Region abstraction is explicitly a set of
disjoint rectangles (`pixman-region.c:121-140`); `exaTryDriverComposite` applies
a constant translation to each box, preserving disjointness. Record the constant
`dst-src` offset and fail closed if callbacks disagree.

Logical dirty bytes are `union_area * 4`. Physical copy/upload bytes and calls
must be recorded separately.

### 4. Copy-before-publication

Do not publish from each `lorieExaComposite` callback in D0b mode.

Approved sequence:

```text
PrepareComposite
→ acquire a completion-proven cached FD (or allocate first cache)
→ each Composite callback: validate bounds, copy exact source rows, add rect
→ DoneComposite: after every CPU dirty copy is finished, publish one existing
  queue entry carrying the accumulated Region (only if rect count fits)
→ existing EGL fence/completedSerial wait and release path
```

If the accumulated Region exceeds `LORIE_GPU_COPY_MAX_RECTS`, metadata/region
allocation fails, offsets disagree, or scheduling fails before publication, the
whole transaction uses existing CPU Over fallback. No partial GPU transaction is
allowed.

The existing `LorieGpuCopyEntry.numRects/rects[]/xOff/yOff` fields are sufficient
(`lorie.h:171-213`). Shared queue layout and ABI remain unchanged.

### 5. Conservative cache reuse

Maintain private cache reuse state tied to the last serial that used the staging
cache. Before any D0b CPU write or cache replacement, require the existing
completion predicate:

```text
lorieGpuCopyIsDone(last_staging_serial) == TRUE
```

A successful current `lorieGpuCopyWait` may mark the cache reusable. A false wait
never does. This uses the existing completedSerial meaning unchanged.

On timeout, disconnect, renderer unavailable, or fence failure:

```text
reuse permission = false
no staging overwrite
no busy-cache unregister/replacement
software fallback for new Composite work
cache remains quarantined until an existing completedSerial proof succeeds
```

A reconnect/generation ambiguity must remain fail-closed; it may leave the single
cache quarantined for the rest of the X-server generation. Bounded retention is
acceptable for this prototype. Do not add a renderer-consumed ack, generation
field, ownership transfer, or fence.

The existing per-entry/caller/cache references and DoneComposite release ordering
remain unchanged. Reading the wait result only controls future cache reuse; it
must not redefine completion or release ownership.

### 6. Stride-safe upload

Add a narrow FD-region upload helper. For each accepted rectangle, upload one row
at a time:

```text
glTexSubImage2D(
  GL_TEXTURE_2D, 0,
  rect.x1, y,
  rect_width, 1,
  GL_RGBA, GL_UNSIGNED_BYTE,
  data + ((size_t)y * stride + rect.x1) * 4)
```

Use overflow-safe pointer/size checks and preserve the current GL_RGBA byte
contract. Do not use or assume `GL_UNPACK_ROW_LENGTH`. FD texture allocation
remains `stride x height`; renderer UV division remains by FD stride.

Only Composite entries under D0b use the region helper. Copy, Present, root draw,
D0a-off, and non-FD paths keep the existing full bind/upload helper.

### 7. Required telemetry

Default-off, append-only telemetry may add:

```text
dirty_rect_count
dirty_union_pixels
staged_logical_bytes
staged_physical_bytes
upload_logical_bytes
upload_physical_bytes
upload_call_count
bounds_reject_count
cache_reuse_proven
cache_quarantine_count
completion_proven
```

Unavailable measurements remain null, never fabricated zero.

## Allowed source scope

```text
lorie/src/main/cpp/lorie/InitOutput.c
lorie/src/main/cpp/lorie/buffer.c
lorie/src/main/cpp/lorie/buffer.h
lorie/src/main/cpp/lorie/renderer.cpp
lorie/src/main/cpp/lorie/b3a_telemetry.c
lorie/src/main/cpp/lorie/b3a_telemetry.h
```

A smaller diff is preferred. No unrelated cleanup.

## Forbidden changes

```text
queue ABI / LorieGpuCopyEntry layout
completedSerial semantics
new fence or renderer-consumed ack
AHB/FD ownership or refcount transfer
CloseScreen / teardown / mutex recovery / generation or epoch
shader / blend / X-byte repair
predicate widening
Gate A / Gate H
Stable com.termux.x11 / DISPLAY=:1
```

## Pre-runtime source acceptance

The writer must build/check the isolated worktree and return the exact diff. Sol
must reject it before runtime if it crosses any forbidden boundary or fails to
make these facts mechanically observable:

```text
accepted rect == copied rect == uploaded rect == sampled rect
all CPU dirty copies complete before publication
busy/quarantined cache is never overwritten or replaced
D0b-off remains current D0a behavior
```

## Gate status

```text
D0b: AUTHORIZED FOR NARROW PROTOTYPE
Gate A: BLOCKED FOR CURRENT BGRA DIRECT-SAMPLING CONTRACT
Gate H: HOLD
Historical SIGSEGV: OBSERVED / NON-REPRODUCED / ROOT CAUSE UNKNOWN
```
