# GL-PRESENT-01 結果 — 2026-09-26：**GL_PRESENT_INVALID**（J0 `GL_PRESENT_TOOL_INVALID`，判準規則的漏洞）

判準：`GL-PRESENT-01-FREEZE.md`（第 1–10 節，加上修訂 1；文件 sha256 `7c06ddd5607fec48…`）。
判定器：`tests/gl_present/gl_present_judge.py` sha256 `2124e1cd77d35836…`（fork `bb45c12`）。輸出在 `gl-present-01/judge.txt`、`judge.json`。
證據：`gl-present-01/main-01`、`main-02`、`xdbg-01`，其他還有 `chain.log`，以及不進判準的 `dry-01`（BLOCKED）、`dry-01-r2`、`diag-egl-01`。

## 判決（凍結，不重判）
| 項目 | 判決 |
|---|---|
| J0 | **`GL_PRESENT_TOOL_INVALID`**：`rep1:glx-off:counts_without_presenting`、`rep2:glx-off:counts_without_presenting` |
| J1 vk／glx／egl | `PATH_INVALID`（因為 J0 無效） |
| J1x vk／glx／egl | `X_WITNESS_CONTRADICTS`／`X_WITNESS_CONTRADICTS`／`X_WITNESS_CONSISTENT`（前兩個是判定器的瑕疵，見下文） |
| J2、J3 vk／glx | `INVALID_TOOL` |
| **STEP1** | **`GL_PRESENT_INVALID`** |

## 有效性（全部成立）
- 3 個 cell 都是 `CMD_CAPTURED`。main 的 2×9 個 segment 和 xdbg 的 3 個 segment 都有效：觸控 0（觸控裝置 selftest 為 true）、焦點、亮屏、沒鎖屏、`thermal_start=0`、驅動身分正確、每個 segment 的 shim 都剛好一行。
- 所有 cell 的 Stable `:1` 前後都相同：pid 29603、`1.03.01-11b82d9-06.09.26`。每個 X3 都用確切 pid SIGTERM 結束（construction，記錄在各 cell 的 `x-end.txt`）。沒有殘留的程序。ADB `192.168.1.100:35761` 全程沒斷。

## 工具錯誤（留下紀錄，錯誤的版本不抹除）
1. **J0 第 2 條寫得太寬。** 原文是「有效的 off segment，除了 `dri3_open` 之外的計數全部是 0」。
   - 但 Zink kopper 在 `glXMakeCurrent` 時就會先建立 swapchain，所以 `glx-off` 兩個 rep 都有 `pixmap_from_buffers` ×3，外加 Present SelectInput（op 3）×3 和 QueryCapabilities（op 4）×1。
   - 它**沒有任何一次交出畫面**：`PresentPixmap`（Present/1）是 0，core 的 72／62／63 也是 0，X3 只有 0.0128 核，和 `vk-off` 一樣安靜。
   - 規則應該只看「交出畫面的 request」，而不是所有計數。主機驗證沒抓到這個問題，是因為 Xvfb 上的 llvmpipe 走 drisw，不會預先建立 swapchain。
2. **J1x 在 J1 無效時仍然輸出 CONTRADICTS。** `xdbg_witness` 在 J1 不是 `PATH_DRI3` 時，只要看到任何匯入 log 就判 CONTRADICTS，沒有處理 `PATH_INVALID` 的情況，應該要輸出 NULL。
   xdbg 的實際內容是：vk 4 行、glx 3 行 `DRI3: imported raw fd, modifier 0`，egl 0 行。**這和 shim 看到的路徑一致，並沒有矛盾。**

**這兩個漏洞都是看過判準資料之後才發現的**，所以不能拿修正後的規則回頭重判這一次。要得到判決，必須另開新 attempt（GL-PRESENT-02）：修正規則、門檻不變、用新的 cell 重跑。

## 描述（**不是判決**；只記錄量到的數字）
X3 核數 = ΔX3 ticks / 100 / 時間窗；ms/幀 = ΔX3 ticks × 10 ms / 幀數。時間窗 20 s，L = 1200×1200，M = 600×600。

| segment | X3 核 rep1／rep2 | X3 ms／幀 | fps（rep1／rep2） | 路徑（shim） | 像素有 client 的顏色 |
|---|---|---|---|---|---|
| idle | 0.0178／0.0183 | — | — | — | — |
| vk-off | 0.0119／0.0114 | 0.015 | 812／758 | NONE | （沒探） |
| glx-off | 0.0128／0.0128 | 0.017 | 732／755 | NONE（有建立 swapchain，沒有 present） | （沒探） |
| **vk-l** | **0.753／0.741** | **0.451／0.461** | 1684／1623 | DRI3，modifier 0 | 是 |
| vk-s | 0.348／0.351 | 0.218／0.219 | 1611／1618 | DRI3，modifier 0 | 是 |
| **glx-l** | **0.491／0.484** | **0.972／0.933** | 511／524 | DRI3，modifier 0 | 是 |
| glx-s | 0.206／0.208 | 0.259／0.261 | 805／805 | DRI3，modifier 0 | 是 |
| egl-l | 0.048／0.052 | — | 834／704 | **NOT_PRESENTED** | **否（黑色）** |
| vk-l-sw | 0.466／0.478 | 1.43／1.43 | 331／337 | CORE_PUT | 是 |

- **L／M 每幀成本的比值 r**：vk 是 2.07／2.10，glx 是 3.75／3.57（像素比是 4）。
  vk 只比凍結門檻 2.0 高出 3–5%。這個邊際很薄，GL-PRESENT-02 **不能**因此調整門檻。
- **兩點線性擬合**（描述值）：X3 每次 present 的成本 ≈ 固定部分＋每像素部分。
  - vk：約 0.14 ms 加 0.22 ns/px，相當於複製速度約 18 GB/s。
  - glx：約 0.03 ms 加 0.64 ns/px，相當於約 6 GB/s。
  - 同樣是 LINEAR buffer，GLX 每像素的成本卻是 VK 的約 3 倍。可能的原因是 kopper 的 swapchain buffer 用了不同的記憶體類型（例如不走 CPU 快取），**但這還沒有證實**。
- **X3 最忙的執行緒**：上屏時 97–99% 的 X3 tick 都落在同一條 comm 為 `main` 的執行緒上（rep1 tid 31028、rep2 tid 13519）。閒置時最忙的是另一條（X3 的 leader）。
- `vk-l-sw` 走的是 CORE_PUT，而不是 SHM：X3 雖然有 MIT-SHM，但 WSI 的 `x11_xcb_display_supports_xshm` 沒有成立（原因還沒查）。這時 client 每幀要花 2.14 ms 的 CPU（DRI3 時是 0.29–0.35 ms）。
- 換算成 120 fps（描述值，只是外推，不是量測）：1200×2400 的視窗，X3 大約 VK 0.09 核、GLX 0.23 核。60 fps 時減半。

## 目前的觀察（還沒有判決支撐，但和原始碼預測一致）
- Ubuntu（`/opt/mesa-kgsl`）的 **VK 和 GLX 已經走 DRI3**，把 LINEAR buffer 交給 X3。上屏的 CPU 成本出現在 **X3 的 Present 複製**（X3 主執行緒，而且隨像素增加），不在 client 端。
  所以原本主線 #3 以「client 端」為重心的前提，看起來要改成以「X3 端」為重心（renderer 直接匯入 client 的 dma-buf，或讓匯入的 buffer 可以 flip）。這要等判決出來，並且跟使用者確認之後再改。
- **EGL（Zink）在 `:3` 上根本不上屏**：兩個 rep 加上 xdbg 都一樣。每幀只送一個 `GetGeometry`，視窗一直是黑的，X3 也沒有收到任何匯入。
  Chromium、Electron、WebGL 走的就是這條路，所以這本身就是一個獨立的阻礙，和上屏成本無關。

## 下一步（要使用者決定）
- **GL-PRESENT-02**（新 attempt）：
  - 凍結修正後的 J0 第 2 條：off segment 裡不能有任何交出畫面的 request，包括 Present/1、MIT-SHM/3、core 72／62／63、`present_pixmap`、各種 put。建立 swapchain 時的匯入允許出現。
  - 修正 J1x：J1 不是路徑類別時輸出 NULL。
  - 所有門檻不變。
  - 用新的 cell 跑 main-01、main-02、xdbg-01，大約 15 分鐘，執行期間不要碰手機。
- 或者接受這次的描述值，直接進主線 #3 第 2 步（可行性調查）。這樣第 1 步就沒有判決。
