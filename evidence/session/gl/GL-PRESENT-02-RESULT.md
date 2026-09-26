# GL-PRESENT-02 結果 — 2026-09-26：**GL_PRESENT_INVALID**（兩個獨立原因）

判準：`GL-PRESENT-02-FREEZE.md`（sha256 `2357ff4a617d84c0…`）。判定器 `gl_present_judge.py` sha256 `38e20fcad17b8014…`（fork `5130cf2`）。
證據：`gl-present-02/main-01`、`main-02`、`xdbg-01`，輸出在 `judge.txt`／`judge.json`，執行紀錄在 `chain.log`（12:05–12:19）。

## 判決（凍結，不重判）
- J0 **`GL_PRESENT_TOOL_INVALID`**：`rep1:vk-off:protocol_histogram_missing`。所以 J1、J2、J3 全部 INVALID，J1x 全部 `X_WITNESS_NULL`（這次 J1x 的修正有生效）。
- **STEP1 `GL_PRESENT_INVALID`**。

## 原因
1. **02 新加的規則本身有漏洞（工具錯誤，留下紀錄）。**
   - J0 第 2 條把「協定直方圖缺少**或是空的**」都當成無法驗證。
   - 但 `vk_present --offscreen` 根本不連 X，所以它的直方圖本來就應該是空的（`majors: []`）。**空的代表「量過了，什麼都沒送」，不是「沒量到」。**
   - 自我測試沒抓到這個問題，因為合成資料裡的 vk-off 帶著一筆 GetGeometry，和真實情況不一樣。判定器只用我自己假設的資料測過，沒有拿形狀真實的資料驗證過，這是方法上的缺口。
2. **rep2 的 `vk-off` 無效**：`focus_pre=null`。同一次讀取裡亮屏和鎖屏都讀到了，只有 `dumpsys window` 的焦點那一項是空的。adb server 的 log 在 12:11–12:13 沒有斷線或重連紀錄，**原因無法確定**。
   就算沒有第 1 點，vk 也只剩 1 個可用的 rep，J2_vk 會是 `INSUFFICIENT_REPS`，STEP1 一樣會是 INVALID。

## 有效性
除了 rep2 的 vk-off 以外，其他 segment 全部有效。Stable `:1` 在三個 cell 前後都相同（pid 29603，`1.03.01-11b82d9-06.09.26`）。X3 都用確切 pid SIGTERM 結束。沒有殘留的程序。

## 描述（不是判決；和 GL-PRESENT-01 的兩個 rep 一致）
| segment | X3 核 rep1／rep2 | X3 ms／幀 | 路徑 | 像素有 client 的顏色 |
|---|---|---|---|---|
| idle | 0.0169／0.0179 | — | — | — |
| vk-off | 0.0109／（0.0119，無效） | 0.013 | NONE（沒有 X 連線） | — |
| glx-off | 0.0119／0.0128 | 0.015 | NONE（有 3 次建立 swapchain 的匯入，0 次 present） | — |
| vk-l | 0.769／0.745 | 0.452／0.465 | DRI3，modifier 0 | 是 |
| vk-s | 0.370／0.385 | 0.184／0.200 | DRI3，modifier 0 | 是 |
| glx-l | 0.486／0.484 | 0.934／0.936 | DRI3，modifier 0 | 是 |
| glx-s | 0.212／0.213 | 0.264／0.272 | DRI3，modifier 0 | 是 |
| egl-l | 0.050／0.054 | — | NOT_PRESENTED | 否 |
| vk-l-sw | 0.463／0.502 | 1.43／1.50 | CORE_PUT | 是 |

- 比值 r：vk 2.46／2.32（01 是 2.07／2.10），glx 3.54／3.45（01 是 3.75／3.57）。
- xdbg：X3 印了 vk 4 行、glx 3 行 `DRI3: imported raw fd, modifier 0`，egl 0 行。和 01 一樣。
- 01 加 02 共 4 個獨立的 X3 生命週期，描述值全部一致：VK／GLX 走 DRI3 LINEAR，X3 上屏時約 0.5–0.77 核（不上屏時約 0.012），每幀成本隨像素增加；EGL 每次都不上屏。
