# Luna D — Stride-safe Partial Upload

```text
session: 20260912_034739_85f27b
model: gpt-5.6-luna-900k
provider: openai-codex
reasoning: max
```

## CONCLUSION

Current FD path performs full `stride x height` GL_RGBA upload. Per-row upload and
a tightly packed span are technically viable without GL_UNPACK_ROW_LENGTH. The
only existing helper is glamor-specific and is not a direct LorieBuffer helper.

## OPTIONS

- **A — one call per row:** high correctness with explicit bounds and pointer arithmetic; no scratch allocation/copy; GL calls scale with row count.
- **B — tightly packed span:** high correctness with explicit overflow checks; extra pack allocation/copy; one GL call per span.
- **C — glamor helper:** capability-gated row-length/row-loop logic exists, but depends on glamor Pixmap/FBO state; high adaptation impact.

## EVIDENCE

- `buffer.h:21-27`: descriptor has width, height, stride, format, type, buffer, data.
- `buffer.c:142-165,228-233`: FD mapping and external stride preservation.
- `buffer.c:635-673`: FD texture allocated `stride x height`; current bind uploads all bytes as GL_RGBA.
- `InitOutput.c:1449-1505,1523-1565`: current cached/noncached paths copy every source row; D0a cached FD has stride==width.
- `renderer.cpp:857-907`: full bind precedes draw over entry rects; FD UV divisor is stride.
- `glamor_transfer.c:30-92`, `glamor.c:789-792`: only existing stride-safe helper and its unpack-subimage capability gate.

## LOWEST-RISK CANDIDATE

A, a narrow LorieBuffer-local per-row helper preserving GL_RGBA and avoiding a
scratch allocation. Row-call amplification requires measurement.

## UNKNOWN

Final rectangle aggregation and upload call count were not specified or measured.
No runtime test was run.

## ARCHITECTURE RISK FLAG

`SOL REVIEW`
