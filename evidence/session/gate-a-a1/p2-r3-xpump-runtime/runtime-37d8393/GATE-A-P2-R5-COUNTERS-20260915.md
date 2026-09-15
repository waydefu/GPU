# Gate A P2 R5 logcat-counter recapture — 37d8393 — 2026-09-15

Exactly one authorized extra cell to complete follow logcat counters.
First corrected cell `r5-ahb-cycles/` **not overwritten**. No silent retry. No R6.
Stable PID **16085** untouched. Production Gate A remains **BLOCKED**.

## Runtime

| | |
|---|---|
| Command | `SERIAL=10.12.7.144:34863 CELL=…/runtime-37d8393/r5-ahb-cycles-counters1 bash run-r5-counters.sh` |
| Script exit | **2** `R5_AHB_CYCLES_COUNTERS_FAIL` |
| Harness-only | `logcat -G 16M` (restored 2M after), filter `gatea-telemetry:V *:S`, 5 s drain |
| Activity | COLD Display0; `GATEA_BIND` not in follow (LorieNative filtered) |
| X `:3` | PID **24498** ALIVE then torn down |
| Watchdog | **NONE** |
| Fixture | `FIXTURE_EXIT=0` `RESULT p_r5_ahb_cycles PASS` checkpoints **1/16/64/256/1024/4096** fail=0 maxΔ=0 |
| Fatal | none |
| Teardown | `STABLE 16085` `NO_X3_RESIDUE` |
| logcat | 9 112 981 bytes; GATEA_EVENT **73738** |

Follow-only counters:

```text
publish=4096 consume=4096 lookup=4096 draw=4096 fence=4096
completed=4096 success=4096 ack=4095 lease_release=4096 repair=4096
relock_dst=4096
unique publish serials 4096 (min 5 max 4100) src=6 dst=7
firstFailed=0 genFatal=0
```

Vs first corrected cell (publish 4095 / fence 4094): publish and fence now
match N. Remaining hole: **ack event=21 serial 766** — that serial still has
publish/consume/lookup/draw/fence/completed/success/repair/lease. Event 18
(RELOCK_SRC) missing serial **1225** only (not in PASS predicate). Same
logcat-drop class, one line.

## Classification

| Claim | Label |
|---|---|
| 4096 pixel exact, hang absent | **PROVEN** (repeat of first 37d8393 cell) |
| publish=fence=completed=success=lease=4096 | **PROVEN** this cell |
| Strict ack==4096 | **FAIL** (one dropped GATEA_EVENT line) |
| Production Gate A / R6 | still **BLOCKED** / **NOT STARTED** |

User 2026-09-15 classified R5 **PASS** despite ack=4095:
`GATE-A-P2-R5-PASS-20260915.md`.

Evidence: `r5-ahb-cycles-counters1/`. First cell remains `r5-ahb-cycles/`.
