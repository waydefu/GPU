---
name: evidence-first-debugging
description: Debug from reproducible evidence before changing code.
version: 0.1.0
author: waydefu, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# Evidence-First Debugging

Find the first proven broken boundary before editing. Do not turn a plausible theory into a root cause.

## When to Use

- Bugs, crashes, regressions, timeouts, hangs, flaky tests, or environment failures.
- Runtime behavior contradicts source assumptions or prior documentation.
- Two attempts have already failed.

Do not use this as permission to alter production, credentials, permissions, or destructive state.

## Procedure

1. **Bind current authority.** Record repository root, branch, HEAD, dirty state, runtime version, and the authoritative handoff/spec. Mark stale snapshots as historical.
2. **Reproduce before repair.** Capture the smallest deterministic failing case and its real exit status. If reproduction is unsafe or unavailable, state the limitation.
3. **Trace the path and verify memory mapping.** Follow entry point → callers → data flow → terminal state. Read definitions and uses; do not invent symbols, APIs, or dependencies.
   - For SIGSEGV/SIGBUS/crashes: **Check `/proc/$PID/maps` first**. Confirm whether the faulting PC falls into native code (`.so` / executable) or a dynamic VM cache (e.g. `dalvik-jit-code-cache`, v8, anonymous executable mapping).
   - Distinguish the signal handler from the fault site: if a backtrace frame resolves to `p2a3CrashHandler` or a signal delivery trampoline, that frame is reporting the signal, not causing it.
4. **Classify evidence.** Label each claim `PROVEN`, `OBSERVED`, `INFERRED`, `FALSIFIED`, or `UNKNOWN`.
   - If a crash occurs in dynamic JIT/VM memory without an identifiable native caller, classify as `OBSERVED / VM-JIT-CLASS`. Do not blindly edit native C/C++ source code to "fix" an unlocalizable JIT null dereference.
5. **Find the first missing boundary.** Instrument or test the boundary immediately before and after it. Do not add broad logging or record secrets, raw credentials, private payloads, or unrelated process data.
6. **Test hypotheses cheaply.** Prefer a minimal local reproducer, unit test, socketpair, fixture, or source invariant before device/runtime repetition.
7. **卡住一次才查，一定要官方或權威文件，不可過時.** Search only after getting stuck once. Use current official or authoritative documents only. Do not use outdated sources. Do not search preemptively. Do not guess a second time. Reject blogs, forums, and superseded docs. Bind URL + version/date. See `no-guess-search` and `mem:global/no-guess-search`.
8. **Write a regression test first.** Verify it fails for the expected reason on the baseline, then make the smallest fix.
9. **Check sibling paths.** Fix the defect class when the same invariant is violated elsewhere, but do not expand into unrelated refactoring.
10. **Re-run the same reproducer.** Then run broader project gates and review the final diff.

## Multi-Tier Agent Discipline

- **Low-tier / Scout agents (e.g., Luna Max)**: Perform bounded evidence collection only—maps lookup, symbol/line binding, register dump extraction, unstripped ELF checks, log slicing. Return concise facts and minimum evidence; do not declare root causes or propose native code edits for untargeted crashes.
- **High-tier / Authority agents (e.g., Sol High)**: Absorb concise facts, check invariants, formulate falsification hypotheses, authorize bounded reruns, and make definitive architecture/code rulings.

## Stop Conditions

Stop and ask before destructive Git, production changes, schema migrations, secrets/IAM changes, dependency replacement, breaking APIs, broad architecture changes, or touching another person's work.

Stop immediately on unexpected dirty files, wrong branch/HEAD, evidence contradiction, possible data corruption, or a safety boundary you cannot verify.

## Report

Return:

```text
ROOT CAUSE
MINIMUM EVIDENCE (path:line / command result)
FALSIFIED HYPOTHESES
CHANGE
REGRESSION TEST (RED → GREEN)
BROADER VERIFICATION
UNKNOWN / RISKS
NEXT AUTHORIZATION BOUNDARY
```

## Verification

A debugging task is complete only when the original failure is reproduced, the failing boundary is proven, the regression test turns RED→GREEN, required gates pass, and the final report distinguishes fact from inference.
