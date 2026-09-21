# V2-R8-C2-SRC-TRACE

DATE    2026-09-21   MODE host-only, read-only, no attempt consumed
VERDICT **CONSTRUCTIBLE** — existing Class-B orchestration IS sufficient. Not DESIGN_REQUIRED.

## Q1 — which file / symbol / call path establishes CLIENT_HOLD
```
tests/r8/p_r8_lifecycle.c  cell_c2()
    pair_create(c, s, fmt32, fmt24, &a, PAIR_W, PAIR_H)
    pair_composite(c, &a, ...)
    /* deliberately NO pair_free(c, &a) — the resource stays live */
    flog("RESULT p_r8_lifecycle C2 CLIENT_HOLD")
```
The literal marker `CLIENT_HOLD` is the contract surface: the runner greps for it in
`fixture.jsonl` / `fixture.stdout` (run-r8-one-cell-b984ded-v6.sh L443) and only then
writes `hold-status.txt = CLIENT_HOLD`. Server side the retained pair is observable in
the checkpoint reply fields `pair_state` / `pair_src` / `pair_dst`.

## Q2 — who controls the holder lifecycle
The holder is the fixture process's own X connection; holder lifetime == fixture
process lifetime. The runner launches it in the BACKGROUND for Class B
(`CLASS=B` set at L360 for R8-C2 and R8-C5-full), records
`fixture-process.json {"mode":"hold","killed_by_runner":false}`, then polls up to 20s
for the marker. The runner never kills it to force a close:
```
L443-452  if the client dies before the marker -> invalid "HOLD_CLIENT_DIED_EARLY"
L573-574  FA_ARG derived from /proc/$FIXPID, passed as --fixture-alive
L582      --fixture-killed-by-runner "$FIXTURE_KILLED"   (initialised 0 at L424)
r8_orchestration_v2.py permit_judge -> "HOLD_CLIENT_KILLED_BY_RUNNER" if it was
```
This directly implements §7.2's three forbidden smuggles: holder death is refused as
INVALID rather than accepted as a clean close, and a runner-initiated kill blocks the
judge outright.

## Q3 — how the terminate request coexists with the holder
`p_r8_lifecycle.c main()`, after the cell function returns:
```c
if (!rc && strcmp(cell, "R8-P1") && strcmp(cell, "R8-P2"))
    rc = r8_terminate(c);      /* SAME connection c, resource still retained */
xcb_disconnect(c);             /* only afterwards */
```
`X_LorieR8Terminate` (opcode 3) is therefore delivered while the client connection is
still open and the pair has never been freed. Server side that is
`ProcLorieR8Terminate -> GiveUp(0) -> DE_TERMINATE`, i.e. the generation close runs
with a registered resource still live — which is precisely the state C2 exists to
exercise (registered resource retirement during close), and it is NOT a
client-disconnect close.

## Contract check
`V2-P009` reports R8-C2 contract-consistent: `judge_c2` requires only
`X_CLOSE_ENTER`, `X_CLOSE_RESULT`, `R_UNBOUND_FINAL` plus stream completeness — all
three were produced for real in R8-C1 attempt-11, none needs a client request the
fixture does not send.

## Residual risk carried into the run (stated, not resolved)
`--fixture-alive` is sampled at L573, after the cell has terminated and disconnected,
so it is expected to be 0 by then. Whether permit-judge treats that as acceptable for
Class B is not provable by source reading alone; if it refuses, the classifier will be
INVALID `JUDGE_NOT_PERMITTED` and the attempt is spent establishing that fact.
