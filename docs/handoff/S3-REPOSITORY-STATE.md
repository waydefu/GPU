# S3 Repository State (verified read-only; nothing modified by this inventory)

## Main working tree (`src/f8-ahb`, experimental target)

| Item | Value |
|---|---|
| repo path | `/root/projects/GPU加速/src/f8-ahb` (the project root itself is NOT a git repo; work per-worktree) |
| branch | `f8-p2-b2-over` |
| HEAD full SHA | `98224356e40913dcf2188d18748eba9401639850` |
| HEAD short | `9822435` |
| HEAD date/subject | 2026-09-08 06:59:57 +0800, `fix(diag): close provenance conditional` |
| upstream tracking | NOT OBSERVED (not queried in this pass; do not assume) |
| `git status` | 10 modified tracked files + 4 untracked source files + 1 untracked `.cache/` dir |
| `git diff --check` | PASS |

### Change classification (verified `git status` + `git diff --stat`)

```text
10 files changed, 416 insertions(+), 62 deletions(-)
```

| File | Class |
|---|---|
| `lorie/.../lorie/InitOutput.c` (+142/-3) | B3A-INSTRUMENTATION |
| `lorie/.../lorie/buffer.c` (+68/-5 B3a; E1 replacements) | B3A-INSTRUMENTATION + S3-E1 |
| `lorie/.../lorie/lorie.h` (+5) | B3A-INSTRUMENTATION |
| `lorie/.../lorie/renderer.cpp` (+60/-5 B3a; E1 replacements) | B3A-INSTRUMENTATION + S3-E1 |
| `lorie/.../lorie/egl_dispatch.c` (new) | S3-E1 typed EGL/GL PFN dispatch |
| `lorie/.../lorie/egl_dispatch.h` (new) | S3-E1 dispatch API/types |
| `lorie/.../lorie/shm/shmem.c` (1 line) | BUILDABILITY (bare-`ANDROID` → `defined(ANDROID)\|\|defined(__ANDROID__)`) |
| `lorie/.../patches/dix-config.h.in` | BUILDABILITY (setgid/setuid ordering) |
| `lorie/.../patches/xserver.patch` | BUILDABILITY (memfd guard + SHMLBA guard + scmd hunk retirement) |
| `lorie/.../recipes/xserver.cmake` | BUILDABILITY + S3-E1 (`egl_dispatch.c` build source) |
| `lorie/.../patches/x11.patch` | S3-X1 named guards for dead client-side protocol code |
| `lorie/.../recipes/xkbcomp.cmake` | S3-X1 target-scoped `XKBCOMP_NO_XLIB_PROTOCOL` |
| `lorie/.../lorie/b3a_telemetry.c` (new) | B3A-INSTRUMENTATION |
| `lorie/.../lorie/b3a_telemetry.h` (new) | B3A-INSTRUMENTATION |
| `.cache/` (untracked dir) | UNKNOWN (build/IDE residue; NOT source; do not ship) |

```text
ARCHITECTURE tracks = 2 approved (S3-E1/S3-X1); rendering/routing/sync/library-topology semantics = 0
```

R3 predicate / semantics untouched: Over-only, ARGB→XRGB, no mask/transform/
bilinear/repeat/componentAlpha; fail-closed fallback intact.

### Submodule pins (main tree, verified `git submodule status`; pins unchanged; patch-applied source state recorded below)

```text
bzip2      6a8690fc (bzip2-1.0.8)
libepoxy   c84bc945 (1.5.10)
libfontenc 780d1f6f (libfontenc-1.1.9)
libtirpc   5ca4ca92 (libtirpc-1-2-7-rc4)
libx11     6c75545a (libX11-1.8.13)
libxau     a9c65683 (libXau-1.0.12)
libxcvt    dd8631c6 (libxcvt-0.1.3)
libxdmcp   1192d3bc (libXdmcp-1.1.5)
libxfont   88b9df88 (libXfont2-2.0.8)
libxkbfile 42e5dedd (libxkbfile-1.2.0)
libxshmfence 89f06474 (libxshmfence-1.3.3)
libxtrans  cf05ba4a (xtrans-1.6.0)
pixman     9cc163c9 (pixman-0.46.4)
xkbcomp    2c778978 (xkbcomp-1.5.0)
xorgproto  fcb7e9a1 (xorgproto-2025.1)
xserver    65d790bd (xorg-server-21.1.24)
```

Note: `libx11` working copy shows `M src/KeyBind.c, M src/Quarks.c, M src/Xrm.c,
M src/xkb/XKBGeom.c` — these are the existing `patches/x11.patch` hunks plus
S3-X1 named-guard hunks applied in-tree by the build's own `patch -N` flow
(expected steady state, not foreign edits).

## Pristine forensic worktree (`/tmp/b3a-pristine-r3`)

| Item | Value |
|---|---|
| path | `/tmp/b3a-pristine-r3` (registered git worktree, detached HEAD) |
| HEAD | `98224356e40913dcf2188d18748eba9401639850` (identical to baseline) |
| submodules | all verified at superproject pins, zero network (`--no-fetch`; missing local objects would have stopped the procedure, none missing at point of use) |
| local env | untracked `local.properties` (`sdk.dir=/root/android-sdk`), mirroring main |
| dirty state | ONLY approved buildability re-landings (setgid `.in`, quad_t `.cmake`, memfd/SHMLBA `.patch` hunks, scmd hunk retirement, shmem guard) — zero rendering/B3a changes |

Wording discipline (binding): NEVER write "pristine committed tree clean-links
and fails". Correct: **R3 baseline + only approved buildability repairs
reproduced the same 19 unresolved symbols under the current toolchain.**

Prior residue found and neutralized here: an earlier session's half-slimmed
submodule checkouts (deleted metafiles, then wrong-commit checkouts) were
restored to pins from local objects; no fetch was performed.
