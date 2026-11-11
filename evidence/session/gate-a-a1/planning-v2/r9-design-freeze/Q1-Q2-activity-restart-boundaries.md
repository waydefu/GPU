# R9 DESIGN FREEZE — Q1 / Q2 (warm new X vs cold Activity restart)

## QUESTIONS
```
Q1  warm new X, same Activity: what does the Activity retain?
Q2  cold Activity restart: what is genuinely rebuilt?
```

## SOURCE AUTHORITY
```
TREE   src/f8-ahb-gatea-r7-p1-arm @ 14caa7b
DATE   2026-09-22
MODE   host-only, read-only, no device, no adb, no build, no CI, no source mutation,
       no runtime attempt
DEPTH  Q3-Q11 standard. Every claim cites file:line. Unsettled -> NOT PROVEN.
BUILDS ON Q4 (13-item renderer inventory — this trace filters it per path rather
       than re-deriving it), Q5 (rebind-busy), Q11 (who dies with whom).
```

## FRAMING — the two questions are one boundary seen from each side

Q11 proved that a **bound** Activity always dies when X dies
(`lorie_gatea_hup_class.h:32-36`; `activity.cpp:421-426`). Therefore:
```
Q1 (Activity SURVIVES a new X)  is reachable ONLY via the UNBOUND arm, or via a
                                connection replaced WITHOUT the old one dying.
Q2 (Activity process DIES)      is the ordinary outcome of any bound fatal.
```
So Q1 is the narrow path and Q2 is the common one — the opposite of how the question
order suggests.

## Q1 — WARM NEW X, SAME ACTIVITY

### The flow is first-class, not incidental
```
MainActivity.java:604-606   if (service == null) { LorieView.requestConnection();
                                handler.postDelayed(this::tryConnect, 250); }
MainActivity.java:609-612   ParcelFileDescriptor fd = service.getXConnection();
                            LorieView.connect(fd.detachFd());
MainActivity.java:577       on binder death -> LorieView.connect(-1)
activity.cpp:540            connect_(env, cls, fd)
```
A 250 ms reconnect retry loop exists in the UI. The renderer's own comment states the
intent outright:
```
renderer.cpp:1240-1241  "Created once, never recreated; only the fd is (re)sent to
                         the X server whenever it (re)connects."
```

### What `connect_` actually resets — and what it leaves alone
```
activity.cpp:544-548   ALooper_removeFd(oldFd); conn_fd = -1; close(oldFd)
activity.cpp:549       g_renderer.setSharedState(NULL)   -> GL thread munmaps the old
                                                            mapping (renderer.cpp:2427)
activity.cpp:550       g_renderer.removeAllBuffers()     -> LEGACY lists only
                                                            (renderer.cpp:1526-1540)
activity.cpp:556-560   conn_fd = fd; ALooper_addFd(..., xcallback, NULL)
activity.cpp:565-567   re-send the wakeup cond fd (EVENT_RENDERER_WAKEUP_COND + SCM_RIGHTS)
```

**RETAINED across a warm new X** (from Q4's inventory, filtered to this path):
| item | decl | why it survives |
|---|---|---|
| `gateABoundNonce/Generation/gateABound` | `activity.cpp:137-139` | `connect_` never touches it; cleared only at `:173` (GENERATION_CLOSE) and `:211` |
| `gateAMappedState` | `activity.cpp:143` | no clear site at all (Q4/F1) — and `:549` just unmapped its target |
| `gateAReady[]`, `gateAPending[]`, `gateAPendingControl[]` | `renderer.cpp:218-220` | `removeAllBuffers` touches only the legacy lists |
| EGL `ctx`, `gpuCopyFbo`, 3 programs | `lorie.h:1792, 1828-1832` | never destroyed (Q4/F2) |
| `stateCond`, `stateCondFd` | `lorie.h:1820-1821` | created once (`renderer.cpp:1244-1248`), only the fd is re-sent |
| R8 obs latches | `renderer.cpp:144-147` | never cleared (Q4/F3) |

**REBUILT/RESET:** `conn_fd` + looper registration, `Renderer::state` (old mapping
munmap'd at `renderer.cpp:2427`), the three legacy buffer lists.

### FINDING Q1-F1 — a warm new X meets an Activity that still claims the OLD tuple
`connect_` does **not** clear `gateABound`, and does **not** drain the Gate A tables.
So when the new X sends its state:
```
activity.cpp:504       gateABindFromState(state)
activity.cpp:204-207   gateABound is STILL 1 and the tuple DIFFERS
                       -> lorieGateAImportBusy()  (renderer.cpp:282-294, counts gateAReady[])
                       -> lorieGateAFatalHalt("r-rebind-busy", FAIL_GENERATION)
```
**A warm new X onto an Activity still holding Gate A imports is FATAL by design.**
Q5 proved the mechanism; Q1 identifies that the warm-restart path is precisely where
it fires. This is containment working, not a defect — but it means **"warm new X" is
not a recoverable mode while imports are live**, and R9 must not assume it is.

If the tables happen to be empty (all imports drained by the GL thread, or the
previous generation closed cleanly at `renderer.cpp:813` which also unbinds), the
rebind succeeds silently and the Activity continues with its old EGL context and GL
objects — retention by construction, per Q4.

### FINDING Q1-F2 — the warm path is what makes Q4/F1 REACHABLE (closes Q4/N1)
Q4 recorded the dangling `gateAMappedState` but left reachability NOT PROVEN because
it required "a new fd registered that HUPs before `EVENT_SHARED_SERVER_STATE`". The
warm-reconnect flow produces exactly that ordering:
```
1  connect_ :549  setSharedState(NULL) -> GL thread munmaps P1 (renderer.cpp:2404, :2427)
                  gateABound STILL 1; gateAMappedState STILL P1 (now unmapped)
2  connect_ :556-560  new fd installed and added to the looper
3  the new X dies/HUPs BEFORE sending EVENT_SHARED_SERVER_STATE
                  (the only writer of gateAMappedState, activity.cpp:503)
4  HUP handler :418-419  bound && gateAMappedState != NULL  -> TRUE
                  -> lorieGateAObserveFatal(&gateAMappedState->gateA)  -> reads unmapped memory
```
Step 3 is not exotic: `MainActivity.java:604-606` retries every 250 ms, so a flapping
or slow-starting X produces a registered-but-not-yet-stateful connection routinely.
```
Q4/N1  WAS: "NOT PROVEN either way"
       NOW: REACHABLE via the warm-reconnect flow. Still NOT PROVEN that it has
            OCCURRED, but it is no longer a hypothetical ordering.
```

## Q2 — COLD ACTIVITY RESTART

### Everything Activity-side is genuinely rebuilt, because it is a new process
All Gate A state on that side is file-scope static (`activity.cpp:137-143`,
`renderer.cpp:218-222`) or a member of the file-scope `g_renderer`
(`activity.cpp:128`), so a fresh process zero-initialises all of it. The source
confirms the init actually runs rather than being skipped:
```
renderer.cpp:1229-1232   void Renderer::init(JNIEnv* env) { if (ctx) return; ... }
activity.cpp:391         g_renderer.init(env)
activity.cpp:396         connect_(NULL, NULL, -1)
```
`ctx` is `EGL_NO_CONTEXT` in a fresh process, so `init` proceeds: new JavaVM handle,
new `lorieViewClass` global ref, new `stateLock`, a **new** `stateCondFd` region
(`renderer.cpp:1244-1248`), and the GL thread is started.

Rebuilt: EGL context and every GL object, all three Gate A tables, the bound-tuple
latch, `gateAMappedState` (back to NULL), the R8 obs latches, the legacy buffer
lists, the wakeup cond.

### FINDING Q2-F1 — what is NOT rebuilt is everything on the X side
A cold Activity restart says nothing about X. If X survived, it still holds:
```
cmdentrypoint.cpp:66    gateAXRegistry[16]        entries for the OLD generation
InitOutput.c:120,:1882  pvfb->gpuCopySerialCounter monotonic, never reset (Q6)
InitOutput.c:499-525    the shared region + its sessionNonce   (Q3: never re-rolled)
cmdentrypoint.cpp:53    registeredBuffers          process-wide list (Q9)
gateADeferredHead/Tail  deferred records           purged only on clean close (Q6)
```
The reconciliation happens on the next `lorieActivityConnected()`:
```
InitOutput.c:575-579   if (generation != 0): PublishFatal(FAIL_GENERATION);
                          lorieGateARegistryCloseGeneration(nonce, oldGeneration)
cmdentrypoint.cpp:389-393  any old entry with pendingCount != 0 or
                           lastSubmittedSerial != 0 -> lorieGateAFatalHalt("x-bump-unterminal")
InitOutput.c:584-586   otherwise ProtocolInit(nonce, generation + 1)
```
So a cold Activity restart is safe **iff** the old generation's registry was terminal.
If it was not, X fail-stops with `x-bump-unterminal`. Again containment, not recovery.

### FINDING Q2-F2 — asymmetry worth stating plainly
```
Activity cold restart  -> a genuinely fresh Activity-side world (new process)
X is untouched         -> old nonce, old registry, old serial counter, old socket
                          state. The SAME nonce is reused for generation N+1
                          (Q3: the nonce is per X PROCESS, not per generation).
```
Consequently **(nonce, generation) is not sufficient to distinguish "same X, new
Activity" from "same X, same Activity, new generation"** — both advance only the
generation half. Any R9 packet that needs to tell those apart must additionally carry
the Activity's process identity, i.e. `(PID, starttime)` per Q7/Q8.

That is a concrete new requirement on the R9 evidence schema, and it dovetails with
D-02: `epoch_id` must be distinct from `epoch_generation`, because the generation
alone cannot express an Activity boundary.

## WHAT IS PROVEN
```
P1  Warm reconnect is a designed mode, with a 250 ms UI retry loop and an explicit
    "created once, only the fd is re-sent" renderer contract.
                          MainActivity.java:604-612; renderer.cpp:1240-1241
P2  connect_ resets the socket, the shared-state mapping and the legacy buffer lists
    ONLY. It does not clear gateABound and does not drain the Gate A tables.
                          activity.cpp:544-550; renderer.cpp:1526-1540
P3  Therefore a warm new X onto an Activity with live imports is r-rebind-busy FATAL.
                          activity.cpp:204-207 via renderer.cpp:282-294
P4  The warm path realises the exact ordering Q4/F1 needed. Q4/N1 is now REACHABLE.
                          activity.cpp:549, :556-560, :503, :418-419
P5  Renderer::init is once-per-process (`if (ctx) return`), so a cold restart really
    does rebuild the EGL context and every GL object.        renderer.cpp:1229-1232
P6  A cold Activity restart rebuilds nothing on the X side; reconciliation is the
    generation bump, which fail-stops on non-terminal old work.
                          InitOutput.c:575-586; cmdentrypoint.cpp:389-393
P7  (nonce, generation) cannot distinguish an Activity boundary from a generation
    boundary — the nonce is per X process (Q3) and only the generation advances.
```

## WHAT IS NOT PROVEN
```
N1  That the Q1-F2 dangling read has ever OCCURRED. Reachability is now established
    (P4); occurrence is a runtime question.
N2  Android's actual Activity/process restart policy — whether a cold restart is a
    new process in every case the UI treats as a restart. Outside this tree.
    (If Android reused the process, P5's `if (ctx) return` would SKIP init and the
    run would silently be a warm restart wearing cold clothes. R9 must assert
    Activity (PID, starttime), not trust the UI's notion of "restart".)
N3  Whether the GL thread reliably drains gateAPending[]/gateAPendingControl[] before
    a warm rebind, which decides whether Q1-F1 fatals or passes silently. Q9/N-series
    already flagged the drain-vs-rebind ordering as unproven.
```

## R9 TEST IMPLICATION
```
1  "Warm new X" is NOT a recovery mode while imports are live — it is a HALT mode
   (Q1-F1). An R9 WARM packet must expect r-rebind-busy, or must first prove the
   tables are empty. Do not write it as a success path by default.
2  R9 evidence MUST carry Activity (PID, starttime) per Q7/Q8 at every boundary.
   (nonce, generation) alone cannot express an Activity boundary (P7) — and N2 means
   the UI's word for "restart" is not trustworthy either.
3  D-02's epoch_id must be independent of epoch_generation, for the same reason.
4  Q1-F2 gives a cheap assertion for any WARM packet: record whether
   EVENT_SHARED_SERVER_STATE arrived before any HUP on the new fd.
```

## CROSS-CHECK
```
CONTRADICTION_FOUND: none.
```
```
Q4  Inventory reused, not re-derived. Q4/N1 UPGRADED from "NOT PROVEN either way" to
    REACHABLE (P4). No Q4 claim withdrawn.
Q5  Confirmed: the rebind-busy fatal is the warm path's terminal (Q1-F1).
Q3  Reused: the nonce being per X process is what makes P7 true.
Q6  Reused: the serial counter and deferred queue are X-side survivors (Q2-F1).
Q9  Reused: registeredBuffers is an X-side survivor; its drain-vs-rebind ordering
    remains unproven (N3).
Q11 Reused as the framing: bound fatal => both die, so Q1 is the narrow arm.
```

## FINAL VERDICT
```
Q1  WARM_RESTART_IS_A_HALT_MODE_WHILE_IMPORTS_LIVE   activity.cpp:204-207
    ACTIVITY_RETAINS_EGL_AND_GATEA_TABLES            renderer.cpp:218-220, 1620-1660
    WARM_PATH_MAKES_Q4F1_REACHABLE                   activity.cpp:549, :418-419
Q2  COLD_RESTART_REBUILDS_THE_ACTIVITY_WORLD_FULLY   renderer.cpp:1229-1232
    X_SIDE_IS_UNTOUCHED_AND_RECONCILES_BY_BUMP       InitOutput.c:575-586
    TUPLE_CANNOT_EXPRESS_AN_ACTIVITY_BOUNDARY        -> R9 schema requirement
```
`DESIGN_REQUIRED` is **not** raised. Both paths terminate in a designed halt or a
designed bump; the new obligations are on R9's evidence schema, not on the product.

## R9 DESIGN FREEZE — COMPLETE
```
Q1 Q2 Q3 Q4 Q5 Q6 Q7 Q8 Q9 Q10 Q11 — all resolved.
One DESIGN_REQUIRED raised (Q10 -> D-01, now ACCEPTED) and one design decision
recorded (D-02, DESIGN_ACCEPTED / IMPLEMENTATION_NOT_STARTED).
§8.1's bar — "R9 must not be run off PR #7's design; these answers replace it" — is
now met on the DESIGN axis. Implementation of D-02 remains a prerequisite for any
multi-epoch R9 runtime.
```
