# OPLAT — 預測與判讀規則（先於任何裝置資料凍結）

DATE 2026-09-23 · PRODUCT `bfb5769` · 工具 fork `tests/pga/p_oplat.c`（RCA instrument，不是 qualification cell）
上游：RCA-XFCE-3（rca3-g-01 INVALID vs rca3-c-01 BASELINE_VALID，同一個 harness、只差 `TERMUX_X11_DISABLE_EXA_GPU`）

## 為什麼要這一步

`TERMUX_X11_DISABLE_EXA_GPU=1` 一次關掉四條路：EXA solid、EXA copy、EXA composite（含 Gate A direct / D0a staging）、
present copy。因果已經被這個開關證明（同 harness、同 workload、tracer 負載相當），**但還不知道是哪一條**。
PGA §13.2 第 1 步要求 root cause 被證明而不是推測；最小修補設計（第 2 步）取決於這個答案。

## 已知的 source 事實（寫預測的依據）

```
每個 EXA GPU op 都同步等完成     lorieExaDoneSolid / DoneCopy / DoneComposite -> lorieGpuCopyWait
                                  (InitOutput.c:2214 / 2329 / 3717,3752,3778)，usleep(200) 輪詢 completedSerial
排程                              X 寫 gpuCopyQueue + pthread_cond_signal(rendererCond)
renderer 處理                     有 pending op 且 surface 可用、不在 waitForNextFrame -> redrawLocked()（整張畫面重畫 + swap）
                                  waitForNextFrame 期間 -> applyPendingGpuCopies() 單獨處理（renderer.cpp:2487-2491）
timer slack                       已排除：X3 的啟動路徑（TermuxService）slack 50 µs，usleep(200) p50 0.276 ms（slack_probe）
```

## 預測（device，G = `TERMUX_X11_GATEA_PROTO=1`，C = `TERMUX_X11_DISABLE_EXA_GPU=1`，同一個 APK）

| # | 預測 | 門檻 |
|---|---|---|
| P1 | G 的 `solid` 與 `copy_win` 單發延遲被畫面節奏綁住；C 不會 | 64x64 single：G p50 ≥ 4000 µs **且** C p50 ≤ 1000 µs（兩個 op 各自判） |
| P2 | 沒有 op 在飛時 X 本身不慢 | `nop` p50：G ≤ 1000 µs |
| P3 | 同步等待不 pipeline：連發 16 個就是 16 次等待 | `solid`、`copy_win` 64x64：G burst16 p50 ≥ 8 × G single p50 |
| P4 | `over_argb`（Gate A direct 候選形狀）在 G 同樣被 DoneComposite 同步等待 | 64x64 single：G p50 ≥ 4000 µs |
| P5 | `src_argb` 不是 GPU 形狀（predicate 只收 Over），G 與 C 相當 | 64x64 single：G/C p50 比值在 [0.5, 2] |

4000 µs 的理由：面板若是 120 Hz，frame 8.3 ms，被 frame 綁住的等待平均約半個 frame；60 Hz 則更長。
`display-refresh.txt` 記錄實際刷新率，但**門檻不因它而事後調整**。

## 判讀（先凍結）

```
P1 與 P3 成立            機制 = 每個 legacy EXA solid/copy 同步等 renderer 完成，且完成被畫面節奏綁住
                         -> PGA-GAP-2 root cause 以此為準，進入 §13.2 第 2 步（最小設計）
P1 不成立（G ≈ C）       solid/copy 不是來源；改查 present / composite（P4），不得往 solid/copy 修
P2 不成立                X 在 G 模式下整體變慢（不只 op 等待）-> 機制另有其因，先不設計修補
P4 成立                  Gate A direct 形狀同樣受同步等待影響 -> 修補設計必須說明 composite 怎麼處理
                         （B.3 會量到同一個成本；不因此改 B.3 的凍結）
P5 不成立                predicate 以外的 composite 也被 GPU 模式影響 -> 需要解釋（例如 root 上有 pending GPU write
                         時的 lorieNeedsGpuLock），不得忽略
```

每一種模式各跑一次（MODE G、MODE C，順序 G 先），rounds 10 × reps 10 = 每個 case 100 個樣本。
結果只作 RCA 證據，不是 qualification；不與任何 baseline 或 B.3 資料合併。

---

## 附錄 A — 第一對（oplat-g-01 / oplat-c-01）之後的更正與 replication 預測（2026-09-23 17:0x，先於 oplat-*-02）

### A.1 第一對的結果與兩個錯誤（留痕，不改寫上面的凍結內容）

evaluator（`tests/pga/oplat_predictions.py` @ 8997bc0，在讀資料前提交）輸出：
`P1=False P2=True P3=False P4=False P5=False reading=SOLID_COPY_NOT_THE_SOURCE`（保存在 `runtime-bfb5769/oplat-predictions.json`）。

```
錯誤 1（evaluator）   reading 表那一列寫的是「P1 不成立（G ≈ C）」；evaluator 只檢查 P1 為假，漏掉 (G ≈ C)。
                      實際 solid 64x64 single：G 941 µs vs C 69 µs（13.6x），不是 G ≈ C。
                      -> SOLID_COPY_NOT_THE_SOURCE 這個標籤不成立；正確讀法：凍結的 reading 表沒有任何一列適用。
錯誤 2（預測構造）     P1/P3 的 copy_win（同一個 window 內複製）不走 GPU：lorieExaPrepareCopy
                      `if (alu != GXcopy || src == dst) return FALSE;`（InitOutput.c:2274）。
                      資料一致：copy_win 在所有尺寸 G/C = 1.1-2.3。P1/P3 中 copy_win 那一半是 construction 無效。
```

依凍結判讀，**被否定的是「frame-coupled」**：G 的 GPU op 單發 p50 約 0.9-1.5 ms（P1/P4 門檻 4000 µs 不成立），
不是一個 frame（120 Hz = 8.3 ms）；frame 級的延遲只出現在 p90/p99（4-10 ms）。

### A.2 事後觀察（未經預測，下面用 replication 驗證）

```
O1  solid / copy_pix / over_argb：所有尺寸、兩種 shape，G p50 都大於 C p50（1024x1024 仍 3-21x）
O2  同一類 GPU op 連發 16 個 ≈ 16 x 單發（沒有 pipeline）
O3  不走 GPU 的操作（copy_win、src_argb、putimage）G 也慢 1.1-2.9x
```

### A.3 replication 預測（oplat-g-02 / oplat-c-02，同一個 build、同一個 runner，G 先）

| # | 預測 | 門檻 |
|---|---|---|
| R1 | O1：GPU 形狀在所有量過的尺寸都輸給 CPU | solid、copy_pix、over_argb × 16/64/256/1024 × single/burst16：24 格**全部** G p50 > C p50 |
| R2 | O2：不 pipeline | solid、copy_pix、over_argb × 16/64：G burst16 p50 ≥ 8 × G single p50，6 格全部成立 |
| R3 | 對照組（應該「不紅」的那一邊）：src == dst 的 copy_win 兩種模式都走 CPU | copy_win × 4 尺寸 × 2 shape：G/C p50 比值全在 [0.5, 3] |

R3 的作用：證明這個儀器不是「G 模式什麼都慢」——若 R3 不成立而 R1 成立，R1 不能單獨歸因於 GPU 路徑。
任一格 X error 或缺格 → 該預測為 null。R1 與 R2 與 R3 全成立 → O1/O2 升格為已證明，作為 PGA-GAP-2 的 op 層證據。
