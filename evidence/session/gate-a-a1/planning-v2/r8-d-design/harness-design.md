# V2-R8-D-HARNESS-DESIGN

DATE 2026-09-21  DEPENDS ON V2-R8-D-SRC-TRACE (SEAM IDENTIFIED)
VERDICT **CONSTRUCTIBLE WITH EXISTING HARNESS — no new tooling, no fixture change**

## Construction steps (each step maps to a source-grounded guarantee)
| # | step | why it is deterministic |
|---|---|---|
| 1 | connect a second client `pc` | isolates Present traffic from the retiring client `c`, so the retirement wait cannot starve its own trigger |
| 2 | `pair_create` + `pair_composite` on `c` | forces Gate A registration of the pair buffers (`gateAEnsureReady`, InitOutput.c:2825) |
| 3 | issue 4 `present_pixmap(ASYNC\|COPY)` on `pc`, then `xcb_flush(pc)` | the presents are on the wire before retirement begins |
| 4 | free the source picture+pixmap on `c`, `xcb_flush(c)` | enters `gateARetireBufferId` -> `gateAWaitTerminal` -> `gateAWaitCleanAck(..., LEGACY_DEFER)` |
| 5 | continue issuing the remaining presents | completions land while policy == DEFER -> DEFER_ENQUEUE + X_WAKE_RECEIVED |
| 6 | free the destination picture+pixmap | second retirement, second overlap window |
| 7 | drain 8 events on `pc` | ensures the client observes completion/cancel, no dangling replies |

Steps 1-7 are already implemented verbatim in `cell_d()`. This design packet records
WHY each line is there so the construction is reproducible and auditable rather than
incidental.

## Observation contract to expect
```
r : R_WAKE_SENT           cause="fence_completed", send_ok=true
x : X_WAKE_RECEIVED
x : DEFER_ENQUEUE         local_id, type
x : DEFER_DISPATCH        local_id  (subset of enqueued ids, no duplicates)
x : RECHECK               site="handleLegacyRecord"
```

## Acceptance mapping (judge_d)
```
defer_not_constructed / wakeup_origin / connection_binding -> INVALID
reentrant_recheck / duplicate_dispatch / stale_deferred /
present_notification_lost                                  -> FAIL
dispatched ids must be a subset of enqueued ids            -> STALE_DEFERRED_DISPATCH
```

## Stop condition
If DEFER_ENQUEUE or DEFER_DISPATCH is absent, classify `INVALID_CONSTRUCTION`
(§7.8) and STOP. Do NOT add a sleep, do NOT retry, do NOT relax the judge.
