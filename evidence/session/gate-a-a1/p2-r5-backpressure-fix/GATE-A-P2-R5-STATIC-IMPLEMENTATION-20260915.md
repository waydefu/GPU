# Gate A P2 R5 backpressure correction — static implementation

Date: 2026-09-15

## Status

```text
ROOT CAUSE: PROVEN
SOURCE: COMMITTED 37d839323255b4830d657da3bcbf7f616bc78ad3
BRANCH: fix/gatea-r5-backpressure-20260915 (pushed to fork)
BASE: d9b7f60f24e722205891f1ce941816393ae4c695
R5 REGRESSION: RED ON BASE / GREEN ON WORKTREE
HOST DECODER: PASS
X-PUMP CONTRACT: PASS
ARM64 INCREMENTAL: PASS
ARM64 FULL-CLEAN: PASS / 41 WARNING FINGERPRINTS == d9b7f60 BASELINE / 0 NEW
INDEPENDENT REVIEW: PASS
COMMIT / PUSH / CI / ARTIFACT: DONE (CI run 34918397208 PASS, ARTIFACT QUALIFIED)
ADB / INSTALL / DEVICE / RUNTIME: DONE (experimental only)
R5 CORRECTED-ARTIFACT QUALIFICATION: PASS (hang FALSIFIED; 4096 pixel exact; follow-logcat ack=4095 capture-drop not blocking per 2026-09-15 user grant)
R6–R8: CONDITIONALLY AUTHORIZED AFTER R5 PASS / NOT STARTED
```

No PR, origin push, Stable, or HDMI operation occurred.

## Root cause addressed

The normal PROTO notifier called `lorieRecordDecoderNext()` only once. A queued
24-byte `EVENT_GPU_COPY_DONE` therefore needed separate main-loop wakeups for
its 4-byte PREFIX and 20-byte BASE. Tiny records accumulated until AF_UNIX
`sk_buff` accounting blocked the renderer's notification writer while it held
`state->lock`. X observed shared `completedSerial`, reached RELOCK_DST, then
needed the same lock for 24bpp repair and could no longer run the sole socket
reader.

Authority:
`../p2-r3-xpump-runtime/runtime-d9b7f60/GATE-A-P2-R5-DEADLOCK-20260915.md`.

## Changes

Only two source files changed:

1. `lorie/src/main/cpp/lorie/cmdentrypoint.cpp`
   - `handleLorieEventsProto` now continues across decoder `INCOMPLETE` phases
     and complete records until the nonblocking receive reports
     `WOULD_BLOCK`.
   - Existing PROGRESSED dispatch, active-generation fatal handling, inactive
     close/reset, deferred WorkProc ownership, and PROTO-OFF parser remain.
   - A post-record `conn_fd != fd` guard prevents continued draining after a
     synchronous close/rebind.
2. `lorie/src/main/cpp/lorie/renderer.cpp`
   - `gateAFencePublishGateA` now returns whether it actually published
     `completedSerial`; it no longer writes the socket itself.
   - Standalone and redraw Gate A notifications occur immediately after
     `state->lock` release.
   - Non-Gate/legacy notification placement remains inside the existing branch.
   - Finite fence, sticky fatal, first-failure, completed watermark, ownership,
     queue, predicate, fallback, and timeout semantics are unchanged.

Diff stat:

```text
lorie/src/main/cpp/lorie/cmdentrypoint.cpp | 56 +++++++++++++++++++-----------
lorie/src/main/cpp/lorie/renderer.cpp      | 34 +++++++++++-------
2 files changed, 58 insertions(+), 32 deletions(-)
```

## TDD evidence

RED on exact base `d9b7f60`:

```text
KERNEL_CAPACITY=sndbuf=229376 writes=299 payload=7176 outq=229632
R5_BACKPRESSURE=FAIL
FAIL callback:missing-drain-loop
FAIL callback:incomplete-phase-not-continued
FAIL callback:would-block-not-terminal
FAIL renderer:gate-helper-notifies-under-lock
FAIL renderer:gate-helper-does-not-report-publication
FAIL renderer:standalone-missing-notify-state
FAIL renderer:standalone-gatea-notify-before-unlock
FAIL renderer:redraw-missing-notify-state
FAIL renderer:redraw-gatea-notify-before-unlock
exit 1
```

GREEN on the edited worktree:

```text
KERNEL_CAPACITY=sndbuf=229376 writes=299 payload=7176 outq=229632
R5_BACKPRESSURE=PASS
CALLBACK_DRAIN=PASS
GATEA_NOTIFY_AFTER_UNLOCK=PASS
exit 0
```

Verifier:
`verify_r5_backpressure_fix.py` in this evidence directory.

## Verification

```text
python3 verify_r5_backpressure_fix.py --repo <worktree>
exit 0

clang -std=gnu11 -Wall -Wextra -g -DLORIE_HOST_RECORD_DECODER_TEST \
  -I<worktree>/lorie/src/main/cpp/lorie \
  ../p2-r3-xpump-implementation/decoder-host/xpump_decoder_socketpair_test.c \
  -o /tmp/r5-xpump-decoder-test && /tmp/r5-xpump-decoder-test
PASS production decoder socketpair tests
exit 0

python3 ../p2-r3-xpump-implementation/verify_xpump_contract.py \
  --repo <worktree>
XPUMP_CONTRACT=PASS
STATIC_INVARIANTS=PASS
SOCKETPAIR_MODELS=PASS
exit 0

git diff --check
exit 0

env LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE=C.UTF-8 \
  ANDROID_HOME=/root/android-sdk \
  ./gradlew ':lorie:buildCMakeDebug[arm64-v8a]'
BUILD SUCCESSFUL
exit 0
```

Full-clean evidence: `arm64-full-clean.log`.
Programmatic comparison against
`../p2-r3-xpump-implementation/ARM64-FULL-CLEAN-POST-EINTR-FIX-20260915.log`:

```text
base_warning_lines=41
new_warning_lines=41
new_fingerprints=[]
missing_fingerprints=[]
error_lines=0
```

Two setup/test-command observations are not source failures:

- The first linked-worktree configure failed because Git worktrees do not
  populate submodule checkouts. Exact pinned submodules were initialized, then
  incremental and full-clean builds passed.
- An improvised host-harness command with `-Werror` failed on the pre-existing
  unused keycode table in `lorie.h`. Re-running with the harness Makefile's
  recorded flags passed. No warning policy was changed.

## Review

Independent Luna review: **PASS**, no proven correctness finding. It confirmed:

- no decoder no-progress spin under current phase machine;
- active/inactive error behavior retained;
- finite fence and `completedSerial` precede notification;
- sticky fatal suppresses publication and notification;
- Gate A notifications are after `state->lock` release in both paths;
- legacy/PROTO-OFF placement is unchanged;
- no ABI, timeout, predicate, fallback, ownership, or generic mutex change.

Residual AMBER note: reconnect/fd-number reuse remains a broader global-decoder
lifecycle concern. This diff adds a post-record identity guard but does not
redesign generation-bound fd identity.

## Documentation impact

Updated: R5 authority, runtime handoff, root handoff, test matrix, this static
implementation record, and an additive A1 decoder-drain erratum. Historical
R5 FAIL cells remain immutable.

## Next boundary

R5 PASS recorded. STOP before R6 unless a new explicit grant names R6.
R7 still requires its missing fault hook in an independently reviewed artifact.

Later (2026-09-15): bounded R6 CLIENT_OK ran; design-complete R6 is written
(`../p2-r6-design/GATE-A-P2-R6-DESIGN-20260915.md`) and is **not** authorized
to implement. This R5 document does not grant that source change.
