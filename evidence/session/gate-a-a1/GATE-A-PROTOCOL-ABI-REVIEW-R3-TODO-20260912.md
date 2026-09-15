# Gate A protocol ABI review R3 TODO — 2026-09-12

Scope: close the six R2 gaps at design level. No code/build/CI/APK/ADB/device/Stable/HDMI operation.

## Acceptance criteria

- [x] Freeze shared-state/result ABI: exact widths/offsets/alignment, lock-free atomics, all release/acquire edges, init/wrap rules; prove lossless SUCCESS derivation under strict in-order execution.
- [x] Prove destination ownership/lifetime: exclusive renderer ownership during GPU work, same-boundary relock/reuse, timeout fail-closed, SUCCESS-gated X-byte repair, ROOT_READY + resize drain rule, cross-op admission via terminal lastSubmittedSerial.
- [x] Define the single fatal atomic edge: once-CAS first detail, renderer per-entry fatal checks, X admission/waiter/release checks, credible vs poisoned serial sets, completed-vs-fatal observation order.
- [x] Prove the wait-for graph cycle-free: all eight waiters bounded + fatal-wakeable; bounded Gate A EGL waits; input-thread-direct wakeup (no WorkProc round-trip); fatal bypass of blocking rendezvous; no state->lock held while waiting.
- [x] Define activity fatal containment in xcallback: short-read/bad-frame/generation rules, REGISTER_FAILED wakeup, HUP bypass of blocking setSharedState, process-termination bottom line; no clipboard/input rewrite.
- [x] Freeze minimal retirement metadata both sides; exact DestroyPixmap/UNREGISTER/CloseScreen paths; duplicate rules; fatal exclusion.

## Completion evidence

- Review: `GATE-A-PROTOCOL-ABI-REVIEW-R3-20260912.md`.
- Verdict: all six PASS; P0 AUTHORIZED; Production Gate A remains BLOCKED.
- HANDOFF status + Next updated to R3 authority.
- D0a/A1 authorities reverified clean; no prohibited operation.
