# f8-proot-fast

`f8-proot-fast` 是 POCO F8 Ultra（及 POCO F6 Pro）在非 Root Android / Termux + Ubuntu 24.04 ARM64 PRoot 環境下使用的 **日常 PRoot 效能修補與自動追蹤器分流（auto-shard）工具鏈**。

## 專案定位與脈絡

- 原先寄生於 `src/f8-ahb-exa-async/tests/tracer_shard/`（未提交）與 `evidence/session/proot/` 零散 patch 檔；2026-11-26 獨立收斂為此專案倉庫，與 `termux-x11` 顯示研發線分離。
- 目標：消除單一單執行緒 `proot` 追蹤器在 Electron / AI Agent 高頻 syscall 下的排隊停頓，並降低 `stat`/`fstat`/`statx` 與無效 syscall 攔截的 ptrace stop 成本。

## 累積 Patch（基於 Termux `proot 5.1.107.92`，現役部署：`proot-fast9 + 09b`）

| 順序 | 檔案 | 版本 | 說明 |
|---|---|---|---|
| 01 | `patches/01-proot-fast-bwrap-compat.patch` | v1 | `PROOT_BWRAP_COMPAT=1` 才開啟 socket／clone 相容攔截 |
| 02 | `patches/02-proot-fast2-kompat-lean.patch` | v2 | `kompat-lean`：停攔無需處理的 syscall（futex/epoll 等），恢復 vDSO；`PROOT_KOMPAT_FULL=1` 可還原 |
| 03 | `patches/03-proot-fast5-stat-at-enter.patch` | v5 | `newfstatat` / `fstat` 於 seccomp enter stop 直接代答，省去 sysexit stop；`PROOT_STAT_AT_ENTER=0` 可關 |
| 04 | `patches/04-proot-fast6-statx-at-enter.patch` | v6 | `statx`（含 `AT_EMPTY_PATH`）於 seccomp enter stop 直接代答 |
| 05 | `patches/05-proot-fast7-peercred.patch` | v7 | 跨追蹤器 `SO_PEERCRED` 映射（讓各分流追蹤器下的程式能連上同 UID 日常 D-Bus） |
| 06 | `patches/06-proot-fast8-autoshard.patch` | v8 | `PROOT_F8_AUTOSHARD=1`：Electron/Chromium（同目錄含 `v8_context_snapshot.bin`）與終端機 `execve` 自動改寫為 `f8-shard --auto=...` |
| 07 | `patches/07-proot-fast9-ioctl-bpf.patch` | v9 | seccomp BPF 放行無需改寫的常見 `ioctl`（減少不必要 ptrace stop） |
| 08 | `patches/08-proot-fast9-geteventmsg.patch` | v9 | 優化 `PTRACE_GETEVENTMSG` 讀取路徑，降低 fork/clone/execve 事件停頓 |
| 09 | `patches/09-proot-fast9-no-close-stop.patch` | v9 | `close` syscall 僅於必要時觸發 stop，減少高頻關閉 fd 的 ptrace 往返 |
| 09b | `patches/09b-terra-claude-host-fix.patch` | v8/v9 | 針對 `shared-memory-region` memfd 回報 `ENOSYS`（觸發 Chromium 安全具名檔備援），並限縮 `/proc/self/fd` dup 相容例外至常規 stdio 與 `fcntl(F_DUPFD_CLOEXEC)` |
| 09c | `patches/09c-netlink-socket-identity.patch` | v9 候選 | socket FD 重用後核對 inode，避免把新 socket 誤判為舊 netlink。 |

> **未採納項目備註**：`fast10`（patches `10`–`11`）、`hybrid/`（橋接原型）與 Mesa 27 經評估後**未採納**進入 `main`。

> 部署腳本會建置含 `09c` 的候選版本。以下現役紀錄對應 `fast9 + 09b` 的部署快照。

## 目錄與現役部署對照（`proot-fast9 + 09b` live on `out8/`，2026-11-26）

> **現況（`LIVE_REDEPLOY_AND_VERIFY_PASS`，2026-11-26 22:28）**：`patches/01..09 + 09b` 已完成原子部署至 `out8/`（`5.1.107.92-fast9`，`shared-memory-region` PRESENT、`PROOT_SYSCALL_STATS` ABSENT），通過部署閘門、`fast9_regress` 4/4、`test_terra_proc_fd_reopen` 7/7 與全部實機桌面／GPU 應用驗收（含 live `f8-shard` 啟動之 `claude-desktop` 與 `org.freedesktop.secrets`）。

| 本倉庫路徑 | 裝置現役部署路徑 | SHA256 / 狀態（2026-11-26 核對） |
|---|---|---|
| `patches/01..09 + 09b` | `~/build/proot-fast/out8/bin/proot-fast8`（`5.1.107.92-fast9`） | `2524856b351a740021c189a32bbf94c7393af51e5ef4f6dcb304833c8e313af3`（live） |
| `patches/01..09 + 09b`（loader） | `~/build/proot-fast/out8/libexec/loader` | `eab6b2135421a2e0268832cf171d877146a9e816d7b060ce425e5017d65f08a6` |
| `patches/01..09 + 09b`（loader32） | `~/build/proot-fast/out8/libexec/loader32` | `91381891fa2627a4573705a754eced936b3ba1159c9f6d041b6472f26189f46a` |
| `build/build8.sh` | `~/build/proot-fast/build8.sh` | — |
| `build/wrapper/proot-fast8` | `~/build/proot-fast/out8/auto/proot-fast8` | `f1c211fd6571d29bd4cde93a2f13a49b0463c2e5b1e288e5f1dd27c27183e552` |
| `shard/f8-shard` | `/usr/local/bin/f8-shard`（PRoot 內） | `7158e011aa07db1c4b5031dd64b3e2529e6aace3c99445768bda830d96fa2e3d` |
| `shard/shard-daemon.sh` | `~/build/proot-fast/shard2/shard-daemon.sh` | `8becae04d2d1e58b544727741f87b6af8fd7d72a230d56dd138ab63af9bd2c87` |
| `shard/shard-run.sh` | `~/build/proot-fast/shard2/shard-run.sh` | `03a249873b4e29a04546d78ab96fbb1a4b4f04330f104c168dcbc9d490a35955` |
| `shard/apply-v8-*.sh` | `~/build/proot-fast/shard2/` | 部署與 fix1/fix2 套用腳本 |
| `deploy/` | — | `deploy-proot-candidate.sh`（含 `09b`、`shared-memory-region` 檢查、fail-closed `fast9_regress` 與 `claude-desktop` non-SIGTRAP 閘門）與 `rollback-to-fast8.sh` |
| `scripts/` | — | `android-host-audit-readonly.sh`（唯讀 Android 主機稽核腳本） |
| `scripts/termux-bg-run` | `/usr/local/bin/termux-bg-run`（PRoot 內） | `738226b3d5022f2811322ba28849773cf61906c8848a884dbeb61c7066a71595`；缺 `ANDROID_ART_ROOT`／`BOOTCLASSPATH` 等 7 個變數時 exit `4`（Termux `am` 會靜默 exit 0 不送 intent） |
| `scripts/restart-desktop.py` | 單次實測腳本（11-27 fast9+09c 換版） | PID／身分／SHA256 為該次專用；修正後只從呼叫端帶入上述 7 個變數（允許清單，不繼承其餘環境），並在 SIGTERM 舊桌面前檢查 |
| `scripts/restart-stable-desktop.py` | `~/build/proot-fast/tools/restart-stable-desktop.py` | `72f879c770df7859307ef843e1bdeade0e1e7a0d71fc9ae924adfa2341e911ef`；可重複使用的 Stable XFCE 重啟（現場偵測 pid，`--dry-run` 不送訊號，`--apply` 需 `--confirm-stable-restart`），步驟見根目錄 `HANDOFF.md` |
| `scripts/restart-stable-desktop.{dryrun,apply}.sh` | 同上 `tools/` | `3eb19e0d…`／`102e6a72…`；固定模式的包裝（`termux-bg-run` 不能帶參數） |
| `tests/` | — | `test_restart_stable_desktop.py`（非破壞性：不送訊號、不啟動桌面；5 個突變對照皆 FAIL）、裁判單元測試、`fast9_regress.c`、mutation check、daemon fix3/fix4 離線回歸測試、`test_android_env_guard.py`（裝置上執行的非破壞性測試：不觸發 TermuxService、不重啟 Stable 桌面，並比對 Stable 身分前後不變） |

## 常用環境開關與回退方式

- **單次略過自動分流**：執行程式前設 `F8_NO_SHARD=1`。
- **停用 enter-time stat 代答**：設 `PROOT_STAT_AT_ENTER=0`。
- **切回原版 proot**：在 Termux 建立 `~/.f8-proot-stock`（或使用「F8 設定」小工具）後重開桌面。
- **一鍵回退至已驗證 `fast8` 備份**：最新 `fast8` 備份位於 `/data/data/com.termux/files/home/build/proot-fast/backups/out8-fast8-20261126-222816`（前次備份 `out8-fast8-20261126-205447` 亦完整保留），可使用 `deploy/rollback-to-fast8.sh`（先 `--dry-run` 驗證，再 `--apply --confirm-live` 還原）。

## 離線測試

- `tests/daemon/test_daemon_wipe.sh <fixture-dir>`：用支援 `F8_SHARD_BASE` 的 `old/`、`new/` fixture 測試清空暫存後的 daemon 行為。每次建立獨立狀態目錄。只有所有檢查與清理完成才輸出 `DAEMON_FIX3_TEST_PASS` 並回傳 0。
- `tests/daemon/test_daemon_inherit.sh`：驗證 `shard-daemon.sh` fix 4（`3>&- 9>&-`）使分流子樹不繼承 lock/fifo fd（`PASS T7`）。
- `tests/test_shard_judge.py`、`tests/test_autoshard_judge.py`：分流／自動分流裁判單元測試（需與 `xfce_v6_judge.py` 並列測試目錄）。
- `python3 tests/test_deploy.py`：離線驗證部署失敗回復、fast8 備份選擇與 Claude 啟動檢查。
- `tests/fast9_regress.c`：`proot-fast9` 回歸探針（ioctl BPF / GETEVENTMSG / no-close-stop（含 netlink FD 重用與 Unix socket 收發），以及 `09b` `shared-memory-region` `ENOSYS`、`/proc/self/fd` `O_RDONLY|O_CLOEXEC` + `O_PATH` 與 `/dev/fd/1` `FD_CLOEXEC` 驗證）。
