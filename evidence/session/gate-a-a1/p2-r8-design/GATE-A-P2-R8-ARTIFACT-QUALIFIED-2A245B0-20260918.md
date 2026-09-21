# GATE A P2 R8 ARTIFACT QUALIFIED — 2a245b0 / 35331185799 — 2026-09-18

```
STATUS: R8_GIVEUP_END_ARTIFACT_QUALIFIED
        package com.waydefu.x11gpu
        X END at ddxGiveUp present (unstripped call)
        protocol v1 layouts QV32 / Register72 / Checkpoint72 unchanged
        Production Gate A BLOCKED
        NOT INSTALLED this turn
```

## Binding

```text
source: 2a245b0bc5d38394df29546e0af0de798f9d260c
parent: 5a782f6f47ffa1a3374bac04aef5616a81d59089
CI: 35331185799 workflow_dispatch success
headSha: 2a245b0bc5d38394df29546e0af0de798f9d260c
universal-debug artifact id: 10541700106
unstripped artifact id: 10541705156
filename: termux-x11-universal-debug.apk
size: 15346290
SHA256: 008a1ece18c0b766abb8389a512fe81d3c2dd8527e7175531964a4cf43683af4
package: com.waydefu.x11gpu
versionName: 1.03.01-2a245b0-18.09.26
versionCode: 15
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
Build ID embedded == unstripped: 5ea80da0915ba382c53345efd28099b66d101828
unzip -t: PASS (archive opened; GitHub zip digest is NOT APK SHA256)
zipalign: NOT CLAIMED
native-code: arm64-v8a armeabi-v7a x86 x86_64
```

## Provenance (embedded arm64 libXlorie.so)

FOUND (strings, not behavior):

- `LORIE-R8-TEST`
- `R8_OBS`
- `R8_OBS_POST_END role=%s phase=%s`
- `R_SURFACE_QUIESCED`
- `X_CLOSE_ENTER`
- `x-destroy-in-lease`

Unstripped `nm`: `ddxGiveUp`, `lorieR8ObsEnd`, `lorieR8Obs`, `lorieExaDestroyPixmap`, `LorieR8TestExtensionInit`.

Unstripped `ddxGiveUp` disassembly: `CloseWellKnownConnections` → `UnlockServer` → `lorieR8ObsEnd` → `exit`.

Protocol v1 compile-time authority unchanged (host verify): QV reply 32 / Register 72 / Checkpoint 72.
Judge SHA `f021048d…0e31` and collector SHA `e6df519a…666c8` unchanged.
