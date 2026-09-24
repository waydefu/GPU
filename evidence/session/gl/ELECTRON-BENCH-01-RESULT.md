# ELECTRON-BENCH-01 結果 — 2026-09-24：**ELECTRON_GPU_NO_BENEFIT**（CPU_BETTER 兩次都不成立）

判準：`ELECTRON-BENCH-01-FREEZE.md`（FROZEN）。判定器 `electron_bench_judge.py` SHA256 `86fb5fe2…85a8`（fork `a4440fa`）。
證據：`electron-bench-01-rep01`（14:01–14:12）、`electron-bench-01-rep02`（14:12–14:23）；判決 `electron-bench-01-judge.txt`。

## 有效性 — 全部成立
- 6 輪：觸控 0、錄製器自我測試 true、thermal 開跑前 0、driver 無錯誤、每階段前後實驗版在前景／亮屏／無鎖屏、
  結束後殘留 0、焦點 true、翻頁與打字確實生效。V0 身分 `Disabled`，V2 身分 Turnip Adreno 840 且 `gpu_compositing=enabled`。
- runner：兩個 cell 都 `CMD_CAPTURED`，Stable 前後相同，mem-guard 未觸發，root 1200×2416，X3 撐到 fixture 結束。
- 每個 cell 各一行 `GATEA_FATAL_HALT what=r-hup reason=6`（14:12:10、14:23:40），都在最後一輪結束後、runner SIGTERM X3 的收尾階段——預期行為。
- 同時在跑：使用者啟動的兩個唯讀 RCA session（共用主機 CPU／記憶體）；影響反映在 A/A 雜訊 5.1%。

## 判決
| | S（捲動＋打字 CPU 秒，Cursor session＋X3） | 倍數（門檻 ≤ 0.80） | 捲動 p95 幀 | >50 ms | 閒置核數 |
|---|---|---|---|---|---|
| rep01 V0（2 輪平均） | 71.09 | — | 25.0 ms | 3.5 | 0.348 |
| rep01 V2 | 68.47 | **0.963** ✗ | 25.0 ms | 4.0 | 0.348 |
| rep02 V0 | 71.27 | — | 25.0 ms | 3.0 | 0.350 |
| rep02 V2（2 輪平均） | 68.85 | **0.966** ✗ | 25.0 ms | 4.5 | 0.354 |

- A/A 雜訊 0.051 → 門檻維持 20%。CPU_BETTER 兩次都不成立；FRAMES_NOT_WORSE、IDLE_OK、CORRECT 都成立。
- V2 三輪截圖正常（主色 93.6%、1273 色），GPU 程序 0 次崩潰。
- **白話：開 GPU 在 Cursor 上是安全的（畫面正確、不空轉、不變卡），但 CPU 只省約 3.5%，沒有實質收益。**

## 描述（不進判準）：CPU 花在哪
| 每輪平均 | Cursor session | X3 | Activity（renderer） |
|---|---|---|---|
| 閒置 60 s | ≈20.3 s（**約 0.33 核**，兩組相同） | ≈0.7 s | ≈0.44 s |
| 捲動 30 s V0 → V2 | 29.1 → 28.3 s | 0.84 → 0.67 s | 0.78 → 1.05 s |
| 打字 30 s V0 → V2 | 40.2 → 38.9 s | 1.08 → 0.92 s | 1.98 → 1.99 s |
- Cursor 的 CPU 幾乎全在自己的程序（JavaScript：編輯器排版、輸入處理、extension host），畫圖只佔一小部分，GPU 能分擔的空間本來就小。
- Cursor 閒置就吃約 0.33 核（兩組相同）——與 GPU 無關，可能是 extension host 或 PRoot 追蹤器開銷，**未查**。
- 捲動 p95 在 12 輪全部剛好 25.0 ms（≈40 Hz）：rAF 被某個固定節奏卡住，這個指標在本負載下不敏感；FRAMES 判斷實際上只靠 >50 ms 次數。

## 限制
- 只測 Cursor、1000×800 視窗、長 C++ 檔的翻頁與打字。沒測 WebGL、影片、大量動畫、多視窗——那些是 GPU 比較可能有差的場景。
- 只在實驗版 `:3` 測；日常的 Stable `:1` 沒測（紅線）。

## 過程紀錄
乾跑 01（焦點被我的點擊移走、rAF 重複記錄）、02（使用者滑掉實驗版 → Gate A `x-hup/6` 設計停機；我一度誤判為 EXA FatalError，已在
`INCIDENT-20260924-X3-EXA-BUG-FATAL.md` 開頭更正）、03（工具檢查全過、觸控 357）。修正都在受判資料之前，記在凍結文件。
