# PROOT-FAST5-STAT-AT-ENTER-01 — 查檔案在進入時代答，省掉一次 ptrace stop（2026-09-25）

## 依據
PROOT-STAT-COST-01：每個 stop ~30 µs（放行並跨核喚醒 tracee ~8 µs＋tracee 核心路徑 ~13 µs＋追蹤器處理）；stat 類有兩個 stop，
離開那次只為 fake_id0（st_uid/st_gid→suid/sgid）與 link2symlink（l2s 的 st_nlink）改寫結果。PROOT-FAST4-SPIN-01 已排除「追蹤器喚醒延遲」。

## 實作：proot-fast v5（= v2 ＋ `proot-fast5-stat-at-enter.patch`，346 行；`out5/bin/proot-fast5` sha256 前綴 `adb3d6d6`）
- `tracee/event.c`：seccomp stop 的 FILTER_SYSEXIT 分支（新順序核心，本機 verbose 確認 `new syscall order`）在翻譯前設 `v5_seccomp_enter`；
  enter 階段若已代答（`v5_answered`）就以 PTRACE_CONT 放行、不要離開 stop。
- `syscall/enter.c` `v5_stat_at_enter()`（在 SYSCALL_ENTER_END 之後）：
  - `newfstatat`（arm64 在 PRoot 表中是 **PR_fstatat64**——第一版只認 PR_newfstatat，完全沒生效，靠 -v 2 追蹤找到）：以已翻譯的主機路徑自己 newfstatat；
    ENOENT／ENOTDIR 直接代答錯誤；其他錯誤（EACCES 等，fake_id0 會重試）走原路徑。
  - `fstat`：`pidfd_open`＋`pidfd_getfd` 複製 tracee 的 fd 後 fstat；link2symlink 需要的路徑仍以 `readlink(/proc/pid/fd/N)`（去掉 " (deleted)"）取得。
  - 改寫順序同 sysexit handlers（擴充以反向初始化順序執行）：先 link2symlink（共用抽出的 `l2s_stat_override()`，原 sysexit handler 也改呼叫它），再 fake_id0。
  - 寫回 tracee 緩衝區、`set_sysnum(PR_void)`（arm64 avoider −1，核心取消且保留結果）、還原 SYSARG_2..6、結果放 SYSARG_RESULT；SP 與 status 由 translate_syscall 既有的 PTRACE_CONT 分支歸位。
  - 退回條件：其他 flags、非絕對或 /proc 路徑、非原生 ABI、chained syscall、sysexit_pending。`PROOT_STAT_AT_ENTER=0` 關閉（對照組）。
- 驗證以 `-v 2` 的 VERBOSE 追蹤確認代答真的發生（stat abs／lstat／相對路徑 6 次、missing 2 次、fstat 9 次）。

## 功能（逐字比對，PRoot 外經 run-as）
- `stat_smoke.sh`（59 行：一般檔／目錄／符號連結跟隨與否／l2s 硬連結 nlink 2／斷連結／不存在／相對路徑／`/proc/self`／`/dev/null`／`/tmp`／
  Python stat・lstat・fstat（硬連結 fd、目錄 fd、pipe、socket、/dev/null、已刪除檔、壞 fd EBADF）／Node／`ls -la`／find／git 擁有者檢查）：
  **v5 與 v5off 皆與 v2 相同**（`proot-fast5-statsmoke-v2.txt`／`-v5.txt`）。
- **必紅對照**：刻意拿掉 uid 改寫的 v5b → `DIFFERS`（Python 看到 uid 10365；`proot-fast5-statsmoke-v5b-broken.txt`）。
- 通用 smoke（`proot-fast2-smoke.sh`，23 行）：v5 與 v5off 皆與 v2 相同。

## 效能 `proot-fast5-bench-03.txt`（交錯兩次；該輪整機較慢，組間比較有效）
| | v2 | v5 | v5off（須≈v2） |
|---|---|---|---|
| stat 絕對路徑 µs | 112.9／109.1 | **65.2／66.7** | 107.8／108.2 |
| stat 不存在 µs | 100.2／101.8 | **56.1／55.8** | 101.5／102.8 |
| fstat µs | 84.3／90.7 | **52.6／42.6** | 87.2／90.4 |
| git status ms（statmix＋agentmix） | 2686／2761 | **2146／2086** | 2774／2805 |
| stat_storm ms | 2226／2421 | **1687／1705** | 2416／2324 |
| python_start ms | 861／941 | **735／760** | 903／881 |
| 整體 wall s | 23.2／23.1 | **16.8／16.3（−29%）** | 22.6／22.9 |
| 整體 CPU s | 23.8／24.2 | **17.5／17.0（−28%）** | 23.7／23.9 |
（bench-01／02 是 v5 未生效與只做 newfstatat 的中間版，保留。）

## 狀態
研究版，**未部署**。尚未涵蓋 statx（coreutils `ls`、Node 走 statx）。部署需使用者決定（日常啟動器 PD_PROOT_BIN 指向 out5）。
