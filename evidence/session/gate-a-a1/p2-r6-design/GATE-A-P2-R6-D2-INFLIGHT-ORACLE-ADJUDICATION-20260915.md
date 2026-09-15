# Gate A P2 R6-D2-INFLIGHT — oracle adjudication

Date: 2026-09-15 22:00 UTC+8

```text
HISTORICAL CELLS: IMMUTABLE
OLD ORACLE (reject-only): FAIL on all five runtime-95e6f96 D2-INFLIGHT cells
NEW HOST JUDGE: dual-branch busy-reject / quiescent-admit
HOST REPLAY: five cells take quiescent (test_current_95e6f96_cells_take_quiescent_branch OK)
DEVICE RERUN: NOT AUTHORIZED / NOT DONE
```

Do not overwrite `evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-95e6f96/r6-d2-inflight*`.
Do not silent-retry those cells. Do not call that replay an R6-D2 PASS.

## Historical cells (kept FAIL)

| Cell | X PID | Size | Old oracle |
|---|---|---|---|
| `r6-d2-inflight` | 21317 | 8×8 | FAIL missing reject |
| `r6-d2-inflight-retry1` | 24492 | 8×8 | FAIL missing reject |
| `r6-d2-inflight-retry2` | 7952 | 8×8 | FAIL missing reject |
| `r6-d2-inflight-retry3` | 13797 | 128×128 | FAIL missing reject |
| `r6-d2-inflight-retry4` | 19332 | 1024×1024 | FAIL missing reject |

Proven in those traces: Present CALLBACK, renderer COMPLETED covering S,
later exact pixels `00804000`, no Stable touch, `NO_X3_RESIDUE`.
Not proven: OOM, timeout/loss, retirement helper, teardown.

## Why reject-only was false-red

`LEASE_RESERVED` is emitted with **serial=0** before serial assignment.
`completedSerial` is a watermark `T>=S`. On this SoC the GPU copy often
finishes before X reaches `gateADirectTryPrepare()`, so the queue is
already quiescent and admit is legal. Binding cover src/dst to Present S
is also wrong when `T>S`.

## New host oracle (already in judge-r6-design.py)

Busy-reject: immediate Composite pair, reason-1 reject before cover, no
target lease/publish/success before cover, then later Composite pair and
direct lifecycle with `LEASE serial=0`.

Quiescent-admit: cover before first target lease; lease serial=0; immediate
lifecycle must finish before the next Composite REQUEST; later pair is a
second transaction.

OOM: no event 32; 33/34 after cover; later SUCCESS after later callback.

Event 32 still fails. Historical `9369553` D1 PASS and D2 retry1 FAIL remain.

## What a planner must not do

Treat host replay of old traces as device qualification of the retirement C.
The retirement APK does not exist yet. The next D2 cell needs a new grant,
new artifact, new `runtime-<sha>/` directory.
