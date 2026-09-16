# Related skills — Gate A R6

Read `HANDOFF.md` first. These skills do not replace live authority.

## Project (parent folder; worktrees do not auto-discover)

| Skill | Use for | Do not use for |
|---|---|---|
| `.cursor/skills/gate-a-r6-design-review/SKILL.md` | Oracle / judge / false-green review | Source write, ADB, CI, install |
| `.cursor/skills/gate-a-r6-present-retirement-implementation/SKILL.md` | Frozen Present helper contract (historical writer) | Re-implementing R6; CI; device cells |
| `.cursor/skills/gate-a-r6-runtime-qualification/SKILL.md` | CI bind, experimental install, D1/D2 cells, verdict | R7, Stable, Production enable |

Worktree Cursor windows may miss `.cursor/skills/`. Read the absolute path
under `/root/projects/GPU加速/.cursor/skills/`.

## Portable (`~/.agents/skills/`; do not copy into `~/.cursor/skills/`)

| Skill | Use for |
|---|---|
| `evidence-first-gate-test-design` | Falsifiable oracles, watermarks, identity binding |
| `verification-integrity` | Exact-head CI, artifact vs live mapping |
| `safe-git-ci-discipline` | Commit/push/CI without weakening gates |
| `evidence-first-debugging` | Crash maps, JIT vs native, first failure |
| `no-guess-search` | Official docs only after getting stuck once |

## Dated packets (not skills)

Current SHA / APK / PID always come from `HANDOFF.md`. These are examples:

- Runtime PASS packet: `evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-0f1e546/GATE-A-P2-R6-RUNTIME-20260916.md`
- Design: `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-DESIGN-20260915.md`
- D2 physical race: `.../GATE-A-P2-R6-D2-INFLIGHT-PHYSICAL-RACE-ANALYSIS-20260915.md`
- 2026-09-15 review that created the design-review skill: `gate-a-r6-design-review/references/R6-D2-REVIEW-20260915.md`
