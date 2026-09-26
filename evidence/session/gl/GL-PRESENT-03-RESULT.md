# GL-PRESENT-03 結果 — 2026-09-26：**PRESENT_COST_IS_X3_PER_PIXEL_COPY**（主線 #3 第一步有判決了）

判準：`GL-PRESENT-03-FREEZE.md`（沿用 01 第 1–10 節加修訂 1，以及 02 的兩個修正；本 attempt 的修正和補記，文件 sha256 `92e3b1330a5bee1e…`）。
判定器 `gl_present_judge.py` sha256 `9c5ca53626853abd…`（fork `40a1750`），cell 檢查 `gl_present_cellcheck.py`（fork `8423f0a`）。
證據：`gl-present-03/main-01`、`main-02`、`xdbg-01`；輸出在 `judge.txt`／`judge.json`；執行紀錄在 `chain.log`（12:27–12:41），main 兩個 cell 都是 `CELLCHECK_OK`。
GL-PRESENT-01 和 02 仍然是 `GL_PRESENT_INVALID`（判定器漏洞，已凍結），本判決沒有使用它們的資料。

## 判決
| 項目 | 判決 |
|---|---|
| J0 | `GL_PRESENT_TOOL_VALID` |
| J1 vk／glx／egl | `PATH_DRI3`／`PATH_DRI3`／**`PATH_NOT_PRESENTED`** |
| J1x vk／glx／egl | `X_WITNESS_CONFIRMS`（4 行，modifier 0）／`X_WITNESS_CONFIRMS`（3 行，modifier 0）／`X_WITNESS_CONSISTENT`（0 行） |
| J2 vk／glx | `X3_PRESENT_COST`（0.975、0.905 核 vs 基準 0.016）／`X3_PRESENT_COST`（0.484、0.476 核） |
| J3 vk／glx | `X3_COST_PER_PIXEL`（r = 4.26、4.36）／`X3_COST_PER_PIXEL`（r = 3.23、3.49） |
| **STEP1** | **`PRESENT_COST_IS_X3_PER_PIXEL_COPY`** |

## 有效性
- 18 個 segment 全部有效：觸控 0、焦點、亮屏、沒鎖屏、`thermal_start=0`、驅動身分正確，shim 和協定直方圖都讀得到，像素探針 4 次取樣都有效。
- 狀態重讀 0 次（`state-retries.txt` 不存在，SEG 行 `state_retries_total=0`）。
- Stable `:1` 在三個 cell 前後都相同（pid 29603，`1.03.01-11b82d9-06.09.26`）。X3 都用確切 pid SIGTERM 結束（19955、2684、18649，記錄在 `x-end.txt`）。沒有殘留程序。熱狀態前後都是 0。

## 數字（20 s 時間窗；L = 1200×1200，M = 600×600）
| segment | X3 核 rep1／rep2 | X3 ms／幀 | fps | 路徑 | 像素有 client 的顏色 |
|---|---|---|---|---|---|
| idle | 0.0164／0.0159 | — | — | — | — |
| vk-off | 0.0119／0.0114 | 0.016／0.013 | 764／855 | NONE | — |
| glx-off | 0.0123／0.0114 | 0.016／0.015 | 763／789 | NONE（有建立 swapchain 的匯入，0 次 present） | — |
| vk-l | **0.975／0.905** | 0.854／0.859 | 1152／1062 | DRI3，modifier 0 | 是 |
| vk-s | 0.378／0.377 | 0.201／0.197 | 1897／1926 | DRI3，modifier 0 | 是 |
| glx-l | **0.484／0.476** | 0.940／0.911 | 520／528 | DRI3，modifier 0 | 是 |
| glx-s | 0.218／0.207 | 0.291／0.261 | 760／802 | DRI3，modifier 0 | 是 |
| egl-l | 0.052／0.048 | — | 706／776 | **NOT_PRESENTED** | **否** |
| vk-l-sw | 0.621／0.626 | 1.62／1.60 | 386／395 | CORE_PUT | 是 |

- X3 最忙的是同一條 comm 為 `main` 的執行緒，上屏時占 X3 tick 的 97–99%。
- 本 attempt 用兩點擬合：VK 和 GLX 每像素都約 **0.6 ns**（約 6.6 GB/s），每幀的固定成本很小（約 0–0.06 ms）。

## 限制（必須和判決一起引用）
- **VK 大視窗的每幀成本，在不同 attempt 之間差了將近一倍**：01／02 是 0.45–0.46 ms（r 2.07–2.46），03 是 0.85–0.86 ms（r 4.26–4.36）。VK 小視窗（0.18–0.22 ms）和 GLX（大視窗 0.91–0.97 ms）三次都很穩定。
  原因**沒有查**。可能的方向包括 X3 主執行緒被排到哪一類 CPU 核心、頻率，或 buffer 的記憶體類型，但都還沒證實。
  判決成立，因為判準要求的是同一個 attempt 內兩個 rep 一致。但「每像素多少 ns」只能給範圍（0.22–0.64 ns/px），不能給單一數字。
- 工作量只有清畫面，用 immediate／swap interval 0。真實程式大多有 vsync，X3 的核數大約是「每幀成本 × fps」。
  外推值（不是量測）：1200×2400 的視窗在 120 fps 時，X3 大約 0.08–0.23 核；60 fps 時減半。
- client 在 PRoot 追蹤器底下執行，所以 client 的 CPU 只描述不判決。範圍只到 `/opt/mesa-kgsl` 加上 `f8-gpu`，以及實驗版 `:3`（f592241，MODE=C）。
  **Stable `:1` 沒有測**：它是官方的 termux-x11，這次按紅線沒有碰。

## 這代表什麼（照凍結第 8 節事先寫好的讀法）
1. **Ubuntu 的 VK 和 GLX 程式早就用 DRI3 把 GPU buffer 交給 X3 了**。上屏的 CPU 成本是 **X3 的 Present 複製**：X3 只接受 LINEAR，把 dma-buf 用 mmap 映射成 CPU 記憶體，而且對匯入的 buffer 一律不 flip，所以每幀都在主執行緒逐像素複製。
   這和舊記憶「Zink 走 drisw、client 端用 CPU 複製」的推測**相反**。
   → 主線 #3 第二步的重點應該從「client 端」移到 **X3 端**：可能是讓 renderer 直接把 client 的 dma-buf 匯入成 EGLImage 或 AHB，或是讓匯入的 buffer 可以 flip。Mesa／client 端可能完全不用改。
   **主線 #3 的名稱和範圍要請使用者確認。**
2. **EGL（Zink kopper）在 `:3` 上不上屏**（`PATH_NOT_PRESENTED`，X 端的旁證也一致）：GPU 在畫，但畫面沒交給 X，視窗一直是黑的。
   Chromium、Electron、WebGL 走的就是這條路，所以這是一個獨立的阻礙，不是成本問題，要另外列出來。
