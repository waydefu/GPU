# Gate A P2 R8-C1 attempt-09 BLOCKED — 2026-09-19

```
STATUS: R8_BLOCKED ADB_CONNECT_FAILED
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        b984ded INSTALLED (last proven 2026-09-18; not re-dumpsys'd this round)
        CI 35347497216
        C1 attempts 01–08 FROZEN
        attempt-09 cell NOT CREATED
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** silent-retry `10.191.48.13:45165`.
Do **not** create attempt-10.
Do **not** start C2 or R9.
Do **not** rerun CI **35347497216**.
Do **not** overwrite attempts 01–08 or `run-r8-one-cell-b984ded.sh`.

Live runner remains `p2-r8-runtime/run-r8-one-cell-b984ded-v2.sh`
SHA256 `53e0c6b8…44e5` / `JUDGE=judge-r8-v2.py`.

Preflight packet
`GATE-A-P2-R8-C1-ATTEMPT-09-BLOCKED-20260919.md`.
Cell dir `runtime-b984ded/r8-c1/attempt-09/` is still absent.

**STOP.** New explicit grant required after ADB connect to a live
`_adb-tls-connect` endpoint succeeds (`ro.product.device=myron`, screen Awake).
Production Gate A remains BLOCKED.
