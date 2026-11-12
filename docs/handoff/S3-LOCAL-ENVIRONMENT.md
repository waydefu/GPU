# S3 Local Environment (verified 2026-09-09 ~18:52 CST, read-only)

No passwords, tokens, or credentials are recorded here.

## Host

| Item | Value |
|---|---|
| hostname | localhost |
| OS / distro | Ubuntu 24.04.4 LTS (PRoot container on Android Termux) |
| kernel | 6.17.0-PRoot-Distro SMP PREEMPT_DYNAMIC, aarch64 |
| arch | aarch64 |
| CPU | 8 cores (`nproc`) |
| RAM | 14 Gi total / ~9.8 Gi used / ~1.1 Gi free / ~4.9 Gi available |
| swap | 15 Gi total / ~5.6 Gi used / ~10 Gi free |
| filesystem | `/dev/block/dm-62` (Android dm device) |
| `/` | 477 G total / 417 G used / 60 G free (88%) |
| `/tmp` | same device as `/` (Termux private tmp); 60 G free (88%) |
| shell / user | bash / root |
| timezone | CST (UTC+08:00) |
| pwd at capture | `/root/projects/GPU加速` |

Build-resource rule derived from this host: default to `ninja -j2`; a `-j10`
default parallel native build risks OOM (observed concern, 8 cores vs ~3–5 Gi
reclaimable). If a build dies with SIGKILL/-9, treat as resource pressure, NOT a
source failure; drop to `-j1` once before stopping.

## Android SDK / NDK (verified, not from memory)

| Item | Value |
|---|---|
| SDK root | `/root/android-sdk` (locally assembled ARM64-compatible layout, NOT a stock x86_64 CLI install) |
| NDK | `/root/android-sdk/ndk/29.0.14206865` (`Pkg.Revision = 29.0.14206865`) |
| clang | `clang version 21.1.8`, default target `aarch64-unknown-linux-android24` (binary used lives under `toolchains/llvm/prebuilt/linux-x86/bin/`) |
| lld | `LLD 21.1.8` |
| target triple | `aarch64-linux-android24` |
| qualification API level | `android-24` (`ANDROID_PLATFORM=android-24`, `minSdkVersion 24`) |
| ABI (this round) | `arm64-v8a` only |

Sysroot facts relevant to S3 (all probed, not assumed):

- `EGL/egl.h`, `GLES2/gl2.h`, `KHR/khrplatform.h` all PRESENT in the NDK sysroot.
  A prior "missing EGL headers" diagnosis was a false alarm caused by an ad-hoc
  compile command without `--sysroot`.
- NDK `libEGL.so` stub exports 44 symbols, all CORE names (`eglCreateSync`,
  `eglCreateImage`, …). KHR-suffixed aliases (`eglCreateSyncKHR`,
  `eglCreateImageKHR`, …) are ABSENT from the stub.
- NDK `libGLESv2.so` stub does NOT export `glEGLImageTargetTexture2DOES`.
- NDK `sys/shm.h` exists but defines NO `SHMLBA` anywhere in this sysroot
  (recursive grep over `usr/include`, zero hits).
- NDK `sys/mman.h` hides `memfd_create` behind an API-30 availability guard;
  targeting android-24, the declaration is invisible.
- NDK `libgen.h` is pristine stock AOSP (declares POSIX `basename`); it was
  never modified.
- NDK clang predefines ONLY `__ANDROID__` (plus `__ANDROID_API__=24`);
  bare `ANDROID` is NOT predefined and no `-DANDROID` is passed.

## Java / Gradle / AGP / CMake / Ninja (verified)

| Item | Value |
|---|---|
| java | OpenJDK 21.0.12 (Ubuntu 24.04 build) |
| Gradle wrapper | 9.7.0 (`gradle-9.7.0-all.zip`) |
| AGP | 9.3.1 (`com.android.tools.build:gradle:9.3.1`) |
| system cmake | 3.28.3 (`/usr/bin/cmake`) |
| SDK cmake package | 3.22.1 present under `/root/android-sdk/cmake` |
| ninja | 1.11.1 (`/usr/bin/ninja`; SDK ninja same version) |
| compileSdk / targetSdk / minSdk | 34 / 34 / 24 (`lorie/build.gradle`) |
| build type (this round) | Debug |
| STL | `c++_shared` |
| canonical native task | `./gradlew --no-daemon --no-build-cache ':lorie:buildCMakeDebug[arm64-v8a]'` |
| local SDK pointer | `local.properties` (`sdk.dir=/root/android-sdk`, untracked, per-worktree) |

Note: no `build_command.txt` exists under `.cxx`; the reproducible configure
inputs were reconstructed from `CMakeCache.txt` (ABI/PLATFORM/NDK/Debug/STL/
toolchain file) for the manual fresh-build forensic.
