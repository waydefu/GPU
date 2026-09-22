# COLD-2 ROUTE SEARCH — RESULT: NO DRIVABLE ROUTE

DATE 2026-09-22  MODE host-only read-only source trace. No device, no build, no
source mutation. Product tree `src/f8-ahb-gatea-r7-p1-arm`, artifact `dc94485`.

STATUS **CONTRADICTION_FOUND** against `V2-R9-FIXTURE` / `r9-lifecycle-cell-spec.json`
R9-COLD-2, and against `COLD1-ROUTE-SEARCH.md`'s condition 3.

TARGET the R9-COLD-2 construction as frozen:

```
1  arm fault 8 (renderer-fatal-pre-fence)
2  drive one direct exact composite so the pair is LEASED (pendingCount = 1)
3  fault 8 fires after CONSUME_DIRECT, before the fence: the renderer publishes
   generationFatal and exits
4  X observes EOF with fatal != 0, so lorieGateAActive() is FALSE and X takes the
   closeLorieConnection else-branch instead of x-eof: X SURVIVES
5  relaunch the Activity
6  the next lorieActivityConnected() meets a registry entry with pendingCount != 0
   and halts with x-bump-unterminal
```

Steps 1-3 are drivable. **Step 4 is false.** Steps 5-6 are therefore unreachable.

---

## A. WHY STEP 4 IS FALSE — X DIES BEFORE IT EVER SEES THE EOF

The renderer's fault-8 publish happens at `renderer.cpp:1795-1801`, inside
`Renderer::applyPendingGpuCopiesLocked`, immediately after `CONSUME_DIRECT` is
traced for `entry.serial`:

```c
renderer.cpp:1795    if (lorieGateATestFaultConsume(state,
renderer.cpp:1796            LORIE_GATEA_TEST_RENDERER_FATAL_PRE_FENCE,
renderer.cpp:1797            LORIE_GATEA_ROLE_RENDERER, entry.serial,
renderer.cpp:1798            directMeta.generation))
renderer.cpp:1799        gateARendererFatal(state, "r-test-fatal-pre-fence",
renderer.cpp:1800                           LORIE_GATEA_FAIL_GENERATION, entry.serial,
renderer.cpp:1801                           entry.srcBufferId, entry.dstBufferId);
```

At that instant X is not in its event loop. It is inside the synchronous Done
path of the very composite that produced `entry.serial`:

```c
InitOutput.c:3532    if (exaGpuComp.scheduled == 0) { ... return; }
InitOutput.c:3539    r = gateAWaitTerminal(exaGpuComp.lastSerial);
```

`gateAWaitTerminal` re-reads the published fatal at the top of every 200 us
iteration and derives the result before it classifies any wake:

```c
InitOutput.c:3177        uint32_t fatal = lorieGateAObserveFatal(&st->gateA);
InitOutput.c:3180        LorieGateAResult r = lorieGateADeriveResult(done, failed, fatal, serial);
InitOutput.c:3183        if (r != LORIE_GATEA_RESULT_NONE)
InitOutput.c:3184            return r;
```

```c
lorie.h:295  static inline ... lorieGateADeriveResult(...) {
lorie.h:296      if (fatal != 0)
lorie.h:297          return LORIE_GATEA_RESULT_FATAL;
```

`fatal != 0` short-circuits **before** `completed` is even compared, so the return
is FATAL whatever the serial state is. Back in the Done path:

```c
InitOutput.c:3540    cls = lorieGateAClassifyDirectDone(
InitOutput.c:3541            r,
InitOutput.c:3542            lorieGateAObserveFatal(&pvfb->state->gateA), ...);
InitOutput.c:3545    if (cls != LORIE_GATEA_DONE_SUCCESS)
InitOutput.c:3546        gateAXFatal("x-direct-not-success", reason, exaGpuComp.lastSerial);
```

`lorie_gatea_done_class.h` maps (RESULT_FATAL, publishedFatal != 0) to
`LORIE_GATEA_DONE_PRESERVE_FATAL`, never to SUCCESS. And `gateAXFatal` with a
fatal already published does not return:

```c
InitOutput.c:3212        uint32_t published = lorieGateAObserveFatal(&st->gateA);
InitOutput.c:3213        if (published != 0) {
InitOutput.c:3216            lorieGateADumpSummary(st, "x-observe-fatal");
InitOutput.c:3217            _exit(127);
InitOutput.c:3218        }
```

**The X process exits with 127 in the same composite that armed the lease.**
There is no window in which X is alive, holds a non-terminal registry entry, and
can accept a second Activity. `x_survived_renderer_death` is unsatisfiable for
fault 8, and the race is not a race: the check is the first statement of the wait
loop.

## B. THE SAME ARGUMENT KILLS EVERY OTHER PUBLISHED RENDERER FATAL

`COLD1-ROUTE-SEARCH.md` already enumerated all 14 renderer-side fault sites and
proved: *every published renderer fatal is strictly between the lease
(`cmdentrypoint.cpp:226-227`) and the ack (`:270-271`)*. COLD-1 read that as bad
news (its condition 5 wanted a TERMINAL registry). For COLD-2 it is the same bad
news for the opposite reason: **being inside the lease is exactly being inside
`gateAWaitTerminal`**, and §A shows that is fatal to X.

COLD-1's condition 3 was written as "X does NOT take the x-eof fatal". That is
true and irrelevant — X does not take `x-eof`; it takes `x-direct-not-success`
and `_exit(127)`s just the same. **CONTRADICTION_FOUND, see §F.**

## C. NO OTHER PUBLISHER CAN LEAVE X ALIVE

`lorieGateAActive()` is the gate on every X-side death branch:

```c
InitOutput.c:620    nonce = lorieGateALoadU64Acquire(&p->sessionNonce);
InitOutput.c:621    generation = lorieGateALoadU64Acquire(&p->generation);
InitOutput.c:622    if (nonce == 0 || generation == 0)
InitOutput.c:623        return 0;
InitOutput.c:624    return lorieGateAObserveFatal(p) == 0;
```

so X survives losing its Activity only if `nonce == 0`, or `generation == 0`, or
`fatal != 0`. All three are dead ends:

**(a) nonce == 0 or generation == 0.** The only writer of zero is the clean close,
and it zeroes *both*:

```c
InitOutput.c:3334    lorieGateAStoreU64Release(&shared->generation, 0);
InitOutput.c:3335    lorieGateAStoreU64Release(&shared->sessionNonce, 0);
```

and `lorieActivityConnected`'s entire Gate A block is gated on a non-zero nonce:

```c
InitOutput.c:567    if (lorieGateAProtoEnabled() && pvfb->state->gateA.sessionNonce != 0) {
```

so after a clean close no bump can ever run again. (This is `mem:` "DE_RESET kills
Gate A" and Q10, from the other direction.)

**(b) fatal != 0 published by X.** Every X-side publisher is `gateAXFatal`
(`InitOutput.c:3205-3227`), which ends in `lorieGateAPublishFatal` followed by
`lorieGateAFatalHalt`, and

```c
lorie.h:1414  __attribute__((noreturn)) static inline ... lorieGateAFatalHalt(...) {
lorie.h:1415      __android_log_print(ANDROID_LOG_FATAL, "gatea-a1", "GATEA_FATAL_HALT ...");
lorie.h:1416      _exit(127);
```

The one X-side `lorieGateAPublishFatal` that is *not* followed by a halt is inside
`lorieActivityConnected` itself (`InitOutput.c:576`) — i.e. it is the bump, not a
way to reach the bump.

**(c) fatal != 0 published by the renderer.** §A and §B.

## D. EVERY PATH THAT OBSERVES THE ACTIVITY'S DEATH TERMINATES X

Three independent observers, all fatal while Gate A is active:

```
cmdentrypoint.cpp:1347-1355   decoder PEER_CLOSED
                              lorieGateAActive() -> gateAFatalFromInput("x-eof")
InitOutput.c:1961-1969        lorieGpuCopyWait
                              !connectionAlive, fatal==0 -> X_HUP      -> gateAXFatal("x-hup")
                              !connectionAlive, fatal!=0 -> PRESERVE   -> gateAXFatal("x-hup")
InitOutput.c:3188-3197        gateAWaitTerminal, identical two classes -> gateAXFatal("x-hup")
```

`lorie_gatea_wait_wake_class.h:37-47` is the shared classifier: `!connectionAlive`
returns PRESERVE_FATAL when a fatal is published and X_HUP when none is. Note the
asymmetry at `InitOutput.c:1963-1966` — X_HUP is survivable only when
`lorieGateAActive()` is false, but PRESERVE_FATAL at `:1968-1969` is
**unconditionally** fatal. A published fatal therefore does not buy survival in the
draw path; it changes the halt's identity, not its existence.

## E. CONSEQUENCE — `x-bump-unterminal` IS UNREACHABLE, AND SO IS `x-share-in-lease`

Collecting §C and §D:

> **No X server process can observe a second `lorieActivityConnected()` with
> `generation != 0`.**

The first connect takes the `generation == 0` branch and sets generation 1
(`InitOutput.c:575, 584-586`). A second connect requires X to outlive its Activity,
which §C and §D exclude. Therefore `lorieGateARegistryCloseGeneration`
(`cmdentrypoint.cpp:380`) has no runtime caller, and both of its guarded halts are
defensive-only in the current product:

```
cmdentrypoint.cpp:389-393   x-bump-unterminal (halt at :391)   (R9-COLD-2's expected fatal)
InitOutput.c:569-570        x-share-in-lease
```

Runtime corroboration, not proof: across every Gate A run recorded under
`evidence/` — 201 989 `GATEA_EVENT` lines and 141 non-zero `GATEA_SUMMARY`
generations — **`generation` has never once been observed above 1.**

A second, independent corroboration is the one consumed attempt: in
`runtime-dc94485/r9-cold-2/attempt-02` no composite ever ran (the fixture aborted on
the missing test extension), yet `am force-stop` alone killed X —
`GATEA_FATAL_HALT what=x-hup reason=6` on the X pid, with `generation=1` and
`generationFatal=6` in the accompanying summary. That is branch §D/`InitOutput.c:1965`
firing on a bare Activity teardown, with no Gate A work in flight at all.

## F. CONTRADICTION_FOUND

```
OLD CLAIM     COLD1-ROUTE-SEARCH.md, "THE TARGET" preamble:
              "Conditions 1-4 and 6 are satisfied by any published renderer fatal
               (Q11 + the COLD trilemma). Condition 5 is the one that fails,
               everywhere."
NEW EVIDENCE  InitOutput.c:3539 -> 3183-3184 -> lorie.h:296-297 ->
              lorie_gatea_done_class.h (PRESERVE_FATAL) -> InitOutput.c:3546 ->
              InitOutput.c:3212-3217 `_exit(127)`.
              Condition 3 ("X does NOT take the x-eof fatal") is satisfied only in
              letter. Condition 4 and the unstated condition "X is still running"
              are NOT satisfied by any published renderer fatal: X is inside
              gateAWaitTerminal for the same serial and exits 127.
AFFECTED      planning-v2/r9-fixture/COLD1-ROUTE-SEARCH.md   (preamble)
              planning-v2/r9-design/V2-R9-DESIGN.md          (R9-COLD-2 section)
              planning-v2/r9-design/r9-cell-spec.json        (R9-COLD-2)
              tests/r9/r9-lifecycle-cell-spec.json           (R9-COLD-2, cell_order,
                                                              removed_cells,
                                                              product_level_finding)
              tests/r9/judge-r9.py                           (COLD-2 judge)
              tests/r9/test-judge-r9.py                      (COLD-2 vectors)
REQUIRED      1. COLD1 preamble: restate condition 3 as "X is still running when the
                 next Activity connects", and record that no published renderer
                 fatal satisfies it.
              2. R9-COLD-2 moves to removed_cells as
                 SOURCE-PROVEN / RUNTIME-NOT-CONSTRUCTIBLE, exactly like WARM-1/2/3:
                 not PASS, not FAIL, not INVALID, not runtime-qualified.
              3. cell_order becomes [R9-F1, R9-F2].
              4. product_level_finding is strengthened from "requires a prior fatal"
                 to "is unreachable": the prior fatal cannot be obtained without X
                 exiting in the same breath.
```

## G. REOPEN CONDITION

R9-COLD-2 reopens if and only if the product gains **either**:

* a renderer-side fatal publisher that is reachable *outside* an X terminal wait
  (today the only pre-lease fault site is `renderer.cpp:674`, fault 16, which sends
  a stale READY and does not fatal the renderer — COLD1 §sweep); **or**
* a warm reconnect / rebind entry point that lets X outlive its Activity with
  `sessionNonce != 0` and `generation != 0` — the same entry point whose absence
  removed R9-WARM-1/2/3.

Either one restores a second `lorieActivityConnected()`, and with it both
`x-bump-unterminal` and `x-share-in-lease`.

## H. WHAT SURVIVES

R9-F1 and R9-F2 are unaffected. Neither needs X to outlive its Activity:

* **R9-F1** needs a Gate A REGISTER so `gateAValidateImport` runs, then fault 16 at
  `renderer.cpp:674-679` sends the stale READY and X halts with
  `x-wrong-generation` (`cmdentrypoint.cpp:640-641`). X halting **is** the PASS.
* **R9-F2** is a fresh X + fresh Activity doing one clean `PictOpOver` composite.

Both are drivable by an ordinary XCB client with no R8 test extension.
