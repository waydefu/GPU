# R9 DESIGN FREEZE — Q6 (stale / in-flight frame across generation transition)

## QUESTION
Can an old-tuple frame / queued record / deferred record / completion / pending GPU
work be accepted, executed, replayed, completed, or allowed to mutate state under a
NEW generation?

## SOURCE AUTHORITY
```
TREE   src/f8-ahb-gatea-r7-p1-arm @ 14caa7b (branch feat/gatea-r8-lifecycle-support-20260918)
MODE   host-only, read-only, no device, no adb, no build, no CI, no source mutation,
       no runtime attempt
DEPTH  Q3/Q5 standard. Every claim cites file:line. Anything the source does not
       settle is marked NOT PROVEN and is not argued around.
NOTE   lorieRecheckGpuCopies() is NOT defined in the lorie tree. Its definition is
       carried as a patch hunk: lorie/src/main/cpp/patches/xserver.patch:640-653,
       applied to present/present_scmd.c. Cited as patch lines.
```

## CALL GRAPH

```
X MAIN THREAD (DIX WorkQueue)                 X INPUT THREAD (InputThreadRegisterDev)
------------------------------                ---------------------------------------
getXConnection closure                        handleLorieEvents            :1361
  cmdentrypoint.cpp:1520-1525                   -> handleLorieEventsProto  :1304
  :1521 InputThreadRegisterDev(...,               -> lorieRecordDecoderNext :1281
            handleLorieEvents, ...)               -> record.isGate?
  :1522 conn_fd = <new socketpair fd>                Y: handleGateARecord  :628
  :1523 lorieActivityConnected()                     N: legacyPolicy switch :1286-1299
          InitOutput.c:565                              CANCEL -> release  :1287
          :576 PublishFatal(old gen)                    DEFER  -> gateAQueueDeferredRecord :1288
          :577 RegistryCloseGeneration                  else   -> handleLegacyRecord(,1)  :1294
          :584 ProtocolInit(nonce, gen+1)
          :592 lorieSendSharedServerState         gateADeferredWorkProc  :799  (X MAIN, WorkQueue)
          :593 lorieRegisterBuffer                  :801 gateADeferredUnlink
                                                    :802 gateADeferredTupleValid :723
gateACloseGeneration InitOutput.c:3289              :803 gateADeferredRelease  (DROP)
  :3324 lorieGateACancelDeferred                    :825 handleLegacyRecord(,0)

RENDERER / ACTIVITY LOOPER THREAD
---------------------------------
activity.cpp:486 EVENT_SHARED_SERVER_STATE -> :504 gateABindFromState :190  (LATCH)
activity.cpp:450 gateAPeekIsGateA -> bound? -> :457 gateAHandleFrame :271
                                    unbound -> :462 lorieGateAFatalHalt("r-unbound-frame")
```

## FRAME TUPLE DEFINITION (A)

`struct LorieGateAFrame`, `lorie.h:787-796`, size static-asserted 40 (`lorie.h:798`):
```
+0   uint32_t magic        LORIE_GATEA_MAGIC
+4   uint16_t version      LORIE_GATEA_PROTOCOL_VERSION
+6   uint16_t type         LorieGateAMsgType
+8   uint32_t length       body bytes
+12  uint32_t reserved     = 0
+16  uint64_t nonce        sessionNonce            <- identity
+24  uint64_t generation                           <- identity
+32  uint64_t bufferId     0 when not applicable   <- resource id
```
**There is no serial field in the frame.** Serial travels only in bodies
(`LorieGateAUnregisterBody.lastSubmittedSerial`, `LorieGateAGenerationCloseBody.lastPublishedSerial`,
`lorie.h:820-821`) and in the shared `gpuCopyQueue`.

| field | written | transmitted | read | compared |
|---|---|---|---|---|
| nonce, generation (X→R) | `cmdentrypoint.cpp:1421`,`:1479`,`:1488` from caller args (`InitOutput.c:2820`, `:3270`, `:3326`) | `conn_fd`, `cmdentrypoint.cpp:1442` under `gateASendMutex` `:1441` | `activity.cpp:276` | `activity.cpp:279` vs **LATCH** |
| nonce, generation (R→X) | `renderer.cpp:400`,`:805` from `ctl->nonce/generation` | `conn_fd` (activity side) | `cmdentrypoint.cpp:1281` decoder | `cmdentrypoint.cpp:603-606` vs **SHARED** |
| bufferId | same sends | same | same | `cmdentrypoint.cpp:650`,`:664`,`:678`; `activity.cpp:287`,`:296` |

`conn_fd` is one socket for both legacy events and Gate A frames —
`cmdentrypoint.cpp:44` (`volatile int conn_fd`, "The only variable shared with
activity code"), state fd sent on it at `:1397-1398`, Gate A frame written to the same
fd at `:1442`.

## NORMAL FRAME PATH (B)

**X side — exactly ONE tuple check, at decode/dispatch time:**
```
cmdentrypoint.cpp:629-631   int active = lorieGateAActive(); if (!active) return;   <- SILENT DROP
cmdentrypoint.cpp:640-643   if (!gateAFrameTupleMatch(fr))
                                gateAFatalFromInput(FAIL_GENERATION, "x-wrong-generation")
cmdentrypoint.cpp:599-607   gateAFrameTupleMatch reads the SHARED field directly
                            (lorieGateALoadU64Acquire on sessionNonce and generation)
```
There is **no second revalidation**, and none is needed on this side: every arm of the
`switch` at `:644-698` completes synchronously inside the same call. The frame never
outlives its own check. Mismatch is **FATAL**, not a drop — `gateAFatalFromInput`
(`:612`) ends in `lorieGateAFatalHalt`, which is `__attribute__((noreturn))` and
`_exit(127)` (`lorie.h:1414-1418`).

**The one silent-drop arm is `:629-631`.** `lorieGateAActive()` (`InitOutput.c:613-627`)
returns 0 when nonce==0, generation==0, atomics not lock-free, **or
`lorieGateAObserveFatal(p) != 0`**. `lorieActivityConnected()` sets exactly that fatal
at `InitOutput.c:576` and clears it at `:584` via `lorieGateAProtocolInit`
(`lorie.h:505`). So for the duration of the bump, inbound old-generation frames are
**silently discarded instead of fatal**. The record is still released by the caller
(`cmdentrypoint.cpp:1300`), so this is a drop, not a leak.

**Renderer side — one check, against the LATCH:**
```
activity.cpp:273-274   if (!lorieGateABoundTuple(&nonce,&generation)) return;   <- see NOT PROVEN
activity.cpp:278-280   if (... || fr.nonce != nonce || fr.generation != generation)
                           lorieGateAFatalHalt("r-bad-frame", FAIL_PROTOCOL)
```
Confirms Q3: the renderer compares against `gateABound{Nonce,Generation}`
(`activity.cpp:137-139`), never the shared field.

## DEFERRED FRAME PATH (C)

**Snapshot is BY VALUE, not a pointer:**
```
cmdentrypoint.cpp:759-762   shared = lorieGateAShared();
                            if (shared != NULL) {
                                queued->nonce      = load(&shared->sessionNonce);
                                queued->generation = load(&shared->generation);
                            }
```
`struct LorieDeferredLegacyRecord` (`lorie.h:1321-1335`) stores `uint64_t nonce`,
`uint64_t generation` as plain members. No reference to mutable current state.

**Revalidated at replay, on the X main thread:**
```
cmdentrypoint.cpp:799   gateADeferredWorkProc
cmdentrypoint.cpp:801     gateADeferredUnlink(queued)
cmdentrypoint.cpp:802     if (!gateADeferredTupleValid(queued)) {
cmdentrypoint.cpp:803         gateADeferredRelease(queued); return TRUE; }     <- DROP + CLEANUP
cmdentrypoint.cpp:723-733 gateADeferredTupleValid:
                            cancelled || nonce==0 || generation==0 -> return !cancelled
                            else: shared != NULL
                                  && shared->sessionNonce == record->nonce
                                  && shared->generation   == record->generation
                                  && lorieGateAObserveFatal(shared) == 0
```
So the answer to "DROP / FATAL / IGNORE / RETURN / cleanup" is: **DROP with cleanup.**
`gateADeferredRelease` (`:718-721`) = `lorieDeferredLegacyDisposeOwned` + `free`.
Not fatal, not ignored, not replayed.

**Zero-tuple records are treated as VALID** (`:726-727` returns `!cancelled` = 1). That
is the non-Gate-A legacy case, where `lorieGateAShared()` returns NULL
(`InitOutput.c:601-605`) and `:760` never assigns.

### FINDING Q6-F1 — DEFER_ENQUEUE observability defect (PRODUCT, contained)
The R8 observation at `cmdentrypoint.cpp:741-758` prints `queued->nonce` and
`queued->generation` **before they are assigned at `:759-762`**. `calloc` at `:738`
zeroed them, so `DEFER_ENQUEUE` always reports `nonce=0, generation=0`.

Verified against captured evidence, not inferred:
```
evidence/.../runtime-b984ded/r8-d/attempt-04  every DEFER_ENQUEUE: "nonce":0,"generation":0
whole p2-r8-runtime corpus                    570 DEFER_ENQUEUE records, 0 with a nonzero generation
```
Consequence for R9: **the deferred queue's tuple snapshot is not observable in
evidence as the product stands.** An R9 packet cannot prove cross-generation deferred
containment from `DEFER_ENQUEUE`. This is a product-source defect in the same class as
GAP-8 (tooling-visible, product deliberately not rebuilt).

## COMPLETION PATH (F)

**The completion message carries no tuple at all.**
```
renderer.cpp:163-165   lorieEvent e = { .type = EVENT_GPU_COPY_DONE };
                       lorieActivitySendLegacyRecord(&e)
```
It is a doorbell. The X handlers do nothing but re-poll:
```
cmdentrypoint.cpp:1203-1208   case EVENT_GPU_COPY_DONE: ... lorieRecheckGpuCopies(); return 0;
cmdentrypoint.cpp:1010-1015   (legacy path) QueueWorkProc -> lorieRecheckGpuCopies()
```
The actual completion datum is `gpuCopyQueue.completedSerial` in the shared mapping,
release-stored by the renderer only (`lorie.h:591-592`, `:1566`;
`renderer.cpp:1038`, `:2022`, `:2279`, `:2295`).

**No generation check exists anywhere on this path:**
```
xserver.patch:640-653   lorieRecheckGpuCopies(): iterates present_exec_queue and calls
                        present_re_execute(vblank) for every vblank with
                        gpu_copy_pending && (lorieGpuCopyIsDone(serial) || stalled)
InitOutput.c:1921-1929  lorieGpuCopyIsDone(serial) = ObserveCompleted(completedSerial) >= serial
InitOutput.c:1931-1944  lorieGpuCopyAck(): pendingDec + LorieBuffer_release on
                        priv->buffer and dst_buffer. No tuple, no generation.
```
**Containment here is implicit, via serial uniqueness, not via an explicit check.**
`pvfb->gpuCopySerialCounter` is never reset — the only writes are the increments at
`InitOutput.c:1882`, `:2069`, `:3459`, and wrap is fatal
(`InitOutput.c:3459-3460`, `gateAXFatal("x-serial-wrap")`). A serial therefore
identifies exactly one submission for the whole X process lifetime, so a stale
completion cannot alias a new generation's serial.

This answers F as asked: draw suppression is **not** what protects the completion
path. Serial uniqueness is. If any future change resets the serial counter per
generation, this containment disappears silently.

## QUEUE LIFETIME (E)

```
deferred queue (gateADeferredHead/Tail, cmdentrypoint.cpp)
  purged on CLEAN CLOSE       YES  InitOutput.c:3324 lorieGateACancelDeferred(nonce, generation)
  purged on RE-SHARE BUMP     NO   lorieActivityConnected (InitOutput.c:565-594) never calls it
  purged on non-active EOF    YES  cmdentrypoint.cpp:1354 lorieGateACancelDeferred(0, 0)
  otherwise                   drained lazily, one record per WorkProc run, dropped on
                              tuple mismatch at cmdentrypoint.cpp:802-803

gpuCopyQueue (readIndex / writeIndex / completedSerial, shared mapping)
  reset on bump               NO   lorieGateAProtocolInit (lorie.h:503-511) writes only
                                   protocolVersion, generationFatal, sessionNonce,
                                   generation, firstFailedSerial, firstFailureCode,
                                   fatalReason. gpuCopyQueue is a different member of
                                   lorie_shared_server_state and is untouched.
  asserted drained on CLEAN CLOSE  YES InitOutput.c:3309-3313 (readIndex==writeIndex,
                                   completedSerial==last, no firstFailed, no fatal)
  asserted on RE-SHARE BUMP   NO   the bump checks only the REGISTRY
                                   (cmdentrypoint.cpp:389-393, fatal "x-bump-unterminal"
                                   if pendingCount or lastSubmittedSerial nonzero)

gpuCopySerialCounter          never reset; wrap fatal (InitOutput.c:3459-3460)
```

**FINDING Q6-F2 — the bump path has no queue-level assertion.** Clean close proves the
GPU queue drained; the re-share bump does not. It relies entirely on the registry
being terminal. Whether an empty registry implies a drained `gpuCopyQueue` is
**NOT PROVEN** from source: no line establishes that invariant.

## OWNERSHIP / CLEANUP (G)

Deferred record holds (`lorie.h:1321-1335`): a **value copy** of `lorieEvent`, an owned
`void *payload` (malloc'd), an owned `int receivedFd`, and the two `uint64_t` tuple
halves. No raw pointer to a foreign object, no shared_ptr, no AHB ref, no GL id.

```
adopt     lorie.h:1348-1358  takes payload+fd from the decoded record, NULLs the source
          lorie.h:1356-1357  EVENT_SCREEN_SIZE: screenSize.name re-pointed INTO payload
dispose   lorie.h:1337-1347  free(payload); payload=NULL; payloadLen=0;
                             if (receivedFd >= 0) close(receivedFd); receivedFd=-1
          -> IDEMPOTENT: free(NULL) is a no-op and the fd is guarded by >= 0
cancel    cmdentrypoint.cpp:779-796 -> lorie.h:1361-1368 CancelIfMatch:
                             cancelled=1 AND dispose NOW, node left as a tombstone
                             (:777-778 comment: prevents the already-queued WorkProc
                             from dereferencing freed memory)
drop      cmdentrypoint.cpp:718-721 gateADeferredRelease = dispose + free(record)
dispatch  cmdentrypoint.cpp:806-819 moves payload/fd out (queued->payload=NULL,
                             queued->receivedFd=-1), re-points screenSize.name at :818-819,
                             then handleLegacyRecord + lorieRecordRelease + free(queued)
```
Cancel-then-drop calls dispose twice. **That is safe** because dispose is idempotent
(`lorie.h:1339-1346`). No double-free, no double-close.

```
use-after-free      NOT FOUND   tombstone design (:777-778) exists specifically to avoid it
double release      NOT FOUND   dispose is idempotent (lorie.h:1339-1346)
leak                BOUNDED     a dropped record's payload/fd live until its WorkProc
                                runs; the node is freed there (:803). Not process-lifetime.
stale completion    SEE F       contained by serial uniqueness, not by a tuple check
```

## RACE MATRIX (D)

**Thread identity — PROVEN, and it is the decisive fact:**
```
cmdentrypoint.cpp:1519-1526  socketpair(); QueueWorkProc(closure)
cmdentrypoint.cpp:1521         InputThreadRegisterDev(fd, handleLorieEvents, nullptr)
cmdentrypoint.cpp:1522         conn_fd = fd
cmdentrypoint.cpp:1523         lorieActivityConnected()        <- the generation bump
```
The bump runs inside a `QueueWorkProc` closure, i.e. on the **X main thread**. The
record pump `handleLorieEvents` is registered with `InputThreadRegisterDev`, i.e. runs
on the **X input thread**. They are **different threads and share no lock on this
path.** The bump/latch window is therefore NOT closed by thread serialization.

Second decisive fact: each Activity connect allocates a **new socketpair**
(`cmdentrypoint.cpp:1519`) and reassigns `conn_fd` (`:1522`). New-generation traffic
travels a **different fd** from any old-generation bytes still queued on the previous
socket, so in-order delivery gives no cross-generation ordering guarantee either.

| # | scenario | source behavior | line |
|---|---|---|---|
| 1 | old frame arrives BEFORE bump | tuple still matches shared → normal dispatch | `cmdentrypoint.cpp:640`,`:644-698` |
| 2 | old frame arrives AFTER bump, `generationFatal` still set (`:576`→`:584`) | `lorieGateAActive()`==0 → **SILENT DROP** | `cmdentrypoint.cpp:629-631`; `InitOutput.c:576`,`584`; `lorie.h:505` |
| 3 | old frame arrives AFTER bump completes | `gateAFrameTupleMatch` fails → **FATAL** `x-wrong-generation` | `cmdentrypoint.cpp:640-643` |
| 4 | old record already QUEUED (deferred) before bump | snapshot holds old tuple; at replay `gateADeferredTupleValid` fails → **DROP + cleanup** | `:759-762`, `:802-803`, `:723-733` |
| 5 | old record deferred, then bump, then CLEAN CLOSE of the new generation | `lorieGateACancelDeferred(newNonce,newGen)` does **not** match the old record; it is still dropped later by tuple mismatch | `InitOutput.c:3324`; `lorie.h:1361-1364` |
| 6 | new-generation X→R frame reaches renderer BEFORE it latches | `fr.generation != latched` → **FATAL** `r-bad-frame` | `activity.cpp:278-280` |
| 7 | renderer unbound when a Gate A frame is peeked | **FATAL** `r-unbound-frame` | `activity.cpp:462` |
| 8 | old-generation completion doorbell after bump | no tuple; re-polls; serial uniqueness prevents aliasing | `renderer.cpp:164`; `cmdentrypoint.cpp:1207`; `xserver.patch:640-653`; `InitOutput.c:3459-3460` |
| 9 | old socket reaches EOF while Gate A active | **FATAL** `x-hup` / `x-eof` | `cmdentrypoint.cpp:1311-1313`, `:1344-1348` |
| 10 | old socket reaches EOF while Gate A inactive | `closeLorieConnection` + `lorieGateACancelDeferred(0,0)` | `cmdentrypoint.cpp:1351-1354` |

**Every row lands on DROP or FATAL. No row reaches "executed under the new
generation".** Q6's seven sub-questions 1–7 are therefore all answered NO for the
paths the source covers.

## WHAT IS PROVEN

```
P1  Frame tuple = (nonce, generation) + bufferId, 40-byte header, offsets
    static-asserted.                                        lorie.h:787-812
P2  X compares against SHARED; renderer compares against its LATCH. Confirms Q3.
                                        cmdentrypoint.cpp:603-606; activity.cpp:279
P3  X-side frame tuple check happens exactly once, at dispatch, and every switch
    arm completes synchronously, so one check is sufficient for frames.
                                                     cmdentrypoint.cpp:640, 644-698
P4  Deferred records snapshot the tuple BY VALUE and are REVALIDATED at replay.
                                             cmdentrypoint.cpp:759-762, 802, 723-733
P5  Deferred tuple mismatch = DROP WITH CLEANUP, not fatal, not replay.
                                                             cmdentrypoint.cpp:803
P6  Dispose is idempotent; cancel-then-drop is safe.            lorie.h:1339-1346
P7  The bump (X main thread) and the record pump (X input thread) are different
    threads sharing no lock on this path.             cmdentrypoint.cpp:1519-1526
P8  Each connect creates a NEW socket, so new-generation frames do not share
    ordering with old-generation bytes.               cmdentrypoint.cpp:1519, 1522
P9  gpuCopySerialCounter is never reset and wrap is fatal, so serials are unique
    for the X process lifetime.                    InitOutput.c:3459-3460, 1882, 2069
P10 The completion path contains NO generation check at any layer.
                       xserver.patch:640-653; InitOutput.c:1921-1929, 1931-1944
P11 DEFER_ENQUEUE emits the tuple before assigning it: always 0/0.
              cmdentrypoint.cpp:741-758 vs 759-762; 570/570 evidence records confirm
P12 During the bump's fatal window, inbound frames are SILENTLY DROPPED rather
    than fatal.                    cmdentrypoint.cpp:629-631; InitOutput.c:576, 584
```

## WHAT IS NOT PROVEN

```
N1  That row 2 (silent-drop window) is actually REACHABLE. It requires the input
    thread to decode a frame while the main thread is between InitOutput.c:576 and
    :584. Both threads exist and share no lock (P7), so it is structurally
    possible, but no source line establishes that it occurs. NOT PROVEN either way.
N2  That an empty X registry implies a drained gpuCopyQueue at bump time. The bump
    asserts only the registry (cmdentrypoint.cpp:389-393); nothing asserts the
    queue. NOT PROVEN.
N3  conn_fd is `volatile int`, not atomic (cmdentrypoint.cpp:44), and is written by
    the main thread at :1522 while the input thread reads it at :1248, :1281, :1317.
    Whether this is free of a torn/stale read is NOT PROVEN from source.
N4  Whether any old-generation bytes can still be buffered in the OLD socket at the
    moment the new generation begins. Depends on peer close ordering, which is not
    in this tree. NOT PROVEN.
N5  present_exec_queue contents across a generation boundary. present_scmd.c is not
    in this tree beyond the patch hunk; only lorieRecheckGpuCopies' body is visible
    (xserver.patch:640-653). Whether a vblank can survive a generation transition
    is NOT PROVEN here.
```

## R9 TEST IMPLICATION

```
1  R9 must PROVE the halts, not defend against them. Rows 3, 6, 7, 9 are all
   FATAL paths; the packets that cover them are halt-observation packets.
2  Row 4 is the only DROP path with a tuple, and P11 means it is currently
   UNOBSERVABLE. Either the product emits the tuple correctly at DEFER_ENQUEUE, or
   R9 must prove deferred containment some other way. This is a blocking
   observability question for any R9-DEFER packet.
3  Row 2 (N1) needs a packet that can hold the main thread between
   InitOutput.c:576 and :584. No existing test fault does this
   (LORIE_GATEA_TEST_WRONG_GENERATION_FRAME at cmdentrypoint.cpp:634 fires the
   fatal, it does not open the window).
4  N2 means an R9 bump packet must record gpuCopyQueue readIndex/writeIndex/
   completedSerial explicitly at the boundary; the product asserts nothing there.
5  P9 is load-bearing and invisible. Any R9 change that resets the serial counter
   per generation silently removes the completion path's only containment.
```

## Q3 / Q5 CROSS-CHECK

```
CONTRADICTION_FOUND: none.
```
Q6 confirms Q3's central claim (renderer admits against its latch, not the shared
field — `activity.cpp:279`) and confirms that the frame path has containment of the
same strength Q5 found for READY imports: FATAL on mismatch
(`activity.cpp:280`, `cmdentrypoint.cpp:642`) rather than silent acceptance.

Two **refinements** to Q3, neither contradicting it:
```
R-A  Q3 described the danger window as InitOutput.c:586 -> activity.cpp:209-211.
     Q6 adds the reason it is a genuine window: the bump runs on the X MAIN thread
     and the record pump on the X INPUT thread (cmdentrypoint.cpp:1519-1526), and
     each connect uses a NEW socket (:1519, :1522). Thread separation, not message
     ordering, is what makes it real.
R-B  Q3 recorded that generationFatal is cleared by the bump (lorie.h:505). Q6 adds
     the operational consequence: while it is SET, lorieGateAActive() is false, so
     inbound frames are silently dropped instead of fatal
     (cmdentrypoint.cpp:629-631). Reachability is NOT PROVEN (N1).
```
A pointer to these refinements has been added to `Q3-generation-nonce-lifecycle.md`.
No Q3 or Q5 claim was withdrawn.

## FINAL VERDICT

```
FRAME_TUPLE_REVALIDATED_SAFE      X frame path: one check, synchronous dispatch,
                                  fatal on mismatch.        cmdentrypoint.cpp:640-643
STALE_FRAME_DROPPED_ON_REPLAY     deferred path: by-value snapshot, revalidated,
                                  dropped with cleanup.     cmdentrypoint.cpp:802-803
STALE_FRAME_FATAL_CONTAINMENT     renderer frame path and both EOF paths halt.
                                  activity.cpp:280, 462; cmdentrypoint.cpp:1311, 1344
QUEUE_LIFETIME_GAP                the re-share bump asserts the registry but NOT the
                                  gpuCopyQueue, and never purges the deferred queue.
                                  InitOutput.c:565-594; cmdentrypoint.cpp:389-393  (N2)
COMPLETION_CROSS_GENERATION_GAP   no generation check exists on the completion path;
                                  containment is implicit in serial uniqueness alone.
                                  xserver.patch:640-653; InitOutput.c:1921-1944, 3459-3460
```
`DESIGN_REQUIRED` is **not** raised: every traced path terminates in DROP or FATAL,
and the two gaps are recorded, bounded, and testable. They are inputs to R9 packet
design, not blockers on the design freeze.

## STILL OPEN
```
Q1 Q2 Q4 Q9 Q10 Q11 — §8.1 still forbids running R9 off PR #7's design.
```
