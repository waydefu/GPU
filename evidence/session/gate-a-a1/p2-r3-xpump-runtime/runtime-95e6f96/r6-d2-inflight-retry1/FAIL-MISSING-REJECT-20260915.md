# R6-D2-INFLIGHT retry1 FAIL — 95e6f96 — 2026-09-15

Keep this cell. Do not overwrite. Do not silent-retry. First FAIL
`../r6-d2-inflight/` remains frozen.

```text
CLASSIFICATION: FIXTURE CONSTRUCTION REPRODUCED (overlap not held)
PRODUCT ADMIT BUG: NOT PROVEN
COMPLETED serial 6: PROVEN
```

| | |
|---|---|
| X `:3` | PID **24492** ALIVE_8S then torn down |
| Env | `PROTO=1` `TELEMETRY=1`; OOM hook **unset** (proven) |
| Fixture | ELF `2ca0957f…68a3` `CLIENT_OK`; later pixels exact `got0=00804000` |
| Script | exit **2** `R6_DESIGN_FAIL d2_inflight_missing_reject_reason1` |
| Event 31 | **ABSENT** |
| Event 14 | renderer `seq=27 serial=6` covering Present GPU S=6 |
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

Same shape as `r6-d2-inflight/` X 21317. Present-before-Composite constructed;
GPU serial 6 already terminal at Composite TryPrepare; reason-1 reject never
emitted. Same ELF, same installed APK. Overlap is not held on this fixture.

Logcat stop printed `STOP logcat pid 24476 still alive after TERM` then the
pid vanished; judge still parsed 84 contiguous events `seq=0..83`. That is
not the FAIL reason.

Do **not** start D2-OOM. Do **not** open retry2 without a new grant that
changes construction (fixture overlap), not another identical cell.
