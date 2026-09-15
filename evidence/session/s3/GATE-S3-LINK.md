# S3 Clean-Link Gate Evidence

- Timestamp: `2026-09-09T20:39:46+08:00` (Asia/Taipei)
- Baseline HEAD: `98224356e40913dcf2188d18748eba9401639850`
- Scope: S3-E1 typed EGL/GL dispatch + S3-X1 embedded xkbcomp source closure only
- Stable: `com.termux.x11`, `DISPLAY=:1` — untouched
- Runtime: **NOT TESTED** in this round

## Verdict

```text
S3-E1: PASS — 6 EGL/OES unresolved -> 0
S3-X1: PASS — 13 X11/XKB unresolved -> 0
new unresolved family: 0
clean native link: PASS
runtime qualification: NOT EXECUTED
```

## S3-E1

Retained the approved typed Khronos PFN dispatch implementation:

- `lorie/egl_dispatch.h`
- `lorie/egl_dispatch.c`
- call-site changes in `lorie/buffer.c` and `lorie/renderer.cpp`
- `lorie/egl_dispatch.c` included in the existing `Xlorie` target
- EGL and GL extension capability checks remain separate
- `glEGLImageTargetTexture2DOES` is resolved only after a current GL context
- NULL proc remains fail-closed
- no KHR-to-core alias, ABI cast, stub, `glFinish` replacement, or fence-order change

The first E1 link had exactly the expected partial shape: the six EGL/OES symbols disappeared and the original 13 X11/XKB symbols remained.

## S3-X1

The approved single-target closure was implemented through the existing patch channel:

- `patches/x11.patch`
- `recipes/xkbcomp.cmake`
- named target-scoped define: `XKBCOMP_NO_XLIB_PROTOCOL`
- no second static library
- no full `libX11`
- `--whole-archive` and `--no-undefined` retained

Guarded dead client-side protocol implementation:

- `KeyBind.c`: Display/protocol key mapping paths
- `XKBGeom.c`: geometry reply/read-buffer transport and `XkbGetGeometry*`
- `Xrm.c`: display database access, combine/merge, file-combine, destroy

Retained and verified in object output:

- `XConvertCase`
- `UCSConvertCase`
- `XkbComputeShapeBounds`
- `XkbComputeSectionBounds`
- `XrmInitialize`
- `XrmGetFileDatabase`
- `XrmQGetResource`
- `XrmEnumerateDatabase`

The 13 target symbols are absent from `libxkbcomp.a` undefined symbols after pruning.

## Patch validation

Formal `x11.patch` validation used `patch --fuzz=0`:

```text
pristine forward dry-run: PASS (rc=0)
pristine apply:          PASS (rc=0)
pristine reverse dry-run: PASS (rc=0)
```

On the existing submodule state, the two already-applied historical Quarks/Xrm hunks are skipped and all eight new X1 hunks apply successfully. CMake reconfigure then completed with `rc=0` and applied the X1 patch to the build source.

## Build verification

Commands and logs:

```text
CMake configure:
  /tmp/b3a-s3x1-configure-2.log
  rc=0

xkbcomp compile:
  ninja -j2 -C /tmp/b3a-fresh-arm64 xkbcomp
  /tmp/b3a-s3x1-xkbcomp-2.log
  rc=0

fresh Xlorie link:
  ninja -j2 -C /tmp/b3a-fresh-arm64 Xlorie
  /tmp/b3a-s3x1-link-2.log
  rc=0

canonical Gradle-native:
  ./gradlew --no-daemon --no-build-cache ':lorie:buildCMakeDebug[arm64-v8a]'
  /tmp/s3-canonical-gradle.log
  BUILD SUCCESSFUL in 17s
  process rc=0
```

The Gradle output contained compiler/AGP/Gradle warnings, but no failed task or link error. Warnings are preserved in `/tmp/s3-canonical-gradle.log`; no warning standard was changed.

## Canonical ELF audit

Canonical artifact:

```text
/root/projects/GPU加速/src/f8-ahb/lorie/build/intermediates/cxx/Debug/01x55434/obj/arm64-v8a/libXlorie.so
SHA256:
e6317851a1d020d3c0a4eeb7a4d48e50d05744e9d40a643580b6201a415eeab7
```

`nm -D -u` target census:

```text
6 EGL/OES target symbols: absent
13 X11/XKB target symbols: absent
eglGetProcAddress: present
```

`readelf -d`:

```text
libGLESv2.so.2
libandroid.so
libmediandk.so
liblog.so
libm.so
libz.so.1
libEGL.so.1
libdl.so
libc.so
```

```text
full libX11 DT_NEEDED: absent
-Wl,--no-undefined: present
-Wl,--whole-archive: present
```

Fresh CMake artifact audit independently produced the same symbol/policy result; its SHA256 was:

```text
6f9282749369ecf613750a6b941dd398b3ba9a16418d2bb24a740ef85cc2616b
```

## Repository verification

```text
git diff --check: PASS
```

The working tree remains uncommitted. Existing B3a instrumentation and approved buildability changes were not reverted or rewritten. No APK was installed and no `:3` or `:1` process was touched.

## Next

**STOP at clean-link checkpoint.** The only next gate is runtime qualification after explicit runtime approval. No runtime, APK installation, R3 oracle, or B3a performance run was executed here.
