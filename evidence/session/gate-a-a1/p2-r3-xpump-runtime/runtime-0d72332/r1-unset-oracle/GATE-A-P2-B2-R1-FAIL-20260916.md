# Gate A P2 B-2 R1 unset — FAIL 2026-09-16 `0d72332`

First attempt. No silent retry. R2–R6-D1 not started. R7 cells not started.
Stop before R8.

| Field | Value |
|---|---|
| HEAD / APK | `0d72332` / `1.03.01-0d72332-16.09.26` CI **35049545631** |
| Cell | `runtime-0d72332/r1-unset-oracle/` |
| X PID | **11212** |
| MODE | unset (`NO_GATEA_ENV`; TEST_FAULT / TEST_ARM / R6 OOM / PROTO / TELEMETRY absent) |
| Oracle | **PASS** 1514/1514 fail=0 maxΔ=0 Xnz=0 |
| Stress 100 | PASS `ok=100 fail=0 alive=1` |
| Stress mixed 100 | PASS `ok=100 fail=0 alive=1` |
| Stress 1000 | **FAIL** `ok=650 fail=350 n=1000 alive=0` (`p_b2_stress` rc=1) |
| `B2_DIAG_FAIL` | 1 × `GETIMAGE_NO_REPLY` iteration=650 `conn_err=1` (X already dead) |
| PIXEL_RGB_MISMATCH | **0** |
| GATEA_EVENT | 0 |
| event 35 | 0 |
| SIGSEGV / SIGILL / Fatal signal | NONE |
| EXA wait timeout | **1** serial=**2370** scheduled=1 `11:27:18.234` |
| Last `Gcomp Done` | `11:27:16.147` (**before** timeout; none after) |
| Fatal | `GATEA_FATAL_HALT what=x-exa-composite-wait reason=4` (`LORIE_GATEA_FAIL_TIMEOUT`) `11:27:18.411` |
| GATEA_SUMMARY | `where=x-exa-composite-wait` `generationFatal=4` `fatalReason=4` |
| timeout→Done | **NONE** (repair fail-stop held) |
| Stable | PID **17922** UNTOUCHED `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03 |
| HDMI | observe-only `mDisplayId=0` |
| Residue | `NO_X3_RESIDUE` |

Historical `runtime-a7528bd/r1-unset-oracle/` remains authoritative for the **old** candidate
(`ok=999 fail=1 alive=1`, timeout then `Gcomp Done`). It was not overwritten.

## Repair regression check

The Composite timeout path no longer continues as successful Done:

1. `EXA GPU composite wait timeout serial=2370 scheduled=1`
2. `GATEA_SUMMARY where=x-exa-composite-wait fatalReason=4`
3. `GATEA_FATAL_HALT what=x-exa-composite-wait reason=4`
4. X PID 11212 exited; client GetImage saw `GETIMAGE_NO_REPLY` / `conn_err=1`
5. No `Gcomp Done` after the timeout line
6. No stale-dest `PIXEL_RGB_MISMATCH`

That is the intended fail-stop. It is **not** R1-unset PASS: the baseline
forbids fatal/timeout, and stress1000 `fail != 0`.

Normal non-timeout Composite remained exact through oracle 1514 and the
first 650 stress1000 iterations (`Gcomp Done` 2363, last at 11:27:16.147).

## Verdict

**B-2 BLOCKED / 0d72332 / r1-unset-oracle: EXA Composite wait timeout serial=2370 fail-stop (`x-exa-composite-wait` reason=4); stress1000 ok=650 fail=350 alive=0**

Do not silent-retry. Do not start R2–R6-D1. Do not start R7.
