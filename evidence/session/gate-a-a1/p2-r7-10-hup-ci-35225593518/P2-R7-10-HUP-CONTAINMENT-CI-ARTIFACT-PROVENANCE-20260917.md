# Gate A P2 R7-10 HUP-containment CI artifact provenance — 2026-09-17 `8545b26`

Parent `a07d66c`. **Not installed. No device run. Not R7-10 PASS. Historical FAIL frozen.**

## BINDING (all exact)

```text
branch: fix/gatea-r7-10-hup-containment-20260917
worktree: src/f8-ahb-gatea-r7-10-hup
parent: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82
local HEAD:  8545b26b308aa60b05685f48560285350e22ee8d
remote fork: 8545b26b308aa60b05685f48560285350e22ee8d
CI run: 35225593518, workflow_dispatch, completed/success, single Build job
run headSha: 8545b26b308aa60b05685f48560285350e22ee8d
url: https://github.com/waydefu/termux-x11/actions/runs/35225593518
Build job: 105216247505 completed/success
Nightly Release: skipped (expected: not termux/termux-x11 master)
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
installed experimental: still a07d66c INSTALLED
```

Local HEAD = fork HEAD = CI headSha.

No local `assembleDebug` APK. Qualification uses this `workflow_dispatch` run only.

This packet qualifies the **build artifact**. It is **not** a device observation
and **not** R7-10 PASS.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15300098 bytes
filename: termux-x11-universal-debug.apk
SHA256: 92220845a4cfff24eb47edef95664070d7bf60b159c01258e03b91d6a332377a
package: com.waydefu.x11gpu
versionName: 1.03.01-8545b26-17.09.26
versionCode: 15
Build ID (embedded == unstripped): 50a4078b940d982e1ca1484cac6dd2bf2abe7b0a
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
unzip -t: PASS
zipalign -c 4: PASS
ABIs: arm64-v8a armeabi-v7a x86 x86_64
```

Report: `apk-elf-verification/p2-r7-10-hup-apk-elf-report.json`

Previous installed APK SHA256 `a25861b4…ace5` (`a07d66c`) is a different file.

## MARKERS / SOURCE BINDING

Present in embedded `libXlorie.so`:

- `x-hup`
- `x-direct-not-success` (genuine live-peer timeout / QUIESCED path kept)
- `r-exit-after-consume`
- `GATEA_HUP_PRESERVE published=%u nonce=%llu generation=%llu`
- `x-observe-fatal`
- `GATEA_FATAL_HALT` / `GATEA_SUMMARY` / `TERMUX_X11_GATEA_TEST_FAULT`
- stall-phase diagnostic strings **absent**

Unstripped `nm -C`:

- `gateAWaitTerminal` **present**
- `gateAXFatal` **present**
- `present_gpu_copy_retire_or_fatal` present
- `gateAHupPreserve` present (prior R7-05 repair retained)
- `lorieGateAClassifyWaitWake` **absent** (static inline; host C test compiles the header)

Source binding:

- `8545b26` → CI headSha `8545b26` → APK `1.03.01-8545b26-17.09.26` →
  Build ID `50a4078b…7b0a` matching unstripped ELF
- `lorieGpuCopyWait(serial, 2000)` unchanged
- `elapsed > 2000` unchanged
- `LORIE_RENDERER_FRAME_WAIT_NS 8000000L` unchanged
- `sizeof(LorieGateAProtocol)==40` unchanged

## Device

**NOT INSTALLED.** No ADB cell in this task.
Historical `a07d66c` R7-10 remains **VALID FAIL / FROZEN**.
Do **not** retry `runtime-a07d66c/r7-10`.
Future requal is one R7-10 cell on **`8545b26` only**, after a separate grant.
