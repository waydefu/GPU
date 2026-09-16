# Gate A P2 R7 fatal-propagation CI artifact provenance — 2026-09-16 `fdfb1ce`

Parent `7549e36`. **Not installed. No device run. Not R7 PASS.**

## BINDING (all exact)

```text
branch: fix/gatea-r7-fatal-propagation-20260916
worktree: src/f8-ahb-gatea-case-loop
parent: 7549e3667ec03b8b5e50d2e5befe03065840bbd9
local HEAD:  fdfb1ce44b429897eda17c43bf33fbd37afe67f3
remote fork: fdfb1ce44b429897eda17c43bf33fbd37afe67f3
CI run: 35103216566, workflow_dispatch, completed/success, single Build job
run headSha: fdfb1ce44b429897eda17c43bf33fbd37afe67f3
url: https://github.com/waydefu/termux-x11/actions/runs/35103216566
Build job: 104817643231 completed/success
Nightly Release: skipped (expected: not termux/termux-x11 master)
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
device experimental: still 7549e36 INSTALLED
```

Local HEAD = fork HEAD = CI headSha.

No local `assembleDebug` APK. Qualification uses this `workflow_dispatch` run only.

This packet qualifies the **build artifact**. It is **not** a device observation,
**not** R7 PASS, and **not** an install binding.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15299566 bytes
filename: termux-x11-universal-debug.apk
SHA256: 5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c
package: com.waydefu.x11gpu
versionName: 1.03.01-fdfb1ce-16.09.26
versionCode: 15
Build ID (embedded == unstripped): 1d6bf3cd0eb06d12804e690679211ee7f34f998e
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
ZIP testzip: PASS
STORED local-header mod4 failures: 0
ABIs: arm64-v8a armeabi-v7a x86 x86_64
```

Report: `apk-elf-verification/p2-r7-fatal-propagation-apk-elf-report.json`

Previous installed APK SHA256 `45500894…4bc3` (`7549e36`) is a different file (asserted).
GitHub artifact ZIP digest `0a1e6700…99ff` is **not** the APK SHA256.

## MARKERS / UNCHANGED SEMANTICS

Present in both embedded and unstripped `libXlorie.so`:

- repair literal `x-observe-fatal` (X preserve path; not a second halt `what`)
- `x-direct-not-success` still present (R7-05 QUIESCED / genuine timeout)
- `r-gatea-DIRECT_LOOKUP_FAIL` (renderer R7-04 identity)
- RCA-1 / CASE_LOOP literals: `x-exa-composite-wait`, 2000 ms wait, 8 ms idle cap
- `GATEA_FATAL_HALT` / `GATEA_SUMMARY` / `TERMUX_X11_GATEA_TEST_FAULT`
- stall-phase diagnostic strings **absent**

Unstripped `nm -C` contains `present_gpu_copy_retire_or_fatal`.
`lorieGateAClassifyDirectDone` is `static inline` — **absent from nm** (expected;
host C test compiles the production header).

Source binding:

- `fdfb1ce` → CI headSha `fdfb1ce` → APK `1.03.01-fdfb1ce-16.09.26` →
  Build ID `1d6bf3cd…998e` matching unstripped ELF
- `lorieGpuCopyWait(serial, 2000)` unchanged
- `LORIE_RENDERER_FRAME_WAIT_NS 8000000L` unchanged
- `sizeof(LorieGateAProtocol)==40` unchanged

## Device

**NOT INSTALLED.** No ADB cell in this task.
Historical R7-04 on `7549e36` remains FAIL.
