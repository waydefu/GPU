# S3 Runtime Environment (ADB identity PASS; first `:3` launch SIGSEGV)

The verified Experimental APK was installed, then its first minimal `:3` launch
crashed with SIGSEGV. No workload, retry, source change, or Stable operation was
performed. Anything not revalidated is marked LAST KNOWN. The authority for
runtime claims remains fresh evidence in this round.

## Stable (production daily driver — NEVER touch)

| Item | Value |
|---|---|
| package | `com.termux.x11` |
| display | `:1` |
| mode | `-legacy-drawing` |
| version (last known) | `1.03.01-11b82d9-06.09.26` |
| PID (last known, 2026-09-08) | 26474, ppid=4718 |
| state | UNTOUCHED through the entire B3a recovery loop |

Prohibited: reinstall, overwrite, kill, broad `pkill termux-x11`, experiment,
config change, reuse of the Stable package identity for tests.

## Experimental (only target)

| Item | Value |
|---|---|
| package | `com.waydefu.x11gpu` |
| display | `:3` |
| APK (current qualification) | `1.03.01-9b6420d-09.09.26` |
| APK SHA256 (current qualification) | `cd61a50e8c0bce90550e23dcd9bdd001c23d68e14145682346a7f89afb297988` |
| X process (current qualification) | survived launch/smoke/R3/stress/lifecycle; final teardown complete |
| display geometry | `:3` 1200x2191, root 0x511, depth 24 |
| current qualification HEAD | `9b6420d` (`9b6420d0ef6a5587e412e37eaa0b4812e8501d72`) |
| qualification APK | `termux-x11-universal-debug.apk` — verified, installed, behaviorally qualified |
| qualification APK SHA256 | `cd61a50e8c0bce90550e23dcd9bdd001c23d68e14145682346a7f89afb297988` |
| qualification version | package `com.waydefu.x11gpu`, versionCode `15`, versionName `1.03.01-9b6420d-09.09.26` |
| qualification source | GitHub run `34396950445`, artifact `10122068244` |
| qualification runtime | PASS behavioral gates; direct per-entry proc telemetry NOT EMITTED |
| XFCE on `:3` | bounded 45 s qualification only; never a daily session |

Kill/install safety (unchanged): stop `:3` + `am force-stop com.waydefu.x11gpu`
before any `pm install-commit`; kill only on exact cmdline
`termux-x11gpu com.waydefu.x11gpu :3`; never `pkill -f f8-x11gpu`; never
`logcat -c`. Experimental APKs are installed via staged sessions, never over
`com.termux.x11`.

## ADB and launch preflight (2026-09-10)

| Item | Result |
|---|---|
| Termux-native endpoint | `10.56.180.219:42761` |
| `adb devices -l` | `device`, product `myron_global`, model `25102PCBEG`, device `myron` |
| F8 identity | PASS — POCO / Xiaomi / Android 16 SDK 36 |
| Stable package path | PRESENT; no Stable process/config/install operation |
| E1b Experimental package | versionCode 15, base SHA `cd61a50e…` |
| MainActivity displayId=0 | PASS; foreground/current focus |
| `f8-x11gpu :3` | PASS launch and qualification windows; final exact teardown |
| xkbcomp/keymap | PASS |
| R3/x100/mixed100 | PASS |
| lifecycle | PASS |
| observability | per-entry proc telemetry NOT EMITTED |
| evidence | `/tmp/s3-e1b-runtime-summary-20260910.txt` |

## Device identity (fresh) / hardware values (last known)

| Item | Value |
|---|---|
| model | POCO F8 Ultra (myron_global) |
| Android | 16 (SDK 36), build fingerprint family `OS3.0.302.0` per TEST-MATRIX baseline |
| GPU | Adreno 840, `/dev/kgsl-3d0` accessible (`crw-rw-rw-`, last verified 09-07) |
| Termux | native (`termux-x11-nightly 1.03.01-6`, Mesa 26.0.6-3, freedreno ICD) |
| Ubuntu | 24.04 PRoot (Mesa 25.2.8, XFCE 4.18, OpenJDK 21) |
| GL path | Zink → Turnip → Adreno 840, GL 4.6, Accelerated: yes (via `f8-gpu` wrapper; bare `glxinfo` is llvmpipe as expected) |
| external 3440×1440 display path | NOT TESTED (never write FAIL for it) |

## ADB (fresh E1b session; final teardown complete)

| Item | Value |
|---|---|
| endpoint | `10.56.180.219:42761` |
| state | `device` at E1b identity/install/runtime; final X3/package teardown complete |
| transport | Termux-native `fakeroot env ANDROID_NO_USE_FWMARK_CLIENT=1 adb` |
| device | POCO / Xiaomi / `25102PCBEG` / `myron` / Android 16 SDK 36 |
| stale helper reference | prior `35859` wrapper output was invalid and discarded |
| runtime summary | `/tmp/s3-e1b-runtime-summary-20260910.txt` |
