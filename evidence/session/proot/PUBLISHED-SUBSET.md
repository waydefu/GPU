

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


## 2026-09-25 batch 2 (after #23)
- PROOT-FAST6-STATX-AT-ENTER-01: v6 answers statx at the seccomp enter stop too (real statx(2) by the tracer + the same STATX_SYSCALL notification): statx -37%, overall -16% vs v5 and -28% vs v2; three smokes identical to v2, deliberately broken v6b caught by all three; five daily apps healthy (`v6-sanity-01`). Daily launchers now select v6 -> v5 -> v2 -> stock.
- Same exclusions (raw-logcat.txt, screenshots).
