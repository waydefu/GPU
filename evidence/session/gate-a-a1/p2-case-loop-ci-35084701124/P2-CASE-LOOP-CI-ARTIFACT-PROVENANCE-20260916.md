# Gate A P2 CASE_LOOP hardened CI artifact provenance — 2026-09-16 `7549e36`

Hardened CASE_LOOP wakeup candidate. **Not installed. No device run.**
**Not B-2. Not R7.**

## BINDING (all exact)

```text
branch: fix/gatea-case-loop-wakeup-20260916
worktree: src/f8-ahb-gatea-case-loop
parent: 0d72332c0e591b2137262d06d7dcab704be49383
initial CASE_LOOP: 327b02838009eca8bac127ca7bb381fd2aff48ed
local HEAD:  7549e3667ec03b8b5e50d2e5befe03065840bbd9
remote fork: 7549e3667ec03b8b5e50d2e5befe03065840bbd9
CI run: 35084701124, workflow_dispatch, completed/success, single Build job
run headSha: 7549e3667ec03b8b5e50d2e5befe03065840bbd9
url: https://github.com/waydefu/termux-x11/actions/runs/35084701124
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
notify-fn worktree: feeaa56 UNCHANGED / still INSTALLED on device
repair worktree: 0d72332 UNCHANGED
R7 worktree: a7528bd UNCHANGED
```

Local HEAD = fork HEAD = CI headSha.

Nightly Release step skipped (expected: not `termux/termux-x11` master).

No local `assembleDebug` APK. Qualification uses this `workflow_dispatch` run only.

This packet qualifies the **build artifact**. It is **not** a device observation,
**not** B-2, **not** R7, and **not** an install binding.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15299506 bytes
filename: termux-x11-universal-debug.apk
SHA256: 45500894023208963b3b1cd51fb7f3aa61807a25e1d70b322f7a7fdad7e14bc3
package: com.waydefu.x11gpu
versionName: 1.03.01-7549e36-16.09.26
versionCode: 15
Build ID (embedded == unstripped): 4c5b7b86c18ec4e9bb14720c4615a25c1d6a8f81
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
ZIP testzip: PASS
STORED local-header mod4 failures: 0
ABIs: arm64-v8a armeabi-v7a x86 x86_64
```

Report: `apk-elf-verification/p2-case-loop-apk-elf-report.json`

Previous diagnostic APK SHA256 `a2d92ff9…3210` (`feeaa56`) is a different file (asserted).
GitHub artifact ZIP digest `3f7318b7…2022b8` is **not** the APK SHA256.

## MARKERS / UNCHANGED SEMANTICS

Present in both embedded and unstripped `libXlorie.so`:

- repair literals: `x-exa-composite-wait`, `EXA GPU composite wait timeout`
- R6/R7 support: `x-present-copy-wait`, `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL`
- `GATEA_FATAL_HALT` / `GATEA_SUMMARY`
- `TERMUX_X11_GATEA_TEST_FAULT` (getenv-only; `setenv` absent)
- `COND_WAIT_ENTER` / `COND_WAIT_EXIT` **absent**
- stall-phase diagnostic strings **absent** (this tree is `0d72332`-based, not `feeaa56`)

Unstripped `nm -C` contains `present_gpu_copy_retire_or_fatal` and
`Renderer::waitWhileIdle`.

Source binding:

- `lorieGpuCopyWait(serial, 2000)` unchanged; no 3000/5000 workaround
- `LORIE_RENDERER_FRAME_WAIT_NS 8000000L` (idle recheck, not EXA timeout)
- sticky `ObserveWriteIndex` before `pthread_cond_timedwait`
- `clock_gettime(CLOCK_MONOTONIC)` deadline; `CLOCK_REALTIME` absent from idle
- `pthread_condattr_setclock(..., CLOCK_MONOTONIC)` + PROCESS_SHARED; abort on failure

Host: `verify_exa_composite_wait.py` PASS; `verify_case_loop_wakeup.py` PASS;
host wakeup RED 151 ms / GREEN 10 ms (`-std=c11 -Wall -Wextra -Werror`);
`git diff --check` PASS. TSan toolchain present but **TSAN NOT RUN**
(PRoot `FATAL: unexpected memory mapping`).

## Next

Device validation of this hardened candidate requires **new explicit
authorization**. Do **not** install this APK. Do **not** rerun
`runtime-feeaa56/stall-obs-01`. Do **not** start B-2. Do **not** start R7.
Device remains `feeaa56`.
