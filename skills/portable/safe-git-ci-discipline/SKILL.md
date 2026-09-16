---
name: safe-git-ci-discipline
description: Change Git and CI safely without weakening gates.
version: 0.1.0
author: waydefu, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# Safe Git and CI Discipline

Preserve user work, keep commits reviewable, and fix CI root causes instead of bypassing them.

## When to Use

- Any repository edit, branch, commit, push, PR, or CI investigation.
- Work involving multiple agents or shared worktrees.

## Before Editing

1. Read repository governance and project instructions.
2. Record repository root, branch, full HEAD, remotes, status, staged/unstaged files, and submodule state.
3. If unexpected dirty files exist, stop; never overwrite, restore, reset, or delete them.
4. For formal or medium/large work, use an isolated branch/worktree. One writer owns one worktree.
5. Define acceptance criteria and the exact tests that will prove them.

## Editing

- Make the smallest change that resolves the proven root cause.
- Match existing patterns; do not add dependencies or refactor unrelated code.
- Add a regression test before bug-fix code and verify RED→GREEN.
- Keep generated, temporary, secret, credential, and local environment files out of commits.
- Review every changed file and run diff whitespace checks before commit.

## Commits

Use atomic Conventional Commits. The message body records why, root cause, behavioral impact, verification, and breaking-change status. Do not mix unrelated cleanup.

Never use force push, destructive reset, history rewrite, admin bypass, or force merge. Ask before altering shared/pushed history.

## CI

1. Bind the run to the exact pushed HEAD.
2. Find the first meaningful failing job and preserve its logs/environment.
3. Fix the root cause; do not skip, disable, ignore, lower thresholds, add waivers, or rerun deterministic failures until green.
4. One diagnostic rerun is allowed only for suspected flaky infrastructure and must preserve the first failure evidence.
5. Required tests, lint, typecheck, formatting, security, build, and project gates remain completion requirements.
6. A PR with missing/queued checks is not green.

## Approval Boundaries

Ask before merge, production deployment/change, database migration/schema change, secrets/auth/IAM changes, branch protection or CI-threshold changes, new runtime dependencies, major upgrades/replacements, breaking APIs/data formats, destructive deletion, payment, or external publication.

## Completion

Report:

```text
BRANCH / HEAD
FILES CHANGED
ROOT CAUSE
COMMITS
VERIFICATION (commands + exit codes)
REQUIRED CI
DOCUMENTATION IMPACT
RISKS / FOLLOW-UP
DECISION REQUIRED
```

Done requires a clean intended diff, regression proof, all required gates green on the exact head, no debug residue or accidental TODOs, and a final diff review. Stop before merge unless explicitly approved.
