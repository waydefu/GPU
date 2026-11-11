# Gate A P2 R7-P1 hold + liveness support — 2026-09-18 host qualification

```
P1_LIVENESS_SUPPORT_HOST_QUALIFIED
P1_COMPLETION_HOLD_SUPPORT_HOST_QUALIFIED
```

Frozen INVALID cells remain immutable:

- `runtime-abb27a65/r7-p1/` `R7_P1_ABB27A65_QUALIFICATION_INVALID`
- `runtime-8545b26/r7-p1/` `R7_P1_8545B26_QUALIFICATION_INVALID`

RCA: `GATE-A-P2-R7-P1-DUAL-RCA-20260918.md`
(`P1_LIVENESS_PROBE_RCA_PROVEN` +
`P1_COMPLETION_RCA_PROVEN_HIGH_WATERMARK`).

This packet is host/static only. It is not a device retry.

## Repair (minimum)

### Liveness (runner/classifier tooling)

`scripts/android_activity_liveness.py` binds Activity liveness from:

- ADB `test -d /proc/$ACT_PID`
- ADB `ps` package identity

Workstation `/proc` is never death or life authority.

### Present hold (test-only, cell 12)

`lorieGateATestFaultClassHoldsIncomplete`: after cell-12 consume of
serial S, `lorieGpuCopyIsDone(S)` returns FALSE even if later T>S
stores `completedSerial=T`.

Unarmed / unconsumed / other serial: production
`completedSerial >= serial` unchanged.

Cell 13 does not hold. R7-10 wait-wake unchanged. ABI/judge/timeout
unchanged.

Does **not** change `lorieGateAPublishCompleted` or
`ObserveCompleted`. Does **not** make production completion
per-serial.

## Host tests (commands + exit 0)

```text
gcc ... scripts/test_gatea_test_fault_class.c → GATEA_TEST_FAULT_CLASS=PASS
python3 scripts/verify_r7_p1_present_target_arm.py → R7_P1_PRESENT_TARGET_ARM=PASS
python3 scripts/test_android_activity_liveness.py → 6 tests OK
gcc ... scripts/test_gatea_wait_wake_class.c → GATEA_WAIT_WAKE_CLASS=PASS
judge SHA fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17 PASS
ABI protocol 40 / fatal off 4 / version 1 / EVENT_MAX 37 / COUNTER_MAX 28 / fault tail 40 PASS
```

Matrix:

| Case | Result |
|---|---|
| host `/proc` absent + device alive | alive |
| device `/proc` alive + ps identity | alive |
| device `/proc` dead | dead |
| host `/proc` exists cannot override device dead | dead |
| target S consumed, no later completion | S incomplete (hold) |
| S held, later T>S publishes | S still incomplete; T complete |
| OFF/unarmed later T>S | S complete (production watermark) |
| cell 13 consume | no hold |
| cell 10 consume | no hold; x-hup/6 vs timeout/4 unchanged |

## Forbidden (verified absent)

- judge mutation
- 2000 ms Present wait change
- 8 ms CASE_LOOP change
- protocol / EVENT_MAX / COUNTER_MAX change
- production completedSerial redesign
- sleep / fake event36 / fake timeout

## Next

One new commit on `abb27a65` (do not amend). Push. One CI.
New candidate-specific P1/P2 runners. Fresh evidence paths only.
