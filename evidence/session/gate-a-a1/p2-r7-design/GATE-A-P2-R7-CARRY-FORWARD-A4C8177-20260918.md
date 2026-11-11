# R7 carry-forward audit — a07d66c → 8545b26 → abb27a65 → a4c8177

```
CARRY_FORWARD_CLEAN
historical cells were NOT rerun
source: a4c8177f4b059fddd111717255e9d23cf0e15e1e
judge SHA: fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17 UNCHANGED
timeout_ms: 2000 UNCHANGED
```

## Lineage (product)

| SHA | Change | Scope when unarmed |
|---|---|---|
| a07d66c | HUP-preserve | cells 1–9, 11 device-qualified here |
| 8545b26 | peer-HUP containment in Done wait | R7-10 device PASS; wait-wake class |
| abb27a65 | test-only Present target arm for cells 12/13 | `lorieGateATestFaultIsPresentBoundCell` is 12\|\|13 only |
| a4c8177 | test-only held-incomplete for consumed cell 12 | `HoldsIncomplete` returns 0 unless consumed && cell==12 && serial==S |

Unarmed / unconsumed: `lorieGpuCopyIsDone` remains `completedSerial >= serial`.
Cells 1–11 selectors in frozen `judge-r7.py` unchanged.

## Host/static (this batch)

- `R7_10_HUP_CONTAINMENT=PASS`
- `GATEA_WAIT_WAKE_CLASS=PASS`
- `GATEA_TEST_FAULT_CLASS=PASS`
- `R7_P1_PRESENT_TARGET_ARM=PASS`
- `R7_HUP_PRESERVE=PASS`
- frozen judge 16/16
- P1 held-incomplete / high-watermark: live validity-02 waited=1 + timeout/4 with later serial 8 allowed

## Per-cell

| Cell | Qualified on | Class |
|---|---|---|
| R7-04 | fdfb1ce X 9891 | CARRY_FORWARD_SAFE |
| R7-05 | a07d66c X 8418 | CARRY_FORWARD_SAFE |
| R7-01 | a07d66c X 15029 | CARRY_FORWARD_SAFE |
| R7-02 | a07d66c X 28625 | CARRY_FORWARD_SAFE |
| R7-03 | a07d66c X 28326 | CARRY_FORWARD_SAFE |
| R7-06 | a07d66c X 21795 | CARRY_FORWARD_SAFE |
| R7-07 | a07d66c X 31938 | CARRY_FORWARD_SAFE |
| R7-08 | a07d66c X 14424 | CARRY_FORWARD_SAFE |
| R7-09 | a07d66c X 22076 | CARRY_FORWARD_SAFE |
| R7-11 | a07d66c X 31764 | CARRY_FORWARD_SAFE |
| R7-10 | 8545b26 X 13115 | CARRY_FORWARD_SAFE (HUP containment unchanged; a4c8177 hold is cell-12-only) |

Historical VALID FAIL remains: a07d66c R7-10 X 12568. Not overwritten.
No cell is AFFECTED. No automatic rerun.
