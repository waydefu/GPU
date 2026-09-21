# R8-P1 / R8-P2 — INVALID_CONSTRUCTION, precondition never occurs

DATE 2026-09-21   CLASSIFIER **INVALID_CONSTRUCTION** (§7.8 rule, inherited by §7.9/§7.10)
NOT a product FAIL. No product defect is claimed here.

## Observed
```
R8-P1 attempt-01  R8_INVALID GPU_OWNED_NOT_CONSTRUCTED   (rc=2, attempt consumed)
R8-P2             not run — same precondition, would fail identically
```
The runner armed the fault correctly:
`TERMUX_X11_GATEA_TEST_FAULT=destroy-while-gpu-owned` + `TERMUX_X11_GATEA_TEST_ARM=1`
(run-r8-one-cell L289-295). The fixture completed (`P CLIENT_DONE`). What is missing
is the STATE the fault is supposed to fire in.

## Precondition chain (source-traced, b984ded)
`judge_p1` / `judge_p2` both require `EVENT_LEASE_GPU_OWNED` (enum 5).
It is emitted at exactly one site:
```
InitOutput.c:3416   gateAPair.state = GATEA_PAIR_GPU_OWNED;
InitOutput.c:3419   lorieGateATrace(..., LORIE_GATEA_EVENT_LEASE_GPU_OWNED, ...)
```
reachable only from the publish path, which first requires
```
InitOutput.c:3361   gateAPair.state == GATEA_PAIR_RESERVED
```
and RESERVED is set only at
```
InitOutput.c:3132   gateAPair.state = GATEA_PAIR_RESERVED;
```
after `gateAQueueSemanticallyQuiescent()`, queue capacity, and
`gateAEnsureReady(src)` + `gateAEnsureReady(dst)` all succeed — i.e. only from the
**Gate A direct EXA composite** path.

## Measured: that path is never entered, in ANY cell
```
event=5  (LEASE_GPU_OWNED)      0 occurrences in r8-p1 ring / raw-logcat / summary
event=5                          0 occurrences in r8-c1 attempt-11 and r8-c4 attempt-01
event=32 (DIRECT_ADMIT_REJECT)   0 occurrences
```
Zero rejects with zero leases means the direct composite path is not being
**refused** — it is not being **attempted**. GPU work itself is clearly happening
(`event=14 COMPLETED_SERIAL` x4, `R_WAKE_SENT cause="fence_completed"`,
DEFER_ENQUEUE/DISPATCH), so the renderer and copy queue are live; it is specifically
the EXA pair-lease composite that never engages under this run configuration.

## Why this is INVALID_CONSTRUCTION and not FAIL
§7.8: "overlap 未形成 → INVALID_CONSTRUCTION（不是 FAIL）". §7.9 additionally requires
"GPU_OWNED proven（不是假設，是證明）" and states the cell is a *synthetic containment
proof*. We cannot prove containment of a state we never entered. Reporting FAIL here
would be §19.1's first named misclassification — blaming the product for a state the
harness did not build.

## What closing this needs (NOT attempted here)
A `V2-R8-P-SRC-TRACE` equivalent to `V2-R8-D-SRC-TRACE`, answering:
```
which XRender composite shapes route to the Gate A direct EXA path at all
what the fixture's pair_composite must change to be admitted
whether :3 software-mode X on this device can ever reserve a pair, or whether
  the lease path requires a configuration R8 has never run under
```
Until that exists, P1/P2 are `DESIGN_REQUIRED`. Running more attempts cannot
resolve it: the precondition is structural, not timing.

## Attempt accounting
R8-P1 attempt-01 is CONSUMED and frozen as INVALID. R8-P2 was not started.
