# Gate A / Gate D Architecture Review — 2026-09-11

Status: architecture decision only; no renderer, ownership, fence, runtime, APK,
ADB, Stable, or Gate H change.

## Decision

```text
Gate A direct AHardwareBuffer/EGLImage: BLOCKED for the current BGRA source contract
Gate D persistent region staging:      PASS-CANDIDATE
Preferred first prototype:             D0 single-slot persistent FD texture + rect upload
Gate H:                                HOLD
```

## Current R3 path

1. `lorieExaPrepareComposite` accepts only the existing narrow R3 predicate and
   snapshots the complete locked BGRA source with `lorieCloneBgraAhbToFd`.
2. `lorieCloneBgraAhbToFd` allocates a full-size FD `LorieBuffer` and copies
   `width * height * 4` logical bytes row by row from the live AHB CPU mapping.
3. `lorieExaComposite` already builds a source rectangle and passes it to
   `lorieTryScheduleGpuBlit`; the queue therefore already carries exact rects and
   source→destination offsets.
4. For Composite, `lorieTryScheduleGpuBlit` substitutes the one-shot FD snapshot
   for the live source AHB, registers/acquires it, increments pending ownership,
   and publishes the queue entry with a release barrier.
5. Renderer `applyPendingGpuCopiesLocked` calls `LorieBuffer_bindTexture`, which
   uploads the complete FD extent with `glTexSubImage2D`; only then does it draw
   the queued rect into the AHB-backed destination FBO.
6. Renderer creates an EGL fence, flushes, blocks until completion, publishes
   `completedSerial`, and notifies X. `lorieExaDoneComposite` waits for the last
   serial before pending-dec/release and destination CPU visibility.

## Root cost

Verified whole-surface work:

- promotion: REGULAR→AHB allocate + lock + full `pixman_blt`;
- Prepare: full FD allocate/mmap + full source clone;
- renderer bind: full FD texture upload for every queue entry;
- Done: blocking completed-serial wait and release lifecycle.

The queue and draw are already rect-aware; staging and texture upload are not.
Existing 64×64 measured batch16 records use full 64×64 rects, so dirty upload
cannot reduce their bytes. A D0 win there can only come from avoiding repeated
FD/texture allocation and registration. Existing oracle rows include smaller
rectangles and can validate exact dirty-byte reduction without adding tests.

## Gate A — direct AHB/EGLImage

### Feasibility: BLOCKED for current source contract

- X11 little-endian ARGB/XRGB storage is byte-ordered B,G,R,A/X. Current source
  promotion deliberately uses `AHARDWAREBUFFER_FORMAT_B8G8R8A8_UNORM`.
- NDK 29's public `AHardwareBuffer_Format` enum does not declare that BGRA
  token. This project defines value `5` in `buffer.h` as an alias for
  `HAL_PIXEL_FORMAT_BGRA_8888`; EGL sampling support is therefore not a public
  NDK format guarantee.
- On this F8 stack, BGRA AHB imported as EGLImage sampled black. The current code
  explicitly excludes that path in `LorieBuffer_attachToGL` and falls back to
  CPU lock + `GL_RGBA` upload.
- Khronos specifies that valid AHardwareBuffer format/usage combinations are
  implementation-specific. Allocation success therefore does not prove usable
  EGLImage sampling.
- Direct sampling would begin while X still owns a CPU mapping unless the EXA
  access lifecycle is changed. Android documents simultaneous/inadequately
  synchronized access as caller responsibility; current source lock calls pass
  fence `-1`, so the caller must already have completed prior writes.
- Current completed-serial fence protects GPU→X reuse after rendering. It does
  not provide the missing CPU→GPU ownership transfer needed before direct source
  sampling.

A safe Gate A design would require: X CPU unlock before publish; an explicit
CPU→GPU fence handoff; EGLImage import and exact channel probe; GPU completion
fence; X relock only after completion; and AHardwareBuffer/EGLImage lifetime
held through the renderer fence. That changes ownership across both processes
and is not a 1–3 function prototype.

### Gate A byte-contract prerequisite

Before reconsidering A, a standalone format microprobe—not the renderer—must
prove on the POCO F8 Ultra:

1. known 2×2 X11 B,G,R,A/X bytes written through AHardwareBuffer CPU mapping;
2. unlock completion/fence honored;
3. EGL native client buffer + EGLImage + GLES texture import succeeds;
4. sampled pixels are exact, not black and not channel-swapped;
5. both source sampling and destination FBO/store/readback contracts pass.

Until then: direct BGRA source sampling is `BLOCKED`; usable alternate format is
`UNKNOWN / NEEDS RUNTIME GATE`.

## Gate D — persistent dirty-region staging

### Feasibility: PASS-CANDIDATE

D can retain the current safe ownership model:

- X continues reading the source through its existing CPU-locked AHB mapping;
- renderer never directly locks/samples that live BGRA AHB;
- immutable/published FD staging remains the cross-process source;
- existing queue barrier, pending references, completed serial, EGL fence, and
  Done wait remain unchanged.

### D0 narrow prototype

Use one bounded staging cache entry keyed by `(width, height, stride, format)`.
The cache owns one FD `LorieBuffer` and therefore one renderer-side GL texture.
On mismatch, after the previous completed serial, unregister/release it and
allocate one exact-size replacement. This is a one-entry memory cap, not a
size router.

For each Composite rect:

1. if the same staging buffer still has a prior queued rect, wait for its serial
   before overwriting staging bytes;
2. copy only the requested source rows into the same coordinates in the mapped
   FD staging buffer;
3. publish the existing queue rect/offset unchanged;
4. renderer binds the already-resident staging texture and uploads only that
   rect. With GLES2, use one contiguous call for full-width spans; otherwise use
   bounded row uploads unless `GL_EXT_unpack_subimage` is positively gated.

Only the current narrow Over predicate may enter D0. Copy/Solid and all software
fallback routes remain byte-for-byte unchanged.

### Exact functions to touch

1. `lorieCloneBgraAhbToFd` — turn full one-shot clone into one-entry cache
   acquire/replace; no pixel copy at Prepare.
2. `lorieExaComposite` — wait-before-reuse, copy only its exact source rect into
   staging, and record dirty/full bytes.
3. `Renderer::applyPendingGpuCopiesLocked` — for Composite+FD only, replace
   whole-texture bind upload with exact rect upload; retain existing draw,
   blending, fence, serial, and notification.

No queue-ABI change is required for D0: existing `rects`, `xOff`, `yOff`, and
`srcBufferId` are sufficient.

## Correctness risks

- stride padding: source pointer uses `srcStride * 4`; uploads must never treat
  logical width as row stride;
- channel contract: retain current `GL_RGBA` upload plus non-swizzle Composite
  shader path; do not introduce `GL_BGRA_EXT`;
- multiple Composite calls per Prepare: staging must not be overwritten before
  the prior renderer upload consumes it;
- partial initialization: only draw a rect after that exact rect has been
  staged and uploaded;
- region bounds/overflow: clip and validate x1/y1/x2/y2 before byte arithmetic;
- fallback after an earlier scheduled rect must wait for completion before CPU
  fallback touches the same destination;
- destination X-byte repair and exact premultiplied-Over math stay unchanged.

## Ownership and fence risks

- cache keeps exactly one owner reference; each queued use keeps the existing
  per-entry acquire/pending reference; Done releases only after completedSerial;
- cache replacement must occur only with no pending use and must call
  `lorieUnregisterBuffer` before dropping its owner reference;
- GL texture deletion remains on the renderer thread through the existing
  added/buffers/removedBuffers lifecycle;
- do not weaken `__sync_synchronize`, EGL fence creation, `glFlush`, blocking
  client wait, completedSerial publication, or Done wait;
- GPU execution/queue duration beyond existing telemetry remains
  `NOT OBSERVABLE`.

## Minimal runtime gate

Use only existing tests/protocols; do not expand B3a:

1. existing 1514-case oracle: exact `fail=0`, `maxDelta=0`, X-byte zero;
2. existing R3 narrow cell: exact pixels and fallback=0;
3. existing lifecycle create/destroy/recreate: no FD/RSS growth and
   `NO_X3_RESIDUE`;
4. existing cold-N5 and batch16 protocols, paired against the frozen current R3;
5. telemetry exact-count plus:
   `cache_hit`, `cache_miss`, `dirty_logical_bytes`, `dirty_transfer_bytes`,
   `full_logical_bytes`, and `row_upload_calls`;
6. assertions:
   dirty bytes equal the exact union/rect bytes, cache hit+miss equals eligible
   Prepare count, and unobservable GPU fields remain null—not zero.

Expected measurable result:

- full 64×64 measured rows: dirty/full ratio remains 1.0; expected win is only
  allocation/mmap/register/texture reuse;
- existing small oracle rectangles: transfer bytes should fall to exact dirty
  area (plus any explicitly reported stride/row overhead);
- no performance claim unless paired measured medians improve beyond run noise
  with identical correctness and lifecycle gates.

## Must not change

Gate H/router; size threshold; predicate; mask; transform; bilinear; repeat;
componentAlpha; two-pass; Copy/Solid; Glamor; Chromium/ANGLE; Stable; destination
format; blend function; X-byte repair; queue ordering; pending refcounts;
completedSerial/fence semantics; fallback safety; B3a workload matrix.

## Rollback

D0 is guarded by one Experimental-only runtime flag defaulting off. Rollback is
remove/disable that flag path and restore the three function bodies; queue ABI,
persistent data format, installed Stable package, and external API stay
unchanged. Every failed D0 session tears down `:3`; no automatic retry.

## Evidence classification

VERIFIED: current path, full clone/full upload, rect-aware queue, BGRA EGLImage
black workaround, current refcount/serial/fence lifecycle, existing raw geometry.

INFERRED: D0 should reduce allocation/registration and small-rect transfer cost.
No speedup is claimed before runtime measurement.

UNKNOWN / NEEDS RUNTIME GATE: row-upload overhead on Adreno 840, cache hit rate in
real desktop workloads, usable direct-AHB source format, native-fence latency,
GPU execution time, queue time.

## Sources

- Android NDK 29 local authority:
  `/root/android-sdk/ndk/29.0.14206865/source.properties` and
  `sysroot/usr/include/android/hardware_buffer.h`.
- Android Native Hardware Buffer reference:
  <https://developer.android.com/ndk/reference/group/a-hardware-buffer>
- Khronos `EGL_ANDROID_get_native_client_buffer`:
  <https://registry.khronos.org/EGL/extensions/ANDROID/EGL_ANDROID_get_native_client_buffer.txt>
- Current working-tree symbols cited above under
  `lorie/src/main/cpp/lorie/{InitOutput.c,buffer.c,buffer.h,lorie.h,renderer.cpp,cmdentrypoint.cpp}`.

## Next action

Implement only D0 behind an Experimental-only default-off flag in the three
functions above, then run the stated existing runtime gate once.
