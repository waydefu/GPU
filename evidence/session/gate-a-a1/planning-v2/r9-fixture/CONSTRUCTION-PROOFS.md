# V2-R9-FIXTURE — CONSTRUCTION PROOFS (packet 2 of 17, stage 1)

DATE 2026-09-22  MODE host-only source proof. No device, no attempts, no build.
GOAL `V2-R9-DESIGN` marked four of eight cells `constructibility: NOT_PROVEN`.
     This stage resolves them BEFORE any attempt is spent — the method that found
     four of R8's nine defects at zero cost.

## RESULT SUMMARY

```
cell                  was          now                        blocker
R9-F1-STALE-REPLAY    NOT_PROVEN   CONSTRUCTIBLE (PROVEN)     none
R9-COLD-2             NOT_PROVEN   CONSTRUCTIBLE (PROVEN)     none
R9-F2-RECOVERY        PLAUSIBLE    CONSTRUCTIBLE (inherits F1) none
R9-COLD-1             PLAUSIBLE    NOT CONSTRUCTIBLE YET      needs a published
                                                              renderer fatal that
                                                              leaves the registry
                                                              TERMINAL (source, 0 cost)
R9-COLD-3             PLAUSIBLE    blocked on COLD-1          same
R9-WARM-1             PLAUSIBLE    **NOT CONSTRUCTIBLE**      needs a DECISION
R9-WARM-2             NOT_PROVEN   **NOT CONSTRUCTIBLE**      needs a DECISION
R9-WARM-3             NOT_PROVEN   **NOT CONSTRUCTIBLE**      needs a DECISION
```

**The headline is not F1. It is that the entire WARM family is unconstructible on a
single X, and WARM-1/2/3 are packets #8-10 — the FIRST device packets in §8.7's
sequence. The R9 device order needs re-planning before any attempt is spent.**

---

## 1. R9-F1-STALE-REPLAY — CONSTRUCTIBLE, and the product already ships the mechanism

V-11 froze the direction as `enum16 / side2 -> x-wrong-generation / reason6`. All four
components are verified present:

```
enum16   lorie.h:1531           LORIE_GATEA_TEST_STALE_READY_REPLAY = 16
side2    renderer.cpp:674-679   consumed with LORIE_GATEA_ROLE_RENDERER inside
                                gateAValidateImport (renderer.cpp:512)
                                  if (lorieGateATestFaultConsume(st, ...STALE_READY_REPLAY,
                                                                 ROLE_RENDERER, 0, generation)) {
                                      uint64_t oldGen   = generation > 0 ? generation - 1 : 0;
                                      uint64_t oldNonce = nonce > 0 ? nonce - 1 : 0;
                                      (void)gateASendReady(id, oldNonce, oldGen, fingerprint);
                                  }
                                => a SECOND READY frame with a deliberately stale tuple,
                                   sent immediately after the legitimate one
fatal    cmdentrypoint.cpp:640-642  the stale frame fails gateAFrameTupleMatch ->
                                gateAFatalFromInput(LORIE_GATEA_FAIL_GENERATION,
                                                    "x-wrong-generation")
reason6  lorie.h                LORIE_GATEA_FAIL_GENERATION = 6
```

**No new fixture mechanism is required.** Arming is environment-only:
`TERMUX_X11_GATEA_TEST_FAULT=16` + `TERMUX_X11_GATEA_TEST_ARM=1`. Because 16 is not a
present-bound cell, `armed` starts at 1 (`InitOutput.c:2592`).

Requirements on the cell:
```
- it must REGISTER a buffer, so gateAValidateImport is reached at all. R8-C4 is the
  registering cell; an R9 cell needs the same shape.
- Gate A must be ACTIVE when the stale frame arrives, because handleGateARecord has a
  SILENT DROP before the tuple check (cmdentrypoint.cpp:629-631, Q6). Right after a
  legitimate READY the generation is live and unfatal, so this should hold - but it is
  a RUNTIME condition to assert, not an assumption. If it does not hold, the cell is
  INVALID_CONSTRUCTION (silently dropped), not VALID_FAIL.
```

This also **revises Q5's framing in F1's favour.** Q5 proved a stale READY cannot be
*consumed* by a new generation. It did not claim a stale frame cannot be *delivered* —
and enum16 delivers one on purpose, precisely so the X-side frame check can be observed
firing. F1's job was always to prove the halt; the product was built to let it.

---

## 2. THE COLD TRILEMMA — and its single solution

COLD requires, at the instant the Activity process dies:
```
(i)  lorieGateAActive() == false   else X fatals with "x-eof" and does NOT survive
                                   (cmdentrypoint.cpp:1348-1352)
(ii) sessionNonce != 0             else lorieActivityConnected() can never re-enter
                                   (InitOutput.c:567) and NO new generation can open
```
`lorieGateAActive()` (`InitOutput.c:613-627`) is false when `nonce == 0` OR
`generation == 0` OR the atomics are not lock-free OR `generationFatal != 0`.
Intersecting with (ii) leaves exactly two states:

```
A  generation == 0, nonce != 0     the window between X startup and the FIRST share.
                                   No generation exists to transition FROM, so this is
                                   not a generation boundary. Useless for COLD.
B  generationFatal != 0, nonce != 0  a POISONED but NOT CLOSED generation.  <-- the route
```

**Why a clean close cannot be used:** `gateACloseGeneration()` zeroes BOTH
`generation` and `sessionNonce` (`InitOutput.c:3334-3335`), so it violates (ii). This
is the same mechanism Q10 found for DE_RESET: after a clean close, Gate A is
permanently dead in that X process.

**State B needs a renderer-side fatal that PUBLISHES.** `gateARendererFatal`
publishes (`renderer.cpp:415`) and then halts, so the renderer dies, X sees EOF with
`fatal != 0`, takes the else-branch, `closeLorieConnection` +
`lorieGateACancelDeferred(0,0)`, and **survives** (`cmdentrypoint.cpp:1353-1356`).

**Only ONE of the three candidate faults publishes.** Checked individually:
```
fault  8  RENDERER_FATAL_PRE_FENCE     renderer.cpp:1796-1801
          -> gateARendererFatal(...)   PUBLISHES fatal   => X SURVIVES   USABLE
fault 10  RENDERER_EXIT_AFTER_CONSUME  renderer.cpp:1803-1808
          -> lorieGateADumpSummary + _exit(127)          NO publish
          => generationFatal stays 0 => lorieGateAActive() is still TRUE
          => X fatals on EOF with "x-eof" => X DOES NOT SURVIVE   UNUSABLE
fault 13  PRESENT_RENDERER_EXIT        renderer.cpp:1992-1997
          -> lorieGateADumpSummary + _exit(127)          same          UNUSABLE
```

Then the next `lorieActivityConnected()` poisons and closes the old generation, and
`lorieGateAProtocolInit` **clears generationFatal** (`lorie.h:505`) so generation N+1
is usable. Q3 recorded that clearing as a trap for evidence reading; here it is the
thing that makes COLD work at all.

**And fault 8 solves COLD-2, NOT COLD-1.** X-side `pendingCount` is set to 1 for both
endpoints at the lease (`cmdentrypoint.cpp:226-227`) and cleared at the ack
(`:270-271`). Fault 8 fires after `CONSUME_DIRECT` is traced but BEFORE the fence, i.e.
strictly between those two points, so `pendingCount` stays 1 — which is exactly what
`x-bump-unterminal` (`cmdentrypoint.cpp:389-393`) detects at the next bump.

```
R9-COLD-2  CONSTRUCTIBLE (PROVEN). Route: arm fault 8 -> renderer publishes fatal and
           dies mid-lease -> X survives with pendingCount == 1 -> relaunch the Activity
           -> the bump hits x-bump-unterminal. This is the EXPECTED fatal for this cell.
R9-COLD-1  STILL NOT CONSTRUCTIBLE — a NEW gap, opened by the above.
           It needs a PUBLISHED renderer fatal that leaves the registry TERMINAL, so
           that the bump SUCCEEDS instead of hitting x-bump-unterminal. Fault 8 is
           mid-lease by construction, and faults 10 and 13 do not publish at all.
           Candidate routes not yet checked: the non-fault gateARendererFatal call
           sites that fire OUTSIDE a lease - e.g. r-ready-send (renderer.cpp:671),
           r-control-tuple (:768), r-unregister-missing (:781). Each publishes, and
           each fires at a point where no pair is leased. Whether any is drivable from
           a fixture has NOT been determined. Source question, zero cost.
R9-COLD-3  Inherits COLD-1's gap: it is COLD-1 plus a stricter evidence schema, so it
           cannot be constructed until COLD-1 can.
```

**This correction came from the offline method paying off a second time in one packet.**
The first draft of this document said "arm fault 8, 10 or 13" and rated COLD-1
constructible. Checking the three faults individually showed that two do not publish
and therefore kill X, and that the one that does works only for the NON-terminal case.
Spending an attempt on COLD-1 with fault 10 or 13 would have produced an X that died
with `x-eof` - an INVALID_CONSTRUCTION, not a result.

---

## 3. THE WARM FAMILY — NOT CONSTRUCTIBLE ON A SINGLE X

WARM requires the Activity to SURVIVE while a new generation opens, i.e. `connect_` must
be called with a new fd. Every route was traced:

```
tryConnect() call sites (MainActivity.java)
  :276   onCreate                     Activity is launchMode="singleInstance"
                                      (AndroidManifest.xml:22), so `am start` on a
                                      running instance does NOT re-run onCreate.
  :588   onReceiveConnection          requires intent.getBundleExtra(null) to carry a
                                      BINDER (MainActivity.java:566-569). Only
                                      CmdEntryPoint can produce it
                                      (CmdEntryPoint.java:59-62). A Binder CANNOT be
                                      marshalled through `am broadcast` from a shell.
  :1132  UI callback                  gated on `!connected`
                                      (MainActivity.java:1131), and connected() is
                                      literally `conn_fd != -1` (activity.cpp:676).
                                      While X1 is alive it is TRUE, so this never fires.
tryConnect() itself :598-604          if (service == null) -> requestConnection() +
                                      250 ms retry. requestConnection (activity.cpp:358)
                                      pokes a TCP port to make X re-broadcast; it is
                                      only reached when service is ALREADY null.
```

```
=> While X1 is alive and `service != null`, NO path calls tryConnect() again.
   Therefore no path calls connect_() with a new fd.
   Therefore the WARM boundary cannot be created on a single X.
```

This kills all three WARM cells, not just WARM-2 — including WARM-1, which
`V2-R9-DESIGN` had rated PLAUSIBLE. That rating was wrong: it assumed the Activity
takes the HUP_UNBOUND arm after a clean close and can then accept a new X. It can
survive, but nothing will hand it a new fd.

### The three options, all of which are DECISIONS

```
(a) A SECOND experimental X process, on a second display.
    X2's CmdEntryPoint broadcasts ACTION_START with its own live binder -> the
    Activity's receiver fires -> service is overwritten with X2's binder ->
    tryConnect() -> service.getXConnection() on X2 -> new socketpair -> connect_(newFd).
    The Activity's gateABound still holds X1's tuple and the Gate A tables still hold
    X1's imports, and X2's nonce differs (new process, new getrandom), so
    gateABindFromState hits r-rebind-busy - which IS WARM-2.
    COST: requires a display other than :3. The standing redline reads
    "Experimental is com.waydefu.x11gpu :3 only". Extending it is ASTRA's call.

(b) A test-support trigger for re-connect.
    e.g. a new opcode, or exposing tryConnect() to the runner. Product change ->
    another artifact -> another PRODUCT_SHA. The precedent exists (D-02), but the
    cost is a full build/install/smoke cycle.

(c) DROP the WARM family from R9's runtime set.
    Record the containment as SOURCE-PROVEN but RUNTIME-UNCONSTRUCTIBLE. This is not
    a cop-out: Q1-F1 and Q5 already establish the r-rebind-busy containment from
    source with four independent filters, and Q4 already enumerates what the Activity
    retains. What runtime would add is confirmation, not discovery - and it costs
    either a redline extension or a product cycle.
```

**Recommendation: (c) for WARM-2 and WARM-3, and (a) or (b) for WARM-1 only if a
retained-state measurement is genuinely wanted.** WARM-1 is the only one of the three
that would measure something not already source-proven: that the EGL context and GL
objects are actually reused across a new X, rather than merely not destroyed. Q4/F2
proves they are never destroyed; it does not prove generation 2 uses them.

---

## 4. CONSEQUENCE FOR §8.7's PACKET ORDER

§8.7 runs `WARM-1/2/3 (#8-10) -> COLD-1/2/3 (#11-13) -> ... -> F1 (#15) -> F2 (#16)`,
with COLD gated on "10 PASS". If WARM is dropped or deferred, that gate is unsatisfiable
as written.

```
PROPOSED REVISED ORDER
  #8   R9-COLD-2     constructible NOW (fault 8; expected fatal x-bump-unterminal)
  #9   R9-F1         constructible NOW (fault 16; expected fatal x-wrong-generation/6)
  #10  R9-F2         after F1's expected fatal exists
  #11  R9-COLD-1     after a published-fatal-with-terminal-registry route is found
  #12  R9-COLD-3     after COLD-1
  --   WARM-1/2/3    disposition per the decision above; NOT a blocker for the rest

Note the inversion: the two cells that are ready FIRST are both EXPECTED-FATAL cells.
The clean-path cells (COLD-1, COLD-3) are the ones still blocked. That is the opposite
of the intuitive order and the opposite of §8.7's.
```
The COLD family no longer depends on WARM, because the trilemma solution (renderer-side
fatal) is independent of anything WARM would have established.

---

## WHAT THIS PACKET DOES NOT CLAIM

```
- That any cell will PASS. Construction and outcome are different questions.
- That COLD-2's construction works. One named gap remains (which fault leaves
  pendingCount != 0), answerable from source at zero cost.
- That the F1 silent-drop condition holds at runtime. It is asserted, not assumed.
- Any judgement on the WARM disposition. Three options are laid out; the choice is
  ASTRA's, and (a) requires extending a standing redline.
```

## NEXT, in cost order

```
1  find a published renderer fatal that leaves the registry TERMINAL (COLD-1's gap)
                                             source, zero cost
2  ASTRA decides the WARM disposition        no cost
3  V2-R9-JUDGE + V2-R9-HOST-VERIFY           host, zero attempts
4  only then any device packet, starting with COLD-2 and F1
```
