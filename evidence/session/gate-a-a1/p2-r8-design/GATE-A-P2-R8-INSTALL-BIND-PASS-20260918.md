# GATE A P2 R8 INSTALL BIND PASS — 65938a4 — 2026-09-18

```
STATUS: R8_INSTALL_BIND_PASS
        experimental 1.03.01-65938a4-18.09.26
        CI 35311343984
        source 65938a447639fce2adae61a15a2d8348e7c6455f
        Stable UNCHANGED PID 20146
        HDMI observe-only INTERNAL
        Production Gate A BLOCKED
```

Previous stop `R8_INSTALL_BIND_BLOCKED` is historical. Isolated ADB 5038
PID 3065 reused (no second server). Live mDNS
`_adb-tls-connect._tcp.local.` `adb-51c6f1fe-ZtRPH4` → `10.191.48.13:37861`.

| Field | Value |
| --- | --- |
| SERIAL | `10.191.48.13:37861` |
| device | `myron` / `25102PCBEG` |
| screen | Awake / keyguard false |
| package | `com.waydefu.x11gpu` |
| versionName | `1.03.01-65938a4-18.09.26` |
| versionCode | 15 |
| APK SHA256 | `b88f12ecdb6a6fb9bf8db724b4dbee5ac363cb863f8246bc15ac08bc20c31a6c` |
| signer | `b6da0148…e5e1` CONTINUITY PASS |
| Build ID | `21770f736570ae13b7635d7765c3d8470b40cfa7` |
| CI | 35311343984 |
| source | `65938a447639fce2adae61a15a2d8348e7c6455f` |
| Stable | `com.termux.x11` `1.03.01-11b82d9-06.09.26` PID **20146** UNCHANGED |
| HDMI | observe-only; INTERNAL displayId=0 |

Cell: `p2-r8-runtime/runtime-65938a4/r0/`
`INSTALL_65938A4_BIND_PASS`

Do not retry frozen CI 35304122983 / 35305368742 / 35311343984.
Next: R8-C1 → … → R8-P2 fail-fast.
