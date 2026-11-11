# Gate A P2 R7-P1 Present-hold-terminal CI artifact provenance — 2026-09-18 `a4c8177`

Parent `abb27a65`. **Not installed in this packet.** Historical
`runtime-abb27a65/r7-p1/` remains **INVALID / FROZEN**. Historical
`runtime-8545b26/r7-p1/` remains **INVALID / FROZEN**.

## BINDING (all exact)

```text
branch: fix/gatea-r7-p1-present-target-arm-20260918
worktree: src/f8-ahb-gatea-r7-p1-arm
parent: abb27a65b029b16837fe178624a85ac18a4ba005
local HEAD:  a4c8177f4b059fddd111717255e9d23cf0e15e1e
remote fork: a4c8177f4b059fddd111717255e9d23cf0e15e1e
CI run: 35295094951, workflow_dispatch, completed/success, single Build job
run headSha: a4c8177f4b059fddd111717255e9d23cf0e15e1e
url: https://github.com/waydefu/termux-x11/actions/runs/35295094951
Build job: 105445903790 completed/success
Nightly Release: skipped (expected: not termux/termux-x11 master)
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
judge SHA: fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17 UNCHANGED
```

Local HEAD = fork HEAD = CI headSha. First attempt. No CI retry.

No local `assembleDebug` APK. Qualification uses this `workflow_dispatch` run only.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15317074 bytes
filename: termux-x11-universal-debug.apk
SHA256: 91a4b74eff2c54cceba89ca3b8f8530442fa371fd7a67523eaf8bbd73c75a55c
package: com.waydefu.x11gpu
versionName: 1.03.01-a4c8177-18.09.26
versionCode: 15
Build ID (embedded == unstripped): dcd8297497c38f6b277cc9cbdb74b2eea06dba60
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
unzip -t: PASS
zipalign: NOT CLAIMED (host aarch64)
ABIs: arm64-v8a armeabi-v7a x86 x86_64
universal-debug artifact id: 10528490453
unstripped artifact id: 10528095908
GitHub zip digest is NOT APK SHA256
```

Report: `apk-elf-verification/p2-r7-p1-hold-apk-elf-report.json`

Previous installed APK SHA256 `b7baa1df…9d99` (`abb27a65`) is a different file.

## MARKERS / SOURCE BINDING

Cxx rebuild (arm64): `InitOutput.c.o` and `present_execute.c.o`.

Unstripped `nm`:

- `lorieGpuCopyIsDone` **present**
- `lorieTryScheduleGpuPresentCopy` **present**
- `present_gpu_copy_retire_or_fatal` **present**
- `gateAHupPreserve` **present**
- `lorieGateATestFaultHoldsIncomplete` **absent** (static inline; expected)
- `lorieGateAClassifyWaitWake` **absent** (static inline; expected)

Embedded strings include `present-hold-complete` / `present-renderer-exit` /
`x-present-copy-wait` / `x-hup` / `GATEA_HUP_PRESERVE`. Stall-phase
diagnostic strings **absent**.

ABI freeze: protocol 40 / generationFatal offset 4 / version 1 /
EVENT_MAX 37 / COUNTER_MAX 28 / Present wait 2000 ms / CASE_LOOP 8 ms.

## Device

Not installed in this packet.
