# Gate D0b-R2 Architecture Design — 2026-09-12

## SOURCE AUTHORITY

```text
repo: /root/projects/GPU加速/src/f8-ahb
branch: qualification/d0a-narrow-20260912
HEAD: a6cc7952861b8a63740d42bf78553573cfa0eec0
tracked diff: clean
R1 prototype: REJECTED / READ-ONLY EVIDENCE ONLY
```

Two independent read-only GPT-5.6 Luna Max scouts ran with
`--provider openai-codex --reasoning max`; Sol verified the decisive source and
OpenGL ES 2.0 error contract. No source mutation, build, commit, CI, APK, ADB, or
device operation occurred.

## CROSS-PROCESS MODE

```text
Renderer needs explicit D0b mode:             NO
Universal renderer region-upload path:        PROVEN for admitted in-bounds R3 Composite
Existing mode channel sufficient:             NOT NEEDED
New queue/shared-state semantics required:    NO for mode elimination
```

The existing `LorieGpuCopyEntry.op == LORIE_GPU_OP_COMPOSITE` is already a
cross-process semantic selector (`lorie.h:171-213`). It can select a universal
region-upload consumer path for all Composite FD staging, independent of whether
the producer performed a full D0a clone or a future partial D0b copy.

For D0a off one-shot and D0a on cached staging, Prepare has already copied the
full current source (`InitOutput.c:1422-1578,2145-2207`); uploading less cannot
change a draw that samples only the queued region. For future D0b, the producer
must copy that exact region before publication. A universal producer bounds gate
must ensure only positive in-bounds rectangles are published; current clean HEAD
does not yet contain that gate.

No renderer `getenv("TERMUX_X11_D0B")`, D0b queue bit, shared mode field, buffer
mode marker, or telemetry-as-control is needed or allowed.

## TEXTURE VALIDITY

Validity unit:

```text
R = exact union of an entry's admitted SOURCE rectangles in FD texture coordinates
```

Definition:

```text
VALID(texture, R)
=
every texel sampled from R was successfully uploaded from corresponding current
staging bytes after those bytes were copied and before the draw.
```

```text
VALID(texture, sampled_region):        NOT PROVEN end-to-end
Stale outside-region texels harmless:  PROVEN under narrow R3
```

Conditional data proof:

- FD texture storage is `stride x height`; a new texture may be NULL-initialized
  outside R (`buffer.c:635-662`).
- Queue/source rect endpoints directly define renderer UV endpoints
  (`InitOutput.c:2270-2305`, `renderer.cpp:885-907`).
- Composite forces `GL_NEAREST` (`renderer.cpp:1352-1374`) and rejects transform,
  repeat, bilinear, mask, and componentAlpha (`InitOutput.c:2077-2121`).
- Therefore fragments of an admitted in-bounds 1:1 draw sample R only. Texels
  outside R cannot affect the current draw; future draws are safe if they first
  refresh/upload their own sampled R.

The end-to-end invariant remains unproven because upload success itself is not
available to control the draw.

## UPLOAD FAILURE

```text
Prepublish elimination:              NOT PROVEN
Full-upload fallback:                NOT PROVEN
Skip-draw correctness:               NOT PROVEN (incorrect with current X flow)
Can stale texture ever be drawn:     YES under current fail-open continuation
Renderer→X failure result required:  YES for recoverable same-transaction failure
```

Producer admission can eliminate geometry, stride, rectangle count, and arithmetic
failures. It cannot prove that the renderer's FD mapping/texture object remains
available, nor can it eliminate GL runtime failure.

OpenGL ES 2.0.25 states:

- `TexSubImage2D` is void and modifies only its specified subregion (§3.7.2).
- Non-OOM GL errors cause the offending command to be ignored with no GL state or
  framebuffer effect; OOM results are undefined (§2.5).
- Errors are observed through `GetError`, not the upload return value.

Current `LorieBuffer_bindTexture` returns void and performs no success check
(`buffer.c:665-673`). Existing `checkGlError` only logs and returns locally
(`renderer.cpp:74-97`); it does not cancel/replay an X transaction. The EGL fence
and completedSerial prove GPU command completion, not semantic success of an
upload that GL ignored (`renderer.cpp:931-967`).

### Candidate A — make upload total before publication

Rejected. Deterministic D0b geometry can be made total, but renderer resource
survival and GL errors cannot be proven away by the producer.

### Candidate B — full upload fallback

The stale-outside-R concern is not the blocker: if full upload succeeds, current R
is valid and outside texels remain irrelevant. The blocker is that full upload uses
the same unavailable resource/void GL mechanism and has no proven success result.
It cannot be a universal same-transaction fallback.

### Candidate C — skip draw

Incorrect under the current contract. After publication, X has no way to replay or
CPU-fallback that Composite. Withholding completedSerial leads only to timeout/
liveness failure; publishing it falsely reports a missing operation as complete.

Thus preserving current-operation correctness after upload failure requires a new
renderer→X result/replay contract, which R2 explicitly forbids.

## LIFECYCLE

```text
Duplicate D0b DoneComposite path required:  NO
completedSerial semantics changed:          NO
ownership/fence semantics changed:          NO in the mode-elimination design
```

A future data-path design could reuse the existing Composite Done/wait/release
path rather than duplicate R1's D0b completion state machine. That does not solve
post-publication upload failure and therefore is not implementation authorization.

## R2 IMPLEMENTATION BOUNDARY

```text
NONE — implementation is not authorized.
```

Potentially valid but insufficient design facts are retained:

1. renderer can universally region-upload `op==COMPOSITE` without a D0b flag;
2. producer must universally reject out-of-bounds GPU Composite rectangles;
3. stale texture texels outside exact sampled R are harmless;
4. D0b need not duplicate DoneComposite lifecycle.

No source may be written until a same-transaction upload-failure contract is proven
without redefining queue/completedSerial/ownership/fence semantics.

## FINAL VERDICT

```text
D0b: HOLD
```

Hard conditions 4 and 5 are only conditional, and conditions 6 and 7 fail: upload
success is not guaranteed; safe replay/fallback needs a forbidden renderer→X
result channel.

Gate A remains `BLOCKED FOR CURRENT BGRA DIRECT-SAMPLING CONTRACT`.
Gate H remains `HOLD`.
Historical SIGSEGV remains `OBSERVED / NON-REPRODUCED / ROOT CAUSE UNKNOWN`.
Stable `com.termux.x11` / `DISPLAY=:1` was untouched.

## NEXT ACTION — ONE ONLY

```text
D0b-R3 design-only upload-totality gate: prove that renderer mapping, texture
attachment, and every GL region upload are total for all admitted Composite
entries without a result/replay channel; otherwise classify D0b BLOCKED under the
current no-new-protocol redlines.
```
