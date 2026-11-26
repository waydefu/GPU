# Stage 5 Phase 3 — 最終收斂與工作站驗收報告（2026-11-26）

> **邊界與狀態聲明**：本報告彙整 Stage 5 Phase 3 Step 1–5 全部實測證據。所有編譯、壓測、GPU 對照與部署驗證均於隔離目錄 `/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp`（`$STAGE`）及隔離分支 `src/f8-proot-fast-stage5`（`stage5/isolated-fast8-20261126` @ `5541ef7`）完成；**現役系統完全未覆寫**（`out8/`、`shard2/`、`/usr/local/bin/f8-shard`、`/opt/mesa-kgsl`、`src/f8-proot-fast` `main` `ee603b8`、Stable `:1` `com.termux.x11`、凍結 `evidence/` 與 ADB `5037` 全數未動）。

---

## 一、各候選路線最終裁決（GO / PAUSE / RETIRE）

| 候選項目 | 最終判定 | 部署狀態 | 關鍵實測依據 |
|---|---|---|---|
| **`PRoot-fast9` (`fast9-combined`, patches `01`–`09`)** | **GO（推薦升級候選，待授權部署）** | **尚未部署現役**（僅完成 `--dry-run` 與模擬目標完整部署／回退循環） | Step 1 `mp_storm` **-22.0%**（9/9，p=0.004）、`electron_multi_agent` 內圈 **-13.5%**（8/9，p=0.039）；Step 5 6 配對 ABBA 複合工作站實測：Chromium 153 啟動 **-7.92%**（6/6，p=0.0312）、Tracer CPU **-11.20%**（6/6，p=0.0312）、總牆鐘 **-2.24%**（6/6，p=0.0312）、181.1 s 連續壓測完成 82 批零殘留；Phase 2 Vulkan Turnip 提交內圈 **2.04×**、1080p 渲染 **1.64×**；35/35 回歸全過。 |
| **`PRoot-fast10`（patches `10`–`11`：PID Hash + talloc）** | **RETIRE（不納入正式版，保留補丁與證據）** | **未部署** | Step 1 9 配對檢定顯示相對 `fast9-combined` 無顯著加速（`mp_storm` p=0.51；`electron_multi_agent` 內圈反偏慢 +2.8%～+5.2%、`talloc-only` 牆鐘僅 1/9 勝且 p=0.039 較慢）。依計畫要求保留補丁與原始 JSON 供後續研究，不合入部署候選。 |
| **`Native Hybrid`（`f8-hybrid-daemon.py` + `f8-hybrid-run`）** | **PAUSE / 條件式保留（僅限重型單次呼叫或常駐後端，禁止全域包裝短 CLI）** | **未部署現役** | Step 2 28/28 測試通過、90 s Soak（5,595 ops、669/669 cancel-kill、0 洩漏）通過；但 9 配對 A/B 實測短 CLI 逐次呼叫有反效果（`zstd_jq_5x` **0.47×**、`trivial_jq_50x` **0.62×**、`git_ops_20x` **1.00×**）。Step 5 驗證**單次重型 `python3` 全樹掃描**可達 **1.89×**（`-46.9%`，5/5 勝，p=0.0625），故僅保留給重型單次腳本或常駐型原生 Agent 後端（Unix socket `41 µs` p50）。 |
| **`Mesa 27.0.0-devel`（Noble ARM64）** | **RETIRE（維持現役 Mesa 26.0.6 `/opt/mesa-kgsl`）** | **未部署** | Step 4 5 配對隔離對照顯示 5 項 GPU 工作負載均無統計顯著收益（`sign_p >= 0.375`）；GL/Zink 因連結 `libLLVM.so.20.1` 造成每行程 PSS 暴增 **+62 MB**（1.1–1.4 MB → 63.6–64.1 MB）；WebGPU 仍因 `/dev/dri` SELinux `EACCES` 退回 SwiftShader。 |
| **`Sprout 0.6.1`** | **RETIRE / 旁線凍結（Phase 2 已結案）** | **未部署** | `Node v24` `uv__close` SIGABRT（`rc=134`）、Chromium 153 `headless-shell` 逾時，且 Vulkan GPU 優勢已被 `fast9` `ioctl` BPF 追平。 |

---

## 二、`fast9-combined` 相較 `fast8` 實測量化總表

### 2.1 Step 1 收斂（9 配對無量化實測，[`STAGE5-PHASE3-CONVERGE-FAST9-10-20261126.md`](STAGE5-PHASE3-CONVERGE-FAST9-10-20261126.md)）
- **`mp_storm`（64 子行程 × 1500 syscalls）**：牆鐘中位數配對差 **`-22.0%`**（9/9 勝，雙尾符號檢定 `p = 0.004`）。
- **`electron_multi_agent`（2× Electron 44.9.1 + 2× Python + 2× Git）**：內圈中位數配對差 **`-13.5%`**（8/9 勝，`p = 0.039`）。

### 2.2 Step 5 真實工作站複合 ABBA 長時壓測（6 配對 = 3 ABBA 循環，單調時鐘 + 事件驅動 `p.wait()`）
負載組合：Chromium 153 Playwright 3 分頁（`libnopci.so`，每分頁 60 幀 `rAF` + 5 次點擊 RTT）＋ 2× Electron 44.9.1 ＋ 2× Python AI Agent ＋ 2× Git CLI 併發（[`step5-workstation-abba.json`](stage5-step5-20261126/step5-workstation-abba.json)）：

| 指標 | `fast8` 中位數 (IQR) | `fast9-combined` 中位數 (IQR) | 逐配對改善 % | 勝場 (`fast9` 勝) | 雙尾 `sign_p` |
|---|---:|---:|---:|---:|---:|
| **複合批次牆鐘 (`wall_ms`)** | `2276.30 ms` (5.06) | **`2223.32 ms`** (1.99) | **`-2.24%`** | **6/6** | **0.0312** |
| **工作負載內圈 (`inner_total_ms`)** | `2176.54 ms` (13.70) | **`2134.20 ms`** (23.47) | **`-2.22%`** | **6/6** | **0.0312** |
| **PRoot Tracer CPU (`tracer_cpu_ms`)** | `540.00 ms` (15.00) | **`470.00 ms`** (15.00) | **`-11.20%`** | **6/6** | **0.0312** |
| **Chromium 153 啟動延遲 (`launch_ms`)** | `185.28 ms` (14.26) | **`165.53 ms`** (5.98) | **`-7.92%`** | **6/6** | **0.0312** |
| **整樹峰值 PSS (`peak_pss_mb`)** | `323.60 MB` (1.63) | **`302.60 MB`** (0.83) | `-6.69%` | 5/6 | 0.2188 |
| **Chromium `rAF` 幀時間 (`p50`/`p95`/`p99`)** | `16.7 / 16.7 / 16.8 ms` | `16.7 / 16.7 / 16.8 ms` | `0.0%`（60Hz vsync 鎖定） | — | — |
| **Chromium 掉幀 (`>20 ms` / `>33.3 ms`)** | `0 / 0`（總計 1,080 幀） | `0 / 0`（總計 1,080 幀） | 0 掉幀 | — | — |
| **操作點擊 RTT (`click_p50` / `click_p95`)** | `33.96 / 85.67 ms` | `33.72 / 84.34 ms` | `-0.62%` / `-3.45%` | 3/6 / 4/6 | 1.0 / 0.6875 |
| **Voluntary Context Switches** | `5,439–5,749` | `4,424–4,841` | **約 -15%**（觀察區間） | — | — |
| **系統剩餘可用記憶體最低 (`mem_avail_min`)** | `2838.2 MB` | `2827.4 MB` | — | — | — |
| **最大樹 FD / 執行緒數 / 孤兒 PID** | `284` / `88–90` / **`0`** | `285–289` / `87–90` / **`0`** | 0 洩漏 / 0 孤兒 | — | — |

- **為何總牆鐘只差 `-2.24%` 而非更大？**：Playwright 內建 60 幀 `requestAnimationFrame` 受 60 Hz vsync 固定佔去 ~`1,000 ms` 牆鐘；扣除該固定等待後，實際與 syscall/行程管理相關的 **Chromium 啟動縮短 7.92%、Tracer CPU 下降 11.20%、自願上下文切換降 ~15%**，且完全消除了舊量測腳本 `time.sleep(0.2)` 的 200 ms 階梯量化誤差。
- **桌面與多 AI Agent 體感收益（已實測 vs 推估區分）**：
  - **已實測**：多程序併發下 PRoot 追蹤器 CPU 稅降低 **11.2%**、Chromium 冷啟動縮短 **~20 ms（-7.92%）**、IOCTL/檔案重負載（`ioctl_hot -98.6%`、`fileio -26.9%`、`mp_storm -22.0%`）與 Vulkan 指令提交（Phase 2 `2.04×`）顯著加速；`rAF` 與互動點擊未出現任何卡頓惡化（0 掉幀）。
  - **推估（未直接於 GUI X11 `:1` 長期量測）**：搭配既已現役的 `f8-shard` v2（Electron 與終端各自獨立 tracer），日常開啟多支 AI Agent 與瀏覽器分頁時 PRoot tracer CPU 爭搶應可下降約一成，但受限於實體 RAM 與 HyperOS 平衡模式鎖頻（見 §三），重度記憶體換頁卡頓無法單靠 PRoot patch 消除。

### 2.3 `fast9-combined` 181.1 秒連續壓測穩定性（[`step5-soak-timeseries.jsonl`](stage5-step5-20261126/step5-soak-timeseries.jsonl)）
- **吞吐與穩定性**：連續無間斷完成 **82 輪**完整 7 程序工作站併發批次，退出碼 `rc = 0`，**`orphan_pids = 0`**。
- **資源曲線（36 次每 5 秒採樣）**：
  - 整樹 PSS：穩定週期震盪於 `297.9–330.2 MB`（中段 `300.1 MB`，末段 `297.9 MB`，無上升趨勢／無記憶體洩漏）。
  - 系統 `MemAvailable`：`3000.1 MB → 最低 2853.8 MB → 結束 3050.3 MB`（完全平穩）。
  - FD 與執行緒：執行中 `fds max=295`、`threads max=92`，未見累積增長。
  - 溫控與降頻：CPU 真實感測器多數維持 `48.2–64.5 °C`（第 16 樣本曾見單次瞬峰 `95.3 °C` 後立即回落至 `64.5 °C`），GPU `max = 69.1 °C`；`cpu6_max` 全程維持 `2880.0 MHz` 未觸發進一步持續降頻。

---

## 三、Android 宿主效能稽核與瓶頸定位（Step 3）

詳細紀錄：[`STAGE5-PHASE3-STEP3-HOST-AUDIT-20261126.md`](STAGE5-PHASE3-STEP3-HOST-AUDIT-20261126.md)（原始資料：[`stage5-audit-20261126/baseline-daily.log`](stage5-audit-20261126/baseline-daily.log)）。

- **記憶體與 Swap**：`MemTotal = 15,373,988 kB`（14.66 GiB），日常 `MemAvailable` 僅剩 **`2,863,616 kB`（~2.73 GiB）**，`SwapTotal = 16 GiB`（ZRAM）已用 **`9.06 GiB`（56.6%）**。單一 `antigravity` 棧（含 `language_server` + helpers）即佔 **~766 MB PSS**，`hermes` 佔 **~270 MB PSS**。多 Agent + Electron + Chromium 併發時的首要卡頓根因是 **可用 RAM 緊縮引發的 Swap/ZRAM 壓力**。
- **CPU 頻率上限與溫度真相**：
  - `cpu-hw-trip-0/1 = 95000` 是硬體跳脫常數、`sdr0_pa = -273000` 為無感測器讀值，不可當成目前溫度。
  - 真實靜止／審計溫度：`cpu-0/1-*` **`54.8–64.8 °C`**、`gpuss-*` **`49.0–52.9 °C`**、`battery` `34.3 °C`。
  - **重大發現**：目前 `walt` governor 下，`cpu0–5` `scaling_max_freq = 2,745.6 MHz`（硬體上限 `3,628.8 MHz`，鎖在 **75.7%**），`cpu6–7` `scaling_max_freq = 2,880.0 MHz`（硬體上限 `4,608.0 MHz`，鎖在 **62.5%**）。顯示系統處於均衡／溫控節制檔位，並非全速解放。
- **未驗證／待手動補測項目**：
  - 本輪執行時無線 ADB 關閉（`f8-adb-port` 為空，`adb -P 5038 get-state` 離線），且從應用 UID 讀取 `/proc/pressure/*`、`/proc/vmstat`、`/sys/block/zram0/mm_stat` 皆為 `Permission denied`。
  - **後續待測（不阻塞本輪結論）**：請使用者開啟 Android「無線偵錯」並分別切換 **省電 / 均衡 / 效能** 三種系統模式後，手動執行 `android-host-audit-readonly.sh <mode>`（走隔離 `-P 5038`），補齊 ZRAM 真實壓縮率、PSI stall %、LMKD 殺程紀錄及 `max_phantom_processes`（目前可見 UID 程序數 `86 > 32`）實際值。
- **問題分類**：
  1. **可由專案優化**：`fast9-combined` 降 syscall 與 tracer CPU 稅、維持 `f8-shard` 隔離重型前端、限制同時開啟 ≤2 個 Electron 應用、僅對重型單次 `python3`/大倉 `git` 或常駐後端使用 Native Hybrid。
  2. **Android 系統限制**：`/dev/dri` SELinux `EACCES` 封鎖 Chromium ≥145 DRM/GBM 及 Dawn WebGPU；PSI/ZRAM stats 需 ADB shell 權限；Phantom Process 監控門檻；HyperOS 預設平衡檔位鎖定 CPU 上限（`2.75 / 2.88 GHz`）。
  3. **硬體限制**：14.66 GiB 總實體記憶體由 Android 與 PRoot 共用；SoC 散熱上限限制雙 Prime 核長期維持 `4.61 GHz`。

---

## 四、Mesa 27 隔離對照與 Native Hybrid 邊界總結（Step 4 & Step 2）

- **Mesa 26.0.6 vs Mesa 27.0.0-devel**（[`STAGE5-PHASE3-STEP4-MESA27-20261126.md`](STAGE5-PHASE3-STEP4-MESA27-20261126.md)）：
  - 5 項實機 1080p 硬體測試（Vulkan `vk_submit_burst` / `vk_gpu_fill_copy`、Surfaceless EGL `gles3` / `gl46`、Chromium 153 `WebGL2` `ANGLE+Turnip`）全數驗證排除 SwiftShader/llvmpipe；Mesa 27 無任何統計顯著勝出（`p = 0.375–1.0`），GL/Zink 反增 **+62 MB/process PSS**（`libLLVM.so.20.1`），且 Chromium WebGPU 在兩者下均因 `/dev/dri` 權限受限而退回 `google/swiftshader`（`fallback=true`）。
  - **決議**：維持現役 **Mesa 26.0.6（`/opt/mesa-kgsl`）**，不升 Mesa 27。
- **Native Hybrid 保留與禁用邊界**（[`STAGE5-PHASE3-STEP2-HYBRID-20261126.md`](STAGE5-PHASE3-STEP2-HYBRID-20261126.md)）：
  - **保留能力**：`f8-hybrid-daemon.py`（`0600` socket、`SO_PEERCRED`、`SCM_RIGHTS`、`.l2s.*`/保護路徑/symlink 逃逸阻擋、read-only `git` + config 掃描、`pidfd_open` syscall 434 無輪詢等待）＋ `f8-hybrid-run.c` 已驗證 28/28 測試與 90 s Soak PASS。
  - **禁止場景**：**不得**全域接管高頻短命 CLI（`jq`/`zstd`/短 `git` 呼叫反慢 0.47×–1.00×，因 PRoot `fork+execve` 轉發成本大於節省量）。
  - **適用場景**：單次重型 `python3`（Step 5 實測 **1.89×**、`-46.9%`）或常駐型原生 Agent 後端透過 Unix socket（`41 µs` p50）直接通訊。

---

## 五、正式部署與一鍵回退方案（僅完成 `--dry-run` 與模擬驗證）

已於 `src/f8-proot-fast-stage5/deploy/` 建立並驗證兩支腳本（原始驗證日誌：[`stage5-step5-20261126/deploy-dryrun.log`](stage5-step5-20261126/deploy-dryrun.log)）：

1. **[`deploy-proot-candidate.sh`](../../../src/f8-proot-fast-stage5/deploy/deploy-proot-candidate.sh)**
   - 由乾淨 `proot-5.1.107.92.zip` 解壓並嚴格以 `patch -p1 --fuzz=0` 套用 `01`–`09` 補丁，指定 `PROOT_UNBUNDLE_LOADER=<target>/libexec` 與 `-DVERSION="5.1.107.92-fast9"` 原生編譯（修復了早期 stage5 候選二進位內嵌暫存路徑與 `stage5-stats` 字串之隱患）。
   - 嚴格檢查 `strings`（確認內嵌目標 `libexec/loader`、不含 `stage5` 路徑或 `PROOT_SYSCALL_STATS`）、`sha256sum` 與前置 `fast9_regress`。
   - 預設 `--dry-run` 絕不寫入現役目錄；正式覆寫必須顯式傳入 `--apply --confirm-live`。
   - 正式覆寫前自動備份現役 `out8/{bin/proot-fast8,libexec/loader,libexec/loader32,auto/proot-fast8}` 與 `backup.sha256` 至 `~/build/proot-fast/backups/out8-fast8-<TS>/`，原子化替換並於客體內驗證 `dpkg-query`；若部署後驗證失敗，自動觸發 `auto_rollback()` 還原。
2. **[`rollback-to-fast8.sh`](../../../src/f8-proot-fast-stage5/deploy/rollback-to-fast8.sh)**
   - 支援 `--dry-run` 核對備份 SHA256 與 `--apply --confirm-live` 一鍵還原 `fast8` 完整二進位與 `auto/proot-fast8`，並以 `cmp -s` 逐位元組與客體 `dpkg-query` 驗證復原成功。
   - **免換檔即時回退開關維持有效**：`F8_NO_SHARD=1`、`PROOT_STAT_AT_ENTER=0`、`touch ~/.f8-proot-stock`。
3. **本輪驗證實測證據（`deploy-dryrun.log` `rc=0`）**：
   - 現役目標 `--dry-run`：`DRY_RUN_PASS`（產出 `bin/proot-fast8` SHA256 `e12dc41e3caf0178e91027e178b0639ce6c9cffd5ddba1d976447388ec35fd6c`、`loader` `eab6b2135421a2e0268832cf171d877146a9e816d7b060ce425e5017d65f08a6`、`loader32` `91381891fa2627a4573705a754eced936b3ba1159c9f6d041b6472f26189f46a`，`fast9_regress PASS`，未動現役 `out8/`）。
   - 無 `--confirm-live` 防呆：`GUARD_REFUSE_OK`。
   - 模擬目錄（`$STAGE/mock-deploy/out8`）完整部署＋回退：`DEPLOY_PASS`（`dpkg-query` = `1514`）→ `ROLLBACK_DRY_RUN_PASS` → `ROLLBACK_PASS`（`ORIG_HASH = REST_HASH = e401eb6caa126f1e36dbb66d23c55735082af3688dfb1752972dda0146f8267c`，位元組完全還原）；且於修正客體 `PATH` 前之一次實測意外觸發並證實了 `auto_rollback()` 在失敗時會自動還原 `out8`。

---

## 六、全域完整性、Git 狀態與零殘留核對（2026-11-26 20:24）

- **現役檔案完整性（`live.sha256` 6/6 `OK`）**：
  - `/data/data/com.termux/files/home/build/proot-fast/out8/auto/proot-fast8` (`f1c211fd…`)：**OK**
  - `/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8` (`e401eb6c…`)：**OK**
  - `/data/data/com.termux/files/home/build/proot-fast/out8/libexec/loader` (`eab6b213…`)：**OK**
  - `/data/data/com.termux/files/home/build/proot-fast/shard2/shard-daemon.sh` (`8becae04…`)：**OK**
  - `/data/data/com.termux/files/home/build/proot-fast/shard2/shard-run.sh` (`03a24987…`)：**OK**
  - `/usr/local/bin/f8-shard` (`7158e011…`)：**OK**
- **現役 Ubuntu rootfs 核心檔（`ubu-core.sha256` 4/4 `OK`）**：`usr/bin/true`、`usr/lib/aarch64-linux-gnu/libc.so.6`、`etc/os-release`、`bin/sh` 全數 **OK**。
- **現役 Mesa 26.0.6（`/opt/mesa-kgsl` 未修改）**：`libgallium-26.0.6.so` (`a40c1f60…`)、`libvulkan_freedreno.so` (`4a3e0b84…`)、`libEGL_mesa.so.0.0.0` (`333357da…`)。
- **Git 狀態（全數乾淨）**：
  - `src/f8-proot-fast`（`main`）：`ee603b8`（`dirty = 0`）
  - `src/f8-proot-fast-stage5`（`stage5/isolated-fast8-20261126`）：**`5541ef7`**（`dirty = 0`，含 Step 1–5 全部程式與修復：`5b8816d` → `136c25d` → `c458d74` → `e9559ff` → `a3b3710` → `b93a56a` → `5541ef7`）
- **行程與零殘留核對**：
  - 隔離測試與壓測行程殘留：**`stage_left = 0`**。
  - 現役服務正常運作未受影響：`shard-daemon.sh`（PID `17875`）、`termux-x11 com.termux.x11 :1 -legacy-drawing`（PID `26794`）、`xfce4-session`（PID `26878`）。

---

## 七、尚未部署與待授權事項

1. **授權正式部署 `proot-fast9` 至 `out8/`**：若核准升級，需由 Termux 原生端執行（建議配合使用者重開桌面時段）：
   ```bash
   /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/root/projects/GPU加速/src/f8-proot-fast-stage5/deploy/deploy-proot-candidate.sh \
     --apply --confirm-live \
     --regress-bin /data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp/sprout-preflight/home/bench/fast9_regress
   ```
2. **將 `stage5/isolated-fast8-20261126` 已核可變更合入 `src/f8-proot-fast` `main`**：僅合入 daemon/judge 修復、`07`–`09` 補丁、deploy/rollback 腳本與驗證測試（`10`–`11` `fast10` 補丁僅保留於研究紀錄或獨立分支，不作為正式啟用預設）。
3. **選擇性補測**：開啟無線偵錯後以 `-P 5038` 執行 `android-host-audit-readonly.sh <power_mode>` 收集三電源模式對照與 PSI/ZRAM `mm_stat`/Phantom Process 精確讀值。
