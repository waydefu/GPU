# Gate A P2 R7-P1 Present-target-arm CI artifact provenance — 2026-09-18 `abb27a65`

Parent `8545b26`. **Not installed in this packet.** Historical
`runtime-8545b26/r7-p1/` remains **INVALID / FROZEN**.

## BINDING (all exact)

```text
branch: fix/gatea-r7-p1-present-target-arm-20260918
worktree: src/f8-ahb-gatea-r7-p1-arm
parent: 8545b26b308aa60b05685f48560285350e22ee8d
local HEAD:  abb27a65b029b16837fe178624a85ac18a4ba005
remote fork: abb27a65b029b16837fe178624a85ac18a4ba005
CI run: 35253641841, workflow_dispatch, completed/success, single Build job
run headSha: abb27a65b029b16837fe178624a85ac18a4ba005
url: https://github.com/waydefu/termux-x11/actions/runs/35253641841
Build job: 105311807890 completed/success
Nightly Release: skipped (expected: not termux/termux-x11 master)
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
installed experimental at this packet: still 8545b26 until Phase C
```

Local HEAD = fork HEAD = CI headSha.

No local `assembleDebug` APK. Qualification uses this `workflow_dispatch` run only.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15300558 bytes
filename: termux-x11-universal-debug.apk
SHA256: b7baa1df5d7541efb993bf38f728846996b9c1601ad34b7f8eadd8128aa99d99
package: com.waydefu.x11gpu
versionName: 1.03.01-abb27a6-17.09.26
versionCode: 15
Build ID (embedded == unstripped): 7362d978c058ee2dac4cc8e60812dc3b3785f452
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
unzip -t: PASS
zipalign: NOT CLAIMED (host aarch64)
ABIs: arm64-v8a armeabi-v7a x86 x86_64
universal-debug artifact id: 10511737393
unstripped artifact id: 10512302130
GitHub zip digest is NOT APK SHA256
```

Report: `apk-elf-verification/p2-r7-p1-arm-apk-elf-report.json`

Previous installed APK SHA256 `92220845…377a` (`8545b26`) is a different file.

## MARKERS / SOURCE BINDING

Cxx rebuild (arm64 build log): `InitOutput.c.o` and `present_execute.c.o`.

Unstripped `nm`:

- `lorieTryScheduleGpuPresentCopy` **present**
- `lorieTryScheduleGpuBlit` **present**
- `gateAWaitTerminal` **present**
- `gateAXFatal` **present**
- `present_gpu_copy_retire_or_fatal` **present**
- `gateAHupPreserve` **present** (8545b26 ancestry)
- `lorieGateAClassifyWaitWake` **absent** (static inline)

Embedded strings:

- `present-hold-complete` / `present-renderer-exit`
- `x-hup` / `x-present-copy-wait` / `x-direct-not-success`
- `r-exit-after-consume` / `GATEA_HUP_PRESERVE` / `GATEA_FATAL_HALT`
- stall-phase diagnostic strings **absent**

Source binding:

- `abb27a65` → CI headSha `abb27a65` → APK `1.03.01-abb27a6-17.09.26` →
  Build ID `7362d978…f452` matching unstripped ELF
- protocol 40 / generationFatal offset 4 / version 1 / EVENT_MAX 37 /
  COUNTER_MAX 28 / Present wait 2000 ms / CASE_LOOP 8 ms unchanged
  (host verifiers PASS on the committed tree)

## Device

**NOT INSTALLED** in this packet. Phase C installs experimental-only.

## Verdict

**`R7_P1_VALIDITY_ARTIFACT_QUALIFIED`**
