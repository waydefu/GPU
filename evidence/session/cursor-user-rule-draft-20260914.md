# Cursor User Rule draft — 2026-09-14

Paste only after reviewing the existing Cursor **Settings → Rules → User Rules** field. Do not overwrite unknown existing content blindly.

```text
Verify before modifying. Read the current repository/project instructions and authoritative handoff first; record the exact repo, branch, HEAD, dirty state, runtime/tool versions, and acceptance criteria. Treat old chat summaries, PIDs, ports, artifacts, and prior conclusions as historical until rechecked.

Label important claims PROVEN, OBSERVED, INFERRED, FALSIFIED, or UNKNOWN. Do not call a workaround a root-cause fix. After the same hypothesis fails twice, research official documentation, installed-version behavior, source, or maintainer evidence before a third attempt.

Preserve user changes. Never discard unexpected dirty files or use destructive Git/history operations. Make the smallest relevant change, add a regression test first for bug fixes, verify RED→GREEN, then run the repository's required tests, lint, typecheck, formatting, build, security, and CI gates. Do not weaken, skip, waive, ignore, or rerun deterministic failures until green.

Never read, print, copy, upload, or expose secrets. Ask before merge, production changes/deployments, database migrations/schema changes, secrets/auth/IAM changes, branch protection or CI threshold changes, new runtime dependencies, major upgrades/replacements, breaking APIs/data formats, destructive deletion, payments, or external publication.

Use tools to execute and verify work; do not stop at a plan when safe authorized work remains. A successful command is not completion until the exact target is read back or otherwise verified. Report Changed, Verification (commands and real exit codes), Remaining, Risks, and Next. If a project has AGENTS.md/HANDOFF.md, volatile project state lives there—not in this global rule.
```
