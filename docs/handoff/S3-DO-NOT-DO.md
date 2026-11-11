# S3 Do-Not-Do (binding rejections from evidence, not preferences)

- KHR→core blanket `-D` alias — ABI lie (`EGLint*` vs `EGLAttrib*` on AArch64).
- `EGLint* → EGLAttrib*` casts — same ABI reason.
- Fake EGL/OES stubs or no-ops — S5 qualification-integrity violation.
- Xlib stubs (`_XReply` etc.) — all 13 proven unreachable; stubs buy nothing and risk loud-or-silent corruption if ever hit.
- Full `libX11` restoration merely to turn the linker green — architecture decision, not a build fix.
- Disabling `--no-undefined` or removing `--whole-archive` globally — weakening the project's own correctness gate.
- Repacking an old APK with a new `.so` as a qualification artifact.
- Modifying the NDK, vendoring Khronos headers, touching Stable (`com.termux.x11`/`:1`).
- Reusing historical runtime results as fresh evidence; writing `0` for unobserved metrics (use `null`/`not_observable`).
- Reopening P0/P1/P2-A/P2-B.1/P2-B.2 sealed issues without fresh contradictory evidence.
- Guessing why R3 CI succeeded — CI/local divergence stays OPEN until proven.
