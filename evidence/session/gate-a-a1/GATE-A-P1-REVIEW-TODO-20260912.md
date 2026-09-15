# Gate A P1 boundary review TODO — 2026-09-12

Scope: generation + REGISTER/READY design/implementation-boundary review only.
No code/build/CI/APK/ADB/device/Stable/HDMI operation.

## Acceptance criteria

- [x] Generation identity/lifecycle: nonce per process, generation per share,
      rotation/close/reset rules, stale-acceptance impossibility.
- [x] REGISTER path: framed transaction, looper-thread receive, GL-thread
      validation, READY/REGISTER_FAILED with reverse-order cleanup, no CPU fallback.
- [x] READY semantics fenced to import-validity; duplicate rules deterministic.
- [x] Registry both sides, keyed/tombstoned, separated from legacy buffer lists.
- [x] Control path diagram with magic gating and no legacy rewrite.
- [x] Threading proof: single writers, leaf mutexes, wakeup analysis with honest
      liveness bound, no rendezvous cycle.
- [x] Failure table terminal-classified; REGISTER_FAILED doubles as cleanup ACK.
- [x] Minimal P1 diff boundary with explicit WILL-NOT-CHANGE list.

## Completion evidence

- Review: `GATE-A-P1-REVIEW-20260912.md`.
- Verdict: all seven PASS; P1 IMPLEMENTATION AUTHORIZED (bounded).
- HANDOFF updated to P1 authority.
- D0a/A1 authorities reverified clean; no prohibited operation.
