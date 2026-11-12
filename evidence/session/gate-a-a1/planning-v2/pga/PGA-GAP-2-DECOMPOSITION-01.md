# PGA-GAP-2 第 2 步：同步 EXA 延遲拆解（第一輪，2026-09-23）

> 狀態：**描述性量測，每模式 2 次擷取**（G：g-02、g-03；C：c-01、c-02）。下列結論的強度依標示。不是 qualification。

## 來源

| 項目 | 值 |
|---|---|
| 產品 | `83d45a9`（已安裝，APK `f4c98b8a…230f`） |
| 擷取 | `p2-pga-rca/runtime-83d45a9/opstream-g-02`（G：`TERMUX_X11_GATEA_PROTO=1`）、`opstream-c-01`（C：`TERMUX_X11_DISABLE_EXA_GPU=1`） |
| 無效擷取 | `opstream-g-01` INVALID（runner 找錯執行緒），凍結 |
| 工具 | fork `tests/pga/p_opstream.c`、`opstream_decompose.py`（efa9d4b）、`run-opstream-trace.sh` |
| 追蹤 | `atrace sched sync gfx`，trace_clock=boot，每 CPU 24 MB，overrun 0、dropped 0 |
| 顯示 | 內建螢幕 1200×2608 @ 120 Hz（一幀 8.33 ms），X root 1200×2191 |
| Stable | 兩次擷取前後 pid 20457 未變 |

## 執行緒身分（由追蹤紀錄判定，不是猜的）

- X dix 執行緒：X3 程序內被 client 叫醒最多的那條（G：14893，687 次）。X3 的 thread-group leader 是 Android Looper（跑 Choreographer 回呼），**不是** dix。
- renderer：Activity 程序（com.waydefu.x11gpu）內被 X 叫醒最多的那條，`Thread-7`（G：15177，1800 次）。
  → **X→renderer 是跨程序交接。** `pthread_setname_np("LorieRendererThread")` 超過 15 字元失敗，所以名稱是 Java 的 `Thread-7`。

## 總延遲（client 端，單一操作 + 一次 round trip，p50）

| 操作（間隔） | G | C |
|---|---|---|
| nop（5 ms） | 0.22 ms | 0.21 ms |
| solid 64（5 ms） | 3.32 ms | 0.35 ms |
| copy_pix 64（5 ms） | 3.12 ms | 0.34 ms |
| over_argb 64（5 ms，Gate A 直通） | 3.58 ms | 0.13 ms |
| solid 64（120 ms，GPU 可閒置） | **9.39 ms** | 0.38 ms |
| solid 64 burst16（5 ms） | 12.42 ms | 0.61 ms |
| solid 1024（5 ms） | 3.06 ms | 0.62 ms |

## 拆解（G，solid 64，間隔 5 ms）

典型一筆（op 51，2.8 ms，完整時間線見分析輸出）：

| 段 | 時間 | 內容 |
|---|---|---|
| X 處理與發佈 | ~0.15 ms | client 叫醒 X，X 準備、發佈佇列、signal |
| **等 renderer 來拿** | **~1.56 ms** | renderer 不在等那個條件變數（在收尾前一幀的 swap／fence），X 的 signal 叫不醒它；X 以 `usleep(200)` 輪詢，實際每 ~280 µs 醒一次 |
| renderer 送出 | ~0.33 ms | 建 kgsl fence、送出 GPU 工作 |
| GPU 執行 + 完成回報 | ~0.27 ms | `kgsl_hwsched` 喚醒 |
| renderer 發佈 + 寫 log | ~0.11 ms | 每筆完成都寫一次 logd |
| X 看到完成、回覆 | ~0.14 ms | |

全相位統計（200 筆）：X 直接叫醒 renderer 只有 23 筆；其餘在 X 開始處理時 renderer 為 睡眠 139、執行中 43、可執行 14。
renderer 真正被 GPU 等待卡住的時間 p50 0.23 ms、p90 2.8 ms；renderer CPU p50 0.5 ms。

## 結論與強度

1. **GPU 本身不是主因**（強：多數相位 GPU 等待 p50 < 0.5 ms，C 模式整體 0.1–0.6 ms）。
2. **最大一段是「renderer 沒來拿工作」**（強：時間線直接可見；X 的 signal 只叫得醒在等條件變數的 renderer）。
   原始碼 `renderer.cpp:2493-2499` 刻意在有 GPU 工作時畫一整幀（共用上鎖與 fence），完成要等這一幀。
3. **完成被綁在畫面節奏上**（部分支持，未證明）：G 間隔 5 ms 相位的操作起點間隔中位數 8.25–8.78 ms ≈ 一幀，
   但只有 21–35% 落在一幀整數倍 ±0.25 ms 內；C 模式無此現象。
4. **GPU 從閒置醒來很貴**（單次擷取，需重現）：間隔 120 ms 時 GPU 等待 p50 7.65 ms、總延遲 9.4 ms。零星的桌面操作每一陣的第一筆都可能付這筆。
5. **連發不 pipeline**：16 筆連發 12.4 ms（≈ 0.78 ms/筆），renderer 其他睡眠 p50 7.7 ms。

## 對架構的意涵（尚未實作、尚未實測）

- 把 GPU EXA 完成從 renderer 的畫面迴圈拆開（獨立提交路徑，或在 X 程序內自有 GL context，省去跨程序交接）。
- Done* 不同步等：每個 pixmap 記錄 fence，CPU 真的要讀時才等（非同步 EXA）。
- X 端以事件喚醒取代 `usleep(200)` 輪詢；完成路徑不寫 log。
- GPU 閒置喚醒成本需要納入路由：小而零星的操作可能留在 CPU 較好。

## 重現（g-03 / c-02，同一產品、同一 runner）

| 項目 | 第一次 | 重現 |
|---|---|---|
| G solid 64 | 3.32 ms | 3.17 ms |
| G copy_pix 64 | 3.12 ms | 2.15 ms |
| G over_argb 64 | 3.58 ms | 1.62 ms（X 直接叫醒 renderer 34 → 116 筆） |
| G 間隔 120 ms | 9.39 ms（GPU 等 7.65） | 13.15 ms（GPU 等 10.92） |
| C 各項 | 0.13–0.62 ms | 0.28–0.64 ms |

依「X 開始處理時 renderer 是否閒著」分組（總延遲 p50）：

| 擷取 · 操作 | 直接交接（renderer 閒） | renderer 忙 |
|---|---|---|
| g-02 solid 64 | 7.42 ms（n=23） | 3.27 ms（n=176） |
| g-02 copy_pix 64 | 1.26 ms（n=32） | 3.19 ms（n=168） |
| g-02 over_argb 64 | 9.34 ms（n=34） | 3.43 ms（n=165） |
| g-02 solid 1024 | 2.73 ms（n=38） | 3.19 ms（n=61） |
| g-03 solid 64 | 1.70 ms（n=21） | 3.18 ms（n=179） |
| g-03 copy_pix 64 | 1.23 ms（n=86） | 2.80 ms（n=113） |
| g-03 over_argb 64 | 1.37 ms（n=116） | 2.73 ms（n=84） |
| g-03 solid 1024 | 2.44 ms（n=30） | 3.19 ms（n=70） |

- 8 組中 6 組：renderer 閒著時 1.2–1.7 ms，忙時 2.7–3.3 ms。**例外**是 g-02 的 solid 64 與 over_argb：直接交接反而更慢（7.4 / 9.3 ms），
  推測是 renderer 閒置夠久時 GPU 也進入閒置、付了喚醒成本——**未證明**。
- 結論 4（GPU 閒置喚醒很貴）**已重現**：7.65 / 10.92 ms。
- **最關鍵的一點**：即使在最好的情況（renderer 閒著、GPU 醒著），同步等待的 GPU 操作也要 1.2 ms 以上，C 模式只要 0.13–0.6 ms。
  **只修交接方式，小操作仍然不會比 CPU 快**；GPU 路徑要有淨效益，X 必須不等（非同步完成），並把 GPU 閒置喚醒成本排除在互動路徑之外。

## 下一步

- 最小原型：非同步完成（X 不在 Done* 等），判準先凍結。
