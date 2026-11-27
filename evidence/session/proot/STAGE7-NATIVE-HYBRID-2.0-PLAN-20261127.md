# Stage 7 — Native Hybrid 2.0 研究計畫與 7.1 唯讀審計（2026-11-27）

> **文件性質與紅線**：本文件為 Stage 7.1 唯讀盤點與 7.2–7.5 工程計畫（docs-only）。全程未安裝任何套件、未部署任何後端、未修改 Stable `:1`、未更動 `fast9+09c` 基準、未重開 Gate A／主線 #3、未覆寫凍結證據。所有未實測項目皆明確標記為 **`UNKNOWN`**，不得將理論推估視為實機結果。

---

## 一、Stage 7.1 唯讀審計結果

### 1.1 既有橋接實測基準（依勘誤文件）

- **唯一橋接實測基準**：[`ERRATUM-STAGE6-HYBRID-SPEEDUP-20261127.md`](ERRATUM-STAGE6-HYBRID-SPEEDUP-20261127.md) 確認 Step 5 單次重型 `python3` 全樹掃描經 `f8-hybrid-daemon.py` + `f8-hybrid-run` 實測為 **`1.89×`**（`123.7 ms → 65.4 ms`、`-46.9%`、`5/5`；原始檔為手機本機限定 `evidence/session/proot/stage5-step5-20261126/step5-workstation-abba.json`，未推 GitHub）。
- **逐次 CLI 包裝禁用邊界**：Step 2 `evidence/session/proot/stage5-hybrid-20261126/hybrid-bench.json`（手機本機限定，未推 GitHub；結論載於 [`STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md`](STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md)）證實每次呼叫付 `fork+execve`（~6–10 ms）＋ IPC/`Popen`（~4–6 ms），短 CLI（`zstd_jq_5x` `0.47×`、`trivial_jq_50x` `0.62×`、`python_scan_10x` `0.95×`、`git_ops_20x` `1.00×`）皆無淨益。因此 Native Hybrid 2.0 瞄準**消除每呼叫 `Popen` 成本的常駐服務（Unix socket `41.02 µs` p50）**。

### 1.2 本機 `src/f8-proot-fast-stage5/hybrid/` 原型審計

位置：手機本機 `/root/projects/GPU加速/src/f8-proot-fast-stage5/`（分支 `stage5/isolated-fast8-20261126`、HEAD `5541ef7`，未合入 GitHub `main`）。

| 檔案 | 既有實證 | 可直接復用元件 | 需改造／限制 |
|---|---|---|---|
| `hybrid/f8-hybrid-daemon.py`（603 行，23.2 KB） | `test_hybrid_bridge.py` **28/28 PASS**；90s Soak **5,595 ops / 669/669 cancel-kill / 0 洩漏**（本機 `stage5-hybrid-20261126/hybrid-soak.json`，未推 GitHub） | ① `TracerPid == 0` 啟動斷言<br>② `0600` socket / `0700` dir / `107`-byte `AF_UNIX` 檢查 / `flock` pidfile<br>③ `SO_PEERCRED` UID 檢查<br>④ `Policy.map_path`/`map_arg`（`--map` 根目錄限制、`.l2s.*`、`realpath` symlink escape、`PROTECTED` 系統路徑拒絶）<br>⑤ `Policy._git_cfg_scan` 與 `GIT_RO` 唯讀白名單＋清淨環境<br>⑥ ARM64 `_pidfd_open`（syscall 434）+ `select.poll()` 監管與 `killpg` 清理<br>⑦ 無引數外洩 JSONL 稽核日誌 | 原協議為 `F8H1` + `SCM_RIGHTS` + 每請求 `Popen`，不具備 MCP JSON-RPC 2.0 狀態機與長駐 in-process worker；`TOOLS` 含 `rg`/`fd`/`jq`/`zstd`，但本機 Termux 原生缺裝該 4 項。 |
| `hybrid/f8-hybrid-run.c`（222 行，7.1 KB） | 含 `F8_NO_HYBRID=1`／路徑保護／連線失敗自動 `execvp()` 回退 | Fallback 設計原則與 protected-path 清單可作參照 | 若 Hermes 改以 MCP 接線，主路徑不需 C wrapper（可選保留或替換為輕量 stdio-UDS proxy）。 |
| `tests/test_hybrid_bridge.py`、`bench_hybrid.py`、`soak_hybrid.py` | 28/28 單元＋安全 fuzz＋90s 壓測骨架 | 安全測試向量（`.l2s.*`、symlink escape、git config `textconv`/`hookspath`、3,000 次 parser fuzz、cancel-kill、0 殘留）可遷移至 7.5 驗收 | `bench_hybrid.py` 測的是逐次 `Popen`，7.3 須改測長駐 MCP 請求與端到端任務。 |

### 1.3 Termux 原生端二進位盤點（2026-11-27 實測）

檢查目錄：`/data/data/com.termux/files/usr/bin/`

| 工具 | 狀態 | 實測版本／備註 |
|---|---|---|
| `python3` | **已安裝** | `Python 3.14.6`（含標準庫 `sqlite3 3.53.4`、`json`、`asyncio`、`hashlib`、`re`、`pathlib`；`pip list` 僅 `ifaddr`, `pip`, `proot-distro`, `zeroconf`） |
| `git` | **已安裝** | `git version 2.55.0` |
| `rg`（`ripgrep`） | **MISSING** | 無原生執行檔；若不裝套件，須以原生 Python 實作唯讀搜尋或標註限制 |
| `node` | **MISSING** | 無原生執行檔；Node-based MCP 伺服器（如 `firebase`）目前**無法**於原生端直接執行 |
| `fd` / `jq` / `zstd` / `duckdb` / `sqlite3` CLI | **MISSING** | `/data/data/com.termux/files/usr/bin/` 無對應執行檔 |

### 1.4 Hermes `v0.23.4` MCP 接線與生命週期盤點（唯讀）

檢查對象：`/usr/local/lib/hermes-agent/`（`Hermes Agent v0.23.4 (2026.9.24)`、`local 8fc037444731`）

- **SDK 與傳輸**：`/usr/local/lib/hermes-agent/venv` 內建 **`mcp 2.0.0`** 與 **`httpx 0.28.1`**（`mcp.client.streamable_http` 可匯入）；`hermes mcp` 子指令支援 `add/remove/list/test/configure`；目前設定有 `firebase` 與 `serena`（皆於 PRoot 內以 `stdio` 啟動）。
- **兩種可行接線路徑比較**：
  1. **選項 A（最推薦）— `stdio` 輕量代理 ↔ `AF_UNIX` socket（`0600` + `SO_PEERCRED`）↔ 原生常駐後端**：
     - 機制：Hermes 依既定 `_run_stdio`（`tools/mcp_tool_transport.py:375`）啟動一支駐留 PRoot 的極薄 stdio-to-UDS 中繼（不自行開重型工作），把 JSON-RPC 轉入 `/tmp/.f8-hybrid/mcp2.sock` 連向 `TermuxService` 預先拉起之原生（`TracerPid=0`）長駐後端。
     - 優勢：不開任何 `127.0.0.1` TCP port、復用 `SO_PEERCRED` UID 認證與 `0600` 權限、直接吃進 Hermes 既有的 `_StderrTee`、`_stdio_pgids` 孤兒回收與 `hermes mcp test`。
  2. **選項 B — `Streamable HTTP`（`http://127.0.0.1:<port>/mcp`）↔ 原生常駐後端**：
     - 機制：利用 `_run_http`（`tools/mcp_tool_transport.py:613`），且 `_mcp_proxy_mounts` 已明確繞過 loopback proxy（`is_loopback_host`）。
     - 限制：`mcp_tool_transport.py` 無 `http+unix://` URL scheme，必須開 `127.0.0.1` TCP port 並自行維護 random bearer token 與 session TTL／keepalive。
- **原生啟動**：已證實可用 `/usr/local/bin/termux-bg-run` / `am startservice --user 0 ... TermuxService` 以 `TracerPid=0` 啟動並由 7 個 Android 環境變數守衛保護。

---

## 二、明確標記為 `UNKNOWN` 之未實測項目

1. **`UNKNOWN`**：Termux 原生 Python `3.14.6` 在**不安裝外部 `mcp` 套件（純 Python stdlib JSON-RPC 2.0 over stdio/UDS）**下，與 Hermes `v0.23.4`（`mcp 2.0.0` client）完整 `initialize` → `tools/list` → `tools/call` → `notifications/cancelled` 協議相容性。
2. **`UNKNOWN`**：PRoot 內薄 stdio-to-UDS 中繼在 Hermes 取消單一工具呼叫、或 Hermes session 關閉／重連時，如何在不殺死共用原生常駐後端（若採單實例共享）的前提下正確中止該次進行中請求（特別是長駐 Python worker 內的中斷與子程序 `killpg`）。
3. **`UNKNOWN`**：實際多輪 AI 工作負載（如 Hermes 呼叫索引／搜尋／唯讀 Git）經由常駐原生 MCP 後端後的端到端牆鐘、Tracer CPU、PSS 與工具呼叫延遲實測改善幅度（不得預先套用理論值）。
4. **`UNKNOWN`**：原生常駐後端在 Android HyperOS 背景閒置／Doze／LMKD 下（無 `termux-wake-lock` 或僅在前景桌面伴隨運行）之存活率與斷線重連穩定度。
5. **`UNKNOWN`**：現有 PRoot 內 `serena`（Python LSP MCP）若嘗試原生化，其 `uv`／輪子與 C 擴充套件是否能於 Termux Bionic arm64 編譯或運行（7.1 未安裝測試）。

---

## 三、Stage 7.2–7.5 工程計畫、驗收門檻、安全邊界與回退方案

### 3.1 分階段執行路徑與量化驗收門檻

| 階段 | 範圍與產物 | 必須滿足之量化 PASS 門檻（任一不達標即停在該階段） |
|---|---|---|
| **7.2 隔離橋接原型** | 復用 `f8-hybrid-daemon.py` `Policy` 模組，於獨立目錄 `~/build/proot-fast/tools/hybrid2/` 建置純 stdlib 原生常駐 JSON-RPC 2.0 MCP server（僅唯讀工具：`repo_tree_scan`、`repo_text_search`、`git_ro`、`python_json_summary`）＋ PRoot stdio-UDS 薄中繼；以 `termux-bg-run` 啟動 `TracerPid=0`。 | ① **Daemon 啟動確認**：由 `termux-bg-run`/`TermuxService` 拉起並驗證 `TracerPid == 0`、`0600` socket、`flock` pidfile 單實例與 readiness probe 通過，且不觸碰 `out8/`/`shard2/`；<br>② **單請求取消（`notifications/cancelled`）**：進行中請求被取消時僅中止該請求與其子程序，不影響共用常駐 daemon 與後續請求；<br>③ **逾時（timeout）**：單請求逾時後正確回收子程序並回報逾時錯誤，daemon 保持健康；<br>④ **斷線清理**：stdio-UDS 中繼斷線（`EOF`/`SIGKILL`）時原生側進行中工作乾淨收尾、`children_final = 0`、`orphan_pids = 0` 且無 FD 洩漏；<br>⑤ **回退開關**：`F8_NO_HYBRID=1`、停止 daemon 或移除測試設定條目後可退回 PRoot `fast9+09c` 路徑且零殘留；<br>⑥ **安全與協議驗收**：通過自 `test_hybrid_bridge.py` 移植之安全/fuzz 單元測試（`.l2s.*`、symlink escape、git config 注入、`SO_PEERCRED`、`0600` 權限、3,000 次 fuzz）及獨立測試 `HERMES_HOME` 下 `hermes mcp test` 握手、`tools/list`、`tools/call`。 |
| **7.3 真實工作站 A/B 對照** | 以受控 ABBA（至少 6 對＋warmup，原生計時器、`fast9+09c` 現況 vs `Native Hybrid 2.0` MCP）比較：`git_ro` 大倉盤點、跨樹搜尋／雜湊索引、JSONL 聚合。 | ① 結果與 PRoot 客體逐字／雜湊 **100% 一致**；<br>② 重型單次工具呼叫與多工具序列展現可重現加速（目標 `sign_p < 0.05` 且無退化至 `< 1.00×` 之項目）；<br>③ 記錄並比較 `wall_ms`、`p50`/`p95` 工具呼叫延遲、`tracer_cpu_ms`、`peak_pss_mb`、`pgmajfault`（ADB `-P 5038`）、`orphan_pids = 0`。 |
| **7.4 單一 Agent 唯讀試點** | 僅以獨立測試 `HERMES_HOME`（不碰日常設定與 Antigravity／Claude）接上唯讀 MCP 工具，跑真實多輪唯讀程式碼庫盤點任務對照。 | ① 全程不觸發權限越界或 PRoot rootfs 寫入；<br>② 端到端任務無超時／協議卡死，記錄實際節省比例（若不顯著則誠實收斂為 `PAUSE`）。 |
| **7.5 穩定性與異常驗收** | 壓測（≥ 1,000 ops、並發請求、斷線注入、逾時注入、強制取消、重複啟停）＋ 記憶體壓力檢查。 | ① `cancel`／斷線後進行中子工作須全部終止、`children_final = 0`、`orphan_pids = 0`；<br>② 常駐後端 RSS 漂移 ≤ 10% 且無 FD 洩漏（`fds_final == fds_baseline`）；<br>③ 停機後零殘留（socket/pidfile/proc 全清）；<br>④ 關閉原生後端時，測試設定切換回客體工具／`F8_NO_HYBRID=1` 須實測退回成功。 |

### 3.2 安全邊界（誠實模型，實作時強制寫入程式並於 7.2 驗證）

- **同一 Android UID 邊界聲明**：PRoot 與 Termux 原生端屬同一 UID，本設計**不宣稱跨越 OS 隔離邊界**，控制重點在於**防誤操作、防命令注入、防破壞 PRoot `.l2s.*` 硬連結與 Ubuntu rootfs**。
- **嚴禁任意 Shell 入口**：無 `bash -c`／`sh -c` 工具、所有子程序一律 `shell=False`；初期試點**僅開放唯讀工具**（沿用 `GIT_RO` 與 `_git_cfg_scan`、`--map` 根目錄白名單、`PROTECTED` 系統目錄拒絶、`.l2s.*` 與 symlink escape 拒絶）。
- **傳輸與日誌**：優先採 `0600` `AF_UNIX` + `SO_PEERCRED` UID 檢查（零 TCP port 暴露）；稽核日誌僅記工具名、決策與耗時，不記錄檔案內容、憑證或私網端點。

### 3.3 回退方案（隔離設計，須經 7.2／7.5 實測驗證）

1. **完全隔離開發**：7.2–7.5 全程僅寫入獨立工作目錄與獨立測試 `HERMES_HOME`；設計目標為不觸碰 `out8/`、`shard2/`、`f8desk*`、`/usr/local/bin/f8-shard`、Stable `:1` 或日常 `~/.hermes/` 設定。
2. **關閉與還原路徑**：停止原生 daemon 並移除測試設定中的 `mcp_servers` 條目（或設 `F8_NO_HYBRID=1`），預期可退回既定 `fast9+09c` 行為；實際無殘留與無影響須由 7.2 與 7.5 實測驗證通過，不可預先視為已保證。
