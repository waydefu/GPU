# S3 Runtime Qualification Gate

## Verdict

```text
S3 LINK: CLOSED
S3-Q1: CLOSED
S3-E1b: CLOSED
S3-X1: CLOSED
S3 RUNTIME: CLOSED — PASS WITH OBSERVABILITY LIMITATION
BUILD RECOVERY: CLOSED
B3a: UNBLOCKED
S3 observability follow-up: OPTIONAL / DEFERRED
Direct per-entry EGL/fence/GL-OES proc telemetry: NOT EMITTED
Stable: UNTOUCHED
```

The E1b candidate installs and launches on the built-in display without the
previous null-PLT SIGSEGV. XKB, keyboard, R3 exact, x100, mixed100, lifecycle,
and minimal desktop smoke all passed. The frozen candidate does not emit a
separate per-entry proc-resolution log, so those individual proc values remain
an explicit observability limitation rather than an invented PASS.

## Runtime display and lifecycle boundary

Any future S3 runtime attempt must target only the F8 Ultra built-in display
(`displayId=0`). An attached HDMI/external display may remain connected, but it
must not be the test target. Display-mode switching, projection, multi-window,
split-screen, floating-window mode, screen lock, backgrounding, swiping away the
Experimental app, and switching to another application are prohibited.

The built-in screen must remain awake and the Experimental app must remain in
foreground. If the desktop is not visible after launch, observe first through
pinned ADB: Experimental process liveness, `DISPLAY=:3`, X reachability,
initialization progress, and fresh crash/fatal logs. Do not classify a slow
initialization as failure while the process remains alive without explicit
failure evidence.

A process crash is a fresh failure and requires evidence plus STOP. Any manual
swipe-away or other user lifecycle action invalidates that attempt as
`INVALIDATED BY USER LIFECYCLE ACTION`; it is neither PASS nor FAIL.

## Historical pre-fix display/crash evidence

```text
attempts 1-2: INVALID — Activity focus was displayId=2 HDMI
correction: am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity
valid attempt: Experimental foreground/current focus on displayId=0
internal displayId=0: 1200x2608, ON
external displayId=2: HDMI 1920x1080, ON, non-target
valid :3 launch: FAIL — SIGSEGV / exit 139
```

The valid attempt targeted the built-in display. No display-mode, projection,
foreground, lock, swipe, or source operation was changed. Fresh valid-attempt
logcat: `/tmp/s3-runtime-logcat-all-20260910-display0.txt`.

## Current E1b runtime evidence

```text
source snapshot: 9b6420d0ef6a5587e412e37eaa0b4812e8501d72
APK SHA256: cd61a50e8c0bce90550e23dcd9bdd001c23d68e14145682346a7f89afb297988
embedded libXlorie SHA256: ffc07242accda5b93b9c4dc71ebc634ccf6814b6f30aa1f7a6b14f9acfd4d927
package: com.waydefu.x11gpu
versionName: 1.03.01-9b6420d-09.09.26
ADB identity/install: PASS
MainActivity target: displayId=0, foreground
X3 launch: PASS; survived launch, smoke, R3, stress, lifecycle windows
X server: xdpyinfo PASS; :3, root 0x511, 1200x2191, depth 24
XKB compile/load: PASS
keyboard ordinary/Shift/Ctrl/Alt: PASS
R3: 1514/1514, fail=0, maxDelta=0, Xnz=0, plus-minus-1=0
x100: 100/100
mixed100: 100/100
lifecycle: PASS; teardown and re-entry verified
minimal desktop smoke: PASS; xterm root child 484x316
RSS: 217688 kB observed; FD: NOT OBSERVED
```

Fresh summary: `/tmp/s3-e1b-runtime-summary-20260910.txt`.

## Native crash forensic result

The APK's exact stripped library has Build ID
`0bad26bceb046b741d40dade0575ae37457451c1`. No matching unstripped library
was found locally; the ARM64 unstripped snapshot candidate has no Build ID and
has different code at `+0xeb190`, so it was not used as an exact symbol file.

The APK LR maps to `+0xf2cc4`, immediately after:

```text
+0xf2cc0: bl eglGetNativeClientBufferANDROID@plt
+0x32f2f4: ldr x17, [x16, #2792]   # GOT +0x342ae8
+0x32f2fc: br x17
```

The APK marks the mangled `eglGetNativeClientBufferANDROID` symbol as weak
undefined; the valid crash has `PC=0`. The exact source call site in the frozen
snapshot is `lorie/src/main/cpp/lorie/renderer.cpp:480`, with the weak declaration
at line 33. Full report: `/tmp/s3-crash-symbolization-20260910.txt`.

No source was modified.

```text
HEAD:
98224356e40913dcf2188d18748eba9401639850 (baseline)

qualification snapshot:
9b6420d0ef6a5587e412e37eaa0b4812e8501d72

canonical native artifact:
/tmp/s3-qualification-snapshot/lorie/build/intermediates/cxx/Debug/01x55434/obj/arm64-v8a/libXlorie.so

libXlorie SHA256:
d3933497f38071558a8fa7adb829c066e96369ae2151ad5e358a8688fc7b04e4

qualification snapshot diff SHA256 (git diff --binary baseline..snapshot):
a49e0c2dd0f5ad179294d0d289e9edb66942f1e3bdea6ff23be7b0a928b9aaa9

candidate ABI:
arm64-v8a

ANDROID_PLATFORM:
android-24

NDK:
29.0.14206865

Gradle / AGP:
9.7.0 / 9.3.1

CMake:
system 3.28.3; SDK package 3.22.1

initial candidate freeze timestamp:
2026-09-09T21:06:30+08:00

qualification workflow commit timestamp:
2026-09-10T01:26:30+08:00
```

The main working tree remains the approved candidate and was not changed in this
runtime round. The qualification snapshot is committed on the disposable branch
at `272fd81148ff4d0e590fe01c52994c62f7620d32`; the only post-build change was
the approved workflow verification-path correction.

## SDK read-only inventory

```text
SDK root: /root/android-sdk
NDK: 29.0.14206865
ABI: arm64-v8a
ANDROID_PLATFORM: android-24
Gradle / AGP: 9.7.0 / 9.3.1
SDK CMake: 3.22.1
System CMake: 3.28.3
platforms/android-24: ABSENT
platforms/android-34: PRESENT
build-tools/35.0.0: PRESENT (Pkg.Revision=35.0.0)
build-tools/36.0.0: ABSENT
sdkmanager (pre-provision): ABSENT
licenses/android-sdk-license: PRESENT
licenses/cmake-3.22.1: PRESENT
```

Official Command-line Tools provisioning attempt:

```text
package URL:
https://dl.google.com/android/repository/commandlinetools-linux-15859902_latest.zip

official SHA256:
4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583

downloaded SHA256: identical
installed path: /root/android-sdk/cmdline-tools/latest
sdkmanager: 22.0, Java launcher works
android CLI binary: cannot execute on this aarch64 host
```

The final read-only license status still reports `7 of 7 SDK package licenses
not accepted` before the targeted interactive pass. The targeted pass accepted
only `android-sdk-license`; all other six exact IDs were answered `n`.

The approved install then created `build-tools;36.0.0`. During the subsequent
Gradle packaging attempt, Gradle automatically installed the unrequested
`platform-tools;37.0.1`; this is outside the approved package set. A rollback of
that exact new directory was attempted but the host authorization gate blocked
the deletion, so it remains present and is recorded as a blocker. No other SDK
package was requested or installed by the agent.

## Historical local qualification APK result

Expected canonical task:

```bash
./gradlew --no-daemon --no-build-cache ':lorie-app:assembleStandaloneDebug'
```

Intended package identity from the current build configuration:

```text
package: com.waydefu.x11gpu
versionCode: 15
versionName: NOT RESOLVED in the historical ARM64-local attempt; current
x86_64 artifact versionName is recorded in the verified S3-Q1 checkpoint below
```

Build logs:

```text
first attempt: `/tmp/s3-qualification-apk-build.log`
blocked on missing/unaccepted build-tools;36.0.0

second attempt: `/tmp/s3-qualification-apk-build-2.log`
platform-tools;37.0.1 was auto-installed by Gradle (unrequested)
then `:lorie:compileDebugAidl` failed while starting:
`/root/android-sdk/build-tools/36.0.0/aidl`
```

Exact second failure:

```text
A problem occurred starting process 'command /root/android-sdk/build-tools/36.0.0/aidl'
```

The exact OS-level start error is not present in the Gradle log; classify this
as host tooling/architecture, not as a source or runtime result.

Observed local tooling after the attempt:

```text
build-tools;35.0.0: present
build-tools;36.0.0: present (Pkg.Revision=36.0.0)
platform-tools;37.0.1: present, unrequested, rollback blocked by host authorization
sdkmanager: present at cmdline-tools/latest/bin/sdkmanager
```

APK:

```text
ARM64 local path: NOT PRODUCED (official SDK host-tool ISA mismatch)
ARM64 local SHA256: NOT AVAILABLE
```

No historical APK, repacked APK, or hand-replaced native library was used.

## Runtime gates

```text
ADB revalidation: PASS — 10.56.180.219:42761 / F8 identity verified
experimental package install: PASS — new base APK SHA256 matches
DISPLAY=:3 launch: PASS — survived launch, smoke, R3, stress, lifecycle windows
EGL 1.5 initialization: PASS observed
EGL/GL/fence typed dispatch: PASS static + behavioral path; per-entry telemetry NOT EMITTED
XKB compile/load: PASS
Keyboard ordinary/Shift/Ctrl/Alt: PASS
P2-B.2 R3 exact regression: PASS — 1514/1514, fail=0, maxDelta=0, Xnz=0, ±1=0
x100: PASS — 100/100
mixed100: PASS — 100/100
minimal desktop smoke: PASS
lifecycle sanity: PASS — teardown, absence, re-entry, teardown
resource sanity: RSS 217688 kB observed; FD NOT OBSERVED
```

Stable `com.termux.x11` package path was queried for existence only. Stable
`DISPLAY=:1` process/config/install/restart/kill operations were not performed
and Stable remains untouched.

## S3-Q1 x86_64 packaging attempt

GitHub Actions run `34362679522` on `ubuntu-24.04` completed runner and exact
SDK checks successfully:

```text
runner: X64 / x86_64
JDK: 21.0.12
Gradle: 9.7.0
AGP: 9.3.1
NDK: 29.0.14206865
Build Tools: 36.0.0
CMake: 3.22.1
compileSdk: 34
minSdk: 24
ABI: arm64-v8a
```

The run reached `:lorie:buildCMakeDebug[arm64-v8a]` and failed before APK
packaging. Exact error family:

```text
lorie/.cxx/Debug/01x55434/arm64-v8a/dix-config.h:174
  typedef long long quad_t;
lorie/.cxx/Debug/01x55434/arm64-v8a/dix-config.h:175
  typedef unsigned long long u_quad_t;
command line:
  -Dquad_t=long long -Du_quad_t=unsigned long long
error: cannot combine with previous 'long long' declaration specifier
```

This occurs because the x86_64 runner's target/sysroot headers already provide
the quad types while the current candidate's approved ARM64 portability define
is also injected. Classification: **new host-specific buildability blocker**.
It is not an S3-E1/X1 runtime result and not a source fix permitted in this
runtime round.

Run `34361917294` only failed the initial SDK-directory verification.
Run `34362679522` passed SDK verification but failed the candidate's native
quad-type collision before APK packaging.
Run `34379933169` passed x86_64/toolchain verification, native build, and
`:lorie-app:assembleStandaloneDebug`; its verification stopped because the
workflow used the wrong APK filename. That workflow path was corrected in
commit `272fd81148ff4d0e590fe01c52994c62f7620d32`.

## S3-Q1 verified packaging checkpoint

```text
workflow: S3 Q1 x86_64 APK
run: 34383008399
runner: ubuntu-24.04 / X64
head: 272fd81148ff4d0e590fe01c52994c62f7620d32
job: Canonical standalone APK (x86_64) — success
artifact id: 10116787938
artifact: s3-q1-apk-272fd81148ff4d0e590fe01c52994c62f7620d32
```

Exact artifact verification:

```text
APK: termux-x11-universal-debug.apk
APK SHA256: 27115b0f6c05ec22fe0cc2d7ea53e141596f2da0297f59b3df000af0f06a4be5
local SHA256 recheck: PASS
package: com.waydefu.x11gpu
versionCode: 15
versionName: 1.03.01-272fd81-09.09.26
embedded libXlorie.so SHA256: 1633716f443f69f6ff41ef38a03ee40a73d10f508174870344b553d078738ad9
forbidden undefined EGL/OES/X11/XKB symbols: none
full libX11 DT_NEEDED: absent
```

Package/version are from the x86_64 CI badging of the same SHA-verified APK;
local ARM64 `aapt2` cannot execute the official x86-64 SDK binary.

The embedded native hash differs from the prior ARM64-host artifact
(`da330ac50c1ca8bbe8604e9816d3157c8ae11bfcbab7dbb773d1e40a3a77d143`). The
workflow records this comparison as non-identical; cross-host bit identity is
not a required S3-Q1 gate. Source snapshot, exact toolchain, successful native
build, unresolved-symbol census, ELF policy, and fresh artifact provenance are
present. APK was not installed.

## Historical quad repair / host packaging blockers

The approved two-line repair was applied only in the disposable snapshot:

```text
xserver.cmake: removed xserver_os -Dquad_t/-Du_quad_t mirror defines
dix-config.h.in: #ifdef ANDROID -> #if defined(ANDROID) || defined(__ANDROID__)
```

F8 ARM64 canonical native validation then reached the final link, but failed on a
different symbol:

```text
log: /tmp/s3-q1-arm64-native-after-quad-fix.log
quad_t collision: not observed after the repair
link failure: undefined symbol: lorieRecheckGpuCopies
```

Patch-channel evidence:

- the new `xserver.patch` hunk is generated from the live submodule diff;
- isolated clean `present_scmd.c` hunk forward/apply/reverse with `--fuzz=0`
  passes and the resulting definition occurrence count is exactly `1`;
- the full `xserver.patch` now passes clean forward/apply/reverse checks with
  `--fuzz=0`;
- the restored clean baseline hashes match after reverse application;
- `lorieRecheckGpuCopies` definition count is exactly `1`;
- the snapshot was committed as `dc34253` before the workflow-only correction
  `272fd81`.

Classification: **closed provenance / buildability blockers**. The ARM64
canonical native build passed after the patch channel was repaired, and the
x86_64 run subsequently passed native build and APK packaging.

```text
host uname -m: aarch64

build-tools/36.0.0/aidl:
ELF 64-bit LSB pie executable, x86-64
interpreter /lib64/ld-linux-x86-64.so.2
readelf e_machine: Advanced Micro Devices X86-64

build-tools/36.0.0/aapt2: x86-64 ELF
build-tools/36.0.0/zipalign: x86-64 ELF
platform-tools/adb: x86-64 ELF
```

Gradle's exact failure from `/tmp/s3-qualification-apk-build-2.log`:

```text
Execution failed for task ':lorie:compileDebugAidl'
A problem occurred starting process
'command /root/android-sdk/build-tools/36.0.0/aidl'
```

Classification: **host ISA/tool execution mismatch**. This is not source
regression, S3-E1/S3-X1 regression, rendering failure, or runtime evidence.

## Current qualification boundary

E1b source/build/APK and behavioral runtime gates are complete. The only explicit
limitation is that the frozen dispatch implementation does not emit individual
proc-resolution telemetry; the PASS claim is based on typed static dispatch,
absence of the old direct weak symbol, successful launch/GPU path, and fresh
behavioral gates.

```text
S3 LINK: CLOSED
S3-Q1: CLOSED
S3-E1b: CLOSED
S3-X1: CLOSED
S3 RUNTIME: CLOSED — PASS WITH OBSERVABILITY LIMITATION
BUILD RECOVERY: CLOSED
Experimental install: PASS
`:3` displayId=0 launch: PASS
XKB/keyboard: PASS
R3 exact/x100/mixed100: PASS
minimal desktop/lifecycle: PASS
per-entry EGL/fence/GL-OES telemetry: NOT EMITTED (follow-up OPTIONAL/DEFERRED)
B3a: UNBLOCKED — measurement may start per GATE-P2-B.3a.md exact-next-measurement
Stable: UNTOUCHED
```

No source, build, patch, EGL, XKB, renderer, fence, routing, or Stable change was
made after E1b commit `9b6420d`. Final teardown left no Experimental X3 process.
