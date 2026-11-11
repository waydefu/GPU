# Gate A P2 B-2 R1 unset — FAIL REPRODUCED 2026-09-16 `0d72332` rerun1

Authorized one-shot rerun. First FAIL cell kept. No second retry.
R2–R6-D1 not started. R7 not started.

| Field | Value |
|---|---|
| HEAD / APK | `0d72332` / `1.03.01-0d72332-16.09.26` CI **35049545631** |
| Cell | `runtime-0d72332/r1-unset-oracle-rerun1/` |
| First FAIL (kept) | `runtime-0d72332/r1-unset-oracle/` X **11212** serial **2370** |
| X PID | **8172** |
| MODE | unset (`NO_GATEA_ENV`) |
| Oracle | **PASS** 1514/1514 fail=0 maxΔ=0 Xnz=0 |
| Stress 100 | PASS `ok=100 fail=0 alive=1` |
| Stress mixed 100 | PASS `ok=100 fail=0 alive=1` |
| Stress 1000 | **FAIL** `ok=90 fail=910 n=1000 alive=0` |
| `B2_DIAG_FAIL` | 1 × `GETIMAGE_NO_REPLY` iteration=90 `conn_err=1` |
| PIXEL_RGB_MISMATCH | **0** |
| EXA wait timeout | **1** serial=**1810** scheduled=1 `11:58:26.798` |
| Last `Gcomp Done` | `11:58:24.776` (**before** timeout) |
| Fatal | `GATEA_FATAL_HALT what=x-exa-composite-wait reason=4` `11:58:26.800` |
| GATEA_SUMMARY | `where=x-exa-composite-wait` `fatalReason=4` |
| timeout→Done | **NONE** |
| Stable | PID **17922** UNTOUCHED |
| Residue | `NO_X3_RESIDUE` |

Same class as first attempt: GPU wait timeout → Composite fail-stop, not false Done.
First FAIL SHA256 `x1000.out` `f2e21d49…0f8f` unchanged.

## Verdict

**B-2 BLOCKED / 0d72332 / r1-unset-oracle-rerun1 FAIL REPRODUCED (timeout serial=1810 fail-stop)**
