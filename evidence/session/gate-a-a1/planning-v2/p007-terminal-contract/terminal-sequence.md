# V2-P007 — TERMINAL CONTRACT SOURCE BIND

PACKET      V2-P007-TERMINAL-CONTRACT-SOURCE-BIND
DATE        2026-09-21
MODE        HOST-ONLY / READ-ONLY / NO DEVICE MUTATION / NO GRANT CONSUMED
VERDICT     SOURCE_BOUND
CLOSES      V-3 (was PARTIALLY_RESOLVED) · GAP-5 · D-14 · R-23

## Source binding

| role | identity | verified |
|---|---|---|
| PRODUCT | `b984dedcac731b77ca4cf8899f8a78b7848ad083` | read via `git show b984ded:<path>` |
| pinned xserver submodule | `65d790bd208ec380b196eb98f144abb0b32e334d` | `ls-tree b984ded -- lorie/src/main/cpp/xserver` == local submodule HEAD, working tree clean |
| worktree | `src/f8-ahb-gatea-r7-p1-arm` | product branch `feat/gatea-r8-lifecycle-support-20260918` |

The xserver teardown is NOT in the product repo; it is the pinned submodule.
Any claim about DIX ordering that does not cite `65d790bd` is unbound.

## Bound terminal sequence (verbatim order, dix/main.c @65d790bd L274-L360)

```
Dispatch() returns
  UnrefCursor · UndisplayDevices · DisableAllDevices
  FreeScreenSaverTimer
  CloseDownExtensions
  FreeAllResources()                      <-- DIX resource teardown
  CloseInput · InputThreadFini
  CloseDownDevices
  CloseDownEvents
  for gpuscreens desc : (*CloseScreen)
  for screens    desc : (*CloseScreen)    <-- lorieCloseScreen runs HERE
  ReleaseClientIds · dixFreeRegistry
  FreeFonts()
  FreeAllAtoms · FreeAuditTimer · DeleteCallbackManager
  ClearWorkQueue()                        <-- UNCONDITIONAL, both DE_RESET and DE_TERMINATE
  if (dispatchException & DE_TERMINATE) CloseWellKnownConnections()
  OsCleanup((dispatchException & DE_TERMINATE) != 0)
  if (dispatchException & DE_TERMINATE) { ddxGiveUp(EXIT_NO_ERROR); break; }
  free(ConnectionInfo)                    <-- reset path only, loops back
```

## Rulings

### RULING-1 — `FreeAllResources()` precedes `CloseScreen`. V-3 conflict resolved.
The legacy phrase "CloseScreen -> resource teardown" is FALSE if read as DIX
`FreeAllResources()`. V2.2's hypothesis is CONFIRMED: the teardown that follows
CloseScreen is Gate A's own registry drain inside `lorieCloseScreen` ->
`gateACloseGeneration()` (InitOutput.c @b984ded L1228-L1245), not DIX.
Judge rules MUST NOT expect DIX resource teardown after CloseScreen.

### RULING-2 — `ClearWorkQueue()` IS a mandatory transit point but is NOT a terminate discriminator.
It executes unconditionally on every `Dispatch()` return. A trace containing
ClearWorkQueue proves nothing about DE_TERMINATE vs DE_RESET.
Answer to the P007 question "ClearWorkQueue required/optional/absent": **REQUIRED
as transit, FORBIDDEN as discriminator.**

### RULING-3 — `ddxGiveUp()` is the sole X `END` producer and is DE_TERMINATE-gated.
InitOutput.c @b984ded L636-L651: `ddxGiveUp` calls `CloseWellKnownConnections`,
`UnlockServer`, then `lorieR8ObsEnd("x")`, then `exit(error)`.
Its own comment pins it "after CloseScreen, FreeFonts, and ClearWorkQueue, and only
on DE_TERMINATE" -- source-confirmed above. V-1 and V-8 hold.

### RULING-4 — entry point is PROVABLE, and this is the C1 discriminator.
`GiveUp(int sig)` (os/utils.c @65d790bd L426-L433) does exactly:
```
dispatchException |= DE_TERMINATE;
isItTimeToYield = TRUE;
```
The `sig` argument is unused. Therefore `GiveUp(0)` is an in-process direct call,
not a signal -- V-2 CONFIRMED at source level.

Two and only two entry points reach it in this build:
```
A. test-control : ProcLorieR8Terminate (lorie_r8_test.c @b984ded L327-L344)
                  emits  R8_OBS x TEST_CONTROL {"op":"TERMINATE"}
                  then WriteToClient(reply), then GiveUp(0)
B. signal       : OsSignal(SIGINT, GiveUp) / OsSignal(SIGTERM, GiveUp)
                  (os/connection.c @65d790bd L299-L300) -- NO TEST_CONTROL record
```
**C1 requires entry point A.** The presence of `TEST_CONTROL {"op":"TERMINATE"}` in
the x stream is the positive proof; its absence means the terminate did not come
from test control, regardless of how clean the rest of the trace looks.
The runner already enforces this: `invalid "MISSING_TEST_CONTROL_TERMINATE"`.

### RULING-5 — DE_TERMINATE-gated steps the plan did not record.
`CloseWellKnownConnections()` and `OsCleanup(TRUE)` run between `ClearWorkQueue()`
and `ddxGiveUp()`, both gated on DE_TERMINATE. `ddxGiveUp` then calls
`CloseWellKnownConnections()` a second time. This double call is upstream behaviour,
not a defect, and MUST NOT be classified as an anomaly.

## Consequences for C1 EXPECTED_TRACE

```
REQUIRED, in order:
  R8_OBS x TEST_CONTROL {"op":"TERMINATE"}      <-- entry-point proof (RULING-4)
  R8_OBS x X_CLOSE_ENTER  {"path":"lorieCloseScreen"}
  (gateACloseGeneration internals)
  R8_OBS x X_CLOSE_RESULT {"generation_close":"invoked"}
  R8_OBS x END                                   <-- from ddxGiveUp (RULING-3)

MUST NOT be asserted:
  - DIX FreeAllResources after CloseScreen          (RULING-1: it is before)
  - ClearWorkQueue as evidence of DE_TERMINATE      (RULING-2)
  - any ordering claim not citing 65d790bd          (unbound)

MUST NOT be flagged as anomaly:
  - CloseWellKnownConnections appearing twice       (RULING-5)
```

V2.1's hardcoded `CloseScreen -> resource drain -> ClearWorkQueue` is RETIRED as a
judge rule. This sequence supersedes it.
