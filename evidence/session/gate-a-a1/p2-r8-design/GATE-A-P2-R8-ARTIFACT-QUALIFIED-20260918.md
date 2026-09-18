# GATE A P2 R8 ARTIFACT QUALIFIED — 65938a4 / 35311343984 — 2026-09-18

```
STATUS: R8_ARTIFACT_QUALIFIED
        package com.waydefu.x11gpu
        protocol v1 layouts QV32 / Register72 / Checkpoint72 bound as
        compile-time authority, not inferred device behavior
        Production Gate A BLOCKED
```

## Binding

```text
source: 65938a447639fce2adae61a15a2d8348e7c6455f
parent: d382c0a96fb84330de939f415413f346fa4b5848
CI: 35311343984 workflow_dispatch success
headSha: 65938a447639fce2adae61a15a2d8348e7c6455f
universal-debug artifact id: 10532844999
unstripped artifact id: 10533790505
filename: termux-x11-universal-debug.apk
size: 15345826
SHA256: b88f12ecdb6a6fb9bf8db724b4dbee5ac363cb863f8246bc15ac08bc20c31a6c
package: com.waydefu.x11gpu
versionName: 1.03.01-65938a4-18.09.26
versionCode: 15
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
Build ID embedded == unstripped: 21770f736570ae13b7635d7765c3d8470b40cfa7
unzip -t: PASS
zipalign: NOT CLAIMED
GitHub zip digest is NOT APK SHA256
```

Installed experimental remains historical `a4c8177` until this packet's
install phase. Do not infer device behavior from strings.

## Test-support provenance (embedded arm64 libXlorie.so)

FOUND (strings, not behavior):

- `LORIE-R8-TEST`
- `R8_OBS`
- `P1_DESTRUCTOR_CALL`
- `R8_HOOK_UNEXPECTED_RETURN`
- `x-destroy-in-lease`
- `x-close-in-lease`

Unstripped `nm` (not device): `LorieR8TestExtensionInit`,
`lorieGateAR8EnsureGpuSampleableAhb`, `lorieGateAR8PixmapReject`,
`lorieExaDestroyPixmap`, `ProcLorieR8Dispatch`.

Protocol v1 compile-time authority (host `_Static_assert`, not strings):

- LORIE-R8-TEST **1.0**
- QueryVersion reply **32**
- RegisterBuffer reply **72**
- Checkpoint reply **72**
