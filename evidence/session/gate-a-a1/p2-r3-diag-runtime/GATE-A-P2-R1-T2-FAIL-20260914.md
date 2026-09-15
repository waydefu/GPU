# Gate A P2 R1 T2 FAIL — 6c7ee6f SIGSEGV PID 21977 — 2026-09-14

Installed peek-diag APK `6c7ee6f` (CI 34789717269, SHA256
`d20e6091817db1ba7eb449f34a0a967ff61d498b42ab0ae1b38f9591d11a4e8a`,
Build ID `49be84eaf4ded3e876f530b132ab25f6099aae00`) over experimental
only. Screen Awake, `isKeyguardShowing=false`, `--display 0`.

## Matrix (stopped; do not silent-retry B2)

| Cell | Mode | X PID | Result |
|---|---|---|---|
| t2-A1-unset | unset | 19329 | PASS ALIVE_AFTER_8S NO_X3_RESIDUE |
| t2-B1-proto0 | PROTO=0 | 20375 | PASS ALIVE_AFTER_8S NO_X3_RESIDUE |
| t2-A2-unset | unset | 21393 | PASS ALIVE_AFTER_8S NO_X3_RESIDUE |
| t2-B2-proto0 | PROTO=0 | **21977** | **FAIL SIGSEGV within 8s** |
| t2-A3-unset | | | NOT RUN |
| t2-B3-proto0 | | | NOT RUN |

Stable `:1` PID **16085** throughout. `com.termux.x11` lastUpdateTime
2026-09-07 22:55:03. HDMI observe-only.

## Crash (authoritative capture)

Handler is `p2a3CrashHandler` (`InitOutput.c:425`). Debuggerd did **not**
write a tombstone for 21977 (newest device tombstone remains 2026-09-14
06:03, unrelated). A first `tombstone_00` pull was **surfaceflinger
2026-09-13** and is not this crash.

```text
Uctx signo=11 si_code=1 si_addr=0x0000000000000000
PC=0x000000004800226c LR=0x0000007676d2b8e0
SP=0x0000007fe2da7750 FP=0x0000007fe2da7790
x0=0x61 x1=0x680f338 x2=0x20 x3=0x1 x4=0x61 x8=0x3
Upid pid=21977 tid=21977
Ssig signo=11 code=1 addr=0 (rt_sigaction+ucontext)
Sbt: xorg_backtrace+0x48 → p2a3CrashHandler (InitOutput.c:425)
     → 0x794540b874
Uraw 60 ASCII fragment: undefinedMonitorStub (ART)
```

Faulting PC is **not** in `libXlorie.so`. Unstripped Build ID MATCH
`49be84ea…ae00`. `llvm-addr2line` on Sbt offset `0xef09c` →
`p2a3CrashHandler` only.

## Classification (not a proven peek-diag regression)

Same class as historical B3a T2 U4 (`evidence/session/p2-b3a/t2-u4-batch16/`):

- identical `PC=0x4800226c`
- identical `x0..x8`
- LR same libc offset `…d2b8e0` (ASLR of mapping)
- `si_addr=0`

Related family (same `0x4800xxxx` page, different PC): A1 `PC=0x48000478`;
`15caa00` R1 PROTO=0 PID 31807 `PC=0x48000ec4`. Those remain OBSERVED /
root cause unknown. This event is a **new observation** of that class on
`6c7ee6f`. It is **not** merged into “fixed”. It is **not** proven to be
caused by the Activity peek-diag patch.

B1 PROTO=0 on this same APK **passed**. The crash is not “every PROTO=0”.

## Verdict

```text
T2 6/6: FAIL (stopped after B2)
ROOT CAUSE: NOT PROVEN
CLASSIFICATION: OBSERVED / same 0x4800226c class as B3a U4
SOURCE FIX: NOT AUTHORIZED from this cell
R1 oracle/stress: NOT RUN
R2 / R3: NOT AUTHORIZED until T2 policy is decided
Production Gate A: BLOCKED
```

Do **not** retry B2 silently. Do **not** treat A1/B1/A2 PASS as a T2 PASS.
Keep the matching unstripped ELF.

Evidence: `evidence/session/gate-a-a1/p2-r3-diag-runtime/t2-B2-proto0/`
and sibling PASS cells `t2-A1-unset`, `t2-B1-proto0`, `t2-A2-unset`.
