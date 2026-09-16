# Gate A P2 stall-phase diagnostic CI artifact provenance — 2026-09-16 `27d8d1b`

Observe-only renderer SWAP / NEXT_FENCE markers. **Not installed. No device run.**

## BINDING (all exact)

```text
branch: diag/gatea-stall-phase-20260916
worktree: src/f8-ahb-gatea-stall-diag
parent: 0d72332c0e591b2137262d06d7dcab704be49383
local HEAD:  27d8d1b4fcfc5456bac8720d36110eeeb7cbc9d3
remote fork: 27d8d1b4fcfc5456bac8720d36110eeeb7cbc9d3
CI run: 35056388284, workflow_dispatch, completed/success, single Build job
run headSha: 27d8d1b4fcfc5456bac8720d36110eeeb7cbc9d3
url: https://github.com/waydefu/termux-x11/actions/runs/35056388284
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
repair worktree: 0d72332 UNCHANGED / still INSTALLED on device
```

Local HEAD = fork HEAD = CI headSha.

Nightly Release step skipped (expected: not `termux/termux-x11` master).

No local `assembleDebug` APK. Qualification uses this `workflow_dispatch` run only.

This packet qualifies the **build artifact**. It is **not** a device observation,
**not** B-2, **not** R7, and **not** an install binding.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15299634 bytes
filename: termux-x11-universal-debug.apk
SHA256: 142b6e1fc6856c87c8dac0a006dd13a97c963bd480f8c2ac548d88325c0a45b0
package: com.waydefu.x11gpu
versionName: 1.03.01-27d8d1b-16.09.26
versionCode: 15
Build ID (embedded == unstripped): e8d859dd25120e21d5be13f72ffc0a7dcf385e2c
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
ZIP testzip: PASS
STORED local-header mod4 failures: 0
ABIs: arm64-v8a armeabi-v7a x86 x86_64
```

Report: `apk-elf-verification/p2-stall-phase-apk-elf-report.json`

Previous repair APK SHA256 `13d7f42f…749e` is a different file (asserted).

## MARKERS / UNCHANGED SEMANTICS

Present in both embedded and unstripped `libXlorie.so`:

- `STALL_PHASE phase=`
- `SWAP_ENTER` / `SWAP_EXIT` / `NEXT_FENCE_ENTER` / `NEXT_FENCE_EXIT`
- repair literals: `x-exa-composite-wait`, `EXA GPU composite wait timeout`
- R6: `x-present-copy-wait`, `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL`
- `GATEA_FATAL_HALT` / `GATEA_SUMMARY`
- `TERMUX_X11_GATEA_TEST_FAULT` (getenv-only; `setenv` absent)

Unstripped `nm` contains `stallPhaseLog` and `present_gpu_copy_retire_or_fatal`.
`stallPhaseMonoNs` inlined (absent from nm; expected).

Source still has `lorieGpuCopyWait(serial, 2000)` and next-buffer
`eglClientWaitSync(..., EGL_FOREVER)`.

## Next

Device observation of SWAP vs NEXT_FENCE requires **new explicit authorization**.
Do not install this APK. Do not rerun B-2. Do not start R7. Device remains `0d72332`.
