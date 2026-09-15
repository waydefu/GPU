# D0b-R1 Native Build Verification — 2026-09-12

## SOURCE

```text
worktree: /root/projects/GPU加速/src/f8-ahb-d0b-r1
branch: qualification/d0b-r1-narrow-20260912
base HEAD: a6cc7952861b8a63740d42bf78553573cfa0eec0
source diff: six approved files only
git diff --check: PASS
```

## Linked-worktree prerequisites

The first verifier run failed before compilation because the new linked worktree
had no SDK path and incomplete submodule materialization. The main worktree
proved `sdk.dir=/root/android-sdk`. All 16 submodules were then initialized at
the superproject-pinned SHAs. Because PRoot left their linked worktree indexes and
working files empty, each newly created isolated submodule checkout was
materialized exactly from its own HEAD using `git read-tree HEAD` plus
`git archive HEAD`; no reset, checkout, dependency upgrade, or source revision
change was used. Every submodule then reported clean.

## Command

```bash
ANDROID_HOME=/root/android-sdk \
ANDROID_SDK_ROOT=/root/android-sdk \
./gradlew ':lorie:buildCMakeDebug[arm64-v8a]' --no-daemon
```

## RESULT

```text
CONFIGURE: PASS
NATIVE COMPILATION: STARTED
BUILD: FAIL
```

The native build reached Ninja and compiled many targets before `InitOutput.c`
failed with three D0b errors:

```text
InitOutput.c:2299:13: error: invalid argument type 'void' to unary expression
    if (!RegionInit(&exaGpuComp.d0bRegion, NULL, 0))

InitOutput.c:2423:9: error: invalid argument type 'void' to unary expression
    if (!RegionInit(&one, (BoxPtr) box, 1))

InitOutput.c:2425:9: error: invalid argument type 'void' to unary expression
    if (!RegionInit(&combined, NULL, 0))
```

`RegionInit` returns `void` in this X server API. The writer's static string test
did not detect this compile-time contract error.

Existing unrelated warnings were emitted but were not the build-stopping error.
No AIDL packaging task, APK, device, or runtime operation was attempted.

## POST-BUILD STATE

- Isolated worktree: exactly six D0b files modified; `git diff --check` passes.
- Main D0a worktree: clean at `a6cc795...`.
- Stable/device: untouched.
