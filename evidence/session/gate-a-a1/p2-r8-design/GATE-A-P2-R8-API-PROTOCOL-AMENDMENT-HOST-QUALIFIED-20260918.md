# GATE A P2 R8 API/PROTOCOL AMENDMENT HOST QUALIFIED — 2026-09-18

```
STATUS: R8_API_PROTOCOL_AMENDMENT_HOST_QUALIFIED
        R8_TEST_API_PROTOCOL_AMENDMENT_ACCEPTED
        LOCAL_NDK_PREFLIGHT_UNAVAILABLE
        no product-semantic change
        no shared Gate A ABI change
        CI 35304122983 / 35305368742 remain FAIL frozen
        R8 device NOT STARTED
        Production Gate A BLOCKED
```

Parent implementation remains `d382c0a96fb84330de939f415413f346fa4b5848`
(unamended at this packet). Historical design acceptance
`R8_DESIGN_ACCEPTED_ON_A4C8177` is unchanged. A01–A11 not rewritten.

Amendment record:
`evidence/session/gate-a-a1/p2-r8-design/GATE-A-P2-R8-TEST-API-PROTOCOL-AMENDMENT-20260918.md`

## Amendment A — shared vs X-only headers

`lorie_r8_test.h` is process-neutral: `stdint.h` + incomplete
`struct LorieBuffer` / `struct LorieGateABufferMeta`. No `PixmapPtr`,
`pixmap.h`, `pixmapstr.h`, or `lorie.h`.

X-only `lorie_r8_test_x.h` declares opaque `struct _Pixmap *` wrappers.
Not `void *`. Definitions in `InitOutput.c` keep `PixmapPtr`.

`cmdentrypoint.cpp` includes only `lorie_r8_test.h`.
`InitOutput.c` and `lorie_r8_test.c` include both.

Test wrapper `lorieGateAR8EnsureReadyForBuffer` returns `int` 0/1
(still calls `gateAEnsureReady`). No product-path change.

## Amendment B — protocol v1 layouts (pre-artifact)

`r8-test-protocol.h` includes `<X11/Xmd.h>` and defines structs
unconditionally. No `__X11_XMD_H` / `CARD8` heuristic. No local CARD
typedefs. Version remains **LORIE-R8-TEST 1.0**.

| Struct | sizeof == sz_* | reply.length |
| --- | ---: | ---: |
| QueryVersionReq | 4 | n/a |
| QueryVersionReply | **32** (`pad3` removed) | 0 |
| RegisterBufferReq | 8 | n/a |
| RegisterBufferReply | 72 | 10 |
| CheckpointReq | 8 | n/a |
| CheckpointReply | **72** (all named fields kept) | 10 |

Earlier proposed Checkpoint `sz_*=64` and QueryVersion `sizeof=36` were
internally inconsistent and never runtime-qualified.

`p_r8_lifecycle.c` uses `xcb_wait_for_reply` (no hardcoded 64-byte
client buffer). SHA256 unchanged
`ca52129288d5e0af68e56f72fe62125b1949926dd2d7fca6f0c8d07284c00954`.

## Host / self-containment

Shared-header host compile uses the grant snippet plus
`-I lorie/src/main/cpp/lorie` (no `LORIE_HOST_RECORD_DECODER_TEST`,
no Pixmap graph).

| Check | Result |
| --- | --- |
| shared C11 `lorie_r8_test.h` | PASS |
| shared C++17 | PASS |
| preprocess has no pixmap.h/pixmapstr.h | PASS |
| X-only opaque header without pixmap.h | PASS |
| X-only after local `typedef struct _Pixmap *PixmapPtr` | PASS (no conflict) |
| protocol alone C11 | PASS |
| protocol alone C++17 | PASS |
| Xmd → protocol | PASS |
| X.h → protocol | PASS |
| Xproto → protocol | PASS |
| protocol → Xproto | PASS |
| `sizeof == sz_*` + swapped QV/Checkpoint | PASS `/tmp/test_r8_protocol` |
| `test_r8_parser.py` | PASS |
| `p_r8_lifecycle --help` | PASS |
| judge vectors | **53 / 53** PASS `failures=0`; `device_cells=10` |
| GATEA_WAIT_WAKE_CLASS | PASS |
| GATEA_TEST_FAULT_CLASS (P1 held-incomplete / high-watermark) | PASS |
| GATEA_HUP_CLASS | PASS |
| R7_10_HUP_CONTAINMENT | PASS |
| R7_P1_PRESENT_TARGET_ARM | PASS |
| R7_HUP_PRESERVE | PASS |
| `verify-r8-support.py` | PASS `R8_SUPPORT_HOST_STATIC_OK` |
| d382c0a `lorieExaDestroyPixmap` prototype | kept |

Full `pixmapstr.h` after the X-only header is **unsupported on this
workstation** (not hacked): `os.h` needs `sigset_t`, `pixman.h` is
absent because `lorie/src/main/cpp/pixman` and `xorgproto` submodules
are empty here. Opaque `struct _Pixmap *` is the supported host form.

`lorie_r8_test.c` host TU syntax-check with real X include paths is
**UNAVAILABLE** for the same pixman/xorgproto hole. Reply types and
Pixmap wrappers are proven by the protocol `_Static_assert`s and the
split headers.

## Local NDK preflight

**LOCAL_NDK_PREFLIGHT_UNAVAILABLE**

- `ANDROID_HOME` / `ANDROID_NDK_HOME` unset
- `/usr/lib/android-sdk` has `build-tools` only (no `ndk/`)
- no `android-ndk*` under `/usr` `/opt` `/root` (maxdepth 4)
- `pixman` / `xorgproto` gitlinks empty in this worktree

Host self-containment still PASS. No invented NDK PASS. Continue to one
source commit + one fresh CI (not 35304122983 / 35305368742).

## Product / ABI freeze (unchanged)

READY, admission, completion, Present ACK/retirement, R7 faults, R8 A05
hooks, R8_OBS meaning, deferred product handling, shared protocol size,
generationFatal offset, protocolVersion, EVENT_MAX, COUNTER_MAX, 2000ms
product timeout, 8ms CASE_LOOP, judge-r7.

## Next

One commit on `d382c0a`. One new `workflow_dispatch` CI. Do not reinstall
`a4c8177` until the new artifact is qualified.
