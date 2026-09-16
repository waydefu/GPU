# Gate A P2 CASE_LOOP renderer wakeup fix — 2026-09-16

Source worktree `src/f8-ahb-gatea-case-loop` branch `fix/gatea-case-loop-wakeup-20260916` HEAD **`327b02838009eca8bac127ca7bb381fd2aff48ed`**, parent `0d72332` (EXA Composite timeout repair). **Not B-2.** **Not R7.** Timeout **2000 ms unchanged**. Frozen R6 `0f1e546` untouched. Diagnostic trees `feeaa56` / `1f85b80` / `27d8d1b` not mutated.

Device still has observational `feeaa56`. This SHA is **not installed**.

## Root cause

```
PROVEN: GLES threadLoop infinite cond_wait while waitForNextFrame
        after S-1, before consume of published S
```

1. `redrawLocked` sets `waitForNextFrame = true` after SWAP/NEXT_FENCE.
2. `lorieRedraw` (AChoreographer, X thread) is the only clearer.
3. `lorieGpuCopyWait` is `usleep(200)` with **no event pump**, so (2) does not run during the EXA wait.
4. `shouldWait` returns true when the queue is empty and `waitForNextFrame` is set → `pthread_cond_wait`.
5. X publishes `writeIndex` then `pthread_cond_signal(rendererCond)` **without** Activity `stateLock` (process-private by design). Lost wakeup is possible.
6. `feeaa56` stall-obs-01: serial 86 published at 17:29:51.581; GLES tid 22960 silent until timeout 17:29:53.583. NOTIFY/SWAP/NEXT_FENCE max 0.105 / 1.479 / 1.751 ms.

FALSIFIED as the 2 s blocker: CASE_NOTIFY, CASE_SWAP, CASE_NEXT_FENCE.
timeout→Done remains ABSENT (repair held).

## Change

`Renderer::waitWhileIdle`:

- Recheck sticky `readIndex != writeIndex` after `shouldWait()` before sleeping.
- If `waitForNextFrame`, `pthread_cond_timedwait` **8 ms** (`LORIE_RENDERER_FRAME_WAIT_NS`).
- Otherwise keep infinite `pthread_cond_wait` (no surface / not vsync-gated).

Standalone `applyPendingGpuCopies` when `waitForNextFrame && gpuCopyPending` is unchanged. EXA `lorieGpuCopyWait(..., 2000)` and `lorieGpuCopyWaitForCompositeOrFatal` are unchanged.

## Verification (host)

```
EXA_COMPOSITE_WAIT=PASS  scripts/verify_exa_composite_wait.py
CASE_LOOP_WAKEUP=PASS    scripts/verify_case_loop_wakeup.py
LEGACY=HANG_AS_EXPECTED  test_renderer_gpu_copy_wakeup legacy  (150 ms, no signal)
FIXED=PASS waited_ms=5   test_renderer_gpu_copy_wakeup fixed   (8 ms timedwait, no signal)
git diff --check         PASS
```

Host test does **not** prove device B-2. It proves the wait policy wakes on a sticky writeIndex without `cond_signal`.

## Not done

- Device install of this SHA
- B-2 matrix / silent-retry of `0d72332` / `feeaa56` stall-obs-01
- Timeout change
- R7
- Stable / HDMI
