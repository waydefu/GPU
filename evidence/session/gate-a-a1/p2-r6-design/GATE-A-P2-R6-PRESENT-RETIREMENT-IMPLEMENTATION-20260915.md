# Gate A P2 R6 Present GPU-copy retirement — implementation record

Date: 2026-09-15 22:00 UTC+8

```text
STATUS: SOURCE+HOST VERIFIED / UNCOMMITTED / NOT R6 PASS
WORKTREE: src/f8-ahb-gatea-r6-retire
BRANCH: fix/gatea-r6-present-retirement-20260915
BASE: 95e6f9602b0146ee190870f84a34aad822ef666f
PARENT DIRTY: lorie/src/main/cpp/patches/xserver.patch
CI / INSTALL / ADB / R7: NOT DONE
```

This records the writer-lane C that exists on disk. It does not authorize
commit, push, CI, or device cells. Tests were not modified in the close-out
that produced this packet.

## Helper

`void present_gpu_copy_retire_or_fatal(present_vblank_ptr vblank)` in
`present_vblank.c`, declared in `present_priv.h`.

Order: NULL vblank → FatalError; `!gpu_copy_pending` → return; save serial;
`serial==0` or `!lorieGpuCopyIsDone` → `lorieGpuCopyWaitForPresentOrFatal`;
then the sole present raw `lorieGpuCopyAck(pixmap, dst_buffer)` (NULL dest is
legal root); then clear pending／dst／serial.

Callers: `present_vblank_scrap` and `present_vblank_destroy` call the helper
before idle／pixmap drop. `present_execute_copy` already-pending and
post-schedule requeue-failure paths use it. Natural requeue failure emits
event 33, helper, event 34 using scalars saved before ACK. Renderer stall
calls helper only (fail-stop must not release).

`gpu_copy_pending=TRUE` is set immediately after successful
`lorieTryScheduleGpuCopy`. Event 32 remains declaration-only.

## Host gates (re-run 2026-09-15, tests unmodified)

```text
test-judge-r6-design.py          37/37 OK
test-r6-design-bind.sh           BIND_NEG=PASS
verify_r6_design_impl.py         R6_DESIGN_IMPL=PASS
test-present-gpu-copy-retirement PRESENT_RETIREMENT=PASS
bash -n r6 design scripts        exit 0
git diff --check (writer)        exit 0
p_r6_d2_present.c -Werror        exit 0
```

ARM64 incremental and full-clean native builds previously succeeded on this
worktree. They were not re-run after the 20:56 markdown-only Hermes turn.

## Remaining before commit

1. Normalize `xserver.patch`: merge retirement hunks into the existing Present
   sections; do not leave a second `+++ ./present/present_execute.c` at EOF.
2. Independent architecture review (not the session that wrote the helper).
3. Parent updates `HANDOFF.md` / `TEST-MATRIX.md` / `AGENTS.md` only after that
   review. This packet does not do it.

## Not proven

Timeout, renderer-loss fail-stop, scrap/destroy/CloseScreen runtime,
D2-OOM device, D1/D2 on a retirement APK.
