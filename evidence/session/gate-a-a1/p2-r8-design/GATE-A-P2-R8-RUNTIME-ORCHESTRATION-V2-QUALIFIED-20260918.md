# GATE A P2 R8 RUNTIME ORCHESTRATION V2 QUALIFIED — 2026-09-18

```
STATUS: R8_RUNTIME_ORCHESTRATION_V2_QUALIFIED
        VALIDATE_ONLY device mutation = 0
        judge_vectors=53 device_cells=10
        product SHA 65938a4 unchanged
```

| Tool | SHA256 |
| --- | --- |
| run-r8-one-cell-v2.sh | `ea05aaa5ceac249f4f09359ddaa4db2698fa93072a0623917ff4b6a593ec5db5` |
| r8_orchestration_v2.py | `21f97d9fd4dca5c4e7b33d6fe0e15269041c7609f852519659b2b7aff4c194cc` |
| test_r8_orchestration_v2.py | `b1bd68bb9fabc630f591aaf22958ff9bb240afe98cb18d89d3815aff2318de93` |
| judge-r8.py | `f021048d…0e31` UNCHANGED |
| collect-r8.py | `e6df519a…666c8` UNCHANGED |
| p_r8_lifecycle.c | `ca521292…0954` UNCHANGED |
| fixture ELF | `d3910436…0493` UNCHANGED |
| lifecycle-cell-spec.json | `ff22a152…b3ba` UNCHANGED |
| judge-negative-cases.json | `360152a8…38b7` UNCHANGED |
| old v1 runner | `f4ed81f4…2c3d` preserved |

Host orchestration tests: **14/14 PASS**.
Judge regression: **53/53 PASS** `failures=0`.
`VALIDATE_ONLY=1` → `R8_LIVE_RUNNER_V2_VALIDATE_ONLY R8-C1`.

Old C1 INVALID remains bound to v1 runner. Do not reuse attempt-01.
