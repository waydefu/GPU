# Gate A P2 stall-notify diagnostic CI artifact provenance — 2026-09-16 `1f85b80`

Observe-only renderer `NOTIFY_ENTER` / `NOTIFY_EXIT` around the post-completion
`notifyGpuCopyDone()` that sits before `SWAP_ENTER`. **Not installed. No device run.**

## BINDING (all exact)

```text
branch: diag/gatea-stall-notify-20260916
worktree: src/f8-ahb-gatea-notify-diag
parent: 27d8d1b4fcfc5456bac8720d36110eeeb7cbc9d3
local HEAD:  1f85b803847e8522647c2bb7a4aba821428a606b
remote fork: 1f85b803847e8522647c2bb7a4aba821428a606b
CI run: 35063553801, workflow_dispatch, completed/success, single Build job
run headSha: 1f85b803847e8522647c2bb7a4aba821428a606b
url: https://github.com/waydefu/termux-x11/actions/runs/35063553801
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
stall-phase worktree: 27d8d1b UNCHANGED / still INSTALLED on device
```

Local HEAD = fork HEAD = CI headSha.

Nightly Release step skipped (expected: not `termux/termux-x11` master).

No local `assembleDebug` APK. Qualification uses this `workflow_dispatch` run only.

This packet qualifies the **build artifact**. It is **not** a device observation,
**not** B-2, **not** R7, and **not** an install binding.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15299742 bytes
filename: termux-x11-universal-debug.apk
SHA256: bbe88f1be8e00724409d51d8660639c048e46495e8cab5e7e2d0e97418319316
package: com.waydefu.x11gpu
versionName: 1.03.01-1f85b80-16.09.26
versionCode: 15
Build ID (embedded == unstripped): d0d9d9242a37b9655447b2fba65f79d4950ff79a
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
ZIP testzip: PASS
STORED local-header mod4 failures: 0
ABIs: arm64-v8a armeabi-v7a x86 x86_64
```

Report: `apk-elf-verification/p2-stall-notify-apk-elf-report.json`

Previous stall-phase APK SHA256 `142b6e1f…45b0` is a different file (asserted).
GitHub artifact ZIP digest `a8792ef2…` is **not** the APK SHA256.

## MARKERS / UNCHANGED SEMANTICS

Present in both embedded and unstripped `libXlorie.so`:

- `STALL_PHASE phase=`
- `NOTIFY_ENTER` / `NOTIFY_EXIT`
- `SWAP_ENTER` / `SWAP_EXIT` / `NEXT_FENCE_ENTER` / `NEXT_FENCE_EXIT`
- repair literals: `x-exa-composite-wait`, `EXA GPU composite wait timeout`
- R6: `x-present-copy-wait`, `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL`
- `GATEA_FATAL_HALT` / `GATEA_SUMMARY`
- `TERMUX_X11_GATEA_TEST_FAULT` (getenv-only; `setenv` absent)
- `COND_WAIT_ENTER` / `COND_WAIT_EXIT` **absent**

Unstripped `nm` contains `stallPhaseLog` and `present_gpu_copy_retire_or_fatal`.

Source still has `lorieGpuCopyWait(serial, 2000)` and next-buffer
`eglClientWaitSync(..., EGL_FOREVER)`. `notifyGpuCopyDone()` body is identical
to `27d8d1b`. `activity.cpp` is identical to `27d8d1b`.

Host: `verify_exa_composite_wait.py` PASS; `verify_stall_phase_markers.py` PASS;
`git diff --check` PASS. Parent tree without NOTIFY markers FAILs the new verifier.

## Next

Device observation of NOTIFY vs SWAP vs NEXT_FENCE requires **new explicit authorization**.
Do **not** install this APK. Do **not** rerun B-2. Do **not** start R7.
Device remains `27d8d1b`.
