# Gate A / Gate D Architecture Review TODO — 2026-09-11

Scope: read-only architecture audit and narrow prototype design. No renderer,
ownership, fence, runtime, APK, ADB, Stable, or Gate H change.

## Acceptance criteria

- [x] Trace the current working-tree R3 path from PrepareComposite through
  Composite and DoneComposite to promotion, LorieBuffer/AHardwareBuffer,
  EGLImage/texture, renderer, and completion.
- [x] Identify where whole-pixmap clone/staging/upload and completion costs occur.
- [x] Evaluate Gate A byte/format contract, CPU/X11 visibility, ownership,
  lifetime, and fence semantics; preserve the historical BGRA-black risk.
- [x] Evaluate Gate D dirty-region source, stride/bytes, region union,
  persistent texture ownership, resize/destroy/recreate, readback hazards, and
  memory cap.
- [x] Choose exactly one first prototype constrained to 1–3 functions.
- [x] Define exact correctness, telemetry, lifecycle, resource, rollback, and
  paired runtime gates without expanding the B3a benchmark matrix.
- [x] Record VERIFIED / INFERRED / UNKNOWN / NEEDS RUNTIME GATE separately.

## Completion evidence

- Serena symbol definitions and references with `file:symbol` evidence.
- Relevant working-tree diff hunks where runtime source differs from HEAD.
- Final `git diff --check` and confirmation that no native source was changed by
  this review.

Completed in `GATE-A-D-ARCHITECTURE-REVIEW-20260911.md`.
