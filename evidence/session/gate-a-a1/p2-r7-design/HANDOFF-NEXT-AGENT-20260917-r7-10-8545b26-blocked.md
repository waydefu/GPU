# Gate A P2 R7 — 2026-09-17 `8545b26` R7-10 device requal **BLOCKED**（無 live mDNS）；未安裝；歷史 FAIL 凍結

```
STATUS: a07d66c last-known INSTALLED (historical R7-10 FAIL frozen)
        8545b26 ARTIFACT QUALIFIED / RUNNER QUALIFIED / NOT INSTALLED
        R7-10 8545b26 device NOT RUN / BLOCKED (ADB mDNS empty)
        do not retry this preflight
        do not use historical SERIAL
        next is restore live _adb-tls-connect then a new same-scope grant
        do not start R7-P1 / R7-P2
        do not retry runtime-a07d66c/r7-10
Stable :1: PID 20146 UNTOUCHED
Production Gate A: BLOCKED
```

Blocked packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-8545b26/GATE-A-P2-R7-10-8545B26-BLOCKED-20260917.md`

Preflight evidence (not the legal cell):
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-8545b26/r7-10-preflight/`

`runtime-8545b26/r7-10/` still ABSENT.
Historical `runtime-a07d66c/r7-10/` intact (`R7_FAIL halt_mismatch what=x-direct-not-success reason=4`).

APK file SHA256 MATCH `92220845…377a`. Dedicated runner HASH_MATCH. No install. No runner invoke.

## Next

Restore live mDNS `_adb-tls-connect._tcp.local.` IPv4 endpoint, then a **new**
grant with the same scope: install `8545b26` experimental only, full live
binding, one `run-r7-10-8545b26.sh`. Do **not** reuse historical
`192.168.1.101:35343`. Do **not** execute from this packet. Do **not** start
R7-P1/P2. Do **not** retry `runtime-a07d66c/r7-10`.
