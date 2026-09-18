# GATE A P2 R8 GIVEUP-END HOST QUALIFIED — 2026-09-18

```
STATUS: R8_GIVEUP_END_HOST_QUALIFIED
        parent 5a782f6f47ffa1a3374bac04aef5616a81d59089 unamended
        commit 2a245b0bc5d38394df29546e0af0de798f9d260c
        Production Gate A BLOCKED
        no device cell in this packet
```

## Frozen C1 history (immutable)

| Attempt | Path | Verdict |
| --- | --- | --- |
| 01 | `runtime-65938a4/r8-c1/attempt-01/` | `R8_INVALID MISSING_END_x` |
| 02 | `.../attempt-02-orchestration-v2/` | `R8_BLOCKED SCREEN_NOT_AWAKE` |
| 03 | `.../attempt-03-orchestration-v2/` | `R8_BLOCKED TOOLING_EMIT_JSON` |
| 04 | `.../attempt-04-orchestration-v2/` | `R8_INVALID END_COUNT_MISMATCH_x` |
| 05 | `runtime-5a782f6/r8-c1/attempt-05-obs-terminal/` | `R8_INVALID POST_END_OBSERVATION` |

Do not retry 01–05. Do not rewrite those packets.

## RCA (source-backed)

`R8_GIVEUP_END_RCA_PROVEN`

Attempt-05 X END at `16:22:27.760` after saved CloseScreen return. Same tid `14452` then:

- `16:22:27.761` `Xlorie: Initialized EGL version 1.5` = `rendererTestCapabilities` from `InitOutput` (`InitOutput.c:1516` on 5a782f6)
- `16:22:27.782` `InstallProbe installed=0` = `lorieInstallXRenderProbe` from `lorieScreenInit`
- `16:22:27.787` shared buffer id 10 = new generation screen pixmap
- `16:22:27.787–27.808` 16×16 bpp=1 `Sprep` then two `X_DESTRUCTOR` POST_END = `CreateRootCursor`
- `16:22:27.857` `DEFER_ENQUEUE` / `X_WAKE_RECEIVED` / `DEFER_DISPATCH` / `RECHECK` = GPU_COPY_DONE under `LORIE_GATEA_LEGACY_DEFER`

This is **server generation reset**, not leftover CloseScreen wrap work. `Dispatch()` clears `DE_RESET` (`dix/dispatch.c:587`) then `dix_main` always CloseScreens and, unless `DE_TERMINATE`, loops `serverGeneration++` → `InitOutput`. Last-client disconnect uses default `dispatchExceptionAtReset = DE_RESET`. Official last DDX hook on terminate is `ddxGiveUp` (`dix/main.c:354` after CloseScreen / FreeFonts / ClearWorkQueue).

Renderer END path is unchanged and already correct on attempt-05 (`post-END r=0`).

## Repair (observation-only)

- Remove `lorieR8ObsEnd("x")` from `lorieCloseScreen`.
- Emit it in existing `ddxGiveUp` after `UnlockServer`, immediately before `exit`, under `LORIE_ENABLE_R8_TEST_SUPPORT`.
- Keep `R8_OBS_POST_END` detector. No silent drop / collector truncation / judge weakening.
- No Gate A product semantics, 2000 ms timeout, shared ABI, protocol, or renderer terminal-logic change.

Unstripped CI `libXlorie.so` `ddxGiveUp` disassembly: `UnlockServer` → `lorieR8ObsEnd` → `exit`.

## Host / static

| Check | Result |
| --- | --- |
| RED `verify-r8-support.py` on 5a782f6 | FAIL `x_end_not_in_close` / `x_obs_end_at_giveup` / `x_end_after_unlock` |
| GREEN after repair | `R8_SUPPORT_HOST_STATIC_OK` |
| judge vectors | 53/53 `failures=0` SHA `f021048d…0e31` unchanged |
| collector SHA | `e6df519a…666c8` unchanged |
| `test_r8_obs_terminal.py` | PASS vectors=8 (reset-then-giveup legal; post-END still red) |
| `test_r8_obs_terminal.c` | PASS (`R8_OBS_POST_END`, not silent drop, END idempotent) |
| R7_10 / R7_P1 / R7_HUP_PRESERVE / wait-wake / test-fault / HUP class | PASS |

## Next

One new commit on parent `5a782f6`. One fresh CI. Do not rerun 35304122983 / 35305368742 / 35311343984 / 35321447455.
