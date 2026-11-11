# R9 DESIGN FREEZE — Q3 RESOLVED (generation / nonce lifecycle)

DATE 2026-09-21  MODE host-only source trace, read-only, no device, no attempt consumed
TREE `src/f8-ahb-gatea-r7-p1-arm` @ `14caa7b` (branch `feat/gatea-r8-lifecycle-support-20260918`)
SCOPE Answers Q3 only. Q1/Q2/Q4/Q5/Q6/Q9/Q10/Q11 remain OPEN.
DEPTH `V2-R8-D-SRC-TRACE` — every claim below cites a line. No speculation.

Q3 asks three things: **allocated when, invalidated when, compared by whom.**

---

## A. Allocated when

The tuple has two components with **different lifetimes**. This asymmetry is the
whole answer to Q3 and it is not stated anywhere in PR #7's design.

### A.1 `sessionNonce` — once per X server PROCESS, never re-rolled

```
InitOutput.c:523   syscall(SYS_getrandom, &gateaNonce, sizeof(gateaNonce), 0)
InitOutput.c:525   lorieScreen.state->gateA.sessionNonce = gateaNonce
```
Inside the one-time server-state `mmap` block, immediately after
`memset(lorieScreen.state, 0, …)` (`InitOutput.c:510`). Exact-length randomness
only; a short read or error leaves the nonce 0 and logs
`"Gate A disabled: session nonce unavailable"` (`InitOutput.c:527`). There is no
weak fallback.

**The complete set of writers to the shared `gateA.sessionNonce` is four lines:**
```
InitOutput.c:525    getrandom value          <- the ONLY nonzero-producing write
InitOutput.c:582    = 0   (generation exhausted)
InitOutput.c:584    via lorieGateAProtocolInit — rewrites the value it just read
InitOutput.c:3335   = 0   (clean generation close)
```
Consequence, load-bearing for Q10: **no code path re-rolls the nonce inside a live
X process.** Once any path zeroes it, Gate A is dead for the remaining life of that
process, because `lorieActivityConnected()` is guarded by `sessionNonce != 0`
(`InitOutput.c:567`) and can never re-enter.

### A.2 `generation` — once per Activity SHARE, 1-based, monotonic

`generation` stays 0 after the memset; it is not allocated with the nonce. The sole
allocator is `lorieActivityConnected()`:
```
InitOutput.c:565   void lorieActivityConnected(void)
InitOutput.c:567     guard: proto enabled && sessionNonce != 0
InitOutput.c:569-570 if (gateAPairActive())
                        lorieGateAFatalHalt("x-share-in-lease", FAIL_GENERATION)
InitOutput.c:575-579 if (generation != 0):   PublishFatal(FAIL_GENERATION)
                                             lorieGateARegistryCloseGeneration(nonce, gen)
InitOutput.c:580-582 if (generation == UINT64_MAX): sessionNonce = 0  (saturate, never wrap)
InitOutput.c:584-586 lorieGateAProtocolInit(&gateA, sessionNonce, generation + 1)
InitOutput.c:592   lorieSendSharedServerState(pvfb->stateFd)
```
The bump at `:586` happens **before** the fd is sent at `:592`. That ordering is what
lets the renderer's bind observe the new generation and never the old one.

**The complete set of writers to the shared `gateA.generation` is two lines**
(`InitOutput.c:584` via `lorie.h:507`, and `InitOutput.c:3334` `= 0`). Everything
else that looks like a generation write — `lorie.h:566`, `:584`, `:1726` — writes a
*per-record* or *per-DirectMeta* copy, not the shared field.

---

## B. Invalidated when

Two distinct paths, with **different effects on the nonce**. Conflating them is the
trap.

### B.1 Re-share bump — keeps the nonce, poison is TRANSIENT

`lorieActivityConnected()` publishes fatal on the outgoing generation
(`InitOutput.c:576`), then closes its registry entries
(`cmdentrypoint.cpp:380-397`), then calls `lorieGateAProtocolInit`. That init
**clears `generationFatal` back to 0** (`lorie.h:505`), along with
`firstFailedSerial`, `firstFailureCode` and `fatalReason` (`lorie.h:508-510`).

So the poison raised at `:576` does not persist into the new generation. What
actually keeps old work out is the *generation number itself*, not the fatal flag.
Any R9 packet that expects to observe `generationFatal != 0` after a re-share will
see 0 and must not treat that as "no fatal occurred".

`lorieGateARegistryCloseGeneration` fail-stops rather than closing over live work:
```
cmdentrypoint.cpp:389-393  if (e->meta.pendingCount != 0 || e->meta.lastSubmittedSerial != 0)
                               lorieGateAFatalHalt("x-bump-unterminal", FAIL_GENERATION)
cmdentrypoint.cpp:395-396  else: meta.state = REG_DEAD; WaiterSignal(FAILED)
```

### B.2 Clean close — zeroes BOTH

**CORRECTED 2026-09-22 by Q10.** This section originally read "terminal for the
process" and glossed the caller as "X server shutdown". Both were wrong: the clean
close also runs on an X server **DE_RESET**, which leaves the process alive. See
`Q10-same-process-reset-support.md` for the proven chain. The line citations below
are unchanged.

`gateACloseGeneration()` (`InitOutput.c:3289`) is a full protocol drain: wait
terminal, assert queue drained and unfatal, retire every registry id, assert the
registry empty, `lorieGateACancelDeferred(nonce, generation)`, send
GENERATION_CLOSE, wait for a clean ACK, and only then:
```
InitOutput.c:3334   generation   = 0
InitOutput.c:3335   sessionNonce = 0
```
**Production callers: exactly one** — `lorieCloseScreen()` (`InitOutput.c:1228`,
call at `:1240`). The enumeration is correct; the original gloss "i.e. X server
shutdown" was NOT. `lorieCloseScreen` is the installed CloseScreen
(`InitOutput.c:1461`) and `dix/main.c:325` calls CloseScreen **unconditionally** in
the loop tail — only `ddxGiveUp` and the loop break are DE_TERMINATE-gated
(`dix/main.c:353-356`). Since `dispatchExceptionAtReset` defaults to `DE_RESET`
(`dix/dispatch.c:3480`) and `-terminate` is not passed in this deployment, **the last
X client disconnecting reaches this close with the process still alive**, and the
nonce allocator is then guarded off (`InitOutput.c:494-495`). Full chain in
`Q10-same-process-reset-support.md`.

The other two call sites (`InitOutput.c:3444`, `:3449`) are behind
`lorieGateATestFaultConsume(…, LORIE_GATEA_TEST_CLOSE_WHILE_LEASE, …)` — fault
injection, which is what R8-P2 exercises.

---

## C. Compared by whom

Two **independent** authorities hold the tuple. This is the part R9 must design
around.

```
AUTHORITY 1  shared mapping  state->gateA.{sessionNonce,generation}   X writes, both read
AUTHORITY 2  renderer-local  gateABound{Nonce,Generation} + gateABound  activity.cpp:137-139
                             guarded by gateABindMutex (activity.cpp:136)
```

Authority 2 is a **latched copy**, taken only on `EVENT_SHARED_SERVER_STATE`:
```
activity.cpp:486   case EVENT_SHARED_SERVER_STATE
activity.cpp:504     gateABindFromState(state)
activity.cpp:190   gateABindFromState(): requires version match && nonce != 0 && generation != 0,
activity.cpp:205-206   and if already bound to a DIFFERENT tuple with live imports ->
                       lorieGateAFatalHalt("r-rebind-busy", FAIL_GENERATION)
activity.cpp:213     otherwise: latch nonce/generation, gateABound = 1
activity.cpp:214     else branch: gateABound = 0  (a zero tuple UNBINDS, it does not fault)
```
It is released by `lorieGateAUnbindTuple` (`activity.cpp:168`), which only succeeds
for an exact tuple match — called from the renderer's GENERATION_CLOSE handler
(`renderer.cpp:813`).

### Comparison sites, by role

| role | site | compares |
|---|---|---|
| X | `lorieGateAActive()` `InitOutput.c:613` | shared nonce != 0 && gen != 0 && !fatal |
| X | `gateAFrameTupleMatch()` `cmdentrypoint.cpp:599` | inbound frame vs shared, both nonzero |
| X | `gateADeferredTupleValid()` `cmdentrypoint.cpp:723` | queued record vs shared + `ObserveFatal` |
| X | direct-meta admit `InitOutput.c:2695-2696` | registry meta vs shared + state READY + fingerprint |
| X | `lorieDeferredLegacyCancelIfMatch()` `lorie.h:1361` | record vs (nonce, generation) argument |
| R | control drain `renderer.cpp:767-769` | **bound tuple** vs control msg → `r-control-tuple` fatal |
| R | ready-import scan `renderer.cpp:857` | entry vs **bound tuple** |
| R | `gateARegistryEmptyForGeneration()` `renderer.cpp:802` | per-generation emptiness at close |
| both | telemetry gate `lorie.h:1664-1665` | shared nonce/gen both nonzero |

**The renderer never compares against the shared field for admission** — it compares
against its latched copy (`renderer.cpp:494`, `:767`, `:851`, `:1735`, `:1777`,
`:2446`). The shared field is read by the renderer only for tracing and for the
`lorieGateAObserveFatal` checks.

---

## Ruling for R9

```
ADOPTED   generation identity = (sessionNonce, generation), both nonzero.
          sessionNonce is per-PROCESS; generation is per-SHARE, 1-based, monotonic,
          saturating at UINT64_MAX into permanent disable.
ADOPTED   A generation boundary is created by exactly one call: lorieActivityConnected().
          Every R9 packet that claims to cross a boundary must drive THAT path.
RECORD    Every R9 packet must record BOTH authorities at the boundary — the shared
          pair AND the renderer's bound pair — because they are latched independently
          and a lag between them is the failure mode, not an implementation detail.
WARNING   generationFatal does NOT survive a re-share bump (lorie.h:505). Absence of
          fatal after a bump proves nothing.
WARNING   A clean close zeroes the nonce (InitOutput.c:3335) and nothing re-rolls it.
```

## Carries into the still-open questions

```
Q10  RESOLVED 2026-09-22 — see Q10-same-process-reset-support.md. This note was
     RIGHT that a reset is impossible without new code, but UNDER-STATED the danger:
     the X server's own DE_RESET (the default; -terminate is not passed) reaches the
     clean close with the process STILL ALIVE, so Gate A can be permanently killed
     without X exiting. Q10 raises DESIGN_REQUIRED on D-01 with a 7-item scope.
Q6   RESOLVED 2026-09-21 — see Q6-stale-inflight-frame-cross-generation.md.
     Two REFINEMENTS to this document (neither withdraws a claim here):
     R-A  the window is genuine because the bump runs on the X MAIN thread while
          the record pump runs on the X INPUT thread (cmdentrypoint.cpp:1519-1526),
          and each connect allocates a NEW socket (:1519, :1522). Thread
          separation, not message ordering, is what makes it real.
     R-B  while generationFatal is SET during the bump, lorieGateAActive() is false,
          so inbound frames are SILENTLY DROPPED rather than fatal
          (cmdentrypoint.cpp:629-631). Reachability NOT PROVEN.
     Q6 also recorded two gaps: the bump asserts the registry but not the
     gpuCopyQueue, and the completion path has no generation check at all
     (containment rests entirely on serial uniqueness).
Q5   RESOLVED 2026-09-21 — see Q5-stale-ready-cross-generation.md.
     CORRECTION to this document's first draft: a stale READY does NOT rebind
     silently. lorieGateAImportBusy() counts READY occupancy (renderer.cpp:292),
     so a rebind over one is "r-rebind-busy" fatal (activity.cpp:204-207).
     §8.2's "most dangerous UAF surface" framing is not supported by the source.
```

## Still OPEN
```
Q1 Q2 Q4 Q5 Q6 Q9 Q10 Q11 — §8.1 still forbids running R9 off PR #7's design.
```
