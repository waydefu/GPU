# P2-B.2 Retry R3 read-only architecture audit

> **Pre-R3 audit snapshot.** This file records the uncertainty before the corrected P2-B.2c oracle. The current verdict is in `GATE-P2-B.2.md`: valid per-pixmap-GC provenance and the corrected oracle passed with `fail=0`, `maxΔ=0`. Do not use the unresolved-boundary wording below to reopen P2-B.2.

Date: 2026-09-08  
Scope: source provenance, pixmap ownership, GPU Copy comparison, format contract, and a fail-fast smoke gate.  
Safety: this audit does not modify the rendering path, Stable `:1`, Damage, `sys_ptr`, `PixmapIsOffscreen`, or the EXA composite hooks.

## Executive conclusion

* PutImage's final backing write is the `fbBltStip()` destination derived from
  `pPixmap->devPrivate.ptr`. In this driver-managed EXA configuration,
  `loriePrepareAccess()` sets that field to `priv->locked`; for a
  `LORIEBUFFER_REGULAR` pixmap, `priv->locked == LorieBuffer_Desc.data`, the
  `calloc()` allocation.
* `sys_ptr` is not the client pixmap's owner in this path. The current
  `Sprep` evidence (`fb_ptr=0`, `sys_ptr=0`) agrees with the driver-managed
  EXA path.
* `lorieEnsureGpuSampleable()` is a convert-and-replace operation, not an
  alias and not allocate-only. `LorieBuffer_convert()` allocates an AHB,
  attempts a `pixman_blt()` from the REGULAR `desc.data`, then frees the old
  allocation and installs the AHB. However, the AHB lock/copy is conditional
  while the type replacement/free is unconditional. A failed AHB lock can
  therefore lose the source contents.
* At the time of this audit, the exact first bad boundary was still unresolved.
  The later R3 provenance run supplied S0/S1/S2/S3 and corrected the client
  harness, so this uncertainty is historical and does not overturn the current
  P2-B.2 PASS.
* The existing GPU Copy path reuses Ensure, buffer registration, the queue,
  renderer texture attachment, GPU fence/serial completion, and pending-copy
  locking. It additionally unlocks its BGRA source before scheduling. Composite
  uses a separate FD snapshot, but its snapshot is taken from the post-convert
  `priv->locked` mapping; the historical `FDCLONE px0=00000000` was therefore
  already downstream of the unresolved boundary.

## 1. Provenance map

### PutImage to GPU upload

```text
XCB PutImage
  ↓
miPutImage()
  src/upstream/lorie/src/main/cpp/xserver/mi/mibitblt.c:694-695
  ↓
GC PutImage dispatch: fbGCOps.PutImage = fbPutImage
  src/upstream/lorie/src/main/cpp/xserver/fb/fbgc.c:41-47
  ↓
exaPutImage() → exaDoPutImage()
  src/upstream/lorie/src/main/cpp/xserver/exa/exa_accel.c:137-230
  ↓ (no UploadToScreen hook, so fallback)
ExaCheckPutImage()
  src/upstream/lorie/src/main/cpp/xserver/exa/exa_unaccel.c:97-118
  ↓
exaPrepareAccess() → ExaDoPrepareAccess()
  src/upstream/lorie/src/main/cpp/xserver/exa/exa.c:282-360, 370-384
  ↓
loriePrepareAccess()
  src/f8-ahb/lorie/src/main/cpp/lorie/InitOutput.c:2172-2188
  pPixmap->devPrivate.ptr = priv->locked ?: priv->mem
  ↓
fbPutImage() → fbPutZImage()
  src/upstream/lorie/src/main/cpp/xserver/fb/fbimage.c:31-76, 77-121
  ↓
fbGetStipDrawable() → fbGetPixmapStipData()
  src/upstream/lorie/src/main/cpp/xserver/fb/fb.h:468-489
  destination = (FbStip *) pPixmap->devPrivate.ptr
  destination row stride = pPixmap->devKind / sizeof(FbStip)
  ↓
fbBltStip() writes:
  dst + (y1 + dstYoff) * dstStride + (x1 + dstXoff) * dstBpp
  ↓
priv->locked == LorieBuffer_Desc.data while type is REGULAR
  ↓
lorieEnsureGpuSampleable(pixmap, LORIEBUFFER_AHARDWAREBUFFER)
  src/f8-ahb/lorie/src/main/cpp/lorie/InitOutput.c:133-152
  ↓
LorieBuffer_convert()
  src/f8-ahb/lorie/src/main/cpp/lorie/buffer.c:225-284
  REGULAR desc.data → AHardwareBuffer lock/map → pixman_blt() → replace backing
  ↓
lorieRegisterBuffer() / lorieTryScheduleGpuBlit()
  src/f8-ahb/lorie/src/main/cpp/lorie/InitOutput.c:1331-1443
  ↓
Renderer::findBufferWithRetry() → LorieBuffer_attachToGL()
  src/f8-ahb/lorie/src/main/cpp/lorie/renderer.cpp:708-730
  src/f8-ahb/lorie/src/main/cpp/lorie/buffer.c:488-512
  ↓
LorieBuffer_bindTexture() → uploadBgraAhbAsRgba() or FD glTexSubImage2D()
  src/f8-ahb/lorie/src/main/cpp/lorie/buffer.c:444-483, 515-523
  ↓
Renderer::drawRegion() / FBO blend or copy
  src/f8-ahb/lorie/src/main/cpp/lorie/renderer.cpp:810-855, 1238-1260
```

### Driver-managed EXA fact that controls the map

`lorieExa.flags` is `EXA_OFFSCREEN_PIXMAPS | EXA_HANDLES_PIXMAPS`, without
`EXA_MIXED_PIXMAPS`, and it supplies `CreatePixmap2`,
`PrepareAccess`, and `FinishAccess` (`InitOutput.c:2203-2215`). EXA therefore
selects `exaCreatePixmap_driver()` and `ExaDoPrepareAccess()` rather than the
mixed-pixmap `sys_ptr` migration machinery:

* `exaDriverInit()` selects `exaCreatePixmap_driver()` and leaves
  `prepare_access_reg = NULL` for `EXA_HANDLES_PIXMAPS` without
  `EXA_MIXED_PIXMAPS` (`xserver/exa/exa.c:958-983`).
* `exaCreatePixmap_driver()` initializes `pPixmap->devPrivate.ptr` to NULL,
  calls `CreatePixmap2`, and records no normal `sys_ptr` for this driver
  (`xserver/exa/exa_driver.c:49-121`).
* `exaGetDrawablePixmap()` returns the pixmap itself for a pixmap drawable
  (`xserver/exa/exa.c:100-119`); it only calls `GetWindowPixmap()` for a
  window drawable.

Thus `sys_ptr` is not an alternate hidden copy that PutImage normally fills in
this configuration.

## 2. Pointer ownership table

| Stage | Pixel owner | Pointer | Stride | Contents expected |
|---|---|---|---|---|
| `CreatePixmap2`, usage hint other than 5 | `LorieBuffer` of type `LORIEBUFFER_REGULAR` | `priv->buffer->desc.data`, then `priv->locked` after `LorieBuffer_lock()` | `desc.stride * 4`; regular allocation sets `desc.stride = width` | Zero initially (`calloc`); becomes PutImage's source pixels |
| EXA before PrepareAccess | `LorieBuffer` REGULAR; X pixmap is only a descriptor | `pPixmap->devPrivate.ptr == NULL` | `pPixmap->devKind` is pitch metadata | No CPU access through `devPrivate.ptr` yet |
| EXA `ExaDoPrepareAccess` / lorie PrepareAccess | Same REGULAR `LorieBuffer` | `pPixmap->devPrivate.ptr = priv->locked ?: priv->mem`; normal client pixmap has `priv->locked` | `pPixmap->devKind`; for the regular allocation, width × 4 | PutImage destination/source bytes must be present here |
| `fbGetPixmapStipData()` | Same owner, transient EXA mapping | `(FbStip *)pPixmap->devPrivate.ptr` | `pPixmap->devKind / sizeof(FbStip)` | `fbBltStip()` writes the requested ZPixmap rectangle |
| EXA after FinishAccess | `LorieBuffer` REGULAR | `pPixmap->devPrivate.ptr = NULL` from EXA; `priv->locked` remains because the pixmap was already persistently locked | `pPixmap->devKind` remains pitch metadata | PutImage bytes remain in `desc.data` |
| Ensure before conversion | REGULAR `LorieBuffer` | `desc.data` is the source used by `LorieBuffer_convert`; `priv->locked` should alias it | `desc.stride` pixels; source copy uses this stride | Must equal the requested PutImage rectangle |
| AHB allocated and CPU-locked | New AHardwareBuffer | local `data` returned by `AHardwareBuffer_lock()` | `AHardwareBuffer_Desc.stride` pixels; destination byte pitch is `stride * 4` | Empty/new AHB until `pixman_blt()` completes |
| After conversion | AHardwareBuffer owns pixels; old REGULAR allocation is freed | `desc.buffer` owns AHB; `desc.data = NULL`; `priv->locked` is reacquired AHB mapping | `desc.stride * 4`; may exceed width × 4 | Must preserve REGULAR contents; current code does not prove this at runtime |
| Composite FD staging | New `LORIEBUFFER_FD` owns an mmap region | `dd->data`; copied from `priv->locked` by `lorieCloneBgraAhbToFd()` | `dd->stride * 4`; copy uses only logical width × 4 per row | Must equal post-convert source; current `FDCLONE px0=0` says it does not |
| Renderer GL texture | Renderer-side registered `LorieBuffer` | AHB is uploaded through a temporary CPU mapping; FD uses `desc.data` | AHB upload tight-packs to logical width if `stride != width`; FD texture is stride-wide | Same requested source bytes in upload format |
| GPU destination | Destination AHB / FBO attachment | `LorieBuffer_getGLTextureId(dst)` attached to FBO | Destination AHB logical width/height | Over blend or Copy result; GPU completion is fenced before Done/ack |
| GetImage | Destination AHB CPU lock or persistent mapping via EXA | `fbGetImage()` reads `pPixmap->devPrivate.ptr` after `PrepareAccess` | `pPixmap->devKind` | Expected exact X11 bytes; current failures equal original destination |

### Important distinction: `devPrivate.ptr`, `priv->locked`, `buffer`, `sys_ptr`

* `pPixmap->devPrivate.ptr` is a transient EXA-visible alias. EXA explicitly
  hides it again in `exaFinishAccess()` (`xserver/exa/exa.c:420-430`).
* `priv->locked` is the driver-private active CPU mapping. For REGULAR and FD
  buffers, `LorieBuffer_lock()` sets it to `desc.data`
  (`buffer.c:322-346`). For an AHB it is the pointer returned by
  `AHardwareBuffer_lock()`.
* `priv->buffer` is the owning `LorieBuffer` object. Its active pixel backing
  is `desc.data` for REGULAR/FD and `desc.buffer` for AHB.
* EXA `sys_ptr` is the EXA system-memory slot. In this driver-managed path it
  is NULL in the current evidence and is not the PutImage target. It must not
  be treated as equivalent to `priv->locked`.

## 3. `LORIEBUFFER_REGULAR` lifecycle and conversion proof

```text
CreatePixmap2(width,height,depth,usage_hint)
  └─ usage_hint != 5 → REGULAR
     └─ LorieBuffer_allocate()
        └─ calloc(1, stride * height * 4)
           └─ LorieBuffer_lock() → priv->locked = desc.data

PutImage
  └─ EXA PrepareAccess → pPixmap->devPrivate.ptr = priv->locked
     └─ fbPutImage/fbPutZImage/fbBltStip writes REGULAR desc.data
        └─ EXA FinishAccess clears pPixmap->devPrivate.ptr
           └─ persistent initial regular lock remains active

EnsureGpuSampleable(AHB)
  └─ sees desc.type == REGULAR
     └─ LorieBuffer_convert(REGULAR → AHB, BGRA for depth 32)
        ├─ allocates AHardwareBuffer with CPU and GPU usage
        ├─ describes it and obtains AHB stride
        ├─ tries AHardwareBuffer_lock(new AHB, ..., &data)
        ├─ if lock succeeds: pixman_blt(old desc.data → data)
        ├─ unlocks new AHB
        ├─ unconditionally changes type/format/stride/buffer
        ├─ unconditionally frees old desc.data
        └─ sets desc.data=NULL and internal buffer lock state to zero
     └─ ModifyPixmapHeader(new AHB stride × 4)
     └─ LorieBuffer_lock(new AHB) → priv->locked = new AHB mapping

GPU registration/upload
  └─ register buffer id and send AHB/FD handle
     └─ renderer attaches texture
        ├─ BGRA AHB: CPU lock and glTexImage2D(... GL_RGBA, bytes)
        └─ FD staging: glTexSubImage2D(... GL_RGBA, desc.data)

Done/destroy
  ├─ Copy: waits completedSerial, acks pending refs; source BGRA mapping was
  │  explicitly unlocked by lorieUnlockBgraAhb() before scheduling
  ├─ Composite: waits completedSerial, releases FD snapshot; the original
  │  source AHB mapping is not unlocked by DoneComposite
  └─ DestroyPixmap: unlocks active mapping, unregisters, releases LorieBuffer
```

### Allocate-only / replace / alias verdict

**Verdict: allocate + copy + replace; not alias.**

Evidence in `buffer.c:257-284`:

1. A new `AHardwareBuffer *b` is allocated.
2. The new buffer is locked into local `data`.
3. `pixman_blt(buffer->desc.data, data, buffer->desc.stride,
   desc.stride, 32, 32, ..., width, height)` is present.
4. `buffer->desc.buffer = b`, `buffer->desc.data = NULL`.
5. The old `buffer->desc.data` is freed.

The preservation guarantee is conditional, not unconditional: the
`pixman_blt()` is inside `if (AHardwareBuffer_lock(...) == 0)`, but the type
mutation and `free(buffer->desc.data)` happen after that conditional without a
failure branch. Therefore a failed lock can produce a new empty/uninitialized
AHB while discarding the only REGULAR copy. This is the first code boundary
that must be stamped.

## 4. Existing known-good GPU Copy comparison

### Working Copy call graph

The EXA Copy-shaped path is:

```text
exaHWCopyNtoN()
  xserver/exa/exa_accel.c:360-558
  ├─ pSrcPixmap = exaGetDrawablePixmap(pSrcDrawable)
  ├─ pDstPixmap = exaGetDrawablePixmap(pDstDrawable)
  ├─ driver-managed path has no migration copy (`do_migration = NULL`)
  ├─ verifies exaPixmapHasGpuCopy(src/dst)
  ├─ PrepareCopy(src,dst)
  │    InitOutput.c:1736-1753
  │    ├─ lorieEnsureGpuSampleable(src, AHB)
  │    ├─ lorieEnsureGpuSampleable(dst, AHB)
  │    └─ lorieUnlockBgraAhb(src)
  ├─ Copy()
  │    InitOutput.c:1756-1790
  │    └─ lorieTryScheduleGpuCopy() / lorieTryScheduleGpuBlit()
  ├─ queue stores srcBufferId, dstBufferId, rects, offsets, serial
  └─ DoneCopy()
       waits completedSerial and calls lorieGpuCopyAck()
```

The renderer side is:

```text
lorieTryScheduleGpuBlit()
  ├─ lorieRegisterBuffer(srcBuffer)
  ├─ acquire + gpuCopyPendingInc(src)
  ├─ register/acquire/pending-inc destination
  └─ publish queue entry after __sync_synchronize()

Renderer::applyPendingGpuCopiesLocked()
  ├─ findBufferWithRetry(src/dst) by id
  ├─ attach registered buffers to GL
  ├─ bindTexture(src)
  ├─ disable blend for Copy
  ├─ drawRegion(... needsSwizzle = format mismatch)
  ├─ fence / flush
  └─ publish completedSerial
```

### Answers to the Copy questions

1. **How it finds source pixels:** EXA obtains the source pixmap with
   `exaGetDrawablePixmap()`. For this driver, `PrepareCopy()` makes the
   LorieBuffer GPU-sampleable. The renderer later finds the registered
   `LorieBuffer` by its `desc.id`, not by `sys_ptr`.
2. **Do REGULAR pixmaps convert:** yes, if `PrepareCopy()` sees
   `LORIEBUFFER_REGULAR`; it calls the same `lorieEnsureGpuSampleable()` and
   therefore the same REGULAR→AHB conversion.
3. **Why Copy can work while Composite is zero:** code alone does not prove
   that the two tested source pixmaps have identical provenance. The current
   Composite path additionally snapshots `priv->locked` after conversion into
   an FD. The Copy path unlocks the source AHB and lets the renderer upload
   the registered AHB. If conversion copied valid bytes, both should have
   nonzero source data; if conversion lost bytes, both should be bad. The
   observed split therefore requires S0/S1/S2 stamps or a test that proves
   the same source pixmap type and PutImage order on both paths.
4. **Reusable staging:** yes, there are two existing mechanisms:
   * REGULAR→AHB CPU copy in `LorieBuffer_convert()`.
   * Composite's FD snapshot in `lorieCloneBgraAhbToFd()` followed by the
     ordinary GPU queue/registration path. The FD snapshot is a valid staging
     transport only if its input mapping is proven nonzero first.
5. **Sync / lock differences:**
   * Copy explicitly calls `lorieUnlockBgraAhb(src)` after PrepareCopy.
   * Composite keeps the source AHB mapping live long enough to clone it,
     then uses the FD copy as the renderer source; DoneComposite releases the
     FD staging object but does not explicitly unlock the original source AHB.
   * Both queue paths use `gpuCopyPendingInc`, a shared state lock where
     `lorieNeedsGpuLock()` requires it, serial completion, and a renderer fence
     before ack.
6. **RGBX EGLImage vs BGRA sample/upload:**
   * RGBX AHBs can use EGLImage import in `LorieBuffer_attachToGL()`.
   * BGRA AHBs deliberately do not use EGLImage because the tested GPU sampled
     them black. They use `AHardwareBuffer_lock()` plus CPU
     `glTexImage2D(... GL_RGBA ...)`.
   * Composite FD staging is not an EGLImage: it allocates a stride-wide GL
     texture and updates it with `glTexSubImage2D(... GL_RGBA ...)`.

The Copy path is therefore a reusable resource/sync pattern, but it is not
proof that Composite's post-convert FD snapshot has valid bytes.

## 5. Format contract and assumptions

### CPU/X11 layout

On little-endian ARM64:

* An X11 numeric `a8r8g8b8` pixel `0xAARRGGBB` is stored as bytes
  `[B, G, R, A]`.
* An X11 numeric `x8r8g8b8` pixel `0x00RRGGBB` is stored as
  `[B, G, R, X]`; GetImage's X byte is expected to be zero in this gate.
* `fbPutZImage()` receives the client ZPixmap bytes and copies four-byte
  pixels using the destination `devKind` pitch.

### AHardwareBuffer and upload

The source code selects:

* depth >= 32: `AHARDWAREBUFFER_FORMAT_B8G8R8A8_UNORM` (constant 5 in
  `buffer.h`, documented in-tree as BGRA_8888);
* depth < 32: `AHARDWAREBUFFER_FORMAT_R8G8B8X8_UNORM`.

`uploadBgraAhbAsRgba()` locks BGRA AHB bytes and calls:

```text
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
             GL_RGBA, GL_UNSIGNED_BYTE, upload)
```

The CPU byte stream is still `[B,G,R,A]`; the GL upload format is explicitly
`GL_RGBA`, not `GL_BGRA_EXT`. If the AHB stride exceeds logical width, the
code tight-packs each row before upload. `LorieBuffer_bindTexture()` repeats
that CPU upload for BGRA AHBs and uses `glTexSubImage2D(... GL_RGBA ...)` for
FD buffers.

### Shader swizzle expectations

The two texture shaders are:

* normal: `texture2D(texture, outTexCoords)`;
* BGRA-flip: `texture2D(texture, outTexCoords).bgra`.

`drawRegion()` selects the BGRA-flip shader when `flip != 0`
(`renderer.cpp:1238-1260`). In the GPU queue:

```text
needsSwizzle = composite ? 0
                         : (LorieBuffer_isRgba(src) != LorieBuffer_isRgba(dst));
```

Thus Copy uses the format-mismatch swizzle decision, while Composite
explicitly forces `needsSwizzle = 0`. This is a separate format/render
contract issue from the current all-destination-unchanged failure. First make
the source nonzero; then validate red/blue with the smoke gate before any
broader oracle.

## 6. Instrumentation recommendation

These are observe-only stamps. They must not change ownership, locking,
formats, shader selection, Damage, or EXA dispatch.

### S0 — immediately before REGULAR conversion

Location: `src/f8-ahb/lorie/src/main/cpp/lorie/InitOutput.c`,
`lorieEnsureGpuSampleable()`, immediately before
`LorieBuffer_convert(priv->buffer, type, format)` at current line 144.

Record:

```text
pixmap pointer and drawable id/size/depth/bpp
buffer id, desc.type, desc.width/height/stride/format
priv->buffer, priv->locked, priv->mem
pPixmap->devPrivate.ptr and pPixmap->devKind
requested src_x/src_y and requested width/height
pixel_at_requested_xy from priv->locked (or desc.data if equivalent)
hash of the requested source rectangle using desc.stride
```

For the three smoke cases, all source requests can use `(0,0)`; for the
offset test, carry the operation's `srcX/srcY` into diagnostic context from
`lorieExaComposite()` before the call chain. Do not infer the pixel from
`sys_ptr`.

### S1 — new AHB mapped, before content copy

Location: `src/f8-ahb/lorie/src/main/cpp/lorie/buffer.c`, AHardwareBuffer
branch of `LorieBuffer_convert()`, after `AHardwareBuffer_describe(b, &desc)`
and successful `AHardwareBuffer_lock(b, ..., &data)`, immediately before
`pixman_blt()` at current line 271.

Record:

```text
old buffer id/type/data pointer
new AHardwareBuffer handle
desc.width/height/stride/format
mapped data pointer
pixel_at_requested_xy in the new mapping
lock return code
```

This stamp must distinguish `lock_rc != 0` from a legitimately zero-filled
new AHB.

### S2 — after conversion copy

Location: immediately after the `pixman_blt()` call and before the new AHB
unlock/old allocation free.

Record:

```text
source pointer and source stride
destination AHB mapping and destination stride
source requested pixel, destination requested pixel
source rectangle hash, destination rectangle hash
lock/copy status and whether the state transition will occur
```

This is the first boundary that can prove whether the existing copy actually
preserved the source. A zero S0 means PutImage/CPU ownership is wrong or the
requested coordinate is wrong. A nonzero S0 with zero S2 means conversion
lock/copy is the first bad boundary.

### S3 — immediately before texture upload/use

Locations:

* `buffer.c:480`, immediately before BGRA
  `glTexImage2D()`, record mapped CPU pixel, AHB stride, tight-packed
  stride, width/height, and upload format.
* `buffer.c:520`, immediately before FD `glTexSubImage2D()`, record
  `desc.data` pixel, FD stride, width/height, and upload format.
* `renderer.cpp:843-851`, immediately before `drawRegion()`, record source
  type/format, texture id, logical dimensions, UV divisor, and
  `needsSwizzle`.

S3 must identify whether the first bad byte is before GL upload or only after
sampling/blending.

### Required counter correlation

For every smoke case, emit a case id alongside:

```text
PrepareComposite count/result
Composite RECT count
DoneComposite count
GetImage result pixel/hash
S0/S1/S2/S3 stamps
```

Do not rely on global 1514-run counters to associate a pixel with a source.

## 7. Fail-fast `p2-b2-smoke` gate

The smoke gate is an XCB/XRender client run only on experimental `:3`.
It must create fresh pixmaps, issue PutImage, issue exactly one targeted
Composite, then GetImage. It must not start XFCE and must not query or touch
Stable `:1`.

Build/run shape:

```sh
cc -O2 -o /tmp/p2-b2-smoke /path/to/new/p2-b2-smoke.c -lxcb -lxcb-render
DISPLAY=:3 /tmp/p2-b2-smoke
```

The client should use the same `put32()`, `put24()`, premultiplied source
encoding, `xcb_render_composite_checked()`, and XCB GetImage byte decoding as
`patches/p_b2_oracle.c`. The smoke runner must print a unique case id before
each request so the server stamps can be correlated.

### Case 1: opaque red

```text
source: 1×1 depth 32, numeric 0xffff0000
destination: 1×1 depth 24, numeric 0x00000000
operation: PictOpOver, no mask, src=(0,0), dst=(0,0), size 1×1
expected RGB: 0x00ff0000
```

PASS requires:

* S0 source pixel is `ffff0000` (or the exact requested premultiplied
  representation as read from the backing bytes);
* S1/S2/staging source is nonzero and preserves red;
* PrepareComposite is true exactly once;
* one GPU RECT and one Done are observed;
* GetImage is red, with X byte zero.

### Case 2: alpha changes known destination

```text
source: 1×1 depth 32, premultiplied 0x80800000
         (straight red with alpha 0x80)
destination: 1×1 depth 24, numeric 0x000000ff
operation: same PictOpOver/no-mask 1×1
expected: ref_over_x8(source,destination), not original blue
```

Use the same `div255()` reference as the existing oracle. The important gate
is that the result differs from `0x000000ff` and matches the exact reference;
this catches a source-alpha-zero/no-op path even if Case 1 happens to be
special-cased.

### Case 3: historical real-sized path

```text
source: 5×24 depth 32, every pixel premultiplied 0x80800000
destination: 5×24 depth 24, known nonzero pattern
operation: PictOpOver/no-mask, src=(0,0), dst=(0,0), size 5×24
expected: per-pixel exact ref_over_x8()
```

This is the smallest required historical shape and catches row-pitch,
rectangle, and staging issues that 1×1 cannot catch.

### Gate rules

Run cases in order and stop immediately:

1. **S0 FAIL:** REGULAR requested pixel is zero/unexpected. Stop; do not run
   Case 2, Case 3, or the 1514 oracle. PutImage-to-REGULAR provenance is bad
   or the requested coordinate/hash is wrong.
2. **S1/S2/staging FAIL:** source becomes zero or changes unexpectedly across
   conversion/snapshot. Stop. The first failing boundary is the only boundary
   to fix.
3. **GPU path FAIL:** Prepare/RECT/Done counts do not match the case, or
   GetImage equals the original destination. Stop. Do not attribute this to
   shader swizzle until S3 is nonzero.
4. **Pixel FAIL:** source provenance and GPU path are good but exact RGB fails.
   Continue only with format/swizzle diagnosis. Do not widen to the 1514
   matrix yet.
5. **Smoke PASS:** all three cases have exact RGB, X byte zero, and the
   expected GPU counters. Only then run the existing
   `DISPLAY=:3 /tmp/p-b2-oracle` 1514-case gate.

## 8. Root-cause ranking from code evidence only

### #1 — conversion can discard valid REGULAR pixels when AHB lock/copy fails

Evidence:

* `buffer.c:270-273` performs `pixman_blt()` only inside the successful
  `AHardwareBuffer_lock()` branch.
* `buffer.c:276-283` changes type to AHB, frees `desc.data`, clears the
  REGULAR pointer, and clears lock state regardless of that lock/copy result.
* All 1515 current FD clones observe `px0=00000000` after the conversion
  boundary, which is consistent with an empty new AHB.

This is the strongest static failure mode, but the runtime lock return and
S0/S2 values are absent, so it is not yet a proven incident-level root cause.

### #2 — source provenance before conversion is not stamped and may be zero

Evidence:

* REGULAR allocation begins with `calloc(1, ...)` (`buffer.c:139-142`).
* PutImage is expected to write through `priv->locked`, but the current
  evidence only records the post-conversion mapping; it does not record
  `desc.data` immediately before conversion.
* `lorieCloneBgraAhbToFd()` copies from `priv->locked` after conversion
  (`InitOutput.c:1295-1328`), so `FDCLONE px0=0` cannot prove that PutImage
  wrote zero bytes.

This remains unresolved until S0 is nonzero for the exact requested
coordinate/rectangle.

### Not ranked as the first blocker: channel order/swizzle

The three APK results are “got equals original destination” with `maxΔ=255`,
and `Xnz=0`; that is a source/no-op symptom before a red/blue ordering
symptom. The format contract must still be validated after source provenance
passes.

## 9. Direct handoff to the implementation agent

```text
Implementation agent should modify ONLY:
  1. observe-only provenance stamps at the S0/S1/S2/S3 boundaries above;
  2. an independent p2-b2-smoke client/parser under the evidence or test path;
  3. if the stamps prove the conversion boundary bad, the smallest
     REGULAR→AHB copy/status-preservation code needed to retain the source;
  4. no Composite predicate broadening, no mask/two-pass/transform/repeat/
     bilinear work, no Damage/sys_ptr/PixmapIsOffscreen changes, and no
     Stable :1 interaction.

First expected observation:
  S0 must show LORIEBUFFER_REGULAR, non-NULL priv->locked/desc.data, and
  the requested source pixel/hash equal to the XCB PutImage pattern.

If S0 is correct and S2 is zero:
  The first bad boundary is LorieBuffer_convert's AHB lock/copy path.
  Record the AHardwareBuffer_lock return, preserve the old REGULAR allocation
  on failure, and do not continue to GPU upload.

If S0 is zero:
  Stop at the PutImage/REGULAR backing boundary. Inspect only the fb/EXA
  destination pointer, devKind, requested rectangle, and the source write;
  do not change renderer format or shader logic.

If S2 is correct and S3 is zero:
  The first bad boundary is staging/registration/upload. Compare the source
  pixel/hash, FD/AHB stride, upload dimensions, and GL_RGBA upload bytes.
  Check FD glTexSubImage2D versus BGRA AHB CPU upload without changing blend
  semantics.
```

## Completion answers

```text
PutImage pixels live at:
  fbBltStip()'s dst derived from pPixmap->devPrivate.ptr, which
  loriePrepareAccess() sets to priv->locked; for REGULAR,
  priv->locked == LorieBuffer_Desc.data (calloc backing).

REGULAR pixel pointer is:
  LorieBuffer_description(priv->buffer)->data, aliased by priv->locked
  while the REGULAR buffer is locked; pPixmap->devPrivate.ptr is only the
  transient EXA alias.

conversion uses:
  new AHardwareBuffer + AHardwareBuffer_lock + pixman_blt() from old
  REGULAR desc.data, then replaces/frees old backing and reacquires the AHB.
  The copy is conditional but replacement is currently unconditional.

existing Copy source path uses:
  exaHWCopyNtoN → lorieExaPrepareCopy → lorieEnsureGpuSampleable →
  lorieUnlockBgraAhb(source) → lorieTryScheduleGpuBlit/register-by-id →
  renderer texture upload/bind → FBO draw → fence/completedSerial/DoneCopy ack.

first likely divergence is:
  UNRESOLVED between S0 and S2. The highest code-evidenced candidate is
  AHardwareBuffer_lock/copy failure in LorieBuffer_convert followed by
  unconditional old-backing free; current FDCLONE proves only that the
  post-conversion mapping is zero.

best three smoke cases are:
  1×1 opaque red on black; 1×1 alpha-0x80 red over known blue; historical
  5×24 Over with exact per-pixel reference and GPU provenance counters.
```
