# AUTO-SHARD-01 — 凍結（跑之前寫，2026-09-26）

## 目的
驗證「自動分流」的**觸發規則**正確、安全：proot-fast8 在 `PROOT_F8_AUTOSHARD=1` 時，會把 Electron／終端機程式的 execve 自動交給 f8-shard v2。
分流本身消除卡頓的效果已由 TRACER-SHARD-01 判定（`SHARD_REMOVES_STUTTER`，同一套 f8-shard／shard-run 機制），這裡**不重量卡頓**，只驗證：
(1) 該分的有分；(2) 不該分的沒分；(3) 出錯時程式照樣能啟動；(4) 真實 Electron app 在自動分流下能正常開啟與關閉。
全程不碰日常 `:1`、Stable、實驗 app、ADB。測試追蹤器由日常追蹤器經 `f8-shard`（`F8_SHARD_PROOT` 測試掛鉤）啟動；真實 app 開在 Xvfb `:99`，使用私有 D-Bus 和隔離的 HOME。

## 受測物（本地，未安裝進日常）
- `~/build/proot-fast/out8/bin/proot-fast8`：v7 加上 `proot-fast8-autoshard.patch`（只改 `execve/shebang.c`）。
- f8-shard v2（fork `tests/tracer_shard/f8-shard`）、`shard2/shard-run.sh` v2（加上 claim）、`shard2/shard-daemon.sh`（常駐程式）。
- 雜湊在跑之前記進 `auto-shard-01/sha256-before-run.txt`。

## A. 規則案例（測試追蹤器 = proot-fast8＋`PROOT_F8_AUTOSHARD=1`）
假 Electron = 複製一份 `/bin/bash`，放進一個有空 `v8_context_snapshot.bin` 的目錄；假終端機 = 複製一份 bash，命名為 `xterm`。
判讀方式：探針程式記下自己的 `TracerPid`。等於測試追蹤器 → `NOT_SHARDED`；等於別的追蹤器（非 0） → `SHARDED`。

| 案例 | 情境 | 預期 | 預期的 log 決定 |
|---|---|---|---|
| E1 | 假 Electron，stdout／stderr 導到檔案 | SHARDED；`F8_SHARD_EXE`＝其正規路徑、`F8_SHARDED=1`；新追蹤器的 argv **沒有** `--kill-on-exit` | `shard electron` |
| E2 | argv 含 `--type=renderer` | NOT_SHARDED | `skip chromium_child` |
| E3 | argv 含 `--remote-debugging-pipe` | NOT_SHARDED | `skip debugging_pipe` |
| E4 | env `ELECTRON_RUN_AS_NODE=1` | NOT_SHARDED | `skip electron_run_as_node` |
| E5 | env `F8_NO_SHARD=1` | NOT_SHARDED | `skip f8_no_shard` |
| E6 | stdout 是 pipe | NOT_SHARDED | `skip stdio_pipe` |
| E7 | 只有 stderr 是 pipe | NOT_SHARDED | `skip stdio_pipe` |
| E8 | E1 分流後，在分流裡再 exec 同一個執行檔 | 留在 E1 的分流追蹤器 | `skip same_app` |
| E9 | E1 分流裡 exec 同目錄的另一個 helper | 留在 E1 的分流追蹤器 | `skip same_app` |
| E10 | env 有 `F8_SHARDED=1`、沒有 `F8_SHARD_EXE`（舊的明確啟動器區塊） | NOT_SHARDED | `skip explicit_shard` |
| E11 | E1 分流裡 exec **另一個** app 目錄的假 Electron | SHARDED 到第三個追蹤器（≠ 測試追蹤器、≠ E1 的） | `shard electron` |
| E12 | 對照：沒有 snapshot 目錄的 bash 複本 | NOT_SHARDED，而且**沒有** log 行 | （無） |
| T1 | 假終端機 `xterm`：啟動一個 `setsid nohup sleep` 後自己馬上結束 | SHARDED；終端機結束 1 s 後孤兒程序**還活著**、在同一個分流追蹤器下；用確切 pid 殺掉孤兒後，分流追蹤器 5 s 內結束 | `shard terminal` |

（跑之前修訂，來自 16:07 的空跑：每成功分流一次，程式在**新追蹤器裡**真正 exec 時，還會再經過一次規則，被判成 `skip same_app`，這是正確行為。所以 E1、L1、X1、E11、T1 各會多一行 `skip same_app`（檔名各自對應）。判定器的 log 預期已照這點修正，其餘預期不變。空跑的紀錄是 `autoshard-dry.log`：`shard electron` 之後接一行 `skip same_app`。）

## B. 出錯時照樣啟動
| 案例 | 情境 | 預期 |
|---|---|---|
| F1 | `PROOT_F8_AUTOSHARD_BIN` 指向一份壞掉的 f8-shard（`RUN=/nonexistent`） | 程式**照原本方式啟動**（NOT_SHARDED）、跑完、exit code 保留（`exit 7` → 7）；stderr 有 `F8_SHARD_REFUSE` |
| F2 | `PROOT_F8_AUTOSHARD_BIN=/nonexistent` | 程式照原本方式啟動（NOT_SHARDED）；log `skip no_f8_shard` |

## C. 應該要紅的對照
| 案例 | 情境 | 預期 |
|---|---|---|
| R1 | 同 E1，但測試追蹤器換成 **proot-fast7**（沒有規則），環境變數相同 | NOT_SHARDED。若判成 SHARDED，表示測試量不到規則是否存在 → 整份 INVALID |
| R2 | 比對器自我檢查：把 E1 的探針結果拿去和「預期 NOT_SHARDED」比 | 必須判「不符」 |

## D. 真實 app（Xvfb `:99`，在 proot-fast8 測試追蹤器內直接 exec Electron 執行檔，stdout 導到檔案）
| 案例 | app | 預期 |
|---|---|---|
| S1 | Cursor（`/usr/share/cursor/cursor`，旗標照 `cursor-gpu`） | 60 s 內：主程序在一個分流追蹤器下（≠ 測試追蹤器、≠ 日常）；至少一個 renderer／zygote 子程序**在同一個分流追蹤器**下（沒有被再分一次）；`:99` 上有視窗。對 f8-shard 送 SIGTERM 後 30 s 內，app 主程序和所有帶 `--type=` 的子程序都結束 |
| S2 | Claude Desktop（`/usr/lib/claude-desktop/claude-desktop`，旗標照桌面圖示，`HOME`／`XDG_*` 指到空的暫存目錄，所以不會碰到使用者正在用的那一份） | 同 S1 |

（跑之前修訂：自動模式不帶 `--kill-on-exit`，這跟日常追蹤器一樣：app 結束後自己留下來的輔助程序會讓分流追蹤器繼續活著。所以 app 結束後分流追蹤器還在**不判 FAIL**，只把它底下剩下的程序列出來當資訊。T1 是專門驗證這個性質的案例。）
（修訂 2，**real-01 之後**：real-01 的 S2（Claude Desktop）判 `SMOKE_REAL_FAIL`，**保留不重判**。
原因是工具缺陷：Chromium 的 setproctitle 會把 `/proc/<pid>/cmdline` 改寫成一整串、`/proc/<pid>/environ` 變成亂碼，所以用「環境變數 `HOME`＋argv[0]」認 app 程序在 Claude Desktop 上失效。
診斷（不判）：`claude-diag/diag.txt` 顯示主程序、zygote、gpu、utility、renderer、crashpad 其實都在同一個分流追蹤器下。
real-02 起改用：分流追蹤器 S 與主程序取自 f8-shard 的 `<job>/f8-shard.out`；「沒有被再分一次」改用規則 log 判斷：app 目錄底下的路徑剛好 1 行 `shard electron`，其他都是 skip。renderer 數的是 S 底下 cmdline（NUL 換成空白後）含 `--type=renderer` 的程序，或 zygote 的子程序。關閉後看 S 底下還有沒有含 app 路徑或 `--type=` 的程序。**判準不變。**）

真實 app 開始前檢查 MemAvailable ≥ 2.5 GB，執行中每秒看一次，低於 1.5 GB 就立刻停（用確切 pid），該案例判 INVALID。

## 判決
- A、B、C、D 全部符合預期 → **`AUTOSHARD_RULES_PASS`**。
- 任一 A／B／D 不符 → **`AUTOSHARD_RULES_FAIL`**（記下是哪一格）。
- R1 或 R2 沒紅 → **`AUTOSHARD_INVALID`**。
- 資訊（不進判決）：自動分流的啟動延遲、被分流程式的 exit code（已知限制：f8-shard 回傳 0）。

## 不在範圍內
- 卡頓效果（TRACER-SHARD-01 已判）。
- 換進日常（使用者自己決定、自己套用，照 v7 的慣例）。
