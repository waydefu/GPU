---
name: gate-a-r6-runtime-qualification
description: >-
  Qualify Gate A R6 CI artifacts, experimental-only install, and D1 /
  D2-INFLIGHT / D2-OOM device cells without false PASS. Use when running R6
  runtime, installing com.waydefu.x11gpu, binding APK SHA256 / Build ID /
  signer, judging Present GPU-copy ownership, dual-branch D2
  (busy-reject vs quiescent-admit), event 32/33/34, fail-stop teardown
  classification, or writing an R6 PASS/BLOCKED/NOT YET VERIFIED verdict.
paths:
  - "AGENTS.md"
  - "HANDOFF.md"
  - "TEST-MATRIX.md"
  - "evidence/session/gate-a-a1/p2-r3-xpump-runtime/**"
  - "evidence/session/gate-a-a1/p2-r6-ci-*/**"
  - "evidence/session/gate-a-a1/p2-r6-design/**"
---

# Gate A R6 Runtime Qualification

Execution skill for R6 after source exists. Not permission to start R7, touch
Stable, weaken a judge, or treat historical cells as current.

Related skills: [references/RELATED-SKILLS.md](references/RELATED-SKILLS.md).
ADB / artifact traps: [references/ADB-AND-ARTIFACT.md](references/ADB-AND-ARTIFACT.md).
Review discipline: `../gate-a-r6-design-review/SKILL.md`.
Writer contract (complete on `0f1e546`; do not re-run):
`../gate-a-r6-present-retirement-implementation/SKILL.md`.

## When to Use

- A new R6 commit needs fork CI, artifact bind, experimental install, or
  D1 / D2-INFLIGHT / D2-OOM.
- A judge reports PASS and the cell may be the wrong artifact, wrong branch,
  or env-only OOM.
- Writing the Traditional Chinese R6 verdict packet.

Do not use to reopen P0/P1/P2-A/P2-B.1/P2-B.2, enable Production Gate A,
implement R7, or rewrite historical FAIL files into PASS.

## Authority First

Live state overrides this skill. Read in order:

1. `AGENTS.md`
2. `HANDOFF.md` — then the newest `HANDOFF-NEXT-AGENT-*.md` it names
3. `TEST-MATRIX.md`
4. `GATE-A-P2-R6-DESIGN-20260915.md`
5. Exact worktree: `git rev-parse HEAD`, `status --short`, `diff --check`,
   remotes (`fork` vs `origin`)

Never infer current SHA, APK hash, Build ID, ADB serial, or Stable PID from
memory. If evidence is absent, write `UNKNOWN` or `NOT VERIFIED`.

## Hard Safety

- Experimental only: `com.waydefu.x11gpu` / `DISPLAY :3`.
- Never kill, reinstall, or qualify `com.termux.x11` / `:1`.
- No HDMI qualification, Production enable, PR, merge, origin push, or force.
- Fork remote only when current governance authorizes it.
- R7 (`TERMUX_X11_GATEA_TEST_FAULT`) stays absent from the R6 artifact.

## Invariant

Once a Present GPU copy is scheduled, GPU completion must be proven before
ACK, pending decrement, ref release, `present_pixmap_idle`, pixmap destroy,
scrap, or CPU reuse. Timeout / renderer loss / unknown completion = FAIL-STOP,
not ACK / fallback / normal cleanup.

`gpu_copy_dst_buffer == NULL` is a valid root destination.

Event 32 `PRESENT_EARLY_ACK` remains forbidden. Do not repurpose it.

## Pre-Edit Gate

READ-ONLY until this checkpoint exists. Treat existing retirement C as
untrusted until reconstructed.

```text
PRE-EDIT VERDICT: READY | BLOCKED
worktree / branch / HEAD / dirty files
ownership lifecycle reconstructed
all raw Present ACK sites
scrap / destroy / timeout / loss / CloseScreen
judge reviewed (do not weaken)
xserver.patch duplication reviewed
```

If any core ownership path is unknown: `BLOCKED`. Do not edit around it.

Raw Present `lorieGpuCopyAck` outside `present_gpu_copy_retire_or_fatal` is
`BLOCKED`.

## Review Paths Separately

| Path | Required |
|---|---|
| A pending + incomplete + renderer healthy + requeue OK | remain pending; no ACK |
| B pending + incomplete + natural requeue fails | ACK only after requeue-fail evidence **and** completion cover |
| C pending + renderer unavailable | FAIL-STOP if completion unproven |
| D pending + already completed | retire if cover is valid |
| E first schedule success then later requeue fail | pending authoritative immediately; no early ACK |

Renderer may complete before the X thread observes requeue failure. Do **not**
require `REQUEUE_FAILED` before `COMPLETED`. Require:

```text
PRESENT_CALLBACK(S,G) < REQUEUE_FAILED(S,G)
PRESENT_CALLBACK(S,G) < COMPLETED(role=RENDERER, G, T>=S)
max(REQUEUE_FAILED, COMPLETED) < ACK_AFTER_COMPLETED
```

## D2 Dual Branch

Do not use the historical reject-only oracle as universal truth.

`completedSerial` is a watermark `T >= S`. `LEASE` serial may be 0; `PUBLISH`
assigns the GPU serial. Telemetry `seq` is order authority, not logcat lines.
A Composite callback alone is not admission.

**BUSY-REJECT:** immediate Composite → reason-1 reject before cover → later
valid Composite + direct lifecycle.

**QUIESCENT-ADMIT:** cover before first target `LEASE serial=0` → complete
immediate lifecycle → later Composite REQUEST/CALLBACK → second complete
lifecycle.

The later-Composite + second lifecycle requirement is a **PRODUCT INVARIANT**
(DESIGN §6.2 / §9). Classify before changing the judge:

```text
PRODUCT INVARIANT
FIXTURE-STRENGTHENING ONLY
UNKNOWN / REQUIRES AUTHORITY DECISION
```

If status cannot be established: **STOP**. Never weaken an oracle to obtain PASS.

## Host Gates (before CI)

Run against the **exact worktree**, not the historical `src/f8-ahb-gatea-r6`
default:

```text
python3 test-judge-r6-design.py
bash test-r6-design-bind.sh
python3 verify_r6_design_impl.py <retire-worktree>
python3 test-present-gpu-copy-retirement.py <retire-worktree>
bash -n harness/bind/install scripts
git diff --check
```

Judge adversarial cases must include missing COMPLETED, wrong role/generation/
pair/transaction, duplicate/conflicting/gap seq, ring-fill PASS, `T > S` PASS,
logcat reorder PASS, software fallback FAIL, env-without-event-33 FAIL,
event 32 FAIL.

`xserver.patch`: normalize **Present hunks only**. Preserve dialect. Do not
regenerate the entire patch. Prove apply + reverse vs submodule `65d790b`.

## CI / Artifact

Local HEAD = fork HEAD = workflow `headSha`. Origin branch must stay absent
unless a new grant says otherwise.

Qualify the APK from **that run only**:

- package `com.waydefu.x11gpu`, versionName contains the candidate SHA prefix
- ABI set includes `arm64-v8a`
- APK SHA256, signer continuity, embedded Build ID = unstripped Build ID
- R6 literals present; `TERMUX_X11_GATEA_TEST_FAULT` absent
- `present_gpu_copy_retire_or_fatal` in unstripped nm (filter must include
  that symbol name; a `gateA`-only grep is a verifier bug)

GitHub artifact ZIP digest is **not** the APK SHA256. Ambiguous provenance:
STOP. Do not install.

## Install / Runtime

Install only after QUALIFIED, experimental only. Capture Stable + experimental
package state before and after. Prove Stable versionName, lastUpdateTime, and
`:1` PID unchanged.

No silent retries. First failure is evidence. Classify:

```text
PRODUCT/SOURCE | TEST CONSTRUCTION | ORACLE | PLATFORM/JIT | ARTIFACT/PROVENANCE | UNKNOWN
```

Historical cells are immutable. New candidate → new `runtime-<sha>/`.

### D1

Correct client, exact pixels, direct semantic success, no invalid fallback,
no fatal/timeout, valid telemetry, OOM env unset, Stable untouched.

### D2-INFLIGHT

Accept **one** proven legal branch: BUSY-REJECT or QUIESCENT-ADMIT. Bind
generation, role, Present serial, telemetry seq, pair, artifact.

### D2-OOM

`TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1` must appear in X environ **and**
event 33 must fire for serial S. Env alone is not evidence. No event 32.
ACK after both cover and requeue-fail. Later direct Composite lifecycle +
exact pixels.

## Fail-Stop Matrix

After runtime, classify each path with exactly one of:

```text
DEVICE-PROVEN | HOST-PROVEN | SOURCE-PROVEN | NOT VERIFIED
```

Never convert SOURCE-PROVEN into DEVICE-PROVEN. If DESIGN demands a device
proof that is still absent, R6 is `NOT YET VERIFIED`.

Timeout / renderer-loss / scrap / destroy / CloseScreen-with-pending are
required **behaviors**, not automatic extra device cells unless DESIGN §9
lists them. Happy-path D1/D2-OOM does not prove timeout.

## ART JIT

Startup SIGSEGV with PC in `dalvik-jit-code-cache`, `si_addr=0`: OBSERVED,
not a C ownership bug. Do not patch pump/waiter/DDX. Bounded rerun only with
explicit authorization. If rerun PASS: `NON-REPRODUCED / ROOT CAUSE NOT PROVEN`.
Never write `FIXED` without proof.

## Verdict

Choose exactly one: `R6 PASS` | `R6 BLOCKED` | `R6 NOT YET VERIFIED`.

Historical results cannot fill gaps for a new artifact. Host green ≠ R6 PASS.
Even if R6 PASS: **STOP BEFORE R7**. Production Gate A stays BLOCKED.

Final report: Traditional Chinese, structure in
[references/REPORT-TEMPLATE.md](references/REPORT-TEMPLATE.md).
