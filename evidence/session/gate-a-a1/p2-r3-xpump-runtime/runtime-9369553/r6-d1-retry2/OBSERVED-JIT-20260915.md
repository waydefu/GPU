# R6-D1-retry2 — OBSERVED ART JIT startup SIGSEGV — X 28170

Authorized 2026-09-15: finish D1 (fixture dest-Solid off Composite dest) then D2.
Device stayed `9369553`. Historical `r6-d1/` and `r6-d1-retry1/` not overwritten.

| | |
|---|---|
| Command | `VARIANT=d1 CELL=…/runtime-9369553/r6-d1-retry2` |
| Script exit | **2** `DIED_DURING_8S` |
| X `:3` | PID **28170** died during 8 s socket wait; fixture **never ran** |
| Fixture ELF | `634338035cb19ca8dd395c989c6a8544ea5cc18baf2042c4d6343c62204a70a8` |
| Env | `PROTO=1` `TELEMETRY=1`; OOM hook **unset** |
| Stable | PID **1004** UNTOUCHED |

Crash signature:

```text
Uctx signo=11 si_code=1 si_addr=0x0 PC=0x48000478
maps: 48000000-4a000000 r-xs [anon_shmem:dalvik-jit-code-cache]
libXlorie backtrace: xorg_backtrace / crash handler only
```

**OBSERVED:** ART JIT class (same family as X 21639 / 21977). Not a DDX / pump / fixture logic cell.

**NOT RUN:** D2-INFLIGHT, D2-OOM. Fail-closed: D1 did not complete; no silent-retry.

Do not overwrite this cell. Next D1 needs a new explicit bounded-rerun grant and a new cell path (`r6-d1-retry3`).
