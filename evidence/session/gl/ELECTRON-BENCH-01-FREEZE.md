# ELECTRON-BENCH-01 — Cursor 開 GPU（V2）對現行設定（V0）：判準凍結

**狀態：FROZEN（2026-09-24，使用者：「你判斷就好，開始吧」）。**門檻照草稿。凍結時沒有任何 V0／V2 對照的互動量測資料；
乾跑（只有 V0、不計分）暴露的工具問題已在受判資料之前修正，記在文末「凍結後、資料前的修正」。

## 揭露：寫判準時已知的資料
- `ELECTRON-GPU-PROBE-RESULT.md`：V2 由 Chromium 回報 Turnip Adreno 840、合成／光柵 enabled；GPU 程序啟動後第 30–50 s 閒置 CPU：
  V0 0.35 s／20 s、V2 2.92 s／20 s（描述；該期間使用者按掉 Cursor 告警）。沒有任何捲動／打字資料。
- GL-BENCH-02 教訓：CPU 驅動重複波動可達 1.6×，「固定倍數 ≫ 雜訊」不可假設 → 本次門檻同時綁 A/A 實測波動。

## 問題
在實驗版 X `:3` 上，Cursor 用 V2（ANGLE→Vulkan→Turnip，加 libnopci 攔截器與 `/opt/mesa-kgsl`）時，
**捲動與打字的總 CPU 是否明顯較低、畫面節奏不變差、閒置不空轉、畫面正確？**範圍：Cursor 單一視窗、下列固定腳本；不代表其他程式。

## 組態
| 代號 | 參數 |
|---|---|
| **V0** | 使用者日常參數：`--no-sandbox --disable-gpu-sandbox --disable-gpu --disable-dev-shm-usage --ozone-platform=x11` |
| **V2** | 同上但拿掉 `--disable-gpu`，加 `--ignore-gpu-blocklist --use-gl=angle --use-angle=vulkan --enable-features=Vulkan,VulkanFromANGLE,DefaultANGLEVulkan`；環境加 `LD_PRELOAD=libnopci.so` 與 mesa-kgsl 變數（`MESA-KGSL-UBUNTU-BUILD-01.md`） |

**兩者共同的隔離**（probe 暴露的問題）：
- 獨立 `HOME=/root/build/electron-bench/home-<run>`：讀不到使用者的 `~/.cursor/mcp.json`，**不啟動 Serena／Firebase MCP**；
- 獨立 D-Bus（`dbus-run-session`）：告警、金鑰圈請求不會跑到日常桌面；
- 全新 `--user-data-dir`、同一份唯讀測試檔（固定內容的長 C++ 原始檔，SHA256 記錄）、同一視窗大小（Cursor 預設視窗；乾跑實測 1000×800 CSS px，兩組相同）。

## 負載（每次執行，全部經 DevTools 協定自動操作，不需要人碰手機）
1. 啟動後等 **60 s** 讓載入結束（不計分）。
2. **閒置 60 s**：量 CPU。
3. **捲動 30 s**：編輯器每 100 ms 送一次翻頁鍵，每 50 次換方向（PageDown 50 次、PageUp 50 次，循環），共 300 次。
4. **打字 30 s**：每 50 ms 輸入一個字元（固定字串循環），共 600 字元（不存檔）。
- 每個階段量：Cursor 整個程序群組的 CPU（所有子程序 utime+stime）＋ X3 CPU ＋ Activity CPU（adb）；
  renderer 內以 `requestAnimationFrame` 記錄每幀間隔（p50、p95、>50 ms 次數）。
- 結束時 `Page.captureScreenshot` 一張；GPU 程序 PID 與退出碼全程記錄。

## 指標與判準（兩次重複都要成立）
令 `S = 捲動＋打字兩階段的總 CPU 秒數`（Cursor 群組＋X3）。
- **A/A 波動**：rep 01 依序 `V0 → V2 → V0'`，rep 02 依序 `V2 → V0 → V2'`。
  `noise = max(|S(V0)−S(V0')|/S(V0) in rep01, |S(V2)−S(V2')|/S(V2) in rep02)`。
- **CPU_BETTER**：每次重複 `S(V2) ≤ S(V0) × (1 − max(0.20, 2 × noise))`（V0 與 V2 各取該 rep 兩次的平均）。
- **FRAMES_NOT_WORSE**：每次重複捲動階段 `p95_frame(V2) ≤ p95_frame(V0) × 1.10`，且 `>50 ms 次數(V2) ≤ >50 ms 次數(V0) + 3`。
- **IDLE_OK**：每次重複閒置階段 Cursor 群組＋X3 的 CPU `V2 ≤ V0 + 0.05 核`（擋「空轉」）。
- **CORRECT**：V2 的截圖不是單色（最多顏色佔比 < 95%，相異顏色 ≥ 16）；V2 的 GPU 程序整段沒有非收尾造成的退出。

判決：
- `ELECTRON_GPU_BENEFIT`：四條在兩次重複都成立。
- `ELECTRON_GPU_NO_BENEFIT`：有效資料下 CPU_BETTER、FRAMES_NOT_WORSE 或 IDLE_OK 任一不成立（註明哪一條）。
- `ELECTRON_GPU_FAIL`：CORRECT 不成立（黑畫面、GPU 程序崩潰）——這是真失敗，不是 INVALID。
- `ELECTRON_INVALID`：有效性不成立（下一節），沒有資訊。

## 有效性（任一不成立 → 該次執行 INVALID）
- 觸控：全程錄 `/dev/input/event7`，有任何 EV_KEY／EV_ABS 就 INVALID（沿用 GL-BENCH 的偵測器與自我測試）。
- 每階段前後實驗版在前景、螢幕亮、無鎖屏；thermal status 開跑前為 0（最多等 300 s）。
- V2 的 Chromium 自我回報必須是 Turnip Adreno 840 且 `gpu_compositing=enabled`；V0 必須是 `Disabled`。**身分不符 = INVALID。**
- DevTools 自動操作全部送達（翻頁鍵 300 次、字元 600 個的確認回應）**而且確實生效**：開始前編輯器輸入元素有焦點；
  第 50 次翻頁後第一行不是 1；打完字後編輯器看得到輸入的字串。rAF 樣本數 > 0。
- runner 層級：Stable 前後不變、X3 未被追蹤、root 1200×2416、mem-guard 未觸發、APK 相符、結束後無殘留程序。

## 工具驗證（受判資料之前）
- 判定器合成案例：V2＝V0（應為 NO_BENEFIT，**必須紅**）、V2 黑畫面（FAIL）、身分不符（INVALID）、觸控（INVALID）、明顯達標（BENEFIT）、
  noise 很大時 20% 改善不夠（NO_BENEFIT）。
- 自動操作乾跑：在 `:3` 上用 V0 跑一次完整腳本，只檢查操作都有送達、量測欄位都不是 null，**不看數字、不計分**。

## 不在範圍內
其他 Electron 程式（Claude／Codex／Hermes 之後各自驗證）、Stable `:1`、長時間穩定性、耗電。

## 凍結後、資料前的修正（乾跑 `electron-bench-dryrun-01`，只有 V0，不計分）
1. 我的合成點擊把焦點從編輯器移走，300 次翻頁與 600 個字元都「確認送達」但沒有作用（第一行仍是 1、字串不可見）。
   → 改為以 JavaScript 對編輯器輸入元素 `focus()`，並把「確實生效」三項加進有效性（上一節）。
2. rAF 記錄器停止後，舊迴圈在下一階段繼續跑（兩階段回報完全相同的幀數 3740）→ 每輪帶世代編號。
3. 視窗大小寫錯（寫成全螢幕 1200×2416，實際 1000×800）→ 改寫為「預設視窗、兩組相同」。
4. 乾跑錄到 36 筆觸控 → 偵測器正常；正式跑期間請使用者不要碰手機。
門檻、指標、組態、順序都沒有改。

## 工具（凍結的版本，乾跑 03 驗證後）
| 檔案 | 位置 | SHA256 |
|---|---|---|
| `electron_bench.sh` | fork `tests/gl/`，commit `a4440fa`（本地，未 push） | `a026a362906e734a21cc6d4643dd7513d4c198046446fd0c5ed5c340b0b4ceec` |
| `electron_bench_drive.mjs` | 同上 | `d7b529e37dd5b7d5b9632c6e6f3bbc8627bab0e8c7fcdc180d2dbbccffd87f13` |
| `electron_bench_judge.py` | 同上；`--selftest` 10/10 SELFTEST_PASS | `86fb5fe2aab5d13a072a6c7eda231c2157e4bc07de6d0416d7fd9b98adc385a8` |
| `libnopci.so` | `/root/build/electron-probe/nopci/` | `0929465a837e7bcedabae6e0b2f210a029466c8cec8fc61fc00567886c18d5f4` |
| 測試檔 `bench.cc`（= Mesa 26.0.6 `tu_device.cc`，4415 行，唯讀） | `/root/build/electron-bench/ws/` | `879dd353e9710ef2886c3bbd1de0f3059016c8e22decd7d896c14af7c59b2e3e` |
| runner | `evidence/session/gl/run-gl-bench.sh`（與 GL-BENCH 相同） | `c5e03c2e16da5b476811d6102e88bd0c576ba55fddefaa736606370b6ce14e16` |

乾跑紀錄：`electron-bench-dryrun-01`（焦點問題）、`-02`（使用者滑掉實驗版 → Gate A `x-hup/6` 設計停機，見 INCIDENT-20260924…，已更正）、
`-03`（所有欄位非 null、焦點 true、第 50 次翻頁第一行 1621、打字可見、無殘留；觸控 357 → 若為正式跑會是 INVALID）。
- 14:00:35 concurrent: user started RCA sessions task_7bdaf674 and task_be769d75 (read-only source analysis) before the formal cells; they share host CPU/memory with the measured runs.
