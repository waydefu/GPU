# Stage 7.3 — 受控工作站 A/B 對照基準報告（2026-11-27）

- **狀態**：**`STAGE7_3_CONDITIONAL_GO`（I/O、目錄掃描、文字搜尋與唯讀 Git 全面通過 `sign_p < 0.05` 且結果 100% 一致，准予按分流邊界推進 Stage 7.4；純 CPU JSON 解析與高並發共用單一 GIL 情境實測為負收益，誠實標記 `NO-NET-GAIN / KEEP-LOCAL`）**
- **執行方式**：由 Termux 原生端（`termux-bg-run`，`TracerPid == 0`，`Uid: 10365`）直接執行 [`scripts/stage7_3_bench.py`](../../../scripts/stage7_3_bench.py)，固定配對 `out8/bin/proot-fast8`（不經 `auto/proot-fast8` 避免 sharding 幹擾）。
- **原始證據**：[`stage7-3-runs-20261127/stage7-3-abba.public.json`](stage7-3-runs-20261127/stage7-3-abba.public.json)（對應未去敏本機原檔 `stage7-3-abba.json` SHA-256 `83fa3ce044b71eefbf5a4620102e3015dfcb76aeb19700606a1f1f647907d4e2`）。
- **版本標註與前置修補**：PRoot 端為 `Python 3.12.3` + `git 2.43.0`，原生端為 `Python 3.14.6` + `git 2.55.0`。實測開跑前發現 `git_ro grep` 因 `GIT_NOEXT_SUBS` 強加 `--no-ext-diff` 雙端報 `rc=129`（已拆分為 `GIT_NOEXT_DIFF_SUBS` 與 `GIT_NOTEXTCONV_SUBS` 並補回歸測試）；`git log --stat` 跨版本因 rename 偵測預設差異需顯式 `--no-renames` 才達逐字一致。

---

## 一、單路分層 ABBA 實測結果（`n = 10` 對／項，真實 `content[0]["text"]` SHA-256 100% 一致）

對照組 **Arm A1（`PRoot_Resident_MCP`）**：PRoot 內常駐 `f8_hybrid2_relay.py`（`F8_NO_HYBRID=1`）；實驗組 **Arm B（`Native_Hybrid2`）**：Termux 原生常駐 `f8_hybrid2_daemon.py`（`TracerPid == 0`）＋ PRoot 內薄中繼（`--no-fallback`）。每輪皆先執行未計時 warmup，再行 `5` 循環 ABBA（`10` 對）。

### 1.1 Layer A — 短命令／小呼叫（每 run 連續 30 calls，檢驗 `>= 1.00×` 不退化）

| 工作負載 ID | 類別 | `A1` 中位 (`p95`) ms | `B` 中位 (`p95`) ms | 中位倍率 | 勝場 (`sign_p`) | Tracer CPU (`A1→B`) ms | 峰值總 PSS (`A1→B`) MB |
|---|---|---:|---:|---:|---|---:|---:|
| `A_tree_scan_small` | `io_syscall` | 556.21 (579.40) | **130.24** (165.66) | **`4.271×`** | 10/10 (`0.0020`) | `323.2 → 0.00` | `13.2 → 32.2` |
| `A_text_search_small` | `io_syscall` | 608.05 (621.96) | **248.10** (363.51) | **`2.451×`** | 10/10 (`0.0020`) | `324.5 → 0.00` | `13.5 → 32.2` |
| `A_git_status_short` | `git_subproc` | 659.88 (675.37) | **318.37** (358.39) | **`2.073×`** | 10/10 (`0.0020`) | `424.7 → 0.00` | `16.1 → 32.6` |
| `A_git_rev_parse` | `git_subproc` | 349.56 (459.41) | **249.29** (264.80) | **`1.402×`** | 10/10 (`0.0020`) | `193.6 → 0.00` | `15.1 → 33.4` |
| `A_json_summary_small` | `python_cpu` | 104.31 (147.89) | **101.75** (148.62) | **`1.025×`** | 9/10 (`0.0215`) | `31.3 → 0.00` | `13.3 → 32.2` |

> 全數 5 項短呼叫皆通過 `>= 1.00×` 不退化門檻；即便加上 PRoot ↔ UDS 來回，30 次 `tree_scan_small` 仍快 **`4.27×`**，最小 JSONL 呼叫（`~3.4 ms`/次）亦完全打平且省下 `31.3 ms` PRoot tracer CPU。

### 1.2 Layer B — 目標重型與混合 AI 工作負載（`n = 10` 對／項）

| 工作負載 ID | 類別 | `A1` 中位 (`p95`) ms | `B` 中位 (`p95`) ms | 中位倍率 | 勝場 (`sign_p`) | Tracer CPU (`A1→B`) ms | 峰值總 PSS (`A1→B`: `pr+dm`) MB |
|---|---|---:|---:|---:|---|---:|---|
| `B_tree_scan_cpp` (4,469 檔 / 51.35 MiB) | `io_syscall` | 1876.79 (1916.77) | **327.07** (338.37) | **`5.738×`** | **10/10 (`0.0020`)** | `1213.7 → 0.13` (**`-99.99%`**) | `16.9 → 41.4` (`13.6+27.9`) |
| `B_git_grep` (`seccomp`, 310 hits) | `git_subproc` | 54.25 (59.41) | **14.23** (15.56) | **`3.814×`** | **10/10 (`0.0020`)** | `45.9 → 0.00` | `18.8 → 35.8` (`13.9+22.0`) |
| `B_mixed_ai_turn` (6 步真實序列) | `mixed_turn` | 3760.51 (3811.97) | **1370.87** (1411.10) | **`2.743×`** | **10/10 (`0.0020`)** | `2155.2 → 0.09` (**`-99.99%`**) | `37.1 → 75.9` (`14.3+62.2`) |
| `B_text_search_fixed` (2,280 `.c/.h`) | `io_syscall` | 1494.83 (1528.83) | **592.62** (599.76) | **`2.522×`** | **10/10 (`0.0020`)** | `862.2 → 0.00` | `16.9 → 39.3` (`13.5+25.8`) |
| `B_git_log_stat` (`-n 500 --no-renames`) | `git_subproc` | 399.09 (408.61) | **199.58** (202.11) | **`2.000×`** | **10/10 (`0.0020`)** | `157.1 → 0.19` | `36.5 → 67.2` (`13.8+53.8`) |
| `B_text_search_regex_worker` (`--regex-worker`) | `io+subproc` | 1598.60 (1623.46) | **836.59** (858.42) | **`1.911×`** | **10/10 (`0.0020`)** | `885.5 → 0.00` | `29.7 → 55.0` (`13.5+41.4`) |
| `B_git_blame` (`InitOutput.c`, 17k lines) | `git_subproc` | 109.57 (113.25) | **87.89** (90.18) | **`1.247×`** | **10/10 (`0.0020`)** | `20.5 → 0.06` | `22.0 → 60.5` (`14.1+47.0`) |
| `B_git_ls_files` (374 tracked) | `git_subproc` | 11.46 (17.12) | **9.91** (14.87) | **`1.156×`** | **10/10 (`0.0020`)** | `5.9 → 0.00` | `14.8 → 47.2` (`13.9+33.3`) |
| `B_json_summary_real_doc` (9.44 MiB JSON) | `python_cpu` | **150.80** (156.39) | 225.29 (235.23) | **`0.669×`** | 0/10 (`0.0020` 負) | `1.1 → 0.00` | `54.8 → 78.2` (`13.9+64.3`) |
| `B_json_summary_synth_50k` (50k 行 JSONL) | `python_cpu` | **207.95** (213.25) | 308.99 (323.17) | **`0.673×`** | 0/10 (`0.0020` 負) | `0.9 → 0.00` | `21.6 → 59.0` (`13.9+45.1`) |

- 全數 15 項工作負載之行程級 `tracer_proc_majflt` 與 `daemon_proc_majflt` 皆為 **`0/0`**；全場系統 `MemAvailable` 穩定於 `3,252.8–3,400.3 MB`、`hw-trip` 過濾後 CPU 實測溫度 `52.9–81.8 °C`；`daemon_fd_delta = 0`（`6 → 6`）、`daemon_exit_rc = 0`、結束後零殘留行程。
- `adb -P 5038` `/proc/vmstat` `pgmajfault` 因包含 Android 背景系統活動出現偶發尖峰（`4` 至 `8,627`），而行程自身 `majflt` 全程為 `0`。

---

## 二、Arm A2、4 路並發與 `--auto-start` 冷啟動實驗

1. **Arm A2（PRoot 逐次啟動 `MCPToolEngine` / CLI，`n = 5`）拆解「常駐化 vs 去 `ptrace`」**：
   - `A2_tree_scan_cpp_oneshot`：`1770.65 ms` vs `A1` `1876.79 ms` vs `B` `327.07 ms`（**`5.74×` 加速幾乎全來自脫離 PRoot `ptrace`，而非單純常駐化**）。
   - `A2_git_log_stat_oneshot`：`398.82 ms` vs `A1` `399.09 ms` vs `B` `199.58 ms`（外掛 `git` 本就按請求 `fork+exec`，**`2.00×` 亦純來自原生 `git` 脫離 `ptrace`**）。
   - `A2_json_synth_50k_oneshot`：`338.68 ms` vs `A1` `207.95 ms` vs `B` `308.99 ms`（**純 CPU JSON 任務之加速來自 PRoot Python 3.12 常駐省下冷啟動，而非 Termux Python 3.14**）。
2. **4 客戶端並發重負載吞吐（`4x_PRoot_Fallback` vs `4x_Native_Shared`，`n = 5` ABBA）**：
   - Makespan：`4557.82 ms`（A1，`3.510 ops/s`）vs `7495.55 ms`（B，`2.135 ops/s`），中位倍率 **`0.608×`（`0/5`, `sign_p = 0.0625`）**；PRoot tracer CPU 總和由 `9901.92 ms` 降至 **`1.24 ms`**，合併峰值總 PSS 由 `86.46 MB` 升至 **`139.55 MB`**。
3. **`--auto-start` 冷啟動端到端延遲**：
   - 保留 7 個 Android 變數經 `TermuxService` 拉起並驗 `tracer_pid == 0`（`n = 10`）：中位 **`1125.15 ms`**（`p95 1184.41 ms`, `max 1217.69 ms`, `10/10` 成功）。
   - 剝除 7 個 Android 變數安全退回 PRoot 本地執行（`n = 5`）：中位 **`156.94 ms`**（`p95 196.45 ms`, 零 `rc=4` 崩潰）。

---

## 三、兩項負收益根因實證與 Stage 7.4 分流裁決

1. **`B_json_summary_*` 負收益（`0.67×`）根因已證實**：
   - 在 Arm A1 中 PRoot tracer CPU 僅 `0.9–1.1 ms`（`<1%` 牆鐘時間），幾乎無 `ptrace` 系統呼叫成本可省。
   - 核對 `/data/data/com.termux/files/usr/lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py` 與 PRoot `python3.12`：Termux Python `3.14.6` 為跨編譯且 **關閉 Computed Gotos (`HAVE_COMPUTED_GOTOS = 0`)、無 `--enable-optimizations` PGO、無 LTO、啟用 `--enable-shared` (`libpython3.14.so`) ＋ `WITH_MIMALLOC=1` / Bionic Scudo**；PRoot Ubuntu `3.12.3` 則具 **`HAVE_COMPUTED_GOTOS = 1`、非共享核心可執行檔與 glibc/pymalloc**。
   - 同 PRoot 環境零 I/O 純記憶體基準證實：硬體指令主導的 `sha256` 兩者完全打平（`5.49 ms` vs `5.49 ms`），但 `_json.loads` (`9.44 MiB`) 3.14.6 慢 **+56.7%（`0.638×`）**、50k JSONL 迴圈慢 **+64.4%（`0.608×`）**，與端到端 ABBA `0.669×`／`0.673×` 精確吻合。
2. **`concurrent_4x` 負收益（`0.608×`）根因已證實**：
   - `4x_PRoot_Fallback` 擁有 4 支獨立 PRoot Python 行程（**4 個 GIL 跨多核並行**），而單一 `f8_hybrid2_daemon.py` 僅以執行緒池共享 **1 個 CPython GIL**，當 4 路同時執行持住 GIL 的 `repo_text_search(fixed_string=True)`＋`python_json_summary`＋`repo_tree_scan` 時完全序列化並放大鎖切換開銷（雖節省 `~9.9 s` PRoot CPU 與多核負載，但總牆鐘顯著變長）。
3. **Stage 7.4 試點裁決與強制邊界**：
   - **採納並試點原生分流**：`repo_tree_scan`（**4.27×–5.74×**）、`repo_text_search`（**1.91×–2.52×**）、`git_ro`（**1.16×–3.81×**）與多工具盤點序列（**2.74×**, tracer CPU **-99.99%**），並藉長駐對話攤銷 `~1.13 s` `--auto-start` 冷啟動與 `~19 MB` Daemon 底噪 PSS。
   - **誠實保留 PRoot 本地或不予外推**：大檔純 CPU `python_json_summary` 明確不具備原生加速價值（`0.67×`）；多客戶端重型純 Python 同時壓測場景受限單一 GIL（`0.61×`），於未另行設計並實測多行程 worker pool 前不得宣稱多路高並發吞吐改善。
