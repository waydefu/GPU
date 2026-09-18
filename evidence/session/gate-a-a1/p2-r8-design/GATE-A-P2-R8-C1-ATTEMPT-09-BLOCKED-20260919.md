# GATE A P2 R8-C1 attempt-09 BLOCKED — 2026-09-19

```
STATUS: R8_BLOCKED ADB_CONNECT_FAILED
        attempt-09 cell directory NOT CREATED
        runner NOT invoked
        Production Gate A BLOCKED
```

Grant was exactly one fresh R8-C1 / attempt-09 on
`run-r8-one-cell-b984ded-v2.sh` / product `b984ded` / CI **35347497216** /
tooling `2a14ab2`.

The live runner was **not** started. Isolated ADB 5038 is alive (PID **3065**),
and live mDNS `_adb-tls-connect._tcp.local.` returned
`adb-51c6f1fe-ZtRPH4` → `10.191.48.13:45165`. `adb connect` to that endpoint
returned `failed to connect to 10.191.48.13:45165`. This was **not**
`CERTIFICATE_UNKNOWN`. TCP to the same host:port is reachable (`connect_ex=0`,
ping PASS). wlan0 inet is the same address. Loopback `127.0.0.1:45165` also
failed to connect.

Host tooling hashes matched the grant. Fixture SHA matched. Local Stable PID
**20146** `:1 -legacy-drawing` present. No experimental `:3` process. Installed
APK dumpsys was **not** reachable, so live package binding was **not**
re-proven this round.

Evidence: `p2-r8-runtime/runtime-b984ded/r8-c1/attempt-09-preflight/`
The cell path `runtime-b984ded/r8-c1/attempt-09/` does **not** exist.

Attempts 01–08 untouched. Frozen `judge-r8.py` untouched. No APK rebuild/
reinstall. No C2. No R9.

**STOP.** Do not silent-retry this endpoint. New explicit grant required
before another C1 attempt-09 once ADB connect works.
