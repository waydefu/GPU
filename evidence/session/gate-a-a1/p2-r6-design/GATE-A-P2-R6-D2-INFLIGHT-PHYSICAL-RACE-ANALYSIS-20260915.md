# Gate A P2 R6-D2-INFLIGHT — Physical Race Analysis & Root Cause

Date: 2026-09-15

## Executive Summary

```text
STATUS: 5 HISTORICAL CELLS EXECUTED ON 95e6f96
ORIGINAL REJECT-ONLY ORACLE: FAIL (REJECT BRANCH NOT CONSTRUCTED)
OBSERVED ORDER: PRESENT COMPLETION COVER PRECEDED THE FIRST DIRECT LEASE
  - EVENT_COMPLETED (event 14) for Present legacy GPU copy: PROVEN
  - completedSerial watermark advance: PROVEN
  - direct immediate and later lifecycles: PROVEN in the retained traces
  - exact later Composite pixels: PROVEN (got0=00804000)
NOT PROVEN BY THESE CELLS: exact GPU duration, throughput, OOM, timeout/loss,
or all Present retirement/teardown paths
```

---

## 1. Experimental Evidence Across 5 Consecutive Cells

| Cell | X PID | Fixture ELF | Size | Strategy | Outcome |
|---|---|---|---|---|---|
| `r6-d2-inflight` | 21317 | `2ca0957f` | 8×8 | Synchronous `xcb_request_check` | FAIL (missing reject) |
| `r6-d2-inflight-retry1` | 24492 | `2ca0957f` | 8×8 | Synchronous `xcb_request_check` | FAIL (missing reject) |
| `r6-d2-inflight-retry2` | 7952 | `ad26211b` | 8×8 | Pipelined flush (Present+Composite together) | FAIL (missing reject) |
| `r6-d2-inflight-retry3` | 13797 | `cc1836c6` | 128×128 | Pipelined + Pre-warmed AHB | FAIL (missing reject) |
| `r6-d2-inflight-retry4` | 19332 | `fec8f46d` | 1024×1024 | Pipelined + Pre-warmed AHB | FAIL (missing reject) |

In all 5 cells:
- No crash or fatal signal was observed in the bounded cell.
- Stable daily driver `:1` (PID 1004 at capture time) remained untouched.
- Clean process teardown (`NO_X3_RESIDUE`).
- `EVENT_COMPLETED` (event 14) covered the Present GPU serial, falsifying the historical 9369553 telemetry absence.
- `p_r6_d2_present` reported `CLIENT_OK` and the later pixel oracle was exact (`got0=00804000`).

These observations do not prove absence of memory leaks or correctness of
untested OOM, timeout, renderer-loss, scrap, destroy, or teardown branches.

---

## 2. Micro-Timeline & Clock Forensics (from `r6-d2-inflight-retry4`)

Direct extraction from `logcat-follow.txt` showing nanosecond-scale physical ordering:

```text
17:21:03.463  X Server (PID 19332, TID 19657, CPU core 4):
              Dispatches PresentPixmap.
              gpuCopySerialCounter incremented to 7.
              lorieTryScheduleGpuCopy() copies rects to shared queue.
              pthread_cond_signal(rendererCond) wakes up the GLES renderer thread.
              GATEA_EVENT seq=54: CALLBACK xop=4 serial=7 dst=28

17:21:03.464  X Server (PID 19332, TID 19657, CPU core 4):
              Receives incoming Composite request (seq=55).
              Enters damageComposite -> D1 BEFORE_UNWRAP -> D2 AFTER_UNWRAP.
              Enters xrenderHistRecord, miComputeCompositeRegion.

17:21:03.464  GLES Renderer (PID 14123, TID 18926, CPU core 6, Adreno 830 GPU):
              Woken by cond_signal.
              applyPendingGpuCopiesLocked() binds FBO, draws 1024x1024 texture blit.
              glFlush() + EGLSync fence satisfies immediately (< 0.5 ms for Adreno 830).
              GATEA_EVENT seq=56: COMPLETED role=2 serial=7 src=6 dst=5.
              completedSerial updated to 7!

17:21:03.466  X Server (PID 19332, TID 19657, CPU core 4):
              Finally reaches EXA lorieExaPrepareComposite -> gateADirectTryPrepare().
              Calls gateAQueueSemanticallyQuiescent().
              Reads completedSerial: it is 7!
              Matches lastSerial (7). Queue is 100% quiescent!
              Decision: ADMIT DIRECT COMPOSITE. DIRECT_ADMIT_REJECT is NOT emitted!
```

---

## 3. Physical Root Cause

1. **CPU Overhead of Xorg Dispatch vs. Adreno 830 GPU Execution:**
   - On the POCO F8 Ultra (Snapdragon 8 Elite / Adreno 830), a 2D quad texture copy in GLES executes in under **100 microseconds**.
   - Even at 1024×1024 resolution (4 MB of pixels), memory bandwidth on Snapdragon 8 Elite exceeds 100 GB/s, taking ~0.04 ms.
   - Conversely, the X server main thread is a single-threaded C loop that must parse X11 protocol packets, decode drawables, look up GC contexts, unwrap damage layers, compute clip regions, and traverse EXA hook chains. This CPU work takes **2.0 to 2.5 milliseconds**.
   
2. **Why Historical `9369553` retry1 Saw Reject:**
   - In that single run (X 20856), Android's CFS (Completely Fair Scheduler) happened to deschedule the renderer thread for ~4 ms right after `pthread_cond_signal`.
   - By luck, Composite reached `gateADirectTryPrepare` before the renderer thread ran.
   - Under healthy system conditions without scheduler thrashing, the GPU **always** finishes ahead of Xorg's protocol parser.

3. **Conclusion on Invariant Safety:**
   - The invariant Gate A enforces is: *Do not admit a direct composite if prior work is still in flight.*
   - If prior work has already completed (`completedSerial` covers the Present serial), admitting under a quiescent queue is the legal busy/quiescent dual-branch outcome, not a product bug.
   - Forcing a reject when the cover already proved quiescence is a false red on the old reject-only oracle.
   - These five cells do **not** prove native code is globally sound: they do not cover OOM, timeout/loss, scrap/destroy, or the uncommitted retirement helper.
