# Published subset — 2026-09-24 PRoot batch

Local evidence is complete; this repository carries the verdict basis only. Every run directory keeps its full
local `sha256sums.txt`; files listed there but absent here were deliberately not published:

```
raw-logcat.txt          full device logcat (6-63 MB per cell); not read by any judge
*.png                   end-of-run Cursor screenshots (binary); not read by the PROOT judge
```

Batch contents:
- PROOT-TRACER-OVERHEAD-01 (socket syscalls trapped since termux/proot 4abc88b5c) + proot-fast v1 patch, micro-benchmarks 01-03.
- PROOT-BENCH-01 (Cursor, stock proot vs proot-fast v1): freeze, dry-run 01 (metered from the wrong SELinux side; its
  survivors=0 was unverifiable) and dry-run 02, rep01/rep02 -> `PROOT_FAST_NO_BENEFIT` (CPU -5..9%, bar 10%).
- PROOT-KOMPAT-OVERHEAD-01: root cause - `--kernel-release` enables kompat, which traps futex / epoll_pwait / fcntl /
  pipe2 / ... for no-op handlers and drops the vDSO. proot-fast v2 (`proot-fast2-kompat-lean.patch`, `build2.sh`),
  micro-benchmark (`proot-fast2-bench-01.txt`), functional smoke (identical to stock), AGENT-MIX (-53% wall / -54% CPU).
- PROOT-BENCH-02 (Cursor, stock vs v2, thresholds identical to 01): dry-run (BLOCKED cell kept: screen locked),
  dry-run 2, rep01/rep02 -> `PROOT_FAST_NO_BENEFIT (rep02:FRAMES_NOT_WORSE)`: tracer -94%, S -24%, idle -76%, but one
  PF2 run's scroll p95 was one 8.3 ms frame higher (33.3 vs 25.0 ms). Daily launcher switch staged, off by default.

Fork tooling: waydefu/termux-x11 local commits 22137ff, 9f7bad4, e4bf7d6 (not pushed). `tools-e4bf7d6/` holds the
files as judged in PROOT-BENCH-02 (`SHA256SUMS`). PROOT-BENCH-01 used the same files except `proot_bench.sh`
(09fb812b...) and `proot_bench_judge.py` (86f0159b...), which differ only by the 3-line `PF_BIN` parametrization of e4bf7d6.
Each cell's `cmd.out` TOOLS line records the drive / launch / args / meter / end sha256 prefixes.
