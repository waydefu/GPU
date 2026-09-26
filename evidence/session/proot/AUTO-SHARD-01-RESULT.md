# AUTO-SHARD-01 — 結果（2026-09-26）

判準：`AUTO-SHARD-01-FREEZE.md`（跑之前寫。修訂 1 來自 16:07 的空跑；修訂 2 在 real-01 之後，只改認程序的方式，判準不變）。

## 判決：**`AUTOSHARD_RULES_PASS`**
| 部分 | attempt | 結果 |
|---|---|---|
| A 規則案例（E1–E12、T1） | `auto-shard-01/rules-01` | 全部符合預期 |
| B 出錯時照樣啟動（F1、F2） | `rules-01` | 都照原本方式啟動，exit code 保留（7） |
| C 應該要紅的對照（R1 v7、R2 比對器） | `rules-01` | 都紅（R1 判 NOT_SHARDED） |
| D 真實 app | `real-01` | **`AUTOSHARD_REAL_FAIL`（凍結，不重判）**：S1 Cursor PASS；S2 Claude Desktop FAIL，原因是工具缺陷（見下） |
| D 真實 app | **`real-02`** | **`AUTOSHARD_REAL_PASS`**：Cursor、Claude Desktop 都通過 |

## 做了什麼
- **proot-fast8**（`out8/bin/proot-fast8` sha256 `10121cc4…`）＝ v7 ＋ `proot-fast8-autoshard.patch`（只改 `execve/shebang.c`，216 行 diff）。
  追蹤器環境有 `PROOT_F8_AUTOSHARD=1` 時，exec 以下兩類程式會被當成開頭有一行虛擬的 `#!<f8-shard> --auto=<類別>`，交給 f8-shard v2 另起一個追蹤器：
  - Electron／Chromium：執行檔同目錄有 `v8_context_snapshot.bin`；
  - 終端機：`xfce4-terminal`、`xterm`。
- **不分流**的情況（程式照原本方式啟動）：
  - stdout 或 stderr 是 pipe／socket（有人要讀它的輸出）；
  - argv 有 `--type=` 或 `--remote-debugging-pipe`；
  - env 有 `F8_NO_SHARD`、`ELECTRON_RUN_AS_NODE`；
  - `F8_SHARD_EXE` 跟這個程式在同一個目錄（app 自己 re-exec，或旁邊的 helper，例如 crashpad）；
  - 只有 `F8_SHARDED`（舊的明確啟動器區塊）；
  - 找不到 f8-shard。
- **f8-shard v2**（`/usr/local/bin/f8-shard` 還是 v1，要套用才會換）：
  - `--auto` 模式：設 `F8_SHARDED=1` 和 `F8_SHARD_EXE`；新追蹤器不帶 `--kill-on-exit`；分流失敗就以 `F8_NO_SHARD=1` 照原本方式 exec 程式。
  - 常駐程式快速路徑。
  - **修 3 秒 bug**：程式已經結束就不再重試 TracerPid 檢查。
  - job claim：同一個工作不會被啟動兩次。
- **shard-daemon.sh**：常駐在 Termux 那側（不被追蹤），從 FIFO 接工作，每 20 個工作清一次舊目錄（留最新 200 個），log 超過 1 MB 就輪替。

## 數字
- **分流啟動（從呼叫到程式開始）**：v1 是 1.05–1.13 s（`am` 本身就要 0.96–1.19 s）；v2 走常駐程式是 **0.113–0.128 s**（6＋3 次）。
- **程式立刻結束時**：v1 要 4.22 s（3 秒 bug），v2 是 0.11–0.12 s。
- 自動分流一個小探針、從 exec 到結束：0.39–0.40 s（`rules-01` L1／X1；含探針本身的工作與測試追蹤器的開銷，只當資訊）。
- 真實 app 在 `real-02`：Cursor 4 s 內、Claude Desktop 1 s 內就有 renderer 和視窗；關閉後 1 s 內全部結束，分流追蹤器也自己退出（兩個 app 都**沒有**留下殘餘程序）。

## real-01 的 S2 為什麼 FAIL（工具缺陷，已留痕）
- 工具用「環境變數 `HOME`＋argv[0]」認 app 的程序。但 Chromium 的 setproctitle 會把 `/proc/<pid>/cmdline` 改成一整串，`/proc/<pid>/environ` 變成亂碼（`diag-claude-setproctitle/diag.txt`：environ 7110 行，`HOME` 比對不到）。
- 同一份診斷顯示，自動分流其實**正確**：主程序、zygote、gpu、utility、3 個 renderer、crashpad 全都在同一個分流追蹤器下；使用者正在用的 Claude Desktop（日常追蹤器下）沒有被碰到。
- real-02 改用 f8-shard 回報的分流追蹤器，加上規則 log 認程序（凍結修訂 2），並先用空跑 real-dry-02 驗過工具。

## 空跑抓到的判定器漏洞（跑之前修正，已留痕）
每成功分流一次，程式在新追蹤器裡真正 exec 時還會再經過一次規則，被判成 `skip same_app`，這是正確行為。原本判定器的 log 預期少算了這一行；16:07 的空跑（`dry-20260926-1607.autoshard.log`）抓到後，在 rules-01 之前修正。

## 判決之後才改的東西（已驗證，但不在判決範圍）
- `shard-daemon.sh` 加了 log 輪替（sha256 `ea8f9848…` → `a07eae43…`，只改清理那段）。rules-01／real-02 用的是舊版（見各 attempt 的 `sha256-before-run.txt`）。
  新版另外驗過：先放 1.1 MB 的假 log，連跑 22 次分流 → 輪替成 `.1`、常駐程式還活著、20／22 走常駐程式（前 2 次常駐程式還在啟動）；`test_shard-final` 是 `TEST_SHARD_PASS`。

## 已知限制（要告訴使用者）
1. 自動分流的程式，stdout／stderr 會寫到分流的 log（`<job>/log`），不會出現在啟動它的終端機；exit code 一律是 0。
2. 不同追蹤器之間 SysV IPC 不通（跟 TRACER-SHARD 相同）。
3. `xfce4-terminal` 預設所有視窗共用一個程序，所以**所有終端機視窗共用一個分流追蹤器**（跟桌面是分開的）。要每個視窗各自一個，得加 `--disable-server`，還沒做。
4. 開機後第一次分流還是要約 1.1 s（走 `am`）；套用後 `f8desk` 會在桌面啟動時先叫起常駐程式，所以之後都是 ~0.1 s。
5. 卡頓效果沒有重量，沿用 TRACER-SHARD-01（同一套分流機制）。

## 套用（使用者決定、自己執行）
在桌面的終端機執行 `~/build/proot-fast/shard2/apply-v8-autoshard.sh`（Termux 路徑 `/data/data/com.termux/files/home/build/proot-fast/shard2/`）。它會：
- 先核對雜湊；
- 把 f8-shard v2 裝到 `/usr/local/bin/f8-shard`（備份成 `.bak-20260926-v1`）；
- 讓 f8desk／f8desk-external 優先選 proot-fast8，並在選到時 export 自動分流變數、叫起常駐程式（備份成 `.bak-20260926-v8`）。
關掉「F8 工作站」再打開才生效。**關掉桌面會把所有 app 一起關掉，包括 Claude Desktop 本身**，請挑方便的時候。

腳本的修改已經在 f8desk 的**副本**上測過：語法 OK；模擬執行選到 proot-fast8，也 export 了變數；雜湊檢查通過。

## Stable／裝置
沒有碰 Stable `:1`、實驗 app、ADB。測試追蹤器由日常追蹤器經 f8-shard 的測試掛鉤啟動；真實 app 開在 Xvfb `:99`，用私有 D-Bus 和空的 HOME。
測試結束後：常駐程式（pid 16057）用確切 pid 停掉，暫存目錄刪掉，沒有殘留程序。

## 套用紀錄（2026-09-26 傍晚）
- 16:41：使用者在 Termux 跑 `apply-v8-autoshard.sh` 兩次都沒成功，第一次是檔案沒有執行權限，第二次是腳本偵測到不在桌面內而拒絕，兩次都沒改到任何東西。之後由 Claude 在桌面內代跑，成功，f8-shard v2 已裝、f8desk 已改。
- 使用者重開工作站後檢查：日常追蹤器已是 proot-fast8（pid 31217），**但是環境裡沒有 `PROOT_F8_AUTOSHARD`**，所以自動分流沒有開；Claude Desktop 仍在日常追蹤器下。行為和 v7 相同，沒有壞掉。
- **原因（套用腳本的錯）**：proot-distro 只會把呼叫者環境裡的 `PROOT_NO_SECCOMP`、`PROOT_VERBOSE`、`PROOT_L2S_DIR` 交給 proot（`proot_distro/commands/login/__init__.py` 約 477–497 行），在 f8desk 裡 export 的變數被丟掉了。
  先前在副本上的測試只驗證了「f8desk 有 export」，沒驗證「proot 收得到」；「PROOT_* 會傳下去」是從 `execenv.py` 的註解推論出來的，沒實測過。
- **修正 1**：`out8/auto/proot-fast8`（sha256 `f1c211fd…`）是一個包裝程式，它先設好變數，再 exec 真正的 proot-fast8。檔名刻意跟真正的程式相同，因為 proot-distro 用 comm 對 PD_PROOT_BIN 的 basename 來認 session。
  實測（`apply-fix1/`）：
  - 從 Termux 那側（不被追蹤）真的 `proot-distro login`：追蹤器 comm 是 `proot-fast8`、argv[0] 是真正的二進位檔、environ 有 `PROOT_F8_AUTOSHARD=1` 和 log（`wrapper-test.out`）；
  - 同一種 session 裡執行假 Electron，被分到另一個追蹤器（session 3563 → app 3598，走常駐程式，`wrapper-e2e.out`）。
- Claude 直接改日常 f8desk 被自動模式的安全機制擋下，所以改成腳本 `shard2/apply-v8-fix1.sh`（只動 Termux 那側的 f8desk／f8desk-external，備份成 `.bak-20260926-v8fix1`），由使用者執行。
  這支腳本整支在副本上跑過：兩個檔都改好、第二次執行會跳過、正式檔沒被動到。
- **修正 1 生效（2026-09-26 17:05 使用者重開 F8 工作站後驗證）**：
  - 日常追蹤器 pid 10369：comm 是 `proot-fast8`，argv[0] 是 `out8/bin/proot-fast8`，environ 有 `PROOT_F8_AUTOSHARD=1`、`PROOT_F8_AUTOSHARD_LOG`。
  - Claude Desktop 已被自動分流：autoshard.log 第一行是 `shard electron /usr/lib/claude-desktop/claude-desktop`，接著是 `skip same_app`（新追蹤器裡的 exec）、`chromium_child`（子程序）、`same_app`（crashpad）、`stdio_pipe`（被 pipe 接走輸出的子程序）。
  - 這個 Claude Code session 的 shell 在追蹤器 11346 下，不是日常的 10369；11346 的 argv 沒有 `--kill-on-exit`。常駐程式 pid 31233 活著。
  - 抽樣 5 s：日常追蹤器 0.004 核、Claude 分流追蹤器 0.014 核（只當資訊）。
- 日常的現況：f8desk／f8desk-external 的 `PD_PROOT_BIN=out8/auto/proot-fast8`；`/usr/local/bin/f8-shard`＝v2。
  退回：`f8desk{,-external}.bak-20260926-v8fix1`（v8 但沒有包裝程式）→ `.bak-20260926-v8`（v7）；`/usr/local/bin/f8-shard.bak-20260926-v1`。
