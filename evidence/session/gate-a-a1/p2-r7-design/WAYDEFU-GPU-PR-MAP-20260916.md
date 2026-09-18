# waydefu/GPU PR map — 2026-09-19

Docs + 接續套件。**Not qualification.**
This repository has **no GitHub status checks**.

`termux/termux-x11` origin PR is forbidden. Fork `debug_build.yml` artifact CI is a **different repo**.

## Graph

```
main 06eff51  ← merge of PR #8 (R8 design)
  ├─ PR #1  r6-pass-0f1e546                         MERGED 0c353dd
  ├─ PR #2  b2-exa-timeout-repair-20260916          MERGED (historical; map once said closed)
  ├─ PR #3  stall-obs-27d8d1b-20260916              MERGED 2ab76b30
  ├─ PR #4  case-loop-feeaa56-20260916              CLOSED without merge
  ├─ PR #5  b2-pass-7549e36-20260916                MERGED 6c83338
  ├─ PR #6  docs/fdfb1ce-r7-04-handoff-20260917     MERGED c95b893
  ├─ PR #7  docs/v1-core-master-plan-20260917       MERGED ece9f3f
  ├─ PR #8  docs/r8-lifecycle-design-20260917       MERGED 06eff51
  ├─ PR #9  docs/r8-c1-attempt-05-invalid-20260918  OPEN (stale attempt-05 record)
            https://github.com/waydefu/GPU/pull/9
  └─ PR #10 docs/r8-c1-b984ded-adb-restored-20260919
            Record b984ded INSTALLED + ADB restored; C1 attempt-09 NOT RUN
```

## Verdict labels (do not mix)

- **R6 = PASS** (frozen `0f1e546`)
- **B-2 = PASS** on `7549e36` (`b2-requalification-02`); `b2-requalification-01` INVALID frozen
- **R7 = PASS / COMPLETE 13/13** on `a4c8177` (historical FAIL/INVALID cells remain frozen)
- **R8 design = ACCEPTED / DESIGN_FROZEN** (PR #8)
- **R8 support `b984ded` = INSTALLED** CI **35347497216** (re-proven 2026-09-19)
- **R8 host tooling v2 = PUBLISHED** commit `2a14ab2` (live runner `run-r8-one-cell-b984ded-v2.sh`)
- **R8-C1 attempts 01–08 = FROZEN** with original classifiers (attempt-08 `R8_INVALID JUDGE_NOT_PERMITTED / MULTI_BEGIN_x`)
- **R8-C1 attempt-09 cell = NOT RUN** (dir absent). Historical preflight **R8_BLOCKED ADB_CONNECT_FAILED** frozen. ADB **RESTORED** SERIAL `10.191.48.13:46847`
- **R8 C2–P2 = NOT RUN**
- **R8 overall = NOT PASS**
- **Production Gate A = BLOCKED**
- **R9–R10 = NOT STARTED**

Docs merge is **not** R8 qualification, **not** V1-Core complete, and **not** Production enable.
This snapshot does **not** authorize C1, C2, or R9.
