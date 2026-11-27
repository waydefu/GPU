# Stage 7.4 — 隔離客戶端試點與既有工作流對照驗收報告（2026-11-27）

- **狀態**：**`STAGE7_4_ISOLATED_PASS`（程式碼層選擇性分流、JSON-RPC 嚴格驗證、有界背壓與斷線收斂落地並通過雙軌測試及隔離試點；未修改任何現役客戶端正式設定、未擴張 worker pool，待審閱合併後進 Stage 7.5 異常壓測）**
- **依據文件**：[`STAGE7-2-MULTI-CLIENT-REVISION-20261127.md`](STAGE7-2-MULTI-CLIENT-REVISION-20261127.md) `§3.2`、[`STAGE7-3-ABBA-BENCHMARK-20261127.md`](STAGE7-3-ABBA-BENCHMARK-20261127.md)
- **協作分工**：Neon（四客戶端隔離試點實測、`rg`／`git`／`Serena`／`RTK` 工作流實測對照與獨立複審）× Hydrogen（程式碼層分流、有界本地 inflight、Daemon 非阻塞輸出佇列背壓、雙軌 13/13 回歸測試與實機交叉複核）
- **紅線遵循**：零現役客戶端設定異動（`/root/.hermes/`、`/root/.codex/`、`/root/.config/Claude/`、`~/.gemini/`）、零 `out8/`/`shard2/`/`f8desk*`/`src/f8-proot-fast*` 更動、零 Stable `:1`（`X1`）影響、不擴張 `worker pool`。

---

## 一、程式碼層真實分流與抗壓／協定修補（非僅文件規範）

| 檔案 | 實測落地之程式變更 | 驗證方式 |
|---|---|---|
| [`scripts/f8_hybrid2_relay.py`](../../../scripts/f8_hybrid2_relay.py) | 1. 預設 `DEFAULT_NATIVE_TOOLS = frozenset({"repo_tree_scan", "repo_text_search", "git_ro"})`；`bridge_stdio_to_uds()` 僅將該 3 項導向原生 UDS Daemon，**`python_json_summary` 留在 PRoot 中繼本地引擎（Python 3.12）執行**（含 `--route-log` 決策稽核；僅 `--native-tools all` 才直通）。<br>2. 前門強制執行完整 **JSON-RPC 2.0 驗證**（與 `MCPToolEngine` 一致拒絕 `jsonrpc != "2.0"`、無效 `id`／`bool` `id`、缺 `method` 與無效 `params`）。<br>3. 補齊有界 **`--max-local-inflight`（預設 8，範圍 1–16，涵蓋 `deferred_local` 與 `local_active`）** 超額直回 `-32000`，以及 `len(to_stdout) >= 8 MiB` 讀取背壓與 `SIGTERM` `< 0.8 s` 快速退出。<br>4. 修復 `initialize` 未覆＋`deferred_local` 非空下遇 `stdin EOF` + `UDS EOF` 必乾淨結束或觸發 `early_eof` 重試／PRoot 回退；且 `notifications/cancelled` 會同步清除 `native_inflight` 防重複 `id` 誤殺。 | `test_selective_tool_routing_stage74` ＋ `test_relay_strict_jsonrpc_native_cancel_deferred_eof_and_bounded_local` ＋ Codex／Hermes 實機稽核：**`audit.jsonl` 僅見 3 項原生工具、零 `python_json_summary`**。 |
| [`scripts/f8_hybrid2_daemon.py`](../../../scripts/f8_hybrid2_daemon.py) | `ClientSession` 改採 `_out_buf` + `_wake_r/_wake_w`＋`serve()` `POLLOUT` 非阻塞事件迴圈（含 `4 MiB` `POLLIN` 背壓／`16 MiB` 硬上限）：`_run_tool_worker()` 先寫入 `_out_buf`、再釋放 `inflight_sem` 與移除 `_active[rk]`、最後才 `_wake()` 喚醒 `serve()` 寫回；徹底消除慢速讀取者阻塞 `sendall()` 造成 worker 堆積（`max_inflight=1` 下實測 16 請求零堆積）與快速客戶端背對背假性 `-32000`。 | 慢速讀取 `SO_RCVBUF=4096` + 16 連發壓測 ＋ `test_f8_hybrid2.py` **PRoot 13/13 PASS** ＋ **Termux 原生（`TracerPid=0`）13/13 PASS**。 |
| [`scripts/f8_hybrid2_ctl.py`](../../../scripts/f8_hybrid2_ctl.py) | 新增 `resolve_host_daemon_py()` 自動依 `DEFAULT_DAEMON_MAPS` 將 PRoot 路徑轉譯為 Termux 宿主路徑並檢核 `/data/data/com.termux/` 前綴；`client_config_snippets()` 優先產出雙側同路徑 `tools/hybrid2/f8_hybrid2_relay.py`。 | 實機直跑 `scripts/f8_hybrid2_relay.py --auto-start` 成功拉起原生 Daemon（`2,125.6 ms`, `tracer_pid=0`）。 |

---

## 二、既有 `rg`／`git`／`Serena`／`RTK` 工作流程對照與邊界矩陣

> **等價性揭露**：下表並列「PRoot CLI 單次執行（含 `exec` 開銷）」與「Stage 7.3 常駐 MCP 中繼（含預啟動常駐）」兩組不同測試載具數據，用於劃定工具分工而非宣稱同載具對比；特別是 `rg --files` 與 `repo_tree_scan` **工作量與過濾規則不等價**（`rg --files` 依 `.gitignore` 與隱藏檔規則僅列 `4,323` 個檔名且不計雜湊，而 `repo_tree_scan` 掃描全部 `4,469` 個非 `.git` 檔並計算 `51.35 MiB` SHA-256），數值僅供各自能力範圍參考。

| 工作負載 | PRoot 直接 CLI 中位 (`p95`) | PRoot 經 `rtk` 中位 (`p95`) | Stage 7.3 Native `B`（常駐 MCP） | 實測對照結論與防重疊邊界 |
|---|---:|---:|---:|---|
| `rg` fixed `"loriePresentFlip"` (`-g *.c -g *.h`, 2,280 檔) | `out8/bin`: **596.00 ms** (`688.17`)<br>互動殼複測 `792.52 ms` | `rtk rg`: 673.16 ms (`696.31`) | **592.62 ms** (`599.76`) | 皆 **2 hits / 346 B**；速度落於同級區間，Native 版省去 PRoot tracer CPU（`862.2 → 0 ms`）；`rtk rg` 0% 壓縮且多 `+77 ms` 負開銷。 |
| `rg` regex `"lorie_mutex\|loriePresent"` (`-g *.c -g *.h`, 2,280 檔) | `out8/bin`: **563.37 ms** (`706.47`)<br>互動殼複測 `799.50 ms` | `rtk rg`: 636.05 ms (`750.98`)<br>複測 `785.32 ms` | 836.59 ms (`858.42`) | 皆 **23 hits / 3,514 B**；Rust SIMD 多執行緒 `rg` 快於另開單執行緒 Python worker 之 `--regex-worker`；重型複雜多分支正則優先用 `/usr/bin/rg` 並避開 `rtk rg`。 |
| 目錄列出 vs 樹雜湊（**非等價操作**） | `rg --files`: 394.33 ms (`448.44`, 4,323 檔僅列路徑) | — | `repo_tree_scan`: **327.07 ms** (`338.37`, 4,469 檔含 51.35 MiB SHA-256) | 兩者過濾規則與輸出不同（非等價 benchmark）；實際需要完整非 `.git` 檔案清單或 SHA-256 校驗時採 Native `repo_tree_scan` 可避開大量 PRoot `getdents`/`stat`（對同工作量 `A1` `1,876.79 ms` 實測加速 `5.74×`）。 |
| `git grep -n seccomp` (`src/termux-proot-upstream`) | 64.05 ms (`74.50`) | `rtk git grep`: 84.08 ms (`118.65`) | **14.23 ms** (`15.56`) | **310 hits / 23,757 B**；`git_ro` 遠快於 PRoot CLI，且 `rtk rewrite` 對 `git grep` 回 `rc=1`、`rtk git grep` 0% 壓縮。 |
| `git log -n 500 --stat --no-renames` (`src/upstream`) | 498.81 ms (`608.41`) | `rtk git log`: 502.52 ms (`588.43`) | **199.58 ms** (`202.11`) | **322,907 B**；`git_ro` 快且不觸發 PRoot 追蹤；`rtk` 0% 壓縮（`rtk rewrite` 額外耗時 `22.5–25.0 ms`）。 |
| 對照：`git log -n 50`（無 `--stat`） | **15.83 ms** (`18.64`) | 40.04 ms (`55.74`) | — | **`25,493 → 14,758 B`（`-42.1%` 壓縮）**；`rtk` 應專用於高雜訊 CLI 摘要，不應疊加於 `rg`／`git grep`／結構化 JSON。 |
| `Serena` (`1.7.0`, LSP AST) | 符號定義／參考／重構 | — | 唯讀檔案樹／搜尋／Git | 職能互補：語意符號查詢用 Serena，全樹雜湊／批量檢索／唯讀 Git 用 Hybrid 2.0。 |

---

## 三、四客戶端隔離試點總表（區分冷／熱啟動、工具延遲與完整會話耗時）

| 客戶端（實測版本） | 7 變數行為與隔離前提 | 冷啟動 (`--auto-start`) | 熱啟動／工具延遲 | 關閉／取消／重連／回退 | 嚴格試點判定與未驗項目 |
|---|---|---:|---:|---|---|
| **Hermes Agent** (`v0.23.4`, `mcp 2.0.0`) | `_SAFE_ENV_KEYS` 預設剝除（安全退回 `4,505 ms`）；於隔離 `HERMES_HOME/config.yaml` 注入 7 變數可拉起原生；隔離環境需 committed venv + `HERMES_DISABLE_LAZY_INSTALLS=1` 防重拉 venv。 | `hermes mcp test`: **6,310.2 ms** (`tp=0`)；腳本化 `ClientSession` `init=1,635.3 ms`／全套 **1,695.6 ms**（4 步混合 **3,335.3 ms**, N=1） | `hermes mcp test` 中位 **4,543.9 ms**（含 ~2.5s CLI 啟動）；腳本化熱會話 `init=198.9 ms`／4 步 **2,481.5 ms**（vs 回退 **5,876.5 ms**） | `asyncio.Task.cancel()` → `audit.jsonl` 記 `"decision": "cancelled"`（fds=6）；`ctl stop` 後自動重連拉起新 daemon (`tp=0`)；`ctl disable` 後 `hermes mcp test` 與腳本化會話皆經 PRoot 通過。 | **`PARTIAL_PASS`**（MCP 工具層、冷熱、取消、重連、回退皆通過；`hermes chat` 無金鑰 `rc=1` → 完整多輪 AI 任務耗時 **`UNKNOWN`**） |
| **Claude Code** (`2.1.330`) | 預設**保留** 7 `AM_REQUIRED_ENV`；隔離 `CLAUDE_CONFIG_DIR` 下 `claude mcp add` 直接生效。 | `claude mcp get hybrid2`：**2,651.6–2,780.2 ms** (`✔ Connected`, 拉起 `tp=0`) | `claude mcp get` 熱連線：**1,108.7 ms**（含 CLI 啟動） | `ctl disable` 後 `claude mcp get` 回傳 **`✔ Connected`**（**1,156.9 ms**, 安全走 PRoot 回退）。 | **`PARTIAL_PASS`**（MCP 註冊／冷熱健康檢查／回退通過；CLI 未帶獨立 `tools/call` 子命令且 `claude -p` 無登入態 → 真實工具調用／AI 對話為 **`BLOCKED_NO_AUTH`**） |
| **Codex CLI** (`0.171.0-alpha.13.2`) | 預設 `shell_environment_policy` 剝除 7 變數（`278.0 ms` 安全退回）；於隔離 `CODEX_HOME/config.toml` 加 `env_vars` 後透過 **`codex app-server`** 免帳號實測。 | `mcpServerStatus/list`：**2,194.1 ms**（實機拉起 `tp=0`） | `thread/start` `120.7 ms`；`mcpServer/tool/call`：`repo_tree_scan` `1,118.9 ms`、`repo_text_search` `807.9 ms`、`git_ro` `73.3 ms`、`python_json_summary` `12.7 ms`（`audit.jsonl` + `routes.jsonl` 雙驗證） | `ctl disable` 後 `mcpServer/tool/call git_ro` 透過 PRoot 通過（`212.3 ms`）。`codex app-server` `ClientNotification` Schema 無取消 RPC → **`UNSUPPORTED_IN_APP_SERVER`**。 | **`PARTIAL_PASS`**（via `codex app-server` 握手／4 工具／選擇性分流／回退通過；無單次取消通知、無認證 `codex exec` 逾時 `>15s` → **`BLOCKED_NO_AUTH`**） |
| **Claude Desktop** (`6.28899.6`) | `mcpServers` stdio JSON；需 `--no-sandbox --disable-gpu --ozone-platform=x11`。 | — | — | 無 `DISPLAY` 下 `--user-data-dir` 探測報 `rc=1`；受 `:1` 紅線、雙 Electron 上限與登入態限制未碰實機桌面。 | **`UNVERIFIED_LIVE_GUI`** |
| **Antigravity** (`44.9.1`) | Electron + Go `language_server`（`1.11.0`, `-gemini_dir`）；無 `DISPLAY` 即使傳 `--user-data-dir` 仍讀 `$HOME` 下配置並 `SIGSEGV (rc=-11)`；獨立 `language_server` 要求互動式 OAuth。 | — | — | 受 `:1` 雙 Electron 上限與紅線限制未改動正式設定或重啟實機 GUI。 | **`UNVERIFIED_LIVE_GUI / BLOCKED_NON_INTERACTIVE`** |

---

## 四、部署前安全條件（暫不修改現役客戶端設定）

1. **僅分流三項原生工具**：維持 `DEFAULT_NATIVE_TOOLS = {"repo_tree_scan", "repo_text_search", "git_ro"}` 與 `--max-local-inflight 8`（預設），確保純 CPU JSON 解析與重型複雜正則／`rtk` 高雜訊摘要不發生負收益，且不在 Stage 7.4 引入多程序 worker pool。
2. **Hermes / Codex 若日後啟用免預啟動 `--auto-start`**：須於其獨立設定檔顯式帶入 7 `AM_REQUIRED_ENV`；未帶入時自動安全退回 PRoot 本地模式。
3. **隔離乾淨狀態**：全部暫存測試路徑已清理，工作站基線未受任何影響，待 PR #53 更新合併後推進 Stage 7.5 異常壓測。

### 五、安全複審候選版（隔離測試通過，待審閱）

- GPT-6.1 Terra 修正 Daemon 回應編碼例外與 worker 啟動失敗時的 inflight 清理。Relay 在 UDS EOF 後會排空已排隊的本地回應，PRoot fallback 與 UDS 斷線排空維持 stdout 非阻塞。
- `git_ro` 拒絕無法辨識的倉庫、裸倉庫、`core.worktree`、物件庫 alternates，並驗證 Git 設定與物件庫的路徑邊界。Linked worktree 的 metadata 必須解析到允許映射且未受保護的路徑。檢查採執行前快照，並行替換 metadata 仍是已知限制。
- 同一裝置重新驗證既有候選版時，PRoot 13/13，Termux Native 12/13（分流測試於 EOF 漏回應）。安全複審候選版通過 PRoot 15/15（21.645 s）與 Termux Native 15/15（16.336 s，`TracerPid: 0`），包含原失敗的分流測試與新增的 Git／worker 例外清理回歸。PRoot 的 fallback 使用滿管線進行驗證，延遲讀取後仍可取得完整回應，未讀取時送出 SIGTERM 於 0.120 s 結束。
- 新版尚待 Neon 複審與 GitHub CI。既有多客戶端試點結果沿用其原測試版本與限制。

### 六、接手複審修補與隔離驗證

- 兩位 GPT-6.1 Terra 分別修補直通傳輸、子程序輸出與取消驗證。直通模式的兩個傳輸佇列各限 8 MiB。正常 UDS EOF 後排空已收到的回應。收到終止訊號時最多再等 1 秒，接收端持續阻塞時可能仍有未送出的資料。
- Git 與正則工作的共用子程序監督器改用有界非阻塞 pipe，stdout 2 MiB、stderr 256 KiB。超限時終止與回收子程序，回報 `subprocess-output-limit`。Daemon、選擇性分流與本地回退共用取消通知驗證。
- 整合程式提交 `0fa61e8` 通過 PRoot 23/23（24.596 s）與 Termux Native 23/23（18.255 s，`TracerPid: 0`）。PRoot 全庫 Python 55/55。必要治理 workflow 已增列 Hybrid 2.0 測試，[PR CI](https://github.com/waydefu/GPU/actions/runs/45983252510) 在 `bba350d` 實跑 23/23。

- 後續補上 `git_ro` 對 `objects/pack` 及其直屬符號連結的邊界檢查。越界路徑在 Git 啟動前拒絕，映射內已打包物件仍可正常讀取。PRoot 24/24（24.213 s），Termux Native 24/24（18.468 s，`TracerPid: 0`）。
