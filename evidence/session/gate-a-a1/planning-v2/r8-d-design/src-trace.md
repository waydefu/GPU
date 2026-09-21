# V2-R8-D-SRC-TRACE

DATE 2026-09-21  MODE host-only, read-only, no attempt consumed
PRODUCT b984ded  VERDICT **SEAM IDENTIFIED — construction is deterministic**

§7.8 requires five source-grounded answers. No speculation below; every claim cites a line.

## Q1 — which event producer triggers the deferred path
`EVENT_GPU_COPY_DONE`, produced by the renderer when a Present GPU copy fence
completes. Renderer side emits `R_WAKE_SENT` (`lorie_r8_obs.c:231/242`) with
`cause="fence_completed"`. The X side receives it in the record pump
(`cmdentrypoint.cpp:1281` `lorieRecordDecoderNext`).

## Q2 — which thread owns the producer
Two distinct owners, which is why this is a real overlap and not a self-race:
```
renderer thread   sends the wake                (R_WAKE_SENT)
X server main thread  runs the record pump, the Gate A waiter, and later the
                      WorkQueue drain           (X_WAKE_RECEIVED / DEFER_*)
```
`lorieR8WakeReceived(0)` fires from the X side at `cmdentrypoint.cpp:757`,
immediately after the record is queued.

## Q3 — which queue carries the event
The X server's own **WorkQueue**, not a Gate A queue:
`cmdentrypoint.cpp:766` `QueueWorkProc(gateADeferredWorkProc, NULL, queued)`.
A parallel intrusive list (`gateADeferredHead/Tail`) tracks the same records for
cancellation. Consequence: a record still queued at teardown is destroyed by
`ClearWorkQueue()` in `dix/main.c` (see V2-P007 terminal sequence), which is why the
dispatch side must be observed, not assumed.

## Q4 — exact schedule seam (which line, between which two states)
```
InitOutput.c:3278   gateAWaitCleanAck(waiter, "x-unregister-wait",
                        LORIE_GATEA_FAIL_UNREGISTER, LORIE_GATEA_LEGACY_DEFER)
```
inside `gateARetireBufferId()`. For the duration of that wait the pump's
`legacyPolicy == LORIE_GATEA_LEGACY_DEFER`, so `cmdentrypoint.cpp:1288` routes every
arriving legacy record to `gateAQueueDeferredRecord()` instead of handling it inline.
The seam is therefore between these two states of the SAME X main thread:

```
STATE-1  blocked in gateAWaitCleanAck        (retirement in flight, policy = DEFER)
           |  a GPU_COPY_DONE arriving here is ENQUEUED, not handled
           |  cmdentrypoint.cpp:735 gateAQueueDeferredRecord
           |     :753 DEFER_ENQUEUE        :757 lorieR8WakeReceived -> X_WAKE_RECEIVED
           |     :766 QueueWorkProc
           v
STATE-2  wait returned, DIX ProcessWorkQueue runs gateADeferredWorkProc
           :802 gateADeferredTupleValid   <-- the race gate: nonce + generation +
                                              lorieGateAObserveFatal must still hold
           :820 DEFER_DISPATCH  -> handleLegacyRecord -> :1205 RECHECK
```
`gateADeferredTupleValid` (`:723-733`) is where retirement and completion actually
contend: if the retirement advanced the generation or raised fatal while the record
sat in the queue, the record is silently released and never dispatched.

## Q5 — how to make them meet deterministically (no sleep, no retry, no fake event)
Determinism comes from two blocking guarantees in the retirement path itself, not
from timing:
```
InitOutput.c:3261  gateAWaitTerminal(meta.lastSubmittedSerial)   — retirement of a
                   buffer with in-flight GPU work MUST wait for that work
InitOutput.c:3278  gateAWaitCleanAck(...)                        — and MUST then wait
                   for the renderer's unregister ack
```
So: submit Present work, then retire a registered buffer. The retirement cannot
complete before the renderer has processed the outstanding work, therefore the
completion wake necessarily lands inside the wait window. No arbitrary sleep,
no retry-until-hit, no injected event — the product's own ordering constraints
create the overlap.

## Existing fixture already implements this
`tests/r8/p_r8_lifecycle.c cell_d()`:
```
open a SECOND connection pc                     (separate client, separate requests)
pair_create + pair_composite on c               -> Gate A registers the pair buffers
8x xcb_present_pixmap(pc, ASYNC|COPY)           -> 8 GPU copies in flight
  at i == 3: xcb_flush(pc)                      -> the 4 presents are on the wire
             free_picture(c, g.src) + free_pixmap(c, g.src_pm) + flush(c)
                                                -> RETIREMENT starts here, mid-flight
after the loop: free g.dst as well              -> a second retirement
drain 8 events from pc
```
The `i == 3` flush-then-free is the construction: it guarantees Present work is
outstanding at the moment retirement begins. `cell_d` needs no modification.

## Forbidden constructions (§7.8) — none used
```
arbitrary sleep            NOT USED  (ordering comes from gateAWaitTerminal/CleanAck)
retry-until-hit            NOT USED  (single deterministic pass)
fake event                 NOT USED  (EVENT_GPU_COPY_DONE is produced by the renderer)
renderer delay for timing  NOT USED
manual log injection       NOT USED
```

## Classification reminder carried into the packet
Per §7.8: overlap not formed -> `INVALID_CONSTRUCTION`, **never** FAIL. Absence of
DEFER_ENQUEUE/DISPATCH means we failed to build the state, not that the product is
broken.
