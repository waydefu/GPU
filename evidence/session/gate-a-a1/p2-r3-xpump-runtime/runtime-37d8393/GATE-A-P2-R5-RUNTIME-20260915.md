# Gate A P2 R5 corrected-artifact cell — 37d8393 — 2026-09-15

Exactly one authorized install + one R5 on qualified `37d8393`.
Historical `d9b7f60` cells **not overwritten**. No silent retry. No R6.
Stable PID **16085** untouched. HDMI observe-only (user: no external).
Production Gate A remains **BLOCKED**.

## Binding

| | |
|---|---|
| HEAD | `37d839323255b4830d657da3bcbf7f616bc78ad3` |
| CI | **34918397208** |
| Package | `com.waydefu.x11gpu` `1.03.01-37d8393-15.09.26` lastUpdateTime **2026-09-15 10:46:05** |
| APK SHA256 | `31ec7037d3f1dc27836b8719ab21527e2943a21bc2763d08a2dbc51f702c1638` MATCH local=staged=installed |
| Build ID | `cc8cee05dd7e4ae35085e33dec25bbb2229cee12` MATCH |
| serial | `10.12.7.144:34863` live-fetched `_adb-tls-connect._tcp.local.` |
| Install | `runtime-37d8393/r0/` session **2034206973** Success |

## R5 runtime

| | |
|---|---|
| Command | `SERIAL=10.12.7.144:34863 CELL=…/runtime-37d8393/r5-ahb-cycles bash run-r5-corrected.sh` |
| Script exit | **2** `R5_AHB_CYCLES_CORRECTED_FAIL` |
| Fixture ELF | SHA256 `ba3a92d6c97cdce0ad8ca53feb544ff060f4b3f54a12be75969b76cdb319c828` (same as d9b7f60 cells) |
| Env | PROTO=1 TELEMETRY=1 DEBUG unset; COLD Display0; silent logcat; stall 45 s / max 300 s |
| Activity | PID **32711** `GATEA_BIND` version=1 bound=1 nonce=`10195072753024455135` |
| X `:3` | PID **14598** ALIVE_8S and X3_STILL_ALIVE after fixture, then torn down |
| Watchdog | **NONE** (no stall, no max) |
| Fixture | `FIXTURE_EXIT=0` `RESULT p_r5_ahb_cycles PASS` checkpoints **1/16/64/256/1024/4096** fail=0 maxΔ=0 |
| Fatal | none (`GATEA_FATAL_HALT` / SIGSEGV / `x-ready-timeout` absent) |
| Teardown | killed 14598, `STABLE 16085`, `NO_X3_RESIDUE` |
| logcat | 20 096 543 bytes filtered; GATEA_EVENT regex **73735** |

Follow-only counters:

```text
publish=4095 consume=4096 lookup=4096 draw=4096 fence=4094
completed=4096 success=4096 ack=4096 lease_release=4096 repair=4096
relock_dst=4095
unique publish serials 4095 (min 5 max 4100) src=6 dst=7
firstFailed=0 genFatal=0 lookup_fail=0 fence_timeout=0 fence_error=0
```

Publish serials start at **5**, same class as historical `d9b7f60` hangs
(min 5 max 819 / 1283). Expected span for 4096 cycles is 5..4100.

One publish hole: serial **3539** has consume/lookup/draw/fence/completed/
success/repair/ack/lease, **no event=6 line**. Fence holes serial **317** and
**2862** still have publish+completed+success. Relock hole serial **397** still
has repair+ack. These are **logcat line drops** under silent-default at ~900
events/s, not a RELOCK_DST hang.

Harness leftover: logcat pid **14549** still listed after TERM then `/proc`
gone. Same family as R4 logcat 29766. Not a product result.

## Classification

| Claim | Label |
|---|---|
| `d9b7f60` hang (serial 819 / 1283 RELOCK_DST, 4096 not reached) reproduced here | **FALSIFIED** |
| 4096 same-AHB cycles exact RGB, X alive, no watchdog | **PROVEN** |
| Strict harness N=4096 publish=fence=… equality | **FAIL** (script exit 2) |
| Missing publish/fence/relock lines while sibling events exist | **OBSERVED** logcat-drop class |
| Production Gate A | still **BLOCKED** |

User 2026-09-15 later classified this cell plus the counters recapture as
**R5 PASS** (`GATE-A-P2-R5-PASS-20260915.md`): hang FALSIFIED and 4096 exact
pixels are the product result; follow-logcat holes are capture-drop.

## What this does not authorize

No second R5. No R6–R10. No C++ patch. No treating counter-mismatch as
Production PASS. Historical FAIL cells remain authority for the `d9b7f60` hang.

Evidence: `r0/`, `r5-ahb-cycles/`.
