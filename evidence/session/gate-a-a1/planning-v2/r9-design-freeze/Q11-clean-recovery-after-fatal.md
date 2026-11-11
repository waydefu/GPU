# R9 DESIGN FREEZE — Q11 (clean recovery after fatal)

## QUESTION
Plan §8.8 defines F2 as: *"只在 F1 已取得 expected fatal 後執行 fresh session recovery.
必須 new nonce / empty registry / clean direct exact SUCCESS. fresh session 有 stale
residue / 無法 direct success → VALID_FAIL."*

So Q11 is **not** in-process recovery. Every Gate A fatal is
`__attribute__((noreturn))` + `_exit(127)` (`lorie.h:1414-1418`); nothing resumes.
Q11 asks: **after a fatal session, does a fresh session provably get a new nonce, an
empty registry, and an unpoisoned path to direct success — with no residue?**

## SOURCE AUTHORITY
```
TREE   src/f8-ahb-gatea-r7-p1-arm @ 14caa7b (branch feat/gatea-r8-lifecycle-support-20260918)
DATE   2026-09-22
MODE   host-only, read-only, no device, no adb, no build, no CI, no source mutation,
       no runtime attempt
DEPTH  Q3/Q4/Q5/Q6 standard. Every claim cites file:line. Unsettled -> NOT PROVEN.
PLAN   F2 criteria quoted from V1-CORE-EXECUTOR-MASTER-PLAN-V2.3.md:1475-1490
BUILDS ON Q3 (nonce is per-process), Q4 (renderer state is per-process)
```

## FATAL TAXONOMY

```
X side      gateAXFatal            InitOutput.c:3205-3228   publishes, traces, dumps, halts
            gateAFatalFromInput    cmdentrypoint.cpp:612-625 publishes (:618), broadcasts, halts
            lorieGateAFatalHalt    direct calls, e.g. InitOutput.c:570 "x-share-in-lease"
                                                          -> does NOT publish
Renderer    gateARendererFatal     renderer.cpp:410-421     publishes (:415), traces, dumps, halts
            gateAHupPreserve       activity.cpp:145-155     logs a NON-frozen token, _exit(127)
            lorieGateAFatalHalt    direct calls, e.g. activity.cpp:206 "r-rebind-busy"
terminal    lorieGateAFatalHalt    lorie.h:1414-1418        __android_log_print + _exit(127)
```
`lorieGateAPublishFatal` is a **first-wins CAS** (`lorie.h:634-641`), and `gateAXFatal`
explicitly declines to overwrite a peer's identity (`InitOutput.c:3213-3218`: dump
summary, `_exit(127)`, no second `GATEA_FATAL_HALT`). Fatal identity is therefore
single-writer by construction.

## DOES A FATAL KILL BOTH PROCESSES?

This is the whole question, because a process that dies reclaims everything F2 cares
about, and a process that survives carries the entire Q4 inventory forward.

### X dies -> Activity reaction
The Activity's looper sees HUP and classifies on `(bound, publishedFatal)` only
(`lorie_gatea_hup_class.h:30-37`):
```
bound && published != 0  -> HUP_PRESERVE  -> gateAHupPreserve -> _exit(127)
                            activity.cpp:421-423, :145-155
bound && published == 0  -> HUP_R_HUP     -> lorieGateAFatalHalt("r-hup") -> _exit(127)
                            activity.cpp:424-426
!bound                   -> HUP_UNBOUND   -> NO halt; falls through to
                            ALooper_removeFd :429, setSharedState(NULL) :436,
                            removeAllBuffers :437, return 1 :438   <- SURVIVES
```
**Both bound arms terminate the Activity.** Whether X published or not, a bound
Activity dies.

### Renderer dies -> X reaction
```
cmdentrypoint.cpp:1344-1348   result == PEER_CLOSED/IO_ERROR/PROTOCOL_FATAL
                              && lorieGateAActive() -> gateAFatalFromInput(
                                   FAIL_GENERATION, "x-eof") -> halt
cmdentrypoint.cpp:1349-1354   else -> closeLorieConnection(fd)
                                      lorieRecordDecoderDestroy
                                      lorieGateACancelDeferred(0, 0)     <- X SURVIVES
cmdentrypoint.cpp:1307-1313   X_NOTIFY_ERROR arm: same shape, "x-hup"
```

### Is the Activity ever UNBOUND at fatal time?
Enumerable. `gateABound` is written at exactly three lines (`activity.cpp:139` init,
`:209` set, `:173` and `:211` clear):
```
activity.cpp:173   inside lorieGateAUnbindTuple, whose ONLY caller is
                   renderer.cpp:813 — the GENERATION_CLOSE handler, i.e. a CLEAN close
activity.cpp:211   gateABindFromState else-branch: version mismatch, or a zero tuple
```
**Neither is on a fatal path.** So a fatal that occurs while a generation is live
finds the Activity bound, and the Activity dies with X. `!bound` means either Gate A
never activated or the generation already closed cleanly — in both cases there is no
fatal session to recover from.

## THE THREE F2 CRITERIA, AGAINST SOURCE

### (a) NEW NONCE — PROVEN by construction
A fresh session is a new X process. Its shared region is **anonymous**:
```
InitOutput.c:499   LorieBuffer_createRegion("xserver", sizeof(*state))
buffer.c:94-106      ASharedMemory_create(name, size)            <- fd-only, name is a
                     else memfd_create(name, MFD_CLOEXEC|...)       debug label, NOT a
                     else open("/dev/ashmem") + ASHMEM_SET_NAME     lookup key
```
None of the three is reopenable by name, so no later process can attach to the dead
session's region. The new process then:
```
InitOutput.c:510   memset(lorieScreen.state, 0, sizeof(*lorieScreen.state))
InitOutput.c:523   syscall(SYS_getrandom, &gateaNonce, sizeof(gateaNonce), 0)
InitOutput.c:524-525 nonzero check, then sessionNonce = gateaNonce
```
A fresh nonce is drawn, and `generationFatal`, `fatalReason`, `firstFailedSerial`,
`firstFailureCode` and the whole `gpuCopyQueue` are zero from the `memset`.
**Criterion (a) cannot fail for a new X process.**

### (b) EMPTY REGISTRY — PROVEN for a new process pair
```
X side        gateAXRegistry[16]          cmdentrypoint.cpp:66      file-scope static
renderer side gateAPending[] / gateAReady[] / gateAPendingControl[]
                                          renderer.cpp:218-220      file-scope statics
              gateABound{Nonce,Generation}, gateABound
                                          activity.cpp:137-139      file-scope statics
              gateAMappedState            activity.cpp:143          file-scope static
```
All are zero-initialized in a fresh process. The criterion therefore reduces to
**"are both processes new?"**, which the previous section answers YES for a bound
fatal.

### (c) CLEAN DIRECT SUCCESS — follows from (a) and (b)
`lorieGateAActive()` (`InitOutput.c:613-627`) needs nonce != 0, generation != 0,
lock-free atomics, and `generationFatal == 0`. (a) supplies the first and last; the
generation is bumped to 1 by the first `lorieActivityConnected()`
(`InitOutput.c:584-586`, per Q3). Nothing from the dead session can reach the new
region. **No source-level obstacle to direct success exists.**

## FINDING Q11-F1 — the survive-arms are the only residue vector

Two arms let a process outlive a disconnect:
```
LORIE_GATEA_HUP_UNBOUND   lorie_gatea_hup_class.h:31; activity.cpp:420, :429-438
X inactive at EOF         cmdentrypoint.cpp:1349-1354
```
Neither is reachable from a *fatal with a live generation* (previous section). But if
either is taken — e.g. a clean close followed by a disconnect — the surviving process
carries the **entire Q4 inventory** into the next session, and F2 would correctly
score that as `stale residue`. Two items are already known-defective there:
```
Q4/F1  gateAMappedState is left dangling by setSharedState(NULL)
       (activity.cpp:436, :549 -> renderer.cpp:2404-2405, :2427-2428) and has no
       clear site (activity.cpp:143, :418-419, :503).
Q4/F3  the renderer obs terminal is one-shot per process
       (renderer.cpp:147, :149-159), so a surviving Activity cannot emit a second
       clean END.
```
**F2 must therefore assert that the Activity process actually died**, not merely that
the socket closed. Without that assertion, a surviving-Activity run and a
fresh-process run are indistinguishable in the evidence.

## FINDING Q11-F2 — the observation channel is inherently cross-session

The R8 observation sink is **logcat**, not a file:
```
lorie_r8_obs.c:146, :162, :189, :200, :220   __android_log_print(..., "R8_OBS", ...)
```
logcat is a kernel-backed ring buffer that survives process death, and the standing
redline forbids `logcat -c`. So a fresh session's capture **will** contain the fatal
session's `R8_OBS` records unless it is windowed.

The runner already windows it, and this must not regress:
```
run-r8-one-cell-b984ded-v11.sh:142   logcat -v threadtime -T "$since"
run-r8-one-cell-b984ded-v11.sh:267   echo "logcat_since=$SINCE" | tee "$EVIDENCE/logcat-since.txt"
```
**F2's "fresh session has stale residue -> VALID_FAIL" must be evaluated against the
windowed capture only.** Pre-window carryover is an artifact of the sink, not product
residue, and misreading it would fail a correct F2.

## WHAT IS PROVEN

```
P1  Every Gate A fatal is noreturn _exit(127). No in-process recovery exists.
                                                              lorie.h:1414-1418
P2  Fatal identity is single-writer: first-wins CAS, and gateAXFatal declines to
    overwrite a peer's identity.              lorie.h:634-641; InitOutput.c:3213-3218
P3  A bound Activity ALWAYS dies when X dies — both classifier arms terminate.
                       lorie_gatea_hup_class.h:32-36; activity.cpp:421-426, :145-155
P4  gateABound is cleared at exactly two lines, neither on a fatal path.
                     activity.cpp:173 (via renderer.cpp:813, clean close only), :211
P5  The shared region is ANONYMOUS in all three creation paths and cannot be
    reopened by name.                                            buffer.c:94-106
P6  A fresh X process memsets the region and draws a fresh getrandom nonce, so
    generationFatal / fatalReason / firstFailed* / gpuCopyQueue all start zero.
                                                   InitOutput.c:510, :523-525
P7  Every Gate A table on both sides is a file-scope static, hence zeroed in a fresh
    process.          cmdentrypoint.cpp:66; renderer.cpp:218-220; activity.cpp:137-143
P8  The R8 obs sink is logcat, which survives process death; the runner windows it
    with -T "$since".    lorie_r8_obs.c:146..220; runner:142, :267
```

## WHAT IS NOT PROVEN

```
N1  Whether Android restarts the Activity after _exit(127), and how soon. Outside
    this tree. F2's "fresh session" therefore depends on an orchestration step the
    product does not control. NOT PROVEN here.
N2  Whether the AHardwareBuffers held by the dying processes are actually released
    by gralloc refcounting. Reclamation is expected from process teardown, but no
    line in this tree establishes it. NOT PROVEN.
N3  Whether an EXPECTED F1 fatal specifically leaves the Activity bound. The general
    argument (P4) covers any fatal with a live generation, but F1's exact
    construction — enum16/side2 -> x-wrong-generation/reason6 — has not been traced
    here to confirm the generation is still live at that instant. Trace it when F1
    is designed.
N4  Whether a surviving Activity (Q11-F1) is observable at all from current evidence.
    Q4/F3 says it cannot emit a second clean END, which is suggestive but is an
    ABSENCE of a record, not a positive signal. NOT PROVEN.
```

## R9 TEST IMPLICATION

```
1  F2 is SATISFIABLE from source: (a) and (b) are structural for a new process pair,
   and (c) follows. No DESIGN_REQUIRED.
2  F2 MUST positively assert the Activity process died — e.g. record the APK
   process (PID, starttime) per Q7/Q8 on both sides of the boundary and require the
   tuple to change. Socket closure alone does not prove it (Q11-F1).
3  F2 MUST evaluate residue against the WINDOWED logcat only (Q11-F2). Record
   logcat-since.txt in the F2 evidence exactly as the R8 runner does.
4  N3 is a small open item owned by F1's construction, not by F2. Settle it when F1
   is designed; F2 inherits the answer.
5  Q4/F1 and Q4/F3 are the two things that would make a survive-arm run LOOK like a
   clean one. Both are recorded; neither needs a product rebuild to be avoided,
   because F2 can assert process identity instead.
```

## Q3 / Q4 / Q5 / Q6 CROSS-CHECK

```
CONTRADICTION_FOUND: none.
```
```
Q3  Directly reused: "sessionNonce is per X PROCESS, never re-rolled" is exactly why
    criterion (a) is structural. A fresh session is a fresh process, so the nonce is
    new by construction rather than by any reset logic.
Q4  Directly reused: the inventory of retained renderer state IS the residue list.
    Q11 adds that it only matters on the survive-arms, which a fatal does not take.
    Q4/F1 and Q4/F3 are re-cited, not revised.
Q5  Consistent. Q5's "containment rests on process death" is the same mechanism that
    makes F2 work: process death is the reclamation path, and F2 is the test that
    it happened.
Q6  Consistent. Q6 traced containment WITHIN a session; Q11 traces what survives
    ACROSS one. Neither revises the other.
```
No claim in Q3, Q4, Q5 or Q6 is withdrawn.

## FINAL VERDICT

```
FRESH_RECOVERY_STRUCTURALLY_SOUND   (a) new nonce and (b) empty registry are
                                    guaranteed for a new process pair; (c) follows.
                                    buffer.c:94-106; InitOutput.c:510, :523-525;
                                    cmdentrypoint.cpp:66; renderer.cpp:218-220
BOTH_PROCESSES_DIE_ON_BOUND_FATAL   both peer-HUP arms terminate the Activity, and
                                    gateABound is never cleared on a fatal path.
                                    lorie_gatea_hup_class.h:32-36; activity.cpp:173, :211
SURVIVE_ARM_RESIDUE_RISK            HUP_UNBOUND and X-inactive-at-EOF let a process
                                    live on carrying the whole Q4 inventory. Not
                                    reachable from a live-generation fatal, but F2
                                    must assert process death rather than assume it.
                                    activity.cpp:420, :429-438; cmdentrypoint.cpp:1349-1354
OBS_CHANNEL_CROSS_SESSION           logcat survives process death and logcat -c is
                                    forbidden; residue must be judged on the windowed
                                    capture.  lorie_r8_obs.c:146..220; runner:142, :267
```
`DESIGN_REQUIRED` is **not** raised. F2's criteria are reachable; the two findings are
assertions F2 must make, not defects that block the freeze.

## STILL OPEN
```
Q1 Q2 Q9 Q10 — §8.1 still forbids running R9 off PR #7's design.
Q10 now has FOUR converging pre-answers: no nonce re-roll (Q3), no READY teardown
    outside UNREGISTER (Q5), no context turnover (Q4/F2), and — from this trace —
    process death being the ONLY reclamation path that actually works.
```
