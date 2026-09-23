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
目前唯一的缺口 PGA-GAP-1 卡在第 8 步（XFCE-FREEZE-V2 系列）。
