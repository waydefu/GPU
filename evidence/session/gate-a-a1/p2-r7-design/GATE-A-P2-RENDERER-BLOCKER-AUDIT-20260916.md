# Gate A P2 renderer-thread blocking audit — 2026-09-16

READ-ONLY source + evidence. HEAD `27d8d1b4fcfc5456bac8720d36110eeeb7cbc9d3`
(`src/f8-ahb-gatea-stall-diag`). No patch / build / install / rerun / B-2 / R7.
Timeout remains 2000 ms.

```
RCA VERDICT: RENDERER BLOCKER NARROWED BUT NOT PROVEN
```

## Binding

- Frozen R6 `0f1e546` PASS (historical).
- Repair `0d72332` fail-stop PROVEN (serial 2370 / 1810).
- stall-obs-01 on `27d8d1b`: STALL_NOT_OBSERVED; SWAP max 1.468 ms; NEXT_FENCE max 4.806 ms.

## Loop (threadLoop)

`renderer.cpp` 2319–2395, `shouldWait` 2283–2317, `redrawLocked` 1983–2281.

```
lock stateLock
  while shouldWait():   # gpuCopyPending → do not wait
      cond_wait(stateCond, stateLock)   # infinite
  maybe refreshContext / attachToGL     # stateLock held
  signal stateChangeFinishCond
unlock stateLock
  if surface && !waitForNextFrame && (draw|cursor|gpuCopy):
      redrawLocked   # may apply copies; then SWAP + NEXT_FENCE
  else if gpuCopyPending:
      applyPendingGpuCopies
  release removed buffers
lock stateLock → loop
```

`waitForNextFrame` is set in `redrawLocked` then cleared on the **X** thread by
`lorieRedraw` (`InitOutput.c` 920–928), queued from AChoreographer
(`cmdentrypoint.cpp` 531–533 → `InitOutput.c` 1390–1395). While X is inside
`lorieGpuCopyWait` (`usleep(200)` poll, no event pump), that clear/signal is
deferred. `gpuCopyPending` still forces `shouldWait` false, so a visible queued
S must take the standalone apply path unless the GL thread never returns to
`shouldWait`.

X `pthread_cond_signal(rendererCond)` after `writeIndex` publish does **not**
hold `stateLock`. Lost wakeup is source-possible in the window
`shouldWait==true` → `cond_wait`.

## Rank

| Rank | Candidate | Evidence for | Evidence against | Confidence |
|---|---|---|---|---|
| 1 | `eglSwapBuffers(sfc)` BufferQueue/SF | fail cells producer hold ~2081–2286 ms; call has no timeout; sits after S-1 complete, before next apply | stall-obs-01 SWAP max 1.468 ms | MEDIUM |
| 2 | next-buffer `eglClientWaitSync(..., EGL_FOREVER)` | unbounded; same interval | obs-01 max 4.806 ms | LOW–MEDIUM |
| 3 | `notifyGpuCopyDone` → blocking `write(conn_fd)` while X is in GpuCopyWait | blocking write; unmarked; X does not read socket during wait | one small event; no 2 s proof | LOW |
| 4 | `cond_wait` lost-wakeup + X not pumping Choreographer | mutex not shared; infinite wait | `gpuCopyPending` predicate; tiny race | LOW |
| 5 | redraw completion `ClientWaitSync` holding `state->lock` | unbounded on legacy | prior RCA S-1 GPU ~1 ms | LOW |

`state->lock` is **not** held across SWAP/NEXT_FENCE. No proven mutex deadlock
with X's `lorieGpuCopyWait` (that wait takes no `state->lock`). `setWindow`
can wait on renderer while renderer is in SWAP (lifecycle), not the B-2
steady path.

## Next action (not executed)

One observe-only pair: `COND_WAIT_ENTER` / `COND_WAIT_EXIT` around
`pthread_cond_wait` in `threadLoop`, logging `mono_ns`, `gpuCopyPending`,
`waitForNextFrame`, `waitingForBuffers`, `readIndex`, `writeIndex`. Log only
on actual waits. Do not add per-frame SWAP spam. Do not retry blind stress1000.
Do not change 2000 ms.
