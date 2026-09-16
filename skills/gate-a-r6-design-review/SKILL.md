---
name: gate-a-r6-design-review
description: Review Gate A R6 ownership tests without false verdicts.
paths:
  - "AGENTS.md"
  - "HANDOFF.md"
  - "TEST-MATRIX.md"
  - "evidence/session/gate-a-a1/**"
  - "src/f8-ahb-gatea-*/lorie/src/main/cpp/**"
---

# Gate A R6 Design Review

Use this skill to review Gate A R6 cross-operation ownership, Present requeue
failure, completion telemetry, runtime judges, fixtures, and artifact binding.
This skill is review discipline, not permission to modify source, push, install,
or run a device cell.

Related skills: `../gate-a-r6-runtime-qualification/references/RELATED-SKILLS.md`.
Runtime/CI/install: `../gate-a-r6-runtime-qualification/SKILL.md`.
Writer contract (complete; do not re-run):
`../gate-a-r6-present-retirement-implementation/SKILL.md`.

## When to Use

- R6-D1 or R6-D2 fails, is redesigned, or is proposed for authorization.
- `completedSerial`, Present COPY, `queue_vblank`, pending references, or an
  `EVENT_COMPLETED_SERIAL` oracle changes.
- A judge or harness reports PASS and the evidence may be incomplete, stale, or
  associated with the wrong serial, generation, buffer pair, artifact, or order.
- Before approving a new R6 C implementation, CI artifact, or device cell.

Do not use this skill to reopen P0/P1/P2-A/P2-B.1/P2-B.2, change the narrow
Composite predicate, touch Stable, or start R7.

## Authority First

Read these files in order every session; do not use remembered state:

1. `AGENTS.md`
2. `HANDOFF.md`
3. `TEST-MATRIX.md`
4. The newest `HANDOFF-NEXT-AGENT-*.md` named by current `HANDOFF.md`
5. `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-DESIGN-20260915.md`
6. The newest R6-D2 HOLD/root-cause packet named by `HANDOFF.md`
7. `references/R6-D2-REVIEW-20260915.md` for the review that created this skill
8. `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-PRESENT-RETIREMENT-IMPLEMENTATION-PLAN-20260915.md`
   when planning the lifecycle correction; the plan is not authorization

Bind source and runtime separately:

- Record exact worktree, branch, HEAD, `git status --short`, and
  `git diff --check`.
- Record installed APK version, source SHA, APK hash, Build ID, package, and
  runtime cell only from current authority/evidence.
- Never claim a local commit is on the device until the mapped APK proves it.
- Historical FAIL cells are immutable evidence; never overwrite or silently
  retry them.

Completion criterion: every conclusion names the exact source snapshot and the
exact runtime artifact, or is explicitly labeled source-only.

## Test-Design Method

### 1. Turn each claim into a falsifiable oracle

For every claimed invariant, write five columns before implementing the test:

| Field | Required content |
|---|---|
| Claim | One precise ordering, ownership, or result statement |
| Authoritative signal | State/event that directly proves it |
| False-green case | Missing/wrong evidence that must FAIL |
| False-red boundary | Legal batching/reordering that must PASS |
| Binding | Generation, role, serial, client sequence, buffer pair, artifact |

Do not accept timing, client success, X liveness, or exact pixels as a substitute
for a missing ownership/completion signal. They prove different things.

### 2. Derive tests from the state machine, not from the happy log

Trace:

```text
schedule
→ pending/ref acquisition
→ queue publish
→ renderer consume
→ GPU fence terminal
→ completedSerial watermark
→ Present/direct result
→ ACK/pending--/ref release
→ CPU reuse
```

For every early return, timeout, renderer loss, requeue failure, callback, and
teardown path, answer:

1. Who owns source and destination now?
2. Which reference and pending count still protect them?
3. What exact event proves GPU quiescence?
4. Can CPU access, pixmap idle, or destruction happen before that event?
5. On uncertainty, does the process fail-stop before release?

Completion criterion: no path reaches ACK, pending decrement, ref release,
`present_pixmap_idle`, CPU access, or ordinary cleanup while completion is
uncertain.

Mechanically enumerate every call site that can ACK, decrement pending, release a
reference, mark idle, scrap, abort, destroy, disconnect, or tear down the owner.
Do not stop after fixing the reported branch: cleanup and destructor paths often
contain a second early release. Prefer one audited retirement helper, and make a
static test fail if raw release calls appear outside it.

### 3. Test both false green and false red

Every judge change needs at least:

- Missing required event → FAIL.
- Wrong role → FAIL.
- Wrong generation → FAIL.
- Wrong buffer pair/client transaction → FAIL.
- Legal completion watermark `T > S` → PASS when `T` covers `S`.
- Event log lines physically reordered but telemetry `seq` correct → PASS.
- Duplicate/conflicting sequence → FAIL.
- Missing prefix or internal sequence → FAIL unless a ring dump fills it.
- Software-fallback pixels without required direct SUCCESS → FAIL.
- Historical known PASS remains PASS.
- Historical known FAIL remains FAIL.

A test suite that only reproduces the expected new PASS is incomplete.

### 4. Exercise the real boundary

Prefer tests that import and call the real judge functions and run the real bind
script. A look-alike parser or copied condition does not verify production logic.
Compile the actual fixture with warnings as errors. Run the source verifier
against the exact worktree and ensure it checks ordering, not just substring
presence.

### 5. Separate construction from verdict

The fixture must positively prove that the intended branch occurred. Merely
setting an environment variable does not prove the one-shot was consumed.
Likewise, a missing reject can mean the in-flight state was never constructed,
not that admission is broken.

Add a branch marker for each forced path and bind it to the target serial and
generation. The judge must reject a trace that could have come from the normal
path.

## R6 Hard Rules

1. **`completedSerial` is a watermark.** Present serial `S` is covered by the
   first renderer completion in the same generation with `serial >= S`; exact
   equality is not required because one fence can complete a batch.
2. **Telemetry `seq` is ordering authority.** Never use logcat line order across
   X and renderer threads. Sort by sequence, require uniqueness, and require the
   complete expected range. A gap without an authoritative ring fill is FAIL.
3. **Completion cover is mandatory.** It must have renderer role, the same
   generation, and a covering serial. Absence is never inferred as success.
4. **Bind the transaction.** Pair Present REQUEST and CALLBACK by client
   sequence. Pair reject and later direct SUCCESS by destination buffer ID (and
   source ID when available). An unrelated SUCCESS cannot close the cell.
5. **No early ownership return.** Keep pending counts and extra references until
   GPU completion is proven. ACK and `present_pixmap_idle` occur only afterward.
6. **Timeout/loss fail-stops.** Renderer loss, timeout, or uncertain completion
   must publish fatal and halt without ACK, pending--, ref release, relock,
   fallback, or normal teardown.
7. **No X-client pump during terminal wait.** A bounded Present wait may rely on
   the renderer thread, but must not dispatch X clients recursively.
8. **Fault injection needs positive proof.** Exact env presence is necessary but
   insufficient; emit an event showing the post-schedule requeue-fail branch ran.
9. **Post-cover recovery must be real.** The later Composite must execute the
   intended direct path and reach same-generation SUCCESS on the target pair;
   pixels alone may come from software fallback.
10. **Default OFF remains behaviorally inert.** PROTO unset/0 must emit no new
    telemetry and preserve existing behavior.
11. **Exact pixels only.** `±1` UNORM is FAIL.
12. **Evidence is immutable.** New APKs use new `runtime-<sha>/` directories,
    fresh X PIDs, exact fixture hashes, and exact artifact identity.
13. **No silent retry.** Preserve the first failure, classify construction versus
    product failure, and obtain explicit authorization before another device cell.
14. **Stop at authorization boundaries.** Ownership/fence/lifecycle changes,
    fork push, CI, install, ADB runtime, R7, PR, merge, origin push, Stable, and
    HDMI follow the current governance grants; never infer permission.

## Required OOM Design Shape

The safe bounded-wait design is:

```text
post-schedule queue_vblank failure
→ retain pending counts and extra refs
→ positively trace requeue-fail branch
→ wait with one monotonic 2000 ms budget for completedSerial >= S
→ success: ACK, pending--, ref release, then pixmap idle
→ timeout/renderer loss: generation fatal + process halt, no release
```

Do not expose a raw wait API that lets the Present caller forget fail-stop. Use a
single exported wrapper from `InitOutput.c`, for example a
`lorieGpuCopyWaitForPresentOrFatal(serial)` contract, and declare only that
wrapper in `present_priv.h`. The existing `lorieGpuCopyWait` is translation-unit
local and cannot be called directly from `present_execute.c`.

For runtime proof, preserve historical event 32 as forbidden
`PRESENT_EARLY_ACK`; do not silently repurpose it. Prefer append-only markers:

```text
PRESENT_REQUEUE_FAILED
PRESENT_ACK_AFTER_COMPLETED
```

Completion may race ahead of the requeue-fail marker on a fast renderer, so do
not require `REQUEUE_FAILED < COMPLETED`. Require both after the Present callback,
then require ACK after both:

```text
PRESENT_CALLBACK(S,G) < REQUEUE_FAILED(S,G)
PRESENT_CALLBACK(S,G) < COMPLETED(T>=S,G,RENDERER)
max(REQUEUE_FAILED, COMPLETED) < ACK_AFTER_COMPLETED
ACK_AFTER_COMPLETED < later target Composite request/callback/direct SUCCESS
```

Any event-number addition or change to the ownership path is a new architecture
boundary and requires explicit approval before source mutation.

## Judge Acceptance Checklist

- [ ] Events sorted by `seq`, not file order.
- [ ] Sequence starts at 0 for a fresh non-overflowed cell and is contiguous
      through the maximum sequence after optional ring merge.
- [ ] Duplicate or conflicting records fail.
- [ ] Overflow fails.
- [ ] Present REQUEST and CALLBACK belong to the same client sequence.
- [ ] Completion cover exists: renderer role, same generation, serial `>= S`.
- [ ] INFLIGHT proves exactly one bound branch:
      busy → reason-1 reject before cover and no target lease/publish/success
      before cover; or quiescent → cover before the first target lease followed
      by a complete target direct LEASE/PUBLISH/COMPLETED/SUCCESS lifecycle
      **and then** a later Composite REQUEST/CALLBACK plus a second complete
      lifecycle. The later Composite is a PRODUCT INVARIANT (DESIGN §6.2 / §9);
      do not delete it to match a short trace. If its status is unknown, STOP.
- [ ] A Composite callback alone is not admission evidence.
- [ ] OOM proves the requeue-fail branch, has no event 32, and proves post-cover
      ACK/idle ordering.
- [ ] Later direct SUCCESS belongs to the same destination pair.
- [ ] Required pixels are exact and fixture exit is zero.
- [ ] Fatal/firstFailed/X death/watchdog fails the cell.
- [ ] Historical PASS and FAIL fixtures retain their classifications.

## Artifact and Cell Binding Checklist

- [ ] Runtime directory matches `runtime-[0-9a-f]{7,40}` exactly.
- [ ] Runtime SHA prefix matches the SHA embedded in `EXPECT_VERSION`.
- [ ] Malformed hex and SHA/version mismatch are negative tests.
- [ ] Canonical runtime root is enforced; arbitrary look-alike paths are refused.
- [ ] Fixture SHA is exact.
- [ ] Installed package is `com.waydefu.x11gpu` only.
- [ ] APK hash, Build ID, signer, ABI, and live mapped APK match qualified CI
      evidence before a cell can count.
- [ ] Frozen `runtime-9369553/` accepts no new cells and never permits D2-OOM.

## Verification Sequence

Before recommending implementation authorization:

1. Run the judge unit tests and require every named positive/negative case PASS.
2. Run bind negative tests, including malformed runtime SHA and mismatched
   version SHA.
3. Run shell syntax checks on the harness and bind scripts.
4. Compile D2 fixture with `-Wall -Wextra -Werror`.
5. Run the static verifier against the exact R6 worktree.
6. Confirm the source verifier proves wait-before-ACK and
   completion-before-release ordering, not merely symbol presence.
7. Recheck exact HEAD, clean status, and `git diff --check`.
8. Stop and request explicit authorization for ownership C changes.

After an authorized implementation, require RED→GREEN source tests, ARM64
incremental and full-clean native builds, zero new warnings, final diff review,
and exact-head multi-ABI CI. Stop again before install/runtime unless separately
authorized.

## Pitfalls

- `serial == S` looks precise but is wrong for a completion watermark.
- A green client and exact pixels can be software fallback.
- An env flag proves configuration, not branch execution.
- A same-generation SUCCESS can still belong to another destination.
- Contiguous `seq=10..16` is incomplete in a fresh non-overflowed trace; missing
  prefix `0..9` must not disappear silently.
- Shell glob `[0-9a-f]*` means “one hex character followed by anything,” not “all
  characters are hex.” Use an anchored regex.
- `lorieGpuCopyWait` is currently `static`; cross-file design must freeze an
  exported fail-stop wrapper before coding.
- A ring fallback described in prose but not captured by the harness is not an
  implemented fallback.

## Reporting Format

Report findings first, ordered by severity. For each finding include:

```text
Severity / confidence
path:line and symbol
exact violated invariant
concrete failure mode
minimal false-green or false-red proof
required correction and acceptance test
```

End with separate verdicts for design, source, host verification, CI artifact,
device runtime, Stable/HDMI, and the next authorization decision. Never collapse
“host tests PASS” into “R6 PASS.”
