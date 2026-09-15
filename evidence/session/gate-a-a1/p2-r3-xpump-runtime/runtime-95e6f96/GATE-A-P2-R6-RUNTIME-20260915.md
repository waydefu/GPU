# Gate A P2 R6 wait-or-fatal runtime — 95e6f96 — 2026-09-15

Install of `95e6f96` **DONE**. D2-INFLIGHT 5 consecutive cells executed:
- `r6-d2-inflight`: X 21317 (8×8, sync) FAIL missing reject
- `r6-d2-inflight-retry1`: X 24492 (8×8, sync) FAIL missing reject
- `r6-d2-inflight-retry2`: X 7952 (8×8, pipelined) FAIL missing reject
- `r6-d2-inflight-retry3`: X 13797 (128×128, pipelined+warm) FAIL missing reject
- `r6-d2-inflight-retry4`: X 19332 (1024×1024, pipelined+warm) FAIL missing reject

Root cause investigation **COMPLETED**:
`../../p2-r6-design/GATE-A-P2-R6-D2-INFLIGHT-PHYSICAL-RACE-ANALYSIS-20260915.md`.

COMPLETED serial S (event 14) **PROVEN** across all runs (historical 9369553
absence FALSIFIED). Physical cause of missing reject: Adreno 830 GPU copy
completes in < 0.5 ms, while Xorg single-threaded dispatch takes 2.0–2.5 ms
to reach `gateADirectTryPrepare()`. Direct composite admission when queue is
quiescent is **correct and safe**.

**D2-OOM NOT RUN**. Frozen `runtime-9369553/` untouched.
Stable `:1` package UNTOUCHED (`1.03.01-11b82d9-06.09.26`). Current X PID **1004**.
Production Gate A remains **BLOCKED**.

## Binding

| | |
|---|---|
| serial | `10.193.235.219:33349` live-fetched `_adb-tls-connect._tcp.local.` |
| Installed | `com.waydefu.x11gpu` `1.03.01-95e6f96-15.09.26` CI **34944171114** |
| APK SHA256 | `60c36b4f59c38d13db6fe6c366e6f115a720ec1d6946d057b3ec41551b12f628` MATCH |
| Build ID | `1188e1cabf3b78285e7e5fbedcf64f0b5e7d44f9` MATCH |
| HEAD | `95e6f9602b0146ee190870f84a34aad822ef666f` |
| Stable | `com.termux.x11` `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03; PID **1004** UNTOUCHED |
| HDMI | observe-only, `mDisplayId=0` |

Install cell: `r0/INSTALL-95e6f96-20260915.md`.
CI QUALIFY: `../../p2-r6-ci-34944171114/P2-R6-CI-ARTIFACT-PROVENANCE-20260915.md`.
KEEP FAIL CI: `../../p2-r6-ci-34943831800/KEEP-FAIL-20260915.md`.

## Summary of Executed Cells

| Cell | X PID | Fixture ELF | Size | Strategy | Outcome |
|---|---|---|---|---|---|
| `r6-d2-inflight` | 21317 | `2ca0957f` | 8×8 | Synchronous `xcb_request_check` | FAIL (missing reject) |
| `r6-d2-inflight-retry1` | 24492 | `2ca0957f` | 8×8 | Synchronous `xcb_request_check` | FAIL (missing reject) |
| `r6-d2-inflight-retry2` | 7952 | `ad26211b` | 8×8 | Pipelined flush (Present+Composite together) | FAIL (missing reject) |
| `r6-d2-inflight-retry3` | 13797 | `cc1836c6` | 128×128 | Pipelined + Pre-warmed AHB | FAIL (missing reject) |
| `r6-d2-inflight-retry4` | 19332 | `fec8f46d` | 1024×1024 | Pipelined + Pre-warmed AHB | FAIL (missing reject) |

All cells kept. No silent retries.

## Not Run

- D2-OOM (`TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1`)
- D1 requal on this APK

## Next Actions for User Decision

1. **Option A (Oracle Redesign):** Accept that on Snapdragon 8 Elite / Adreno 830, GPU copy latency (<0.5ms) is physically shorter than Xorg CPU dispatch (2.5ms). Update the D2-INFLIGHT oracle to accept either:
   - `DIRECT_ADMIT_REJECT reason=1` (if CPU catches GPU in flight), OR
   - Immediate `SEMANTIC_SUCCESS` if `completedSerial == lastSerial` proved quiescence before admission.
2. **Option B (D2-OOM Execution):** Proceed to D2-OOM fault injection testing, which tests the critical wait-or-fatal and requeue failure path without depending on physical GPU race conditions.
3. **Option C (STOP):** Freeze current evidence and wait.
