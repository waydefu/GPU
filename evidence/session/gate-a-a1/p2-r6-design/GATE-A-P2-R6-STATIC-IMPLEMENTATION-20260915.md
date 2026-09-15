# Gate A P2 R6 — design-complete static implementation

Date: 2026-09-15

## Status

```text
DESIGN: COMPLETE (GATE-A-P2-R6-DESIGN-20260915.md)
IMPLEMENTATION GRANT: USER 2026-09-15 (rollback required)
SOURCE 9369553: 936955397619091b48c8e717f28b2cd187d79065 (events 29–32)
SOURCE 54ff35b: 54ff35bd2e47a250c88b5c19391c22b0f6af5700 (legacy EVENT_COMPLETED; not on device)
BASE / ROLLBACK SHA: 37d839323255b4830d657da3bcbf7f616bc78ad3
INSTALLED WORKTREE: src/f8-ahb-gatea-r5-fix stays 37d8393 clean
DEVICE APK: 1.03.01-9369553-15.09.26 (CI 34926730189); 54ff35b not installed
HOST FIXTURES: cc PASS; new D2 ELF 2ca0957f…68a3
STATIC VERIFIER: PASS verify_r6_design_impl.py (includes gateATraceLegacyCompleted)
ARM64 / CI: PASS run 34926730189 for 9369553; 54ff35b CI not run
INSTALL / RUNTIME: D1 PASS retry5 / D2-INFLIGHT-retry1 FAIL / D2-OOM NOT RUN
D2 COMPLETED PACKET: GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md
R7: NOT STARTED
Production Gate A: BLOCKED
Stable / HDMI: UNTOUCHED
```

## Rollback map

| Layer | How to undo |
|---|---|
| Device | No change. Experimental APK remains `37d8393`. |
| Installed-source worktree | `src/f8-ahb-gatea-r5-fix` never left `37d8393`. |
| This branch | `git -C src/f8-ahb-gatea-r6 checkout 37d8393` or delete the branch. |
| Worktree | `git -C src/f8-ahb-gatea-r5-fix worktree remove src/f8-ahb-gatea-r6` then `git branch -D qualification/gatea-r6-20260915`. |
| Fork branch (if pushed) | delete `fork/qualification/gatea-r6-20260915` only; never force-push `fix/gatea-r5-backpressure-20260915`. |

Do not reset, rebase, or force-push `37d8393`.

## Files (worktree)

| File | Change |
|---|---|
| `lorie/src/main/cpp/lorie/lorie.h` | events 29–32; XOP/reject constants; C prototypes; static asserts (event 28 and `COUNTER_MAX==28` frozen) |
| `lorie/src/main/cpp/lorie/InitOutput.c` | request/callback/reject/early-ack helpers; EXA/PrepareAccess traces; Present OOM one-shot getenv |
| `lorie/src/main/cpp/patches/xserver.patch` | dix `dispatch.c` REQUEST_ARRIVED before `ProcVector`; `present_execute.c` post-schedule one-shot + Present CALLBACK + `PRESENT_EARLY_ACK`; `present_priv.h` externs |

xserver submodule HEAD remains `65d790b`. CI applies `xserver.patch` (`patch -p1`). Round-trip: clean submodule + this patch **exit 0**.

Not modified in `9369553`: `renderer.cpp` fence order, `cmdentrypoint.cpp`,
`gateAWaitTerminal` (still `usleep(200)`, no X-client pump), queue/protocol/direct
ABI, counters, R7 `TERMUX_X11_GATEA_TEST_FAULT`.

`54ff35b` adds telemetry-only `gateATraceLegacyCompleted` in `renderer.cpp`
(fence order unchanged). See `GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md`.

## Fixtures (project `patches/`, not in the APK repo)

| Source | Host cc |
|---|---|
| `patches/p_r6_d1_queued.c` | SHA256 `d25d2b797c9938c3ca74191f64534f33cceb6a7ca847fb2ab228121a81f11753` |
| `patches/p_r6_d2_present.c` | SHA256 `c4e8a680a457f54ba1d0c612c82fb692336b1e69b0276b02b2e7f7cd32a13c9a` (CompleteNotify after race; ELF `2ca0957f…68a3`) |

Do not edit `patches/p_r6_cross_op.c`. Do not overwrite `runtime-37d8393/r6-cross-op/`.

## Verification this session

```text
python3 evidence/session/gate-a-a1/p2-r6-design/verify_r6_design_impl.py \
  src/f8-ahb-gatea-r6
→ R6_DESIGN_IMPL=PASS

cc -O2 patches/p_r6_d1_queued.c -lxcb -lxcb-render -lxcb-present
cc -O2 patches/p_r6_d2_present.c -lxcb -lxcb-render -lxcb-present
→ exit 0

patch -p1 -d <xserver@65d790b> -i lorie/src/main/cpp/patches/xserver.patch
→ exit 0
```

## Next (not this grant)

Install, ADB, device, and the three runtime cells each need a **new** explicit
grant. Device stays on `37d8393` until then. CI provenance:
`../p2-r6-ci-34926730189/P2-R6-CI-ARTIFACT-PROVENANCE-20260915.md`.
