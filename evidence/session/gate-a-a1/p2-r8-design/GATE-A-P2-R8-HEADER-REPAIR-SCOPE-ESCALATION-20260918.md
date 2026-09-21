# GATE A P2 R8 HEADER REPAIR SCOPE ESCALATION — 2026-09-18

```
STATUS: R8_HEADER_REPAIR_SCOPE_ESCALATION
        no source commit under this grant
        no new CI
        R8 device cells NOT RUN
        Production Gate A BLOCKED
```

This is a **new** freeze. It does not rewrite:

- `GATE-A-P2-R8-CI-FAIL-20260918.md` (CI **35304122983** / `bc25170`)
- `GATE-A-P2-R8-CI-FAIL-D382C0A-20260918.md` (CI **35305368742** / `d382c0a`)

Worktree remains `d382c0a96fb84330de939f415413f346fa4b5848` (parent `bc25170`). Prototype forward declaration of `lorieExaDestroyPixmap` is **kept**. No amend.

## Why this grant cannot HOST_QUALIFY

The authorized repair is **type / include / layout visibility only**, plus mandatory host tests:

1. `lorie_r8_test.h` self-contained `PixmapPtr`
2. `r8-test-protocol.h` self-contained via `<X11/Xmd.h>`
3. `sizeof(actual struct) ==` frozen `sz_*`

(2) is visibility-true. (1) cannot use the preferred `#include "pixmap.h"` in the shared header. (3) fails for two replies **without changing named protocol fields**.

Changing named checkpoint fields, or changing frozen `sz_*`, is **beyond** this grant.

## PixmapPtr — source review (preferred include rejected)

Pinned provider: `lorie/src/main/cpp/xserver/include/pixmap.h`

```
74: typedef struct _Drawable *DrawablePtr;
75: typedef struct _Pixmap *PixmapPtr;
```

That file is **not** pointer-only. It includes:

- `"misc.h"` → `"os.h"` (`sigset_t` / POSIX thread mask)
- `"regionstr.h"` → `"miscstruct.h"` → `<pixman.h>`
- `<X11/extensions/randr.h>`

Host probe of `#include "pixmap.h"` (xserver include dir, even with `<signal.h>` first): `os.h:726` unknown `sigset_t`, then fatal `pixman.h` missing (pixman submodule **not** checked out on this workstation; `git submodule status` shows `-9cc163c9… pixman`).

Shared consumers of `lorie_r8_test.h`:

| TU | Language | Already has full Xlorie include graph? |
| --- | --- | --- |
| `InitOutput.c` | C | yes |
| `lorie_r8_test.c` | C | yes on Android CI |
| `cmdentrypoint.cpp` | C++ | yes on Android CI; includes this header for non-Pixmap APIs (`lorieGateAR8CopyRegistry`, host inject) |

`pixmap.h` therefore **cannot safely be consumed by every translation unit that includes `lorie_r8_test.h`**, including the mandatory host tiny TU, without the full generated Xlorie include graph (pixman, POSIX, dix-config). The grant forbids substituting `void *`.

Allowed next-grant alternatives (not executed here):

- split: `lorie_r8_test.h` process-neutral + `lorie_r8_test_x.h` X-only wrappers that include `pixmap.h` only in C X TUs; **or**
- guarded incomplete typedef identical to `pixmap.h:75` (`typedef struct _Pixmap *PixmapPtr`) when `PIXMAP_H` is not already defined.

Do **not** include `pixmapstr.h` / `windowstr.h` / `scrnintstr.h` into the shared header.

## Protocol / Xmd — visibility RCA confirmed

System `/usr/include/X11/Xmd.h` include guard is **`XMD_H`**, not `__X11_XMD_H`.

`CARD8` is a **typedef** (`typedef unsigned char CARD8;`), not a macro. `defined(CARD8)` is false even after a correct `Xmd.h` include.

That matches CI **35305368742**: `xLorieR8QueryVersionReply` not visible.

Preferred visibility fix (not committed here because sizeof gate fails):

```c
#include <X11/Xmd.h>
```

then define the layouts **without** `#if defined(__X11_XMD_H) || defined(CARD8)`.

Do not invent `CARD8`/`BYTE` aliases. Do not invent `__X11_XMD_H`.

## Protocol sizeof vs frozen sz_ (host probe)

Probe: `/tmp/r8_sz_probe.c` with `#include <X11/Xmd.h>` and the current struct bodies (ifdef stripped). gcc host:

| Struct | sizeof | frozen sz_ |
| --- | ---: | ---: |
| `xLorieR8QueryVersionReq` | 4 | 4 |
| `xLorieR8QueryVersionReply` | **36** | **32** |
| `xLorieR8RegisterBufferReq` | 8 | 8 |
| `xLorieR8RegisterBufferReply` | 72 | 72 |
| `xLorieR8CheckpointReq` | 8 | 8 |
| `xLorieR8CheckpointReply` | **72** | **64** |

QueryVersion extra: trailing `CARD32 pad3` (4 bytes) beyond a 32-byte `length /* 0 */` reply.

Checkpoint extra: **16** body `CARD32`s after the 8-byte X reply header = 72. Frozen 64 with comment `length /* 8 extra dwords */` is **14** body `CARD32`s. All 16 body fields are **named** (`phase` … `generationLo/Hi`). Dropping two named fields is a test-protocol layout decision, not include visibility.

`lorie_r8_test.c` uses `WriteToClient(client, sizeof(rep), &rep)` while REGISTER/CHECKPOINT set `rep.length` from `sz_*`. Visibility-only un-hiding of the oversized structs would compile CI and then send **sizeof** bytes that disagree with frozen `sz_*`.

This grant forbids changing frozen lengths / field widths / field order. Matching `sizeof == sz_` for checkpoint therefore **requires a named-field freeze**. **STOP.**

## Prototype repair retained

`InitOutput.c:2003`:

```c
void lorieExaDestroyPixmap(ScreenPtr pScreen, void *driverPriv);
```

Not removed. Not re-signed. CI **35305368742** already built `InitOutput.c.o`.

## What was not done

- no source commit on top of `d382c0a`
- no push
- no new CI (do not rerun **35304122983** / **35305368742**)
- no artifact / install / device cells
- no R9

## Next grant (report only)

Must explicitly authorize, in one commit:

1. `<X11/Xmd.h>` + delete the broken `CARD8`/`__X11_XMD_H` gate
2. `PixmapPtr` via split X header or guarded `pixmap.h:75` typedef (not `void *`, not shared `pixmap.h` include)
3. **explicit** checkpoint/QV struct freeze so `sizeof == sz_*` (QV drop extra pad **or** keep 36 and change frozen 32 — pick one; checkpoint pick which two body words leave the 64-byte reply)
4. host: protocol standalone + include-order + C11/C++17 + 53 judge vectors + R7 regressions
5. one new CI; do not rerun the two frozen fails
