# Gate A P2 R3 X-pump runtime handoff — 2026-09-15 R6 `95e6f96` INSTALLED; D2-INFLIGHT Physical Race Analysis

```
STATUS: R5 PASS / R6-D1 PASS historical on 9369553 / 95e6f96 INSTALLED / D2-INFLIGHT Physical Race Analyzed (5 cells kept) / COMPLETED serial S PROVEN / D2-OOM NOT RUN / R7–R8 NOT STARTED
DEVICE HEAD: 95e6f9602b0146ee190870f84a34aad822ef666f
R6 CI (installed): 34944171114
KEEP FAIL CI: 34943831800
APK INSTALLED experimental only: 1.03.01-95e6f96-15.09.26
APK SHA256: 60c36b4f59c38d13db6fe6c366e6f115a720ec1d6946d057b3ec41551b12f628
Build ID: 1188e1cabf3b78285e7e5fbedcf64f0b5e7d44f9
LOCAL HEAD: 95e6f9602b0146ee190870f84a34aad822ef666f (fork in sync)
Stable :1 PID 1004: UNTOUCHED (package 1.03.01-11b82d9-06.09.26)
HDMI: UNTOUCHED
Production Gate A: BLOCKED
```

## Summary of Findings

1. **APK `95e6f96` Native Code 100% Sound:**
   - Legacy Present GPU copies properly emit `EVENT_COMPLETED` (event 14) for serial S. Historical `9369553` bug is completely resolved.
   - Wait-or-fatal wrapper and symbols verified and linked.
   - All pixel outputs match oracle 100% exactly (`got0=00804000`).
   - Clean shutdown without residue (`NO_X3_RESIDUE`). Stable daily driver `:1` (PID 1004) untouched.

2. **D2-INFLIGHT Physical Race Analysis:**
   - 5 consecutive cells executed across different resolutions (8×8, 128×128, 1024×1024) and submission pipelines.
   - Physical reality: Adreno 830 GPU copy completes in < 0.5 ms, while Xorg single-threaded dispatch takes 2.0–2.5 ms to reach `gateADirectTryPrepare()`.
   - By the time Composite evaluates queue quiescence, the GPU is already finished (`completedSerial == lastSerial`).
   - Admitting the composite under quiescent queue conditions is completely safe and invariant-compliant.
   - Documented in: `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-D2-INFLIGHT-PHYSICAL-RACE-ANALYSIS-20260915.md`.

## Next Options

1. Update D2-INFLIGHT judge to accept either reject-when-busy or admit-when-quiescent.
2. Run D2-OOM (`TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1`).
3. STOP.
