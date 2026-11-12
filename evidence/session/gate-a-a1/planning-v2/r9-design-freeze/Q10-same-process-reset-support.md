# R9 DESIGN FREEZE — Q10 (same-process reset support)

## QUESTION
Plan §D-01 / line 1399: *"same-process reset support：product 是否支援"* — and it
*"決定 R9-RESET 是否存在"*. `V2-R9-RESET` is listed as **conditional** (plan:1458:
"13 PASS + Q10 支援成立").

## SOURCE AUTHORITY
```
TREE   src/f8-ahb-gatea-r7-p1-arm @ 14caa7b (branch feat/gatea-r8-lifecycle-support-20260918)
DATE   2026-09-22
MODE   host-only, read-only, no device, no adb, no build, no CI, no source mutation,
       no runtime attempt
DEPTH  Q3/Q4/Q5/Q6/Q9/Q11 standard. Every claim cites file:line.
SCOPE  This trace covers BOTH the lorie tree and the vendored xserver
       (lorie/src/main/cpp/xserver), because the reset primitive lives in dix/os.
```

## HEADLINE

**A same-process reset path already EXISTS, is the DEFAULT, and is reachable without
any new code — and it KILLS Gate A permanently while the X server keeps running.**

That is a different answer from "not supported", and it inverts the framing: R9-RESET
does not need a mechanism to be built; it needs the existing mechanism to be
recognised as a one-way kill.

## PART 1 — THERE IS NO RESET PRIMITIVE IN THE GATE A PROTOCOL

```
lorie.h  LorieGateAMsgType: REGISTER=1, READY=2, REGISTER_FAILED=3, UNREGISTER=4,
         UNREGISTER_ACK=5, GENERATION_CLOSE=6, GENERATION_CLOSED=7, FATAL_NOTIFY=8
```
Eight types, none of them a reset. `GENERATION_CLOSE`/`CLOSED` are a **terminal**, not
a restart: the close handler zeroes the tuple (`InitOutput.c:3334-3335`) and the
renderer unbinds (`renderer.cpp:813`). No message, no shared field and no helper
exists to re-arm a generation in place.

## PART 2 — BUT THE X SERVER HAS ITS OWN RESET, AND IT IS ON BY DEFAULT

This is the part the five prior traces did not reach, because it lives in the
vendored xserver rather than in `lorie/`.

### 2.1 The default is RESET, not TERMINATE
```
xserver/dix/dispatch.c:3480   char dispatchExceptionAtReset = DE_RESET;
xserver/include/opaque.h:41   #define DE_RESET 1
xserver/os/utils.c:946        "-terminate" would set dispatchExceptionAtReset = DE_TERMINATE
xserver/dix/dispatch.c:407    dispatchException |= dispatchExceptionAtReset;
```
`-terminate` is **not passed** in this deployment:
```
start-x3.py:15                exec /data/data/com.termux/files/usr/bin/f8-x11gpu :3
f8-x11gpu (launcher)          exec app_process ... com.termux.x11.Loader "$@"   ($@ = ":3")
CmdEntryPoint.java:41,48,166  main(args) -> new CmdEntryPoint(args) -> start(args), unchanged
```
So the last X client disconnecting raises **DE_RESET**, not DE_TERMINATE.

### 2.2 CloseScreen runs on BOTH exits; only ddxGiveUp is TERMINATE-only
```
xserver/dix/main.c:325    (*screenInfo.screens[i]->CloseScreen)(screenInfo.screens[i]);
                          <- UNCONDITIONAL, inside the loop tail
xserver/dix/main.c:347    if (dispatchException & DE_TERMINATE) CloseWellKnownConnections();
xserver/dix/main.c:353-356 if (dispatchException & DE_TERMINATE) { ddxGiveUp(...); break; }
```
The product states the same thing in its own words:
```
InitOutput.c:644-647   "dix/main.c calls this [ddxGiveUp] after CloseScreen, FreeFonts,
                        and ClearWorkQueue, and only on DE_TERMINATE. Reset CloseScreen
                        is not producer quiescence — dix_main then loops into
                        InitOutput / CreateRootCursor, which still emit role=x R8_OBS."
InitOutput.c:1259-1260 "Observation END is not here: last-client disconnect is DE_RESET,
                        and dix_main re-enters InitOutput after this returns."
```

### 2.3 The installed CloseScreen is the Gate A one
```
InitOutput.c:1459   pvfb->CloseScreen = pScreen->CloseScreen;     (save the wrap)
InitOutput.c:1461   pScreen->CloseScreen = lorieCloseScreen;      (install)
InitOutput.c:1228   static Bool lorieCloseScreen(ScreenPtr pScreen)
InitOutput.c:1239-1240  if (lorieGateAProtoEnabled()) gateACloseGeneration();
```

### 2.4 The loop re-enters OsInit, but the nonce allocator is guarded
```
xserver/dix/main.c:142   while (1) {
xserver/dix/main.c:143     serverGeneration++;
xserver/dix/main.c:151     OsInit();
xserver/os/osinit.c:317      OsVendorInit();
InitOutput.c:489           void OsVendorInit(void) {
InitOutput.c:494-495         if (lorieScreen.stateFd != -1)   // already initialized
                                 return;                      <- NO-OP on every reset
InitOutput.c:499             LorieBuffer_createRegion("xserver", ...)   never re-reached
InitOutput.c:510             memset(state, 0, ...)                      never re-reached
InitOutput.c:523-525         getrandom -> sessionNonce                  never re-reached
```
**The nonce block is in `OsVendorInit`, not in `InitOutput`, and it is guarded by
`stateFd != -1`.** `InitOutput` is re-entered on a reset; the allocator is not.

## PART 3 — THE PROVEN CHAIN

```
1  last X client disconnects (no -terminate)
       -> dispatchException |= DE_RESET          dix/dispatch.c:407, :3480
2  loop tail runs CloseScreen unconditionally    dix/main.c:325
       -> lorieCloseScreen                       InitOutput.c:1228 (installed :1461)
       -> gateACloseGeneration()                 InitOutput.c:1240
3  clean drain completes, then:
       generation   = 0                          InitOutput.c:3334
       sessionNonce = 0                          InitOutput.c:3335
4  DE_TERMINATE is NOT set, so the loop does NOT break
                                                 dix/main.c:353-356
5  loop re-enters OsInit -> OsVendorInit         dix/main.c:151; os/osinit.c:317
       -> returns immediately, stateFd != -1     InitOutput.c:494-495
       -> NO new region, NO memset, NO getrandom
6  X keeps running and serves new clients, but
       lorieActivityConnected() is guarded by sessionNonce != 0
                                                 InitOutput.c:567
       -> can never re-enter -> no generation can ever be allocated again (Q3 A.2)
```
**Result: after one DE_RESET, Gate A is permanently dead in a still-live X process.**

## CONTRADICTION_FOUND

```
OLD CLAIM        Q3-generation-nonce-lifecycle.md, §B.2, heading and body:
                 "### B.2 Clean close — zeroes BOTH, terminal for the process"
                 "Production callers: exactly one — lorieCloseScreen()
                  (InitOutput.c:1228, call at :1240), i.e. X server shutdown."

NEW EVIDENCE     lorieCloseScreen also runs on DE_RESET, which is NOT shutdown:
                   dix/main.c:325    CloseScreen called unconditionally
                   dix/main.c:353-356 loop breaks ONLY on DE_TERMINATE
                   dix/dispatch.c:3480 dispatchExceptionAtReset = DE_RESET by default
                   os/utils.c:946    -terminate would change that; it is not passed
                                     (start-x3.py:15; f8-x11gpu; CmdEntryPoint.java:41,166)
                   InitOutput.c:1259-1260 the product's own comment says so

WHAT IS WRONG    The caller ENUMERATION is correct. The GLOSS is wrong: clean close is
                 NOT equivalent to shutdown, and the close is NOT "terminal for the
                 process". Q3 therefore under-stated the reachability of nonce-zeroing
                 and treated it as a non-issue in production.

AFFECTED DOCUMENT  Q3-generation-nonce-lifecycle.md (§B.2 heading + body)
REQUIRED CORRECTION  Replace "i.e. X server shutdown" with the DE_RESET chain, and
                 retitle §B.2 so it does not claim process termination.
STATUS           CORRECTED IN PLACE 2026-09-22. Q3's §A.1 consequence
                 ("no code path re-rolls the nonce inside a live X process ... Gate A
                 is dead for the remaining life of that process") is UNCHANGED and is
                 now MORE load-bearing, not less — Q10 supplies the live-process path
                 that reaches it.
```

## PART 4 — CONFIRMATION AGAINST THE FIVE PRIOR TRACES

Each was recorded as a Q10 pre-answer. All five hold; the table adds what each one
means specifically for a *reset* rather than for a teardown.

| pre-answer | source | holds? | meaning for R9-RESET |
|---|---|---|---|
| Q3 — no nonce re-roll | `InitOutput.c:494-495`, `:523-525` | **YES**, and Q10 strengthens it by locating the guard | a reset needs a nonce re-roll that does not exist |
| Q5 — no READY teardown outside UNREGISTER | `renderer.cpp:444`, one caller `:783` | **YES** | a reset must destroy READY GL objects itself |
| Q4/F2 — no context turnover | `renderer.cpp:1620-1660`, `:1472` | **YES** | the surviving EGL context is the one thing that *helps*: a reset would not have to rebuild it |
| Q11 — process death is the only working reclamation | `lorie.h:1414-1418`; `buffer.c:94-106` | **YES** | a reset must replace that reclamation, not inherit it |
| Q9 — no X-side socket teardown outside error/EOF | `cmdentrypoint.cpp:1519-1523`, `:848/:1308/:1351` | **YES** | a reset must close the old socket explicitly |

## PART 5 — WHAT A GENUINE SAME-PROCESS RESET WOULD REQUIRE

Concrete and enumerated, so the Astra/Sol decision on D-01 has a scope rather than a
feeling:
```
1  re-roll the nonce            new code: the allocator is guarded off after the first
                                run (InitOutput.c:494-495). Needs either a second
                                entry point or a relaxation of that guard.
2  destroy READY GL objects     new code: gateADestroyReadyImport (renderer.cpp:444)
                                has exactly one caller, the UNREGISTER handler (:783).
3  purge the deferred queue     EXISTS: lorieGateACancelDeferred (cmdentrypoint.cpp:779),
                                but the bump path never calls it (Q6).
4  reset/assert gpuCopyQueue    new code: lorieGateAProtocolInit (lorie.h:503-511)
                                does not touch it; only the clean close asserts it
                                drained (InitOutput.c:3309-3313).
5  close the old socket         new code: getXConnection does neither close nor
                                unregister (Q9/F1).
6  clear gateAMappedState       new code: it has no clear site at all (Q4/F1).
7  re-arm the renderer obs      new code: lorieR8ObsEnd("r") is one-shot per process
                                (Q4/F3). Test-support only.
```
Items 1, 2, 4, 5, 6 are product changes; 7 is test-support; 3 is a call that already
exists but is not wired to the bump.

## WHAT IS PROVEN

```
P1  The Gate A protocol has no reset primitive: 8 message types, none of them reset.
                                                                       lorie.h enum
P2  dispatchExceptionAtReset defaults to DE_RESET.            dix/dispatch.c:3480
P3  -terminate is not passed in this deployment.
                      start-x3.py:15; f8-x11gpu; CmdEntryPoint.java:41, :48, :166
P4  CloseScreen is called unconditionally in the loop tail; only ddxGiveUp and the
    loop break are DE_TERMINATE-gated.                dix/main.c:325, :347, :353-356
P5  lorieCloseScreen is the installed CloseScreen and calls gateACloseGeneration.
                                                  InitOutput.c:1461, :1228, :1240
P6  The clean close zeroes sessionNonce.                        InitOutput.c:3335
P7  OsInit -> OsVendorInit is re-called on every server generation, and returns
    immediately because stateFd != -1.
                        dix/main.c:151; os/osinit.c:317; InitOutput.c:489, :494-495
P8  Therefore Gate A cannot be re-armed after a DE_RESET, while X keeps running.
                                                  InitOutput.c:567 (guard), Q3 A.2
P9  All five prior Q10 pre-answers hold unchanged.
```

## UPSTREAM CONFIRMATION (added 2026-09-22)

The reset semantics were cross-checked against authority outside this repo, because
the whole finding rests on them.

**1. Official X.Org `Xserver(1)` man page** — the semantics are documented, not
incidental:
```
-terminate   "causes the server to terminate at server reset, instead of continuing
              to run. This overrides a previous -noreset command line option."
-noreset     "prevents a server reset when the last client connection is closed.
              This overrides a previous -terminate command line option."
```
So by DOCUMENTED DEFAULT the server **resets and continues to run** when the last
client connection closes. `-terminate` is opt-in, and this deployment does not opt in.

**2. Upstream source, independently obtained** — Debian-packaged `xorg-server
2:21.1.24-1` (sources.debian.org), compared against the vendored tree:
```
upstream dix/dispatch.c:3480   char dispatchExceptionAtReset = DE_RESET;
vendored dix/dispatch.c:3480   char dispatchExceptionAtReset = DE_RESET;
upstream :407, :424, :425, :432 — identical line numbers and content
```
Same file, same line numbers. This area of the vendored tree is upstream verbatim.

**3. termux-x11 does not patch it.** `patches/xserver.patch` DOES modify
`dix/main.c`, `dix/dispatch.c`, `os/osinit.c` and `os/utils.c`, but contains **zero**
occurrences of `dispatchExceptionAtReset`, `DE_RESET`, `DE_TERMINATE`, `noreset` or
`terminate`. The reset machinery is untouched.

**4. The exact trigger, named:**
```
dix/dispatch.c:3569   CloseDownClient():
                        if (ShouldDisconnectRemainingClients())
                            SetDispatchExceptionTimer();
dix/dispatch.c:421-433 SetDispatchExceptionTimer():
                        if (!(dispatchExceptionAtReset & DE_TERMINATE)) {
                            dispatchException |= dispatchExceptionAtReset;   <- DE_RESET, no delay
                            return;
                        }
os/utils.c:414-419    AutoResetServer(int sig)  -> dispatchException |= DE_RESET
os/utils.c:426-431    GiveUp(int sig)           -> dispatchException |= DE_TERMINATE
```

## N1 / N2 — RESOLVED 2026-09-22, zero attempt cost

### N1 RESOLVED — R8 can never reach DE_RESET, and the reason matters
The R8 fixture does not simply exit. It issues a custom X extension request whose
server-side handler calls upstream `GiveUp(0)` directly:
```
lorie_r8_test.c:335   lorieR8Obs("x", "TEST_CONTROL", "\"op\":\"TERMINATE\"")
lorie_r8_test.c:341   /* Same DE_TERMINATE flag as os/utils.c GiveUp. */
lorie_r8_test.c:342   GiveUp(0);
os/utils.c:426-430    GiveUp(int sig) { ... dispatchException |= DE_TERMINATE; }
p_r8_lifecycle.c:212, :222  TERMINATE_SENT / TERMINATE_ACK
```
So every R8 cell forces **DE_TERMINATE**, which pre-empts the default reset. Class P
cells never get there at all — the runner records `fatal_no_clean_term` and X dies by
fatal halt.

**R8 is protected by the fixture's explicit terminate, not by anything structural.**

### N2 RESOLVED — no existing R8 evidence is contaminated
Checked across all ten passing attempts of `runtime-b984ded` (zero device cost):
```
cell                      x_pre_cleanup   x3-residue        terminate markers
r8-c1/attempt-13          DEAD            NO_X3_RESIDUE     4
r8-c2/attempt-03          DEAD            NO_X3_RESIDUE     4
r8-c3-disconnect/att-03   DEAD            NO_X3_RESIDUE     4
r8-c3-window/attempt-04   DEAD            NO_X3_RESIDUE     2
r8-c4/attempt-03          DEAD            NO_X3_RESIDUE     2
r8-c5-full/attempt-04     DEAD            NO_X3_RESIDUE     2
r8-c5-overflow/att-03     DEAD            NO_X3_RESIDUE     4
r8-d/attempt-04           DEAD            NO_X3_RESIDUE     2
r8-p1/attempt-03          DEAD            NO_X3_RESIDUE     0   (fatal cell)
r8-p2/attempt-01          DEAD            NO_X3_RESIDUE     0   (fatal cell)
```
X is DEAD in 10/10 with no residue. A DE_RESET would have left X **alive**. No R8
result is a post-reset observation, and none needs re-judging.

### The sharpened R9 warning this produces
R8's immunity is an accident of its fixture design, and it does not transfer:
```
ANY R9 packet whose fixture EXITS NORMALLY instead of issuing the terminate request
will drop the last client, fire DE_RESET, and silently kill Gate A for the remainder
of that X process — with no fatal and no log line.
```
R9 fixtures must either (a) keep issuing the explicit terminate, or (b) hold a second
X client open across the boundary, or (c) launch X with `-terminate`. Option (c) is
the only one that removes the hazard rather than avoiding it, and it changes the
frozen X launch command (`start-x3.py:15`), so it is an Astra/Sol decision.

## WHAT IS NOT PROVEN

```
N3  Whether relaxing the OsVendorInit guard (item 1 of Part 5) is safe — it also
    protects the mutexes, the cursor lock and b3a telemetry init
    (InitOutput.c:530-535+). NOT ANALYSED here; it is design work, not source reading.
```

## R9 TEST IMPLICATION

```
1  V2-R9-RESET's precondition is INVERTED from what the plan assumed. The plan asks
   whether reset is "supported"; the source says a reset EXISTS and is destructive.
   R9-RESET is therefore constructible today, but its only honest verdict is
   "Gate A is permanently dead afterwards" — it cannot demonstrate recovery.
2  D-01 becomes a scoping decision with a 7-item list (Part 5), not an open question.
3  N1 is cheap to settle and should be settled BEFORE any R9 packet: if a DE_RESET
   can occur mid-run, every long-lived-X assumption in R9 is at risk, and so is the
   interpretation of any "Gate A inactive" observation in R8.
4  N2 is a zero-attempt offline check against existing evidence. Do it first.
```

## Q3 / Q4 / Q5 / Q6 / Q9 / Q11 CROSS-CHECK

```
CONTRADICTION_FOUND: YES — against Q3 §B.2. Detailed above and CORRECTED IN PLACE.
```
```
Q3   §B.2 gloss corrected. §A.1, §A.2, §C and the ruling are UNCHANGED and are
     strengthened: Q10 supplies the live-process path that reaches the zeroing Q3
     described.
Q4   Unchanged. Q4/F1 (gateAMappedState) and Q4/F3 (obs terminal) become items 6 and
     7 of the reset requirement list.
Q5   Unchanged. Becomes item 2.
Q6   Unchanged. Its deferred-purge gap becomes item 3, and its gpuCopyQueue gap
     becomes item 4.
Q9   Unchanged. Becomes item 5.
Q11  Unchanged, and NOT contradicted: Q11's criterion (a) is defined over a NEW X
     PROCESS, which a DE_RESET is not. Q10 adds that a live X process after a reset
     is NOT a fresh session and must never be mistaken for one in F2.
```

## FINAL VERDICT

```
NO_GATEA_RESET_PRIMITIVE          8 message types, none of them a reset; no shared
                                  field or helper re-arms a generation in place.
XSERVER_RESET_EXISTS_AND_IS_DEFAULT
                                  DE_RESET is the default and -terminate is not
                                  passed.        dix/dispatch.c:3480; start-x3.py:15
RESET_PERMANENTLY_DISABLES_GATEA  CloseScreen runs on reset, zeroes the nonce, and
                                  the allocator is guarded off.
                                  dix/main.c:325; InitOutput.c:1240, :3335, :494-495
R9_RESET_CONSTRUCTIBLE_BUT_ONE_WAY
                                  R9-RESET can be built today; it can only prove the
                                  kill, never a recovery.
DESIGN_REQUIRED                   RAISED for D-01, scoped: 7 enumerated items (Part 5),
                                  5 product + 1 test-support + 1 already-existing call
                                  that is simply not wired to the bump.
```
This is the **first** `DESIGN_REQUIRED` of the freeze. It is raised deliberately: the
plan made `V2-R9-RESET` conditional on Q10, and Q10's answer is that the packet as
imagined cannot exist without the seven changes above.

## STILL OPEN
```
Q1 Q2 — the last two, and the only ones with no trace yet.
§8.1 still forbids running R9 off PR #7's design.
```
