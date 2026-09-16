# waydefu/GPU PR map — 2026-09-16

Docs-only records. **Not merged. Not qualification.**
This repository has **no GitHub status checks** (`check_runs` empty / combined status pending with `total_count=0`).

`termux-x11` fork `debug_build.yml` **artifact CI PASS** (e.g. `0f1e546` **34999213228**, `a7528bd` **35007764673**, `0d72332` **35049545631**, `27d8d1b` **35056388284**) is a **different repo**. It does not green these PRs.

## Graph

```
main 5580e73   ← stale 00:49 snapshot (device then written as 95e6f96)
  ├─ PR #1  r6-pass-0f1e546              d61d7d5   R6 PASS record
  └─ PR #2  b2-exa-timeout-repair-20260916  5c9d12e   B-2 RCA + timeout-repair excerpt
        └─ PR #3  stall-obs-27d8d1b-20260916  78e3f77   = 5c9d12e + stall-obs
                   (#3 contains #2; does NOT contain #1)
```

| PR | Branch | HEAD | Commits vs main | Role | Overlap |
|---|---|---|---|---|---|
| [#1](https://github.com/waydefu/GPU/pull/1) | `r6-pass-0f1e546` | `d61d7d5` | 1 | Historical **R6 PASS** `0f1e546` | Independent of #2/#3 |
| [#2](https://github.com/waydefu/GPU/pull/2) | `b2-exa-timeout-repair-20260916` | `5c9d12e` | 1 | Historical B-2 RCA on `a7528bd` (body still says patch uncommitted; later `0d72332` superseded that) | **Subset of #3** |
| [#3](https://github.com/waydefu/GPU/pull/3) | `stall-obs-27d8d1b-20260916` | `78e3f77` | 2 | Current stall-obs **STALL_NOT_OBSERVED** record | Superset of #2; not #1 |

## Verdict labels (do not mix)

- **R6 = PASS** (frozen `0f1e546`)
- **B-2 = BLOCKED** (`0d72332` fail-stop; historical `a7528bd` FAIL kept)
- **stall-obs-01 = STALL_NOT_OBSERVED** — **not** B-2 PASS
- **R7 support artifact** `a7528bd` exists; **R7 qualification NOT STARTED**

## Recommendation (not executed)

- **Keep #1 open** as the frozen R6 PASS docs snapshot. Do not mix it into #3.
- **Keep #3 open** as the current docs snapshot. Do not merge without new authorization.
- **Close #2 without merge** when convenient: every commit is already in #3. Leave the branch.
- Do **not** merge #1 and #3 together without an explicit docs-reconciliation; both rewrite `STATUS-HANDOFF-20260916.md` / `HANDOFF.md`.

No test cell was overwritten. No C change. No runtime rerun.
