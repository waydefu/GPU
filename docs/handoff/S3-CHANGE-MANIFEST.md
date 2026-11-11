# S3 Change Manifest (regenerated from live `git status`/`git diff --stat`)

```text
branch: f8-p2-b2-over
HEAD:   98224356e40913dcf2188d18748eba9401639850
```

| File | Class | Lines |
|---|---|---|
| `lorie/.../lorie/InitOutput.c` | B3A-INSTRUMENTATION | +142/-3 |
| `lorie/.../lorie/buffer.c` | B3A-INSTRUMENTATION + S3-E1/E1b dispatch call sites | +68/-5 B3a; E1/E1b replacements |
| `lorie/.../lorie/lorie.h` | B3A-INSTRUMENTATION | +5 |
| `lorie/.../lorie/renderer.cpp` | B3A-INSTRUMENTATION + S3-E1/E1b dispatch/fence call sites | +60/-5 B3a; E1/E1b replacements |
| `lorie/.../lorie/egl_dispatch.c` (new) | S3-E1 | typed EGL/GL PFN dispatch |
| `lorie/.../lorie/egl_dispatch.h` (new) | S3-E1 | dispatch API/types |
| `lorie/.../lorie/shm/shmem.c` | BUILDABILITY | 1 line |
| `lorie/.../patches/dix-config.h.in` | BUILDABILITY | reorder block |
| `lorie/.../patches/xserver.patch` | BUILDABILITY | memfd + SHMLBA hunks, scmd hunk retirement |
| `lorie/.../recipes/xserver.cmake` | BUILDABILITY + S3-E1 target source | quad_t -D + b3a build line + dispatch TU |
| `lorie/.../patches/x11.patch` | S3-X1 | named guards for dead client-side protocol code |
| `lorie/.../recipes/xkbcomp.cmake` | S3-X1 | target-scoped `XKBCOMP_NO_XLIB_PROTOCOL` |
| `lorie/.../lorie/b3a_telemetry.c` (new) | B3A-INSTRUMENTATION | new file |
| `lorie/.../lorie/b3a_telemetry.h` (new) | B3A-INSTRUMENTATION | new file |
| `.cache/` (untracked dir) | UNKNOWN (non-source residue) | n/a |

```text
ARCHITECTURE tracks = 2 approved (S3-E1/S3-X1); E1b is a narrow S3-E1 dispatch repair; rendering/routing/sync/library-topology semantics = 0
DOCUMENTATION changes (this round) = `docs/handoff/*.md` + `evidence/session/s3/GATE-S3-LINK.md`
```

Commit discipline (pending, not yet executed): portability/build fixes and B3a
instrumentation must land as separate commits; temporary workarounds, forensic
scripts, and formatting must not mix into qualification commits.
