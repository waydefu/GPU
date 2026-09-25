# PROOT-FAST6-STATX-AT-ENTER-01 — statx 也在進入時代答（2026-09-25）

## 背景
v5（PROOT-FAST5-STAT-AT-ENTER-01）只處理 newfstatat／fstat；coreutils（`ls`、`stat`）與 Node（libuv）走 statx。
原本 statx：enter 翻譯路徑 → 核心執行 → exit stop 由 `tracee/statx.c` `handle_statx_syscall()` **再翻譯一次路徑**、讀回核心結果（失敗時用 stat() 模擬）、
發 `STATX_SYSCALL` 給 fake_id0（uid/gid）與 link2symlink（l2s 的 nlink）、有改就寫回。

## 實作：v6 = v5 ＋ `proot-fast6-statx-at-enter.patch`（135 行；`out6/bin/proot-fast6` sha256 前綴 `2d5596dc`）
`tracee/statx.c` `v6_statx_at_enter()`（由 `syscall/enter.c` v5_stat_at_enter 分派 PR_statx）：
- 與 exit handler 相同的 `statx_syscall_state`：路徑 = `translate_path()`（ORIGINAL 參數、同樣的 deref 規則）；AT_EMPTY_PATH = `readlink_proc_pid_fd()`。
- 內容 = 追蹤器自己做的**真 statx(2)**（AT_EMPTY_PATH 用 pidfd_getfd 複製的 fd）＝一般路徑下核心給 tracee 的結果（比 SIGSYS 備援的 stat()→statx 轉換更完整）。
- 同一個 `STATX_SYSCALL` 通知 → 整個 struct statx 寫回 → PR_void＋結果 0 → PTRACE_CONT。
- ENOENT／ENOTDIR 直接代答；其他錯誤、非預期 flags、/proc 或非絕對路徑走原路徑（保留 exit 的 stat() 備援）。`PROOT_STAT_AT_ENTER=0` 一併關閉。
- `-v 2` 確認代答：成功 6（路徑／nofollow／fd 各 2）、ENOENT 2。

## 功能（`v6check-run.sh`，PRoot 外經 run-as、setsid nohup 脫離 adb；`proot-fast6-check-01.txt`）
| 測試 | v6 | v6off | v6b（故意不發 STATX_SYSCALL，必紅） |
|---|---|---|---|
| stat_smoke（59 行：含 coreutils stat／ls -la／Node statSync） | 與 v2 相同 | 相同 | DIFFERS 40 行（uid 10365） |
| smoke（23 行） | 相同 | 相同 | DIFFERS 4 行 |
| daily_check（14 行） | 相同 | 相同 | DIFFERS 6 行（git clone 物件 nlink 1≠2） |
（第一次執行跑到一半 ADB 斷線——手機換網到 192.168.1.100、無線偵錯失效——輸出不完整作廢；使用者重開無線偵錯後以脫離 adb 的方式重跑。）

## 效能 `proot-fast6-bench-01.txt`（v2／v5／v6／v6off 交錯兩次；本輪整機波動較大）
| | v2 | v5 | **v6** | v6off |
|---|---|---|---|---|
| statx 路徑 µs | 93.6／111.3 | 91.2／104.9 | **65.2／59.8** | 111.3／76.5 |
| statx fd µs | 67.8／85.2 | 72.0／80.4 | **51.0／44.3** | 88.3／63.4 |
| statx 不存在 µs | 94.6／103.5 | 93.2／106.6 | **69.5／56.6** | 109.8／97.4 |
| stat 路徑 µs | 89.2／98.9 | 53.5／60.3 | **50.4／52.1** | 109.2／84.6 |
| ls -laR ×3 ms | 5496／6059 | 5731／5945 | **5076／4893** | 6192／4558 |
| node walk ×3 ms | 2577／2806 | 2700／2667 | **2226／1476** | 2871／2725 |
| 整體 wall s | 34.3／38.9 | 30.4／32.1 | **28.3／24.5** | 39.5／32.4 |
| 整體 CPU s | 33.8／40.3 | 30.9／32.9 | **29.0／24.5** | 40.8／32.6 |
statx −37%；相對 v5 整體 −16%，相對 v2 −28%。

## 狀態
五個日常程式健康檢查 `proot/v6-sanity-01`（見下方更新）。日常仍是 v5；是否換 v6 由使用者決定。

## 更新：五個日常程式健康檢查（`proot/v6-sanity-01`，APP_IDLE_SANITY，PF_BIN=out6）
claude（拋棄式設定檔）1 視窗 18／18、chatgpt 2 視窗 18／18、chatgptweb 2 視窗 20／20、hermes 1 視窗 16／16、cursor 1 視窗 22／22；
全部觸控 0、殘留 0、追蹤器結束；runner `CMD_CAPTURED`；Stable 前後相同。
