# GATE A P2 R8-C1 INVALID — 65938a4 — 2026-09-18

```
STATUS: R8_INVALID
        cell R8-C1
        reason MISSING_END_x
        attempt-01 once; FROZEN; do not retry
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Install of `65938a4` remains **R8_INSTALL_BIND_PASS**. This cell is the
first genuine non-PASS after that bind.

## Binding

| Field | Value |
| --- | --- |
| SERIAL | `10.191.48.13:37861` live mDNS `adb-51c6f1fe-ZtRPH4` |
| support SHA | `65938a447639fce2adae61a15a2d8348e7c6455f` |
| CI | **35311343984** |
| versionName | `1.03.01-65938a4-18.09.26` |
| APK SHA256 | `b88f12ec…1a6c` |
| Build ID | `21770f736570ae13b7635d7765c3d8470b40cfa7` |
| X PID | **14713** |
| env | `ENV_EXACT_OK` PROTO=1 TELEMETRY=1 R8_ARM=1 R8_CASE=R8-C1 |
| fixture | `CLIENT_OK` FIXTURE_EXIT=0 |
| pre-cleanup X | DEAD (observed, not substituted) |
| residue | `NO_X3_RESIDUE` |
| Stable | PID **20146** UNCHANGED `1.03.01-11b82d9-06.09.26` |
| HDMI | observe-only INTERNAL |

Cell: `p2-r8-runtime/runtime-65938a4/r8-c1/attempt-01/`

## Completeness (fail-closed)

X observations: **40** records, BEGIN=1, **END=0**. Last phases are
`X_DESTRUCTOR_ENTER/EXIT`. Renderer observations: **5** records, BEGIN=1,
**END=0**, `case=null`. `gatea-summary.txt` / `gatea-ring.txt` = NONE.
Ring completeness x_count=0 r_count=0.

Frozen judge `judge-r8.py` completeness requires BEGIN and END per role.
First stop: `R8_INVALID MISSING_END_x`. `judge.json` exit=2.

Mandatory END cannot be inferred from destructor traffic, CLIENT_OK, or
absence of residue. Unknown/null does not become zero or PASS.

## Not a retry candidate

One attempt. No second X. C2–P2 not started. Do **not** rewrite this
cell. Do **not** silent-retry `runtime-65938a4/r8-c1`.
