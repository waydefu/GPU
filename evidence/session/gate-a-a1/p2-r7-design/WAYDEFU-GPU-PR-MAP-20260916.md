# waydefu/GPU PR map — 2026-09-16

Docs-only records. **Not qualification.**
This repository has **no GitHub status checks** (`check_runs` empty / combined status pending with `total_count=0`).

`termux-x11` fork `debug_build.yml` **artifact CI PASS** (e.g. `0f1e546` **34999213228**, `a7528bd` **35007764673**, `0d72332` **35049545631**, `27d8d1b` **35056388284**) is a **different repo**. It does not green these PRs.

## Graph (after merge)

```
main 5580e73   ← stale 00:49 snapshot (historical)
  ├─ PR #1  r6-pass-0f1e546              d61d7d5   R6 PASS record  → MERGED 0c353dd
  └─ PR #2  b2-exa-timeout-repair-20260916  5c9d12e   B-2 RCA
        └─ PR #3  stall-obs-27d8d1b-20260916  6ed7c42
                   (#3 contains #2; then merged main/#1 taking current STATUS)
                   → MERGED to main
PR #2 CLOSED without merge (subset of #3)
```

| PR | Branch | HEAD | Role | Outcome |
|---|---|---|---|---|
| [#1](https://github.com/waydefu/GPU/pull/1) | `r6-pass-0f1e546` | `d61d7d5` | Historical **R6 PASS** `0f1e546` evidence | **MERGED** |
| [#2](https://github.com/waydefu/GPU/pull/2) | `b2-exa-timeout-repair-20260916` | `5c9d12e` | Historical B-2 RCA on `a7528bd` | **CLOSED without merge** (already in #3) |
| [#3](https://github.com/waydefu/GPU/pull/3) | `stall-obs-27d8d1b-20260916` | post-#1 reconcile | Current stall-obs **STALL_NOT_OBSERVED** + unique R6 files from #1 | **MERGED** |

Conflict resolution on overlapping `AGENTS.md` / `HANDOFF.md` / `README.md` / `STATUS-HANDOFF-20260916.md` / `TEST-MATRIX.md`: keep **#3 current authority**. Unique `runtime-0f1e546/` cells and R6 skills from #1 are kept.

## Verdict labels (do not mix)

- **R6 = PASS** (frozen `0f1e546`)
- **B-2 = BLOCKED** (`0d72332` fail-stop; historical `a7528bd` FAIL kept)
- **stall-obs-01 = STALL_NOT_OBSERVED** — **not** B-2 PASS
- **R7 support artifact** `a7528bd` exists; **R7 qualification NOT STARTED**

Docs merge is **not** R7 qualification and **not** a B-2 PASS.

No test cell was overwritten. No C change. No runtime rerun.
