# S3 CI Paradox (facts only — no guessing why CI succeeded)

## Authority

```text
GitHub Actions run: 34168546084 (workflow: Build, branch f8-p2-b2-over)
HEAD: 98224356e40913dcf2188d18748eba9401639850
Result: SUCCESS (verified against the Actions record, not from memory)
Toolchain: NDK 29.0.14206865, ./gradlew assembleDebug
```

## CI artifact forensics (read-only, `/tmp/ci-r3-libs`, KEEP)

- `termux-x11-unstripped-libraries-for-ndk-stack` (28 MB): `arm64-v8a`,
  `armeabi-v7a`, `x86`, `x86_64` `libXlorie.so` (+ 7 MB APK artifacts alongside).
- arm64 `DT_NEEDED`: libGLESv2, libandroid, libmediandk, liblog, libm, libz,
  libEGL, libdl, libc (no X11 — as designed).
- `nm -D -u`: EGL KHR/OES imports present (normal imports, not evidence of
  anything wrong); **X11-family undefined count = 0** (all 13 re-checked
  including lowercase `_Xkb*`).
- Same AGP config hash (`01x55434`) as local — noted, no conclusion drawn.

## Local results on the same inputs

```text
fresh manual CMake (pristine configure, same NDK/target/ABI/Debug) → same 19
canonical Gradle dirty (pristine staging, --no-build-cache)          → same 19
pristine R3 + buildability-only canonical Gradle                     → same 19
```

So: stale-`.cxx` hypothesis = CLOSED; B3a-dirty-changes-as-cause = CLOSED
(pristine+repairs-only reproduces byte-identical unique-19 list).

## Open divergence

```text
CI/local divergence = OPEN
```

Allowed statements only:

```text
UNKNOWN:
- CI cache state at run time
- exact CI linker/stub provenance
- historical AGP/CMake behavior on the runner
- hidden environment divergence (e.g. NDK content assembly)
```

Strengthened local facts constraining the unknown: canonical link carries
`--no-undefined` + `--whole-archive` from committed recipe with NO section-GC
flags anywhere; local NDK revision string matches CI nominally
(29.0.14206865); submodules pinned and clean.
