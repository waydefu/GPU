# GATE A P2 R8 ARTIFACT QUALIFIED — b984ded / 35347497216 — 2026-09-18

```
STATUS: R8_XCB_SENDER_ARTIFACT_QUALIFIED
        package com.waydefu.x11gpu
        X END still only at ddxGiveUp
        test-only Terminate opcode 3 → GiveUp(0) → DE_TERMINATE
        host fixture now sends extension minors via libxcb
        protocol v1 layouts QV32 / Register72 / Checkpoint72 unchanged
        Production Gate A BLOCKED
        NOT INSTALLED this packet
```

## Binding

```text
source: b984dedcac731b77ca4cf8899f8a78b7848ad083
parent: fb4f017c73e942e13dc2423744acb912c055b74e
CI: 35347497216 workflow_dispatch success
headSha: b984dedcac731b77ca4cf8899f8a78b7848ad083
universal-debug artifact id: 10547527477
unstripped artifact id: 10547752137
filename: termux-x11-universal-debug.apk
size: 15346450
SHA256: 0d06de68025ca41d91e316d55f6f77ba9d5b3ba1a90b6a2bfacb65add0d398d3
package: com.waydefu.x11gpu
versionName: 1.03.01-b984ded-18.09.26
versionCode: 15
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
Build ID embedded == unstripped: 3658dd1f8047bfbb9d4671b269305313adaf1aa7
unzip -t: PASS (archive opened; GitHub zip digest is NOT APK SHA256)
zipalign: NOT CLAIMED
native-code: arm64-v8a armeabi-v7a x86 x86_64
```

## Provenance (embedded arm64 libXlorie.so)

FOUND (byte search / strings, not behavior):

- `LORIE-R8-TEST`
- `"op":"TERMINATE"`
- `R8_OBS_POST_END role=%s phase=%s`
- `R_SURFACE_QUIESCED`
- `X_CLOSE_ENTER`
- `x-destroy-in-lease`

Unstripped `nm`: `ddxGiveUp`, `GiveUp`, `lorieR8ObsEnd`, `LorieR8TestExtensionInit`,
`ProcLorieR8Dispatch`. `ProcLorieR8Terminate` is static and inlined into
`ProcLorieR8Dispatch`.

Unstripped `ddxGiveUp`: `CloseWellKnownConnections` → `UnlockServer` →
`lorieR8ObsEnd` → `exit`.

Unstripped opcode 3 path: `cmp w8, #0x3` → `lorieR8Obs` → `WriteToClient` → `GiveUp@plt`.

`GiveUp`: `orr w10, w10, #0x2` (`DE_TERMINATE`). Product `DE_RESET` remains 1.

Native Build ID matches `fb4f017` because this commit does not change `libXlorie.so`
sources; versionName binds `b984ded`.

Judge SHA `f021048d…0e31` and collector SHA `e6df519a…666c8` unchanged.
Host `verify-r8-support.py` **R8_SUPPORT_HOST_STATIC_OK**.
