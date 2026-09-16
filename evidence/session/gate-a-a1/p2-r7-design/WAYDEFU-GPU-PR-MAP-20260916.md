# waydefu/GPU PR map — 2026-09-16

Docs-only records. **Not qualification.**
This repository has **no GitHub status checks** (`check_runs` empty / combined status pending with `total_count=0`).

`termux/termux-x11` origin PR is forbidden. Fork `debug_build.yml` artifact CI is a **different repo**.

## Graph

```
main 2ab76b30  ← merge of PR #3 (contains unique R6 files from #1)
  ├─ PR #1  r6-pass-0f1e546                 MERGED 0c353dd
  ├─ PR #2  b2-exa-timeout-repair-20260916  CLOSED without merge (subset of #3)
  ├─ PR #3  stall-obs-27d8d1b-20260916      MERGED 2ab76b30
  └─ PR #4  case-loop-feeaa56-20260916      OPEN (docs snapshot)
```

| PR | Branch | Role | Outcome |
|---|---|---|---|
| [#1](https://github.com/waydefu/GPU/pull/1) | `r6-pass-0f1e546` | Historical **R6 PASS** `0f1e546` | **MERGED** |
| [#2](https://github.com/waydefu/GPU/pull/2) | `b2-exa-timeout-repair-20260916` | Historical B-2 RCA | **CLOSED without merge** |
| [#3](https://github.com/waydefu/GPU/pull/3) | `stall-obs-27d8d1b-20260916` | Historical stall-obs **STALL_NOT_OBSERVED** | **MERGED** |
| [#4](https://github.com/waydefu/GPU/pull/4) | `case-loop-feeaa56-20260916` | `feeaa56` **CASE_LOOP** + hardened `7549e36` **not installed** | **OPEN** (do not merge in this task) |

## Verdict labels (do not mix)

- **R6 = PASS** (frozen `0f1e546`)
- **B-2 = BLOCKED** (`0d72332` fail-stop; historical `a7528bd` FAIL kept)
- **feeaa56 stall-obs-01 = CASE_LOOP DEVICE-PROVEN** — **not** a B-2 PASS
- **CASE_LOOP initial `327b028` + hardened `7549e36` = COMMITTED, not installed**
- **R7 support artifact** `a7528bd` exists; **R7 qualification NOT STARTED**

Docs merge is **not** R7 qualification, **not** a B-2 PASS, and **not** device install of `7549e36`.

No APK / ELF / logcat. No C tree. No runtime rerun in this PR.
