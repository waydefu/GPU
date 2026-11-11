# Gate A P2 notify-function-coverage diagnostic CI artifact provenance — 2026-09-16 `feeaa56`

Observe-only `NOTIFY_ENTER` / `NOTIFY_EXIT` inside `notifyGpuCopyDone()` so
every invocation is logged once. **Not installed. No device run.**

## BINDING (all exact)

```text
branch: diag/gatea-stall-notify-function-20260916
worktree: src/f8-ahb-gatea-notify-fn
parent: 1f85b803847e8522647c2bb7a4aba821428a606b
local HEAD:  feeaa569b86216126116c9bd99037a014efe0b79
remote fork: feeaa569b86216126116c9bd99037a014efe0b79
CI run: 35076884763, workflow_dispatch, completed/success, single Build job
run headSha: feeaa569b86216126116c9bd99037a014efe0b79
url: https://github.com/waydefu/termux-x11/actions/runs/35076884763
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
stall-phase worktree: 27d8d1b UNCHANGED
notify-diag worktree: 1f85b80 UNCHANGED / still INSTALLED on device
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
APK: 15299982 bytes
filename: termux-x11-universal-debug.apk
SHA256: a2d92ff9ecb948c5b3ac3c424727d12e97b9991f3b1b68d068a6828d744f3210
package: com.waydefu.x11gpu
versionName: 1.03.01-feeaa56-16.09.26
versionCode: 15
Build ID (embedded == unstripped): 62d4a3f66adf3326513b7b79868c21c3ad8310f2
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
ZIP testzip: PASS
STORED local-header mod4 failures: 0
ABIs: arm64-v8a armeabi-v7a x86 x86_64
```

Report: `apk-elf-verification/p2-stall-notify-fn-apk-elf-report.json`

Previous notify-diag APK SHA256 `bbe88f1b…9316` is a different file (asserted).
GitHub artifact ZIP digest `41572990…` is **not** the APK SHA256.

## MARKERS / UNCHANGED SEMANTICS

Present in both embedded and unstripped `libXlorie.so`:

- `STALL_PHASE phase=`
- `NOTIFY_ENTER` / `NOTIFY_EXIT`
- `SWAP_ENTER` / `SWAP_EXIT` / `NEXT_FENCE_ENTER` / `NEXT_FENCE_EXIT`
- repair literals: `x-exa-composite-wait`, `EXA GPU composite wait timeout`
- R6/R7 support: `x-present-copy-wait`, `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL`
- `GATEA_FATAL_HALT` / `GATEA_SUMMARY`
- `TERMUX_X11_GATEA_TEST_FAULT` (getenv-only; `setenv` absent)
- `COND_WAIT_ENTER` / `COND_WAIT_EXIT` **absent**

Unstripped `nm` contains `stallPhaseLog`, `notifyGpuCopyDone`, and
`present_gpu_copy_retire_or_fatal`.

Source still has `lorieGpuCopyWait(serial, 2000)` and next-buffer
`eglClientWaitSync(..., EGL_FOREVER)`. `activity.cpp` and `InitOutput.c`
are identical to `1f85b80`.

Host: `verify_exa_composite_wait.py` PASS; `verify_stall_phase_markers.py` PASS
on this tree; `git diff --check` PASS.

RED → GREEN: the same new verifier against parent `1f85b80` FAILs
`notify:function-body-not-instrumented`.

## Next

Device observation of function-body NOTIFY vs SWAP vs NEXT_FENCE requires
**new explicit authorization**. Do **not** install this APK. Do **not**
rerun `runtime-1f85b80/stall-obs-01`. Do **not** start B-2. Do **not** start R7.
Device remains `1f85b80`.
