# GATE A P2 R8 TEST API / PROTOCOL AMENDMENT — 2026-09-18

```
STATUS: R8_TEST_API_PROTOCOL_AMENDMENT_ACCEPTED
        test-support only
        before first successful R8 artifact
        A01–A11 not rewritten
```

This is an **additive** amendment. Historical
`GATE-A-P2-R8-DESIGN-ACCEPTANCE-20260918.md` (`R8_DESIGN_ACCEPTED_ON_A4C8177`)
remains immutable. Historical CI FAIL packets **35304122983** and
**35305368742** remain FAIL.

| Field | Value |
| --- | --- |
| Parent implementation | `d382c0a96fb84330de939f415413f346fa4b5848` |
| R7 final | `a4c8177f4b059fddd111717255e9d23cf0e15e1e` |
| Production Gate A | BLOCKED |
| R8 device | not started |

Frozen wait precedence unchanged:
SUCCESS already derived > published generationFatal > peer HUP > live-peer genuine timeout.

`d382c0a` prototype remains:
`void lorieExaDestroyPixmap(ScreenPtr pScreen, void *driverPriv);`

## Amendment A — split Pixmap-dependent API

`lorie_r8_test.h` is process-neutral. It must not mention `PixmapPtr`,
`PixmapRec`, `pixmap.h`, or `pixmapstr.h`. It also must not include
`lorie.h` (Android/EGL/X server graph). Consumers such as
`cmdentrypoint.cpp` already include `lorie.h` themselves.

Shared declarations use `struct LorieBuffer *` / `struct LorieGateABufferMeta *`
and `stdint.h` only.

X-only wrappers live in `lorie_r8_test_x.h`, consumed only by X-side TUs
(`InitOutput.c`, `lorie_r8_test.c`). Opaque form:

```c
struct _Pixmap;
LorieBuffer *lorieGateAR8EnsureGpuSampleableAhb(struct _Pixmap *pixmap);
int lorieGateAR8PixmapReject(struct _Pixmap *pixmap);
```

Not `void *`. Definitions may keep `PixmapPtr` where full X headers exist
(`PixmapPtr` == `struct _Pixmap *`). No duplicated implementations.

`cmdentrypoint.cpp` includes only `lorie_r8_test.h`.

## Amendment B — Xmd self-containment + pre-artifact v1 layout freeze

Remove `#if defined(__X11_XMD_H) || defined(CARD8)`.
`r8-test-protocol.h` includes `<X11/Xmd.h>` and defines layouts
unconditionally. No local CARD8/CARD16/CARD32/BYTE typedefs.

There has been **no** qualified/installed R8 protocol artifact. Protocol
remains **LORIE-R8-TEST** major **1** minor **0**. Earlier proposed
Checkpoint `sz_*=64` and QueryVersion `sizeof=36` were internally
inconsistent and never runtime-qualified.

| Struct | sizeof / sz_* | notes |
| --- | ---: | --- |
| QueryVersionReq | 4 | unchanged |
| QueryVersionReply | **32** | drop redundant `pad3`; `length=0` |
| RegisterBufferReq | 8 | unchanged |
| RegisterBufferReply | 72 | unchanged named fields; `length=10` |
| CheckpointReq | 8 | unchanged |
| CheckpointReply | **72** | keep all named body CARD32s; `length=10` |

Invariant: `sizeof(struct) == sz_*`. Replies: `length == (sizeof-32)/4`
(0 when sizeof==32). Compile-time `_Static_assert` / `static_assert`.

Named Checkpoint fields retained (occupancy and registryCount both kept).

## Not in this amendment

Normal Gate A product path, READY, admission, completion, Present
ACK/retirement, R7 faults, R8 A05 hooks, R8_OBS meaning, deferred product
handling, shared Gate A ABI, timeouts, judge-r7.
