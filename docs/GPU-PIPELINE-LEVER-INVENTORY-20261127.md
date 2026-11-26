# GPU 管線槓桿盤點（2026-11-27，唯讀）

> 性質：唯讀彙整，未執行任何量測、裝置操作或建置，不重判任何凍結判決。由 Haiku 子代理整理、主代理抽查（`X3-DIRECT-FEAS-RESULT.md:44,56`、`XFCE-NOTEL-01-FREEZE.md:139-140,144`、`PGA-GAP-2-DECOMPOSITION-01.md:28`、`ELECTRON-BENCH-01-RESULT.md:14-19` 數值與原文一致）。重開任何 PAUSED 戰線由使用者決定。

## 結論

渲染管線、記憶體傳輸、CPU↔GPU 同步三個面向都已量測過。剩下能量到的空間很小，而且全部要重開 PAUSED 戰線：

- **X3 上屏複製**是唯一還有實際數字的槓桿：60 fps 全螢幕時，X3 每幀複製約 0.82–1.9 ms，相當於 0.05–0.11 核（`X3-DIRECT-FEAS-RESULT.md:56`）。就算完全零複製，上限也就是這麼多，比閒置的 Cursor（約 0.35 核，`ELECTRON-BENCH-01-RESULT.md:16-19`）還小。
- **小 op 的 GPU 同步路徑**在所有量過的尺寸都比 CPU 慢約 5–28 倍（3.06／0.62 到 3.58／0.13）（solid 64：G 3.32 ms 對 C 0.35 ms，`PGA-GAP-2-DECOMPOSITION-01.md:28`）。把 `usleep(200)` 輪詢換成事件喚醒最多省約 1.56 ms，G 仍剩約 1.0 ms，依然慢於 CPU。
- **已實現的最大 CPU 節省**是關掉 telemetry，約 0.18 核（`XFCE-NOTEL-01-FREEZE.md:144`），已是預設。
- **Electron／XFCE 開 GPU**：`ELECTRON_GPU_NO_BENEFIT`（CPU 比 0.963／0.966，門檻 ≤0.80）；XFCE telemetry 關閉後 `NO_SEPARATION`（`XFCE-NOTEL-01-FREEZE.md:139-140`）。

## 剩餘槓桿（ESTIMATE 皆由已量測數字推得）

| 槓桿 | 收益上限 | 代價／限制 | 會重開 | 量化它需要的單一量測 |
|---|---|---|---|---|
| X3 端 Vulkan GPU 複製取代 CPU 複製 | 每幀省 0.55–1.61 ms CPU，60 fps ≈ 0.03–0.10 核 | GPU 每幀 +1.19 ms（`X3-DIRECT-FEAS-RESULT.md:44`）；120 fps 約佔 14% GPU；需 size+5300 bytes 繞道 | 主線 #3 | `:3` renderer 原型，60／120 fps 記 X3 核數與 GPU 幀時間 |
| X3 複製比 memcpy 慢（0.22–0.64 對 0.28 ns/px） | ≈ 0.06 核（60 fps） | 原因未查；VK 大視窗兩次差近 2 倍 | 主線 #3 (c) | 同 process 比 X3 copy 與 memcpy，記核心與頻率 |
| 客戶端 AHB（modifier 1255）真零複製 | 0.05–0.11 核（60 fps） | 需改 Mesa WSI；09-26 已決定不做 | 主線 #3 | — |
| X→renderer 交接改事件喚醒 | 單 op 最多 −1.56 ms | G 仍 ≈1.0 ms > C 0.13–0.61 ms，對 CPU 無淨收益 | Gate A PGA-GAP-2 | `:3` 替換 `usleep` 重跑 atrace |
| GPU 閒置喚醒（120 ms 間隔首筆 9.39 ms 對 5 ms 間隔 3.32 ms） | 單次 ≈ 6 ms | keep-alive 的 CPU 成本 never measured | Gate A | 間隔 20／60／120／500 ms 掃描 |
| EGL（Zink kopper）上屏修復 | 可用性問題，非 CPU 節省 | `PATH_NOT_PRESENTED`（`GL-PRESENT-03-RESULT.md:12,53`） | 主線 #3 條件式待辦 | EGL 上屏 trace |

## 已證實約為 0 的方向

- Cursor／Electron GPU：`ELECTRON_GPU_NO_BENEFIT`（`ELECTRON-BENCH-01-RESULT.md:1,14-19`）。
- XFCE 2D GPU（telemetry 關閉）：`NO_SEPARATION`（`XFCE-NOTEL-01-FREEZE.md:139-140`）。
- dma-buf 直接匯入 EGL／GLES：`DMABUF_IMPORT_UNAVAILABLE`（`X3-DIRECT-FEAS-RESULT.md:25-26`）。
- 非同步 EXA 端到端（XFCE）：op 層 0.19–0.24× 但 XFCE p99 未改善（`PGA-GAP-2-ASYNC-XFCE-FREEZE.md:44-45`）；尖峰來源（AHB 升級風暴）已由 f592241 尺寸分流消除（`ROUTING_REMOVES_SPIKES`）。

## 未知與風險

- 量測雜訊大：lavapipe A/A 差 1.61×（`GL-BENCH-02-RESULT.md:22,25-27`），X3 VK 大視窗兩次差近 2 倍；新判準必須先處理雜訊再凍結門檻。
- 每像素成本是範圍而非單點；兩處原因未查（VK 0.45 對 0.85 ms、X3 copy 比 memcpy 慢）。
- 本盤點未讀 raw／zst log，未驗證 `:3` 現行狀態，未涵蓋 PRoot／CPU 調度。
