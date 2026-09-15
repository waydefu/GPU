# R6-D2-INFLIGHT — FAIL missing DIRECT_ADMIT_REJECT

Authorized after D1-retry5 PASS (scheme A). New X PID. Device `9369553`.
D2-OOM **NOT RUN** (fail-closed).

| | |
|---|---|
| X `:3` | PID **17596** |
| Fixture ELF | `7052a358…9bf8` mode `inflight` |
| Script exit | **2** `R6_DESIGN_FAIL d2_inflight_missing_reject_reason1` |
| Client | `CLIENT_OK` later pixels `got0=00804000` |
| Env | PROTO=1 TELEMETRY=1; OOM **unset** |
| Stable | PID **1004** UNTOUCHED |

```text
seq 19 PresentPixmap REQUEST
seq 20 Composite REQUEST (immediate)
seq 21 CALLBACK Composite xop=3
seq 26/30/36 LEASE/PUBLISH/SUCCESS serial=6  ← Composite admitted
seq 45 CALLBACK Present xop=4 serial=7       ← Present GPU copy after Composite SUCCESS
```

**PROVEN:** Present CALLBACK exists, but after the racing Composite already SUCCESS.
Present was not yet in `present_execute_copy` / GPU queue when Composite ran
(same MSC+1 queue as D1 retry4). No event 31 reason=1.

Do not silent-retry. Do not start D2-OOM or R7 without a new grant.
