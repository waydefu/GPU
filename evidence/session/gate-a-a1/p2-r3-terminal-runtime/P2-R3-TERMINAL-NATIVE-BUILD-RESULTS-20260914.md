# ARM64 native build results — 2026-09-14

Worktree `/root/projects/GPU加速/src/f8-ahb-gatea-a1`
HEAD after commit: `88e3f176d5be313b7dee058da9021cfe8d09e7de`

## Environment

Recorded: `build-env-utf8-20260914.txt`
`LANG=C.UTF-8` `LC_ALL=C.UTF-8` `LANGUAGE=C.UTF-8`
Java `file.encoding` / `native.encoding` / `sun.jnu.encoding` = UTF-8.

SDK via command-local `ANDROID_HOME=/root/android-sdk` only.
`local.properties` was not created and is not committed.
CMakeCache `ANDROID_NDK=/root/android-sdk/ndk/29.0.14206865`.

## Frozen first-failure log (do not overwrite)

`P2-R3-TERMINAL-NATIVE-BUILD-20260914.log`

1. First attempt: `GPU??????` wrapper-jar decode (CLOSED by UTF-8 locale).
2. UTF-8 retry without SDK: `:lorie` configure “SDK location not found”.

## Incremental retry (SDK env)

Log: `P2-R3-TERMINAL-NATIVE-BUILD-SDKENV-RETRY1-20260914.log`

```text
shell EXIT: 0
BUILD SUCCESSFUL in 45s
2 actionable tasks: 2 executed
UTF-8 path: GPU加速 (no GPU??????)
C/C++: ninja compiled activity.cpp, cmdentrypoint.cpp, renderer.cpp, InitOutput.c
```

## Full-clean

Log: `P2-R3-TERMINAL-NATIVE-BUILD-FULL-SDKENV-20260914.log`

```text
shell EXIT: 0
BUILD SUCCESSFUL in 3m 4s
5 actionable tasks: 5 executed
:lorie:externalNativeBuildCleanDebug then fresh ninja
libXlorie.so mtime 2026-09-14 16:18:44 +0800
```

## Warning fingerprint

Compared unique (file, -Wflag, message) ignoring line-number drift.

| Baseline | New unique | Gone unique |
|---|---|---|
| 15caa00 `GATE-A-P2-B1-B4-NATIVE-BUILD-FULL-20260914.log` | 0 | 0 |
| R1 `GATE-A-P2-R1-DIAG-NATIVE-BUILD-FULL-20260914.log` | 0 | 0 |

Pre-existing lorie warnings (line drift only): `c99-designator` keycode
table, `reorder-init` AHB desc, two `%llu` in renderer, `%llu` in
activity/cmdentrypoint. xserver `typedef-redefinition` is in every local
full-clean, not a new source warning. CI ninja stdout omits some of those
include warnings; local Gradle C/C++ wrapper is the ARM64 authority here.

NEW WARNINGS: 0
