# Production Gate A protocol design TODO — 2026-09-12

Scope: architecture design only against `qualification/d0a-narrow-20260912` / `a6cc795`. No source/build/CI/APK/ADB/device/Stable/HDMI operation. D0a/D0b/Gate H unchanged.

## Acceptance criteria

- [x] Decide whether READY is per-buffer or per-draw and bind its invalidation domain.
- [x] Preserve or explicitly revise `completedSerial` semantics.
- [x] Prove when GPU completion permits source relock without fence transport.
- [x] Define pre-publication failure, post-publication failure, timeout, and renderer-death behavior.
- [x] Define generation, unregister acknowledgment, context-loss, and CloseScreen ordering.
- [x] Decide queue-entry ABI, shared-state ABI, result channel, and native-fence transport requirements.
- [x] Bound first prototype to server-owned, non-imported AHB; no transparent replay or D0b work.
- [x] Select exactly one verdict: PROTOTYPE AUTHORIZED / HOLD / BLOCKED.

## Completion evidence

- Final design: `evidence/session/gate-a-a1/GATE-A-PRODUCTION-PROTOCOL-DESIGN-20260912.md`.
- Verdict fixed as `PROTOTYPE AUTHORIZED`; Production Gate A remains BLOCKED pending implementation and qualification.
- HANDOFF status block and Next item 9 updated to the same authority.
- Final source verification: `a6cc7952861b8a63740d42bf78553573cfa0eec0`, branch clean, `git diff --check` PASS.
- No source/build/CI/APK/ADB/device/process/Stable/HDMI operation; D0a/D0b/Gate H unchanged.
