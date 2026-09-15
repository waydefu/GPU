# Cursor Luna Execution Brief — R6 Present Retirement

Paste the instruction below into a **new Cursor Luna session** after the parent
has created and opened the required linked worktree. This brief is not source
write authorization by itself.

---

## Prompt for Cursor Luna

You are the only writer for Gate A P2 R6 Present GPU-copy retirement.

Load and obey:

1. `.cursor/skills/gate-a-r6-present-retirement-implementation/SKILL.md`
2. `.cursor/skills/gate-a-r6-design-review/SKILL.md`
3. `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-PRESENT-RETIREMENT-IMPLEMENTATION-PLAN-20260915.md`
4. The authority files named by those skills.

The project workspace is `/root/projects/GPU加速`. Work only in the already
created linked worktree:

```text
/root/projects/GPU加速/src/f8-ahb-gatea-r6-retire
```

Required branch and base:

```text
branch: fix/gatea-r6-present-retirement-20260915
base: 95e6f9602b0146ee190870f84a34aad822ef666f
```

Before any write, verify exact branch/base, clean tracked status, submodule HEAD,
and current authority. If any mismatch exists, stop and report it. Do not create
another worktree.

The user authorization must explicitly cover both Present lifecycle C changes
and the D2-INFLIGHT dual-branch oracle. If that authorization is absent from the
current Cursor conversation, do read-only inspection and stop.

Implement only the frozen contract in the writer skill:

- one `present_gpu_copy_retire_or_fatal(vblank)` in `present_vblank.c`;
- one executable raw ACK in xserver/present, inside that helper;
- completion proof before ACK, pending decrement, idle, scrap, or destroy;
- timeout/renderer loss fail-stop without release;
- set pending immediately after successful scheduling;
- use the helper from already-pending, post-schedule, scrap, and destroy paths;
- preserve root destination `dst_buffer == NULL` semantics;
- preserve events and ABI; event 32 remains forbidden;
- implement busy-reject and quiescent-admit judge branches without accepting
  missing evidence.

Use strict RED→GREEN. First add source tests that fail on the three existing raw
ACK paths and a judge test that fails because the old oracle requires reject.
Only then edit production C/judge. Run focused tests after each vertical slice,
then all host gates and ARM64 incremental/full-clean builds.

Do not modify `InitOutput.c`, `lorie.h`, renderer, fence semantics, queue ABI,
direct predicate, dependencies, Stable, device state, or CI. If the frozen API
is insufficient, stop for architecture review rather than expanding scope.

Do not commit, push, dispatch CI, install, run ADB/device cells, start R7, open a
PR, merge, or invoke another agent. Leave a verified uncommitted diff for the
parent.

Return exactly the evidence packet required by the writer skill, including
commands and exit codes. Do not claim R6 PASS.

---

## Parent prerequisites before opening Cursor Luna

- Record explicit source/oracle authorization in the Cursor conversation.
- Create exactly one linked worktree from `95e6f96`.
- Keep the baseline worktree clean and frozen.
- Open `/root/projects/GPU加速` as the Cursor workspace so `.cursor/skills/` and
  the root evidence files are discoverable.
- Ensure no other writer is modifying either the linked worktree or host judge
  files.

## Parent review after Luna exits

The parent must independently verify:

- teardown lifetime and all ACK/release callers;
- exact helper ordering and root-destination behavior;
- raw ACK count and absence of event-32 callsites;
- judge false-green/false-red boundaries;
- xserver patch round-trip;
- host tests and ARM64 builds;
- final diff and scope.

Only the parent may decide whether to commit and later request push/CI/device
authorization.
