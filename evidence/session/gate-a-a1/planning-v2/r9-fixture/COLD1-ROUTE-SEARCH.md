# COLD-1 ROUTE SEARCH — RESULT: NO DRIVABLE ROUTE

DATE 2026-09-22  MODE host-only source search. No device.
TARGET a renderer fatal path that simultaneously satisfies all six:
```
1  calls gateARendererFatal() / publishes fatal
2  the Activity therefore exits
3  X does NOT take the x-eof fatal
4  sessionNonce stays non-zero
5  registry / pendingCount already TERMINAL
6  the next Activity can reconnect and bump the generation
```
**Condition 5 is the one that fails, everywhere** — that is this document's result
and it still stands.

> **CORRECTION 2026-09-22 (COLD2-ROUTE-SEARCH.md §F).** The sentence that stood here
> — "Conditions 1-4 and 6 are satisfied by any published renderer fatal (Q11 + the
> COLD trilemma)" — was wrong, and the error is in condition 3. Condition 3 was
> written as "X does NOT take the x-eof fatal", which is too narrow: it asks only
> that one halt identity not fire, not that X still be running. Every published
> renderer fatal reaches X while X is inside `gateAWaitTerminal` for the same serial
> (`InitOutput.c:3539`), where `lorieGateADeriveResult` short-circuits on
> `fatal != 0` (`lorie.h:296-297`), `lorieGateAClassifyDirectDone` returns
> PRESERVE_FATAL, and `gateAXFatal("x-direct-not-success", ...)`
> (`InitOutput.c:3546`) takes the already-published branch and `_exit(127)`s
> (`InitOutput.c:3212-3217`). So conditions 3, 4 and 6 all fail too, for every
> published renderer fatal: **X is dead.** Condition 3 should read "X is still
> running when the next Activity connects", and no published renderer fatal
> satisfies it. This does not change COLD-1's verdict (still NO DRIVABLE ROUTE); it
> removes COLD-2's, which had been resting on the retracted sentence.

## METHOD

All 26 `gateARendererFatal` call sites in `renderer.cpp` were enumerated with their
enclosing function, then each was tested for **fixture drivability** — not merely for
whether it publishes. A fixture can control only: the R8 test-extension requests
(QueryVersion / RegisterBuffer / Checkpoint / Terminate), ordinary XCB protocol
actions, and environment-armed test faults.

## THE THREE CANDIDATES FROM V2-R9-FIXTURE, ALL REFUTED

```
r-tuple-mismatch      renderer.cpp:527-533, inside gateAValidateImport
                      TERMINAL: yes — REGISTER validation runs before any lease.
                      DRIVABLE: NO. Condition is
                        !lorieGateABoundTuple(&bn,&bg) || bn != nonce || bg != generation
                      i.e. the import's tuple must differ from the renderer's latch.
                      That is the bump/latch window (Q3/Q6), not something a fixture
                      can request. No test fault targets this site.

r-duplicate-ready     renderer.cpp:633-642, inside gateAValidateImport
                      TERMINAL: yes — same pre-lease position.
                      DRIVABLE: NO, and structurally so. It requires X to send a
                      SECOND REGISTER for the same (id, nonce, generation), but the
                      X-side registry refuses exactly that:
                        cmdentrypoint.cpp:121-124
                          if (dup != NULL && dup->meta.nonce == nonce
                              && dup->meta.generation == generation) return -1;
                          /* strict double-insert; P3 never does this */
                      X never emits the frame, so the renderer arm is unreachable
                      from the X side's own protocol.

r-ready-send          renderer.cpp:671, inside gateAValidateImport
                      TERMINAL: yes.
                      DRIVABLE: NO. Condition is gateASendReady() returning non-zero,
                      i.e. a socket write failure. A fixture cannot make the
                      renderer's write to X fail.
```

## SYSTEMATIC SWEEP OF EVERY RENDERER-SIDE TEST FAULT

Test faults are the only deliberate fault-injection mechanism, so if none of them
lands pre-lease with a publish, no drivable route exists. Every renderer-side
consumption site, by enclosing function:

```
site   enclosing function                    lease state    publishes a renderer fatal?
674    gateAValidateImport                   PRE-LEASE      NO — fault 16 only sends an
                                                            extra stale READY frame; it
                                                            does not fatal the renderer
934    Renderer::consumeGateAComposite       leased         yes (paths below)
937    Renderer::consumeGateAComposite       leased         yes
971    Renderer::consumeGateAComposite       leased         yes
1006   Renderer::consumeGateAComposite       leased         yes
1029   gateAFencePublishGateA                leased         yes
1043   gateAFencePublishGateA                leased         yes
1795   Renderer::applyPendingGpuCopiesLocked leased         yes — fault 8 (this is COLD-2)
1802   Renderer::applyPendingGpuCopiesLocked leased         NO publish (_exit only)
1809   Renderer::applyPendingGpuCopiesLocked leased         yes — fault 3
1991   Renderer::applyPendingGpuCopiesLocked leased         NO publish (_exit only)
2054   Renderer::applyPendingGpuCopies       post-batch     NO — fault 12 returns early,
                                                            no fatal, renderer survives
2221   Renderer::redrawLocked                leased         leads to :2236 fatal, gated on
                                                            gpuCopyOut.gateASeen
2267   Renderer::redrawLocked                leased         yes
2326   Renderer::redrawLocked                leased         NO — fault 12 again
```

```
=> The ONLY pre-lease test-fault site is 674, and it does not fatal the renderer.
=> Every published renderer fatal is in the composite / fence / draw path, i.e.
   strictly between the lease (cmdentrypoint.cpp:226-227, pendingCount = 1) and the
   ack (:270-271, pendingCount = 0).
=> Condition 5 is therefore unsatisfiable by any drivable route.
```

## VERDICT

```
R9-COLD-1  NOT CONSTRUCTIBLE.  Reclassify as WARM was:
           SOURCE-PROVEN / RUNTIME-NOT-CONSTRUCTIBLE, removed from the R9 device set.
R9-COLD-3  Same. It is COLD-1 plus a stricter evidence schema.
```
Not PASS, not FAIL, not INVALID, not runtime-qualified. If the product later gains a
published renderer fatal at a pre-lease point, or a fixture-drivable one, these two
must be reopened.

## THE FINDING THAT MATTERS MORE THAN COLD-1

Putting this search together with Q10 and the COLD trilemma yields a product-level
statement that no single question produced:

```
GATE A HAS NO REACHABLE CLEAN SAME-PROCESS GENERATION BOUNDARY.
```
Every route to a second generation in a surviving X is blocked or poisoned:
```
clean generation close   zeroes sessionNonce (InitOutput.c:3334-3335), so Gate A is
                         permanently dead in that X process afterwards (Q10). A clean
                         END is terminal, not a transition.
the bump path            lorieActivityConnected() retires the old generation WITHOUT
                         zeroing the nonce (InitOutput.c:575-586) — this IS the clean
                         transition, and it is correctly built. But reaching it needs
                         connect_ with a new fd, which needs either
                           a WARM reconnect entry point  -> does not exist in the
                             product (V2-R9-FIXTURE construction proofs), or
                           a new Activity (COLD)          -> whose death fatals X unless
                             generationFatal is ALREADY set (the trilemma)
=> a generation boundary in a surviving X requires a PRIOR FATAL.
```
The bump machinery is well built — nonce/generation asymmetry, registry rotation,
poison-then-close, fatal clearing — and is, as far as this trace can tell, entirely
unreachable without first entering a fatal state.

**Consequence for R9:** all three surviving cells are fatal-path cells. There is no
clean-path generation-boundary cell in R9 at all, and that is a property of the
product, not a gap in the test design.

**Consequence beyond R9:** this belongs to D-06 (production lifecycle redesign scope).
Production Gate A is expected to survive ordinary Activity lifecycle events; if the
only reachable generation boundary runs through a fatal, that is a production-lifecycle
question, not an R9 one. Recorded here, NOT decided here.

## FINAL R9 DEVICE CELL SET — 3 CELLS

```
#1  R9-COLD-2   CONSTRUCTIBLE NOW   fault 8  -> expected fatal x-bump-unterminal
#2  R9-F1       CONSTRUCTIBLE NOW   fault 16 -> expected fatal x-wrong-generation / 6
#3  R9-F2       after F1's expected fatal exists -> new nonce, empty registry,
                clean direct SUCCESS (event=5 present)

REMOVED, SOURCE-PROVEN / RUNTIME-NOT-CONSTRUCTIBLE
    R9-WARM-1, R9-WARM-2, R9-WARM-3     no product entry point for same-Activity
                                        warm reconnect
    R9-COLD-1, R9-COLD-3                no drivable published fatal with a terminal
                                        registry
DOES NOT EXIST
    V2-R9-RESET                         Q10 / D-01
```
Nine device packets in §8.7 (#8-16) become **three cells**. Every one of the six
removals is source-proven, not assumed, and each names the condition that would
reopen it.
