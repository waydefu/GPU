---
name: verification-integrity
description: Prove every green signal ran on the intended inputs.
version: 0.1.0
author: waydefu, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# Verification Integrity

A PASS is only meaningful when its inputs, artifact, environment, and acceptance criteria are bound to the intended change.

## When to Use

- CI, builds, generated files, packages, deployments, device qualification, benchmarks, or claims that a fix is live.
- A green check contradicts observed runtime behavior.
- Evidence crosses hosts, worktrees, branches, or artifacts.

## Procedure

1. **Name the claim.** State exactly what the check is supposed to prove and what it does not prove.
2. **Bind source.** Record repository, branch, full HEAD, dirty state, submodule pins, and relevant configuration.
3. **Bind the command.** Preserve the exact command and real exit status. For piped commands, use the producer's status (`pipefail`/equivalent), not the logger's success.
4. **Bind environment.** Record relevant OS, architecture, runtime/toolchain versions, and feature flags. Confirm flags reached the process that matters.
5. **Bind CI.** Require local HEAD = remote HEAD = workflow head SHA. A successful run on another commit is not evidence.
6. **Bind artifacts.** Download from the exact run; verify identity, size/hash where required, package/version, signer, archive integrity, expected binaries, and build IDs/symbol provenance.
7. **Bind live state.** A running process must map the qualified artifact. Launcher flags and process liveness do not prove child/backend behavior.
8. **Check coverage.** Positive tests alone do not prove a deny gate. Add negative cases, malformed inputs, failures, and completeness assertions.
9. **Keep layers separate.** Build PASS ≠ package PASS ≠ install binding PASS ≠ runtime correctness PASS ≠ performance PASS.
10. **Preserve negative evidence.** Never delete or overwrite a failed run to make the latest state look clean; label it historical or superseded.

## Anti-Patterns

- Re-running until green without explaining the first failure.
- Comparing stale generated output to another stale copy.
- Treating absence from a lossy log as proof an event did not happen.
- Claiming totals or completeness without machine counting.
- Reporting a host-tool blocker as a source defect.
- Replacing a missing artifact with an older one.
- Reading secrets to test whether redaction works.

## Report

```text
CLAIM
SOURCE BINDING
COMMAND + EXIT STATUS
ENVIRONMENT
CI HEAD BINDING
ARTIFACT BINDING
LIVE BINDING
ACCEPTANCE RESULTS
LIMITATIONS
VERDICT: PASS / FAIL / BLOCKED / NOT TESTED
```

## Verification

Before finalizing, confirm every declared PASS has an exact evidence source, every count is computed, every required gate actually ran, and every limitation is named without upgrading partial evidence into success.
