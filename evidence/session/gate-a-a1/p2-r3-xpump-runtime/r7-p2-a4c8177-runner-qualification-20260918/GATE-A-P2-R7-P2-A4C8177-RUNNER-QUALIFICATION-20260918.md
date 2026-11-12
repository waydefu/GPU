# Gate A P2 R7 — a4c8177 R7-P2 dedicated runner tooling qualification — 2026-09-18

```
PRIMARY_VERDICT: R7_P2_A4C8177_RUNNER_QUALIFIED
a4c8177: ARTIFACT QUALIFIED / NOT INSTALLED at this packet
R7-P2 device: NOT RUN
historical abb27a65 R7-P1: INVALID / FROZEN
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
| runner | `run-r7-p2-a4c8177.sh` SHA256 `6b0a9bdbcbf71a3cbe43f8da80d13d2b7a1c4f5331ada69feb8800969b90d55e` |
| classifier | `classify_r7_p2_a4c8177.py` SHA256 `272265b144b7cacced14ac4c41410812131360748c4b94a52bf52de4b8105c2c` |
| judge | frozen SHA `fba3c10f…cc17` unmodified |

Does **not** overwrite `run-r7-p2-abb27a65.sh` SHA `d36a4ccc…d8cc`.

Expected device contract (not run here): CALLBACK30 src=4 → event35
enum13 side=2 → renderer `_exit` → `x-hup/6`. Startup CopyArea cannot
consume enum13.

Host tests: `test_r7_p2_a4c8177_runner.sh` **pass=31 fail=0**

Fresh evidence path: `runtime-a4c8177/r7-p2` (not created in this packet).
