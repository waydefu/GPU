# Gate A P2 R1 T2 rerun PASS — 6c7ee6f — 2026-09-14

Documented full matrix after maps disposition. Does **not** erase PID 21977.

| Item | Result |
|---|---|
| First matrix | FAIL B2 PROTO=0 SIGSEGV PID **21977** `PC=0x4800226c` |
| Mapping | `dalvik-jit-code-cache` / `dalvik-main space`; X=`app_process64` |
| Rerun dir | `t2-rerun-1/` |
| A1 unset | PASS PID 27627 |
| B1 PROTO=0 | PASS PID 28210 |
| A2 unset | PASS PID 28840 |
| B2 PROTO=0 | PASS PID 29397 |
| A3 unset | PASS PID 29916 |
| B3 PROTO=0 | PASS PID 30690 |
| Stable | PID **16085** throughout |
| Residue | NO_X3_RESIDUE each cell |

```text
T2 6/6: PASS (rerun-1)
PID 21977: OBSERVED / NON-REPRODUCED on rerun-1 / ROOT CAUSE (exact JIT method) NOT PROVEN
CLASS: ART JIT SIGSEGV, not libXlorie
NEXT: R1 OFF oracle/stress on this APK
Production Gate A: BLOCKED
```
