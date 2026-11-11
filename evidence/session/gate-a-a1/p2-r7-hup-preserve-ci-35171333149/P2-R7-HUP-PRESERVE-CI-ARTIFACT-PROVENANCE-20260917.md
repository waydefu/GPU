# Gate A P2 R7-05 HUP-preserve CI artifact provenance — 2026-09-17 `a07d66c`

Parent `fdfb1ce`. **Not installed. No device run. Not R7 PASS. Not R7-05 PASS.**

## BINDING (all exact)

```text
branch: fix/gatea-r7-hup-fatal-preserve-20260917
worktree: src/f8-ahb-gatea-r7-hup-preserve
parent: fdfb1ce44b429897eda17c43bf33fbd37afe67f3
local HEAD:  a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82
remote fork: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82
CI run: 35171333149, workflow_dispatch, completed/success, single Build job
run headSha: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82
url: https://github.com/waydefu/termux-x11/actions/runs/35171333149
Build job: 105043446575 completed/success
Nightly Release: skipped (expected: not termux/termux-x11 master)
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
installed experimental: still fdfb1ce INSTALLED
```

Local HEAD = fork HEAD = CI headSha.

No local `assembleDebug` APK. Qualification uses this `workflow_dispatch` run only.

This packet qualifies the **build artifact**. It is **not** a device observation,
**not** R7-05 PASS, and **not** an install binding.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15299854 bytes
filename: termux-x11-universal-debug.apk
SHA256: a25861b41fe9088a7163e5d882909ca0a292780e418e1278665a436b27bface5
package: com.waydefu.x11gpu
versionName: 1.03.01-a07d66c-17.09.26
versionCode: 15
Build ID (embedded == unstripped): ad3509c0e64d4de3c7846117978881995b2543f2
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
unzip -t: PASS
zipalign -c 4: PASS
ABIs: arm64-v8a armeabi-v7a x86 x86_64
```

Report: `apk-elf-verification/p2-r7-hup-preserve-apk-elf-report.json`

Previous installed APK SHA256 `5313fc9a…915c` (`fdfb1ce`) is a different file.
GitHub artifact ZIP digest `3c3ca807…adcb` is **not** the APK SHA256.

## MARKERS / SOURCE BINDING

Present in both embedded and unstripped `libXlorie.so`:

- repair literal `GATEA_HUP_PRESERVE published=%u nonce=%llu generation=%llu`
- `x-direct-not-success` still present (R7-05 QUIESCED / genuine timeout)
- `x-observe-fatal` (R7-04 X preserve path)
- `r-gatea-DIRECT_LOOKUP_FAIL` (renderer R7-04 identity)
- `r-hup` / `x-hup` still present
- RCA-1 / CASE_LOOP literals: `x-exa-composite-wait`
- `GATEA_FATAL_HALT` / `GATEA_SUMMARY` / `TERMUX_X11_GATEA_TEST_FAULT`
- stall-phase diagnostic strings **absent**

Unstripped `nm -C`:

- `gateAHupPreserve(unsigned int, unsigned long, unsigned long)` **present**
- `present_gpu_copy_retire_or_fatal` present
- `lorieGateAClassifyPeerHup` **absent** (static inline; host C test compiles the header)

Source binding:

- `a07d66c` → CI headSha `a07d66c` → APK `1.03.01-a07d66c-17.09.26` →
  Build ID `ad3509c0…43f2` matching unstripped ELF
- `lorieGpuCopyWait(serial, 2000)` unchanged in source
- `LORIE_RENDERER_FRAME_WAIT_NS 8000000L` unchanged
- `sizeof(LorieGateAProtocol)==40` unchanged

## Device

**NOT INSTALLED.** No ADB cell in this task.
Historical R7-05 on `fdfb1ce` remains FAIL.
R7-04 on `fdfb1ce` remains PASS.
B-2 remains PASS.
