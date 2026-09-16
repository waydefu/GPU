---
name: evidence-first-gate-test-design
description: Design gates that reject false green and false red.
version: 0.1.0
author: waydefu, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  related_skills: [verification-integrity, evidence-first-debugging]
---

# Evidence-First Gate Test Design

Use this skill when designing or reviewing a test gate, runtime oracle, fault
injection, asynchronous ordering check, artifact qualification, or PASS/FAIL
judge. The goal is not merely to make the expected run green; it is to prove
that forbidden behavior turns red and legal edge behavior stays green.

## When to Use

- A gate controls whether code may ship, deploy, install, migrate, or advance to
  another stage.
- A test infers behavior from logs, events, counters, timestamps, serials,
  callbacks, queues, watermarks, or asynchronous workers.
- A PASS could come from fallback, skipped work, stale artifacts, incomplete
  logs, the wrong transaction, or the wrong environment.
- A failure prompted a redesign of the fixture, judge, or observability.

Do not use a passing host oracle as permission for production, device, IAM,
secret, schema, destructive, merge, or other separately gated actions.

## Core Model

Before writing code, define one row per claim:

| Field | Question |
|---|---|
| Claim | What exact behavior must be true? |
| Direct evidence | Which state/event proves it without inference? |
| Identity | Which operation, generation, object, user, request, or artifact? |
| Order | What must happen before/after what? |
| False green | What broken behavior could the current judge accept? |
| False red | What legal batching/reordering could it reject? |
| Missing evidence | Does absence fail closed? |
| Recovery | What proves the system returns to a valid terminal state? |

A gate is not designed until each row has a falsifiable oracle and at least one
negative test.

## Hard Rules

1. **Evidence before verdict.** A required signal must exist. Never infer success
   merely because no contradictory signal appeared.
2. **Bind identity end to end.** Correlate source revision, artifact, process,
   request/transaction, generation/epoch, object IDs, and result. A valid event
   for another operation is not evidence.
3. **Use semantic order, not delivery order.** Logs from different threads,
   processes, or machines may arrive out of order. Use authoritative sequence
   numbers or clocks with a proven common domain.
4. **Treat watermarks as watermarks.** If value `T` means all work through `T`
   completed, operation `S` is covered by `T >= S`; exact equality can reject
   legal batching.
5. **Prove branch execution.** An env flag, mock configuration, or fault knob
   proves setup only. Require a positive marker that the injected branch was
   consumed.
6. **Fail closed on incomplete traces.** Missing, duplicate, conflicting,
   overflowed, truncated, or unbound evidence cannot PASS. Use an authoritative
   fallback recorder or stop.
7. **Positive tests are insufficient.** Every allow rule needs forbidden-input
   tests; every deny rule needs legal-boundary tests.
8. **Pixels/output do not prove the path.** Correct output may come from fallback,
   cache, stale data, skipped work, or a different backend. Require path identity
   separately.
9. **Liveness does not prove correctness.** A process can remain alive after
   silent failure, fallback, data loss, or incomplete work.
10. **Timing is commentary unless it is the contract.** “Returned quickly” or
    “probably overlapped” is not an ordering proof. Use explicit events/state.
11. **Fault paths preserve ownership.** Timeout, cancellation, requeue failure,
    worker loss, or partial publication must not release resources before a
    terminal proof. Uncertain state fails safely.
12. **Recovery must be observed.** A gate that proves rejection but never proves
    later valid work succeeds is incomplete.
13. **Historical evidence is immutable.** Never overwrite the first failure or
    silently rerun until green. New attempts get new identities and evidence.
14. **A test must test production logic.** Import/call the real judge, parser,
    policy, or helper. A copied look-alike can pass while production remains
    broken.
15. **Artifact layers stay separate.** Source test PASS, build PASS, package
    qualification, deployment binding, runtime correctness, and performance are
    distinct verdicts.
16. **One failure, one classification.** Separate fixture construction failure,
    observability failure, product defect, stale artifact, environment blocker,
    and infrastructure flake.
17. **No threshold weakening.** Do not skip checks, widen tolerances, ignore
    errors, add sleeps/retries, or redefine PASS to make a red result green.
18. **Authorization is external to correctness.** A technically sound plan still
    needs explicit approval at architecture, production, destructive, security,
    payment, merge, and other governed boundaries.

## Procedure

### 1. Bind authority and baseline

- Read repository governance, current handoff/state, specification, and test
  matrix before the implementation or logs.
- Record repository/worktree, branch, full HEAD, dirty state, submodule pins,
  toolchain, relevant flags, and baseline command/exit status.
- Bind the running/deployed artifact separately from local source.
- Mark dated reports as historical unless current authority adopts them.

Completion criterion: the review names exactly what source and runtime state it
can prove and does not blend two snapshots.

### 2. Draw the state machine and ownership ledger

Trace create/acquire → publish → consume → terminal result → acknowledge →
release → reuse, including every timeout, cancellation, early return, callback,
retry, teardown, and worker loss.

For each resource record:

| Resource | Creator | Current owner | Consumer | Terminal proof | Release point | Failure cleanup |
|---|---|---|---|---|---|---|

Completion criterion: no resource is released or reused while a consumer may
still hold it, and every nonterminal path has an explicit safe outcome.

Mechanically enumerate all ACK, pending-decrement, reference-release, idle,
abort, scrap, destructor, disconnect, cancellation, and teardown call sites.
Never assume the reported failure branch is the only release path. Prefer one
audited retirement helper and add a static test that rejects raw release calls
outside that helper; this turns future cleanup additions into visible failures
instead of silent ownership holes.

### 3. Define the authoritative event schema

For every event define:

- producer role/thread/process;
- sequence domain;
- generation/epoch;
- operation serial/request ID;
- object/source/destination IDs;
- publication memory ordering;
- whether the serial is exact or a watermark;
- whether the event means submission, consumption, quiescence, semantic success,
  acknowledgment, or release.

Never let one event stand for two of these meanings.

### 4. Write negative tests first

At minimum cover:

- required event absent;
- wrong role;
- wrong generation/epoch;
- wrong request/transaction ID;
- wrong object/resource pair;
- stale artifact or mismatched source revision;
- event before its prerequisite;
- duplicate/conflicting sequence;
- internal and prefix sequence gaps;
- overflow/truncation;
- injected branch not executed;
- fallback output falsely accepted as target-path success;
- timeout/loss followed by forbidden release;
- client/process success with missing semantic success.

Verify each case fails for the intended reason, not because the fixture is
malformed.

### 5. Write legal-boundary tests

At minimum cover:

- completion watermark greater than the target serial;
- physical log order different from authoritative sequence order;
- batched completion;
- completion racing before the observer enters its wait;
- idempotent duplicate input where permitted;
- trace gap repaired by the authoritative recorder;
- exact boundary values and rollover/overflow containment;
- historical known PASS data.

These tests prevent an over-strict judge from calling correct behavior broken.

### 6. Prove fault-injection consumption

Use two distinct proofs:

1. configuration reached the target process;
2. the intended branch emitted a transaction-bound marker.

A test with only proof 1 cannot qualify the fault path. If the branch may
legitimately race with completion, specify a partial order instead of forcing a
single total order.

### 7. Correlate recovery

After rejection/failure handling, require a later valid operation tied to the
same relevant object/tenant/pair to reach its intended terminal success. Do not
accept an unrelated success from the same generation or process.

### 8. Bind artifacts and evidence paths

- Parse identifiers with anchored formats, not permissive shell globs.
- Require evidence directory IDs to match artifact/source IDs.
- Verify exact command, exit code, fixture hash, package/version, artifact hash,
  build ID/signer when applicable, and live process binding.
- Refuse existing/frozen evidence paths.
- Never substitute an older artifact when the expected one is missing.

### 9. Verify the verifier

Add unit tests for the judge and binding logic themselves. Run them against:

- synthetic minimal traces;
- historical known PASS evidence;
- historical known FAIL evidence;
- malformed identifiers and path bindings.

A static checker that searches only for symbol names or substrings does not
prove ordering. Parse the relevant block or test the executable behavior.

### 10. Report in layers

Return separate verdicts:

```text
DESIGN
FIXTURE CONSTRUCTION
JUDGE / ORACLE
SOURCE IMPLEMENTATION
HOST TESTS
BUILD / CI
ARTIFACT BINDING
RUNTIME
PERFORMANCE
UNKNOWN / LIMITATIONS
DECISION REQUIRED
```

Never collapse partial PASS results into the final gate.

## Async and Concurrent Systems Checklist

- [ ] Ordering uses a defined sequence domain.
- [ ] Sequence starts/ends are known or captured from authoritative metadata.
- [ ] Multi-thread log delivery cannot reorder the verdict.
- [ ] Watermark coverage uses the correct comparison.
- [ ] Generation/epoch prevents stale completion reuse.
- [ ] Request and callback are correlated.
- [ ] Success is correlated to the target resource pair.
- [ ] Publish, consume, complete, semantic success, ACK, and release remain
      distinct.
- [ ] Timeout/cancellation does not masquerade as completion.
- [ ] Missing consumer progress fails without releasing ownership.
- [ ] Recovery succeeds on the same intended resource after terminal proof.

## Judge Unit-Test Matrix

A reusable minimum matrix:

| Case | Expected |
|---|---|
| Exact intended trace | PASS |
| Required terminal absent | FAIL |
| Terminal from wrong role | FAIL |
| Terminal from wrong generation | FAIL |
| Terminal for wrong transaction/resource | FAIL |
| Legal watermark greater than target | PASS |
| Forbidden action before watermark cover | FAIL |
| Log lines reversed, sequence correct | PASS |
| Duplicate/conflicting sequence | FAIL |
| Prefix/internal gap, no fallback evidence | FAIL |
| Gap filled by authoritative evidence | PASS |
| Correct output through fallback only | FAIL |
| Fault configured but branch marker absent | FAIL |
| Recovery success for unrelated object | FAIL |
| Historical known PASS | PASS |
| Historical known FAIL | FAIL |

## Artifact-Binding Negative Tests

- malformed revision ID;
- too-short/too-long identifier;
- identifier with a valid prefix and invalid suffix;
- evidence-path SHA different from version/source SHA;
- local HEAD different from workflow head;
- qualified artifact different from installed/mapped artifact;
- attempt to reuse or overwrite a frozen result directory;
- valid package name but wrong signer/build ID;
- flag set in launcher but absent from the worker that consumes it.

## Pitfalls

- `[0-9a-f]*` in a shell glob is not an all-hex regex.
- Sorting logs by timestamp does not create a shared clock domain.
- A counter total cannot prove per-operation ordering.
- A later success in the same process may belong to another request.
- An environment variable may be present while the fault branch is dead code.
- A completion event can be valid but refer to a prior generation.
- A trace contiguous from its first captured sequence may still be missing a
  prefix; know the expected starting sequence.
- A recorder fallback described in documentation but not produced by the harness
  does not exist operationally.
- Adding a marker before an operation proves entry, not successful completion;
  pair ENTER/RETURN or use a terminal state.
- Retrying a construction-sensitive race until it happens biases the evidence.

## Verification

Before approving a gate design, verify:

- every required claim maps to a direct, identity-bound signal;
- every missing signal fails closed;
- false-green and false-red tests pass as expected;
- fault consumption and post-terminal recovery are both proven;
- ownership release follows terminal proof on every path;
- judge tests execute the real judge;
- historical PASS/FAIL classifications remain stable;
- artifact and evidence identifiers are strictly bound;
- the final report keeps host, CI, artifact, runtime, and performance verdicts
  separate;
- the next side-effecting or architecture step still waits for its required
  authorization.
