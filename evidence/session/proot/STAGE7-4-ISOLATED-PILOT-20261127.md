# Stage 7.4 — 隔離客戶端試點與既有工作流對照驗收報告（2026-11-27）

- **狀態**：**`STAGE7_4_ISOLATED_PASS`（程式碼層選擇性分流落地並於隔離試點驗收通過；未修改任何現役客戶端正式設定、未擴張 worker pool，待審閱部署決策後再議 Stage 7.5 壓測）**
- **依據文件**：[`STAGE7-2-MULTI-CLIENT-REVISION-20261127.md`](STAGE7-2-MULTI-CLIENT-REVISION-20261127.md) `§3.2`、[`STAGE7-3-ABBA-BENCHMARK-20261127.md`](STAGE7-3-ABBA-BENCHMARK-20261127.md)
- **協作分工**：Neon（四客戶端隔離試點實測與 `rg`／`git`／`Serena`／`RTK` 工作流實測對照）× Hydrogen（程式碼層分流實作、跨側路徑修復、`daemon` 競態修復、雙軌 12/12 回歸測試與實機交叉複核）
- **紅線遵循**：零現役客戶端設定異動（`/root/.hermes/`、`/root/.codex/`、`/root/.config/Claude/`、`~/.gemini/`）、零 `out8/`/`shard2/`/`f8desk*`/`src/f8-proot-fast*` 更動、零 Stable `:1`（`X1`）影響、不擴張 `worker pool`。

---

## 一、程式碼層真實分流與關鍵修復（非僅文件規範）

| 檔案 | 實測落地之程式變更 | 驗證方式 |
|---|---|---|
| [`scripts/f8_hybrid2_relay.py`](../../../scripts/f8_hybrid2_relay.py) | 預設 `DEFAULT_NATIVE_TOOLS = frozenset({"repo_tree_scan", "repo_text_search", "git_ro"})`；`bridge_stdio_to_uds()` 解析 MCP stdio JSON-RPC 行後，僅將該 3 項工具送往原生 `AF_UNIX` Daemon，**`python_json_summary` 一律留在 PRoot 本地引擎（Python 3.12）於中繼行程執行**（支援管線化 `initialize` 佇列、本地 `notifications/cancelled`、重複 `req_id` `-32600`、`pre-init` `-32002`、`early_eof` 重試防漏與 `--route-log` 決策稽核；僅明確傳 `--native-tools all` 才退回全通道轉發）。 | `test_selective_tool_routing_stage74` ＋ Codex／Hermes 實機稽核：**`audit.jsonl` 僅見 3 項原生工具、零 `python_json_summary`；`routes.jsonl` 確記 `native_uds` vs `proot_local`**。 |
| [`scripts/f8_hybrid2_ctl.py`](../../../scripts/f8_hybrid2_ctl.py) | 新增 `resolve_host_daemon_py()`，於 `_start_via_termux_service()` 自動依 `DEFAULT_DAEMON_MAPS` 將 PRoot 路徑（`/root/projects/...`）轉譯為 Termux 宿主路徑並檢核 `/data/data/com.termux/` 前綴（解決先前從 `scripts/` 呼叫 `--auto-start` 時白耗 `6s` 報 `Errno 2` 之問題）；`client_config_snippets()` 優先產出雙側同路徑 `tools/hybrid2/f8_hybrid2_relay.py` 並補充 Hermes/Codex 7 變數提示。 | 實機直接執行 `scripts/f8_hybrid2_relay.py --auto-start` 通過（`2,125.6 ms`, `running=True`, `tracer_pid=0`）。 |
| [`scripts/f8_hybrid2_daemon.py`](../../../scripts/f8_hybrid2_daemon.py) | `_run_tool_worker()` 改為於 `call_tool()` 結束後**先釋放 `inflight_sem` 與移除 `_active[rk]`，再執行 `send_json()`**，消除 Termux 原生超低延遲下背對背請求觸發假性 `-32000` 之競態。 | `test_f8_hybrid2.py` **PRoot 12/12 PASS**（`23.782s`）＋ **Termux 原生（`TracerPid=0`）12/12 PASS**（`15.880s`）。 |

---

## 二、既有 `rg`／`git`／`Serena`／`RTK` 工作流程實測對照與邊界矩陣

於相同 Stage 7.3 目標目錄（`src/upstream/lorie/src/main/cpp` 2,280 `.c/.h` 檔、`src/termux-proot-upstream`、`src/upstream`），以 `out8/bin/proot-fast8` 實測對照（`n = 10` 交錯＋2 warmup；另有同機 Antigravity 殼層 3 次複測作附註）：

| 工作負載 | PRoot 直接 CLI 中位 (`p95`) | PRoot 經 `rtk` 中位 (`p95`) | Stage 7.3 Native `B` 中位 | 實測對照結論與防重疊邊界 |
|---|---:|---:|---:|---|
| `rg` fixed `"loriePresentFlip"` (`-g *.c -g *.h`) | **596.00 ms** (`688.17`)<br>複測 `792.52 ms` | `rtk rg`: 673.16 ms (`696.31`) | **592.62 ms** (`599.76`) | 皆 **2 hits / 346 B**；速度打平，但 Native `repo_text_search` 省去 PRoot tracer CPU（`862.2 → 0 ms`）；`rtk rg` 無壓縮且多 `+77 ms` 負收益。 |
| `rg` regex `"lorie_mutex\|loriePresent"` (`-g *.c -g *.h`) | **563.37 ms** (`706.47`)<br>複測 `799.50 ms` | `rtk rg`: 636.05 ms (`750.98`)<br>複測 `785.32 ms` | 836.59 ms (`858.42`) | 皆 **23 hits / 3,514 B**；Rust SIMD 多執行緒 `rg` 比原生 `--regex-worker` **快 1.48×**；重型複雜回溯正則應留給 PRoot `/usr/bin/rg`（且避開 `rtk rg` 0% 壓縮開銷）。 |
| `rg --files` vs `repo_tree_scan` | 394.33 ms (`448.44`, 4,323 檔無 SHA) | — | **327.07 ms** (`338.37`, 4,469 檔含 51.35 MiB SHA-256) | Native `repo_tree_scan` 連同完整檔案 SHA-256 仍快過僅列檔名之 PRoot `rg --files`。 |
| `git grep -n seccomp` | 64.05 ms (`74.50`) | `rtk git grep`: 84.08 ms (`118.65`) | **14.23 ms** (`15.56`) | **310 hits / 23,757 B**；Native `git_ro` 快 **4.50×**；`rtk rewrite` 對 `git grep` 回 `rc=1` 且 `rtk git grep` 0% 壓縮。 |
| `git log -n 500 --stat --no-renames` | 498.81 ms (`608.41`) | `rtk git log`: 502.52 ms (`588.43`) | **199.58 ms** (`202.11`) | **322,907 B**；Native `git_ro` 快 **2.50×**；`rtk` 0% 壓縮（`rtk rewrite` 本身耗 `22.5–25.0 ms`）。 |
| 對照：`git log -n 50`（無 `--stat`） | **15.83 ms** (`18.64`) | 40.04 ms (`55.74`) | — | **`25,493 → 14,758 B`（`-42.1%` 壓縮）**，證實 `rtk` 價值在於高雜訊 CLI 摘要而非 `rg`／結構化輸出。 |
| `Serena` (`1.7.0`, LSP AST) | 符號定義／參考／重構 | — | 檔案／文字／唯讀 Git | 職能互補不重疊：符號語意操作用 Serena，大樹掃描／批量搜尋／唯讀 Git 用 Hybrid 2.0。 |

---

## 三、四客戶端隔離試點實測總表（明確區分冷／熱啟動、工具延遲與完整會話耗時）

| 客戶端（實測版本） | 7 變數行為與設定隔離 | 冷啟動 (`--auto-start`) | 熱啟動／工具延遲 | 關閉／取消／重連／回退 | 試點判定與誠實未測邊界 |
|---|---|---:|---:|---|---|
| **Hermes Agent** (`v0.23.4`, `mcp 2.0.0`) | `_SAFE_ENV_KEYS` 預設剝除（安全退回 `4,505 ms`）；於隔離 `HERMES_HOME/config.yaml` `env:` 帶入後可拉起原生。另需 committed venv + `HERMES_DISABLE_LAZY_INSTALLS=1` 防 `_prepare_borrowed_launch` 重建 venv。 | `hermes mcp test`: **6,310.2 ms** (`tp=0`)；`ClientSession` `init=1,635.3 ms`／全套 **1,695.6 ms**（4 步混合會話 **3,335.3 ms**） | `hermes mcp test` 中位 **4,543.9 ms**（含 ~2.5s CLI 啟動）；熱會話 `init=198.9 ms`、`session_e2e=2,481.5 ms`（`git_ro grep` 21.2ms、`tree_scan` 430.2ms、`json_local` 8.5ms） | `asyncio.Task.cancel()` → `audit.jsonl` 實錄 `"decision": "cancelled"`（fds=6 零洩漏）；`ctl stop` 後自動重連拉起新原生 daemon (`tp=0`)；`ctl disable` 後 `hermes mcp test` 與全會話（5,876.5 ms）皆安全走 PRoot 通過。 | **`PASS`**（MCP 工具層全通過；`hermes chat` 無金鑰報 `rc=1` → 完整 LLM 對話循環標記 **`UNKNOWN`**） |
| **Claude Code** (`2.1.330`) | 預設**保留** 7 `AM_REQUIRED_ENV`；隔離 `CLAUDE_CONFIG_DIR` 下 `claude mcp add` 直接生效。 | `claude mcp get hybrid2`：**2,651.6–2,780.2 ms** (`✔ Connected`, 拉起 `tp=0`) | `claude mcp get` 熱連線：**1,108.7 ms**（含 CLI 啟動） | `ctl disable` 後 `claude mcp get` 回傳 **`✔ Connected`**（**1,156.9 ms**, 安全走 PRoot 回退）。 | **`PASS`**（MCP 註冊／冷熱健康檢查／回退全通過；`claude -p` 無登入態 → **`BLOCKED_NO_AUTH`**） |
| **Codex CLI** (`0.171.0-alpha.13.2`) | 預設 `shell_environment_policy` 剝除 7 變數（`278.0 ms` 安全退回）；於隔離 `CODEX_HOME/config.toml` 加 `env_vars` 後透過 **`codex app-server`** 免帳號實測。 | `mcpServerStatus/list`：**2,194.1 ms**（實機拉起 `tp=0`） | 同會話 `thread/start` `120.7 ms`；`mcpServer/tool/call`：`repo_tree_scan` `1,118.9 ms`、`repo_text_search` `807.9 ms`、`git_ro` `73.3 ms`、`python_json_summary` `12.7 ms`（`audit.jsonl` + `routes.jsonl` 雙驗證） | `ctl disable` 後 `mcpServer/tool/call git_ro` 透過 PRoot 通過（`212.3 ms`）。`codex app-server` `ClientNotification` Schema 無取消 RPC → 單次取消標記 **`UNSUPPORTED_IN_APP_SERVER`**。 | **`PASS`（via `codex app-server`）**（`codex exec` 無認證逾時 `>15s` → **`BLOCKED_NO_AUTH`**） |
| **Claude Desktop** (`6.28899.6`) | `mcpServers` stdio JSON；需 `--no-sandbox --disable-gpu --ozone-platform=x11`。 | — | — | 無 `DISPLAY` 下 `--user-data-dir` 探測報 `rc=1`；受 `:1` 紅線、雙 Electron 上限與登入態限制未碰實機桌面。 | **`UNVERIFIED_LIVE_GUI`** |
| **Antigravity** (`44.9.1`) | Electron + Go `language_server`（`1.11.0`, `-gemini_dir`）；無 `DISPLAY` 即使傳 `--user-data-dir` 仍讀 `$HOME` 下配置並 `SIGSEGV (rc=-11)`；獨立 `language_server` 要求互動式 OAuth。 | — | — | 受 `:1` 雙 Electron 上限與紅線限制未改動正式設定或重啟實機 GUI。 | **`UNVERIFIED_LIVE_GUI / BLOCKED_NON_INTERACTIVE`** |

---

## 四、部署前安全條件（暫不自動修改現役客戶端設定）

1. **僅分流三項原生工具**：維持 `DEFAULT_NATIVE_TOOLS = {"repo_tree_scan", "repo_text_search", "git_ro"}`，確保純 CPU JSON 解析與 `rg` 多分支複雜正則／`rtk` 高雜訊摘要各歸其位、零負收益。
2. **Hermes / Codex 若日後要免預啟動 `--auto-start`**：須於其各別 `config.yaml` / `config.toml` 明確保留 7 `AM_REQUIRED_ENV`，否則依設計自動退回 PRoot 本地執行；長期高頻使用則建議於階段間由 `f8_hybrid2_ctl.py ensure-running` 維持單例熱常駐，省去 `1.1–2.8 s` 冷啟動。
3. **本階段不異動現役設定**：所有測試目錄 `/tmp/s74_*` 與 `.f8hyb2-s74*`／`.f8hyb2-h74*` 已清除，工作站與測試套件全綠，待審閱核准後再進 Stage 7.5 或評估單客戶端正式試點部署。
