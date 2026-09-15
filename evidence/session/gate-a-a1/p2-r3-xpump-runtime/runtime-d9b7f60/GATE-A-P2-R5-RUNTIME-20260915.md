# Gate A P2 R5 FAIL — d9b7f60 same-AHB cycles — 2026-09-15

Exactly one fresh `p_r5_ahb_cycles` after R4 PASS on installed `d9b7f60`.
PROTO=1 TELEMETRY=1. COLD Activity. Fresh X `:3`.
Stable PID **16085** untouched. Teardown `NO_X3_RESIDUE`.
Do **not** silent-retry. Do **not** start R6–R10 without a new decision.
Production Gate A remains **BLOCKED**. No C++ patch from this cell.

## Runtime

| | |
|---|---|
| Command | `SERIAL=10.193.235.219:38663 CELL=…/runtime-d9b7f60/r5-ahb-cycles bash run-r5.sh` |
| Fixture | `patches/p_r5_ahb_cycles.c` SHA256 `80b77bfa…`; ELF `ba3a92d6…` glibc `/lib/ld-linux-aarch64.so.1` |
| Activity | COLD `--display 0` PID **21111** `GATEA_BIND` bound=1 |
| X `:3` | PID **14858** |
| Pixel checkpoints | **1, 16, 64, 256 PASS** exact maxΔ=0; CYCLE **768** exact |
| Hang | after CYCLE 768, before checkpoint 1024. Last GATEA at **02:35:32** |
| Operator stop | 02:51:20 SIGTERM fixture PID **15526** → `FIXTURE_EXIT=143` |
| Script | exit **1** (no `RESULT PASS`) |
| Fatal | none (`GATEA_FATAL_HALT` / SIGSEGV / `x-ready-timeout` absent) |
| Teardown | killed 14858, `STABLE 16085`, `NO_X3_RESIDUE` |

Follow-only GATEA_EVENT (14667 parsed records):

```text
publish=consume=success=815
ack=814 lease_release=814
relock_src=815 relock_dst=815 repair=813
unique serials 815 (min 5 max 819) src=6 dst=7
last: seq=14668 role=1 event=19 RELOCK_DST serial=819
```

Last complete-looking serial **818** has ACK+LEASE. Serial **819** stops after
SUCCESS + RELOCK_SRC + RELOCK_DST. No REPAIR(20) / ACK(21) / LEASE_RELEASE(23)
for 819. Client stayed in `do_sys_poll`. X later idle `do_epoll_wait`.
No further GATEA_EVENT for ~16 minutes.

`gateADoneDirect` (`InitOutput.c`) order after SUCCESS is relock → 24bpp
`lorieExaRepairDestXByteZero` (PrepareAccess) → ACK. Hang is **OBSERVED** at
that boundary. Stuck-inside-repair vs missing X11 reply after a silent
PrepareAccess FALSE is **NOT PROVEN**. Source fix **not authorized**.

## What this proves / does not prove

Same-AHB pair (src=6 dst=7) did **256+ exact cycles** with direct publish.
Does **not** qualify R5 (need 1024 and 4096). Does **not** prove Production
Gate A. Does **not** authorize R6.

Harness note: `logcat-follow.txt` grew to ~23 MB with non-GATEA lines
(HwcComposer/SDM/audit). Secondary; hang is the product result.

Evidence: `r5-ahb-cycles/` (do not overwrite).
Bounded rerun 2026-09-15 **FAIL REPRODUCED** (X 31265, serial 1283):
`GATE-A-P2-R5-RUNTIME-RERUN-20260915.md`. Do not overwrite `r5-ahb-cycles-rerun1/`.
