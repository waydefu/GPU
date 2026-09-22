# D-06 — V1 LIFECYCLE SCOPE — **DECIDED 2026-09-22**

DECISION OWNER user (authorised 2026-09-22).
PRODUCT `dc94485a7ef4f74cada36ea3c1d35d0aa0f48693`, tree `src/f8-ahb-gatea-r7-p1-arm`.
MODE host-only source trace + already-frozen R8/R9 runtime evidence. No new device run.

---

## 1. THE DECISION

**V1-Core does not implement, and does not qualify, any of:**

```
same-X warm reconnect                  a NEW Activity attaching to a SURVIVING X
Activity replacement while retaining X  same thing, stated the other way
generation 2                            any second generation inside one X process
cross-generation registry handoff
cross-generation GPU resource reclamation
```

**V1-Core's recovery model is FRESH-PROCESS RECOVERY:**

```
Activity / renderer suffers an unrecoverable interruption
  -> the experimental X3 session ends
  -> the old process(es) disappear
  -> new X process + new Activity + new sessionNonce + fresh registry
  -> Gate A is re-established
```

If a future V2 wants same-X reconnect, it reopens generation qualification then.
**V1 does not wait for it.**

## 2. WHY THIS IS NOT A POLICY CHOICE

The important part of this decision is that **it describes the only behaviour the
product has.** It is not a scope cut layered on top of a more capable product; every
alternative is unreachable in `dc94485`.

### 2.1 There is no reachable generation boundary

Proven in `planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md` §C-§E. The bump path
(`InitOutput.c:565-589`) runs exactly once per X process — the first
`lorieActivityConnected()` takes the `generation == 0` branch and sets generation 1.
A second is unreachable because

* X outlives its Activity only when `lorieGateAActive()` is already false
  (`InitOutput.c:620-624`);
* a clean close zeroes `sessionNonce` as well as `generation`
  (`InitOutput.c:3334-3335`) and the bump is gated on a non-zero nonce (`:567`);
* every fatal publisher that would clear the gate exits the X process in the same
  breath — X-side through `lorieGateAFatalHalt`'s `_exit(127)`
  (`lorie.h:1414-1416`), renderer-side because all 14 publish sites fire while X is
  inside `gateAWaitTerminal` for that serial.

Corroboration, not proof: 201 989 `GATEA_EVENT` lines under `evidence/`, `generation`
never above 1.

### 2.2 A new Activity cannot attach to a surviving X

`planning-v2/r9-fixture/CONSTRUCTION-PROOFS.md` §3 traced every `tryConnect()` call
site. While X1 is alive and `service != null`, no path calls `tryConnect()` again, so
no path calls `connect_()` with a new fd. `MainActivity` is `singleInstance`
(`AndroidManifest.xml:22`), so `am start` on a running instance does not re-run
`onCreate`; the `ACTION_START` route needs a **Binder**, which cannot be marshalled
through `am broadcast` from a shell; and the UI route is gated on `!connected`, which
is `conn_fd != -1` and therefore false while X1 lives.

### 2.3 NEW, and the reason this decision can be made with confidence

Section 2.2 is about the Activity being handed a new fd. There is a second, stronger
reason, found while designing R10: **when Gate A is bound and the X socket HUPs, the
Activity process dies, unconditionally.**

```c
lorie_gatea_hup_class.h:28-34   lorieGateAClassifyPeerHup(bound, publishedFatal)
    !bound                 -> LORIE_GATEA_HUP_UNBOUND
    bound, published != 0  -> LORIE_GATEA_HUP_PRESERVE
    bound, published == 0  -> LORIE_GATEA_HUP_R_HUP

activity.cpp:442-447
    PRESERVE -> gateAHupPreserve(...)                 -> _exit(127)   (:149-156)
    R_HUP    -> lorieGateAFatalHalt("r-hup", ...)     -> _exit(127)   (lorie.h:1416)
```

Both arms terminate the process. The Activity survives an X disconnect **only** when
`bound == 0`.

**Runtime evidence for both arms, from frozen R9 attempts:**

```
PRESERVE  r9-f1/attempt-03   X halts x-wrong-generation; Activity pid 15036 logs
                             "GATEA_HUP_PRESERVE published=6 nonce=1413323786942
                             4124691 generation=1" and Zygote reports
                             "Process 15036 exited cleanly (127)"
R_HUP     r9-f2/attempt-01   X killed abruptly with no published fatal; Activity pid
                             22241 logs "GATEA_FATAL_HALT what=r-hup reason=6"
```

So for every *unclean* end of an X session, both processes die. **The V1 recovery
model in §1 is not a rule we are imposing — it is what happens.**

### 2.4 The one path where the Activity does survive, and why it is not a bump

`bound` returns to 0 on a **clean** generation close. `renderer.cpp:834-860`, unbind at `:846`: on
`GENERATION_CLOSE` the renderer requires its own registry to be empty for that tuple
(`r-close-not-empty` otherwise), ACKs, traces `GENERATION_CLOSED`, and calls
`lorieGateAUnbindTuple` — which sets `gateABound = 0` (`activity.cpp:171-181`).

A later HUP is then classified `UNBOUND` and the Activity survives. `connect_`
(`activity.cpp:564-598`) will accept a new fd, and `CmdEntryPoint` re-broadcasts
`ACTION_START` every 1000 ms (`CmdEntryPoint.java:125-129`) so a running
`MainActivity`'s receiver picks the new X up (`MainActivity.java:130-133` ->
`onReceiveConnection` -> `tryConnect` -> `LorieView.connect(fd)` at `:612`).

**Runtime evidence:** R8-D `attempt-01` ends with the test-control terminate. The
renderer process 29941 emits `R_UNBOUND_FINAL {"ready":0,"pending":0}` at
`08:50:13.761` and is still logging at `08:50:16.215`, 2.5 s later. Zero
`GATEA_HUP_PRESERVE`, zero `r-hup`, no exit.

**This is a NEW X session in a surviving Activity process.** It is not generation 2
and not a same-X reconnect: the new X is a new process, so it draws a **new
`sessionNonce`** and starts at generation 1 with an empty registry. It needs no
product change. Calling it "warm" in the §8.4 sense is correct; calling it a
generation bump is not.

It matters for V1 for one reason, and R10 is built around it: **the Activity process
outlives the session, so anything the renderer fails to release at a clean close
accumulates across sessions in a process the user never restarts.**

### 2.5 What is therefore defensive-only in the current product

```
x-bump-unterminal   cmdentrypoint.cpp:391    no runtime caller (§2.1)
x-share-in-lease    InitOutput.c:570         same
r-rebind-busy       activity.cpp:211-212     reachable only from gateABindFromState
                                             with a DIFFERENT tuple while bound. The
                                             only route to a second bind is §2.4,
                                             which passes through a clean close, and
                                             a clean close has already proven the
                                             renderer registry empty. So the "busy"
                                             arm cannot be entered.
```

Defensive-only is **not** dead code to be removed. It is the containment that makes
the above statements safe to rely on, and its continued presence is pinned by
`verify-r9-support.py`.

## 3. WHAT THIS DECIDES FOR QUALIFICATION

```
R9 removed cells      stay SOURCE-PROVEN / RUNTIME-NOT-CONSTRUCTIBLE. §2.3 and §2.4
                      STRENGTHEN the WARM removal rather than overturning it: not
                      only can nothing hand a live Activity a new fd while X1 lives
                      (§2.2), the Activity would also have to survive X1's death,
                      which it does not unless the close was clean (§2.3).
R10                   must NOT test generation 2, and must NOT be built from V2.3
                      §9.2's "warm + cold" as originally meant. See V2-R10-DESIGN.
Master plan §8.4      WARM ("Activity 未重啟，X server 為新") remains a REACHABLE
                      configuration, but only via §2.4's clean close. It is a new
                      SESSION, not a new generation. §8.4 never said "generation",
                      so it is not wrong; it is easy to misread and is annotated.
Master plan §9        the sampling point K3 "generation close / process exit 後" is
                      only observable in-process on the clean-close path; on the
                      fatal paths the process is gone. V2-R10-DESIGN splits it.
```

## 4. CLAIM SCOPE

This decision is bound to `dc94485` and to the V1 lifecycle. It says nothing about
whether same-X reconnect is *desirable*, only that it is absent and that V1 does not
need it. Every statement above is either a `file:line` in this tree or a frozen
runtime observation named by attempt.

**Reopen conditions** (any one reopens generation qualification, and with it
R9-WARM-1/2/3 and R9-COLD-2):

```
a warm reconnect / rebind entry point that hands a live Activity a new fd while
  its current X is alive
a renderer fatal publisher reachable OUTSIDE an X terminal wait
a change to lorieGateAClassifyPeerHup that lets a BOUND Activity survive a HUP
```

`verify-r9-support.py` pins the source facts behind the first two.
The third is pinned by `V2-R10-HOST-VERIFY` (see V2-R10-DESIGN §7).
