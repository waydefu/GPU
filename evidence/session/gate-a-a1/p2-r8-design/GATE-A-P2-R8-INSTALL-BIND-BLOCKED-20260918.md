# GATE A P2 R8 INSTALL BIND BLOCKED — 2026-09-18

```
STATUS: R8_INSTALL_BIND_BLOCKED
        artifact QUALIFIED, not installed
        isolated ADB 5038 has no device
        mDNS _adb-tls-connect._tcp.local. empty
        experimental remains a4c8177
        R8 device cells NOT RUN
        Production Gate A BLOCKED
```

Host/CI/artifact/tooling of `65938a4` remain PASS. Install was not started
(`RUN_INSTALL` never YES against a live serial). No experimental
`pm install`. Stable `:1` not touched. HDMI not mutated.

## Binding that did PASS before this stop

| Field | Value |
| --- | --- |
| Support SHA | `65938a447639fce2adae61a15a2d8348e7c6455f` |
| Parent | `d382c0a96fb84330de939f415413f346fa4b5848` |
| CI | **35311343984** success |
| APK SHA256 | `b88f12ecdb6a6fb9bf8db724b4dbee5ac363cb863f8246bc15ac08bc20c31a6c` |
| versionName | `1.03.01-65938a4-18.09.26` |
| Build ID | `21770f736570ae13b7635d7765c3d8470b40cfa7` |
| Installed experimental | still **`a4c8177`** CI **35295094951** |

## ADB evidence (this stop)

Existing isolated server (not started this session):

`pid 3065` `/data/data/com.termux/files/usr/bin/adb -L tcp:5038 server nodaemon`

`adb -H 127.0.0.1 -P 5038 devices -l` → `List of devices attached` (empty).

Python zeroconf browse `_adb-tls-connect._tcp.local.` 6s and 10s → no IPv4
endpoints. `adb mdns services` on this build prints an empty discovered list
plus `unknown host service` for `mdns:check`.

No hardcoded serial. No 5037. No second 5038 server. No install attempt.

## Not run

Install of `65938a4`. R8-C1 … R8-P2. R9.

## Next

Bring the POCO F8 Ultra back onto isolated ADB 5038 (live mDNS
`_adb-tls-connect._tcp.local.`), then install the already-qualified
`65938a4` artifact and run the 10 cells fail-fast. Do not rerun CI
**35304122983** / **35305368742** / **35311343984**.
