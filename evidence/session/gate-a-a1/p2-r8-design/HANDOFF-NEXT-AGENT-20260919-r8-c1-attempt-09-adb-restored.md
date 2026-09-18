# Gate A P2 R8-C1 ADB restored — 2026-09-19

```
STATUS: ADB_LANE_RESTORED
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        b984ded INSTALLED (re-proven this round)
        CI 35347497216
        SERIAL 10.191.48.13:46847
        C1 attempts 01–08 FROZEN
        attempt-09 cell NOT CREATED
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** silent-start C1.
Do **not** create attempt-10.
Do **not** start C2 or R9.
Do **not** reuse frozen `10.191.48.13:45165`.
Do **not** rerun CI **35347497216**.
Do **not** overwrite attempts 01–08 or `run-r8-one-cell-b984ded.sh`.

Live runner remains `p2-r8-runtime/run-r8-one-cell-b984ded-v2.sh`
SHA256 `53e0c6b8…44e5` / `JUDGE=judge-r8-v2.py`.

Restore packet
`GATE-A-P2-R8-C1-ATTEMPT-09-ADB-RESTORED-20260919.md`.
Historical blocked preflight remains
`GATE-A-P2-R8-C1-ATTEMPT-09-BLOCKED-20260919.md`.
Cell dir `runtime-b984ded/r8-c1/attempt-09/` is still absent.

**STOP.** Request explicit authorization for one fresh R8-C1 / attempt-09
on SERIAL `10.191.48.13:46847` after confirming screen still Awake.
Production Gate A remains BLOCKED.
