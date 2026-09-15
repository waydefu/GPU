# D0b-R3 FINAL ARCHITECTURE VERDICT

## SOURCE

```text
branch: qualification/d0a-narrow-20260912
HEAD: a6cc7952861b8a63740d42bf78553573cfa0eec0
tracked worktree: clean
R1 prototype: REJECTED / READ-ONLY EVIDENCE ONLY
```

## R2 CLOSED FINDINGS

```text
Renderer needs explicit D0b mode: NO
Universal Composite region-upload path: PROVEN for admitted in-bounds narrow R3
Shared D0b mode bit: NOT NEEDED
New queue/shared-state semantics for mode: NO
Stale texture texels outside sampled region: PROVEN HARMLESS
Duplicate D0b DoneComposite lifecycle: NOT REQUIRED
completedSerial meaning: UNCHANGED
ownership/fence semantics for the data path: UNCHANGED
```

## UPLOAD TOTALITY

```text
IMPOSSIBLE UNDER CURRENT CONTRACT
```

Evidence:

- `LorieBuffer_bindTexture` (FD path) issues `glTexSubImage2D` and returns void; no success check (`buffer.c:665-673`).
- `uploadBgraAhbAsRgba` issues `glTexImage2D`, returns true after void call; its checks cover AHB lock/allocation only, not GL semantic acceptance (`buffer.c:593-632`).
- `checkGlError` loops `glGetError`, logs locally, returns void; cannot cancel/replay entry (`renderer.cpp:74-97`).
- R1 `uploadFdRegion` returns false only for preflight checks; after void per-row `glTexSubImage2D` calls it returns true without `glGetError` (`d0b-r1/renderer.cpp:780-853`).
- `completedSerial` published only after EGL fence wait; proves GPU command completion, not GL upload semantic success (`renderer.cpp:931-967`).

OpenGL ES 2.0.25 §2.5: `TexSubImage2D` is void; non-OOM GL errors cause command to be ignored with no state change; OOM results undefined; errors observed via `GetError`, not command return.

## GL ERROR DETECTION

```text
NO — local detection alone cannot restore X transaction correctness
```

- `checkGlError` logs and returns; no queue entry cancellation, no X notification, no CPU replay trigger.
- Detecting failure ≠ replaying failed Composite.

## CONTINUE-DRAW

```text
UNSAFE
```

- Current flow: upload failure → log → blend → draw → advance readIndex → eventually completedSerial.
- Can draw stale/uninitialized texture when GL ignored the upload.

## SKIP-DRAW

```text
UNSAFE
```

- X has no same-Composite replay or CPU fallback after publication.
- Withholding `completedSerial` → timeout/liveness failure.
- Publishing it → false completion report.

## FULL-UPLOAD FALLBACK

```text
UNSAFE / NOT PROVEN
```

- Uses same void GL mechanism, same missing resource/texture risk, no proven success result.
- Cannot be universal same-transaction fallback.

## EXISTING X REPLAY/FALLBACK

```text
NO
```

- EXA CPU fallback exists only when scheduling fails **before** publication.
- After publication, `DoneComposite` waits, logs, acknowledges/releases; no Composite replay.

## NEW RESULT/REPLAY PROTOCOL REQUIRED

```text
YES
```

Without a renderer→X per-entry upload success/failure result and a same-transaction replay/fallback contract, current-operation correctness cannot be guaranteed.

## CURRENT REDLINES COMPATIBLE

```text
NO — current no-new-protocol redlines cannot be satisfied while guaranteeing VALID(texture, sampled_region) for every admitted entry.
```

## FINAL CLASSIFICATION

```text
D0b:
BLOCKED UNDER CURRENT NO-NEW-PROTOCOL REDLINES
```

This is **not** "D0b is impossible". It is:

```text
D0b is blocked under the current no-new-protocol architecture constraints.
```

It may be reopened only by explicitly authorizing a new:

```text
renderer→X result/replay protocol
```

and separately reviewing ownership, memory ordering, generation/lifecycle, timeout/disconnect semantics.

## GATES

```text
Gate A: BLOCKED FOR CURRENT BGRA DIRECT-SAMPLING CONTRACT
Gate H: HOLD
```

## STABLE

```text
UNTOUCHED
com.termux.x11 / DISPLAY=:1
```

## HISTORICAL SIGSEGV

```text
OBSERVED / NON-REPRODUCED / ROOT CAUSE UNKNOWN
```

## REOPEN CONDITION

Explicit architecture authorization of a `renderer→X result/replay` protocol, with full lifecycle/ownership/memory-ordering review.

## NEXT ACTION

```text
NONE — no code, build, commit, CI, APK, ADB, device, or Stable operation.
```

Maintain D0a qualification authority; await explicit protocol authorization.