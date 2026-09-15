# Gate A A1 microprobe execution — 2026-09-12

CONCLUSION

- STOPPED during Experimental `:3` startup/initialization after a new current-run native SIGSEGV. This is not an A1 pixel result and no Gate A architecture verdict is issued.
- A1 oracle coverage is `0/9 runs NOT TESTED`; `0/9 parsed`; no A1 JSON/CSV was produced.
- This closure pass was read-only against the retained source/remote/device packet. No adb/device command, retry, launch, stop, kill, logcat command, DISPLAY query, Stable operation, Experimental operation, HDMI operation, source/worktree edit, build, commit, push, CI, PR, merge, reset, clean, restore, or mutation was performed by this pass.

AUTHORITY AND ARTIFACT BINDING

- Source checkpoint: `3db76baa15c0a6c13460349060485d863102dc86`.
- Verified source HEAD: `3db76baa15c0a6c13460349060485d863102dc86`; source worktree status was clean at verification.
- Remote run: `waydefu/termux-x11` run `34688831275`, attempt 1, head SHA equal to checkpoint.
- Exact APK: `/root/projects/GPU加速/evidence/session/gate-a-a1/artifacts/34688831275/termux-x11-universal-debug.apk`.
- APK SHA256: `5a241f1fb726ecd709ecd601d80f607cbe3413a061d9c1cec66fd27009603583`.
- Exact unstripped ARM64 ELF: `/root/projects/GPU加速/evidence/session/gate-a-a1/artifacts/34688831275/01x55434/obj/arm64-v8a/libXlorie.so`.
- Unstripped ELF SHA256: `6612aa2ee2888d32a3892cad9edb807e90dd21f524557e7af83188b08252a79f`.
- Embedded and unstripped Build ID recomputation: both `8036f683d110370a7a39dfd719cae9a6ee0adee3`; equality PASS before symbolization.
- APK identity: package `com.waydefu.x11gpu`, versionCode `15`, versionName `1.03.01-3db76ba-12.09.26`, primary ABI `arm64-v8a`.
- The artifact packet retains its qualified limitations: formal host zipalign was blocked by the x86-64 tool on the aarch64 host; this runtime document does not promote that check.

DEVICE, INSTALL, AND INTERNAL DISPLAY VERIFICATION

- Retained fresh ADB preflight: endpoint `192.168.1.100:33635`, state `device`, exactly one authorized device, model `25102PCBEG`, device `myron`, Android 16 / SDK 36. Evidence: `r1-adb-devices-l-20260912T113855Z.raw.txt`, `r1-device-get-state-20260912T113911Z.raw.txt`.
- Exact Experimental install session: `pm install-create` succeeded; `pm install-write` streamed `14957326` bytes; `pm install-commit` returned `Success` (all status exit code 0). Evidence: `r2-pm-install-create-20260912T114246Z.raw.txt`, `r2-pm-install-write-20260912T114301Z.raw.txt`, `r2-pm-install-commit-20260912T114314Z.raw.txt` and its status file.
- Installed base APK readback SHA256 exactly matched the selected APK: `5a241f1fb726ecd709ecd601d80f607cbe3413a061d9c1cec66fd27009603583`. Evidence: `r2-readback-installed-base-apk-sha256-20260912T114407Z.raw.txt`.
- Installed package path and metadata matched the artifact: `/data/app/~~nsaYjK_z5JKm1pYcOeYFKw==/com.waydefu.x11gpu-cSbhgrv5JLN1sOfICQzpkA==/base.apk`, versionCode 15, versionName `1.03.01-3db76ba-12.09.26`, primary ABI `arm64-v8a`. Evidence: `r2-readback-experimental-path-20260912T114332Z.raw.txt`, `r2-readback-experimental-package-metadata-20260912T114351Z.raw.txt`.
- Internal-display launch was explicitly `am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity`, exit code 0. Evidence: `r3-activity-start-display0-20260912T114608Z.status.txt` and `.raw.txt`.
- Display verification passed for the packet: `Display #0` contained the Experimental MainActivity; it was top-resumed/resumed, `display=0`, current focus and focused app were `com.waydefu.x11gpu/com.termux.x11.MainActivity`, with a display-0 window. Evidence: `r3-dumpsys-activity-activities-20260912T114628Z.raw.txt:2-23,337-338,466-479`; `r3-dumpsys-window-20260912T114648Z.raw.txt:545-557,708-728`.
- The attached external display was not used for the Experimental placement. No display mode, projection, or windowing-mode change was made.

A1 MATRIX AND OBSERVABILITY

- CONTROL / `AHARDWAREBUFFER_FORMAT_R8G8B8X8_UNORM` / value 2: run1 `NOT TESTED`, run2 `NOT TESTED`, run3 `NOT TESTED`.
- BGRA_CANDIDATE / `AHARDWAREBUFFER_FORMAT_B8G8R8A8_UNORM` / value 5: run1 `NOT TESTED`, run2 `NOT TESTED`, run3 `NOT TESTED`.
- RGBA_DIAGNOSTIC / `AHARDWAREBUFFER_FORMAT_R8G8B8A8_UNORM` / value 1: run1 `NOT TESTED`, run2 `NOT TESTED`, run3 `NOT TESTED`.
- `DIRECT_FBO_DIAGNOSTIC=SKIPPED` is source-declared; its runtime line was not observed.
- No current-run `GATEA_A1` per-run segment, aggregate, state_restore line, EGL/GL status, classification, or returned run record was emitted. The harness logs each run only after `gateaA1RunOne` returns; absence of those lines is therefore not used to infer whether the probe body was entered.
- Actual server RSS, external FD count, explicit per-buffer release telemetry, lifecycle recreate cycle, and pixel verdict are `NOT OBSERVED`/`NOT TESTED`, not zero measurements.

CURRENT-RUN FATAL SIGNAL

- Current-run log time: `2026-09-12 19:48:15.795`–`19:48:15.797 +0800` in the full main log. PID 21238 had loaded the exact APK library at `19:48:15.782`, printed checkpoint `3db76baa...` at `19:48:15.783`, printed the P2-A.3 observe-only diagnostic at `19:48:15.792`, then emitted the custom signal-handler backtrace.
- Process identity: `termux-x11gpu com.waydefu.x11gpu :3`; Android log PID `21238`.
- Signal: `signo=11`, `si_code=1`, `si_addr=0x0000000000000000`.
- Uctx evidence: `PC=0x0000000048000478`, `LR=0x0000007c3d72b8e0`, `SP=0x0000007fd45a5620`, `FP=0x0000007fd45a567c`; recorded registers `x0=0x1c x1=0x64fd440 x2=0x6471e10 x3=0x1d x4=0x1 x5=0x1c x6=0x61 x7=0 x8=0x58`.
- Handler backtrace: frame 0 `libXlorie.so (xorg_backtrace+0x48) [0x7b7ab270bc]`; frame 1 `libXlorie.so (?+0xeccf8) [0x7b7a903cf8]`; frame 2 `? (?+0x0) [0x7f0b0e0874]`. Evidence: `r3-x3-launcher.raw.log:1-11` and timestamped `r3-crash-logcat-main-full-20260912T114844Z.raw.txt:70721-70733`.
- The current-run crash-buffer dump contains no PID 21238 record. Its fatal entries are older, including 2026-09-08/09-09/09-11/09-12 historical processes. Those entries are not counted as this crash. HANDOFF separately labels the older U4 startup SIGSEGV `observed / non-reproduced` with root cause unknown; it is not merged with this current-run event.

TEARDOWN AND SAFETY

- Exact Experimental force-stop after the crash returned exit code 0. No restart was performed.
- Post-crash and post-force-stop host scans both showed the same Stable process only: `pid=14862 cmdline=termux-x11 com.termux.x11 :1 -legacy-drawing`; `EXPERIMENTAL_MATCHES` was empty. Evidence: `r3-post-crash-host-proc-scan-20260912T115000Z.raw.txt`, `r5-post-force-stop-host-proc-scan-20260912T115105Z.raw.txt`.
- `DISPLAY=:3 xdpyinfo` after teardown failed with `unable to open display ":3"` (exit code 1), and no restart was performed. Evidence: `r5-display3-reachability-after-teardown-20260912T115141Z.raw.txt` and status.
- Stable `:1` remained untouched; its PID and cmdline were unchanged. HDMI was untouched: no HDMI command, mode change, projection change, or HDMI cleanup was performed.
- Runtime result is fail-closed/STOPPED. This document issues no Gate A architecture verdict.

RAW EVIDENCE PATHS

- Runtime summary: `/tmp/gatea-a1-runtime-01.stdout`.
- Runtime raw directory: `/root/projects/GPU加速/evidence/session/gate-a-a1/runtime/`.
- Current-run launcher: `r3-x3-launcher.raw.log`.
- Full current-run logs: `r3-crash-logcat-main-full-20260912T114844Z.raw.txt`, `r3-crash-logcat-system-full-20260912T114906Z.raw.txt`, `r3-crash-logcat-crash-full-20260912T114928Z.raw.txt`.
- Teardown crash dump: `r5-crash-logcat-after-teardown-full-20260912T115200Z.raw.txt`.
- Authority/provenance: `checkpoint-source-provenance.txt`, `GATE-A-A1-ARTIFACT-PROVENANCE-20260912.md`, `AUTHORITY-CHECKSUM-A1-ARTIFACT-20260912.md`.
- Device/install/display/cleanup raw files are the `r1-*`, `r2-*`, `r3-*`, and `r5-*` files named above; `command-ledger-20260912T113249Z.txt` is retained.
