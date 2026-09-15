# Gate A A1 crash forensics — 2026-09-12

SCOPE AND STOP RULE

This is read-only forensic closure against the retained packet. No retry, device action, source mutation, build, or fix was performed. The result is a crash classification, not a Gate A architecture verdict. The historical U4 startup SIGSEGV in HANDOFF is preserved as `observed / non-reproduced / root cause unknown`; it is separate from the current PID 21238 event.

PROVENANCE GATE — EXACT BUILD-ID BINDING

- Checkpoint/HEAD: `3db76baa15c0a6c13460349060485d863102dc86`.
- APK: `/root/projects/GPU加速/evidence/session/gate-a-a1/artifacts/34688831275/termux-x11-universal-debug.apk`; recomputed SHA256 `5a241f1fb726ecd709ecd601d80f607cbe3413a061d9c1cec66fd27009603583`.
- Matching unstripped ARM64 ELF: `/root/projects/GPU加速/evidence/session/gate-a-a1/artifacts/34688831275/01x55434/obj/arm64-v8a/libXlorie.so`; recomputed SHA256 `6612aa2ee2888d32a3892cad9edb807e90dd21f524557e7af83188b08252a79f`.
- Embedded extracted ELF and unstripped ELF both read Build ID `8036f683d110370a7a39dfd719cae9a6ee0adee3`; equality PASS. Symbolization proceeded only after this match.
- Available symbolizer/objdump: `/data/data/com.termux/files/usr/bin/llvm-symbolizer`, `llvm-addr2line`, `llvm-objdump`, LLVM 21.1.8. The NDK 29 x86_64 binaries were not executable/present on this aarch64 host; this is recorded as a tool-path limitation, not an ELF substitution. The ELF/DWARF binding is exact.

CURRENT SIGNAL AND TIME

Full main-log evidence shows PID 21238 loading the exact library at `2026-09-12 19:48:15.782 +0800`, printing the checkpoint at `.783`, installing/using the observe-only P2-A.3 path, and writing the signal-handler backtrace at `.795`–`.797`.

- Identity: `termux-x11gpu com.waydefu.x11gpu :3`, Android PID `21238`.
- `Uctx signo=11 si_code=1 si_addr=0x0000000000000000 PC=0x0000000048000478 LR=0x0000007c3d72b8e0 SP=0x0000007fd45a5620 FP=0x0000007fd45a567c x0=0x000000000000001c x1=0x00000000064fd440 x2=0x0000000006471e10 x3=0x000000000000001d x4=0x0000000000000001 x5=0x000000000000001c x6=0x0000000000000061 x7=0x0000000000000000 x8=0x0000000000000058`.
- `Ssig signo=11 code=1 addr=0x0000000000000000 (rt_sigaction+ucontext)`.
- Current handler frames: frame 0 `libXlorie.so (xorg_backtrace+0x48) [0x7b7ab270bc]`; frame 1 `libXlorie.so (?+0xeccf8) [0x7b7a903cf8]`; frame 2 `? (?+0x0) [0x7f0b0e0874]`.
- The full current-run crash-buffer file has no PID 21238/native current entry. Its entries are historical and were not counted. The authoritative current signature is the timestamped main-log handler output plus the launcher snap.

SYMBOLIZATION — EXACT / CONTROL-FLOW-EXACT / INFERRED-SOURCE

1. `xorg_backtrace+0x48` observed at `0x7b7ab270bc` maps to ELF relative `0x3100bc` using load bias `0x7b7a817000` (`0x7b7ab270bc - (0x310074 + 0x48)`). Exact DWARF resolves to `xorg_backtrace`, `xserver/os/backtrace.c:369:1`. `EXACT`.
2. `libXlorie.so+0xeccf8` at `0x7b7a903cf8` maps to the same bias plus `0xeccf8`. Exact DWARF resolves to `p2a3CrashHandler`, `lorie/InitOutput.c:365:15`; function start `0xeb8c4` resolves to `InitOutput.c:297`. `EXACT`.
3. The static existing startup wrapper `rendererTestCapabilities` at `0xf4ff4` resolves to `lorie/renderer.cpp:563`; `Renderer::testCapabilities` at `0xf4588` resolves to `renderer.cpp:368`. `EXACT` symbol/source binding.
4. The static Gate A entry `gateaA1MicroprobeRun` at `0xf7a88` resolves to `lorie/gatea_a1_microprobe.cpp:1175`. `EXACT` symbol/source binding, not runtime execution proof.
5. `gateaA1RunOne` is the source-level static worker at `gatea_a1_microprobe.cpp:688`; the entry body loops formats/runs at lines 1193-1197 and calls the worker at line 1196. This is source correspondence only for the runtime question. `INFERRED_SOURCE` when used to discuss whether the current process entered the body.
6. Frame 2 has no usable module/offset and is not symbolizable.

DECISIVE DISASSEMBLY

- Exact handler window (`llvm-objdump`, `/tmp/gatea-a1-objdump-handler.txt`):
  - `0xeccf0: bl p2a3WriteLine`
  - `0xeccf4: bl 0x333ee0 <xorg_backtrace@plt>`
  - `0xeccf8: add w0, w19, #0x80`
  - `0xeccfc: bl 0x333b00 <_exit@plt>`
  This proves the reported `+0xeccf8` frame is the existing signal handler immediately after it requested the auxiliary backtrace, not the original fault instruction. `CONTROL_FLOW_EXACT`.
- `xorg_backtrace@plt` is a normal AArch64 PLT sequence (`adrp/ldr/add/br x17`) with a `R_AARCH64_JUMP_SLOT` relocation to the defined `xorg_backtrace` symbol value `0x310074`; it is not a weak-undefined null target in this ELF.
- Exact renderer window (`/tmp/gatea-a1-objdump-renderer-testcap.txt`) shows the Gate A boundary in `Renderer::testCapabilities`: `eglMakeCurrent` returns, `lorieGlesDispatchInit` runs, `getenv("TERMUX_X11_GATEA_A1")` is called, bytes are checked for the exact string `"1"`, and `0xf4bf0: bl 0xf7a88 <gateaA1MicroprobeRun>` is followed by the pre-existing `glActiveTexture` path. `CONTROL_FLOW_EXACT` static boundary only.
- Checkpoint source ties the same route to `InitOutput.c:1343 rendererTestCapabilities(...)`, `renderer.cpp:563` wrapper, and the existing `Renderer::testCapabilities` body. The source hook is `renderer.cpp:535-537`; the probe capture/loop/worker sequence is `gatea_a1_microprobe.cpp:1183-1204` and `:688-745`.

CONTROL-FLOW CLASSIFICATION

- Proven: `PREEXISTING_STARTUP_PATH` at the handler level only. The current process reached the pre-existing P2-A.3 SIGSEGV handler installed from `OsVendorInit`; the current main log contains the P2-A.3 diagnostic immediately before the handler output.
- Not proven: `PROBE_BODY_CONFIRMED` — no `GATEA_A1` run/aggregate line returned.
- Not proven: `PROBE_CALL_BOUNDARY/ENTRY_ONLY` at runtime — the exact binary contains the call boundary, but no runtime register/PC/backtrace evidence reaches `gateaA1MicroprobeRun` or `gateaA1RunOne`.
- Original fault localization: `NOT LOCALIZABLE`. The Uctx PC `0x48000478` is not an address in the exact ELF; the Uctx LR `0x7c3d72b8e0` is outside the derived libXlorie mapping and yields no usable ELF call site. No exact call instruction, target register, or runtime GOT value can be derived from this packet.
- The absence of `GATEA_A1` lines is deliberately not used as negative proof: the source logs each run only after `gateaA1RunOne` returns.

WEAK / UNDEFINED / RELOCATION CHECK

- The exact ELF has weak undefined `AHardwareBuffer_allocate`, `AHardwareBuffer_lock`, `AHardwareBuffer_unlock`, `AHardwareBuffer_sendHandleToUnixSocket`, `AHardwareBuffer_release`, `AHardwareBuffer_describe`, and `AHardwareBuffer_recvHandleFromUnixSocket`. `nm -D -u` records them as weak (`w`); `readelf -WsW` records `WEAK DEFAULT UND`.
- Their static relocations are `R_AARCH64_JUMP_SLOT`, including allocate `0x347db0`, lock `0x347db8`, unlock `0x347dc0`, send `0x347dc8`, release `0x347e08`, describe `0x347e40`, and recv `0x347f70`. The corresponding PLT uses `br x17` through the GOT.
- `eglGetNativeClientBufferANDROID` is absent from the exact ELF's dynamic undefined-symbol census and relocation search. No direct weak/mangled EGL candidate is present.
- These weak AHardwareBuffer entries are a static candidate inventory for the probe/renderer path, not a crash-site finding: the only localized current frame is the handler epilogue, which contains no AHardwareBuffer call; the Uctx PC/LR cannot bind to any of these PLT entries. Therefore no direct null-call chain is proven.
- Precision labels remain separate: Build-ID/DWARF symbolization is `EXACT`; handler and static call-window conclusions are `CONTROL_FLOW_EXACT`; any claim that the current signal occurred before/inside the probe body is only `INFERRED_SOURCE` and is not accepted as a verdict.

ROOT CAUSE

`UNKNOWN`. The evidence proves a new startup SIGSEGV with `SEGV_MAPERR`-class null address and a custom handler backtrace, but not the original fault instruction, target, or resource operation. No root cause is declared.

MINIMAL FALSIFIER RECOMMENDATION — ONE ACTION, NOT EXECUTED

For Sol decision only: if further work is authorized later, add one synchronous fail-safe marker immediately on entry to `gateaA1MicroprobeRun`, before GL-state capture and before `gateaA1RunOne`; use that single marker to split “probe entered” from “pre-probe startup.” Do not retry this crash or mutate the source in this closure.

FORENSIC INPUTS AND REPORTS

- `/root/projects/GPU加速/evidence/session/gate-a-a1/runtime/r3-x3-launcher.raw.log`
- `/root/projects/GPU加速/evidence/session/gate-a-a1/runtime/r3-crash-logcat-main-full-20260912T114844Z.raw.txt`
- `/root/projects/GPU加速/evidence/session/gate-a-a1/runtime/r3-crash-logcat-system-full-20260912T114906Z.raw.txt`
- `/root/projects/GPU加速/evidence/session/gate-a-a1/runtime/r3-crash-logcat-crash-full-20260912T114928Z.raw.txt`
- `/root/projects/GPU加速/evidence/session/gate-a-a1/runtime/r5-crash-logcat-after-teardown-full-20260912T115200Z.raw.txt`
- `/tmp/gatea-a1-objdump-handler.txt`
- `/tmp/gatea-a1-objdump-renderer-testcap.txt`
- `/tmp/gatea-a1-libXlorie-nm.txt`
- `/tmp/gatea-a1-libXlorie-readelf-symbols.txt`
- `/tmp/gatea-a1-libXlorie-readelf-relocs.txt`
- `/tmp/gatea-a1-libXlorie-undefined.txt`
