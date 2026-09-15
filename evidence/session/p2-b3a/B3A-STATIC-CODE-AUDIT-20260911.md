# B3a Static Code Audit — 2026-09-11

## Scope

- Read-only static audit only; no source patch, commit, PR, APK install, process control, or device operation.
- Experimental path: `com.waydefu.x11gpu` / `DISPLAY=:3`.
- Stable `com.termux.x11` / `DISPLAY=:1` untouched.
- Worktree: `/root/projects/GPU加速/src/f8-ahb`.
- HEAD: `98224356e40913dcf2188d18748eba9401639850`.
- Existing dirty worktree retained. The audited renderer/buffer/InitOutput/activity/cmdentrypoint/EGL-dispatch/telemetry source blobs match runtime artifact source `1954f82cda9b548ab88f420e428f7296a2d3c72c`.
- `git diff --check`: PASS.

## Verdict

```text
B3a STATIC CODE AUDIT: HIGH-RISK FINDINGS
Historical batch16 startup SIGSEGV: observed / non-reproduced
Root cause: UNKNOWN
Renderer source modified by audit: NO
Stable: UNTOUCHED
```

## Top crash candidates

### C1 — Fence PFN calls are not capability-gated

- **Severity:** HIGH
- **Confidence:** HIGH
- **Files/functions:** `lorie/renderer.cpp::Renderer::applyPendingGpuCopies`, `Renderer::redrawLocked`; `lorie/egl_dispatch.c::lorieEglDispatchInit`; `lorie/InitOutput.c::lorieTryScheduleGpuBlit`, `lorieTryScheduleGpuSolid`, `lorieCanAccelComposite`.
- **Exact evidence:** `egl_dispatch.c:68-74` may leave fence PFNs NULL and set `hasFence=false`. `renderer.cpp:938-944`, `1091-1112`, and `1130-1132` call the PFNs without checking `lorieEglHasFence()` or the pointer. `InitOutput.c:490-493` only disables Present GPU offload; Solid `:1674` and Composite `:2004` remain eligible.
- **Failure mode:** NULL indirect call can SIGSEGV. An `EGL_NO_SYNC` result is also passed to wait/destroy.
- **Trigger hypothesis:** Missing `EGL_KHR_fence_sync`, transient `eglGetProcAddress()` failure, or incomplete EGL initialization followed by EXA Solid/Composite.
- **How to prove/disprove:** Use an EGL test shim or injected capability failure, then run Solid/Composite and record PFN addresses, capability result, fence handle, and create/wait/destroy return values.

### C2 — X shared-state `mmap()` failure checks NULL instead of `MAP_FAILED`

- **Severity:** HIGH
- **Confidence:** HIGH
- **File/function:** `lorie/InitOutput.c::OsVendorInit`.
- **Exact evidence:** `InitOutput.c:435-440` tests `if (!(lorieScreen.state = mmap(...)))`; `mmap()` failure is `MAP_FAILED`, not NULL, and is then passed to `memset()`.
- **Failure mode:** Write through `(void *)-1`, producing SIGSEGV and leaving invalid global state.
- **Trigger hypothesis:** Shared-state mapping failure from resource exhaustion, invalid FD, or address-space failure.
- **How to prove/disprove:** Fault-inject `mmap()` to return `MAP_FAILED`; execution must stop before `memset()`.

### C3 — Receive failure reuses a stale `LorieBuffer*`

- **Severity:** HIGH
- **Confidence:** HIGH
- **Files/functions:** `lorie/buffer.c::LorieBuffer_recvHandleFromUnixSocket`; `lorie/activity.cpp::xcallback(EVENT_ADD_BUFFER)`.
- **Exact evidence:** `activity.cpp:212` uses static `LorieBuffer *buffer`. `buffer.c:494` ignores short/failed struct reads. On receiver allocation failure, `buffer.c:529-530` assigns `outBuffer = NULL` instead of `*outBuffer = NULL`. The caller still logs and calls `g_renderer.addBuffer(buffer)` at `activity.cpp:214-218`.
- **Failure mode:** Previous buffer may already be released; list operations or renderer attachment then use freed memory. If an AHB receive fails, the copied cross-process `desc.buffer` pointer is not explicitly invalidated before use.
- **Trigger hypothesis:** Short socket frame, connection teardown, AHB/FD receive failure, or receiver allocation failure.
- **How to prove/disprove:** Socketpair harness with short/closed frames plus allocation fault injection; verify the caller pointer becomes NULL and run with ASan/list poisoning.

## Top lifecycle risks

### L1 — Shared mutex recovery treats connection loss as owner death

- **Severity:** HIGH
- **Confidence:** HIGH
- **File/function:** `lorie/lorie.h::lorie_mutex_lock`.
- **Exact evidence:** `lorie.h:69-81` reinitializes the process-shared mutex after timeout whenever `lorieConnectionAlive()` is false, without proving `lockingPid` has exited. `lorie.h:82-85` treats every non-`ETIMEDOUT` return as success.
- **Failure mode:** X and renderer can both believe they own `state->lock`; AHB CPU access and GPU draw/release lose mutual exclusion, causing data races and possible SIGBUS/UAF-like teardown corruption.
- **Trigger hypothesis:** Socket HUP or intentional disconnect while the renderer still holds the lock during fence/queue drain.
- **How to prove/disprove:** At each reinitialization log `lockingPid`, actual PID liveness, queue serial, and current phase; close the connection during a fence and verify whether reinitialization occurs while the owner remains alive.

### L2 — CloseScreen destroys X resources before stopping the renderer consumer

- **Severity:** HIGH
- **Confidence:** HIGH for the lifecycle gap; MEDIUM for a specific crash manifestation.
- **Files/functions:** `lorie/InitOutput.c::lorieCloseScreen`; `lorie/renderer.cpp::Renderer::threadLoop`; `lorie/activity.cpp::xcallback`.
- **Exact evidence:** `InitOutput.c:1078-1094` dumps, sets `pScreenPtr=NULL`, destroys the root pixmap, and calls the lower CloseScreen without stopping/draining the renderer. Renderer `threadLoop()` is an unconditional loop at `renderer.cpp:1171-1235`. `setSharedState(NULL)` only comes from activity connection teardown at `activity.cpp:151-160` or `:238-244`. A queued redraw can enter `lorieRedraw:782-820` after CloseScreen, and `lorieFramecounter:1015-1060` has no local cancellation here.
- **Failure mode:** Old shared state, buffer, damage, or queued work can be used after screen teardown; recreate can mix old and new screen state.
- **Trigger hypothesis:** Server-generation reset, disconnect/reconnect timing, or pending renderer work during CloseScreen.
- **How to prove/disprove:** Add generation/state-map logging at CloseScreen, state-null, dequeue, draw, and release; a post-CloseScreen use of the old generation proves the ordering defect.

### L3 — AHB/EXA completion errors do not fail closed

#### L3a — AHB lock failure poisons lock state

- **Severity:** HIGH
- **Confidence:** HIGH
- **Files/functions:** `lorie/buffer.c::LorieBuffer_lock`; `lorie/InitOutput.c::loriePrepareAccess`.
- **Exact evidence:** `buffer.c:426` stores the AHB lock result, but `buffer.c:433-436` still sets `buffer->locked=1`. `InitOutput.c:2393-2400` takes `state->lock`, then returns on lock failure without unlocking it.
- **Failure mode:** Buffer remains logically locked after a failed AHB lock; shared mutex can remain held, causing later EEXIST/deadlock/teardown failure.
- **Trigger hypothesis:** AHB lock failure while a GPU copy is marked pending.
- **How to prove/disprove:** Force an AHB lock error and inspect `buffer->locked`, `lockedData`, `state->lockingPid`, and the next CPU access.

#### L3b — DoneComposite releases ownership after an incomplete wait

- **Severity:** HIGH
- **Confidence:** MEDIUM-HIGH
- **Files/functions:** `lorie/InitOutput.c::lorieExaDoneComposite`, `lorieGpuCopyWait`; `lorie/renderer.cpp::Renderer::threadLoop`.
- **Exact evidence:** `InitOutput.c:2247-2277` logs but ignores a false `lorieGpuCopyWait()` result, then repairs and releases pending refs. `renderer.cpp:1223-1228` still drains pending GPU copies when `surfaceAvailable` is false.
- **Failure mode:** X may clear pending ownership and allow CPU access while renderer later consumes the same queue entry/AHB.
- **Trigger hypothesis:** Surface background, connection teardown, or 2-second wait timeout.
- **How to prove/disprove:** Force `surfaceAvailable=false` with a queued serial; compare release/pending timestamps to renderer dequeue and completion timestamps.

## Question answers

- **Q1 NULL path:** YES. C1, C2, C3, and unchecked `pvfb->state`/AHB receive paths are real conditional NULL/invalid-pointer entries.
- **Q2 AHB pairing:** Happy-path allocate/lock/unlock/release is mostly paired; error paths are not safe. C3 and L3a are the important exceptions. `testCapabilities()` also leaks AHB/EGL resources on `renderer.cpp:514-529` early returns.
- **Q3 EGL/GL lifetime:** NOT SAFE. C1 applies; `renderer.cpp:290-296` ignores window-surface/current failures before GL calls, and `refreshContext()` can leave `surfaceAvailable` stale after `eglCreateWindowSurface()` failure.
- **Q4 renderer raw pointer:** Queue entries carry IDs, not pointers. `findBufferWithRetry()` returns a raw pointer after releasing `bufferLock`; deferred `removedBuffers` release protects the normal path, but there is no explicit generation/ref protocol across CloseScreen and malformed receive paths.
- **Q5 teardown ordering:** FAIL. CloseScreen does not stop/drain the consumer, and `notifyGpuCopyDone()` writes a raceable `conn_fd` without a local fd-lifetime guard.
- **Q6 DoneComposite stale state:** Normal success zeroes `exaGpuComp` and clears `exaCompSrcUpload`, but there is no transaction/generation token. Re-entry/teardown mismatch and L3b timeout paths are unsafe.
- **Q7 global/static reset:** NO. `stateFd`, EGL dispatch flags, renderer thread, telemetry `next_record/dumped`, EXA transaction structs, and several static counters do not reset on same-process recreate. `Renderer::init()` also guards on asynchronously assigned `ctx`, allowing overlapping initialization.
- **Q8 telemetry lifecycle risk:** The historical empty-startup dump latch bug is fixed by `b3a_telemetry.c:486-492` in `1954f82`. Partial early dump, dump-before-consumer-stop, latch-before-file-open, concurrent record serialization, and no generation reset remain observability risks. They are not the highest-confidence direct SIGSEGV root cause.
- **Q9 original SIGSEGV:** Not uniquely explainable. `si_addr=0` is consistent with a NULL-access class, but `PC=0x4800226c` has no exact source-line/load-bias binding; matching unstripped symbolization returned no line, and C2 replay was 3/3 clean. Classification remains observed/non-reproduced/root cause unknown.
- **Q10 instrumentation points:** (1) fence PFN/handle boundary; (2) queue publish/dequeue/ack ownership boundary; (3) CloseScreen → state-null → renderer stop/drain boundary.

## Next action

Keep the matching unstripped ELF and perform one source-level review of the three instrumentation points; do not retry the crash or touch Stable.
