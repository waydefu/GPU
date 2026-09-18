# GATE A P2 R8-C1 attempt-09 ADB restored — 2026-09-19

```
STATUS: ADB_LANE_RESTORED
        attempt-09 cell directory NOT CREATED
        runner NOT invoked
        Production Gate A BLOCKED
```

User supplied a live wireless-debug pairing endpoint. Isolated ADB 5038
PID **3065** was reused (no second server; 5037 untouched).

Live mDNS:
- `_adb-tls-pairing._tcp.local.` `adb-51c6f1fe-ZtRPH4` → `10.191.48.13:35027`
- `_adb-tls-connect._tcp.local.` `adb-51c6f1fe-ZtRPH4` → `10.191.48.13:46847`

`adb pair 10.191.48.13:35027` → Successfully paired `[guid=adb-51c6f1fe-ZtRPH4]`.
Pairing code was not written to evidence.
`adb connect 10.191.48.13:46847` → connected. Not `CERTIFICATE_UNKNOWN`.
Frozen failed endpoint `10.191.48.13:45165` was **not** reused.

Device: `ro.product.device=myron`, screen Awake / Display ON,
`mDreamingLockscreen=false`.
Experimental `com.waydefu.x11gpu` `1.03.01-b984ded-18.09.26`
APK SHA256 `0d06de68…98d3` MATCHES CI **35347497216** bind.
Stable `:1` PID **20146** `com.termux.x11` `-legacy-drawing` UNCHANGED.
No experimental `:3`.

Evidence: `p2-r8-runtime/runtime-b984ded/r8-c1/attempt-09-adb-restore/`
Cell path `runtime-b984ded/r8-c1/attempt-09/` still does **not** exist.
Attempts 01–08 untouched. Live runner not invoked. No C2. No R9.

**STOP.** New explicit grant required before R8-C1 attempt-09.
Production Gate A remains BLOCKED.
