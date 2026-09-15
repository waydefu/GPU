# Gate A P2 R4 PASS — d9b7f60 1514 production oracle — 2026-09-15

Exactly one fresh session **after R2 PASS** on installed `d9b7f60`.
Pinned `p-b2-oracle` (1514). PROTO=1 TELEMETRY=1. **TERMUX_X11_DEBUG unset**.
COLD Activity. Fresh X `:3`. Stable PID **16085**. Teardown `NO_X3_RESIDUE`.
Do **not** silent-retry this cell. Do **not** start R5–R10 without a new decision.
Production Gate A remains **BLOCKED**.

## Runtime

| | |
|---|---|
| Command | `SERIAL=10.193.235.219:38663 CELL=…/runtime-d9b7f60/r4-oracle bash run-r4.sh` |
| Exit | **0** `R4_PRODUCTION_ORACLE_PASS` |
| Activity | PID **11227** (GL / bind) COLD `--display 0` (Display0 visible; Display3 is Stable `com.termux.x11`) |
| X `:3` | PID **29807** alive after fixture, then torn down |
| Oracle | `tests=1514 fail=0 exact_px_acc=1396616 ±1_px=0 Xnz=0 maxΔ=0` `FIXTURE_EXIT=0` |
| NEG | src-op / mask-a8 / dst-argb / bilinear / repeat Composite completed (software) |
| GATEA_BIND | version=1 bound=1 generation=1 nonce=`7501007111204281365` pid 11227 |
| GATEA_EVENT | follow-only **240** lines (not follow+blob) |
| N | publish **8** |
| Counters | consume=lookup=draw=fence=completed=success=ack=**8** |
| firstFailed / genFatal | **0** / **0** |
| Absent (count 0) | LOOKUP_FAIL(9) FENCE_TIMEOUT(12) FENCE_ERROR(13) |
| Fatal / timeout | no `GATEA_FATAL_HALT`; no `x-ready-timeout` |

`counts={1: 32, 2: 8, 3: 8, 4: 8, 5: 8, 6: 8, 7: 8, 8: 8, 10: 8, 11: 8, 14: 8, 17: 8, 18: 8, 19: 8, 20: 8, 21: 8, 22: 16, 23: 8, 24: 16, 25: 32, 26: 16}`

Event 1 REGISTER_READY=32 matches N×2 (src+dst) ×2 roles. Event 6 PUBLISH=N.

Harness leftover: logcat pid **29766** still listed after TERM then `/proc` gone
(`REFUSE … missing -H 127.0.0.1`). Same family as R3 logcat 8008. Not a
product result. Experimental X killed; Stable **16085** unchanged.

## What this proves / does not prove

Pixel-correct 1514 oracle on the production path **and** the named Gate A
counters match N=8. A correct screen with counter mismatch would have been FAIL.

Machine-checked from `logcat-follow.txt` only: publish=consume=lookup=draw=
fence-satisfied=completed=SUCCESS=ACK=N; firstFailed=0; genFatal=0.

Does **not** separately prove design extras that were not counted here:
monotonic serial walk, pending/lease numeric baseline, violation mask=0,
`direct_to_legacy=0` as a named counter. Does **not** prove Production Gate A
(ownership/lifecycle completeness / enable). Does **not** authorize R5
(same-AHB cycles).

Evidence: `r4-oracle/`.
