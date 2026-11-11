# PGA-GAP-2：非同步 legacy EXA（solid / copy）原型設計 — 2026-09-23

> 依據：`PGA-GAP-2-DECOMPOSITION-01.md`。同步等待即使在最好情況也要 ≥1.2 ms，CPU 0.13–0.6 ms；
> 只修交接贏不了 CPU，X 必須不在 Done* 等。本文件在**實作與量測之前**凍結範圍、語意與判準。

## 1. 範圍

| 路徑 | 本原型 |
|---|---|
| EXA Solid（PrepareSolid/Solid/DoneSolid） | **非同步** |
| EXA Copy（PrepareCopy/Copy/DoneCopy） | **非同步** |
| EXA Composite（含 Gate A direct / staging） | 不變（仍同步）；僅在入口補「先清空待修補」 |
| Present copy | 不變（仍同步）；僅在入口補「先清空待修補」 |
| renderer（Activity 程序） | 不變 |

開關：X 環境變數 `TERMUX_X11_EXA_ASYNC=1`。**未設定時所有新程式碼都不執行，行為與 83d45a9 相同**，
所以同一個 APK 可以做 G-sync / G-async / C 三方比較，production 預設不變。

## 2. 語意（EXA 原生模型）

EXA 本來就是非同步設計：加速操作後 `exaMarkSync`，CPU 存取前 `exaWaitSync → WaitMarker`。
lorie 把 `WaitMarker` 設成空函式、改在每個 Done* 同步等。本原型改為：

1. **Done\* 不等 GPU。** 每筆已排程操作記入 in-flight 表 `{serial, srcBuffer, dstBuffer|root}`，
   原本在 Done* 做的 ack（`gpuCopyPendingDec` + `LorieBuffer_release`）延到 **reap**：`completedSerial ≥ serial` 時才做。
   in-flight 表存的是排程當下 acquire 的那個 `LorieBuffer*`，不是 pixmap（pixmap 可能先被刪除）。
2. **CPU 存取前一定等。** 等待放在 `loriePrepareAccess`（EXA 核心與 lorie 內部的 CPU 存取都經過它）：
   該 pixmap 有進行中的 GPU 寫入／讀取（buffer 的 `gpuCopyPending`、root 的 `rootGpuCopyPending`）或有待修補 → 等全部 in-flight 完成並 reap。
3. **depth < 32 的 X byte 修補延後。** RGBX 目標會把 X byte 寫成 0xFF，同步版在 DoneSolid 等完後用 CPU 修回 `fg>>24`。
   X byte 只有 CPU 看得到（顯示與 GPU 取樣都忽略它），所以把修補框記在 pixmap 私有資料，**CPU 存取時（等完 GPU 之後）才套用**。
   上限 32 框（與同步版相同）；超過 → 立即 drain 並用同步版的 union 修補。
4. **順序保證（最終位元組必須與同步版一致）。** 下列情況先 drain 並套用待修補，再排新工作：
   - copy 的 src 或 dst 有待修補；
   - solid 的 dst 有待修補且 X byte 值不同；
   - 任何 composite / present copy 入口、`RRScreenSetSize`、`CloseScreen`，只要有任何 pixmap 有待修補或 in-flight 非空。
5. **生命週期。** `DestroyPixmap`：buffer 仍有進行中的 GPU 操作 → 先 drain 再註銷（否則 renderer 處理佇列時找不到 buffer）。
   待修補清單隨 pixmap 一起丟棄（像素已不存在）。
6. **佇列滿。** 排程失敗且 in-flight 非空 → 等最舊的一筆、reap、重試一次；仍失敗 → CPU fallback（其 PrepareAccess 會 drain）。
7. **等待失敗**（renderer 消失／逾時）：與同步版相同處理——記錄錯誤、照樣 ack，不留懸空引用。
8. Reap 時機：每次排程、每個 Done*、每次 PrepareAccess（不阻塞的 reap）。

## 3. 風險與不做的事

- 不動 renderer 的畫面迴圈耦合（完成仍要等下一幀）；那只影響「多久看得到」，不再卡住 X。
- 不動 Gate A lease／fence／ownership 語意；composite 仍在 DoneComposite 同步等自己的 serial（FIFO 佇列，會隱含等到前面的非同步操作）。
- 新增的引用延長（in-flight 期間 buffer 不釋放）可能使記憶體峰值略增；以 mem-guard 與 `activity.maps_count` 觀察。

## 4. 凍結判準（在任何 async 裝置資料之前）

**正確性（必要，不通過即 ASYNC_PROTO_FAIL_CORRECTNESS）**
- 新 verifier `p_async_oracle`：隨機序列的 solid / copy（window↔pixmap、pixmap↔pixmap、刪除剛被讀的 pixmap、穿插 GetImage），
  client 端維護軟體參考模型，每次 GetImage 必須**逐位元組相等**（含 depth 24 的 X byte 依 CPU 語意）。
  - 在 Xvfb 必須全綠（驗證參考模型）；對參考模型植入錯誤的突變必須變紅（驗證 verifier 會失敗）。
  - 裝置上 C、G-sync、G-async 三種模式都必須全綠。
- 既有 oracle V3（`tests/oracle`）在 G-async 下仍須 ORACLE_PASS（Gate A 直通路徑未被破壞）。

**效能（描述 + 一條凍結的改善判準）**
- 工具：同一套 `p_opstream` + atrace + `run-opstream-trace.sh`，模式 G-async 為新增 MODE。
- **ASYNC_LATENCY_IMPROVED** 當且僅當：G-async 的 client 延遲 p50 在 `solid 64 gap5` 與 `copy_pix 64 gap5`
  **兩次擷取都** ≤ 同一輪 G-sync p50 的 50%。否則 NOT_IMPROVED。
- 與 C 的比較只描述，不下「比 CPU 快」的結論，除非另有凍結判準與實測。
- 另記錄：X 程序 CPU、renderer CPU、每操作 GPU 等待（atrace）、mem-guard 峰值。

## 5. 產物流程

fork 新 branch（基於 efa9d4b）→ 實作 → host build 檢查 → fork CI → artifact QUALIFIED（sha／Build ID 綁定）
→ 只裝到 `com.waydefu.x11gpu` → 依 §4 執行。Stable `:1` 不碰。

## 修訂 1（2026-09-23，任何 async 裝置資料產生之前）

§4 正確性判準的「含 depth 24 的 X byte 依 CPU 語意」改為下列，理由：同步版的 GPU copy 以 RGBX 為目標，
X byte 很可能被寫成 0xFF 而不修補——這是 83d45a9 既有行為，若要求 CPU 語意，G-sync 自己就會失敗，
判準便無法分辨「非同步引入的錯誤」。本原型要守的不變量是**非同步與同步逐位元組相同**：

- RGB（depth 24 的低 24 位元、depth 32 的全部 32 位元）：C、G-sync、G-async 每次 GetImage 都必須與 client 端參考模型完全相等。
- depth 24 的 X byte：G-async 的所有 GetImage X byte 雜湊必須**等於**同一 seed 的 G-sync 雜湊；C 的 X byte 另行描述，不作判準。
- 參考模型只在 Xvfb 驗證（必須全綠），並以突變（模型略過某一類操作）驗證 verifier 會變紅。

## 結果 · 0245ff3（CI 35884494432）— **ASYNC_PROTO_FAIL_CORRECTNESS**（凍結，不重判）

- p_async_oracle seed 11 / 4000 ops：C 0/614 錯（xdigest 與 Xvfb 相同 `908bc344…`）；**G 496/614、GA 497/614 RGB 錯**。
- 依 §4 判準（三模式皆須全綠）為 FAIL。第一個錯誤在 G 與 GA 完全相同（depth 32 pixmap 讀回 00000000），
  p_depth_probe 證實是**既有缺陷 PGA-GAP-4**（同步版本身），不是非同步引入的；但判準不因此放寬。
- 修正 PGA-GAP-4 後（b3e5d54）以新 artifact 重跑三模式；0245ff3 的結果保留原判。
- 非同步與同步的 X byte 雜湊（G `16bf8722…` / GA `65f88b29…`）在同步版本身錯誤的情況下無法判讀，留待新 artifact。

## 結果 · b3e5d54（CI 35886655107）— 只跑 probe，PGA-GAP-4 修補假設被推翻（凍結）

- p_depth_probe G / GA 仍 16 處錯（depth 32 讀回 00000000）。見 V2-PGA-GAP-INVENTORY PGA-GAP-4。

## 結果 · d1c86dd（CI 35887541569）— G 通過、**GA ASYNC_PROTO_FAIL_CORRECTNESS**（凍結，不重判）

| seed | G | GA | C |
|---|---|---|---|
| 11 | 0/614 | **16/614** | 0/614 |
| 12 | 0/614 | **11/614** | 0/614 |

- p_depth_probe G / GA：0 處錯 → **PGA-GAP-4 修補（depth 32 目的地走 CPU）在裝置上驗證**，同步 GPU 路徑 RGB 正確。
- GA 與 G 的 X byte 雜湊相同（seed 11 `fc22db73…`、seed 12 `6a0b5095…`）：X byte 延後修補的語意與同步一致。
- GA 的 RGB 錯誤 RCA（主機重放 seed 11，`--watch`）：op #251 非同步 GPU copy **從 root 讀** win(69,6)→p24a；
  op #253 CPU 的 Render Src 寫入 win(70,99)；loriePrepareAccess 對 root 只看 `rootGpuCopyPending`（只計入**寫** root 的操作），
  沒看 root buffer 自己的 `gpuCopyPending`（**讀** root 的操作計在這裡），CPU 沒等就覆寫了尚未被 GPU 讀取的來源。
- 修正：11b3b79（root 兩個計數器都檢查）。以新 artifact 重跑 2 seed × 3 模式。

## 結果 · 11b3b79（CI 35888747835）— **正確性 PASS、ASYNC_LATENCY_IMPROVED**

**正確性（§4 + 修訂 1）— 全部達成**

| 檢查 | 結果 |
|---|---|
| p_async_oracle seed 11 / 12，G · GA · C | RGB 錯誤 0 / 0 / 0（兩個 seed 皆是），共 3684 次 GetImage |
| GA X byte 雜湊 = G | seed 11 `fc22db73…` = `fc22db73…`；seed 12 `6a0b5095…` = `6a0b5095…` |
| p_depth_probe G / GA | 0 / 0 處錯 |
| Gate A oracle V3（`run-oracle-11b3b79.sh`，ORACLE_ASYNC=1） | **ORACLE_PASS**：1298/1298 direct exact、36 fresh、7 negative、lifecycle 平衡、無 fatal |

注意：oracle V3 以 composite 為主，async 只推入 2 筆（counters），它證明的是「原型沒破壞 Gate A」，async 本身的正確性由 p_async_oracle 證明。

**效能（凍結判準：GA p50 ≤ G p50 × 50%，solid 64 與 copy_pix 64，兩組配對皆須成立）→ ASYNC_LATENCY_IMPROVED**

| 配對 | solid 64 G → GA | copy_pix 64 G → GA |
|---|---|---|
| g-01 / ga-01 | 1.389 → 0.340 ms（0.24） | 1.350 → 0.316 ms（0.23） |
| g-02 / ga-02 | 1.424 → 0.287 ms（0.20） | 1.510 → 0.284 ms（0.19） |

描述（不下結論）：GA 小操作約等於 C（0.34 / 0.36 ms）；solid 1024 GA 0.26–0.29 ms、C 0.66 ms；GPU 可閒置的 gap120 由 14 ms 降到 0.43–0.50 ms；
burst16 GA 2.1–2.3 ms 仍約 C 的 3 倍（佇列容量 8 的推測，未證明）；X 程序 CPU 時間各模式 0.8–1.2 s，未見明顯差異。
over_argb（Gate A，仍同步）GA-02 3.43 ms 高於 G：該相位 X 直接喚醒 renderer 僅 37/200，與 83d45a9 g-02（3.58 ms、34/200）同型，
屬同步 composite 被畫面節奏耦合的既有變異（有前例、未證明）。

**限制**：以上是 client 端延遲（X 不再卡住），**不是**畫面上看到結果的延遲——GPU 結果仍在 renderer 下一幀才顯示。XFCE 流暢度尚未量測。
