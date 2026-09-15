# Gate A P2 R3 X-pump design TODO — 2026-09-14

Scope: source-only design correction after `88e3f17` R3 FAIL. No C/C++ mutation, build, push, CI, ADB, install, runtime, Stable, or HDMI operation.

## Acceptance criteria

- [x] Bind analysis to Gate A worktree HEAD `88e3f176d5be313b7dee058da9021cfe8d09e7de`, clean.
- [x] Bind xserver source to submodule HEAD `65d790bd208ec380b196eb98f144abb0b32e334d`.
- [x] Trace `InputThreadPreInit` / `InputThreadInit` / `InputThreadRegisterDev` and `SetNotifyFd` callback execution.
- [x] Trace REGISTER → waiter → READY frame → registry mark/signal.
- [x] Correlate the source wait-for graph with the frozen `88e3f17` runtime timestamps.
- [x] Classify the observed R3 root cause without retrying the cell.
- [x] Review the uploaded main-thread-pump proposal for blocking-I/O, reentrancy, framing, writer-serialization, HUP, and timeout risks.
- [x] Define a bounded record-aware pump contract that preserves the frozen wire/queue/result ABIs and the 2000 ms deadline.
- [x] Provide alternatives, trade-offs, recommendation, blast radius, and RED/GREEN verification requirements.
- [x] State the next authorization boundary before any source change.

## Completion evidence

- Design: `GATE-A-P2-R3-XPUMP-DESIGN-20260914.md`
- Runtime authority: `../p2-r3-terminal-runtime/runtime-88e3f17/GATE-A-P2-R3-RUNTIME-20260914.md`
- Source status checked before design: HEAD exact, worktree clean, `git diff --check` PASS.
- Device/runtime: NOT RUN.
