# PROOT-STAT-COST-01 — 查檔案（stat 類）在 proot-fast2 下的成本拆解（2026-09-25）

## 拆解 1：時間 vs CPU（`fstatloop.c`，日常 v2 PRoot，n=50000）
每次 fstat：wall 62.8 µs；tracee user 0.11／**sys 26.1** µs；追蹤器 user **11.0**／sys **38.2** µs（日常追蹤器 ticks 差，基線 ~0.013 核）。
CPU 合計 75 µs > wall → 全是計算、沒有空等（與 PROOT-FAST4-SPIN-01 忙等無效一致）。

## 拆解 2：追蹤器每個 fstat 發出的呼叫（`proftrace.c` LD_PRELOAD 進 proot，`proot-stat-prof-01.txt`，n=20000 減 n=0）
| 呼叫 | 每 fstat 次數 | 平均 µs | 每 fstat µs |
|---|---|---|---|
| PTRACE_CONT (0x7) | 1 | 8.2 | 8.2 |
| PTRACE_SYSCALL (0x18) | 1 | 8.2 | 8.2 |
| PTRACE_GETREGSET ×2＋GETEVENTMSG | 3 | 0.5–0.6 | 1.8 |
| process_vm_readv／writev（fake_id0 改 st_uid） | 2 | 0.7–0.8 | 1.5 |
| readlink ×2＋lstat＋fstatat（link2symlink 查 l2s） | 4 | 1.9–2.2 | 8.2 |
| waitpid（阻塞等待，含等 tracee） | 4 | 18（牆鐘） | — |
結論：每個 stop 的主成本是「放行並跨核喚醒 tracee」（每次 ~8 µs）＋ tracee 端 ~13 µs 核心路徑；fstat 有兩個 stop（進入＋離開），
離開那次只為 fake_id0 改 uid／gid 與 link2symlink 修 nlink。

## 方向（未實作）
v5「進入時代查」：stat 家族在 syscall-enter 時由追蹤器以翻譯後路徑（fstat 用 pidfd_getfd 取得 fd）自行 stat、套用 fake_id0／link2symlink 改寫、
寫回 tracee、跳過原 syscall → 每次省掉一個 stop（預估 64 → ~35 µs）。需處理：/proc/self 類路徑退回原路徑、AT_EMPTY_PATH、相對路徑、錯誤碼、ABI。
