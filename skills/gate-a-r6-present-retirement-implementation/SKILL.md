---
name: gate-a-r6-present-retirement-implementation
description: Implement R6 Present retirement under frozen contracts.
paths:
  - "AGENTS.md"
  - "HANDOFF.md"
  - "TEST-MATRIX.md"
  - "evidence/session/gate-a-a1/p2-r6-design/**"
  - "evidence/session/gate-a-a1/p2-r3-xpump-runtime/**"
  - "src/f8-ahb-gatea-r6-retire/lorie/src/main/cpp/**"
---

# Gate A R6 Present Retirement — Cursor Luna Writer

Use this skill only for one Cursor Luna session acting as the sole writer in an
already-created linked worktree. The architecture below is frozen: implement it,
test it, and stop at an uncommitted diff. Do not redesign ownership, weaken a
gate, create another worktree, spawn another agent, or perform device/network
publication work.

## When to Use

Use only when the user has explicitly authorized both:

1. Present ownership/lifecycle C changes on top of `95e6f96`.
2. The D2-INFLIGHT busy-reject / quiescent-admit dual-branch oracle.

Loading this skill, asking for a plan, or opening the worktree is not source-write
authorization. If the current user message does not contain an equivalent grant,
read and report only; do not mutate source, tests, or authority documents.

Do not use for architecture review, runtime qualification, ADB, CI, PR, merge,
or R7. Use `gate-a-r6-design-review` for review.

## Fixed Inputs

- Project workspace: `/root/projects/GPU加速`
- Immutable base: `95e6f9602b0146ee190870f84a34aad822ef666f`
- Required writer worktree: `/root/projects/GPU加速/src/f8-ahb-gatea-r6-retire`
- Required writer branch: `fix/gatea-r6-present-retirement-20260915`
- Implementation plan:
  `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-PRESENT-RETIREMENT-IMPLEMENTATION-PLAN-20260915.md`
- Review skill:
  `.cursor/skills/gate-a-r6-design-review/SKILL.md`

The parent or owner creates the linked worktree. Cursor Luna must not create a
second worktree. If the exact worktree, branch, clean state, or base is absent,
stop and report the mismatch.

## Authority Order

Read before writing:

1. `AGENTS.md`
2. `HANDOFF.md`
3. `TEST-MATRIX.md`
4. `evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md`
5. `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-DESIGN-20260915.md`
6. `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-D2-HOLD-20260915.md`
7. The implementation plan named above
8. The review skill named above
9. `/root/.serena/memories/global/f8-workstation.md`

Current authority and the user's latest grant override this skill. Conflict means
stop; do not reconcile it silently.

## Absolute Boundaries

- ONE WRITER = this Cursor Luna session = one linked worktree.
- Do not invoke Hermes CLI or any subagent.
- Do not modify the baseline `src/f8-ahb-gatea-r6` worktree.
- Do not touch frozen A1/xpump/R5 worktrees.
- No commit, push, CI dispatch, download, install, ADB, device cell, PR, merge,
  origin push, R7, Stable, or HDMI.
- No renderer, fence, queue ABI, P0 sideband, direct predicate, BGRA/RGBX contract,
  dependency, or event-number change.
- No artificial GPU delay, sleeps to force reject, fallback on uncertainty, or
  validation weakening.
- Stop if a required fix exceeds the allowed files or frozen contract.

## Allowed Write Set

Source worktree:

```text
src/f8-ahb-gatea-r6-retire/lorie/src/main/cpp/xserver/present/present_execute.c
src/f8-ahb-gatea-r6-retire/lorie/src/main/cpp/xserver/present/present_vblank.c
src/f8-ahb-gatea-r6-retire/lorie/src/main/cpp/xserver/present/present_priv.h
src/f8-ahb-gatea-r6-retire/lorie/src/main/cpp/patches/xserver.patch
```

Host tests and dated documents:

```text
evidence/session/gate-a-a1/p2-r6-design/test-present-gpu-copy-retirement.py
evidence/session/gate-a-a1/p2-r6-design/verify_r6_design_impl.py
evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-PRESENT-RETIREMENT-IMPLEMENTATION-20260915.md
evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-D2-INFLIGHT-ORACLE-ADJUDICATION-20260915.md
evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-D2-INFLIGHT-PHYSICAL-RACE-ANALYSIS-20260915.md
evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-DESIGN-20260915.md
evidence/session/gate-a-a1/p2-r3-xpump-runtime/judge-r6-design.py
evidence/session/gate-a-a1/p2-r3-xpump-runtime/test-judge-r6-design.py
patches/p_r6_d2_present.c
```

Do not edit `InitOutput.c` or `lorie.h`: their existing wait-or-fatal API is the
frozen boundary. If it proves insufficient, stop with the exact reason.
Do not update `HANDOFF.md`, `TEST-MATRIX.md`, or `AGENTS.md`; the parent updates
authority only after independent verification.

## Frozen Helper Contract

### Name, location, and signature

Implement exactly in `present_vblank.c`, declared in `present_priv.h`:

```c
void present_gpu_copy_retire_or_fatal(present_vblank_ptr vblank);
```

Do not add flags, callbacks, modes, fallback results, or a second retirement
helper without stopping for architecture review.

### Valid root destination

`vblank->gpu_copy_dst_buffer == NULL` is valid: it denotes the root destination,
and `lorieGpuCopyAck()` then decrements `rootGpuCopyPending`. Never classify this
NULL as malformed state.

### State transition

The helper must implement this exact sequence:

```text
if !vblank
    fail loudly as an internal programming error; do not return success
if !gpu_copy_pending
    return without touching serial, pointer, pending counts, or refs
save serial = gpu_copy_serial
if serial == 0
    call lorieGpuCopyWaitForPresentOrFatal(0), which fail-stops
if !lorieGpuCopyIsDone(serial)
    call lorieGpuCopyWaitForPresentOrFatal(serial)
wrapper returns only after completedSerial >= serial
call the sole xserver/present raw lorieGpuCopyAck(pixmap, dst_buffer)
set gpu_copy_pending = FALSE
set gpu_copy_dst_buffer = NULL
set gpu_copy_serial = 0
return
```

Do not clear any field before ACK. Do not call idle, scrap, destroy, notify, or
flush inside the helper. On timeout or renderer loss the existing wrapper must
fatal and never return; therefore no release follows uncertainty.

### Schedule-state rule

After `lorieTryScheduleGpuCopy()` returns success, set
`vblank->gpu_copy_pending = TRUE` immediately, before any requeue attempt or
other return-capable operation. The scheduler has already acquired pending
counts and extra refs; the vblank state must reflect that ownership at once.

### Caller rules

- Already done: helper retires without waiting, then normal Present completion.
- Not done + renderer healthy + requeue success: retain pending and return queued.
- Not done + requeue failure: save trace serial/destination, event 33, helper,
  event 34, then normal completion.
- Not done + renderer loss: helper reaches fail-stop; no scrap or normal return.
- `present_vblank_scrap()`: helper before idle or pixmap destruction.
- `present_vblank_destroy()`: helper before pixmap/region/fence drop.
- A second helper call after successful retirement is a no-op, preventing double
  decrement.

Trace serial and destination identity needed after retirement must be copied to
local scalar values before calling the helper. Never dereference an opaque buffer
after ACK may have released its final extra reference.

### Single-release rule

After implementation, `xserver/present/` may contain exactly one executable
`lorieGpuCopyAck(` call: inside this helper. Declarations and comments do not
count. All executable `gpu_copy_pending = FALSE` terminal transitions also live
inside the helper; zero-initialization is exempt.

### Event contract

- Event 32 `PRESENT_EARLY_ACK` remains frozen and forbidden at runtime.
- Do not delete, renumber, or repurpose event 32.
- Events 33/34 retain requeue-failure semantics.
- Do not add telemetry events.
- Event 34 occurs only after the helper returns, using serial/destination saved
  before retirement.

## Frozen D2-INFLIGHT Oracle

The oracle accepts exactly one of two branches, with all common bindings intact.
This is not permission to accept missing evidence.

### Common requirements

- Sort by telemetry `seq`; require unique, contiguous sequence after ring merge.
- Pair Present REQUEST/CALLBACK by client sequence.
- Completion cover is renderer role, same generation, serial `T >= S`.
- Bind target destination/pair and direct lifecycle.
- Require fixture exit zero, exact pixels, no fatal/firstFailed/X death/watchdog.
- Any event 32 fails.

### Busy-reject branch

```text
Present CALLBACK(S,G)
< immediate Composite REQUEST/CALLBACK
< DIRECT_ADMIT_REJECT reason=1
< completion cover(T>=S,G)
< later target LEASE/PUBLISH/COMPLETED/SUCCESS
```

No target direct lease, publish, or success may occur before cover.

### Quiescent-admit branch

```text
Present CALLBACK(S,G)
< immediate Composite REQUEST/CALLBACK
completion cover(T>=S,G,RENDERER)
< first target LEASE_RESERVED
< PUBLISH
< direct COMPLETED
< SEMANTIC_SUCCESS
```

Completion may occur before or after Composite callback. The binding rule is
`cover.seq < first_target_lease.seq`. Callback alone is not admission evidence.

### Mandatory negative cases

Fail on lease/publish before cover, missing both reject and complete direct
lifecycle, wrong role/generation/destination, unrelated success, pixels-only,
sequence gap/duplicate/overflow without authoritative recovery, or missing
completion cover.

Do not rewrite historical cells. Add a dated adjudication; the five existing
`95e6f96` cells stay immutable.

## Cursor Luna Procedure

### 1. Bind and inspect

Verify exact base, branch, worktree status, submodule HEAD, and current authority.
Trace every caller of `present_vblank_scrap`, `present_vblank_destroy`, and every
raw ACK. Completion criterion: an ownership ledger covers normal, requeue,
renderer-loss, window-close, client-disconnect, abort, scrap, destroy, and screen
close paths.

### 2. Prove teardown prerequisites

Confirm `pvfb`, `pvfb->state`, pixmap, and held refs remain valid when the helper
runs. Confirm `gateACloseGeneration()` precedes wrapped Present close. If any
caller can run after required state is invalid, stop; do not add a NULL fallback.

### 3. RED first

Create `test-present-gpu-copy-retirement.py` against the real worktree. It must
fail on the three current raw ACK sites for the expected reason, not a syntax or
path error. Add the quiescent-admit judge test and watch it fail under the old
reject-only judge. Record commands, outputs, and exit codes.

### 4. GREEN in vertical slices

Implement helper and migrate scrap/destroy; run the focused test. Then migrate
already-pending and post-schedule execute paths; run it again. Then update the
judge and run its focused tests. Do not batch all code before first verification.

### 5. Regenerate xserver.patch

Treat the live xserver diff as the source for the parent patch. Prove a clean
`65d790bd208ec380b196eb98f144abb0b32e334d` checkout accepts the regenerated
patch and yields a byte-equivalent diff. Never use `reset --hard`.

### 6. Run host gates

Require the new retirement test, full judge suite, binding tests, static verifier,
fixture `-Wall -Wextra -Werror` compile, shell syntax, `git diff --check`, and
callsite audit to pass. Preserve full commands and exit codes.

### 7. Build locally

Run ARM64 incremental and full-clean native builds sequentially. Compare warning
fingerprints and require zero new warnings. Do not edit during builds.

### 8. Self-review, then stop

Review the full diff against this frozen contract. Remove caches/debug artifacts.
Do not commit. Return the required packet and leave an uncommitted, verified diff
for the parent to inspect independently.

## Stop Conditions

Stop immediately if:

- explicit source/oracle authorization is absent;
- exact worktree/base/branch is wrong;
- teardown lifetime cannot be proven;
- raw release cannot be centralized without `InitOutput.c`, renderer, fence, ABI,
  predicate, or event changes;
- a test cannot first reproduce RED;
- patch round-trip, build, or a negative test fails;
- a new warning appears;
- Stable, device, CI, network publication, or history rewriting would be needed;
- the user changes scope or says stop.

Do not improvise. Keep the diff/evidence and report the smallest decision needed.

## Required Return Packet

Return only:

```text
STATUS
BASE / BRANCH / WORKTREE
TEARDOWN LIFETIME PROOF (path:line)
ROOT CAUSE CALLSITES
RED EVIDENCE (command, exit, expected labels)
CHANGES (file:symbol)
RAW RELEASE CALLSITE AUDIT
GREEN VERIFICATION (command, exit)
PATCH ROUND-TRIP
ARM64 BUILDS / WARNING COMPARISON
FINAL DIFF STAT / DIFF CHECK
UNKNOWN / RISKS
ARCHITECTURE DEVIATION: NONE or STOPPED
NEXT AUTHORIZATION: parent review only
```

Never claim R6 PASS, CI PASS, artifact qualification, or device success.
