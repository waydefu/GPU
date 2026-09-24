# PROOT-KOMPAT-OVERHEAD-01 — 日常 PRoot 追蹤器的真正負擔：kompat 白攔 futex／epoll_pwait（2026-09-24）

## 起點
PROOT-BENCH-01（proot-fast v1，只拿掉 socket／clone 攔截）判 `PROOT_FAST_NO_BENEFIT`：PF 下 Cursor 的追蹤器在閒置、捲動、打字都還吃 0.28–0.30 核。
使用者目標：解放手機效能（見記憶 user-goal-unleash-phone）；19:32 授權兩小時內自行決定測試。

## 日常 PRoot 的量測（pid 20277，只開 Claude Desktop＋本 Claude Code session＋XFCE）
- `ps`：PRoot 開 79 分鐘，追蹤器累計 1345 s CPU；guest 程序自身合計約 1400 s（不含已結束子程序）→ **追蹤器開銷 ≈ 程式本身**。
- 閒置 60 s（我不操作）：追蹤器 0.33–0.40 核、每秒約 1450 次 context switch；Claude Desktop 畫面程序約 0.2 核（背景工作指示動畫）。
- 先前看到的 xfwm4 每秒 1423 次喚醒是間歇性的（閒置時 0），不是穩定負擔；adb server 閒置時對追蹤器無影響（A/B 0.360 vs 0.369 核）。
- **ptrace-stop 抽樣**（`trapmix`：每個被追蹤執行緒的 `/proc/.../stat` 狀態為 `t` 時讀 `/proc/.../syscall`；檔案開一次、以 pread 重讀，抽樣器幾乎不增加攔截），25 s、430 執行緒：
  `recvmsg 39.7%`、**`futex 28.1%`**、**`epoll_pwait 20.7%`**、`sendto 6.7%`、其他 < 5%。
  tracee 的 `Seccomp: 2`（2 個過濾器）→ 不是「全部攔」；futex／epoll_pwait 本不該被 PRoot 攔。

## 根因（原始碼）
- proot-distro 帶 `--kernel-release=…`（為了假 `uname`）→ 啟用 `src/extension/kompat/kompat.c`。
- kompat 的 `filtered_sysnums[]` **無條件**把 33 個 syscall 加進 seccomp 攔截：`futex`、`epoll_pwait`、`pselect6`、`fcntl`、`pipe2`、`dup3`、`eventfd2`、
  `accept4`、`socket`、`openat`（FILTER_SYSEXIT）、`execve`（FILTER_SYSEXIT）…
- 但每個處理都以 `needs_kompat(config, KERNEL_VERSION(2,6,x))` 把關，最高門檻 **2.6.29**；實際核心是 6.x → 全部 no-op。攔截卻照樣發生，
  而且 FILTER_SYSEXIT 讓 openat／fcntl／pipe2 等每次多停一次（離開時）。
- kompat 還在每次 execve 後把 `AT_SYSINFO_EHDR` 拿掉（為了不讓程式從 vDSO 讀到真核心版本）→ **所有程式沒有 vDSO**，`clock_gettime` 每次都進核心。

## 修補：proot-fast v2（kompat-lean）
- 原始碼樹 `~/build/proot-fast/proot-5.1.107.92-v2`（= v1 ＋ kompat 修改），`build2.sh`，產物 `out2/bin/proot-fast2`（sha256 前綴 `8a30e9d63aead905`，
  VERSION `5.1.107.92-fast2`），loader `out2/libexec`。
- 規則：實際核心 ≥ 2.6.29 且未設 `PROOT_KOMPAT_FULL` → kompat 只攔 `uname`／`sethostname`／`setdomainname`（假版本照舊），且不拿掉 vDSO。
  `PROOT_KOMPAT_FULL=1` 或 `PROOT_FORCE_KOMPAT` → 原行為（對照組）。v1 的 socket／clone 規則不變（bwrap 需要時 `PROOT_BWRAP_COMPAT=1`）。

## 微基準 `proot-fast2-bench-01.txt`（`bench2.sh`＋`sysbench2.c`，日常 42 參數，PRoot 外經 run-as 執行，各兩次）
| µs | stock | v1 | **v2** | v2＋`PROOT_KOMPAT_FULL=1`（必須變慢） |
|---|---|---|---|---|
| getpid（從未被攔，對照） | 0.20 | 0.20 | 0.18 | 0.21 |
| futex_wake | 31.6 | 31.7 | **0.23** | 29.4 |
| epoll_pwait(0) | 31.9 | 29.0 | **0.21** | 33.5 |
| fcntl(GETFL) | 63.5 | 62.3 | **0.22** | 66.4 |
| clock_gettime | 0.22（無 vDSO） | 0.24 | **0.06**（vDSO present） | 0.27（absent） |
| open+close | 128.5 | 119.6 | **82.9** | 127.1 |
| fstat（fake_id0／link2symlink 仍攔） | 67.4 | 73.7 | 69.7 | 71.3 |
| socket send+recv | 62.2 | 1.6 | **1.3** | 1.1 |
`uname` 四組都是 `6.17.0-PRoot-Distro`。（數字取第 1 次；第 2 次同量級，見原始檔。）

## 功能對照（`proot-fast2-smoke*.{sh,js,txt}`）
同一腳本在 stock 與 v2 下輸出 **逐字相同**（`SMOKE_IDENTICAL`）：root 身分、chmod／chown、硬連結（link2symlink，nlink 2）、symlink、mv／rm、
Python 8 執行緒×20000 次鎖（160000）、sqlite、ssl、socketpair、subprocess、pipe、Node worker_threads 與 child_process、git、dpkg、apt-cache、DNS、SysV IPC。
（第一版的 Node worker 測試是腳本錯誤——兩邊同樣報錯——已修正後重跑。）

## 下一步
PROOT-BENCH-02（`PROOT-BENCH-02-FREEZE.md`，門檻與 01 相同）以 Cursor 實測判決；BENEFIT 才把日常啟動器 `f8desk`／`f8desk-external`
加上 `PD_PROOT_BIN`（proot-distro 內建覆寫；v2 或 loader 不存在時自動退回系統 proot），下次重開桌面生效。

## AGENT-MIX（描述性，非閘門；`agentmix.sh`＋`agentmix-run.sh` → `agentmix-01.txt`，手機鎖屏、PRoot 外經 run-as，交錯兩次＋對照）
AI 工具呼叫常做的事，每項 10 次：git status／log、grep、find、python／node 啟動、bash 管線、Python 4 執行緒鎖、Node setImmediate 20000 次。
| | stock #1／#2 | **v2 #1／#2** | v2＋`PROOT_KOMPAT_FULL=1` |
|---|---|---|---|
| 總時間 | 15.59／15.71 s | **7.26／7.42 s（−53%）** | 18.35 s |
| 總 CPU（launcher 的 children user+sys＝追蹤器＋guest） | 16.25／16.33 s | **7.52／7.68 s（−54%）** | 14.26 s |
| node_async | 8602／8720 ms | **826／791 ms** | 11208 ms |
| py_threads | 1300／1289 ms | 1017／1036 ms | 1290 ms |
| find_tree | 274／313 ms | 213／224 ms | 314 ms |
| git_status／git_log | 1407／2297 ms | 1329／2273 ms | 1383／2335 ms |
git 幾乎不變：它的成本在 stat 類（fake_id0／link2symlink 仍攔）。事件迴圈類（Node／Electron 的本質）快 10 倍。
