# Gate A P2 CASE_LOOP renderer wakeup fix — 2026-09-16

Source worktree `src/f8-ahb-gatea-case-loop` branch `fix/gatea-case-loop-wakeup-20260916`.

| Role | SHA |
|---|---|
| parent (EXA Composite fail-stop) | `0d72332c0e591b2137262d06d7dcab704be49383` |
| initial CASE_LOOP fix | `327b02838009eca8bac127ca7bb381fd2aff48ed` |
| hardened candidate | `7549e3667ec03b8b5e50d2e5befe03065840bbd9` |

**Not B-2.** **Not R7.** Timeout **2000 ms unchanged**. Frozen R6 `0f1e546` untouched. Diagnostic trees `feeaa56` / `1f85b80` / `27d8d1b` not mutated.

Device still has observational `feeaa56`. Hardened SHA is **not installed**.

## Evidence language

```
DEVICE-PROVEN: CASE_LOOP consume stall
  X published serial 86; renderer did not consume it for ~2002 ms
  NOTIFY max 0.105 ms; SWAP max 1.479 ms; NEXT_FENCE max 1.751 ms
  CASE_NOTIFY / CASE_SWAP / CASE_NEXT_FENCE FALSIFIED as the 2 s blocker

SOURCE-SUPPORTED ROOT MECHANISM:
  waitForNextFrame + possible lost wakeup + unbounded idle wait

NOT DIRECTLY OBSERVED:
  GLES sitting inside pthread_cond_wait for the entire 2 s
  (no COND_WAIT_ENTER / COND_WAIT_EXIT markers)
```

1. `redrawLocked` sets `waitForNextFrame = true` after SWAP/NEXT_FENCE.
2. `lorieRedraw` (AChoreographer, X thread) is the only clearer.
3. `lorieGpuCopyWait` is `usleep(200)` with **no event pump**, so (2) does not run during the EXA wait.
4. `shouldWait` returns true when the queue is empty and `waitForNextFrame` is set.
5. X publishes `writeIndex` then `pthread_cond_signal(rendererCond)` **without** Activity `stateLock` (process-private by design). Lost wakeup is possible.
6. `feeaa56` stall-obs-01: serial 86 published at 17:29:51.581; GLES tid 22960 silent until timeout 17:29:53.583.

timeout→Done remains ABSENT (repair held).

## Invariant

If GPU-copy work becomes visible in the sticky queue while the renderer is
frame-gated, the renderer must re-evaluate the queue within
`LORIE_RENDERER_FRAME_WAIT_NS` (8 ms) even if the associated condvar signal
is lost.

This interval is **not** a GPU completion timeout. The outer EXA fail-stop
remains `lorieGpuCopyWait(serial, 2000)` / `LORIE_GATEA_FENCE_TIMEOUT_NS`.

## Change (`7549e36`)

`Renderer::waitWhileIdle`:

- Recheck sticky `readIndex != writeIndex` after `shouldWait()` before sleeping.
- If `waitForNextFrame`, `pthread_cond_timedwait` **8 ms** (`LORIE_RENDERER_FRAME_WAIT_NS`) with a **CLOCK_MONOTONIC** deadline.
- Otherwise keep infinite `pthread_cond_wait` (no surface / not vsync-gated).

`Renderer::init` sets `stateCond` with `PTHREAD_PROCESS_SHARED` **and**
`pthread_condattr_setclock(..., CLOCK_MONOTONIC)`. Failure aborts; there is
no silent fallback to unbounded wait.

Clock verdict: **MONOTONIC_SAFE**.

- `stateCond` is mmap'd shared memory. GLES waits; X only `pthread_cond_signal`.
- Signal does not interpret the clock. Protocol / mmap size / shared-state ABI unchanged.
- Bionic `pthread_condattr_setclock` is API 21+; project `minSdkVersion` is 24.
- Official Bionic header: default CLOCK_REALTIME timeouts are typically inappropriate; CLOCK_MONOTONIC is the initialization option.
  https://android.googlesource.com/platform/bionic/+/main/libc/include/pthread.h

Standalone `applyPendingGpuCopies` when `waitForNextFrame && gpuCopyPending` is unchanged.

## Host test

`scripts/test_renderer_gpu_copy_wakeup.c` no longer uses `volatile` as
synchronization. Queue words are C11 `_Atomic uint64_t` with
`memory_order_release` publish / `memory_order_acquire` observe, matching
`lorieGateAPublishWriteIndex` / `lorieGateAObserveWriteIndex`.
`finished` / `entered_wait` are ancillary flags with the same acquire/release
pair (not seq_cst). Compile: `-std=c11 -Wall -Wextra -Werror -pthread`.

No `cond_signal` in either mode. Legacy process-exit reaps the hung waiter;
`pthread_cancel` is not used.

## Host + CI

```
cc -std=c11 -Wall -Wextra -Werror -pthread -O1 -g
LEGACY=HANG_AS_EXPECTED still_blocked after 151 ms without signal
FIXED=PASS waited_ms=10 (sticky writeIndex, no cond_signal)
CASE_LOOP_WAKEUP=PASS
EXA_COMPOSITE_WAIT=PASS
git diff --check PASS
TSAN NOT RUN (toolchain present; PRoot FATAL unexpected memory mapping)
fork CI 35084701124 workflow_dispatch success headSha=7549e36
APK 1.03.01-7549e36-16.09.26 SHA256 45500894…4bc3 Build ID 4c5b7b86…8f81
signer continuity PASS; NOT INSTALLED
```

Host test does **not** prove device B-2.

## Not done

- Device install of `7549e36`
- B-2 matrix / silent-retry of `0d72332` / `feeaa56` stall-obs-01
- Timeout change
- R7
- Stable / HDMI
