# S3 Grok Brief (entry document — start here, then follow `HANDOFF-S3.md`)

## Mission

Design the minimum safe S3 architecture that eliminates the current 19
unresolved symbols at link time (`ld.lld --no-undefined`), without touching
rendering correctness, synchronization, Stable, or qualification integrity.
Full context lives in this folder; no chat history is needed.

## Frozen correctness

P2-B.2 R3 exact correctness (1514/1514 oracle, maxΔ=0) is immutable. The R3
slice (Over-only ARGB→XRGB, no mask/transform/bilinear/repeat/componentAlpha,
fail-closed) and the X-byte CPU repair stay exactly as they are in this round.

## Track A — EGL (6 symbols)

Decide a **typed `eglGetProcAddress` dispatch architecture**:

- `eglCreateImageKHR` ×2 (real `EGLint[3]` attribs — aliasing to core is an ABI
  lie), `eglCreateSyncKHR` ×3 (attribs provably NULL — narrow wrapper is
  *candidate only*), destroys/waits (handle-only), `glEGLImageTargetTexture2DOES`
  ×2 (no core equivalent; one use is off the R3 FD path, one is a probe).
- Khronos rule (verified): extension entrypoints must be acquired via
  `eglGetProcAddress` + extension-string check; static linking against them is
  non-portable by design.
- Decide: proc ownership, init timing, extension detection, fail-closed policy
  (NULL-proc ⇒ software fallback, never crash/skip), R3 FD-path independence,
  typed function pointers, no ABI alias.

## Track B — X11 (13 symbols)

Decide **dead client-side Xlib isolation**:

- All 13 (`XGetKeyboardMapping`, `XGetModifierMapping`, `XFreeModifiermap`,
  `_XFreeMutex_fn`, `_XReply`, `_XGetRequest`, `XkbUseExtension`, 6× `_Xkb*`)
  are proven live-`Display*`-unreachable (full closure in `S3-X11-CLOSURE.md`).
- Compare: minimal source set removal from the `xkbcomp` static target vs
  static-library split vs target-topology alternative. Full libX11, stubs, and
  global `--whole-archive` removal are all prohibited inputs.

## Constraints

Stable untouched · no stubs · no full libX11 · keep `--no-undefined` · no
global whole-archive removal · no rendering semantic change · no sync redesign
· no NDK/vendor modification · unobserved metrics stay `null`.

## Deliverables expected from Grok

1. preferred architecture (A + B)
2. alternatives considered and rejected (with reason)
3. dependency graph before/after
4. exact files/targets affected
5. minimal diff plan
6. runtime fallback behavior per path
7. validation gates (link must go green with `--no-undefined` intact)
8. rollback boundary (per-track revertibility)
9. hidden ABI/lifetime risks
10. implementation order (link-green first, behavior-neutral throughout)
