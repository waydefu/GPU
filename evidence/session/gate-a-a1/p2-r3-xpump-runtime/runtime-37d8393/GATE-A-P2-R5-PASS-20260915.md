# Gate A P2 R5 PASS — 37d8393 — 2026-09-15

User grant 2026-09-15: after confirming the correction is recorded, classify
**R5 PASS**. This does **not** start R6–R8. Production Gate A remains **BLOCKED**.

## Record check (all present)

| Record | Status |
|---|---|
| Commit `37d8393` `fix(gatea): break R5 completion backpressure deadlock` | present, 2 files +58/−32 vs `d9b7f60` |
| Worktree | `src/f8-ahb-gatea-r5-fix` branch `fix/gatea-r5-backpressure-20260915` clean, tracks fork |
| Static impl | `p2-r5-backpressure-fix/GATE-A-P2-R5-STATIC-IMPLEMENTATION-20260915.md` |
| Host RED→GREEN / decoder / X-pump / ARM64 41==41 | recorded in static impl |
| CI **34918397208** QUALIFIED APK SHA256 `31ec7037…1638` Build ID `cc8cee05…` | provenance + install bind |
| Install experimental only | `runtime-37d8393/r0/INSTALL-37d8393-20260915.md` lastUpdateTime 2026-09-15 10:46:05 |
| Hang FAIL cells on `d9b7f60` | preserved (`r5-ahb-cycles/`, `r5-ahb-cycles-rerun1/`) |
| Corrected pixel cells | both `RESULT p_r5_ahb_cycles PASS` checkpoints 1/16/64/256/1024/4096 |
| Stable `:1` | PID **16085** UNTOUCHED |
| Control | `88e3f17` clean |

## PASS meaning

R5 on `37d8393` **PASS** because the `d9b7f60` hang (RELOCK_DST, 4096 not
reached) is **FALSIFIED** twice (X **14598**, X **24498**), 4096 same-AHB
cycles are exact RGB, X stayed alive, no watchdog, no fatal.

Follow logcat `ack=4095` on the recapture cell remains **OBSERVED**
capture-drop (serial **766** still has lease). Harness script exit 2 is
kept as a capture fact, not as a product hang. User classified that as
not blocking R5.

Does **not** prove Production Gate A. Does **not** authorize R6–R8, PR,
origin, Stable, HDMI, or a third recapture.

Authorities: this file;
`GATE-A-P2-R5-RUNTIME-20260915.md`;
`GATE-A-P2-R5-COUNTERS-20260915.md`.
