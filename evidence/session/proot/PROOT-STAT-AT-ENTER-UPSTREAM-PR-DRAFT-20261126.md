# `termux/proot` 上游 PR 紀錄：在 seccomp enter stage 直接代答 `newfstatat` / `fstat` / `statx`（2026-11-26）

> **狀態**：**PR #430 已依使用者指示撤回（CLOSED / WITHDRAWN）**：https://github.com/termux/proot/pull/430
> - 保留 `waydefu/proot`（分支 `stat-at-enter`，commit `edc3319`，基於上游 `master` `0e42875`）與下列本地匯出 patch，待後續再行評估送出。
> - 匯出 Patch：[`upstream-stat-at-enter-20261126/0001-syscall-answer-stat-fstat-and-statx-at-seccomp-enter.patch`](upstream-stat-at-enter-20261126/0001-syscall-answer-stat-fstat-and-statx-at-seccomp-enter.patch)

---

## 實作摘要（`STAT_SYSCALL` extension event 分層）

1. **核心與外掛完全解耦（`extension.h`, `fake_id0`, `link2symlink`）**：
   - 新增 `STAT_SYSCALL` extension event 與 `struct stat_syscall_state { host_path, stat_buf }`。
   - `fake_id0_handle_stat_syscall()` 僅更新 `st_uid` / `st_gid`（`USERLAND` 模式下回傳 `-ENOSYS` 退回正常路徑）。
   - `link2symlink_handle_stat()` 僅於 backing 檔上以 `get_link_count()` 更新 `st_nlink`；若遇到未解析之 link2symlink symlink/intermediate（`S_ISLNK` 且含 `PREFIX`），回傳 `-EAGAIN` 退回 `handle_sysexit_end()`。兩者修改欄位正交，不受 `inherit_extensions()` 反轉順序影響。
2. **Event loop 与安全守衛（`tracee/event.c`, `tracee/statx.c`, `syscall/enter.c`）**：
   - `tracee/event.c` 新增 `seccomp_enter_skippable` / `answered_at_enter`，僅於 `seccomp_after_ptrace_enter && !sysexit_necessary` 下允許以 `PTRACE_CONT` 跳過 sysexit stop。
   - 僅於 `ABI_DEFAULT`、`(long) SYSCALL_AVOIDER < 0`（跳過 ARM32）、無 chained syscalls、無既有 `sysexit_pending` 時啟用。
   - `statx` 直接重用 `CURRENT SYSARG_2` 已翻譯之 host path（或 `pidfd_open` + `pidfd_getfd` 處理 `AT_EMPTY_PATH`），避免二次路徑尋訪；`newfstatat` / `statx` 只代答 `ENOENT` / `ENOTDIR`，其餘錯誤（`EACCES`、`ENOSYS`、`EPERM` 等）全部退回正常 enter+exit 路徑。

---

## 實測結果（ARM64 Android 16，Termux + Ubuntu 24.04，TermuxService `TracerPid == 0`）

3 輪交替實測（`base#1 -> patched#1 -> base#2 -> patched#2 -> base#3 -> patched#3`）中位數：

| 測項 | `0e42875` 中位數 | `stat-at-enter` (`edc3319`) 中位數 | 改善 |
|---|---:|---:|---:|
| `newfstatat` abs (`20k`, µs/call) | 70.97 | 40.21 | **-43.3%** |
| `newfstatat` nofollow (`20k`, µs/call) | 73.75 | 40.27 | **-45.4%** |
| `newfstatat` rel (`20k`, µs/call) | 73.63 | 40.69 | **-44.7%** |
| `newfstatat` `ENOENT` (`20k`, µs/call) | 67.16 | 38.73 | **-42.3%** |
| `fstat` wall (`20k`, µs/call) | 60.20 | 38.26 | **-36.4%** |
| `fstat` tracee sys (µs/call) | 26.19 | 13.48 | **-48.5%** |
| `fstat` `nvcsw` (`20k` calls) | 40000 | 20000 | **-50.0%** |
| `statx` abs (`20k`, µs/call) | 71.18 | 41.28 | **-42.0%** |
| `statx` nofollow (`20k`, µs/call) | 69.91 | 40.44 | **-42.2%** |
| `statx` `AT_EMPTY_PATH` (`20k`, µs/call) | 63.30 | 39.24 | **-38.0%** |
| `statx` `ENOENT` (`20k`, µs/call) | 64.91 | 40.15 | **-38.1%** |
| `git status` (×10, ms) | 1129 | 822 | **-27.2%** |
| `find` (×10, ms) | 196 | 162 | **-17.3%** |
| Python `os.walk` `os.stat` (×3, ms) | 1700 | 1235 | **-27.4%** |
| `ls -laR` (×3, ms) | 3768 | 3181 | **-15.6%** |
| Node `fs.lstatSync` walk (×3, ms) | 1767 | 1328 | **-24.8%** |
| 6 套綜合總牆鐘 (ms) | 30650 | 22304 | **-27.2%** |

## 正確性回歸

- `stat_smoke.sh`（59 行）、`smoke.sh`（23 行）、`daily_check.sh`（17 行）：全數 **0 diff**。
- `statx_edge` 子行程深度 1：**0 diff**；深度 0 `fstat_file` 回傳正確 `uid=0 gid=0`（並記錄了上游 `inherit_extensions()` + `link2symlink` `handle_sysexit_end()` 於偶數深度覆寫 `fake_id0` 的既有問題）。
- `termux/termux-x11`：`lorie/src/main/cpp/lorie/InitOutput.c:947` flip 尺寸判斷上游已修正，無需開立 PR。
