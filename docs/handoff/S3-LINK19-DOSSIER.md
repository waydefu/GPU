# S3 Link-19 Dossier (historical blocker analysis; resolved by S3-E1/S3-X1)

> The pre-implementation 19-symbol failure is retained as forensic provenance.
> Current implementation/link authority is `evidence/session/s3/GATE-S3-LINK.md`.

## Exact linker policy (committed, `recipes/xserver.cmake:302-303`)

```text
-Wl,--as-needed
-Wl,--no-undefined
-Wl,--whole-archive ${XSERVER_LIBS} -Wl,--no-whole-archive
android mediandk log m z EGL GLESv2
```

Historical blocker command source: `/tmp/b3a-gradle-native.log` (pre-S3, 19 unresolved).
Current clean-link command/log: `/tmp/s3-canonical-gradle.log` and
`evidence/session/s3/GATE-S3-LINK.md`.
The final command still carries `--no-undefined` and `--whole-archive`; no
linker weakening was used.

## EGL family (6 symbols)

| Symbol | source:line | Actual arguments | Attrib list | NDK stub? | Device runtime (last known) |
|---|---|---|---|---|---|
| `eglCreateImageKHR` | `buffer.c:598` | dpy, NO_CTX, NATIVE_BUFFER_ANDROID, clientBuf, arr | REAL `EGLint[3]` (`buffer.c:589`) | NO (stub: 44 core-only symbols) | present (R3 runs) |
| `eglCreateImageKHR` | `renderer.cpp:483` | same shape, arr (`renderer.cpp:369`) | REAL `EGLint[3]` | NO | present |
| `eglCreateSyncKHR` | `renderer.cpp:917/1070/1110` | `(dpy, EGL_SYNC_FENCE_KHR, nullptr)` ×3 | always NULL | NO | present |
| `eglDestroyImageKHR` | `buffer.c:387`, `renderer.cpp:530` | (dpy, image) | n/a | NO | present |
| `eglDestroySyncKHR` | `renderer.cpp:923/1091/1111` | (dpy, fence) | n/a | NO | present |
| `eglClientWaitSyncKHR` | `renderer.cpp:920/1088/1110` | (dpy, fence, flags, FOREVER) | n/a | NO | present |
| `glEGLImageTargetTexture2DOES` | `buffer.c:609` (EGLImage branch, NOT the R3 FD path), `renderer.cpp:518` (capability probe) | (target, img) | n/a | NO (GLESv2 stub too) | present |

Normative grounding (Khronos `eglGetProcAddress` reference, verified
2026-09-09): *"For functions that are queryable with eglGetProcAddress,
implementations may choose to also export those functions statically…
However, portable clients cannot rely on this behavior."* The NDK stub omitting
KHR/OES entrypoints is therefore conformant vendor behavior — not an NDK bug —
and the defect class is **entrypoint acquisition / link-time API compatibility**.

### Rejected (with reason)

- **Blanket KHR→EGL-1.5-core `-D` alias: REJECTED.** `eglCreateImageKHR` takes
  `const EGLint*` while core `eglCreateImage` takes `const EGLAttrib*`
  (`intptr_t`-class; the 1.5 change exists precisely for 64-bit handle-sized
  attributes). Both image call sites pass real arrays — aliasing would be an
  ABI lie on AArch64. Same for the Sync pair in general.
- **`EGLint* → EGLAttrib*` casts: REJECTED** (same ABI reason).
- **Fake stubs / no-ops / invented aliases: PROHIBITED** (S5).

### Implemented S3-E1 dispatch (current status)

The approved typed `eglGetProcAddress` dispatch table now resolves the EGL KHR
entrypoints after EGL initialization and the GL OES entrypoint after a current
context. Extension capability checks remain separate and NULL procedures
fail closed. The canonical clean-link result is recorded in
`evidence/session/s3/GATE-S3-LINK.md`.

## X11 family (13 symbols) — see `S3-X11-CLOSURE.md`

Dependency shape:

```text
xkbcomp static target
  embeds selected libX11 1.8.13 sources (KeyBind/KeysymStr/Quarks/StrKeysym/Xrm,
  XKBGeom/XKBMisc/XKBMAlloc/XKBGAlloc/XKBAlloc, +xkbcomp proper)
    ↓ client-side Xlib references (protocol + read-buffer + locking)
Xlorie --whole-archive ${XSERVER_LIBS}
    ↓ --no-undefined failure (19 total with EGL)
```

Prohibited: full libX11 restoration, fake Xlib stubs, global whole-archive
removal, weakening `--no-undefined`.

### Implemented S3-X1 closure

The dead client-side protocol functions are now excluded from the existing
single `xkbcomp` static target under `XKBCOMP_NO_XLIB_PROTOCOL`. Live pure
compute and keysym/database functions remain. Canonical clean-link evidence is
in `evidence/session/s3/GATE-S3-LINK.md`.