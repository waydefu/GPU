# R9-COLD-2 — two frozen INVALID attempts against a cell that was later REMOVED

DATE 2026-09-22  PRODUCT dc94485

Both attempts stay **frozen INVALID**. The removal of R9-COLD-2 does not reclassify
them: a consumed attempt keeps its number and its verdict
(`policy.frozen_attempt_policy`). Neither is a PASS, a FAIL, or evidence about the
cell's hypothesis.

## attempt-01 — `x-r8-env` at startup

```
judge.json   R9_INVALID  IDENTITY_FIELD_MISSING_x_pid
raw-logcat   GATEA_FATAL_HALT what=x-r8-env reason=5
fixture      FAIL connect errno=111        (X was already dead; :3 refused)
```

Cause: the runner armed R8 observation (`TERMUX_X11_R8_ARM=1`, `R8_CASE=R8-C1`)
alongside an R9 fault. `parseArm()` in `lorie_r8_obs.c` hard-codes the only two legal
(case, fault) pairs — `R8-P1`/`destroy-while-gpu-owned` and
`R8-P2`/`close-while-lease` — and sets `r8EnvFatal` for any other case with any
fault. X halted before the cell ran.

## attempt-02 — the R8 test extension was absent

```
judge.json   R9_INVALID  IDENTITY_FIELD_MISSING_x_fd_table_had_previous_conn_fd
raw-logcat   GATEA_FATAL_HALT what=x-hup reason=6
fixture      FAIL LORIE-R8-TEST missing
```

Cause: disarming R8 to avoid attempt-01's halt also stops
`LorieR8TestExtensionInit()` registering the extension (`lorieR8ValidateStartupEnv()`
returns != 1, so it returns early), and `p_r8_lifecycle` aborts on its first request.
This is what produced the extension-free fixture `tests/r9/p_r9_boundary.c`.

**This attempt is also corroborating evidence for the removal.** No composite ever
ran, so no lease and no renderer fault existed — and `am force-stop` on its own still
killed X: `GATEA_FATAL_HALT what=x-hup reason=6`, with `generation=1` and
`generationFatal=6` in the accompanying summary. That is `lorieGpuCopyWait`'s
`!connectionAlive` branch (`InitOutput.c:1963-1965`) firing on a bare Activity
teardown, which is exactly the structural fact that makes a second
`lorieActivityConnected()` unreachable.

## Why the cell is gone

`planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md` — **SOURCE-PROVEN /
RUNTIME-NOT-CONSTRUCTIBLE**, on the same terms as R9-WARM-1/2/3. Not PASS, not FAIL,
not INVALID as a *cell*, not runtime-qualified. `x-bump-unterminal`
(`cmdentrypoint.cpp:391`) needs a second `lorieActivityConnected()` with
`generation != 0`, and no X process can reach one.

Reopen if the product gains a renderer fatal publisher reachable outside an X terminal
wait, or a warm reconnect/rebind entry point. `judge-r9.py` refuses the cell with
`R9_BLOCKED` until then, and `verify-r9-support.py` pins the six source facts the
removal rests on.
