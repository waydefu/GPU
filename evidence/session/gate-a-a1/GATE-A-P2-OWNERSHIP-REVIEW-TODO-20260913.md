# Gate A P2 ownership architecture review TODO — 2026-09-13

Scope: design/source review only at exact HEAD `5e9eb2a`; no source code,
build, CI, APK, ADB, runtime, Stable, or HDMI operation.

## Acceptance criteria

- [x] Bind P1 and D0a HEAD/status/diff-check and governing authority.
- [x] Trace source ownership through FinishAccess/PrepareComposite/Composite/
      DoneComposite/PrepareAccess, including every post-unlock path.
- [x] Trace destination ownership through renderer write, fence, serial result,
      repair/read/write/reuse, Present/resize/destroy interactions.
- [x] Prove first-use and reuse state transitions or identify a blocker.
- [x] Verify queue entry initialization and release/acquire ordering without ABI
      or completedSerial semantic change.
- [x] Verify persistent direct registry lookup/bind path cannot enter CPU/staging.
- [x] Verify bounded EGL fence completion and all create/wait/context failures.
- [x] Re-prove R3 SUCCESS derivation assumptions against current exact source.
- [x] Close unlock→revalidate→publish race with an implementable state/lock/CAS
      model, including DestroyPixmap interaction.
- [x] Define cross-operation admission for Composite/Present/CPU access/destroy/
      resize/CloseScreen.
- [x] Classify every requested failure cell as PRE-PUBLISH FALLBACK,
      FAILED_QUIESCED, or FATAL.
- [x] Bound the minimum P2 diff and explicitly preserve all redlines.
- [x] Produce one verdict; if any invariant remains unproved, NOT AUTHORIZED.

## Completion evidence

- Review: `GATE-A-P2-OWNERSHIP-ARCHITECTURE-REVIEW-20260913.md`.
- Exact source: P1 `5e9eb2a` clean; D0a `a6cc795` clean; both diff-check PASS.
- Official contracts: local NDK r29 `hardware_buffer.h:451-526`, current Android
  AHardwareBuffer reference, Khronos EGL_KHR_fence_sync registry text.
- Independent read-only lanes flagged current skip/early-ack/EGL_FOREVER risks;
  parent independently reproduced each decisive path and bounded it in the
  authorized design.
- Verdict: all ten architecture cells PASS; P2 implementation AUTHORIZED,
  Production Gate A remains BLOCKED.
