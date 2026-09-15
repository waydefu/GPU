# Gate A P2 R3 drain-wait repair — local compile 2026-09-14

Worktree `/root/projects/GPU加速/src/f8-ahb-gatea-a1`
Base HEAD `6c7ee6f`. File: `lorie/src/main/cpp/lorie/renderer.cpp` only.

## Cause (proven on 6c7ee6f R3)

`GATEA_HANDLE type=1 id=6` then 2s `x-ready-timeout`. Enqueue + `wakeGateA`
ran; `shouldWait` treated the wake as spurious, so
`gateADrainPendingImports` never ran.

## Change

`gateAHasPendingDrain()` (pending import/control/overflow only, not ready
registry). `shouldWait` returns false when it is set, same class as
`gpuCopyPending`. `GATEA_DRAIN` INFO on `LorieNative` when drain has work.

`lorieGateAImportBusy` unchanged (still includes ready entries for rebind).

## Compile

`:lorie:buildCMakeDebug[arm64-v8a]` incremental BUILD SUCCESSFUL, 30s,
exit 0. `git diff --check` PASS. 4 C++ warnings, all pre-existing
(c99-designator keycode table, reorder-init, two `%llu` format). 0 new.

Do not install local ninja `.so`. CI/APK: run **34791993198** PASS,
HEAD `8479997`, APK `0a9d91f6…23a2`, Build ID `b072c9d2…654a`.
Installed experimental-only. Runtime: R1/R2 PASS; R3 FAIL after
`GATEA_DRAIN imports=1` (no READY). Drain-wait itself is proven.
Do not retry R3 on `6c7ee6f` or `8479997`. Production Gate A BLOCKED.
Authority: `p2-r3-drain-runtime/HANDOFF-NEXT-AGENT-20260914.md`.
