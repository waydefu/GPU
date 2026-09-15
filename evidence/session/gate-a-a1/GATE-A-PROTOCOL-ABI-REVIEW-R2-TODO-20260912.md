# Gate A protocol ABI review R2 TODO — 2026-09-12

Scope: review only revised P0–P4, fatal path, and unregister. No source/build/CI/APK/ADB/device/Stable/HDMI operation.

## Acceptance criteria

- [x] Prove watermark + sticky-first-failure result derivation under queue ordering.
- [x] Review concrete cross-process widths/alignment/offsets/lock-free assertion strategy and all memory-order edges.
- [x] Review crash-safe generation identity and clean-vs-fatal closure.
- [x] Review READY resource proof, first-use ordering, admission/fallback, and CPU→GPU ownership.
- [x] Review fatal containment, unregister metadata/ACK, control-path symbol map, and waiter liveness.
- [x] Decide P0 authorization with all remaining correctness gaps listed.

## Completion evidence

- Review: `GATE-A-PROTOCOL-ABI-REVIEW-R2-20260912.md`.
- Verdict: HOLD; P0 implementation NOT AUTHORIZED; six remaining gaps.
- HANDOFF item 10 updated to R2 authority.
- No prohibited operation; source was not modified.
