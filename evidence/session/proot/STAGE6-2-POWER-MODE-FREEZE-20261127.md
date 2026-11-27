# Stage 6.2 電源模式對照 — 判定門檻凍結

**狀態：FROZEN。** 2026-11-27 09:52 CST 使用者在對話中批准全文（原話：「批准，合併 PR」）。本文件經 PR 合併進 GitHub `main` 之後才開始任何負載量測；之後任何數字的更動，視為整批作廢、須另立新的凍結文件。

## 1. 要回答的問題與範圍

- 問題：現役 `fast9+09c` 在日常工作站負載下，把 HyperOS 電源模式從**均衡**切到**效能**，是否有可重現、穩態不崩的淨改善？（對應 [Stage 6 計畫書](STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md) §4.1 候選 3。）
- 比較對象只有兩個狀態：`balanced`（`POWER_PERFORMANCE_MODE_OPEN=0`）與 `performance`（`=1`）。`low_power` 全程為 0。
- 另有一個**紅色對照**：省電模式（`low_power=1`），目的是證明量測工具抓得到大差異（§7）。
- 所有 Android 設定由使用者手動切換；我們不執行任何 `settings put`、`device_config put`、`setprop`。不碰 Stable `:1`、不碰 ADB 5037（只用 `-P 5038`）、不 `logcat -c`。

## 2. 揭露：凍結前已看過什麼

2026-11-27 讀過三份**閒置單次快照**（[README](stage6-audit-20261127/README.md)）：電源旗標、`cpu` 頻率上限／當下頻率、溫度、ZRAM 用量。沒有看過任何工作負載的結果（`wall_ms`、點擊延遲、`rAF` 等）。門檻所依據的雜訊資料只取自**本文件之前已凍結並公開**的 Stage 5 與 fast9+09c 驗收（見 §6 表）。

## 3. 對 Stage 6 計畫書的更正（以本文件為準）

| 計畫書原文 | 更正 | 依據 |
|---|---|---|
| 透過 ADB 可讀 `/proc/pressure/*` 與 `zram0/mm_stat` | **讀不到**，`adb shell` 也 Permission denied；PSI 與 `mm_stat` 一律記 `null` | `audit-baseline-*.txt` §6 |
| ZRAM 壓縮率來自 `mm_stat` | 改用 `dumpsys meminfo` 的 `ZRAM: X physical used for Y in swap` | 同上；省電開 2.96×、關 2.95× |
| `/proc/vmstat` 可由本機讀 | PRoot 內是靜態假檔案（全 0）；原生 Termux 是 Permission denied；**只有 `adb shell` 讀得到真實計數**。腳本內的 vmstat 區段因此為空，量測時必須經 `adb shell` 讀 `pswpin pswpout pgmajfault allocstall_* compact_stall`，記區塊前後差值 | 2026-11-27 實測 |
| 型號須為 `F8` | `ro.product.device=myron`（型號代碼 `25102PCBEG`） | `getprop` |
| 起測電量 40–85% | 改為 40–90%（量測當下為 86%，原範圍沒有實質理由） | 凍結前調整，已揭露 |
| 「不得掃描 port」 | 採專案既定做法：原生端執行 `f8-adb-port`（含掃描並驗證 adb 協定） | `CLAUDE.md`、`HANDOFF.md` |

## 4. 實驗設計

**比較單位是「區塊」，不是批次。** 同一區塊內的連續批次受溫度影響、彼此不獨立，不能當獨立樣本做符號檢定。

- 每區塊：起測條件成立後，用現役 `proot-fast8` 連續跑**複合工作站批次** 180 秒（負載定義沿用 Stage 5 Step 5：Chromium 153 三分頁，每分頁 60 幀 `rAF` 加 5 次點擊 RTT，加 2× Electron、2× Python Agent、2× Git CLI），全程原生執行（`TracerPid=0`），單調時鐘、事件驅動等待。
- 視窗：批次起點落在區塊的 0–30 秒為 **early**，90–180 秒為 **late**；30–90 秒只記錄、不判定。
- 排程（9 個區塊，ABBA 兩輪加對照）：`B1 P1 P2 B2 | B3 P3 P4 B4 | S1`。`B`=balanced、`P`=performance、`S`=省電對照。需使用者手動切換 5 次（B1→P1、P2→B2、B3→P3、P4→B4、B4→S1）。
- 配對（相鄰區塊）：(B1,P1)、(P2,B2)、(B3,P3)、(P4,B4)。
- 區塊之間靜置冷卻；起測條件（§5 V3）成立才開始，每 30 秒檢查一次，最久等 15 分鐘，逾時該區塊 INVALID。
- 估計總時間約 1–2.5 小時（**估計，未量測**）。

**每批次記錄：** `wall_ms`、`inner_total_ms`、`tracer_cpu_ms`、`launch_ms`、`click_p50/p95`、`rAF p50/p95/p99` 與掉幀（>20 ms、>33.3 ms）、`peak_pss_mb`、`rc`、`orphan_pids`、起始時間戳。
**每 5 秒取樣：** 各 cpu 的 `scaling_cur_freq`／`scaling_max_freq`、`thermal_zone*`（排除 `hw-trip` 與 `-273000`）、電池溫度與電量（`dumpsys battery`）、`Thermal Status`、`MemAvailable`、電源旗標。
**每區塊前後各一次：** `dumpsys meminfo` 的 ZRAM、經 `adb shell` 的 vmstat 計數、`Charge counter`、`logcat -d -b events` 中 `am_kill`／`lmk` 行（只讀，不清除）。

## 5. 有效性閘門（任一失敗 = 該區塊 `INVALID`，不是 FAIL）

- **V1** 電源旗標在區塊開始與結束時都符合該區塊的預期（`low_power`、`POWER_PERFORMANCE_MODE_OPEN`、`speed_mode=0`）。
- **V2** 起測時的頻率上限等於預期：balanced 為 cpu0–5 `2,745,600` kHz、cpu6／7 `2,880,000` kHz；performance 為 `3,628,800`／`4,608,000` kHz；省電對照為 cpu6／7 `768,000` kHz。
- **V3** 起測溫度：真實 `cpu-*` 溫度區最大值 ≤ 55.0 °C，且電池溫度 ≤ 36.0 °C。
- **V4** 全程放電（`status: 3`）、電量 40–90%、各區塊起始電量差 ≤ 5 個百分點。
- **V5** 螢幕 `mWakefulness=Awake`，且全程不變；區塊進行中使用者不得碰手機。
- **V6** ADB 取樣失敗比例 ≤ 10%；批次 `rc≠0` 或 `orphan_pids≠0` 的比例 ≤ 10%。
- **V7（量測解析度）** 四個 balanced 區塊的 late 視窗 `wall_ms` 中位數，其 `(最大−最小)/中位數` ≤ 4%；四個 performance 區塊同。超過代表量測雜訊大到無法解析 2% 的差異，整個實驗 `INVALID`。
- **V8（紅色對照）** S1 的 late 視窗 `wall_ms` 中位數必須比 balanced 四區塊中位數**慢至少 2.0%**，否則量測工具對大差異也沒反應，整個實驗 `INVALID`。
- **重試規則**：`INVALID` 的區塊永久保留紀錄；同一排程位置最多再試一次（記為 attempt 2）；仍 `INVALID` 則整個實驗 `INVALID`。已有效的區塊不重跑、不重判。

## 6. 判定

**主要指標（唯一用來判 GO 的）：** 每個區塊 late 視窗的 `wall_ms` 中位數。每個配對的改善 = `(B − P) / B`。

**雜訊底（A/A）：** `max( (四個 B 的最大−最小)/中位數 , (四個 P 的最大−最小)/中位數 )`。

| 判定 | 條件（全部同時成立） |
|---|---|
| **GO** | 4/4 配對改善 ≥ 2.0%；改善中位數 ≥ 2 × A/A；下列護欄 G1–G6 全部成立 |
| **RETIRE** | 改善中位數 < 0.5%；或任一配對改善 ≤ −2.0%（效能模式反而慢）；或 G5 失敗（殺程、孤兒、`rc≠0`） |
| **PAUSE** | 其餘情形，含：early 視窗 4/4 配對改善 ≥ 2.0% 但 late 視窗未達（熱降頻）；或護欄 G1–G4、G6 失敗 |
| **INVALID** | §5 任一整體閘門（V7、V8、重試後仍失敗）不成立；不下 GO/PAUSE/RETIRE |

**護欄：**
- **G1** performance 的 late `click_p95` 中位數 ≤ 1.15 × balanced。
- **G2** performance 的 `rAF p95` ≤ balanced + 1.0 ms，且 >33.3 ms 掉幀數 ≤ balanced。
- **G3** performance 區塊 late 視窗內所有取樣 `Thermal Status = 0`。
- **G4** 所有取樣：電池溫度 ≤ 42.0 °C、真實 `cpu-*` 溫度區 ≤ 85.0 °C（低於 95 °C 硬體跳脫常數）。
- **G5** 區塊內無 `com.termux` 的 `am_kill`／`lmk`、`orphan_pids = 0`、有效批次 `rc = 0`。
- **G6** performance 的 late/early `wall_ms` 比值 ≤ balanced 的比值 + 0.03（後段漂移不得更糟）。

**次要指標（只報告，不判定）：** `launch_ms`、`tracer_cpu_ms`、`inner_total_ms`、`click_p50`、`peak_pss_mb`、`MemAvailable` 最低值、ZRAM 前後、vmstat 差值（經 `adb shell`；`null` 不得寫成 0）、PSI（`null`）。
**功耗：** 不參與判定。`Charge counter` 解析度看起來是 10,000 µAh 的倍數（兩次讀值 5,330,000 與 5,220,000；10 秒間閒置時不變），實際解析度由乾跑量測；區塊 Δ 小於解析度的 5 倍就記 `null`，否則報告 `ΔµAh × 電壓 / 時間`。

**門檻依據（皆來自已凍結、已公開的資料）：**

| 數字 | 依據 |
|---|---|
| 2.0% 主要門檻 | Stage 5 Step 5：`wall_ms` 的 IQR 為 5.06 ms／2,276.30 ms ≈ 0.22%；`-2.24%` 的差異在 6/6 配對中成立（`sign_p=0.0312`）。2.0% 約為底噪的 9 倍，且與已確認可辨識的效應同量級。 |
| 4% 解析度（V7）、2×A/A | 門檻 2.0% 的兩倍，確保同模式區塊間的自然離散不會大於要偵測的效應。 |
| 15% `click_p95` 護欄 | fast9+09c 驗收中近似相同建置之間，`click_p95` 差到 13.33%（來源註明樣本不足）；護欄必須高於已觀察到的雜訊。 |
| 0.5% RETIRE | 同上 `wall_ms` 底噪 ≈ 0.2%；低於 0.5% 視為無可辨識效應。 |
| 42.0 °C 電池、85.0 °C 晶片 | 計畫書 §5.1 的電池上限，以及低於 95 °C 跳脫常數的實務邊際。 |

## 7. 工具與驗證（開跑前必須完成，否則不得上機）

- 量測工具尚未寫。它會從 `src/f8-proot-fast-stage5/tests/bench_workstation_abba.py` 的批次邏輯衍生：單一 binary、連續 180 秒批次、每批時間戳、5 秒取樣；vmstat 經 `adb shell` 取得。
- 判定程式先用合成資料驗證，**必須包含會失敗的案例**：明確勝出 → `GO`；無差異 → `RETIRE`；同模式區塊離散過大 → `INVALID`；early 勝出但 late 崩 → `PAUSE`；紅色對照不夠慢 → `INVALID`。任一案例判錯，工具不得使用。
- 上機前做一次 30 秒的乾跑區塊（不計入結果），確認取樣、時間戳、`Charge counter` 解析度、`orphan_pids` 都正常。
- 工具修正必須寫進 commit 與報告，不抹除錯誤版本。

## 8. 已知限制

- 只有一支手機、一種負載、電池放電狀態；結論不外推到插電、其他負載或其他裝置。
- 不比較 `power_saver` 的實用性，只當紅色對照。
- 功耗解析度粗，可能多數區塊為 `null`。
- tracer 為單執行緒，不一定吃得到更高的頻率上限；若如此，結果就是 `RETIRE`，這是有效結論。
- PSI 無法取得，無法用「記憶體停滯時間」佐證。

## 9. 批准後的流程

1. 使用者批准本文件（或指出要改的數字，改完再批准）。
2. 去掉「DRAFT」標記，經 PR 合併進 `waydefu/GPU` `main`。
3. 寫量測與判定工具，完成 §7 驗證。
4. 依 §4 排程執行；每個區塊結束先檢查有效性再進下一個，不過就停。
5. 結果與判定另立 `STAGE6-2-POWER-MODE-RESULT-*.md`，不回改本文件。
