# S3 Build Commands (only commands actually run and observed)

## Canonical Gradle-native arm64 (the qualification path)

```bash
./gradlew --no-daemon --no-build-cache \
  ':lorie:buildCMakeDebug[arm64-v8a]'
```

Run from the worktree root (`src/f8-ahb` or `/tmp/b3a-pristine-r3`).
Requires untracked `local.properties` with `sdk.dir=/root/android-sdk`.
Full log of the historical dirty-tree run: `/tmp/b3a-gradle-native.log`
(observed before S3 implementation: 536/536 compiled, link failed on the 19).

Current S3 clean-link run:

```text
log: `/tmp/s3-canonical-gradle.log`
result: BUILD SUCCESSFUL in 17s
artifact: `lorie/build/intermediates/cxx/Debug/01x55434/obj/arm64-v8a/libXlorie.so`
SHA256: `e6317851a1d020d3c0a4eeb7a4d48e50d05744e9d40a643580b6201a415eeab7`
```

## Fresh manual CMake (forensic, approved parameters)

```bash
NDK=/root/android-sdk/ndk/29.0.14206865
SRC=<worktree>/lorie/src/main/cpp
rm -rf /tmp/b3a-fresh-arm64
cmake -S "$SRC" -B /tmp/b3a-fresh-arm64 \
  -G Ninja \
  -DCMAKE_MAKE_PROGRAM=/usr/bin/ninja \
  -DCMAKE_TOOLCHAIN_FILE="$NDK/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a \
  -DANDROID_PLATFORM=android-24 \
  -DCMAKE_BUILD_TYPE=Debug \
  -DANDROID_STL=c++_shared \
  -DANDROID_NDK="$NDK"
ninja -j2 -C /tmp/b3a-fresh-arm64 Xlorie
```

Repro inputs were reconstructed from the old `.cxx` `CMakeCache.txt` (no
`build_command.txt` exists). Resource rule: `-j2` (never bare parallel ninja
on this 8-core / ~3 Gi-reclaimable host).

## Pristine worktree

- Path: `/tmp/b3a-pristine-r3` (registered worktree, detached `9822435`).
- Submodule procedure actually used: `git submodule update --init --recursive
  --no-fetch` (zero network; a prior session's slimmed/deleted submodule files
  and wrong-commit checkouts were restored to pins from local objects, then
  verified clean), plus untracked `local.properties` as above.
- Build command: same canonical Gradle-native task as §1.
- Logs: `/tmp/b3a-pristine-gradle*.log` (first: missing-sdk env failure;
  setgid compile stop; quad stop; …; final: same link-19).

## Single-target ninja diagnostics (approved pattern)

```bash
ninja -j1 -C <build-dir> CMakeFiles/<target>.dir/<path>/<tu>.o
```

Used TU-by-TU for root-causing blockers without full rebuilds.
