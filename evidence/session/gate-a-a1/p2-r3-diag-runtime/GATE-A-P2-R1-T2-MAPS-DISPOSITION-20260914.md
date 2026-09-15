# T2 SIGSEGV PID 21977 — mapping disposition — 2026-09-14

Recorded crash on `6c7ee6f` remains **OBSERVED**. This note does not
retry B2 and does not convert T2 FAIL into PASS.

## Live maps (unset X PID 26015, same installed APK)

Experimental `:3` launched unset (the PASS path). Process is
`/system/bin/app_process64` with cmdline
`termux-x11gpu com.waydefu.x11gpu :3`. Stable PID **16085** untouched.
Teardown `NO_X3_RESIDUE`.

| Address from crashes | Live mapping |
|---|---|
| `PC=0x4800226c` (PID 21977, B3a U4) | `48000000-4a000000 r-xs [anon_shmem:dalvik-jit-code-cache]` |
| `PC=0x48000ec4` (`15caa00` PID 31807) | same JIT cache |
| `PC=0x48000478` (A1 PID 21238) | same JIT cache |
| `x1=0x680f338` (PID 21977 / B3a U4) | `06000000-26000000 rw-p [anon:dalvik-main space]` |

Fault PC is **ART JIT code**, not `libXlorie.so`. `x1` is **Java heap**.
X is `app_process` (`f8-x11gpu` execs `Loader`). `undefinedMonitorStub` in
Uraw is consistent with ART.

Exact JIT method / Java frame: **NOT PROVEN** (no tombstone; handler does
not dump maps; JIT bytes not captured). Gate A C++ NULL deref: **NOT
SUPPORTED** by this mapping.

## What this authorizes

- Keep PID 21977 as T2 FAIL / OBSERVED. Do not silent-retry that cell.
- Peek-diag `activity.cpp` is **not** a proven cause of this SIGSEGV.
- One **documented full T2 6/6 rerun** (new evidence dir, start at A1) is
  authorized to close T2 on this APK. If any cell SIGSEGVs, stop again.
- R1 oracle / R2 / R3 stay blocked until that rerun is 6/6 PASS.

Evidence: `t2-forensic-maps-unset/`.
