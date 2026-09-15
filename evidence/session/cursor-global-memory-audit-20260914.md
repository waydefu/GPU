# Cursor global context / memory audit — 2026-09-14

Scope: read-only inspection and migration recommendation. No authentication files, tokens, MCP payloads, chat contents, or private transcript contents were read. No Cursor/Codex/Hermes global configuration was changed.

## Executive verdict

```text
MODEL EFFORT: NOT THE PRIMARY PROBLEM
DURABLE GLOBAL ENGINEERING GUIDANCE: FILE-BACKED LAYER ABSENT
GPU PROJECT AUTHORITY: PRESENT VIA /root/projects/GPU加速/AGENTS.md
MCP SELECTION: MISALIGNED FOR GPU (firebase ready; serena not loaded)
TOOL CATALOG CACHE: LARGE
RECOMMENDATION: CURATED PORT, NOT RAW HERMES MEMORY COPY
```

The observed problem is mainly context architecture, not evidence that Grok 4.6 has no reasoning ability. Cursor is configured for Grok 4.6 high effort with fast mode off, but the reusable guidance/tool layers are inverted for this task: no file-backed global Cursor rules or skills were found, while Firebase is the ready custom MCP and Serena is not loaded.

## 1. Observed installation and model settings

| Item | Observed |
|---|---|
| Cursor Desktop | `3.18.25` (`/usr/share/cursor/resources/app/package.json`) |
| Cursor Agent CLI | `2026.09.02-c22c1a3` |
| Selected model | `grok-4.6` / `cursor-grok-4.6-high` |
| Effort | `high` |
| Fast mode | `false` |
| Max mode | `false` |
| Explore subagent model | `default` |
| Approval mode | `allowlist` |
| Sandbox | disabled |

The account also exposes `cursor-grok-4.6-xhigh`, `gpt-5.6-sol-*`, `gpt-5.6-luna-*`, and other models. Model switching may help architecture work, but it will not correct stale authority, missing durable rules, or irrelevant tools.

## 2. Durable guidance layers

Filesystem inspection found:

```text
~/.cursor/rules/**/*.mdc: 0
~/.cursor/skills/**/SKILL.md: 0
project .cursor/rules/**/*.mdc: 0
project SKILL.md: 0
```

Two global custom agents exist:

- `~/.cursor/agents/clinic-luna-scout.md`
- `~/.cursor/agents/clinic-luna-worker.md`

Both are explicitly scoped to `waydefu/clinic`; they are not GPU project memory and should not be generalized to Gate A.

Cursor's official `/context/memories` documentation currently describes Rules. Reliable persistence is therefore supplied by:

- User Rules (UI/global);
- Project Rules (`.cursor/rules/*.mdc`);
- `AGENTS.md`;
- Skills;
- explicit chat resume/transcript context.

No local CLI command exposes the existing UI User Rules for read-only export. Their presence/content is therefore **not observable** from this audit. The conclusion is limited to the file-backed layers above; it does not claim the remote/UI User Rules field is empty.

## 3. GPU project context

Cursor has a project cache at:

`/root/.cursor/projects/root-projects-GPU`

The IDE state recently referenced:

- `/root/projects/GPU加速/HANDOFF.md`
- `/root/projects/GPU加速/TEST-MATRIX.md`
- `/root/projects/GPU加速/README.md`

The shared project root `AGENTS.md` was updated before this audit to route Cursor, Codex, and Hermes through the same authority chain. This is the correct place for changing Gate state, PIDs, commits, and hard project redlines. Such volatile facts must not be copied into global Cursor memory.

The CLI state field `workerIdsByDisplayName` has no GPU entry. This field belongs to Cursor self-hosted/persistent workers; its absence is **not** evidence that ordinary IDE project context is broken and must not be used as a root-cause claim.

The GPU project cache contains 22 transcript JSONL files, including 13 under subagent paths. Those are historical session artifacts. They do not replace an authority file and should not be assumed to load automatically into a fresh agent session.

## 4. MCP/tool audit

Generated GPU project cache descriptors:

```text
MCP server directories: 10
Tool descriptors: 193
Prompt descriptors: 5
Resource descriptors: 17
```

Server directories include app control, browser, GitHub, Gmail, Calendar, Drive, Notion, Slack, Firebase, and Serena. Cache presence alone does not prove all 193 tools are injected into every turn.

The authoritative CLI status is narrower:

```text
firebase: ready
serena: not loaded (needs approval)
```

For Gate A C/C++ work this is misaligned:

- Firebase contributes 45 cached tool descriptors and is unrelated to the current renderer/Xserver investigation.
- Serena is the relevant symbol-navigation tool, but it is not loaded.
- The existing Gate A Serena project configuration has a known historical risk: it was registered as Java/read-write rather than reliable C/C++ read-only. Enabling it before correcting/validating that project is not recommended.
- Globally disabling Firebase would affect Clinic and other Firebase work, so this audit does not do it.

## 5. Why the current experience feels unreliable

### 5.1 Rules are present at project level but thin globally

A fresh GPU chat can read `AGENTS.md`, but a new unrelated project does not inherit Hermes-style evidence discipline, two-failure research rule, secret boundaries, final verification, or high-risk escalation. The model must reconstruct those expectations from each prompt.

### 5.2 Tool availability is not scoped to the task

The only ready custom MCP in CLI is Firebase, while source navigation is unavailable. Even when irrelevant tools are not invoked, a broad tool selection surface can make routing less predictable. The exact amount of prompt-token overhead is not observable here and is not claimed.

### 5.3 Long GPU sessions depend too much on chat compression

Historical transcript files exist, but current truth changes frequently. If a model resumes a long chat instead of re-reading `HANDOFF.md`, it can combine old PIDs, old artifacts, and superseded hypotheses. This is a context-authority defect, not fixed by increasing reasoning effort.

### 5.4 High effort is not maximum architecture review

The current model is Grok 4.6 High, not XHigh, and `maxMode=false`. For routine source reading High is adequate. For Gate A cross-thread lifecycle decisions, a higher model/reasoning lane can be justified—but only after context and tools are corrected.

## 6. What to port from Hermes

### Port as a short global User Rule

Only stable, cross-project behavior:

- verify current repo/branch/status/versions before conclusions;
- evidence hierarchy and explicit `PROVEN / OBSERVED / INFERRED / UNKNOWN` labels;
- stop blind retry after two failures and research before a third approach;
- preserve user dirty changes and avoid destructive Git;
- do not read/print secrets;
- root-cause fixes plus regression tests;
- required tests/CI remain hard gates;
- ask before merge, production, IAM/secrets, destructive operations, breaking changes, or large architecture work;
- completed work must report changed, verification, remaining, and next;
- when a project has `AGENTS.md`/`HANDOFF.md`, those files own volatile project state.

Keep this rule short. Do not paste Hermes' full system prompt, tool catalog, profile semantics, or current memory snapshot.

### Port as portable Skills

Good candidates, rewritten for Cursor's tools:

1. `evidence-first-debugging`
2. `verification-integrity`
3. `safe-git-ci-discipline`
4. optionally `native-gpu-lifecycle-audit` as a project skill, not global

Use `~/.agents/skills/` if the goal is one portable skill set shared by Cursor and Codex. Do not copy Hermes skills verbatim when they reference Hermes-only tools (`skill_view`, `patch`, vault tools, delegate APIs, or Hermes profiles).

### Keep project-specific

Do not place these in global memory:

- Stable PID or current ADB endpoint;
- Gate A commit/CI/APK hash;
- R3 result or next stage;
- package/display redlines specific to this project;
- exact worktree and evidence paths.

They stay in `/root/projects/GPU加速/AGENTS.md`, `HANDOFF.md`, `TEST-MATRIX.md`, and gate documents.

## 7. Recommended optimization order

### Phase 1 — durable behavior, no tool changes

1. Draft a compact Cursor User Rule from the stable Hermes engineering policies.
2. Create three portable skills under `~/.agents/skills/` for Cursor + Codex.
3. Keep GPU volatile truth only in the already-synchronized root `AGENTS.md` chain.
4. Start new GPU chats instead of resuming heavily compressed historical threads when authority has changed.

### Phase 2 — GPU tool scoping

1. Validate/fix the Gate A Serena project as C/C++ read-only, without touching active sessions.
2. Approve Serena only for a fresh GPU source-analysis session.
3. Do not globally disable Firebase unless the user accepts the impact on Clinic.
4. Prefer project-specific `.cursor/cli.json` MCP deny/allow rules where supported; permissions reduce accidental calls but may not remove all descriptor context.
5. If true per-workspace MCP enablement is required, use a separate Cursor profile/config boundary rather than toggling global Firebase back and forth.

### Phase 3 — model lane

- Routine bounded implementation: Grok 4.6 High can remain.
- Gate A architecture/cross-thread lifecycle: use Grok 4.6 XHigh or GPT-5.6 Sol XHigh/Max if available and cost is acceptable.
- Mechanical lookup can use Luna, but final architecture authorization remains with the primary reviewer.

Changing the model before Phases 1–2 may produce somewhat better reasoning, but it will still operate with the same stale/underspecified context.

## 8. Decision boundary

Recommended next action:

```text
APPROVE PHASE 1 ONLY
- create one reviewed User Rule draft (do not overwrite UI state automatically)
- create three portable ~/.agents/skills for Cursor + Codex
- verify their schemas and discovery
- no MCP enable/disable and no model change
```

A later, separate approval should cover Phase 2 because changing MCP approval/configuration can affect other projects. No global configuration change was made by this audit.
