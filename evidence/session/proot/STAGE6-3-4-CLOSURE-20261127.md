# Stage 6.3 & 6.4 — Android 宿主最佳化評估與結案裁決報告（2026-11-27）

> **依據文件**：[`STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md`](STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md)、[`STAGE6-2-POWER-MODE-RESULT-20261127.md`](STAGE6-2-POWER-MODE-RESULT-20261127.md)、[`stage6-audit-20261127/README.md`](stage6-audit-20261127/README.md)。全程維持非 Root、Android 系統設定零寫入（no `settings put` / `device_config put` / `setprop`）、未觸碰 Stable `:1`、未動 ADB `5037` 與已凍結資產。

---

## 一、Stage 6.3：候選 1、2、4 實證與對照實驗

### 1.1 候選 1：同時活躍 Electron／Chromium 上限與操作紀律

**實測證據彙整（6.1、6.2 與 6.3 即時盤點）：**
- **6.1 閒置基線**：`MemTotal = 15,373,988 kB`（`14.66 GiB`），均衡模式閒置 `MemAvailable = 3,223,376 kB`（`3,147.8 MiB`）、ZRAM swap 已用 `9,549,952 kB`（`9.11 GiB` / `56.9%`）。
- **6.2 五個 180 秒高壓區塊**：`MemAvailable` 最低降至 `3,210.6–3,591.5 MB`、ZRAM `swap` 佔用 `7.5–8.6 GiB`、單區塊經 ADB 實測 `pgmajfault` 增量 `+36,706` 至 `+113,593`（`S1`）。
- **6.3 即時 UID 記憶體分布盤點（2026-11-27 11:17 CST，`UID_PROCS = 83`）**：合計 `PSS = 711.9 MB`、`RSS = 1,850.1 MB`、`SwapPss = 1,911.1 MB`。
  - `electron_antigravity`（`n=14`）：**`547.6 MB PSS`（佔總 UID PSS 76.9%）**、`943.7 MB RSS`、`453.0 MB SwapPss`（單一 renderer `255.3 MB PSS`、`language_server` `135.4 MB PSS` + `133.5 MB SwapPss`、軟體 `gpu-process` `74.6 MB PSS`）。
  - `python_agents_mcp`（`n=4`）：`78.9 MB PSS`、`570.3 MB SwapPss`（`hermes` `76.1 MB PSS` + `321.0 MB SwapPss`）。
  - `node_other` + `node_or_claude`（`n=4`）：`1.8 MB PSS`、`459.6 MB SwapPss`（閒置 MCP 伺服器主要由 ZRAM 承載）。
  - `native_other`（`n=10`）：`40.3 MB PSS`、`139.4 MB SwapPss`（`termux-x11` `29.0 MB PSS`、`com.termux` `6.2 MB PSS`、`com.termux.widget` `4.3 MB PSS`）。
  - `traced_desktop_misc`（`n=46`）：`39.0 MB PSS`、`280.3 MB SwapPss`；`proot_tracers`（`n=5`）：`4.3 MB PSS`。

**日常併發操作建議（不硬編碼於程式中）：**
1. 桌面同時維持 **`≤ 2` 個重型 Electron／Chromium 應用**，避免多個 IDE 或瀏覽器常駐分頁同時佔用實體 RAM。
2. 長駐代理、閒置 MCP 與工作分頁用畢即關閉或切換至輕量 CLI；保留 `f8-shard` v2 將重型前端分離至獨立 `proot-fast8` tracer。
3. 依據下節 2B 實測，在記憶體餘裕吃緊時控制並行重型 worker 數（`≤ 2` 併發波次），可即時換回約 `40%` 峰值 PSS 空間；此建議不寫死為程式硬限制，以免阻礙多工作業或正常擴充。

---

### 1.2 候選 2：Node／Electron V8 記憶體配額與併發邊界實驗

實測工具：`scripts/stage6_3_candidate2_bench.py` 與共用隔離模組 `scripts/stage6_adb.py`（強制原生端 `TracerPid=0`、清空 `ADB_SERVER_SOCKET`／`ANDROID_ADB_SERVER_ADDRESS`／`ANDROID_ADB_SERVER_PORT`、鎖定 `-H 127.0.0.1 -P 5038 -s <serial>` 與 `HOME`、並執行 `myron`/`25102PCBEG` 及 `com.termux.x11`/`com.waydefu.x11gpu` 身份驗證；原始逐次數據見 [`stage6-3-candidate2-20261127/`](stage6-3-candidate2-20261127/README.md)）。`/proc/pressure/memory`（`PSI`）與 `/sys/block/zram0/mm_stat`（ZRAM 真實壓縮率）皆實證 `Permission denied`，明確標記為 **`UNAVAILABLE_DUE_TO_PERMISSION`**（不可取得，不視為完整量測通過）。
背景基線量測發現 V8 預設 `heap_size_limit` 極高：**`node v24.20.0 = 2,240 MB`**、**`electron 44.9.1 = 4,192 MB`**。

#### 實驗 2A：V8 `--max-old-space-size=512` vs 預設（`2× Electron + 2× Python`，3 輪 ABBA = 6 對）

| 指標 | `default`（`4192 MB`） | `cap_512`（`--max-old-space-size=512`） | 差異／觀察 |
|---|---|---|---|
| 完成／成功數 | `6/6` (`rc=0`) | `6/6` (`rc=0`) | 皆無失敗 |
| 耗時中位數 (`wall_ms`) | `722.34 ms` | `723.12 ms` | `+0.11%`（打平） |
| 峰值 PSS 中位數 | `303.3 MB` | `359.1 MB` | 無節省（中位數反略高，單對互有勝負） |
| 峰值 RSS 中位數 | `395.0 MB` | `464.3 MB` | 無節省 |
| `MemAvailable` 最低 | `3754.4 MB` | `3629.2 MB` | 無改善 |
| `pgmajfault` 中位數 | `1620.5` | `789.0` | 高離散（區間 `191–31,405`，無穩定方向性淨益） |
| `PSI` | `UNAVAILABLE_DUE_TO_PERMISSION` | `UNAVAILABLE_DUE_TO_PERMISSION` | 非 Root `adb shell` `Permission denied`，不可取得 |

**應用相容性探針（`2A_compat_probe`，實際保留 `250 MB` 與 `650 MB` V8 JS 物件）：**

| 配額設定 | `250 MB` 負載 (`rc` / `peak_pss` / OOM) | `650 MB` 負載 (`rc` / `peak_pss` / OOM) |
|---|---|---|
| `--max-old-space-size=512` | `rc=0` / `203.2 MB` / 無 | **`rc=255`（原生直跑 `rc=134`）** / `511.5 MB` / **`FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory`** |
| `--max-old-space-size=1024` | `rc=0` / `248.1 MB` / 無 | `rc=0` / `636.4 MB` / 無 |
| `default` | `rc=0` / `261.5 MB` / 無 | `rc=0` / `714.4 MB` / 無 |

- **2A 結論**：全域套用 `--max-old-space-size=512` 在日常負載上**沒有可重現的 PSS／耗時淨收益**，且會在 >512 MB 重型 JS 工作時直接造成 OOM 閃退；因此**不採納全域 V8 heap 上限**（退回）。

#### 實驗 2B：工作量等價之併發 worker 上限對照（`seq_2x2` 兩波 2+2 vs `par_4x4` 單波 4+4，3 輪 ABBA = 6 對）

| 指標 | `par_4x4`（4 Electron + 4 Python 併發） | `seq_2x2`（兩波各 2 Electron + 2 Python） | 差異 |
|---|---|---|---|
| 完成／成功數 | `6/6` (`rc=0`) | `6/6` (`rc=0`) | 皆無失敗 |
| 峰值 PSS 中位數 | `730.2 MB` | **`441.9 MB`** | **`-39.5%`**（6/6 對全部下降） |
| 峰值 RSS 中位數 | `958.0 MB` | **`544.0 MB`** | **`-43.2%`**（6/6 對全部下降） |
| `MemAvailable` 最低 | `3252.5 MB` | **`3800.1 MB`** | **`+547.6 MB`**（6/6 對全部提高） |
| 耗時中位數 (`wall_ms`) | `1179.14 ms` | `1690.99 ms` | **`+43.4%`**（序列化換取記憶體空間） |
| `pgmajfault` 中位數 | `4107.5` | `6336.5` | 未降反略高（等量工作總觸頁數相近，受背景頁回收波動影響） |
| `pswpin` / `pswpout` 中位數 | `3883.5` / `14081.0` | `5802.0` / `11685.0` | `pswpout` 略低、`pswpin` 略高 |
| `PSI` | `UNAVAILABLE_DUE_TO_PERMISSION` | `UNAVAILABLE_DUE_TO_PERMISSION` | 非 Root `adb shell` `Permission denied`，不可取得 |

- **Native Hybrid 邊界**：沿用 Stage 5 Step 5 已凍結實測（`fast9+09c` 驗收）：僅對單次重型 `python3` 全樹掃描於 `TracerPid=0` 執行（`5.55×`、`1542.5 → 277.9 ms`），短高頻 CLI 留於 `proot-fast8` 內。
- **2B 結論**：序列降併發（`4→2`）有顯著峰值記憶體保護（`-39.5%` PSS、`+547.6 MB` 可用空間），但以 `+43.4%` 耗時換取且未降低 `pgmajfault`；僅作為記憶體吃緊時的操作／排程守則，不強行硬改程式預設。

---

### 1.3 候選 4：Phantom Process 殺程保護

- **觀測事實**：6.1 檢查顯示 `max_phantom_processes=32`、`settings_enable_monitor_phantom_procs=null`、`uid_visible_procs = 83–89`。然而在 6.1 盤點、6.2 全部 5 個 180 秒高壓區塊（`370/370` 批次）以及 6.3 對照實驗期間，唯讀讀取 `logcat -d -b events` 中針對 `com.termux` 的 `am_kill`／`lmk` 事件均為 **0 次**。
- **處置**：依計畫書 §4.1 觸發條件（未證實遭誤殺即不動作）與使用者指令，**裁決 `PAUSE`、不修改 Phantom Process 或任何 Android 系統設定**。

---

## 二、Stage 6.4：候選 1–4 正式裁決總表

| 候選項目 | 正式裁決 | 核心實測依據 | 採納／執行範圍與回復方式 |
|---|---|---|---|
| **1. 同時活躍 Electron／Chromium 上限與節流紀律** | **`GO`（純操作紀律）** | 6.3 盤點 Antigravity 佔 UID PSS **76.9%**（`547.6 MB`）；6.2 壓測 `MemAvailable` 最低 `3.21 GB`；2B 降併發可省 `39.5%` 峰值 PSS。 | 採納為工作流規範（`≤ 2` 重型 Electron、關閒置分頁、維持 `f8-shard` v2），**不硬編碼於程式**；零系統殘留。 |
| **2. 使用者態記憶體配額與 Native Hybrid 邊界** | **`PAUSE`（部分保留／全域上限退回）** | 2A 實測 `--max-old-space-size=512` 耗時與 PSS 無淨益（`722.34→723.12 ms`、`303.3→359.1 MB`）且 `650 MB` OOM 閃退；2B 降併發以 `+43.4%` 耗時換 `-39.5%` PSS；Stage 5 單次重型掃描維持 `5.55×` Hybrid 邊界。 | 退回全域 V8 heap 上限；僅保留既定 Stage 5 Native Hybrid 邊界與「記憶體吃緊時降併發」建議。 |
| **3. 電源模式情境化切換策略** | **`PAUSE`（僅短時爆發或配散熱）** | Stage 6.2 實測：`balanced` 極穩（`0.026%` 離散）；`performance` 前 30s 快 `+6.39%/+6.45%`，但兩次均破 G4 `85.0 °C`（`87.2`/`85.7 °C`）且 `P2` 遭 `cpu6` 砍半至 `2.23 GHz`（`-0.00%`）。 | 日常預設維持 `balanced`；僅短時需求或配外接散熱時手動切換；UI 一鍵復原。 |
| **4. Phantom Process 殺程保護** | **`PAUSE`（不觸發、零修改）** | `uid_visible_procs = 83–89` 下，6.1/6.2（370 批）/6.3 全程 `com.termux` `am_kill`/`lmk` **0 次**。 | 不修改任何 Phantom Process 或 Android 系統參數。 |

---

## 三、Stage 6 計畫書 §5.2 結案驗收清單核對（4 項完整通過、1 項權限受限部分達成）

- [x] **連線與身份驗證**：2026-11-27 經 `-H 127.0.0.1 -P 5038` 驗證 `ro.product.model=25102PCBEG`、`ro.product.device=myron`；`com.termux.x11` 版號 `1.03.01-11b82d9-06.09.26`（`firstInstallTime=2026-09-03 22:35:10`）；`com.waydefu.x11gpu` 版號 `1.03.01-f592241-24.09.26`（`firstInstallTime=2026-09-07 03:45:30`）；ADB `5037` 全程未動。並已將裝置選擇、環境隔離與身份驗證補入 `scripts/stage6_adb.py`（經 `scripts/test_stage6_adb.py` 單元測試與實機驗證），供 `stage6_2_power_bench.py` 與 `stage6_3_candidate2_bench.py` 共用。
- [ ] **Stage 6.1 基線補齊（`PARTIAL / UNAVAILABLE_DUE_TO_PERMISSION`，不視為完整量測通過）**：
  - **已取得**：三模式閒置快照存檔於 [`stage6-audit-20261127/`](stage6-audit-20261127/README.md)；`dumpsys meminfo` ZRAM（實體／swap 淨配比 ~2.95–3.0×）、`/proc/vmstat`（經 `adb shell`）、`max_phantom_processes`、LMKD logcat 皆已補齊。
  - **不可取得（權限不足）**：`/proc/pressure/*`（**PSI**）與 `/sys/block/zram0/mm_stat`（**ZRAM 真實壓縮率** `orig_data_size / compr_data_size`）在非 Root `adb shell`（`com.android.shell`）下實證 `Permission denied`，明確標記為 `UNAVAILABLE_DUE_TO_PERMISSION`，**不視為完整量測通過**。
- [x] **Stage 6.2 三模式受控對照**：完成第一輪 `B1 P1 P2 B2` 與紅色對照 `S1` 結案（[`STAGE6-2-POWER-MODE-RESULT-20261127.md`](STAGE6-2-POWER-MODE-RESULT-20261127.md)），已排除 `hw-trip`／`-273000` 假讀值，並完成乾跑解析度校準後之功耗換算；唯該階段同樣受限於 `PSI` 與 `zram0/mm_stat` 不可取得。
- [x] **Stage 6.3 合規與可逆性**：候選 1–4 維持非 Root、零 Android 系統設定寫入（zero mutation）。
- [x] **Stage 6.4 裁決與全域潔淨**（2026-11-27 11:24 CST 實測核對）：
  - `out8/` 與凍結清單 `baselines/fast9-09c-20261127/sha256sums.txt` **5/5 OK**。
  - `src/f8-proot-fast`、`src/f8-proot-fast-fast9-fixes`、`src/f8-proot-fast-stage5` 三工作樹 `git status --short` 皆為空（`dirty=0`）。
  - Stable `:1`（`28218` `termux-x11 com.termux.x11 :1 -legacy-drawing`）全程未觸碰；`shard-daemon.sh` 單一實例 `17875`；6.2 與 6.3 全部批次 `orphan_pids = 0`。

---

## 四、證據索引與 SHA256 總覽

| 項目 | 位置 | 內容與雜湊說明 |
|---|---|---|
| **Stage 6.1 唯讀基線** | [`stage6-audit-20261127/README.md`](stage6-audit-20261127/README.md) | 省電／均衡／效能 3 份閒置快照與權限實測紀錄 |
| **Stage 6.2 凍結門檻** | [`STAGE6-2-POWER-MODE-FREEZE-20261127.md`](STAGE6-2-POWER-MODE-FREEZE-20261127.md) | 凍結判定規則（未改動） |
| **Stage 6.2 實測報告** | [`STAGE6-2-POWER-MODE-RESULT-20261127.md`](STAGE6-2-POWER-MODE-RESULT-20261127.md) | 第一輪 `B1 P1 P2 B2` ＋ `S1` 分析與圖表 |
| **Stage 6.2 逐批原始檔** | [`stage6-2-runs-20261127/README.md`](stage6-2-runs-20261127/README.md) | 去敏後 `DRYRUN`、`B1`、`P1`、`P2`、`B2`、`S1`、`series_verdict` + [`SHA256SUMS`](stage6-2-runs-20261127/SHA256SUMS) + [`ORIGINAL_ON_DEVICE_SHA256SUMS`](stage6-2-runs-20261127/ORIGINAL_ON_DEVICE_SHA256SUMS) |
| **Stage 6.3 候選 2 原始檔** | [`stage6-3-candidate2-20261127/README.md`](stage6-3-candidate2-20261127/README.md) | `2A`（6 對）+ 相容探針（6 次）+ `2B`（6 對）逐次 JSON + [`SHA256SUMS`](stage6-3-candidate2-20261127/SHA256SUMS) |
| **Stage 6.2/6.3 腳本與測試** | `scripts/{stage6_adb.py,test_stage6_adb.py,stage6_2_judge.py,test_stage6_2_judge.py,stage6_2_power_bench.py,stage6_3_candidate2_bench.py}` | 隔離 ADB、判定器與實驗執行腳本 |
