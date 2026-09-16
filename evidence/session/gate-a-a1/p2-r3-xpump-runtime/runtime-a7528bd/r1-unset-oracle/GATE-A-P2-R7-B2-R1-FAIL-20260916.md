# Gate A P2 R7 B-2 R1 unset — FAIL 2026-09-16

First attempt. No silent retry. R7 cells not started. Stop before R8.

| Field | Value |
|---|---|
| HEAD / APK | `a7528bd` / `1.03.01-a7528bd-15.09.26` CI **35007764673** |
| Cell | `runtime-a7528bd/r1-unset-oracle/` |
| X PID | **17192** |
| MODE | unset (TEST_FAULT / TEST_ARM / R6 OOM / PROTO / TELEMETRY all absent from `/proc/17192/environ`) |
| Oracle | **PASS** 1514/1514 fail=0 maxΔ=0 Xnz=0 |
| Stress 100 | PASS `ok=100 fail=0` |
| Stress mixed 100 | PASS `ok=100 fail=0` |
| Stress 1000 | **FAIL** `ok=999 fail=1 n=1000 alive=1` (`p_b2_stress` rc=1) |
| GATEA_EVENT | 0 |
| event 35 | 0 |
| GATEA_FATAL / SIGSEGV / SIGILL | NONE |
| GATEA_SUMMARY | present `where=x-close-screen`; nonce=generation=nextSequence=0; all 28 counters 0 |
| Harness | `run-r1-off.sh` aborted on `set -o pipefail` after stress 1000; logcat TERM race; teardown completed out of band |
| Stable | PID **17922** UNTOUCHED |
| HDMI | untouched |

`p_b2_stress` has no per-iteration log. `alive=1` so the miss is GetImage failure or a 1-pixel RGB mismatch, not a disconnect. Root cause **NOT PROVEN**. Not classified as ART JIT.

B-2 rule: any FAIL → do not start R7 cells. Do not silent-retry this cell.
