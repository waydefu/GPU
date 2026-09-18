# GATE A P2 R8 CLEAN-CELL ORCHESTRATION RCA — 2026-09-18

```
STATUS: R8_CLEAN_CELL_ORCHESTRATION_RCA_PROVEN
        tooling/construction bug, not product failure
        product SHA 65938a447639fce2adae61a15a2d8348e7c6455f FROZEN
        historical R8-C1 INVALID preserved
        Production Gate A BLOCKED
```

## Frozen C1 INVALID (immutable)

`p2-r8-runtime/runtime-65938a4/r8-c1/attempt-01/`

X 14713; fixture CLIENT_OK exit 0; X obs 40 BEGIN=1 END=0;
renderer 5 BEGIN=1 END=0; summary/ring NONE;
judge `R8_INVALID MISSING_END_x`.

## X END source (exact 65938a4)

`lorieCloseScreen()` in `InitOutput.c`:

X_CLOSE_ENTER → `gateACloseGeneration()` → X_CLOSE_RESULT → `lorieR8ObsEnd("x")`
then CloseScreen dump / gatea-summary.

Normal shutdown: `OsSignal(SIGTERM, GiveUp)` (`os/connection.c`) →
`GiveUp` sets `DE_TERMINATE` (`os/utils.c`) → dix `CloseScreen` then
`ddxGiveUp(EXIT_NO_ERROR)`. Not a crash path.

## Renderer END source

`LORIE_GATEA_MSG_GENERATION_CLOSE` in `renderer.cpp`: empty-registry
check → GENERATION_CLOSED send → unbind → `R_UNBOUND_FINAL` →
`lorieR8ObsEnd("r")`.

Cannot be produced merely because the fixture returned.

## Old runner defect

`run-r8-one-cell-65938a4.sh` ran fixture, optionally TERM, then collected
and judged immediately. No wait for CloseScreen / generation close /
unbind / producer END. Completeness was demanded before the only source
path that can emit it.

C2 / C5-full `CLIENT_HOLD` + `hold_until_hangup()` also cannot complete
under fixture→judge without shutdown-driven hangup.

## Not done

No product source change. No CI. No APK. Judge/collector/fixture/spec
SHA unchanged. Old C1 evidence not rewritten.
