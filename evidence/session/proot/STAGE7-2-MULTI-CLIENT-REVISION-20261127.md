# Stage 7.2–7.5 修訂計畫：通用多客戶端 MCP 原生工具後端（2026-11-27）

> **文件定位**：依 append-only 治理規則，保留原 [`STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md`](STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md) 不覆寫，由本修訂正式取代該檔 `§1.4` 及 `§3.1–3.3` 之 Hermes 單一架構限制。
> **分工模式**：主工程師 **Hydrogen**（架構、MCP 協議、安全邊界、生命週期與最終裁決）× 獨立審查 **Neon**（架構／競態／安全漏洞審查、多客戶端相容矩陣、測試與效能分析）。

---

## 一、架構轉向：從 Hermes 專用轉為通用 MCP 原生後端

1. **客戶端中立的標準 MCP Stdio 接入**：
   - 所有支援 MCP stdio 的客戶端統一透過 `python3 .../f8_hybrid2_relay.py` 連入共用單例原生（`TracerPid == 0`）`AF_UNIX` Daemon，不依賴任何單一 Agent 的專有 CLI 或環境變數白名單。
2. **脫離 `$PREFIX/tmp` 遷往 `TERMUX_HOME`**：
   - 依 `shard-daemon.sh` 歷史實證，TermuxService 重啟會清空 `$PREFIX/tmp`，造成 socket/pidfile 遭 unlink 而分裂出雙 daemon；且無 `--shared-tmp` 的 PRoot 會話看不見 `$PREFIX/tmp`。
   - 預設 runtime 目錄改設於 `/data/data/com.termux/files/home/.f8hyb2/`（`m.sock` 全長 `47` bytes `<= 107`，所有非隔離 PRoot 會話皆預設掛載且不被 TermuxService 清空），並保留 `sock_ino`/`pid_ino` 核對與原子就緒標記。
3. **統一啟停控制器（`f8_hybrid2_ctl.py`）＋ 單例／多客戶端／閒置回收／全域停用**：
   - 控制器提供 `start / stop / restart / status / probe / enable / disable / ensure-running / client-config`。
   - 跨行程 `flock` single-flight 防驚群（thundering-herd）；正確處理 MCP 客戶端（如 Hermes `_SAFE_ENV_KEYS`、`mcp 2.0.0`、Codex、Claude）剝除 7 個 Android 環境變數的情境——未事前啟動且無法透過 `am` 跨界拉起時，**安全退回 PRoot 引擎而非以 `rc=4` 崩潰**。
   - Daemon 強制單例、支援 `--max-clients`／`--max-inflight` 背壓、Per-Connection 請求隔離、禁止重複活躍 `req_id`、`initialize` 狀態機驗證，及「先原子 `unlink(m.sock)` 再 drain `accept()` backlog」的無競態閒置自動停機（`--idle-timeout`）。
   - 全域停用：`ctl disable`（寫入 `disabled.flag` 並停機；停機逾時回非零碼，已連線 UDS 會話以 `EOF` 斷線結束而非透明熱切換，僅新連線／重連轉由 PRoot 本地執行）或 `F8_NO_HYBRID=1`，停機零殘留。
   - **安全強化（補齊 Stage 5 並修復 7.2 初版缺口）**：`validate_git_ro` 補齊路徑／`--no-index`／`-f` 檢查、`--no-textconv`、`GIT_OPTIONAL_LOCKS=0` 與完整 `GIT_BAD_CFG`／`worktree`／`commondir` 檢查；`map_path` 針對 `real_host` 反查 `PROTECTED`；所有讀檔採用 `O_NOFOLLOW`；`_tool_git_ro` 使用 `pidfd_open` + `select.poll()` 消除 `20 ms` 輪詢；限制檔案讀取／JSON 載入與單行正則長度防 OOM/ReDoS；JSON 回應按 UTF-8 位元組安全截斷。

---

## 二、本機六大 MCP 客戶端實情與相容性矩陣（2026-11-27 實測盤點）

| 客戶端 | 安裝路徑與實際版本 | MCP 設定介面與傳輸 | 狀態分類（嚴禁混同） | 隔離驗證策略 |
|---|---|---|---|---|
| **Hermes Agent** | `/root/.local/bin/hermes` (`v0.23.4`, `mcp 2.0.0`) | `$HERMES_HOME/config.yaml` (`mcp_servers`)；stdio + Streamable HTTP；`_SAFE_ENV_KEYS` 會濾除 7 Android 變數 | **協議支援／設定已驗／待通用化重測** | `HERMES_HOME=/tmp/...` 執行 `hermes mcp add/test` ＋ `mcp 2.0.0` `ClientSession` 並發／取消／超時／回退實測 |
| **Codex CLI** | `/usr/lib/chatgpt/resources/codex` (`codex-cli 0.171.0-alpha.13.2`) | `$CODEX_HOME/config.toml` (`[mcp_servers.<name>]`)；stdio + Streamable HTTP (`codex mcp add/get/list`) | **協議支援／離線設定可驗／實機握手 `UNKNOWN`（待測）** | `CODEX_HOME=/tmp/...` 離線 `codex mcp add/get --json/list` 驗證＋檢查無帳號依賴握手能力 |
| **Claude Code** | `/root/.config/Claude/claude-code/2.1.330/fd32a5b15526/claude` (`2.1.330`) | `$CLAUDE_CONFIG_DIR` / `.mcp.json` (`claude mcp add/get/list`)；stdio/SSE/HTTP；`get` 會主動健康檢查 | **協議支援／待實機健康檢查驗證** | `CLAUDE_CONFIG_DIR=/tmp/...` 於暫存專案執行 `claude mcp add` ＋ `claude mcp get` 實機觸發 stdio 健康檢查 |
| **Claude Desktop** | `/usr/bin/claude-desktop` (`dpkg 6.28899.6` arm64) | `/root/.config/Claude/claude_desktop_config.json` (`mcpServers` stdio JSON)；GUI Electron 長駐連線 | **協議支援／Schema 已確認／實機 GUI `UNVERIFIED_LIVE_GUI`** | 不動 `/root/.config/Claude` 與 `:1`；驗證 JSON schema ＋ stripped-env `relay` 模擬；實機 GUI 留待隔離 `:99` 授權實驗 |
| **Antigravity (AGY)** | `/opt/antigravity-hub/antigravity` (`44.9.1`) | `~/.gemini/config/mcp_config.json` (`mcpServers` Stdio + Streamable HTTP，無 legacy SSE) | **協議支援／Schema 已確認／實機 GUI `UNVERIFIED_LIVE_GUI`** | 不動 `~/.gemini/`；驗證 `mcp_config.json` schema ＋ stripped-env `relay` 模擬；實機 GUI 留待隔離授權實驗 |
| **OpenCode** | **MISSING**（全根目錄檔案掃描無二進位） | 標準 MCP stdio JSON（通用協議層） | **`NOT INSTALLED` / `UNKNOWN`** | 本機未安裝，不納入實機 PASS 條件 |

---

## 三、修訂後 Stage 7.2–7.5 必驗門檻

### 3.1 Stage 7.2 通用隔離原型必過項目
1. **統一控制器與 7-env 剝除測試**：`ctl start/stop/restart/status/probe/disable/enable/ensure-running` 正常運作；在 `env -i PATH=... HOME=...`（剝除 7 個 Android 變數）下執行 `relay`，不得出現 `rc=4` 崩潰。
2. **多客戶端並發、請求隔離與驚群防線**：`4+` 客戶端並發連線（含 `ensure-running` 競爭）保持單實例無 split-brain；單一客戶端觸發 `--max-inflight`、`notifications/cancelled`、`-32001` timeout、策略拒絕或 `SIGKILL` 斷線時，**不影響其他已連線客戶端的並行請求**，`children_final = 0`、`fds_final == fds_base`。
3. **全部斷線、閒置自動回收與重連**：最後一個客戶端關閉並經過 `idle_timeout` 後，原子 `unlink` socket、排空 backlog、零殘留停機；在 `idle_timeout` 觸發臨界壓測並發 `connect()` 不得出現「連上卻 EOF 失敗」；後續 `ctl ensure-running`／`start` 重連可平滑恢復。
4. **全域停用與安全回退**：`ctl disable` 或 `F8_NO_HYBRID=1` 下，所有客戶端透過 `relay` 退回與原生端相同 `--map`／安全規則的 PRoot 本地模式；停止並移除暫存設定後，工作站零殘留。
5. **補齊安全迴歸與資源防線測試**：覆蓋 `git diff --no-index /etc/...`、`git grep -f`、`.git/config.worktree`、`[filter]`/`[diff] command=`、mapped 目錄內 symlink 連向 `PROTECTED`、重複活躍 `req_id`、未 `initialize` 呼叫工具、UTF-8 多位元組截斷與大檔記憶體上界。
6. **多客戶端實機隔離驗收**：於獨立暫存設定根實測 **Hermes**（`hermes mcp test` ＋ `mcp 2.0.0` `ClientSession`）、**Claude Code**（`claude mcp add` ＋ `claude mcp get` 健康檢查）、**Codex CLI**（`codex mcp add/get --json/list` ＋ 確認是否具免 API 握手）；其餘客戶端嚴格依表區分 `UNVERIFIED_LIVE_GUI`／`NOT INSTALLED`。

### 3.2 Stage 7.3–7.5 同步修訂重點
- **Stage 7.3（A/B 對照）**：ABBA 樣本提高至 **至少 `n = 10` 對**（`>= 9/10` 勝方得雙尾符號檢定 `sign_p = 0.0215 < 0.05`）；分層區分**目標重型工具工作負載**與**短命令（不退化門檻 `>= 1.00×`）**，並同步量測多客戶端冷啟動延遲與並行吞吐。
- **Stage 7.4（多客戶端隔離試點）**：先以隔離設定根跑通 Hermes / Claude Code（及 Codex 若有離線通道），不主動更動日常桌面與客戶端正式設定；Serena/Node 重型 LSP 不塞入共用 stdlib Daemon，以免推高 RSS 遭 LMKD 連坐砍殺。
- **Stage 7.5（穩定性與異常壓測）**：除 `>= 1,000` ops 與斷線／取消壓測外，必須補測 **模擬 socket/pidfile 遭外部刪除（如 TermuxService 事件）之自癒不分裂** 與 **閒置停機臨界並發重連**。
