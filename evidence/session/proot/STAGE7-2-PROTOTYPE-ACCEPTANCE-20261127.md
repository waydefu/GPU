# Stage 7.2 — 通用多客戶端 Native Hybrid 2.0 隔離原型驗收報告（2026-11-27）

- **狀態**：**`STAGE7_2_PASS`（達標通用化 Stage 7.2，停在 7.2 邊界等待 PR 審閱後再決定是否啟動 7.3）**
- **依據文件**：[`STAGE7-2-MULTI-CLIENT-REVISION-20261127.md`](STAGE7-2-MULTI-CLIENT-REVISION-20261127.md)（取代原 [`STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md`](STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md) `§1.4`／`§3.1–3.3`）
- **角色協作**：Hydrogen（核心架構、MCP 協議、安全邊界、生命週期與裁決）× Neon（三輪獨立審查：架構／程式碼與覆蓋率／PR #51 修補後負面安全與生命週期復驗，全數 Blocker/High/Medium/Low 缺口均已修復並經 **`PASS`** 複檢）
- **紅線遵循**：純 Python stdlib（零額外套件安裝）、未修改 `out8/`／`shard2/`／`f8desk*`／`/usr/local/bin/f8-shard`／Stable `:1`／`src/f8-proot-fast*`／任何現役 AI 客戶端設定（`/root/.hermes/`、`/root/.codex/`、`/root/.config/Claude/`、`/root/.gemini/`）。

---

## 一、通用架構與交付模組

| 檔案（`scripts/` ＆ 隔離目錄 `tools/hybrid2/`） | 核心能力與修訂項目 |
|---|---|
| `f8_hybrid2_policy.py` | 預設 runtime 遷至 `TERMUX_HOME/.f8hyb2/`（`47` bytes，免疫 TermuxService 清空 `$PREFIX/tmp`）；`map_path` 對 `//` 正規化並對 `real_host` 反查 `PROTECTED`；`open_nofollow` 加 `O_NONBLOCK` 免疫 FIFO；`validate_git_ro` 改採各 Git 子命令嚴格允許清單 `GIT_SUBCMD_SPECS`（20 個子命令拆 `flags_no_val` / `flags_eq_only` / `flags_val_req` / `flags_int_attached` / `flags_path_val` 與 `pos_mode`），全面禁止 `branch`/`tag`/`symbolic-ref` 寫入、阻擋 `OPTARG` `=`-only 旗標注入與 `-` 開頭偽旗標、關閉 `cat-file --batch-check` 與 `for-each-ref --shell/--perl/--python/--tcl`、`_map_git_arg` 檢查裸 symlink 與含 symlink 前綴未落盤路徑，補 `--no-textconv`、`GIT_OPTIONAL_LOCKS=0`、`GIT_CEILING_DIRECTORIES`；`git_cfg_scan` 掃描同行 `[core] fsmonitor`、`.git/config.worktree`、`512 KiB` 上限與目錄型 `.git` realpath。 |
| `f8_hybrid2_tools.py` | 強制 MCP `initialize` 狀態機（`-32002`）、嚴格 `canonical_req_key`（區分 `int`/`str`、拒絕 `bool`）、`RequestContext.cancel()` 與 `attach_wake_fd()` 全程持鎖防 FD 重用寫錯連線；共享 `_run_supervised_popen()`（`pidfd_open` + wakeup pipe + `select.poll()` + `except BaseException:` `killpg` 保護），`_tool_text_search` 對含 `[*+?{|]` 具回溯風險正則以隔離子程序 `--regex-worker` 執行並於輸出端 `_fit_json_payload(..., MAX_TEXT_BYTES)` 預先裁切（防 `> 2 MiB` stdout 截斷噴 `JSONDecodeError`），取消／逾時確定 `SIGKILL` 整組進程回 `-32001`；`_strict_int_arg` 拒絕 `null`/非整數、`.jsonl` 設 `1 MiB` 單行與 `32 MiB` 總量防線。 |
| `f8_hybrid2_daemon.py` | 原生單例 Daemon（強制 `TracerPid == 0` 且拒於 `disabled.flag` 下啟動）：`flock` pidfile → `bind(0600)` + `listen(64)` → 原子 `.ready`（含 `_ready_ino`）；支援 `--max-clients`／`--max-inflight` 背壓（`-32000`）、拒絕重複活躍 `req_id`（`-32600`）、每 5 秒 `sock_ino`/`pid_ino` 防分裂檢查、`5 MiB` 稽核日誌輪替；無競態 `idle-timeout` 先原子刪 `sock`/`ready` → 排空 `accept()` backlog → 立即釋放 `d.pid` 供新實例無縫重啟，且 drain 期間收到 `SIGTERM`/`SIGINT` 會強制 `cancel_all()` 與 `join_workers`。 |
| `f8_hybrid2_relay.py` | 客戶端中立 stdio-to-UDS 中繼：尊重 `disabled.flag` 與 `F8_NO_HYBRID=1`；PRoot 下遇客戶端剝除 7 Android 變數時安全退回 PRoot 引擎而不 `rc=4` 崩潰；`sent_to_uds` 上限提升至 `MAX_FRAME_BYTES`（`4 MiB`），`bridge_stdio_to_uds` `finally` 還原 `SIGTERM`/`SIGINT` 處理器；fallback worker 補齊異常保護（`-32603`）、`4 MiB` 幀上限與 `< 0.8s` `SIGTERM` 喚醒。 |
| `f8_hybrid2_ctl.py` | 統一啟停控制器（`start/stop/restart/status/probe/enable/disable/ensure-running/client-config`），全寫入路徑共享 `ctl.lock` 防驚群，`stop` 先核對 `pidfile` 與 `/proc/<pid>/cmdline` 再送 `SIGTERM`；`client-config` 全面補齊 `--auto-start`；`disable` 與 `restart` 於舊 daemon 停機逾時確定回傳 `rc=1` / `ok=false`。 |
| `test_f8_hybrid2.py` | 11 項完整單元、安全、ReDoS 逾時、多客戶端並發、斷線重連真實行為與控制器測試（PRoot 與 Termux 原生皆為 **11/11**）。 |

---

## 二、實測驗收結果（全部於最終修補版本後重跑驗證）

### 2.1 單元、安全與生命週期測試（`test_f8_hybrid2.py`）

| 環境 | 指令 | `TracerPid` | 結果 |
|---|---|---:|---|
| PRoot Ubuntu | `python3 scripts/test_f8_hybrid2.py` | `!= 0` | **11/11 PASS**（`17.494s`） |
| Termux 原生（`termux-bg-run`） | `F8_HYBRID2_NATIVE=1` + `run-native-tests.sh` | **`0`**（`Uid: 10365`） | **11/11 PASS**（`12.928s`，`rc=0`） |

涵蓋並通過項目：
- 安全邊界：`protected-path`（含 `//etc/passwd`、mapped 父目錄內受保護子目錄、`.f8hyb2`、`out8/`）、`symlink-escape`（含裸 symlink `status -- escape` 與前綴 `log -- escape/missing`）、`.l2s.*`、FIFO `O_NONBLOCK` 不阻塞；嚴格 Git 子命令允許清單攔截 `branch evil`／`branch --abbrev evil`／`branch -f`／`tag evil`／`symbolic-ref HEAD refs/heads/evil`／`diff --no-index`／`diff -U --output=...`／`log --pretty --output=...`／`blame -M --contents=...`／`grep -f/etc/passwd`；`GIT_CEILING_DIRECTORIES`、單行 `[core] fsmonitor = true`、`.git/config.worktree`、`filter.process`、`diff.command`、`512 KiB` config 上限、`.gitfile`／`commondir` 絕對路徑。
- 協議、ReDoS 與資源邊界：未 `initialize` 回 `-32002`、`bool` id 回 `-32600`、重複活躍 `req_id` 回 `-32600`、`max_entries: null` 於 native 與 fallback 皆回 `-32602`、`entries`/`stdout`/`stderr` UTF-8 截斷、`.jsonl` 單行 `> 1 MiB` 拒絕、`> 2 MiB` 搜尋標記 `skipped_oversize`、`(a+)+b` 病態正則於隔離 `--regex-worker` `0.15s` 逾時回 `-32001`（`children == []`）且 `6,000` 行匹配正確裁切、3,000 次 fuzz。
- 多客戶端、按需啟動與停用/啟用真實行為：`--max-clients 4` 第 5 連線 `-32000`、`--max-inflight 1` 確定命中 `-32000`、4 客戶端並發查詢與單客戶端取消／逾時不干擾他人、`fds_final == base_fds`（`0` FD 洩漏）、`children == []`、`idle_timeout 0.3s` 觸發時立即重啟不撞鎖；外部刪 `m.sock` 自癒退出、`ctl` 4 執行緒防驚群、`env -i` 剝除 7 變數安全退回；`SIG_IGN` 停機逾時驗證 `ctl disable` 確定回 `rc=1`／`ok=false`；已連線 UDS 會話（C1）於 `ctl disable` 後收到 `EOF` 斷線結束（非透明熱切換），新連線進入 PRoot 回退（C2），後續 `ctl enable` + `ensure-running` 後既有 C2 仍留在 PRoot 回退而僅新連線（C3）連入原生 Daemon；PRoot 下帶 7 變數實測 `relay --auto-start --no-fallback` 成功按需拉起原生 Daemon（`pid=6494`, `TracerPid=0`）。

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
