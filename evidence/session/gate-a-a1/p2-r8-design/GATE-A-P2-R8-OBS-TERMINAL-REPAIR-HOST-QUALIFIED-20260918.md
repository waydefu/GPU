# GATE A P2 R8 OBS TERMINAL REPAIR HOST QUALIFIED — 2026-09-18

```
STATUS: R8_OBS_TERMINAL_REPAIR_HOST_QUALIFIED
        parent 65938a447639fce2adae61a15a2d8348e7c6455f unamended
        LOCAL_NDK_PREFLIGHT_UNAVAILABLE (same workstation hole)
        Production Gate A BLOCKED
        no device cell in this packet
```

## Frozen C1 history (immutable)

| Attempt | Path | Verdict |
| --- | --- | --- |
| 01 | `runtime-65938a4/r8-c1/attempt-01/` | `R8_INVALID MISSING_END_x` |
| 02 | `.../attempt-02-orchestration-v2/` | `R8_BLOCKED SCREEN_NOT_AWAKE` |
| 03 | `.../attempt-03-orchestration-v2/` | `R8_BLOCKED` tooling emit JSON |
| 04 | `.../attempt-04-orchestration-v2/` | `R8_INVALID END_COUNT_MISMATCH_x` |

attempt-04 is not re-judged PASS. Orchestration v2 construction remains proven (X 21246, both ENDs, GiveUp→CloseScreen).

## RCA

`R8_OBS_TERMINAL_RCA_PROVEN`

X END was emitted in `lorieCloseScreen` immediately after `X_CLOSE_RESULT`, before `DestroyPixmap` of the screen pixmap. Producer seq 43–48 were destructor enter/exit; 49–52 were GPU_COPY_DONE defer/recheck.

Renderer END was emitted immediately after `R_UNBOUND_FINAL`. Later same renderer thread: `R_WAKE_SENT cause=fence_completed` then `R_WAKE_SENT cause=surface_loss`.

## Saved CloseScreen audit

`pvfb->CloseScreen` is captured after `present_screen_init` and before wrapping `lorieCloseScreen`. Delegate cannot recurse into `lorieCloseScreen`.

The saved chain is present → miPointer → RR → EXA → Picture → DRI3 → fb. `present_scmd_flip_destroy` → `present_flip_idle` can `dixDestroyPixmap` while EXA `DestroyPixmap` is still `lorieExaDestroyPixmap`. Therefore X observation END is after `pScreen->CloseScreen(pScreen)` returns, not before the delegate.

## Repair (observation-only)

- X: `lorieR8ObsEnd("x")` after root `DestroyPixmap`, restore of saved `CloseScreen`, and the saved CloseScreen return.
- Renderer: test-only `r8RendererGenerationUnbound` / `r8RendererSurfaceQuiesced` / `r8RendererLoopDrained` / `r8RendererEndEmitted`. `lorieR8MaybeFinalizeRendererObs` is idempotent. END requires unbound AND surface quiesced AND the threadLoop apply/release drain point (so same-iteration `fence_completed` after unbind is included). `!win` keeps product `surfaceAvailable=false` then `notifyGpuCopyDoneCause("surface_loss")` before `R_SURFACE_QUIESCED`.
- `lorieR8Obs` after END emits `R8_OBS_POST_END role= phase=` and does not write a normal `R8_OBS` record.

No Gate A register/ready/pair/lease/publish/completion/Present ACK/HUP/timeout/surface/generation-close/buffer-destruction product change. Shared ABI and R8 test protocol sizes unchanged. Judge SHA `f021048d…0e31` and collector SHA `e6df519a…666c8` unchanged.

## Host / static

| Check | Result |
| --- | --- |
| `tests/r8/verify-r8-support.py` | PASS `R8_SUPPORT_HOST_STATIC_OK` |
| judge vectors | 53/53 `failures=0` |
| `test_r8_obs_terminal.py` | PASS (X END→destructor fail; UNBOUND→END→surface_loss fail; unbound→surface→END PASS; surface→unbound→END PASS) |
| `test_r8_obs_terminal.c` | PASS (`R8_OBS_POST_END`, not silent drop, END idempotent) |
| `R7_10_HUP_CONTAINMENT` | PASS |
| `R7_P1_PRESENT_TARGET_ARM` (incl. cell-12 hold) | PASS |
| `R7_HUP_PRESERVE` | PASS |
| `GATEA_WAIT_WAKE_CLASS` | PASS |
| `GATEA_TEST_FAULT_CLASS` | PASS |
| `GATEA_HUP_CLASS` | PASS |

## Local NDK preflight

**LOCAL_NDK_PREFLIGHT_UNAVAILABLE** — `ANDROID_HOME` / `ANDROID_NDK_HOME` unset; no NDK tree; host cannot produce `InitOutput.c.o` / `renderer.cpp.o` / `lorie_r8_obs.c.o` / `cmdentrypoint.cpp.o` / native link. Closest available proof is the host gcc obs-terminal compile + existing header/protocol compile in `verify-r8-support.py`.

## Next

One new commit on parent `65938a447639fce2adae61a15a2d8348e7c6455f`. One fresh CI. Do not rerun 35304122983 / 35305368742 / 35311343984.
