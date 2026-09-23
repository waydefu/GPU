# RCA-XFCE-3 — untraced X3 上 XFCE 仍然 INVALID：產品的同步 EXA GPU 路徑讓 X 變慢

DATE 2026-09-23 · PRODUCT `bfb5769` · FREEZE `XFCE_DESIGN_FROZEN_V3`（manifest 66e37b23，collector 串流化，語意不變）
上游：RCA-XFCE-2（traced X3 是 harness 拓樸問題 → V3 改成 untraced）

## 1. 觸發

```
xfce3-c1-01   凍結 judge → INVALID
              validity  choreo_every_step_ok（8 步失敗：T2/T3 的視窗查找）· choreo_no_step_late（4 步 > 2 s）
              crash     全過（X、Activity、xfce 核心程序 pid 不變；terminal 5/5 exit 0；零 fatal、零 ANR）
              hard      全過（c12..c17 560/560、registry/lease 0、c27=1、generation [1]、一次 GATEA_BIND）
              x3_untraced PASS（TracerPid 0）· screen_awake_throughout PASS · diag_stamps_absent PASS
```

X3 已不被 PRoot 追蹤，視窗仍在 10 s 內找不到。

## 2. 對照實驗（RCA pair，非 baseline，永不與 baseline 合併）

同一個凍結 V3 runner、同一個 workload（C1）、同一台機器，只差 X 的一個環境變數；兩個 arm 都帶
`tests/pga/rca_sampler.py`（每 250 ms 一次 GetInputFocus 往返、每 3 s 一次與 choreo 相同的 xdotool search、
每 5 s 各程序 CPU，含 PRoot tracer）。

```
                              G（凍結設定：PROTO=1，EXA GPU 開）   C（TERMUX_X11_DISABLE_EXA_GPU=1）
凍結 judge                    INVALID（34 步失敗、9 步遲到）        BASELINE_VALID（0 失敗）
X 往返 GetInputFocus（視窗內） p50 8.9  p90 29  p99 181  max 282 ms  p50 1.5  p90 5.9  p99 11.6  max 99 ms
xdotool search                p50 3.7 s  p90 10.4 s  找到 17/25      p50 0.20 s  p90 0.55 s  找到 44/48
CPU（核）                     X 0.55 · PRoot tracer 0.57            X 0.65 · PRoot tracer 0.65
5 s 計數（150 s 視窗）         solid GPU 13032 · copy GPU 10571      全部 0（GPU 路徑關閉）
                              composite prepare_true 2643
                              renderer frames 8733                  renderer frames 2970
Gate A direct（event=5）       整個 run 15 次                        —
```

- harness 可行性已證明：同一個 runner 在 C arm 得到 `BASELINE_VALID`。
- 兩個 arm 的 tracer 負載相當（0.57 / 0.65 核），RCA-XFCE-2 的拓樸因素已排除。
- G 的 X **不是 CPU 飽和**（0.55 核，低於 C 的 0.65）：X 是在等。
- `present copies offloaded` 與 `EXA copies offloaded` 永遠相等，因為兩個計數器在同一個排程函式裡累加
  （`gpuCopyOffloads++` 於 InitOutput.c:1915，EXA copy 經過它）；實際 GPU op 只有 solid、copy、composite 三類，
  每 150 s 約 2.6–2.8 萬個（約 190/s）。
- Gate A direct 在 XFCE 裡幾乎沒被用到（15 次）；延遲來自 Gate A 之前就存在的 legacy EXA GPU offload。
- `rca_sampler` 的 thread-state 取樣在 G arm 有偏差：取樣迴圈會被 xdotool search（G 下每次好幾秒）擋住，
  只在搜尋結束後取樣，會高估閒置。thread state 不當證據；往返與搜尋時間由獨立程序量測，不受影響。

## 3. 原始碼機制（bfb5769）

```
排程   lorieTryScheduleGpuSolid / 共用 copy 排程：寫 gpuCopyQueue、pthread_cond_signal(rendererCond)
等待   lorieExaDoneSolid / DoneCopy / DoneComposite -> lorieGpuCopyWait（InitOutput.c:1946）
       每個 Done 都同步等 completedSerial，usleep(200) 輪詢；所以同一個 client 的下一個 request、
       以及所有其他 client，都排在這個等待後面
renderer  有 pending op 且 surface 可用、不在 waitForNextFrame -> redrawLocked()（整張重畫 + swap）
          waitForNextFrame 期間 -> applyPendingGpuCopies()（renderer.cpp:2487-2491）
CPU 寫 root  loriePrepareAccess 對 screen pixmap 的 DEST 存取一律拿 state->lock（lorieNeedsGpuLock，
          InitOutput.c:3935），也就是 renderer 重畫時持有的那把鎖
自我複製 lorieExaPrepareCopy：src == dst 一律 CPU（InitOutput.c:2274）
```

## 4. 被否定的假設（保留）

```
H-slack   Android 背景 timer slack 讓 usleep(200) 睡很久
          -> 否定。slack_probe 經 X3 同一條啟動路徑（TermuxService、untraced）：inherited slack 50 µs，
             usleep(200) p50 0.276 ms / p99 0.600 ms（PRoot 內 0.225 ms）
H-frame   每個 GPU op 的完成被畫面節奏綁住（p50 ≥ 半個 frame）
          -> 否定（OPLAT 預測 P1/P4，先凍結）：G 單發 p50 0.9–1.5 ms，120 Hz frame 是 8.3 ms；
             frame 級延遲只在 p90/p99（4–10 ms）
```

## 5. 單一操作延遲（`tests/pga/p_oplat.c`，預測先凍結於 p2-pga-rca/OPLAT-PREDICTIONS.md）

第一對 `oplat-g-01` / `oplat-c-01`（各 100 樣本/格，screen awake、Stable 前後不變、X3 untraced、0 X error）：

```
op（src -> dst）          size    G p50   C p50   G/C  | G burst16 p50  C burst16 p50
solid -> window（root）    16      926      66    14.0 |   14609           164      (89x)
                           64      941      69    13.6 |   14566           174
                          256     1374      72    19.1 |   19594           318
                         1024     2578     191    13.5 |   42747          1985
copy pixmap -> window      16     1172      72    16.3 |   15024           136      (110x)
                           64     1110      69    16.1 |   16040           174
                         1024     1808     575     3.1 |   26117          7448
over a8r8g8b8 -> window    16     1474      72    20.5 |   20162           249
  （Gate A direct 形狀）    64     1455      75    19.4 |   19689           329
                         1024     3239     974     3.3 |   50951         16002
copy window -> 同一 window  64      123      77     1.6 |     195           153      （CPU 兩邊皆是）
src a8r8g8b8 -> window     64      184      72     2.6 |     649           297      （predicate 外，CPU）
putimage                   64      207      71     2.9 |     483           265
nop（只有往返）             —        80      63     1.3
（單位 µs；完整 49 格在 runtime-bfb5769/oplat-*-01/oplat.out）
```

事後觀察（第一對；第二對 replication 預測先凍結於附錄 A.3）：

```
O1  三個 GPU 形狀在所有量過的尺寸、兩種 shape 都輸給 CPU（1024x1024 仍 3.1–21x）
O2  沒有 pipeline：連發 16 個 ≈ 16 x 單發
O3  不走 GPU 的操作在 G 也慢 1.1–2.9x（候選解釋：CPU 寫 root 必拿 renderer 的 state->lock，
    G 下 renderer 為每個 GPU op 重畫，持鎖時間變長——未驗證，不當證據）
```

## 6. replication（`oplat-g-02` / `oplat-c-02`）

預測在第一對之後、第二對之前凍結（OPLAT-PREDICTIONS.md 附錄 A.3），evaluator 在跑之前提交（1e5d615）：

```
oplat-replication.json   R1 True（24/24 格 G p50 > C p50）· R2 True（6/6 burst16 ≥ 8x single）
                         R3 True（對照組：copy_win 8/8 格 G/C 在 [0.5, 3]）-> O1_O2_CONFIRMED
有效性                   兩次擷取 screen awake 且未鎖（前後）、Stable 前後相同、X3 TracerPid 0、49/49 格 0 X error
重現性（single p50，G/C µs） 01: solid16 926/66  solid1024 2578/191  copy_pix16 1172/72  over16 1474/72  over1024 3239/974
                         02: solid16 1252/68 solid1024 2294/193  copy_pix16 1041/66  over16 1291/75  over1024 3150/961
```

O1、O2 升格為已證明。O3 仍是觀察（沒有被預測、沒有被驗證）。

## 7. 工具錯誤（留痕）

```
evaluator reading   oplat_predictions.py @ 8997bc0 對第一對輸出 SOLID_COPY_NOT_THE_SOURCE。該標籤只檢查 P1 為假，
                    凍結的那一列要求「P1 為假且 G ≈ C」；實測 13.6x，不適用。保留原輸出，更正寫在
                    OPLAT-PREDICTIONS.md 附錄 A.1 與 evaluator docstring（1e5d615）。
預測構造            P1/P3 把 copy_win（src == dst）當 GPU 路徑；原始碼（InitOutput.c:2274）與資料都顯示它是 CPU。
collector 記憶體     xfce_collect.py 整檔讀入 → INCIDENT-20260923-LMK-KILLED-TERMUX；已串流化（b650982），
                    對 xfce3-c1-01 / rca3-g-01 重新產生的輸出與先前存下的逐欄相同。
```

## 8. 結論

**PGA-GAP-2 的 RCA（§13.2 第 1 步）在 op 層已證明：**

```
cell       XFCE-FREEZE-V3 C1（xfce3-c1-01 INVALID；RCA pair rca3-g-01 INVALID / rca3-c-01 BASELINE_VALID）
predicate  「凍結的 production GPU 設定下，XFCE choreography 能在凍結時限內找到視窗」為假
cause      每個走 GPU 的 EXA op（solid、pixmap->window copy、Over composite）在 Done* 同步等 renderer 完成：
           單發 1–3 ms，比 CPU 慢 3–20 倍（16..1024 所有尺寸），連發不 pipeline（16 個 ≈ 16 倍）。
           XFCE 每秒約 190 個這種 op，X 花在等待上的時間加上成串的 burst，讓所有 client 的往返
           p50 從 1.5 ms 變 8.9 ms、p99 從 11.6 ms 變 181 ms，xdotool 查找從 0.2 s 變 3.7 s（p90 10.4 s）。
causal     同一 harness、同一 workload、只差 TERMUX_X11_DISABLE_EXA_GPU：verdict INVALID ↔ BASELINE_VALID
           op 層：同一開關、每格 100 樣本、兩對重現、對照組不變
```

沒有被證明的（不寫成結論）：

```
- 1–3 ms 的組成（X→renderer 交接、lock、GL submit、fence wait、X 輪詢各佔多少）。要拆需 TERMUX_X11_B3A_TELEMETRY
  （只涵蓋 composite）或新增量測。若修補選擇「不送 GPU」，不需要拆；若選擇「非同步完成」，必須先拆。
- O3（非 GPU op 在 G 也慢 1.1–2.9x）的原因。
- Gate A direct 在更大尺寸 / batch / readback 組合下是否仍輸：這是 B.3（V2-B3-MATRIX-BIND）要量的，
  OPLAT 不取代 B.3（1024x1024 以上、ratio、reuse、residency、readback 都沒量）。
```

對後續的直接影響：

```
XFCE baseline   G 設定下再跑 V3 系列只會重複 INVALID；series 暫停，等 PGA-GAP-2 有修補或 Gate H 決定路由
B.3             仍照凍結執行（它是 Gate H 的唯一合法輸入）；OPLAT 的結果不改 B.3 的凍結
Gate H          若 B.3 也顯示 GPU 在所有格子都不勝，router 的問題變成「production 預設是否該送 GPU」，
                這是 V1-Core 的方向性決策，會回報使用者
```
