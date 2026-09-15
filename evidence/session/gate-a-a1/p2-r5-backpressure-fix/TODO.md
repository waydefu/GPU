# Gate A P2 R5 backpressure correction TODO

Base: `d9b7f60f24e722205891f1ce941816393ae4c695`
Branch: `fix/gatea-r5-backpressure-20260915`
Worktree: `/root/projects/GPU加速/src/f8-ahb-gatea-r5-fix`

## Scope

- Fix normal PROTO callback under-drain of incremental records.
- Remove Gate A completion notification writes from the `state->lock` critical section in both standalone and redraw completion paths.
- Preserve wire/shared/queue ABI, 2000 ms waiter budget, fence ordering, `completedSerial` semantics, ownership, predicate, PROTO-OFF behavior, Stable, HDMI, D0a/D0b/Gate H.
- Do not change generic `lorie_mutex_lock` clock/recovery semantics in this correction.

## Acceptance criteria

- [x] RED regression fails on exact `d9b7f60` for normal callback phase drain and Gate A notify-under-lock.
- [x] Normal PROTO callback continues across `INCOMPLETE` decoder phases and complete records until nonblocking `WOULD_BLOCK`; fatal/error handling remains fail-closed.
- [x] Gate A `notifyGpuCopyDone()` executes only after `state->lock` release in standalone and redraw paths.
- [x] Fence completion and `completedSerial` publication remain before notification; legacy/PROTO-OFF notification placement stays unchanged.
- [x] Existing decoder socketpair suite passes against edited source.
- [x] R5 backpressure regression passes, including same-kernel tiny-write capacity evidence.
- [x] Existing X-pump contract verifier passes.
- [x] `git diff --check` passes.
- [x] ARM64 incremental and full-clean native builds pass with zero new warnings versus baseline.
- [x] Final diff review and independent Luna review pass.
- [x] Conventional Commit records root cause and verification. (commit 37d8393)
- [x] Fork push, exact-source multi-ABI CI and artifact qualification pass before any device action. (run 34918397208, SHA256 31ec7037..., Build ID cc8cee05...)
- [x] Stop and notify user before ADB/install/device/runtime testing. (STOP HERE; awaiting user authorization)
- [x] Corrected-artifact R5 PASS (user 2026-09-15): hang FALSIFIED, 4096 pixel exact ×2. Follow-logcat ack=4095 recorded as capture-drop, not blocking. R6–R8 still STOP.

## Completion evidence

Static implementation authority:
`GATE-A-P2-R5-STATIC-IMPLEMENTATION-20260915.md`.
Artifact qualification authority:
`../p2-r5-backpressure-ci-34918397208/P2-R5-BACKPRESSURE-CI-ARTIFACT-PROVENANCE-20260915.md`.

Current boundary: 37d8393 installed; R5 PASS; R6 bounded client PASS;
design-complete R6 not claimed; STOP before R7.
`../p2-r3-xpump-runtime/runtime-37d8393/GATE-A-P2-R6-RUNTIME-20260915.md`.
