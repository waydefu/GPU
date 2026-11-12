# Gate A P2 R7 — a4c8177 R7-P1 dedicated runner tooling qualification — 2026-09-18

```
PRIMARY_VERDICT: R7_P1_A4C8177_RUNNER_QUALIFIED
a4c8177: ARTIFACT QUALIFIED / NOT INSTALLED at this packet
R7-P1 device: NOT RUN
R7-P2 device: NOT RUN
historical abb27a65 R7-P1: INVALID / FROZEN
historical 8545b26 R7-P1: INVALID / FROZEN
R7 overall: IN PROGRESS (11/13)
Production Gate A: BLOCKED
Device execution this packet: NONE
```

## Bind

| Field | Value |
|---|---|
| source | `a4c8177f4b059fddd111717255e9d23cf0e15e1e` |
| parent | `abb27a65b029b16837fe178624a85ac18a4ba005` |
| CI | **35295094951** |
| APK SHA256 | `91a4b74eff2c54cceba89ca3b8f8530442fa371fd7a67523eaf8bbd73c75a55c` |
| versionName | `1.03.01-a4c8177-18.09.26` versionCode 15 |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` |
| Build ID | `dcd8297497c38f6b277cc9cbdb74b2eea06dba60` |
| runner | `run-r7-p1-a4c8177.sh` SHA256 `4cbb1394c7b714bb4fb570dff352539ad179b8e5b39d174b8f325c9ec33e1b47` |
| classifier | `classify_r7_p1_a4c8177.py` SHA256 `232892b2e895bc0f63e3b98ad866773ce6ab91975fbd74dbc3a969a684c827c4` |
| judge | frozen SHA `fba3c10f…cc17` unmodified |

Does **not** overwrite `run-r7-p1-abb27a65.sh` SHA `95900a2d…7098`.

Liveness: ADB `test -d /proc/$ACT_PID` + ADB `ps` identity. Host `/proc`
is commentary only. Classifier consumes bound `activity_alive_during_wait`.

Positive class: `EXPECTED_PRESENT_TIMEOUT`
Negative: `TARGET_COMPLETED` `PEER_DIED` `NO_PRESENT_CALLBACK`
`WRONG_TERMINAL` `WRONG_REASON4_IDENTITY` `REPEATED_FAULT` `TRACE_INCOMPLETE`
plus arm-construction `EARLY_COPY_CONSUME` `SERIAL_MISMATCH` `INVALID_ENV`

Host tests: `test_r7_p1_a4c8177_runner.sh` **pass=38 fail=0**

Fresh evidence path: `runtime-a4c8177/r7-p1` (not created in this packet).
