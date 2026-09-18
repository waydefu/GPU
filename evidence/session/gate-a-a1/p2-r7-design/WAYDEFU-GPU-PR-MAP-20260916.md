# waydefu/GPU PR map — 2026-09-18

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
  └─ PR #9  docs/r8-c1-attempt-05-invalid-20260918
            Record 5a782f6 INSTALLED + R8-C1 attempt-05 INVALID
            https://github.com/waydefu/GPU/pull/9
```

## Verdict labels (do not mix)

- **R6 = PASS** (frozen `0f1e546`)
- **B-2 = PASS** on `7549e36` (`b2-requalification-02`); `b2-requalification-01` INVALID frozen
- **R7 = PASS / COMPLETE 13/13** on `a4c8177` (historical FAIL/INVALID cells remain frozen)
- **R8 design = ACCEPTED / DESIGN_FROZEN** (PR #8)
- **R8 support `5a782f6` = INSTALLED** CI **35321447455**
- **R8-C1 attempt-05 = R8_INVALID `POST_END_OBSERVATION`** (X 14186; frozen; no attempt-06)
- **R8-C1 attempts 01–04** frozen with original classifiers
- **R8 C2–P2 = NOT RUN**
- **R8 overall = NOT PASS**
- **Production Gate A = BLOCKED**
- **R9–R10 = NOT STARTED**

Docs merge is **not** R8 qualification, **not** V1-Core complete, and **not** Production enable.
This snapshot does **not** authorize R9 or a C1 retry.
