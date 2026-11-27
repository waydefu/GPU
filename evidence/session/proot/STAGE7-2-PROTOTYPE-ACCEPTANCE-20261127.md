# Stage 7.2 — 通用多客戶端 Native Hybrid 2.0 隔離原型驗收報告（2026-11-27）

- **狀態**：**`STAGE7_2_PASS`（達標通用化 Stage 7.2，停在 7.2 邊界等待 PR 審閱後再決定是否啟動 7.3）**
- **依據文件**：[`STAGE7-2-MULTI-CLIENT-REVISION-20261127.md`](STAGE7-2-MULTI-CLIENT-REVISION-20261127.md)（取代原 [`STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md`](STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md) `§1.4`／`§3.1–3.3`）
- **角色協作**：Hydrogen（核心架構、MCP 協議、安全邊界、生命週期與裁決）× Neon（兩輪獨立架構／程式碼／測試覆蓋率審查，其第 2 輪所提全數 Blocker/High 缺口均已修復並經複測）
- **紅線遵循**：純 Python stdlib（零額外套件安裝）、未修改 `out8/`／`shard2/`／`f8desk*`／`/usr/local/bin/f8-shard`／Stable `:1`／`src/f8-proot-fast*`／任何現役 AI 客戶端設定（`/root/.hermes/`、`/root/.codex/`、`/root/.config/Claude/`、`/root/.gemini/`）。

---

## 一、通用架構與交付模組

| 檔案（`scripts/` ＆ 隔離目錄 `tools/hybrid2/`） | 核心能力與修訂項目 |
|---|---|
| `f8_hybrid2_policy.py` | 預設 runtime 遷至 `TERMUX_HOME/.f8hyb2/`（`47` bytes，免疫 TermuxService 清空 `$PREFIX/tmp`）；`map_path` 對 `//` 正規化並對 `real_host` 反查 `PROTECTED`（不誤殺 `--map` 顯式祖先）；`open_nofollow` 加 `O_NONBLOCK` 免疫 FIFO；`validate_git_ro` 阻擋 `--no-index`／`-f`/`-f...`／`--contents=` symlink 逃逸，補回 `--no-textconv`、`GIT_OPTIONAL_LOCKS=0`、`GIT_CEILING_DIRECTORIES`；`git_cfg_scan` 掃描同行 `[core] fsmonitor`、`.git/config.worktree`、`512 KiB` 上限與目錄型 `.git` realpath。 |
| `f8_hybrid2_tools.py` | 強制 MCP `initialize` 狀態機（`-32002`）、嚴格 `canonical_req_key`（區分 `int`/`str`、拒絕 `bool`）、`RequestContext.cancel()` 全程持鎖防 FD 重用寫錯連線、`_tool_git_ro` 使用 `pidfd_open` + wakeup pipe 進 `select.poll()`（單次 `git_ro` 由 `32.59 ms` 降至 `11.8 ms`）且取消必拋 `RequestCancelled`、`_strict_int_arg` 拒絕 `null`/非整數、`.jsonl` 設 `1 MiB` 單行與 `32 MiB` 總量防線、`_fit_json_payload` 按 UTF-8 byte 安全截斷 `entries`/`matches`/`stdout`/`stderr`。 |
| `f8_hybrid2_daemon.py` | 原生單例 Daemon（強制 `TracerPid == 0` 且拒於 `disabled.flag` 下啟動）：`flock` pidfile → `bind(0600)` + `listen(64)` → 原子 `.ready`（含 `_ready_ino`）；支援 `--max-clients`／`--max-inflight` 背壓（`-32000`）、拒絕重複活躍 `req_id`（`-32600`）、每 5 秒 `sock_ino`/`pid_ino` 防分裂檢查、`5 MiB` 稽核日誌輪替；無競態 `idle-timeout` 先原子刪 `sock`/`ready` → 排空 `accept()` backlog → **立即釋放 `d.pid` 供新實例無縫重啟**再等舊連線收尾。 |
| `f8_hybrid2_relay.py` | 客戶端中立 stdio-to-UDS 中繼：尊重 `disabled.flag` 與 `F8_NO_HYBRID=1`；PRoot 下遇客戶端剝除 7 Android 變數時安全退回 PRoot 引擎而不 `rc=4` 崩潰；`early_eof` 自動重連／退回；`selectors` 動態 `EVENT_WRITE` + wakeup pipe；fallback worker 補齊異常保護（`-32603`）、`4 MiB` 幀上限與 `< 0.8s` `SIGTERM` 喚醒。 |
| `f8_hybrid2_ctl.py` | 統一啟停控制器（`start/stop/restart/status/probe/enable/disable/ensure-running/client-config`），全寫入路徑共享 `ctl.lock` 防驚群與競態，`stop` 先核對 `pidfile` 與 `/proc/<pid>/cmdline` 再送 `SIGTERM`。 |
| `test_f8_hybrid2.py` | 10 項完整單元、安全、多客戶端並發與生命週期測試（PRoot 與 Termux 原生皆為 10/10）。 |

---

## 二、實測驗收結果（全部於最終版本程式碼後重跑驗證）

### 2.1 單元、安全與生命週期測試（`test_f8_hybrid2.py`）

| 環境 | 指令 | `TracerPid` | 結果 |
|---|---|---:|---|
| PRoot Ubuntu | `python3 scripts/test_f8_hybrid2.py` | `!= 0` | **10/10 PASS**（`16.794s`） |
| Termux 原生（`termux-bg-run`） | `F8_HYBRID2_NATIVE=1` + `run-native-tests.sh` | **`0`**（`Uid: 10365`） | **10/10 PASS**（`11.275s`，`rc=0`） |

涵蓋並通過項目：
- 安全邊界：`protected-path`（含 `//etc/passwd`、mapped 父目錄內受保護子目錄、`.f8hyb2`、`out8/`）、`symlink-escape`、`.l2s.*`、FIFO `O_NONBLOCK` 不阻塞、`git diff --no-index`、無空格 `git grep -f/etc/passwd`、`git blame --contents=escape/...`、`GIT_CEILING_DIRECTORIES`、單行 `[core] fsmonitor = true`、`.git/config.worktree`、`filter.process`、`diff.command`、`512 KiB` config 上限、`.gitfile`／`commondir` 絕對路徑。
- 協議與資源邊界：未 `initialize` 回 `-32002`、`bool` id 回 `-32600`、重複活躍 `req_id` 回 `-32600`、`max_entries: null` 於 native 與 fallback 皆回 `-32602`、`entries`/`stdout`/`stderr` UTF-8 截斷、`.jsonl` 單行 `> 1 MiB` 拒絕、`> 2 MiB` 搜尋標記 `skipped_oversize`、3,000 次 fuzz。
- 多客戶端與控制器：`--max-clients 4` 第 5 連線 `-32000`、`--max-inflight 1` 確定命中 `-32000`、4 客戶端並發查詢與單客戶端取消／逾時不干擾他人、`fds_final == base_fds`（`0` FD 洩漏）、`children == []`、`idle_timeout 0.3s` 觸發時立即重啟不撞鎖且舊實例不誤刪新 `ready`/`m.sock`、外部刪 `m.sock` 自癒退出、`ctl` 4 執行緒防驚群、`env -i` 剝除 7 變數不崩潰、`ctl disable`／`enable` 與 4 工具 fallback 100% 一致、fallback `SIGTERM < 0.8s`。

### 2.2 跨界隔離實機驗收與六大客戶端矩陣

| 客戶端 | 安裝路徑與實測版本 | 分類結論 | 實測證據與邊界說明 |
|---|---|---|---|
| **Hermes Agent** | `/root/.local/bin/hermes` (`v0.23.4`, `mcp 2.0.0`) | **`PASS`** | 隔離 `HERMES_HOME` 下以 `--no-fallback` 直連原生 Daemon（`pid=12927`, `tracer_pid=0`）通過 `hermes mcp test`；`mcp 2.0.0` 4 路並行 `ClientSession`（`--no-fallback`）同回 `ab18e49ad288`（`11.8 ms`）、47 檔掃描（`6.22 ms`）、3 命中搜尋（`19.18 ms`）、500 行 JSONL（`5.2 ms`），且並行觸發 `-32001` 與 `-32602` 互不影響；`ctl disable` 後退回 PRoot 測試仍通過（`1690ms`, 4 工具）。 |
| **Claude Code** | `/root/.config/Claude/claude-code/2.1.330/fd32a5b15526/claude` (`2.1.330`) | **`PASS`** | 隔離 `CLAUDE_CONFIG_DIR` 下 `claude mcp add --no-fallback` ＋ `claude mcp get hybrid2` 主動健康檢查實機 **`✔ Connected`**（走原生 `conn_id=3`）；`ctl disable` 停機並切回標準中繼參數後再次 `claude mcp get` 通過 PRoot 回退。 |
| **Codex CLI** | `/usr/lib/chatgpt/resources/codex` (`codex-cli 0.171.0-alpha.13.2`) | **`PARTIAL`（離線設定 `PASS`／握手 `UNKNOWN`）** | 隔離 `CODEX_HOME` 下 `codex mcp add`、`codex mcp list`、`codex mcp get --json` 全部通過；`codex mcp` 無免登入／免 API 之離線握手測試子指令，故實際 MCP 握手誠實標記為 **`UNKNOWN`**。 |
| **Claude Desktop** | `/usr/bin/claude-desktop` (`dpkg 6.28899.6` arm64) | **`UNVERIFIED_LIVE_GUI`** | 驗證 `ctl client-config` JSON schema 與 `env -i` 剝除環境探針；未改動 `/root/.config/Claude/claude_desktop_config.json` 與 Stable `:1`，未執行實機 GUI 啟動。 |
| **Antigravity (AGY)** | `/opt/antigravity-hub/antigravity` (`44.9.1`) | **`UNVERIFIED_LIVE_GUI`** | 驗證 `ctl client-config` JSON schema 與 `env -i` 剝除環境探針；未改動 `~/.gemini/config/`，未執行實機 GUI 重啟測試。 |
| **OpenCode** | 未安裝 | **`NOT_INSTALLED`** | 全根目錄掃描無執行檔，未納入本機實機 PASS 條件。 |

另於同輪實測驗證：`ctl enable` → `ctl start --idle-timeout 2`（`pid=16050`）→ probe 成功 → 閒置 `2s` 後自動停機（`audit.jsonl` 記 `"reason": "idle-timeout"`、`running: false`、socket/pidfile/ready 零殘留）。

---

## 三、既有工作站基線未受影響證明

- `out8/` SHA256 核對 `baselines/fast9-09c-20261127/sha256sums.txt`：**5/5 `OK`**。
- `src/f8-proot-fast` 與 `src/f8-proot-fast-stage5`：`git status --short` 皆為 **`0`**。
- `/root/.codex/config.toml`、`/root/.config/Claude/claude_desktop_config.json`、`/root/.hermes/config.yaml` 時間戳維持原樣未更動。
- Stable `:1`（`com.termux.x11 :1 -legacy-drawing`、`X1`）維持運行未受影響，暫存目錄與程序零殘留。
