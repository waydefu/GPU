# GATE A P2 R8 SUPPORT HOST VERIFIED — 2026-09-18

Verdict: **R8_SUPPORT_HOST_VERIFIED**

| Field | Value |
| --- | --- |
| Design acceptance | `evidence/session/gate-a-a1/p2-r8-design/GATE-A-P2-R8-DESIGN-ACCEPTANCE-20260918.md` `R8_DESIGN_ACCEPTED_ON_A4C8177` |
| Historical design source | `fdfb1ce44b429897eda17c43bf33fbd37afe67f3` |
| Parent (R7 final) | `a4c8177f4b059fddd111717255e9d23cf0e15e1e` |
| Branch | `feat/gatea-r8-lifecycle-support-20260918` |
| judge_vectors | 53 (host/judge; not device executions) |
| device_cells | 10 (not run in this packet) |

## Allowlist (this generation)

CMake option `LORIE_ENABLE_R8_TEST_SUPPORT` default **OFF**. Experimental `lorie/build.gradle` passes `-DLORIE_ENABLE_R8_TEST_SUPPORT=ON` for this APK lineage. Runtime still requires `TERMUX_X11_R8_ARM=1` plus exact `TERMUX_X11_R8_CASE`.

New sources: `lorie_r8_obs.[ch]`, `lorie_r8_test.[ch]`, `tests/r8/*`.

Product-path edits are compile-gated observation, P1 real `lorieExaDestroyPixmap` on the ON candidate, P2 still calls real `gateACloseGeneration`, Present submit/pre/post observation hooks, renderer destroy-stage/ACK/unbind observation, deferred local IDs + host-only inject seam (`!__ANDROID__`).

Read-only pending accessor `LorieBuffer_gpuCopyPendingCount` (does not change ownership).

No shared Gate A wire/ABI / EVENT_MAX / timeout / judge-r7.py change.

## Host results

| Check | Result |
| --- | --- |
| test_r8_protocol sizes/opcodes | PASS |
| test_r8_parser I02 swapped/invalid phase | PASS |
| test-judge-r8.py 53 vectors | PASS `failures=0` |
| p_r8_lifecycle --help | PASS |
| GATEA_WAIT_WAKE_CLASS | PASS |
| GATEA_TEST_FAULT_CLASS (incl. cell12 hold) | PASS |
| GATEA_HUP_CLASS | PASS |
| R7_10_HUP_CONTAINMENT | PASS |
| R7_P1_PRESENT_TARGET_ARM | PASS |
| R7_HUP_PRESERVE | PASS |
| OFF cmake default | PASS |
| Host inject `#if !defined(__ANDROID__)` | PASS |
| REGISTER_BUFFER does not call Prepare/pair/submit | PASS |

## Tool hashes at HOST_VERIFIED

| Tool | SHA256 |
| --- | --- |
| tests/r8/judge-r8.py | `f021048da3c1b729c6f9bf560eba52609b2f980336dd4fab77ad1700438c0e31` |
| tests/r8/collect-r8.py | `e6df519a75c872c8a56fac00146585853eec7f17a3f424e70e5d4736340666c8` |
| tests/r8/lifecycle-cell-spec.json | `ff22a1521d23a8954b0b4f3a603dbb19af98b3e8b3727342caf5e107b639b3ba` |
| tests/r8/run-r8-one-cell.sh | `f4ed81f4df1da97d2e65e0fbc11b8581f258e9b861fe0bb0a6ecd5d6bcac2c3d` |
| tests/r8/p_r8_lifecycle.c | `ca52129288d5e0af68e56f72fe62125b1949926dd2d7fca6f0c8d07284c00954` |
| tests/r8/r8-test-protocol.h | `b90b82b3ec847ce2cca80500a71309e2bd5a0a458deb3719f8285d8824f44f9b` |
| host ELF `/tmp/p_r8_lifecycle` | `d3910436ca6489a991725f5293d915286c04b911f4526b95d84ce7cbfb200493` |

A11 split is frozen: real CloseScreen cannot have live **client** Gate A registrations (`FreeAllResources` first). C2 device cell uses that disposition. Synthetic live-at-close is not a device cell in this matrix.

I04 OFF-build proof: option default OFF; P1 consume-site stub remains in `#else`; extension/obs sources added only when option ON.

Proceed to one source commit on this branch. Do not amend `a4c8177`.
