# GATE A P2 R8 INSTALL BIND BLOCKED — 5a782f6 — 2026-09-18

```
STATUS: R8_INSTALL_BIND_BLOCKED
        5a782f6 HOST + CI + ARTIFACT QUALIFIED, not installed
        isolated ADB 5038 has no device
        mDNS _adb-tls-connect._tcp.local. empty
        experimental remains 65938a4
        fresh C1 attempt-05 NOT STARTED
        Production Gate A BLOCKED
```

Observation-terminal repair is committed and CI-built. Install was not
started (`RUN_INSTALL` never YES against a live serial). No experimental
`pm install` this session. Stable `:1` PID **20146** not touched. HDMI
not mutated.

## Binding that did PASS before this stop

| Field | Value |
| --- | --- |
| Repair SHA | `5a782f6f47ffa1a3374bac04aef5616a81d59089` |
| Parent | `65938a447639fce2adae61a15a2d8348e7c6455f` (unamended) |
| CI | **35321447455** success (not a rerun of 35304122983 / 35305368742 / 35311343984) |
| APK SHA256 | `43590412d5537339bb6822d0157e135b5fc00a7cca80570d987adc87c15ba78e` |
| versionName | `1.03.01-5a782f6-18.09.26` |
| Build ID | `d032a8188b4f768a523b4c06cfe62a813950b02a` |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` |
| Installed experimental | still **`65938a4`** CI **35311343984** |

Host: `R8_OBS_TERMINAL_REPAIR_HOST_QUALIFIED`.
Artifact: `R8_OBS_TERMINAL_ARTIFACT_QUALIFIED`.
Install script ready: `p2-r8-runtime/install-5a782f6.sh` (requires `RUN_INSTALL=YES` + live SERIAL).

## ADB evidence (this stop)

Existing isolated server (not started this session):

`pid 3065` `/data/data/com.termux/files/usr/bin/adb -L tcp:5038 server nodaemon`

`adb -H 127.0.0.1 -P 5038 devices -l` → `List of devices attached` (empty).

Python zeroconf browse `_adb-tls-connect._tcp.local.` 6s and 10s → no IPv4
endpoints. No hardcoded serial. No 5037. No second 5038 server.

## Frozen C1 history (immutable)

attempt-01 `MISSING_END_x`. attempt-02 `SCREEN_NOT_AWAKE`. attempt-03 tooling emit JSON. attempt-04 `END_COUNT_MISMATCH_x`. Do not retry. Next C1 path must be `runtime-5a782f6/r8-c1/attempt-05-obs-terminal/` and must not exist before start.

## Not run

Install of `5a782f6`. Fresh C1. C2–P2. R9.

## Next

Bring the POCO F8 Ultra back onto isolated ADB 5038 (live mDNS), then
`RUN_INSTALL=YES` `install-5a782f6.sh` into `runtime-5a782f6/r0`, rebind
v2/v3 orchestration to the new artifact, and run one C1 at
`runtime-5a782f6/r8-c1/attempt-05-obs-terminal/`. Do not rerun CI
**35304122983** / **35305368742** / **35311343984** / **35321447455**.
