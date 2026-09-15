# PID 21639 PROTO=0 SIGSEGV forensics — d9b7f60 — 2026-09-15

Read-only. First cell `r1-proto0-oracle/` preserved. No source mutation.
R3 on the same APK already PASS (`r3-single-direct/`). Do not silent-retry
PROTO=0. Do not treat this as an xpump READY-path defect.

## Bind

| | |
|---|---|
| APK | `1.03.01-d9b7f60-14.09.26` CI 34872266646 |
| Unstripped ELF | `p2-r3-xpump-ci-34872266646/unstripped/01x55434/obj/arm64-v8a/libXlorie.so` |
| Build ID | `2b02bf139236d45aaa24a95fa8609cca0d956e7d` MATCH |
| X | PID **21639** PROTO=0, died before holder |
| Authority | siginfo + Uraw; Uctx parse advisory (`InitOutput.c` `p2a3DumpUraw`) |

## Observed

```text
Uctx signo=11 si_code=1 si_addr=0 PC=0x4800229c
LR=0x6effd2b8e0 SP=0x7fcc0d4090 FP=0x7fcc0d40d0
x0=0x61 x1=0x680f338 x2=0x20 x3=0x1 x4=0x61 x8=0x3
Uraw 52 last qword = 0x4800229c (same as Uctx PC)
Uraw 60 qwords 0x6e6f4d656c646e75 0x62757453726f7469
  → ASCII fragment "undleMonitorStub" (ART)
maps: 48000000-4a000000 r-xs [anon_shmem:dalvik-jit-code-cache]
Sbt 0 xorg_backtrace+0x48
Sbt 1 libXlorie.so+0xef620 → p2a3CrashHandler InitOutput.c:425 EXACT
Sbt 2 0x71db73d874 unsymbolized
```

`llvm-addr2line` on `0xef620` is the **handler** after it requested
`xorg_backtrace()`, not the original fault instruction.

Uctx PC `0x4800229c` is inside the live `dalvik-jit-code-cache` mapping.
`si_addr=0` / `si_code=1` is a null MAPERR while executing that JIT page.

## Same class as 21977 / B3a U4 (PROVEN match)

| | 21639 (`d9b7f60`) | 21977 (`6c7ee6f`) |
|---|---|---|
| signo / si_code / si_addr | 11 / 1 / 0 | 11 / 1 / 0 |
| x0–x8 | identical | identical |
| Uraw 60 ART fragment | identical qwords | identical qwords |
| PC | `0x4800229c` | `0x4800226c` |
| PC mapping | dalvik-jit-code-cache | same 0x4800xxxx class |

PC differs by `0x30` on the same JIT page. Not a new xpump-pump class.

## Classification

```text
OBSERVED: startup SIGSEGV in ART JIT cache during PROTO=0 X start
NON-REPRODUCED: authorized rerun PASS X 27435
ROOT CAUSE: NOT PROVEN (why JIT code null-dereferenced)
FALSIFIED: “record-aware X pump caused 21639”
  — PROTO=0 does not take the READY waiter; R3 PROTO=1 PASS
SOURCE FIX: NOT AUTHORIZED from this packet
```

Original fault instruction inside JIT code is **NOT LOCALIZABLE** to a
libXlorie source line. Do not “fix” `lorieGateAPumpConnection` from this
cell.

Evidence: `r1-proto0-oracle/` + `forensics/`.
