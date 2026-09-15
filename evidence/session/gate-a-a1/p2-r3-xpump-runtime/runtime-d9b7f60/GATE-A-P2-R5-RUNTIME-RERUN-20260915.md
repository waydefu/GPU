# Gate A P2 R5 FAIL REPRODUCED — d9b7f60 bounded rerun — 2026-09-15

Exactly one authorized bounded rerun after first-cell FAIL and source+log
investigation. Same installed APK `d9b7f60`, same ELF `p_r5_ahb_cycles`.
PROTO=1 TELEMETRY=1. COLD Activity. Fresh X `:3`.
Harness-only deltas: logcat `gatea-telemetry:V gatea-a1:V LorieNative:I *:S`;
fixture-output stall watchdog 45 s / max 240 s.
First cell `r5-ahb-cycles/` **not overwritten**.
Stable PID **16085** untouched. Teardown `NO_X3_RESIDUE`.
No second retry. No C++ patch. Do **not** start R6–R10 without a new decision.
Production Gate A remains **BLOCKED**.

## Runtime

| | |
|---|---|
| Command | `SERIAL=10.193.235.219:38663 CELL=…/runtime-d9b7f60/r5-ahb-cycles-rerun1 bash run-r5-rerun.sh` |
| Script exit | **2** (`R5_AHB_CYCLES_RERUN_FAIL`) |
| Fixture | ELF SHA256 `ba3a92d6c97cdce0ad8ca53feb544ff060f4b3f54a12be75969b76cdb319c828` (same as first cell) |
| Activity | COLD `--display 0` app PID **29908** `GATEA_BIND` bound=1 nonce=`3732133409241769135` |
| X `:3` | PID **31265** |
| Pixel | checkpoints **1/16/64/256/1024 PASS** exact maxΔ=0; CYCLE **1216** exact |
| Hang | after CYCLE 1216, before 1280/4096. Last GATEA **03:01:22.598** |
| Watchdog | 45 s fixture.out stall → SIGTERM fixture PID **31560** → `FIXTURE_EXIT=143` |
| wchan | fixture `do_sys_poll`; X `do_epoll_wait` (State R) |
| Fatal | none (`GATEA_FATAL_HALT` / SIGSEGV / `x-ready-timeout` absent) |
| Teardown | killed 31265, `STABLE 16085`, `NO_X3_RESIDUE` |
| logcat follow | 6 263 378 bytes (filtered). First cell was 23 071 697 unfiltered |

Follow-only GATEA_EVENT (23021 parsed records):

```text
publish=consume=lookup=draw=fence=completed=success=1279
ack=1278 lease_release=1278 repair=1278
relock_dst=1279
unique serials 1279 (min 5 max 1283) src=6 dst=7
last: seq=23020 role=1 event=19 RELOCK_DST serial=1283
```

Last complete-looking serial **1282** has REPAIR+ACK+LEASE.
Serial **1283** stops after SUCCESS + RELOCK_SRC + RELOCK_DST.
Renderer had already logged COMPLETED (`event=14`) for 1283.
No REPAIR(20) / ACK(21) / LEASE_RELEASE(23) for 1283.

Same class as first cell (X **14858**, serial **819**, ack=success−1).
Not the same serial or cycle count. First hang at n≈768 / 1024 not reached;
this rerun passed checkpoint 1024 and hung before 4096.

Watchdog false-positive from CYCLE-every-64 stdout gap is **FALSIFIED**:
~1216 cycles in ~24 s of GATEA (~1.2 s per 64-cycle print gap); stall waited
45 s with no further fixture output and no GATEA after 03:01:22.598.

## What this proves / does not prove

**PROVEN:** R5 hang **REPRODUCED** on `d9b7f60` at `gateADoneDirect` after
SUCCESS: last trace is RELOCK_DST, then silence; client in `poll`; X later
`epoll_wait`. Same-AHB pair (src=6 dst=7) did **1024 exact cycles** then
stuck. Filtered logcat did not prevent the hang.

**Does not** qualify R5 (need 4096 + N=4096 counter equality).
**Does not** prove Production Gate A.
**Does not** prove H1 (lock livelock) or H2 (`conn_fd` write-block) — still
INFERRED from source order.
**Does not** authorize a C++ patch or R6.

Evidence: `r5-ahb-cycles-rerun1/` (do not overwrite).
First cell: `r5-ahb-cycles/` + `GATE-A-P2-R5-RUNTIME-20260915.md`.
Investigation: `GATE-A-P2-R5-INVESTIGATION-20260915.md`.
