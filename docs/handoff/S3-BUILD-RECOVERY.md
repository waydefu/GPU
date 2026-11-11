# S3 Build-Recovery Ledger (all fixes verified by actual compiler invocations)

Every item below was reproduced from a clean state and verified fixed by the
real build invocation — never by weakening a gate. Pre-existing vs introduced
is marked per item. Nothing here changes rendering, routing, or fence semantics.

## CLOSED

### 1. setgid/setuid generated-macro ordering — PRE-EXISTING
- Symptom: `cmdentrypoint.cpp` (and every TU eating `dix-config.h` under
  `-DHAVE_DIX_CONFIG_H`): `unistd.h:192/247: expected identifier`, macro notes
  pointing at generated `dix-config.h:205-206` (`#define setgid(a) 0` before
  `#include <unistd.h>`).
- Root cause: committed `patches/dix-config.h.in` P2-A block defines the macros
  before the system includes, rewriting bionic's own prototypes.
- Fix: `patches/dix-config.h.in` — system includes first, defines after
  (exact approved diff). Location: recipe patch template (not upstream source).
- Validation: `cmdentrypoint.cpp.o` + `activity.cpp.o` built, zero errors.

### 2. EGL/GLES "missing headers" — FALSE ALARM (introduced by ad-hoc command)
- Symptom claimed: `EGL/egl.h` not found.
- Root cause of the claim: ad-hoc compile without `--sysroot`. The NDK r29
  sysroot provably contains EGL/GLES2/KHR.
- Fix: none needed; use the real build invocation. No headers were vendored.

### 3. `basename` without declaration (`shmem.c`) — PRE-EXISTING
- Symptom: clean build: `shmem.c:83: call to undeclared function 'basename'`.
- Root cause: `#ifdef ANDROID` (bare) is never true — NDK clang predefines only
  `__ANDROID__` — so `<libgen.h>` was never included. Old `.cxx` object was a
  fossil of a reverted temporary workaround.
- Fix: `lorie/shm/shmem.c:22`, 1 line: `#if defined(ANDROID) || defined(__ANDROID__)`.
- Validation: object builds; NDK `libgen.h` verified pristine (never touched).

### 4. tirpc `quad_t`/`u_quad_t` propagation — PRE-EXISTING
- Symptom: `xserver_os/rpcauth.c` via vendored `libtirpc/rpc/types.h`: unknown
  type name (bionic lacks BSD quad types; glibc `__quad_t` assumption fails).
- Root cause: build-recipe propagation defect — the `tirpc` target already
  carried `-Dquad_t="long long" -Du_quad_t="unsigned long long"`, but consumer
  target `xserver_os` did not. (A `types.h` typedef attempt was tried, proven
  wrong by collision with those same macros, and fully reverted.)
- Fix: `recipes/xserver.cmake` — mirror the two `-D`s onto `xserver_os`
  (exact approved diff; only consumer is `os/rpcauth.c`).
- Validation: `tirpc` + `xserver_os` build clean.

### 5. `memfd_create` Android API visibility — PRE-EXISTING
- Symptom: `xserver/Xext/shm.c:1221` undeclared identifier (bionic hides the
  declaration behind an API-30 guard; target is android-24; existing O_TMPFILE →
  mkostemp fallback preserved).
- Fix: `patches/xserver.patch` new hunk: `#if !defined(__ANDROID__) ||
  __ANDROID_API__ >= 30` around the call (approved; non-Android untouched).
- Validation: `shm.c.o` builds; fallback branch intact.

### 6. `present_scmd.c` duplicate + non-idempotent hunk — PRE-EXISTING (patch/tree drift)
- Symptom: `redefinition of 'lorieRecheckGpuCopies'`; full-file `patch -N`
  dry-run showed the retired hunk still forward-applicable (offset 30) — the
  hunk was never idempotent.
- Root cause: tracked tree and tracked patch both carried the function after a
  drift; reverse-detection failed so `-N` re-applied it.
- Fix: in-tree dedup to single definition + RETIRE hunk#1 from
  `patches/xserver.patch` (file headers restored completely); hunk#2
  (`after_flip`) kept.
- Validation: definition count = 1; reverse dry-run `--fuzz=0` clean;
  forward `-N` shows skip-only for the file.

### 7. SHMLBA qualification-toolchain guard — PRE-EXISTING
- Symptom: `xserver/Xext/xf86bigfont.c:723` undeclared `SHMLBA`; this NDK
  sysroot genuinely lacks the macro at every level (recursive grep, `-dM`
  dump, and header read all confirm — no header-routing defect).
- Fix: `patches/xserver.patch` capability-aware hunk:
  `#if !defined(CSRG_BASED) && !defined(__CYGWIN__) && (!defined(__ANDROID__) || defined(SHMLBA))`
  → falls back to the upstream `sysconf(_SC_PAGESIZE)` branch (page-size
  round-up use only; `<unistd.h>` already included; runtime page-size correct,
  including 16 KiB-page devices).
- Validation: object builds with zero errors (sysconf path proven taken).

## AGP / packaging

Packaging stage is DEFERRED and tracked independently from the native
compile/link investigation. No packaging blocker has been diagnosed; do not
conflate the two.
