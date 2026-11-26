# Stage 6 — Android 宿主效能與電源最佳化計畫（2026-11-26）

> **文件性質與邊界聲明**：本文件為 Stage 6 規劃與協議文件（docs-only plan），尚未執行 ADB 連線、三模式實測或任何系統調校。執行任何步驟時必須嚴守本專案紅線：不修改 `src/f8-proot-fast*` Git repository、不覆寫現役 `out8/` / `shard2/`、不觸碰 Stable `:1`（`com.termux.x11`）、不觸碰 ADB port `5037`，且未經使用者明確授權嚴禁執行任何 Android 系統寫入。

---

## 一、背景與已實證宿主瓶頸

依據 Stage 5 Phase 3 Step 3（[`STAGE5-PHASE3-STEP3-HOST-AUDIT-20261126.md`](STAGE5-PHASE3-STEP3-HOST-AUDIT-20261126.md)）與總結報告（[`STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md`](STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md)）的本機唯讀審計（`baseline-daily.log`），POCO F8 Ultra（`myron`）日常工作站卡頓與資源上限主要來自下列已量測之宿主瓶頸：

1. **實體記憶體緊縮與 ZRAM 高佔用**：
   - `MemTotal = 15,373,988 kB`（`14.66 GiB`），日常未壓測狀態下 `MemAvailable` 僅剩 **`2,863,616 kB`（`2,796 MiB` / `~2.73 GiB`）**，`MemFree` 僅 `209,596 kB`（`205 MiB`）。
   - `SwapTotal = 16,777,212 kB`（`16 GiB` ZRAM），已使用 **`9,502,444 kB`（`9.06 GiB`，`56.6%`）**，`SwapFree` 剩 `7,274,768 kB`。在可用 RAM 僅剩 ~2.73 GiB 且 ZRAM 已過半的狀況下，多代理／瀏覽器併發極易觸發記憶體回收與換頁抖動（swap thrash）。
2. **重型 AI Agent / Electron 記憶體足跡與 UID 行程數超標**：
   - PRoot / Termux 同一 UID 下可見行程數達 **`uid_visible_procs = 86`**（遠高於 Android 預設 `32` 的 Phantom Process 監控門檻），合計 `1,248.2 MB PSS` / `2,190.6 MB RSS`。
   - 單一 `antigravity` 棧合計約 **`~766 MB PSS`**（主行程 PID `22993` 佔 `386.7 MB PSS` / `463.4 MB RSS` + 輔助行程 `~151.4 MB PSS` 共 `~538 MB PSS`，加上 `language_server` PID `22855` 佔 `228.0 MB PSS` / `229.5 MB RSS`）。
   - `hermes`（PID `8982`）佔 **`270.4 MB PSS`（`~270 MB PSS` / `271.6 MB RSS`）**；`termux-x11`（`main` PID `26794`）佔 `45.4 MB PSS` / `185.3 MB RSS`。
3. **CPU `walt` governor 預設頻率上限鎖定**：
   - `cpu0–cpu5`（big/performance 叢集）：`gov=walt`、`min=787.2 MHz`，**`scaling_max_freq = 2,745.6 MHz`（`2.75 GHz`）**，對照硬體極限 `cpuinfo_max_freq = 3,628.8 MHz`（`3.63 GHz`）僅開放 **75.7%**。
   - `cpu6–cpu7`（prime 叢集）：`gov=walt`、`min=883.2 MHz`，**`scaling_max_freq = 2,880.0 MHz`（`2.88 GHz`）**，對照硬體極限 `cpuinfo_max_freq = 4,608.0 MHz`（`4.61 GHz`）僅開放 **62.5%**。
   - 顯示系統日常處於均衡／溫控節制檔位，並非全速解放。
4. **真實溫度區間與非溫度假讀值區分**：
   - **真實感測器讀值**：`cpu-0-*` **`54.8–64.8 °C`**、`cpu-1-*` `57.9–64.8 °C`、`cpullc-*` `58.1–62.1 °C`、`cpu_therm` `48.8 °C`、`gpuss-*` `49.0–52.9 °C`、`ddr` `54.0 °C`、`battery` `34.3 °C`、`quiet_therm` `36.4 °C`、`display_therm` `33.2 °C`。審計當下為微溫穩態，未達急迫過熱點。
   - **不可誤判為即時溫度之讀值**：`thermal_zone67 (cpu-hw-trip-0) = 95000` 與 `thermal_zone68 (cpu-hw-trip-1) = 95000` 為硬體跳脫常數（`[HW_TRIP_CONSTANT]`，`95.0 °C`）；`thermal_zone93 (sdr0_pa) = -273000`（`0 K`）為未校準／無感測器假讀值。
5. **與 PRoot 層優化的分工邊界**：
   - Stage 5 Step 5 已證明 `fast9-combined` 能使複合負載的 `tracer_cpu_ms` 下降 `11.20%`、Chromium 啟動縮短 `7.92%`，但宿主 RAM 容量緊縮、HyperOS 電源頻率上限與 Android LMKD / Phantom Process 機制無法單靠 PRoot patch 解決，且 Step 3 因無線偵錯關閉，`/proc/pressure/*`、`/proc/vmstat`、`/sys/block/zram0/mm_stat` 與 `dumpsys` 尚缺 `com.android.shell` 權限讀值，故立項 Stage 6 進行先取證、後對照、再決策之宿主層優化。

---

## 二、Stage 6.1：先取證、零寫入之唯讀基線補齊

### 2.1 隔離 ADB 通道規範（嚴守 `-P 5038`、零寫入）

依 [`ADB-CONNECT.md`](../../../ADB-CONNECT.md) 執行：

1. **前置**：使用者手動開啟 Android「設定 → 開發人員選項 → 無線偵錯」，取得當次畫面顯示之 `<HOST:PORT>`（IP 與 port 每次皆可能變動，禁寫死，亦不得掃描 port）。
2. **啟動隔離 server（嚴禁碰 `5037`）**：於原生 Termux 環境（`TracerPid=0`）使用 authority binary `/data/data/com.termux/files/usr/bin/adb` 並指定 `HOME=/data/data/com.termux/files/home`（確保 TLS 金鑰指紋一致）：
   ```bash
   TADB=/data/data/com.termux/files/usr/bin/adb
   HOME=/data/data/com.termux/files/home \
     env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
     "$TADB" -L tcp:5038 server nodaemon
   HOME=/data/data/com.termux/files/home "$TADB" -H 127.0.0.1 -P 5038 connect <HOST:PORT>
   ```
   - 所有後續查詢必須顯式攜帶 `-H 127.0.0.1 -P 5038 -s <HOST:PORT>`，禁止裸 `adb shell` 與禁止 `kill` 既有 `5037` server。
   - Note：`/usr/local/bin/f8-adb-port` 在 PRoot 內僅為 wrapper，應於原生 Termux 執行或直接讀取無線偵錯主頁之最新 connect port。
3. **身份驗證（每次連線必做並寫入當次 evidence）**：
   - `getprop ro.product.model`（須為 `F8`）、`getprop ro.product.device`（須為 `myron`）。
   - `dumpsys package com.termux.x11 | grep -iE "versionName|firstInstallTime"` 與 `dumpsys package com.waydefu.x11gpu | grep -iE "versionName|firstInstallTime"`。

### 2.2 唯讀基線採樣清單、命令與欄位定義

以既有唯讀腳本 [`android-host-audit-readonly.sh`](../../../src/f8-proot-fast/scripts/android-host-audit-readonly.sh) 為藍本，透過 `/usr/local/bin/termux-bg-run` 於原生端（`TracerPid=0`）執行，並將原始日誌存檔至 `evidence/session/proot/stage6-audit-<DATE>/`。補齊項目如下：

| 觀測維度 | 採樣來源與唯讀命令（`-P 5038` / 本機） | 關鍵欄位定義與判讀口徑 |
|---|---|---|
| **RAM / PSS 分佈** | 本機 `/proc/meminfo`、`/proc/<pid>/smaps_rollup`；ADB `dumpsys meminfo` 與 `dumpsys meminfo com.termux` | `MemAvailable`、App/Native/Graphics/Unknown PSS、`Total PSS`、`Lost RAM`；區分 Android 前景 App 與 `com.termux` PRoot 樹個別佔用。 |
| **ZRAM 真實壓縮率** | ADB `cat /sys/block/zram0/mm_stat`；`grep -E '^(pswpin\|pswpout\|pgmajfault\|allocstall\|compact_stall)' /proc/vmstat` | `mm_stat` 欄位依序為 `orig_data_size`、`compr_data_size`、`mem_used_total`、`mem_limit`、`mem_used_max`、`same_pages`、`pages_compacted`、`huge_pages`。真實壓縮比 = `orig_data_size / compr_data_size`；淨節省倍率 = `orig_data_size / mem_used_total`。搭配前後 `vmstat` 增量判斷是否發生持續換頁抖動。 |
| **PSI 資源停滯指標** | ADB `cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io` | `some`（至少一個可執行任務等待資源之比例 %）與 `full`（全部非閒置任務同時停滯之卡頓比例 %）；同時記錄 `avg10` / `avg60` / `avg300` 與採樣區間前後之 `Δtotal`（微秒），避免僅讀開機累計值造成誤判。 |
| **Phantom Process 與 LMKD** | ADB `device_config get activity_manager max_phantom_processes`、`settings get global settings_enable_monitor_phantom_procs`、`dumpsys activity settings`、`dumpsys activity processes`；唯讀事件 `logcat -d -b events \| grep -E 'am_kill\|lmk'` 及 `logcat -d \| grep -iE 'lowmemorykiller\|lmkd\|phantom'` | 確認 `max_phantom_processes`（常見預設 `32`）與開關實際狀態，核對 `uid_visible_procs = 86` 是否受豁免或已觸發背景強殺；嚴禁執行 `logcat -c`。 |
| **CPU / GPU 頻率與電源旗標** | `/sys/devices/system/cpu/cpu{0..7}/cpufreq/{scaling_governor,scaling_cur_freq,scaling_max_freq,cpuinfo_max_freq}`；`/sys/class/kgsl/kgsl-3d0/{gpu_model,gpubusy,devfreq/cur_freq,devfreq/max_freq,gpuclk,max_gpuclk}`；ADB `settings get global low_power`、`settings get system POWER_PERFORMANCE_MODE_OPEN`、`settings get system speed_mode` | 確認各電源模式下 `cpu0–5`（上限 `3,628.8 MHz`）與 `cpu6–7`（上限 `4,608.0 MHz`）之實際 `scaling_max_freq` 解鎖幅度，以及 `Adreno840v2` (`kgsl-3d0`) 之工作佔空比 `gpubusy`。 |
| **溫控與電池電力** | `/sys/class/thermal/thermal_zone*/{type,temp}`、`/sys/class/power_supply/battery/{status,capacity,temp,voltage_now,current_now}`；ADB `dumpsys thermalservice`、`dumpsys battery` | 僅採計真實感測器（`cpu-0-*`、`cpu-1-*`、`cpullc-*`、`gpuss-*`、`ddr`、`battery`），明確排除 `hw-trip`（`95000`）與 `sdr0_pa`（`-273000`）；預先檢驗 `current_now` 單位（µA/mA）與充放電正負號方向後再計算瓦數。 |

---

## 三、Stage 6.2：省電 / 均衡 / 效能三種電源模式受控實測協議

### 3.1 模式定義與切換原則

- 由使用者透過 Android / HyperOS 系統設定手動切換三種電源模式：
  1. **`power_saver`**（省電模式）
  2. **`balanced`**（均衡模式，對應 Step 3 現況基線）
  3. **`performance`**（效能模式）
- 每次切換後須重新跑一次唯讀電源旗標快照（`low_power`、`POWER_PERFORMANCE_MODE_OPEN`、`speed_mode`、`scaling_max_freq`），驗證模式已實際生效。嚴禁使用 script 寫入系統設定。

### 3.2 熱穩態與排程防偏誤設計

為避免將「冷機前 10 秒爆發跑分」或「前輪餘熱導致後輪提前降頻」誤判為真實模式差異，必須遵守：

1. **固定冷卻溫度窗起點**：每模式開測前靜置冷卻至一致起始窗（建議 `cpu-0-*` / `cpu-1-* <= 55.0 °C` 且 `battery <= 36.0 °C`），起測與終測皆記錄完整溫度快照；未回落至溫度窗前不開下一輪。
2. **供電與螢幕條件鎖定**：三模式全程維持相同螢幕狀態與供電條件（建議統一於電池供電且電量 `40%–85%` 區間，或固定相同充電器／旁路條件並於報告明確標記，不可混用插電與不插電數據比較功耗）。
3. **排程順序與輪次**：以 `balanced → performance → power_saver` 為主序，於許可時補做反向次序或雙重複驗證，避免單向升溫／背景清理干擾；每模式須包含 **穩態持續負載窗（建議連續 `120–180 s` 結構化迴圈）**，並分段統計前段（0–30 s）與後段（90–180 s）之降頻與延遲漂移。

### 3.3 固定工作站複合負載與必收指標

沿用 Stage 5 Step 5 經實證且具零殘留保證之工作站複合負載結構（於隔離測試目錄執行，不寫入現役目錄或 Stable `:1`）：
- **負載組合**：Chromium Playwright 3 分頁（60 幀 `rAF` + 5 次點擊 RTT）＋ 2× Electron ＋ 2× Python AI Agent ＋ 2× Git CLI 併發（事件驅動回收與孤兒檢查 `orphan_pids = 0`）。
- **每輪必收指標**：
  - **延遲與互動**：複合批次牆鐘延遲（`wall_ms` 中位數 / IQR）、`click_p50` / `click_p95`、Chromium `rAF` 幀時間（`p50` / `p95` / `p99` 與 `>20 ms` / `>33.3 ms` 掉幀數）。
  - **CPU/GPU 實際頻率上限**：每 5 秒採樣 `cpu0–5` / `cpu6–7` 之 `scaling_max_freq`（偵測是否遭 `thermalservice` 動態下壓）與 `scaling_cur_freq`、GPU `devfreq/cur_freq` 與 `gpubusy`。
  - **溫度與功耗**：起／中／末段 `cpu-0-*`、`cpu-1-*`、`gpuss-*`、`ddr`、`battery` 溫度；依實測 `current_now` 與 `voltage_now` 換算平均與峰值功率 `P (W) = |current_now * voltage_now| / 10^12`（於確認 µA/µV 單位後套用）。
  - **ZRAM / PSI 變化**：負荷前後之 `MemAvailable` 最低點、`SwapUsed` 增量、`zram0/mm_stat` 壓縮比與 `mem_used_total` 增量、`PSI (cpu/memory/io)` 之 `Δtotal` 停滯時間及 `pgmajfault` / `allocstall` 增量。

---

## 四、Stage 6.3：非 Root、可逆最佳化候選與紅線

**決策鐵則**：僅依據 Stage 6.1 與 6.2 的實測證據決定是否採納以下候選項目；未經實證之猜測性調校不得套用。

### 4.1 候選最佳化項目（均須滿足非 Root 且完全可逆）

| 候選項目 | 觸發條件（須先由 6.1/6.2 實證） | 具體可逆措施 | 回復方式 |
|---|---|---|---|
| **1. 同時活躍 Electron / Chromium 實例上限與應用節流紀律** | 若確認 `antigravity`（`~766 MB PSS`）+ `hermes`（`~270 MB PSS`）+ 多瀏覽器併發導致 `MemAvailable < 2.0 GiB`、`PSI memory` 上升或 `pgmajfault` 飆高。 | 制定工作流紀律：桌面同時維持 `<= 2` 個重型 Electron 應用、避免多套 Chromium 常駐；重度 IDE 分頁閒置時關閉或改用 CLI／單體終端；配合既定 `f8-shard` v2 分離各重型前端之 `ptrace` tracer（待授權部署 `proot-fast9` 後可再減 `11.2%` tracer CPU）。 | 純使用者端操作與啟動習慣，即時調整、零系統殘留。 |
| **2. 使用者態記憶體配額與 Native Hybrid 邊界調度** | 若 ZRAM 已用過半且大型掃描／常駐後端導致大量換頁或 PRoot `ptrace` 序列化瓶頸。 | 限制並行 Python/Node worker 數量與 V8 heap 上限（如 `--max-old-space-size`）；僅將**單次重型 `python3` 全樹掃描**或**常駐原生 Agent 後端**置於 `TracerPid=0` 原生端（依 Stage 5 Step 2/5 邊界，禁止用來包裝高頻短 CLI）。 | 移除對應 env flag 或關閉獨立後端行程即可完全復原。 |
| **3. 電源模式情境化切換策略** | 若 Stage 6.2 證實 `performance` 模式能合法抬高 `cpu0–5` / `cpu6–7` `scaling_max_freq` 且在穩態窗未因熱降頻崩盤。 | 建立場景化建議表：短時高併發交互／編譯切換至 `performance`；長時多代理輕中載維持 `balanced`；低電量或高環境溫度時切換 `power_saver`，全由使用者手動切換。 | 系統 UI 一鍵切回「均衡」模式。 |
| **4. Phantom Process 殺程保護（僅限實測確認遭誤殺時評估）** | 僅當 6.1 實測證實 `settings_enable_monitor_phantom_procs=1`、`max_phantom_processes=32` 且 logcat 確實出現 `com.termux` 子程序遭 phantom killer 終止。 | 優先採使用者手動於 HyperOS 設定 `com.termux`「無限制」省電與鎖定後台；若仍不足且獲使用者**明確書面授權**，才評估備份原始值後再決定是否調整對應旗標。 | 切回原電池策略或透過預存還原指令回復預設值。 |

### 4.2 不可逾越紅線（Hard Redlines）

1. **禁止停用 LMKD 或核心系統保護**：不得關閉 Android Low Memory Killer Daemon、不得關閉溫控降頻或修改任何 thermal trip 閾值。
2. **禁止未授權之系統寫入**：嚴禁未經使用者逐項明確核准而執行 `settings put`、`device_config put`、`setprop` 或改寫系統分區。
3. **禁止觸碰 Stable `:1` 與 ADB `5037`**：永不覆蓋或重啟 `com.termux.x11`（`:1` 日用環境）；實驗 X11 僅限 `com.waydefu.x11gpu`（`:3`），停機只認前綴 `termux-x11gpu com.waydefu.x11gpu :3`；禁 `pkill -f f8-x11gpu`；禁 `logcat -c`；禁 kill ADB `5037`。
4. **禁止越界修改凍結資產**：Stage 6 審計與壓測不得寫入 `src/f8-proot-fast`（`ee603b8`）、`out8/`、`shard2/`、`/opt/mesa-kgsl` 及已結案之 Gate A / Stage 5 證據目錄。

---

## 五、Stage 6.4：Go / Pause / Retire 門檻與驗收清單

### 5.1 決策門檻（GO / PAUSE / RETIRE）

| 判定 | 必須同時滿足之量化準則 |
|---|---|
| **`GO`（採納為建議最佳化方案）** | ① **穩態效能勝出**：在 Stage 6.2 穩態持續負載窗（後段與整體）相較 `balanced` 基線，複合負載 `wall_ms`、`click_p95` 或 `PSI memory`／掉幀率展現可重現、統計一致之淨改善；<br>② **熱控與電力安全**：穩態期間 `cpu-0-*` / `cpu-1-*` 未持續逼近 `95 °C` trip 常數且未出現後段熱降頻反超（後段延遲劣化不得抵消前段收益），`battery <= 42 °C`；<br>③ **零副作用**：零 `am_kill` / LMKD / Phantom killer 誤殺、`orphan_pids = 0`、零未預期行程終止；<br>④ **完全可逆**：保留原始基線與明確單步還原路徑。 |
| **`PAUSE`（條件性保留／暫緩預設化）** | ① 僅在短時間窗或特定重負載有利，進入穩態後即因溫控牆 (`thermal throttling`) 與 `balanced` 持平，或功耗 (`W`) 增幅遠高於實感延遲改善；<br>② 僅列為「插電／短時專用策略」，不納入常態建議。 |
| **`RETIRE`（淘汰不採納）** | ① 對複合負載延遲、`rAF` 幀穩定度、`PSI` 或 `MemAvailable` 無可重現淨收益，甚至惡化尾部延遲（`p95`）與換頁；<br>② 觸發 LMKD 殺程、嚴重過熱降頻，或需依賴不可逆／違反 4.2 紅線之系統更動者，立即淘汰並封存證據。 |

### 5.2 Stage 6 結案驗收清單（Acceptance Checklist）

- [ ] **連線與身份驗證**：已於無線偵錯開啟下透過 `-H 127.0.0.1 -P 5038` 完成 `F8` / `myron` 驗證並登錄 `com.termux.x11` / `com.waydefu.x11gpu` 版號；ADB `5037` 全程未動。
- [ ] **Stage 6.1 基線補齊**：`zram0/mm_stat` 真實壓縮率、`PSI (cpu/memory/io)` `some`/`full`、`vmstat` 換頁增量、`dumpsys meminfo`、`max_phantom_processes`、LMKD/phantom logcat 證據全數取得並存檔至 `evidence/session/proot/stage6-audit-<DATE>/`。
- [ ] **Stage 6.2 三模式受控對照**：完成 `power_saver`、`balanced`、`performance` 於相同冷卻起點、固定供電口徑與穩態負載窗之實測；報告已明確區分真實感測器溫度與 `hw-trip` / `-273000` 假讀值，並附單位驗證後之 `current_now * voltage_now` 功耗與 `PSI` / ZRAM 變化。
- [ ] **Stage 6.3 合規與可逆性**：所有採納措施皆為非 Root、可逆方案；若無明確授權，Android 系統設定維持零寫入（zero mutation）。
- [ ] **Stage 6.4 裁決與全域潔淨**：每個候選項目均完成 `GO` / `PAUSE` / `RETIRE` 正式裁決；結案檢查確認 Stable `:1`、`out8/`、`shard2/` 與 `src/f8-proot-fast*` 乾淨無殘留、`orphan_pids = 0`。
