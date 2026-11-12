# R9 DESIGN FREEZE — Q9 (socket lifecycle and cross-generation residue)

## QUESTION
What is the full lifecycle of the X↔renderer socket on each side, and what state
attached to it survives a generation boundary?

## SOURCE AUTHORITY
```
TREE   src/f8-ahb-gatea-r7-p1-arm @ 14caa7b (branch feat/gatea-r8-lifecycle-support-20260918)
DATE   2026-09-22
MODE   host-only, read-only, no device, no adb, no build, no CI, no source mutation,
       no runtime attempt
DEPTH  Q3/Q4/Q5/Q6/Q11 standard. Every claim cites file:line. Unsettled -> NOT PROVEN.
BUILDS ON Q6 (each connect allocates a NEW socket; two threads), Q11 (both EOF arms)
```

## LIFECYCLE — X SIDE

```
CREATE      cmdentrypoint.cpp:1519   socketpair(AF_UNIX, SOCK_STREAM, 0, client)
REGISTER    cmdentrypoint.cpp:1521   InputThreadRegisterDev(client[1], handleLorieEvents, nullptr)
INSTALL     cmdentrypoint.cpp:1522   conn_fd = client[1]          (volatile int, :44)
BUMP        cmdentrypoint.cpp:1523   lorieActivityConnected()     -> generation +1 (Q3)
HAND OFF    cmdentrypoint.cpp:1528   client[0] adopted by Java via ParcelFileDescriptor
TEARDOWN    cmdentrypoint.cpp:831-840 closeLorieConnection(fd):
              :833  InputThreadUnregisterDev(fd)
              :834-835  if (conn_fd == fd) conn_fd = -1
              :836  close(fd)
              :837  lorieEnableClipboardSync(FALSE)
              :838-839  drain registeredBuffers
            callers: :848 (legacy X_NOTIFY_ERROR), :1308 (proto X_NOTIFY_ERROR),
                     :1351 (proto EOF/IO/PROTOCOL_FATAL while Gate A INACTIVE)
```

## LIFECYCLE — RENDERER SIDE

```
TEARDOWN-FIRST  activity.cpp:540-553  connect_():
                  :544-548  if (oldFd != -1): ALooper_removeFd(oldFd); conn_fd = -1; close(oldFd)
                  :549-550  setSharedState(NULL); removeAllBuffers()
INSTALL         activity.cpp:556      conn_fd = fd
REGISTER        activity.cpp:558-560  ALooper_addFd(..., xcallback, NULL)
HANDSHAKE       activity.cpp:565-567  EVENT_RENDERER_WAKEUP_COND + SCM_RIGHTS as ONE record
HUP TEARDOWN    activity.cpp:429-437  ALooper_removeFd; conn_fd = -1; close(fd);
                                      setSharedState(NULL); removeAllBuffers()
```

## FINDING Q9-F1 — the two sides are ASYMMETRIC, and only X leaks

`connect_` (renderer) **tears the old socket down before installing the new one**:
`ALooper_removeFd` `:545`, `close(oldFd)` `:548`.

`getXConnection` (X) does **neither**. It registers the new fd (`:1521`) and reassigns
`conn_fd` (`:1522`) without calling `closeLorieConnection`, without
`InputThreadUnregisterDev`, and without closing the previous fd. `closeLorieConnection`
is reachable only from the three input-thread error/EOF arms listed above.

**Consequence:** between a second `getXConnection` and the old socket's EOF, **two fds
are registered to the same handler** `handleLorieEvents` (`:1521`), and the old fd is
still open.

That repeated calls are expected is itself established by the source: the bump path
exists only to service them —
```
InitOutput.c:571-574   "P1: every share starts a fresh generation. If the previous
                        tuple was still bound, poison it first..."
InitOutput.c:575-579   if (generation != 0) { PublishFatal; RegistryCloseGeneration; }
```
A first-and-only connect could never take that branch.

## FINDING Q9-F2 — one decoder, two fds, two threads, no lock

`gateARecordDecoder` is a **single file-scope static** (`cmdentrypoint.cpp:71`), with
a companion flag `gateARecordDecoderReady` (`:72`). It is used by two different
callers reading from two different fd expressions:

```
X INPUT thread   handleLorieEventsProto(int fd, int ready)      cmdentrypoint.cpp:1304
                   :1319  if (!gateARecordDecoderReady) gateAInitRecordDecoder()
                   :1327  lorieRecordDecoderNext(fd, &gateARecordDecoder, &record)
                          ^^ the CALLBACK's fd
X MAIN thread    lorieGateAPumpConnection(deadline, legacyPolicy) cmdentrypoint.cpp:1237
                   :1246  if (!gateARecordDecoderReady) gateAInitRecordDecoder()
                   :1248  pollFd.fd = conn_fd
                   :1281  lorieRecordDecoderNext(conn_fd, &gateARecordDecoder, &record)
                          ^^ the CURRENT conn_fd
                 called from InitOutput.c:2768, inside gateAWaitForReply
```

Thread identity is established in Q6: `handleLorieEvents` is registered with
`InputThreadRegisterDev` (`:1521`) and therefore runs on the X **input** thread, while
`lorieActivityConnected` and the Gate A waiters run on the X **main** thread inside a
`QueueWorkProc` closure (`:1520-1525`). `InputThreadUnregisterDev` appears exactly
once, in `closeLorieConnection` (`:833`), so nothing suspends the input thread while
the main thread pumps.

**No mutex covers the decoder.** `cmdentrypoint.cpp` declares exactly two file-scope
mutexes — `gateARegistryMutex` (`:67`) and `gateASendMutex` (`:68`) — plus per-entry
waiter locks (`:108-110`). Neither is taken on any decoder path.

And partial state is retained **by design**, which is what makes the sharing matter:
```
InitOutput.c:2775-2776   "INCOMPLETE and WOULD_BLOCK retain decoder state and return
                          to the same absolute deadline. There is deliberately no
                          sleep retry."
```
The retained fields are substantial (`lorie.h:911-928`): `phase`, `prefix/prefixLen`,
`gateHeader/gateHeaderLen`, `gateBody/gateBodyLen/gateBodyNeed`,
`legacyBase/legacyBaseLen`, `payload/payloadLen/payloadOffset`, `receivedFd`.

```
CLASS       shared mutable parser state across two threads and (after Q9-F1) two fds
PROVEN      one decoder (:71); two callers on two threads (:1327 vs :1281); no lock
NOT PROVEN  that both callers are ever ACTIVE simultaneously. The X main thread only
            pumps while blocked in gateAWaitForReply (InitOutput.c:2768); whether the
            input thread can deliver a record in that interval is not settled by any
            line in this tree. NOT PROVEN either way.
```

## FINDING Q9-F3 — an old socket's EOF wipes the NEW connection's decoder

Both proto teardown arms destroy the shared decoder unconditionally:
```
cmdentrypoint.cpp:1308-1310   closeLorieConnection(fd);
                              lorieRecordDecoderDestroy(&gateARecordDecoder);
                              gateARecordDecoderReady = 0;
cmdentrypoint.cpp:1351-1353   same, on the EOF/IO/PROTOCOL_FATAL arm
```
`lorieRecordDecoderDestroy` is `lorieRecordDecoderReset` (`lorie.h:962-965`), which
frees `payload`, closes `receivedFd`, and memsets the whole struct
(`lorie.h:950-959`).

Combined with Q9-F1: after a second `getXConnection`, the **old** fd is still
registered. When it reaches EOF, its handler runs `closeLorieConnection(oldFd)` —
correctly leaving `conn_fd` alone, because of the guard at `:834-835` — but then
**destroys the decoder that the NEW connection may be mid-record on**, and clears
`gateARecordDecoderReady`.

The same arm also drains `registeredBuffers` (`:838-839`), a single process-wide list
(`:53`, initialised once at `:556`) that the **new** generation has already populated
via `lorieRegisterBuffer` (`InitOutput.c:593` -> `cmdentrypoint.cpp:1403-1412`).

```
PROVEN      the decoder destroy and the registeredBuffers drain are unconditional on
            those arms, and conn_fd is correctly guarded while they are not
NOT PROVEN  that an old fd survives long enough to reach EOF after a new connect.
            Depends on Java-side close ordering, outside this tree.
```

## CROSS-GENERATION RESIDUE — INVENTORY

| # | state | decl | tied to a socket? | cleared on teardown? |
|---|---|---|---|---|
| 1 | `conn_fd` | `cmdentrypoint.cpp:44` | yes | `:834-835`, guarded by identity |
| 2 | `gateARecordDecoder` | `cmdentrypoint.cpp:71` | **no — process-wide** | `:1309`, `:1352` (unconditional) |
| 3 | `gateARecordDecoderReady` | `cmdentrypoint.cpp:72` | no | `:1310`, `:1353` |
| 4 | `registeredBuffers` | `cmdentrypoint.cpp:53` | **no — process-wide** | drained `:838-839` |
| 5 | `gateAXRegistry[16]` | `cmdentrypoint.cpp:66` | no | NOT on socket teardown; per-generation via `:380-397` (Q3) |
| 6 | `gateADeferredHead/Tail` | `cmdentrypoint.cpp` | no | `lorieGateACancelDeferred(0,0)` at `:1354` only on the INACTIVE arm (Q6) |
| 7 | InputThread registration | `:1521` | yes | only `closeLorieConnection` `:833` |
| 8 | renderer `conn_fd` + looper reg | `activity.cpp:556-560` | yes | `:545-548`, `:429-431` — both sides torn down |
| 9 | renderer wakeup fd (SCM_RIGHTS) | `activity.cpp:565-567` | sent once per connect | → `lorieSetRendererWakeupCond`, `cmdentrypoint.cpp:1197-1201` |

**Items 2, 3, 4 and 6 are process-scoped but torn down on a per-socket event.** That
mismatch is the entire content of Q9.

## FD OWNERSHIP

```
decoder-received fd   lorie.h:955-956   closed by lorieRecordDecoderReset
per-record fd         lorie.h:938-946   lorieRecordRelease: free(payload) + close(fd),
                                        idempotent (fd guarded by >= 0, free(NULL) ok)
deferred record fd    lorie.h:1337-1347 lorieDeferredLegacyDisposeOwned, idempotent (Q6)
wakeup fd             cmdentrypoint.cpp:1196-1201  moved out of the record
                                        (record->receivedFd = -1) before handing to
                                        lorieSetRendererWakeupCond -> no double close
socketpair halves     :1528 client[0] to Java; client[1] to the WorkProc closure
```
No double-close and no leak is visible on the record paths. **NOT PROVEN:** whether
`client[1]` is leaked if `QueueWorkProc` (`:1520`) fails — its return value is not
checked, and there is no error arm.

## WHAT IS PROVEN

```
P1  The renderer tears the old socket down before installing a new one; X does not.
                          activity.cpp:544-548 vs cmdentrypoint.cpp:1519-1523
P2  closeLorieConnection is reachable ONLY from the three input-thread error/EOF
    arms, never from getXConnection.        cmdentrypoint.cpp:848, :1308, :1351
P3  Repeated connects are an expected mode: the generation-bump branch only executes
    on a second one.                                        InitOutput.c:571-579
P4  One process-wide decoder serves two callers on two different threads reading two
    different fd expressions, with no mutex.
            cmdentrypoint.cpp:71, :1327 (input thread), :1281 (main thread), :67-68
P5  Retaining partial decoder state across calls is deliberate.
                                                           InitOutput.c:2775-2776
P6  Both proto teardown arms destroy the shared decoder and clear its ready flag
    unconditionally.                             cmdentrypoint.cpp:1308-1310, :1351-1353
P7  conn_fd IS correctly identity-guarded on teardown, so an old fd's close does not
    clobber a newer conn_fd.                            cmdentrypoint.cpp:834-835
P8  registeredBuffers is one process-wide list drained by any socket teardown.
                                          cmdentrypoint.cpp:53, :556, :838-839
P9  Record and deferred fd disposal is idempotent; the wakeup fd is moved out before
    hand-off, so no double close is visible.
                                lorie.h:938-946, :955-956, :1337-1347; :1196-1201
```

## WHAT IS NOT PROVEN

```
N1  Whether the X input thread and the X main thread are ever concurrently inside
    lorieRecordDecoderNext. Structurally possible (P4, and nothing suspends the input
    thread — InputThreadUnregisterDev occurs only at :833). NOT PROVEN either way.
N2  Whether an old fd survives a second getXConnection long enough to reach EOF and
    run the destructive arm (Q9-F3). Depends on Java-side close ordering. NOT PROVEN.
N3  Whether getXConnection is in fact called more than once per X process. P3 proves
    the C side is DESIGNED for it; the Java call site is outside this tree.
N4  Whether client[1] leaks when QueueWorkProc fails (:1520, return value unchecked).
N5  Whether SOCK_STREAM short reads can split a Gate A frame across a decoder
    destroy. The decoder is explicitly incremental (P5) so it tolerates splitting
    WITHIN a connection; splitting ACROSS a destroy is Q9-F3 and is NOT PROVEN
    reachable.
```

## R9 TEST IMPLICATION

```
1  Every R9 packet that crosses a generation boundary by RECONNECTING must record,
   on the X side, whether the previous fd was still registered at the moment of the
   bump. Nothing in the product reports this today, so it has to come from /proc
   (the fd table of the X PID) at the boundary.
2  Q9-F2 gives a cheap falsifiable assertion: if the decoder were ever corrupted by
   concurrent use, the symptom is a PROTOCOL_FATAL / x-record-error on a stream that
   was otherwise healthy. R9 should classify any such fatal as a Q9 candidate rather
   than a construction failure.
3  Q9-F3 means an R9 RECONNECT packet must not treat "decoder reset" as evidence of a
   clean boundary — an OLD socket's EOF produces the same observable.
4  Item 4 of the inventory (registeredBuffers) is the one that can silently change
   the NEW generation's admissibility: after a stale EOF, lorieRegisterBuffer
   (:1404) will re-send buffers it thinks are unregistered. Record the list length
   at the boundary, or the effect is unattributable.
```

## Q3 / Q4 / Q5 / Q6 / Q11 CROSS-CHECK

```
CONTRADICTION_FOUND: none.
```
```
Q6   Directly extended. Q6 proved each connect allocates a NEW socket
     (cmdentrypoint.cpp:1519, :1522) and that the bump and the pump run on different
     threads. Q9 adds that the OLD socket is neither closed nor unregistered, which
     is what turns Q6's "different fd" observation into a live residue question.
Q11  Consistent and complementary. Q11 traced the two EOF arms as the survive-vs-die
     decision; Q9 traces what those same arms DESTROY on the way through
     (decoder :1309/:1352, registeredBuffers :838-839).
Q3   Reused: the bump branch (InitOutput.c:575-579) is the proof that repeated
     connects are expected (P3).
Q4   Consistent. Q4 inventoried RENDERER-side retention; Q9 inventories the X-side
     socket-adjacent retention. Together they cover both processes.
Q5   Untouched by this trace.
```
No claim in Q3, Q4, Q5, Q6 or Q11 is withdrawn.

## FINAL VERDICT

```
SOCKET_TEARDOWN_ASYMMETRY        renderer closes+unregisters the old socket before
                                 installing a new one; X does neither.
                                 activity.cpp:544-548 vs cmdentrypoint.cpp:1519-1523
SHARED_DECODER_UNSYNCHRONIZED    one process-wide decoder, two threads, two fd
                                 expressions, no mutex; partial state retained by
                                 design. Concurrency NOT PROVEN (N1).
                                 cmdentrypoint.cpp:71, :1281, :1327; InitOutput.c:2775-2776
STALE_EOF_DESTROYS_LIVE_STATE    an old socket's EOF unconditionally destroys the
                                 shared decoder and drains registeredBuffers, both of
                                 which may belong to the NEW connection.
                                 cmdentrypoint.cpp:1308-1310, :1351-1353, :838-839
CONN_FD_IDENTITY_GUARD_CORRECT   the one thing the X side does get right.
                                 cmdentrypoint.cpp:834-835
```
`DESIGN_REQUIRED` is **not** raised: all three findings are conditional on N2/N3,
which are Java-side facts, and none corrupts state on a path proven reachable here.
They are observation requirements for R9, not freeze blockers.

## STILL OPEN
```
Q1 Q2 Q10 — §8.1 still forbids running R9 off PR #7's design.
Q10 now has FIVE converging pre-answers: no nonce re-roll (Q3), no READY teardown
    outside UNREGISTER (Q5), no context turnover (Q4/F2), process death as the only
    working reclamation (Q11), and — from this trace — no X-side socket teardown
    outside an error/EOF arm.
```
