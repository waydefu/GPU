# V2-PGA-GAP-INVENTORY — Production Gate A 缺口清單（計畫書 §13）

DATE 2026-09-23 · 現行產品 `bfb5769`（PGA-GAP-1 修補）· 前一權威 `dc94485`

**入列規則（§13.1）：** 必須指出哪一格、哪一份 evidence、哪一個 predicate 為假。
沒有 evidence 指向的 → 不入列（記為 deferred / risk）。

## A. §13.3 的六項歷史缺口 — 逐項重新確認

| # | 缺口 | 現況 | 依據 |
|---|---|---|---|
| 1 | CPU ownership release transition | **已由 runtime 證據覆蓋** | direct 路徑在 publish 時 checked unlock（InitOutput.c:3397 `UNLOCK_SRC_OK`），完成後 relock（:3512 `RELOCK_SRC`）。R8 10/10、R10 A/B/C：每個 direct composite 的 event 3/4 與 18/19 次數相等（probe-02：8/8/8/8） |
| 2 | import-ready acknowledgment | **已覆蓋** | `gateAEnsureReady` 送 REGISTER 後等 READY（InitOutput.c:2820-2824）；renderer 發 READY（renderer.cpp:682），X 端消費（cmdentrypoint.cpp:212）。R3 d9b7f60 首次證明 X 不再自等；R8/R9/R10 全部有 event 1 成對 |
| 3 | per-serial success/failure with quiesced replay | **已覆蓋** | `lorieGateADeriveResult`（lorie.h）；FIRST_FAILED_SERIAL 發布點 renderer.cpp:1073/2313。R7 13/13 以 fault injection 走遍失敗路徑，CARRY_FORWARD 到 dc94485 → bfb5769 |
| 4 | acquire/release publication | **已覆蓋** | 所有跨 process 欄位經 `lorieGateA*Acquire/Release` 存取，lock-free 靜態斷言（lorie.h:496 起）。R-series 無任何 torn-state 症狀 |
| 5 | generation-bound drain/unregister lifecycle | **已覆蓋（V1 範圍內）** | R8 C1–C5/D/P1/P2、R9 F1/F2、R10 A/B/C/E：counter 全數平衡、registry/lease 歸零。generation 2 依 D-06 **不在 V1**（fresh-process recovery；且 COLD2-ROUTE-SEARCH 證明第二個 boundary 不可到達） |
| 6 | producer-fence contract for imported / client-owned AHB | **V1 構造上不適用** | imported AHB 直接被拒（InitOutput.c:3087 `sp->imported`；R2 CARRY_FORWARD）。Gate A 只碰 X 自有 AHB：lock 傳 fence -1、unlock 傳 NULL（buffer.c:438/477，同步語意），GPU→CPU 順序由 renderer 的 EGL fence 等待（event 11）＋completion 發布保證。fence fd 的**可觀測性**仍是 R-30（observability，不是正確性缺口） |

## B. 由 workload 證據新發現的缺口

### PGA-GAP-1 — 熱路徑診斷 stamp 讓 X 飽和　**狀態：修補中（八步進行到第 8 步）**

```
evidence   p2-xfce-runtime/runtime-dc94485/xfce-c1-03   BASELINE_DEFECT
predicate  「XFCE workload 能照凍結時間表執行」為假
1 RCA      PGA-GAP-1-RCA.md（emit ≥332 µs → 天花板 3015/s；X 實測 2123 中位 / 3494 峰值）
2 design   PGA-GAP-1-DESIGN.md（執行期旗標 TERMUX_X11_P2A_DIAG，預設關）
3 host     tests/pga/test_p2a2_gate.py 9/9；對 dc94485 紅 7/9（對照組會失敗）
4 patch    fork bfb5769（dix-config.h.in +19 −1）
5 CI       35811368916 success
6 artifact APK ff7b9309…8472 · Build ID 890db760… · signer 不變
7 install  INSTALL_BFB5769_BIND_PASS（裝置讀回 sha 相符）
8 requal   touched-semantics audit → R0–R10 CARRY_FORWARD；smoke R8-D / R8-P2 = R8_PASS；
           兩格 logcat 的 stamp 行數 = 0；XFCE-FREEZE-V2 系列執行中
```

### PGA-GAP-2 — 同步的 legacy EXA GPU offload 讓 X 在桌面負載下變慢　**狀態：第 1 步完成（op 層已證明），第 2 步等 B.3**

```
evidence   p2-xfce-runtime/runtime-bfb5769/xfce3-c1-01 INVALID；RCA pair rca3-g-01 INVALID / rca3-c-01 BASELINE_VALID
           p2-pga-rca/runtime-bfb5769/oplat-{g,c}-{01,02}（op 層，預測先凍結，02 為 replication）
predicate  「凍結的 production GPU 設定（PROTO=1）下，XFCE choreography 能在凍結時限內找到視窗」為假
1 RCA      planning-v2/xfce-baseline/RCA-XFCE-3.md：每個走 GPU 的 EXA op 在 Done* 同步等 renderer 完成，
           單發 1–3 ms、比 CPU 慢 3–20x（16..1024 全部尺寸）、連發不 pipeline；XFCE ~190 op/s
           -> 往返 p50 1.5→8.9 ms、p99 11.6→181 ms。否定：timer slack、frame-coupled p50。
2 design   未開始。兩條路互斥、影響面差很多：
             (a) production 不把 legacy EXA solid/copy 送 GPU（CPU 在所有量過的尺寸都較快）——路由決策，
                 與 Gate H 重疊；composite / Gate A direct 的去留由 B.3 + Gate H 決定
             (b) Done* 改非同步完成——動 ownership / fence semantics，屬「大改架構」停止條件，需先拆 1–3 ms 組成
           先跑 B.3（凍結、Gate H 唯一合法輸入）再選；不在 B.3 之前改產品
3–8        未開始
```

### PGA-GAP-3 — staging 的 FD 複本註冊給 renderer 後永不註銷（記憶體洩漏）　**狀態：第 1 步完成（原始碼證明＋量化）**

```
evidence   p2-b3-runtime/runtime-bfb5769/b3-s-02（S 模式 45 s 註冊 1518 個 / 7.4 GB -> lmkd 殺 Stable 與 com.termux）
           INCIDENT-20260923-2-LMK-B3-S.md；XFCE G：xfce3-c1-01 3348 個 / 4.1 GB、rca3-g-01 3225 個；C：0
predicate  「production 設定下，一個 session 的 renderer 記憶體不隨 composite 數量無界成長」為假
1 RCA      PGA-GAP-3-RCA.md：InitOutput.c:1855 註冊、3759-3801 只 release 不 unregister；__LorieBuffer_free 不送
           EVENT_REMOVE_BUFFER；renderer 只在 remove 或斷線（removeAllBuffers）時釋放
2 design   PGA-GAP-3-DESIGN.md：Done 在等待完成後 lorieUnregisterBuffer(upload)，排除 D0a cache
3 host     tests/pga/test_gap3_unregister.py：對 bfb5769 紅、修補後綠；3 個 mutant 被抓（e6432a9，先於 patch）
4 patch    fork 83d45a9（InitOutput.c +7；bfb5769..83d45a9 其餘只動 tests/）
5 CI       35845935317 success
6 artifact APK f4c98b8a…230f · Build ID 67e8ad53… · signer 不變（p2-pga-artifact/artifact-83d45a9/）
7 install  INSTALL_83D45A9_BIND_PASS（裝置讀回 sha / signer / build-id 相符，Stable pid 不變）
8 requal   requal-01 **GAP3_REQUAL_FAIL**（frozen）：記憶體全過（staged 15.8 GB、swap +0、MemAvailable −169 MB、
           mem-guard 未觸發、22/22 像素正確），但 Activity maps +19 > 16——門檻當初沒有基準。
           requal-02（設計附錄 A，先凍結）：**GAP3_REQUAL_FAIL**：S +22、C −7，殘差 29 > 16（記憶體再次全過）
           → 依凍結規則 PGA-GAP-3 **未完整**：GB 級洩漏已修（兩次證明），每筆 staging 仍殘留 ~0.01 個 mapping；
           下一步：2 倍輪數區分線性洩漏或驅動 pool 上限（判準先凍結）
關聯       R10 D-04（Activity maps_count 上飄）：修補前每次註冊殘留 0.166 個 mapping，修補後 0.0068
```

## C. 評估過但**不入列**的項目（沒有 predicate 為假的證據）

| 項目 | 為什麼不入列 | 去處 |
|---|---|---|
| D-04 activity.maps_count 跨 session 上飄 | 無 counter 失衡、無 fd 成長、無 PSS 趨勢；幅度 2–4 mapping/session | 仍 OPEN；XFCE／長序列資料補判 |
| R-30 三個 ahb_*_fence_fd 無 trace site | 觀測缺口，不是正確性缺口（見 A-6） | risk register |
| R-31 X 啟動時 VM-JIT 崩潰 | 簽名在 ART 的 dalvik-jit-code-cache，不在 native；PROTO=0 也會發生 → 不是 Gate A | risk register；Gate W「任何 crash」會碰到它 |
| GAP-8 ProcLorieR8Checkpoint 重複 `phase` 鍵 | 只在 R8 test extension 裡，production 不走 | deferred（已在 tooling 端收容） |
| logcat 在高負載下掉 GATEA_EVENT 行 | qualification telemetry（預設關），產品行為不受影響；judge 已用 seq 完整性處理 | 無需修補 |

## D. 資格證據缺口（不是產品缺口，但 V1 acceptance 需要）

| 項目 | 現況 | 需要 |
|---|---|---|
| direct 路徑 pixel-exact（acceptance #6） | 只有 R3 d9b7f60 一個 8×8 case（`exact_px=64 maxΔ=0`）。B.2c 的 1514 測試是 **staging 路徑** | 在最終 artifact 上以 PROTO=1 跑完整 oracle，並用 event=5 數量證明真的走了 direct |
| unsupported fallback safe（acceptance #9） | B.2 的 negative controls（src-op / mask / dst-argb / bilinear / repeat / transform / CA）是在舊 artifact | 同一次 oracle 補跑 negative controls |

## 關閉條件（§13.5）

inventory 內每個缺口八步完成、每個 requal PASS、carry-forward 皆有裁決、沒有「暫時接受」。
PGA-GAP-1 卡在第 8 步（XFCE 系列需要 G 設定下可執行，被 PGA-GAP-2 擋住）；PGA-GAP-2 在第 2 步前等 B.3；PGA-GAP-3 第 8 步兩次 FAIL（只剩 mapping 殘差；記憶體已修）。B.3 mode S 在 PGA-GAP-3 修補前暫停（會觸發 mem-guard，且資料被記憶體壓力污染）。
