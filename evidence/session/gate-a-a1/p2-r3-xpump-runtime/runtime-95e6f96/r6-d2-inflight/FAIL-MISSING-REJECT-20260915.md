# R6-D2-INFLIGHT FAIL — 95e6f96 — 2026-09-15

Keep this cell. Do not overwrite. Do not silent-retry.

```text
CLASSIFICATION: FIXTURE CONSTRUCTION (overlap not held)
PRODUCT ADMIT BUG: NOT PROVEN
COMPLETED serial 6: PROVEN (historical 9369553 ABSENT FALSIFIED on this APK)
```

| | |
|---|---|
| X `:3` | PID **21317** ALIVE_8S then torn down |
| Env | `PROTO=1` `TELEMETRY=1`; OOM hook **unset** (proven) |
| Fixture | ELF `2ca0957f…68a3` `CLIENT_OK`; later pixels exact `got0=00804000` |
| Script | exit **2** `R6_DESIGN_FAIL d2_inflight_missing_reject_reason1` |
| Event 31 | **ABSENT** (count=0) |
| Event 14 | **9** including renderer `seq=27 serial=6` covering Present GPU S=6 |
| Event 32/33 | ABSENT |
| Fatal | none |
| Stable | PID **1004** UNTOUCHED |
| Teardown | `NO_X3_RESIDUE` |

## Authoritative order (`seq`)

```text
seq 24 PresentPixmap REQUEST  dst=20
seq 25 CALLBACK xop=4 serial=6 dst=20
seq 26 Composite REQUEST      dst=22
seq 27 COMPLETED role=RENDERER serial=6 src=6 dst=5
seq 28 CALLBACK xop=3 serial=0 dst=22
seq 37 PUBLISH serial=7
seq 42 COMPLETED serial=7
seq 43 SUCCESS serial=7 dst=5
```

Present-before-Composite **schedule constructed**. `gateAQueueSemanticallyQuiescent`
requires `completedSerial == last`. Renderer published COMPLETED serial 6 at
seq 27 during Composite (logcat 16:17:53.873 between D1 BEFORE_UNWRAP and
EXA_COMPOSITE_ENTER). Composite was therefore admitted; reason-1 reject never
fired.

Compare frozen `runtime-9369553/r6-d2-inflight-retry1/` (same ELF family
ASYNC\|COPY): CALLBACK serial 6 then REJECT reason=1 **before** any serial-6
COMPLETED. This cell lost that ~1 ms overlap.

Do **not** treat missing reject as a proven admit regression. Do **not** run
D2-OOM on this FAIL. Next device cell needs a new identity
(`r6-d2-inflight-retry1/`) and explicit authorization.
