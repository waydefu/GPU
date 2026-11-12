# R8 PR #8 authority reconciliation — docs only — 2026-09-18

```
R8_AUTHORITY_RECONCILED_DOCS_ONLY
PR: https://github.com/waydefu/GPU/pull/8
state: MERGED (historical design)
R8 status: PROPOSED (NOT DESIGN_FROZEN)
implementation: NOT STARTED
device tests: NOT STARTED
```

## Anchors

Research / fatal-propagation product pin remains **`fdfb1ce44b429897eda17c43bf33fbd37afe67f3`**.
Final R7 runtime authority is **`a4c8177f4b059fddd111717255e9d23cf0e15e1e`** (CI **35295094951**).

## Final R7 changes to retain in R8 matrix

- 8545b26: peer-HUP containment (`x-hup/6` during Done wait)
- abb27a65: Present fault12/13 target arming
- a4c8177: fault12 terminal hold against later high-watermark completion

Wait precedence unchanged:

SUCCESS already derived
> published fatal
> peer HUP
> live-peer genuine timeout

## Regression matrix (docs)

- `R7_10_HUP_CONTAINMENT`
- `GATEA_WAIT_WAKE_CLASS`
- `GATEA_TEST_FAULT_CLASS`
- `R7_P1_PRESENT_TARGET_ARM`
- P1 held-incomplete / high-watermark

## Risks retained

- C2 CloseScreen live-resource construction decision
- R8-D real deferred `GPU_COPY_DONE` overlap construction risk
- No fake scheduling overlap
- No synthetic device completion

R8 remains **PROPOSED**. No source implementation, CI dispatch, install, or device cell in this batch.
