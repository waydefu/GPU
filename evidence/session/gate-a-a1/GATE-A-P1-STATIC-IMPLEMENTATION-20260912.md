# Gate A P1 static implementation — 2026-09-12

## SOURCE

```text
branch: qualification/gatea-a1-microprobe-20260912
base:   97401bce514fa7d43be80df271e163669f849746 (preserved, not amended)
worktree: /root/projects/GPU加速/src/f8-ahb-gatea-a1
D0a:    qualification/d0a-narrow-20260912 / a6cc795, untouched
```

## DIFF

```text
lorie/src/main/cpp/lorie/InitOutput.c      |  57 +++++
lorie/src/main/cpp/lorie/activity.cpp      | 145 +++++++++++++
lorie/src/main/cpp/lorie/buffer.c          |  31 +++
lorie/src/main/cpp/lorie/buffer.h          |  16 ++
lorie/src/main/cpp/lorie/cmdentrypoint.cpp | 328 +++++++++++++++++++++++++++++
lorie/src/main/cpp/lorie/lorie.h           |  57 +++++
lorie/src/main/cpp/lorie/renderer.cpp      | 297 ++++++++++++++++++++++++++
7 files changed, 933 insertions(+), 0 deletions(-)
```

Purely additive. `git diff --check`: PASS.

What each file carries:

- `lorie.h`: P1 cross-TU decls, `lorieGateAFatalHalt`, shared `lorieGateAReleaseAhb`.
- `InitOutput.c`: `sys/random.h`+`stdint.h` includes, OsVendorInit nonce
  (raw `syscall(SYS_getrandom)`, exact-length, fail = disabled), share-time
  generation bump + poison + registry sweep, `lorieGateAShared`,
  `lorieGateAActive`.
- `cmdentrypoint.cpp`: X registry + waiter pool, send mutex, framed REGISTER
  send, atomic MarkChecked, input-thread magic dispatch, HUP supplement.
- `activity.cpp`: bound tuple, share-time bind, magic dispatch, REGISTER
  consume + AHB handoff, HUP supplement bypassing the blocking rendezvous.
- `renderer.cpp`: pending/ready pools, enqueue, GL-thread drain + validation,
  READY/FAILED send under one writer mutex, flag-guarded threadLoop hook.
- `buffer.c`/`buffer.h`: availability-guarded raw AHB release + checked
  raw-handle send (direct NDK calls stay in this TU: minSdk 24 vs API-26).

## STATIC CHECKLIST

- ABI exact size/offset: PASS (P0 asserts intact and still compiling).
- Atomics/lock-free: PASS (no new shared fields; all access via accessors).
- Release/acquire centralized: PASS (one verified exception class: pre-share
  single-threaded init writes, documented).
- First failure / fatal sticky, single authority: PASS (publish sites only
  add information, never clear).
- Fatal wakeup reachable: PASS (broadcast + waiter primitives wired in both
  HUP supplements and input dispatch).
- Queue entry ABI: UNCHANGED. completedSerial: UNCHANGED (zero touches).
- Default OFF: PASS (every new runtime path flag-gated; OFF == D0a).
- Production behavior: UNCHANGED when OFF (additive diff, no call-site change).
- No imported enablement / replay / D0b / Gate H: confirmed absent.
- No new volatile sync; no TODO/FIXME; no dead statics (one found and removed
  during review: uncalled unbind helper).
- Name collisions: all new symbols unique to their TUs.
- Lock discipline: registry/send/waiter mutexes are leaves; registry→waiter is
  the only nesting order; no state->lock held while waiting.
- Self-found and fixed during review: TOCTOU between Find and Mark (merged into
  atomic MarkChecked, weak Mark deleted); duplicate-READY relied on a later
  observer (now CASes fatal inline with state passed in); unbound-magic spin
  hazard (dispatch requires bound); fatal-path inconsistency for malformed
  frames (uniform active→halt / inactive→drop).

## NATIVE COMPILE

Three runs, `:lorie:buildCMakeDebug[arm64-v8a]`, `--no-daemon --no-build-cache`:

1. First: FAILED on 3 real defects — direct API-26 NDK calls outside buffer.c
   (`AHardwareBuffer_release` in a header inline, `sendHandleToUnixSocket` in
   cmdentrypoint) and hidden `getrandom` wrapper. Fixed per file conventions
   (buffer.c guarded wrappers; raw `syscall(SYS_getrandom)` per InitOutput
   precedent).
2. Incremental re-run: BUILD SUCCESSFUL; 1 new warning (availability-guard
   style) → fixed by nesting the ifs.
3. Full clean rebuild: BUILD SUCCESSFUL, 41 warnings, all proven pre-existing
   classes (xserver/lib/shm third-party-ish, keycode designators, format,
   reorder, GLX, Gradle minify). Zero from P1 code.

Logs: `GATE-A-P1-NATIVE-BUILD-20260912.log` (incremental),
`GATE-A-P1-NATIVE-BUILD-FULL-20260912.log` (full clean).

## SCOPE

No P3 admission, unlock transition, queue publication, sampling, Done/Destroy/
CloseScreen changes, imported support, replay, entry/completedSerial changes.
No CI, APK, ADB, device, runtime, Stable, or HDMI operation.
