# Gate A P2 R7-P1 qualification-validity support — 2026-09-18

Primary verdict: **`R7_P1_VALIDITY_SUPPORT_HOST_QUALIFIED`**

Frozen device verdict remains **`R7_P1_8545B26_QUALIFICATION_INVALID`**.
RCA remains **`R7_P1_VALIDITY_RCA_PROVEN`**
(`GATE-A-P2-R7-P1-VALIDITY-RCA-20260918.md`).

This packet is test-support host qualification only.
It is **not** a device retry. It is **not** NEXT-037 product RCA.
It does **not** execute R7-P2. It does **not** overwrite
`runtime-8545b26/r7-p1/`.

## Frozen INVALID authority

| Field | Value |
|---|---|
| Cell | `runtime-8545b26/r7-p1/` |
| X | 14331 |
| Classifier | `NO_PRESENT_CALLBACK` |
| Judge | NOT INVOKED |
| Disposition | INVALID / FROZEN |

Do not overwrite, delete, append a new verdict, retry in that directory,
or reinterpret as FAIL/PASS.

## Source bind

| Field | Value |
|---|---|
| Parent | `8545b26b308aa60b05685f48560285350e22ee8d` |
| Worktree | `src/f8-ahb-gatea-r7-p1-arm` |
| Branch | `fix/gatea-r7-p1-present-target-arm-20260918` |
| HEAD | still `8545b26` (**uncommitted** validity support) |
| Parent tree `src/f8-ahb-gatea-r7-10-hup` | clean, unmodified |
| Commit | **NOT COMMITTED** |
| CI / APK | **NOT BUILT** |
| Install | **NOT INSTALLED** |

8545b26 is not rewritten.

## Device construction (frozen, not re-run)

| Identity | seq | meaning |
|---|---|---|
| CALLBACK event30 src=1 serial=1 | 0/1 | bring-up CopyArea |
| event35 enum=12 side=2 serial=1 | 2 | fault12 consumed |
| CALLBACK event30 src=4 serial=7 | 54 | target Present |
| event14 serial=7 | 56 | Present GPU COMPLETED |
| event36 serial=7 waited=0 | 79 | helper after done |
| fixture CompleteNotify + CLIENT_OK | — | Present retired |

Fault12 fired **before** target Present CALLBACK. Later Present was not held.

## Exact consume paths (8545b26, unchanged in renderer)

Both on legacy `!gateASeen` completion after EGL fence:

1. `Renderer::applyPendingGpuCopies` — `renderer.cpp`
2. `Renderer::redrawLocked` — `renderer.cpp`

Predicate: selector 12 + armed + optional target fields + CAS consumed.
No Present origin. `entry.op` is COPY for both CopyArea and Present.

P2 enum13 consumes in `applyPendingGpuCopiesLocked` on `entry.op == COPY`
at readIndex advance. Same early-Copy risk.

`P2_EARLY_CONSUME_RISK = YES` (assessment only; P2 not executed).

## Why CopyArea was eligible / Present unprotected

`PublishFromEnv` on 8545b26 stored `armed=1`, `targetGeneration=0`,
`targetOrdinal=0` (wildcards). First legacy COPY completion consumed the
one-shot. Present serial=7 later completed normally (`event14`,
`event36 waited=0`, CLIENT_OK).

`entry.op` cannot distinguish. Renderer cannot see CALLBACK src=4.
ARM=1 was startup-only. Timing-only is formally impossible: holder keeps
`surfaceAvailable`; EXA CopyArea is a product path before the Present
fixture.

## Selected repair: Class A+B

Present-schedule-site arm **before** `writeIndex`, using existing Artifact-B
tail fields (`cell/armed/consumed/targetGeneration/targetOrdinal`). No
shared protocol ABI change.

Rejected:

| Class | Why not chosen as the only fix |
|---|---|
| Timing-only runner/fixture order | No source invariant that zero COPY completions occur before Present |
| Class C origin bit | `LorieGpuCopyEntry` has no Present provenance; `op==COPY` is shared |
| CALLBACK-only arm | `writeIndex` is published **before** event30; not fail-closed |
| Silent re-arm after wrong consume | Breaks one-shot |
| Shared ABI field | Forbidden; STOP for architecture review |

Semantics:

1. Cells 12/13: getenv publishes selector, `armed=0`, targets 0.
2. CopyArea stays `lorieTryScheduleGpuCopy` / `presentTarget=0` / cannot arm.
3. Present uses `lorieTryScheduleGpuPresentCopy` / `presentTarget=1`.
4. After serial assign and **before** `__sync_synchronize` / `writeIndex`,
   `ArmPresentTarget(serial, generation)` stores identity then `armed=1`.
5. Matching renderer consume CAS once → event35 → withhold completedSerial.
6. Consumed forbids re-arm. Different serial while armed is refused.
7. Present-bound consume refuses wildcard targets even if `armed=1`.
8. CALLBACK src=4 is backup idempotent arm of the same identity; CopyArea
   xop=1 does not arm.
9. Cells other than 12/13 keep startup `armed=1` (R7-10 unchanged).
10. OFF / unconfigured: `ArmPresentTarget` no-ops (magic mismatch).

One-shot after repair:

- pre-target eligible count = 0
- target eligible count = 1
- post-consume eligible count = 0

## Host tests

`scripts/test_gatea_test_fault_class.c` → `GATEA_TEST_FAULT_CLASS=PASS`

| Case | Result |
|---|---|
| OFF / unconfigured | no consume, no arm |
| Early CopyArea serial=1, cell 12 unarmed | consume=0, event path not taken |
| armed=1 with wildcard targets | still consume=0 for cells 12/13 |
| Arm serial 0 / generation 0 | refused |
| Target serial=7 gen=1 | consume exactly once |
| Unrelated serial 1 or 8 after arm | consume=0 |
| Repeat consume / re-arm after consume | consume=0, arm=0 |
| Idempotent same-target arm | keeps serial 7; different serial refused |
| Cell 13 | same Present-bound arming (no P2 device) |
| Cell 10 wildcard | still consumes first serial (R7-10) |
| Peer death wait-wake | `x-hup` / reason=6 |
| Live timeout wait-wake | `timeout` / reason=4 |

`scripts/test_gatea_wait_wake_class.c` → `GATEA_WAIT_WAKE_CLASS=PASS`

## Static verifier

`scripts/verify_r7_p1_present_target_arm.py` → `R7_P1_PRESENT_TARGET_ARM=PASS`

`scripts/verify_r7_10_hup_containment.py` → `R7_10_HUP_CONTAINMENT=PASS`

`xserver.patch` `patch -p1 --dry-run` → exit 0 (submodule left clean).

## ABI / timeout / judge freeze

| Freeze | Status |
|---|---|
| `LorieGateAProtocol` size 40 | PASS |
| `generationFatal` offset 4 | PASS |
| `protocolVersion` 1 | PASS |
| `EVENT_MAX` 37 | PASS |
| `COUNTER_MAX` 28 | PASS |
| Artifact-B `LorieGateATestFault` size 40 | PASS (no new field) |
| Product Present wait 2000 ms | PASS |
| CASE_LOOP 8 ms | PASS |
| `judge-r7.py` SHA256 `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17` | PASS, not in repair tree |
| Historical `run-r7-p1-8545b26.sh` SHA256 `46c2289d…16ba7` | unmodified |
| Historical `classify_r7_p1_present_hold.py` SHA256 `07de408b…3908` | unmodified |

P1 expected halt remains `x-present-copy-wait / 4` with CALLBACK30 src=4.

## Files changed (uncommitted)

Worktree `src/f8-ahb-gatea-r7-p1-arm` only:

| Path | Role |
|---|---|
| `lorie/src/main/cpp/lorie/lorie_gatea_test_fault_class.h` | test-fault class (Armed/Consume/ArmPresentTarget) |
| `lorie/src/main/cpp/lorie/lorie.h` | include + wrappers; consume still emits event35 after CAS |
| `lorie/src/main/cpp/lorie/InitOutput.c` | PresentCopy path, env unarmed 12/13, CALLBACK backup, COMPOSITE `presentTarget=0` |
| `lorie/src/main/cpp/patches/xserver.patch` | Present call site + extern |
| `scripts/test_gatea_test_fault_class.c` | host tests |
| `scripts/verify_r7_p1_present_target_arm.py` | static verifier |

Not changed: renderer completion, `completedSerial` publish except existing
fault12 withhold, `notifyGpuCopyDone`, wait-wake, 2000 ms, R7-10 HUP,
judge, historical runners/evidence, shared protocol.

## CI / artifact

**NOT BUILT.** No new SHA, no CI run, no APK, no Build ID.

Future binary must **not** be recorded as `runtime-8545b26`.
After commit+CI+artifact+runner+install grants, a new attempt path is
`runtime-<newsha>/r7-p1` with new runner authority. Do not suffix the
frozen INVALID directory.

## Device mutation audit (this validity round)

| Action | Count |
|---|---|
| ADB install | 0 |
| X3 launch | 0 |
| Activity launch | 0 |
| Present fixture | 0 |
| fault12 device trigger | 0 |
| R7-P2 | 0 |
| Stable mutation | 0 |
| HDMI mutation | 0 |

## R7 state (unchanged)

| Cell | Status |
|---|---|
| R7-04 … R7-09, R7-11 | PASS |
| a07d66c R7-10 | VALID FAIL / FROZEN |
| 8545b26 R7-10 | PASS / FROZEN |
| R7-P1 | INVALID / FROZEN |
| R7-P2 | NOT RUN |
| Overall | IN PROGRESS 11/13 |
| Production Gate A | BLOCKED |

## Recommended next

Explicit grant to **commit** this uncommitted worktree, then CI / artifact
qualification. Do **not** install. Do **not** retry `runtime-8545b26/r7-p1`.
Do **not** start R7-P2. Do **not** rewrite 8545b26.
