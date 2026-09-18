# GATE A P2 R8 OBS TERMINAL ARTIFACT QUALIFIED — 5a782f6 / 35321447455 — 2026-09-18

```
STATUS: R8_OBS_TERMINAL_ARTIFACT_QUALIFIED
        package com.waydefu.x11gpu
        R8 OBS terminal repair present (strings + unstripped BSS)
        protocol v1 layouts QV32 / Register72 / Checkpoint72 unchanged
        R7 lineage strings retained
        Production Gate A BLOCKED
```

## Binding

```text
source: 5a782f6f47ffa1a3374bac04aef5616a81d59089
parent: 65938a447639fce2adae61a15a2d8348e7c6455f
CI: 35321447455 workflow_dispatch success
headSha: 5a782f6f47ffa1a3374bac04aef5616a81d59089
universal-debug artifact id: 10537776053
unstripped artifact id: 10537905757
filename: termux-x11-universal-debug.apk
size: 15346290
SHA256: 43590412d5537339bb6822d0157e135b5fc00a7cca80570d987adc87c15ba78e
package: com.waydefu.x11gpu
versionName: 1.03.01-5a782f6-18.09.26
versionCode: 15
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
Build ID embedded == unstripped: d032a8188b4f768a523b4c06cfe62a813950b02a
unzip -t: PASS (archive opened; GitHub zip digest is NOT APK SHA256)
zipalign: NOT CLAIMED
```

## Terminal-repair provenance (embedded arm64 libXlorie.so)

FOUND (strings, not behavior):

- `LORIE-R8-TEST`
- `R8_OBS`
- `R8_OBS_POST_END role=%s phase=%s`
- `R_SURFACE_QUIESCED`
- `R_UNBOUND_FINAL`
- `X_CLOSE_ENTER`
- `X_CLOSE_RESULT`
- `P1_DESTRUCTOR_CALL`
- `x-destroy-in-lease`
- `x-close-in-lease`

Unstripped BSS (observation-only, not product admission):

- `r8RendererGenerationUnbound`
- `r8RendererSurfaceQuiesced`
- `r8RendererLoopDrained`
- `r8RendererEndEmitted`

Unstripped `nm`: `lorieR8Obs`, `lorieR8ObsEnd`, `lorieExaDestroyPixmap`, `LorieR8TestExtensionInit`. `lorieR8MaybeFinalizeRendererObs` is file-static and may be inlined; flags above prove the renderer terminal state compiled.

Protocol v1 compile-time authority unchanged:

- QueryVersion reply **32**
- RegisterBuffer reply **72**
- Checkpoint reply **72**

R7 lineage retained: `x-destroy-in-lease`, `x-close-in-lease`, HUP-preserve / present-target-arm host scripts still PASS on this SHA.
