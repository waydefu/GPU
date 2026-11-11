# D-02 TRANSPORT SEAM REVIEW — whole-run finalization

DATE 2026-09-22  MODE host-only read-only source review, no build, no device
TREE `src/f8-ahb-gatea-r7-p1-arm` @ `14caa7b`
GOAL Pick the transport for "renderer process END authority = explicit whole-run
     finalization" (plan §23.2 D-02, deliberately left unfrozen).

## THE ACTUAL CONSTRAINT

The signal has two legs. Most candidate seams only solve one:
```
LEG 1  runner/fixture -> X        (a client already has X_LorieR8Terminate = opcode 3)
LEG 2  X -> renderer               <-- THIS is the binding constraint
```
The renderer cannot see an X extension request, cannot `getenv`
(`activity.cpp:158-159`: "Never getenv: the APK process does not inherit the X
launcher flag"), and reads X-side intent only from the shared mapping or a Gate A
frame.

## CANDIDATES

| # | seam | leg 2 solved? | cost | verdict |
|---|---|---|---|---|
| A | new opcode `X_LorieR8FinalizeObs = 4` | **NO** | protocol growth, still needs a leg-2 seam | rejected — does not solve the binding constraint |
| B | renderer peer-HUP handler (`activity.cpp:415-438`) | n/a | zero protocol | **rejected — semantically wrong** |
| C | existing reserved word in `struct LorieGateATestFault` | YES | layout-neutral | **SELECTED** |
| D | new `LorieGateAMsgType` frame | YES | **new Gate A ABI** | rejected — STOP condition |
| E | `gateATelemetry.reserved` bits | YES | already carries telemetry-published | rejected — overloads a live field |
| F | do nothing; let the outer END fire early | n/a | zero | **rejected — requires changing the frozen terminal contract** |

### Why B is rejected (this is the non-obvious one)
`activity.cpp:415-438` is a real process-terminal path, but at HUP time the renderer
**cannot distinguish "run over" from "X restarting, warm reconnect incoming"** — that
is exactly Q1's finding (`Q1-Q2-activity-restart-boundaries.md`, Q1-F1/F2, with
`MainActivity.java:604-606` retrying every 250 ms). Finalizing there would end the
observation stream in the middle of a multi-epoch run. Using it anyway would require
assuming "X death == run end", which is precisely the harness assumption D-02 forbids
pre-committing to.

### Why F is rejected
`lorie_r8_obs.c:184-192` DROPS every record after `r8Ended[ix]` and emits
`R8_OBS_POST_END` -> `R8_INVALID POST_END_OBSERVATION`. That behaviour is locked by
host tests (`test_r8_obs_terminal.py` cases `x_end_then_any`,
`r_unbound_end_then_surface`). Changing it is a **frozen R8 contract change** = STOP.

## SELECTED: SEAM C — `struct LorieGateATestFault` reserved word

### It is ABI-layout-neutral
```
lorie.h:1534-1543   struct LorieGateATestFault {
                      uint32_t magic;    /* +0  */   uint32_t version;  /* +4  */
                      uint32_t cell;     /* +8  */   uint32_t armed;    /* +12 */
                      uint32_t consumed; /* +16 */   uint32_t pad;      /* +20 */  <-- free
                      uint64_t targetGeneration; /* +24 */
                      uint64_t targetOrdinal;    /* +32 */ }            /* size 40 */
```
All five existing static asserts stay literally unchanged and still pass:
```
lorie.h:1545  sizeof == 40
lorie.h:1546  offsetof(magic) == 0
lorie.h:1547  offsetof(targetGeneration) == 24
lorie.h:1548  offsetof(targetGeneration) % 8 == 0
lorie.h:1549  offsetof(consumed) % 4 == 0
```
`pad` exists purely to align `targetGeneration` to +24. Giving it a name and a
meaning changes **no size, no offset, no alignment**.

### The word is provably free
```
grep '\.pad\b|->pad\b' over *.c *.cpp *.h  ->  ONE hit:
InitOutput.c:2586   st->gateATestFault.pad = 0;
```
That single site is inside `lorieGateATestFaultPublishFromEnv`
(`InitOutput.c:2558`), called exactly once from `OsVendorInit`
(`InitOutput.c:513`) at process startup. The whole region is already `memset` to 0 at
`InitOutput.c:510`. **The word is never read anywhere.**

### It is test-only on both sides
The struct is the test-fault channel the renderer already reads from the shared tail
(`lorie.h:1510`: "Renderer never getenv; it reads gateATestFault from the shared
tail"). Every producer and consumer is inside
`#ifdef LORIE_ENABLE_R8_TEST_SUPPORT`. **No Production Gate A semantics are touched.**

### `verify-r8-support.py:66` still passes
The check is literally `need('lorieR8ObsEnd' not in term_fn, ...)` where `term_fn` is
the body of `ProcLorieR8Terminate`. Seam C adds a **publish** call there, not
`lorieR8ObsEnd`. The renderer, not X, performs the finalization.

### The ordering is race-free, and that is provable from existing source
```
ProcLorieR8Terminate  publishes runFinalize, then calls GiveUp(0)   lorie_r8_test.c:342
GiveUp                sets dispatchException |= DE_TERMINATE         os/utils.c:426-430
X then unwinds: Dispatch -> CloseScreen -> lorieCloseScreen          InitOutput.c:1461, :1240
                -> gateACloseGeneration()                            InitOutput.c:3289
                -> gateAWaitCleanAck("x-generation-close-wait")      InitOutput.c:3331-3332
                   ^^ X BLOCKS here until the renderer sends GENERATION_CLOSED
```
The renderer is therefore **guaranteed to be running** between the publish and X's
exit — it has to be, to produce the ack. And the renderer's ack path
(`renderer.cpp:801-820`) is the exact code that sets
`r8RendererGenerationUnbound = 1` today (`:820`), so the flag is read at the point
where the decision is already being made.

### It reproduces current R8 behaviour EXACTLY — verified against frozen evidence
The new authority is "the fixture sent TERMINATE". Measured across all ten passing
attempts of `runtime-b984ded` (zero device cost):
```
cell                        r_BEGIN  r_END  x_END  TERMINATE sent
r8-c1/attempt-13               1       1      1        1
r8-c2/attempt-03               1       1      1        1
r8-c3-disconnect/attempt-03    1       1      1        1
r8-c3-window/attempt-04        1       1      1        1
r8-c4/attempt-03               1       1      1        1
r8-c5-full/attempt-04          1       1      1        1
r8-c5-overflow/attempt-03      1       1      1        1
r8-d/attempt-04                1       1      1        1
r8-p1/attempt-03               1       0      0        0    (fatal cell)
r8-p2/attempt-01               1       0      0        0    (fatal cell)
```
**Perfect correlation: the renderer END appears in exactly the 8 cells that sent
TERMINATE, and in neither of the 2 that did not.** Gating finalization on the
terminate-published flag is therefore **observationally equivalent** on the entire
frozen R8 corpus — it re-derives the same outcome from a correct authority instead of
an incidental one (first generation-unbind).

## STOP-CONDITION SELF-CHECK
```
Gate A production semantics changed?   NO  — test-only struct, all sites #ifdef'd
Frozen R8 contract changed?            NO  — observationally equivalent, 10/10 (above);
                                             the terminal DROP contract is untouched
New ABI required?                      NO  — no size, offset or alignment change; all
                                             five static asserts unchanged; the word
                                             was never read. A previously-unused
                                             reserved word gains a meaning, and both
                                             processes ship in one artifact.
Design-freeze contradiction found?     NO  — Q1/Q4/Q5/Q6/Q9/Q11 all consistent; this
                                             review USES Q1-F1 to reject seam B.
=> No stop condition triggered. Proceeding to implementation.
```
Note for the record: if the reviewer considers **any** semantic assignment inside a
cross-process struct to be an ABI change — even a layout-neutral one to a
never-read reserved word — then seam C is the single thing to veto, and seam D (a
real new frame type) would be the only remaining option at strictly higher cost.

## IMPLEMENTATION SCOPE THAT FOLLOWS
```
1  lorie.h                  pad -> runFinalize + release/acquire accessors
2  lorie_r8_test.c          ProcLorieR8Terminate publishes runFinalize before GiveUp(0)
3  renderer.cpp             lorieR8MaybeFinalizeRendererObs() requires the flag
4  lorie_r8_obs.c           per-epoch tuple: obs variant taking explicit nonce/generation
5  renderer.cpp             R_EPOCH_BEGIN / R_EPOCH_END ordinary phase records
6  cmdentrypoint.cpp        DEFER_ENQUEUE obs moved AFTER the tuple assignment (Q6-F1)
7  activity.cpp             gateAMappedState cleared on every unmap path (Q4-F1)
8  tests/r8                 host tests + verify-r8-support.py extended
```
