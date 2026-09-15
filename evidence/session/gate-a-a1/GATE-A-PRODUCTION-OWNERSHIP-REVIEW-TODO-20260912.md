# Gate A production direct-live-AHB architecture review TODO — 2026-09-12

Scope: read-only architecture proof against `qualification/d0a-narrow-20260912` / `a6cc7952861b8a63740d42bf78553573cfa0eec0`. No source/build/ADB/device/Stable/HDMI operation; no D0a/D0b/Gate H mutation.

## Acceptance criteria

- [x] Bind exact clean source and A1 9/9 microprobe evidence separately.
- [x] Trace production source create → CPU access → direct AHB register/import/sample → queue → GPU completion → X reuse/release.
- [x] Build an ownership ledger for pixmap/private, AHB, CPU mapping, buffer ID/registry ref, EGLImage/texture, queue entry, fence/serial, and shared state.
- [x] Audit failure paths: promotion/import, lock/unlock, registration/lookup, GL/EGL failure, fence create/wait, timeout, disconnect, teardown/recreate.
- [x] State required invariants and classify each as PROVEN / MISSING / CONTRADICTED / UNKNOWN in current code.
- [x] Decide whether production Gate A can safely use direct live-AHB sampling without a new ownership/fence/result protocol.
- [x] Produce exact path:line/symbol evidence, concrete risks, and one next action; preserve A1 scope limits.

## Completion evidence

- Final report: `evidence/session/gate-a-a1/GATE-A-PRODUCTION-DIRECT-AHB-ARCHITECTURE-REVIEW-20260912.md`.
- Final source verification: D0a HEAD `a6cc7952861b8a63740d42bf78553573cfa0eec0`, branch clean, `git diff --check` PASS; A1 HEAD `4196798dd7bb93ab386b955009f49e7a5a0e1019`, branch clean, `git diff --check` PASS.
- Serena-generated untracked `.cache/` was confirmed created after the clean entry check, removed exactly, and source worktree reverified clean.
- Stable/HDMI/device untouched; no build, CI, APK, ADB, process, or source mutation occurred.
