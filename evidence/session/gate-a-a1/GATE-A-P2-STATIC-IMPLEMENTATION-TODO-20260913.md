# Gate A P2 bounded implementation TODO — 2026-09-13

Base: P1 HEAD `5e9eb2a`, worktree clean. D0a `a6cc795` clean, untouched.
Scope: 8 authorized blockers only. NO CI/APK/ADB/runtime/device/Stable/HDMI.

## Acceptance criteria

- [x] Renderer Gate A lookup miss never consumes/completes as success (FATAL).
- [x] All Gate A completion waits bounded (no EGL_FOREVER on Gate A path).
- [x] Wait/fence failure: no repair, no ACK, no pending--, no release, no relock.
- [x] Present OOM/scrap/early-ACK cannot bypass pair lease terminal boundary.
- [x] Queue indices + completedSerial use P0 accessors on every path (X + renderer).
- [x] Direct draw uses P1 READY registry only (tuple/state/retiring/imported/fatal
      checks); no legacy lookup/attach/bind, no CPU lock/clone/upload.
- [x] Source+destination pair ownership lease enforced end to end (reserve → publish →
      terminal → success-only release).
- [x] Post-publish uncertainty fail-stops (sticky failure/fatal, waiter wake,
      generation/session terminate, no replay, no D0a fallback).
- [x] `git diff --check` PASS; ARM64 native compile PASS; zero new warnings;
      default-OFF == D0a (no production call-site change when flag off).
- [x] HANDOFF + evidence doc updated; D0a untouched; no scope deviation
      (or explicitly listed mechanism-only deviation).

## Completion evidence

- Static: `GATE-A-P2-STATIC-IMPLEMENTATION-20260913.md`.
- Compile: incremental + full clean `:lorie:buildCMakeDebug[arm64-v8a]`
  BUILD SUCCESSFUL, 0 errors, 41 warnings all pre-existing lines/classes.
- Logs: `GATE-A-P2-NATIVE-BUILD-20260913.log` (incremental),
  `GATE-A-P2-NATIVE-BUILD-FULL-20260913.log` (full clean).
- Self-found in review: RGBX import gate (would have dead-ended direct),
  post-scheduled FALSE (would have raced GPU-owned pair), admit fresh-lock
  ptr restore.
- Mechanism note: no shared-state lock around unlock (monotonic + sticky
  checks are stable; `lorie_mutex_lock` is unbounded) — invariant unchanged.
- P2 STATIC: PASS. Production Gate A remains BLOCKED. No CI/runtime.
