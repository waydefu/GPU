# Stage 7.2 — Native Hybrid 2.0 隔離橋接原型驗收報告（2026-11-27）

- **狀態**：**`STAGE7_2_PASS`（停在 7.2 邊界，未啟動 7.3 效能對照）**
- **依據計畫**：[`STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md`](STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md) §3.1 Stage 7.2 六項必要門檻
- **紅線遵循**：全程純 Python stdlib（無額外 `apt`/`pkg`/`pip` 安裝）、未修改 `out8/`／`shard2/`／`f8desk*`／`/usr/local/bin/f8-shard`／Stable `:1`／`src/f8-proot-fast*`／日常 `/root/.hermes/config.yaml`；部署僅限隔離目錄 `/data/data/com.termux/files/home/build/proot-fast/tools/hybrid2/`。

---

## 一、交付模組與架構

復用 `src/f8-proot-fast-stage5/hybrid/f8-hybrid-daemon.py` 的路徑／Git／環境／Socket 安全設計，重構並實作 4 個純標準庫模組與 1 套單元／生命週期測試：

| 檔案（`scripts/` ＆ 隔離部署目錄 `tools/hybrid2/`） | 職責 |
|---|---|
| `f8_hybrid2_policy.py` | 復用並強制 `PROTECTED`、`.l2s.*`、`--map` 前綴限制、`realpath` symlink escape 檢查、`GIT_RO` 唯讀白名單、`GIT_BAD_CFG` 與 `.gitfile` 檢查、清淨環境（`PYTHONNOUSERSITE=1`、`GIT_CONFIG_GLOBAL=/dev/null`、清除 `LD_PRELOAD`/`GH_TOKEN` 等）、`107`-byte `AF_UNIX` 檢查、`SO_PEERCRED` UID 認證、ARM64 `pidfd_open`（syscall `434`）。 |
| `f8_hybrid2_tools.py` | 無狀態 MCP JSON-RPC 2.0 工具引擎（支援 `initialize`、`notifications/initialized`、`ping`、`tools/list`、`tools/call`），僅開放 4 項唯讀工具：`repo_tree_scan`、`repo_text_search`、`git_ro`、`python_json_summary`；內建 `RequestContext` 以支援協作中斷、deadline 逾時與子程序群組 `os.killpg(..., SIGKILL)`，並以暫存檔取代未排空 `PIPE` 避免死鎖。 |
| `f8_hybrid2_daemon.py` | 原生端（強制 `TracerPid == 0`）常駐 `AF_UNIX` MCP Daemon：`0700` socket 目錄、`0600` socket、`flock` pidfile 單實例、`SO_PEERCRED` 檢查、區分 `SHUT_WR` 與 `POLLHUP`（對等端斷線／`SIGKILL` 立即中止進行中工作並回收子程序）、無引數內容外洩的 JSONL 稽核日誌、`SIGTERM` 零殘留停機。 |
| `f8_hybrid2_relay.py` | PRoot 內薄 stdio-to-UDS 中繼：支援 `--probe` readiness 探針；當 `F8_NO_HYBRID=1` 或無法連線原生 socket 時，自動退回同套純 Python 唯讀引擎於 PRoot 內執行（可用 `--no-fallback` 強制停用回退）。 |
| `test_f8_hybrid2.py` | 8 項單元、安全、3,000 次 JSON-RPC fuzz、逾時、`notifications/cancelled`、`SIGKILL` 斷線清理與雙模式回退測試。 |

---

## 二、Stage 7.2 必驗門檻實測結果

### 2.1 離線與原生單機單元／安全／生命週期測試（`test_f8_hybrid2.py`）

| 執行環境 | 指令／觸發路徑 | `TracerPid` | 結果 |
|---|---|---:|---|
| PRoot Ubuntu（開發機內測試） | `python3 scripts/test_f8_hybrid2.py` | `!= 0`（使用 `--skip-tracer-check`） | **8/8 PASS**（`8.258s`） |
| Termux 原生（`termux-bg-run`） | `F8_HYBRID2_NATIVE=1` + `run-native-tests.sh` | **`0`**（`Uid: 10365`，不跳過檢查） | **8/8 PASS**（`3.692s`，`TERMUX_BG_RUN_DONE rc=0`） |

涵蓋驗證項目：
- **安全向量（`PolicyAndSecurityTests`）**：`protected-path`（含 `/etc`、`/usr/lib`、`/root/.hermes`、`out8/`）、`path-outside-map`、`l2s-path`、`symlink-escape`、`git` 唯讀白名單與寫入／危險旗標拒絶（`commit`/`push`/`branch -D`/`-c`/`--ext-diff`/`--output`/`--upload-pack`）、`.git/config` 注入與異常 `.gitfile` 拒絶、環境變數清洗、3,000 次畸形 JSON-RPC fuzz。
- **Daemon 硬強化與生命週期（`DaemonLifecycleAndProtocolTests`）**：超長 socket 路徑（`>107` bytes）在 `mkdir` 前即 exit `4`；`flock` 單實例衝突 exit `3`；`0600` socket／`0700` 目錄；`notifications/cancelled` 單請求中止且共用 Daemon 與後續 `ping` 正常；`repo_tree_scan` 與 `git_ro` `timeout_s=0.001` 回報 `-32001` 且 `children_of(daemon) == []`；中繼 `SIGKILL` 斷線後 `children == []` 且 FD 無洩漏；原生與 `F8_NO_HYBRID=1`／Daemon 停機回退輸出 100% 一致；`SIGTERM` 結束後 socket 與 pidfile 零殘留。

### 2.2 跨界端對端實機驗收（PRoot `TracerPid != 0` ↔ `termux-bg-run` 原生 Daemon `TracerPid == 0`）

1. **① Daemon 啟動確認**：
   - `termux-bg-run` 拉起 `live-daemon-session.sh`，實測 `pid=25802`、`tracer_pid=0`、`Uid=10365`、`sock_mode=600`、`fds_base=6`。
   - PRoot 側 `f8_hybrid2_relay.py --socket /tmp/.f8-hyb2-e2e/m.sock --probe` 回傳 `{"ok": true, "detail": "ok"}`。
2. **⑥ 隔離 `HERMES_HOME` 端對端與協議一致性**：
   - 於完全獨立暫存資料根 `HERMES_HOME=/tmp/hermes-hyb2-iso` 設定 `hybrid2`（不觸碰 `/root/.hermes/config.yaml`）：
     - `hermes mcp test hybrid2`：**`✓ Connected (1592ms)`、`✓ Tools discovered: 4`**（`repo_tree_scan`、`repo_text_search`、`git_ro`、`python_json_summary`）。
   - 以 Hermes 內建 `venv` 的 `mcp 2.0.0` `stdio_client` + `ClientSession` 實測跨界工具呼叫與錯誤邊界：
     - `git_ro`（`src/f8-proot-fast` `rev-parse HEAD`）=`ab18e49ad288`（`32.59 ms`），與 PRoot `git` 一致；
     - `repo_tree_scan`（`src/f8-proot-fast`）=`47` 檔、`sha256` `96a999da6c7eebae...`（`13.19 ms`），與 PRoot `os.walk` 雜湊 100% 一致；
     - `repo_text_search`（`scripts/*.py` `verify_peercred`）=`3` 筆命中（`11.88 ms`）；
     - `python_json_summary`（`500` 行測試 JSONL）=`500` 筆（`2.98 ms`）；
     - `timeout_s=0.001` 觸發 `MCPError` `-32001`（`1.25 ms`）；`/etc` 觸發 `MCPError` `-32602` `protected-path`（`0.03 ms`）；錯誤後同連線後續 `git_ro` 仍正常通過（`22.05 ms`）。
   - Daemon JSONL 稽核日誌確認無檔案內容或秘密外洩。
3. **②③④ 跨界斷線清理與停機零殘留**：
   - PRoot 中繼於掃描進行中遭 `SIGKILL` 強制終止後，`--probe` 維持 `ok: true`；原生摘要確認停機前 `fds_pre_stop=6 == fds_base=6`（0 FD 洩漏）、`kids_pre_stop=0`（0 子程序殘留）。
   - `stop.flag` 觸發 `SIGTERM` 後 `stop_rc=0`、`sock_after=0`、`pidfile_after=0`、`proc_after=0`（`TERMUX_BG_RUN_DONE rc=0`）。
4. **⑤ 回退開關**：
   - `F8_NO_HYBRID=1` 經隔離 `HERMES_HOME` 實測 `hermes mcp test hybrid2` 通過（`1380ms`、`4` 工具）。
   - 原生 Daemon 停機後再次執行隔離 `hermes mcp test hybrid2` 通過（`1509ms`、`4` 工具）。
   - `hermes mcp remove hybrid2` 清理設定後 `hermes mcp list` 確認零設定殘留。

---

## 三、既有工作站基線未受影響證明

- `out8/` SHA256 核對 `baselines/fast9-09c-20261127/sha256sums.txt`：**5/5 `OK`**。
- `src/f8-proot-fast` 與 `src/f8-proot-fast-stage5`：`git status --short` 皆為 **`0` 筆變更**。
- `/root/.hermes/config.yaml`：時間戳維持原樣（`Nov 25 21:13`），未改動日常設定。
- Stable `:1`：`termux-x11 com.termux.x11 :1 -legacy-drawing` 與 `/tmp/.X11-unix/X1` 維持運行未觸碰，無任何殘留 `f8_hybrid2` 程序。

> **下一步建議**：Stage 7.2 六項安全與協議驗收均已通過，本階段依約停在 7.2。待審閱並合併本 PR 後，再決定是否推進 Stage 7.3 真實工作站 A/B 對照基準。
