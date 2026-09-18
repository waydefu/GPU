# GATE A P2 R8 RUNTIME TOOLING QUALIFIED — 2026-09-18

```
STATUS: R8_RUNTIME_TOOLING_QUALIFIED
        VALIDATE_ONLY device mutation = 0
        judge_vectors=53 device_cells=10
```

Immutable manifest:
`evidence/session/gate-a-a1/p2-r8-runtime/runtime-65938a4/r8-runtime-tooling-manifest.json`

Binds design acceptance, API/protocol amendment, support SHA `65938a4`,
CI **35311343984**, APK SHA256 `b88f12ec…1a6c`, signer
`b6da0148…e5e1`, Build ID `21770f73…cfa7`, protocol v1 sizes
QV32/Reg72/Ck72.

| Tool | SHA256 |
| --- | --- |
| p_r8_lifecycle.c | `ca521292…0954` (unchanged vs host-verified client) |
| host ELF `/tmp/p_r8_lifecycle` | `d3910436…2c3d` |
| run-r8-one-cell.sh | `f4ed81f4…2c3d` |
| judge-r8.py | `f021048d…0e31` |
| collect-r8.py | `e6df519a…666c8` |
| verify-r8-support.py | `5c3a070e…2839` |
| lifecycle-cell-spec.json | `ff22a152…b3ba` |
| judge-negative-cases.json | `360152a8…38b7` |

`VALIDATE_ONLY=1` `run-r8-one-cell.sh --cell R8-C1` →
`R8_RUNNER_VALIDATE_ONLY R8-C1` rc=0. No ADB, no install, no X.

`verify-r8-support.py` PASS. `test-judge-r8.py` 53/53 `failures=0`.
