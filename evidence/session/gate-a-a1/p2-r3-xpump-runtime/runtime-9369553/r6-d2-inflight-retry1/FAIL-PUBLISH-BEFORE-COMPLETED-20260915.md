# R6-D2-INFLIGHT-retry1 — FAIL publish before Present COMPLETED

Authorized 2026-09-15: D2 fixture only (`ASYNC|COPY`). Keep `r6-d2-inflight/`.
Device `9369553`. D2-OOM **NOT RUN**.

| | |
|---|---|
| X `:3` | PID **20856** |
| Fixture | source `6b7e8277…4ec8` ELF `ffce3910…b068` |
| Script exit | **2** `d2_lease_or_publish_before_completed` PUBLISH seq 36 serial=8 |
| Client | `CLIENT_OK` later pixels `got0=00804000` |
| Env | PROTO=1 TELEMETRY=1; OOM **unset** |
| Stable | PID **1004** UNTOUCHED |

```text
seq 19 PresentPixmap REQUEST
seq 20 CALLBACK Present xop=4 serial=6
seq 21 Composite REQUEST
seq 23 DIRECT_ADMIT_REJECT reason=1 serial=6
seq 26 later Composite REQUEST
seq 36 PUBLISH serial=8
seq 41 COMPLETED serial=8
seq 42 SUCCESS serial=8
```

**PROVEN vs first inflight cell:** Present CALLBACK before Composite; reject reason=1 fires.

**ABSENT:** EVENT_COMPLETED serial=6 (only COMPLETED in follow is serial=8).
Later Composite PUBLISH serial=8 therefore fails design “no publish serial>S until COMPLETED covers S”.

Quiescence of Present serial 6 was **not traced** (event 14 absent). Later
classification (2026-09-15, do not overwrite this cell): admission used
`completedSerial` without EVENT_COMPLETED on legacy COPY. Packet:
`../../../p2-r6-design/GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md`.
Do not silent-retry this ELF. Do not start D2-OOM on `9369553`.
