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


## 2026-09-25 batch (PR after #21/#22)
Same exclusions (`raw-logcat.txt`, screenshots). Contents:
- APP-IDLE-01 (daily apps idle CPU, stock vs proot-fast2): `DAILY_ENABLE false` (16/16 pairs lower under v2, noise term fails 3/4); the user then enabled v2 daily by hand (daily tracer 0.36 -> 0.013 cores).
- PROOT-FAST-NETLINK-01: proot-fast broke getifaddrs (half-done netlink emulation); v3 probe shows Android denies rtnetlink outright; fixed in the guest by `f8ifaddrs.c` via /etc/ld.so.preload (IPv4 only; Python ifaddr still bypasses it).
- DND-PROBE-01: non-ASCII drag-and-drop crash not reproduced (GTK and Electron targets, C and C.UTF-8 locales).
- PROOT-FAST4-SPIN-01: "tracer wake-up latency" hypothesis falsified (spinning before waitpid: no gain, +45% CPU).
- PROOT-STAT-COST-01: per-stop cost decomposition (proftrace LD_PRELOAD into the tracer): ~8 us per resume, two stops per stat.
- PROOT-FAST5-STAT-AT-ENTER-01: v5 answers newfstatat (PR_fstatat64 on arm64) / fstat at the seccomp enter stop: stat -41%, fstat -45%, agent-type work -29% wall / -28% CPU; smokes identical to v2, deliberately broken v5b caught (must-be-red).
- V5-SANITY-01: Claude Desktop, ChatGPT, chatgpt-web, Hermes, Cursor all start and idle normally under v5; daily switched to v5.
The judged / used tool files are in `tools-be7fbc0/` (fork commits local only).
