# GL-PRESENT-02 凍結 — 2026-09-26：GL-PRESENT-01 的新 attempt（只修兩個判定器漏洞，門檻不變）

狀態：**FROZEN**（寫於本 attempt 任何 cell 之前）。
GL-PRESENT-01 已經判為 `GL_PRESENT_INVALID`，**永久保留、不重判**（見 `GL-PRESENT-01-RESULT.md`）。本 attempt 的證據放在 `gl-present-02/`，完全不引用 01 的 cell。

## 沿用（原文不重複）
下列內容全部照 `GL-PRESENT-01-FREEZE.md` 第 1–10 節加上修訂 1（文件 sha256 `7c06ddd5607fec48…`），這裡不再重複：問題、預測、環境與綁定、segment、有效性、判準、對照組、讀法、限制、執行規則。

- 產物 `1.03.01-f592241-24.09.26`（APK `f9e35b69…075c`）；`run-gl-bench.sh` `KIND=cmd MODE=C`；`EXPECT_ROOT=1200x2464`；client 經 `f8-gpu`。
- 工具二進位全部和修訂 1 相同：`present_count.so` `3e0299f6…`、`vk_present` `aeb348e8…`、`gl_present_egl` `00d343ad…`、`gl_present_glx` `27fd211f…`、`req_count.so` `199786b4…`、`px_probe` `f86f109e…`。cell 腳本 `326e7da07264c83e…` 也不變。
- chain 腳本 `gl-present-chain.sh` 只多了 `GLP_DIR` 參數（sha256 `12010472887a2418…`），用 `GLP_DIR=gl-present-02` 呼叫。
- 依序跑 main-01 → main-02 → xdbg-01。

## 唯一的改變：判定器（fork `5130cf2`，`gl_present_judge.py` sha256 `38e20fcad17b8014…`）
1. **J0 第 2 條**：有效的 off segment 只有在「交出畫面」時才會失敗。「交出畫面」指的是下列任一項：
   - `present_pixmap`、`shm_put_image`、`put_image`、`x_put_image`、`x_shm_put_image` 大於 0（`HANDOFF_COUNTS`）；
   - 協定層出現 Present/1 或 MIT-SHM/3（`HANDOFF_EXT_REQS`），或 core major 72／62／63；
   - 協定層直方圖缺少或是空的（因為無法驗證，一律判失敗）。

   建立 swapchain 時的匯入（DRI3 PixmapFromBuffers、Present SelectInput）**不算**交出畫面。
   理由：GL-PRESENT-01 的 glx-off 裡，Zink kopper 在 `glXMakeCurrent` 就先建好 swapchain，產生 3 次匯入，但一次都沒有 PresentPixmap，X3 也只有 0.013 核。
2. **J1x**：J1 不是路徑類別（`PATH_INVALID`／`PATH_UNSTABLE`）時，輸出 `X_WITNESS_NULL`。原本會輸出 `CONTRADICTS`。

**門檻完全不變**：`COVER 0.90`、`ON_MIN_CORES 0.10`、`ON_OVER_OFF 3.0`、`FLOOR_CORES 0.01`、`OFF_CTRL_MARGIN 0.05`、`CHEAP_MAX 0.05`、`SCALE_PER_PIXEL 2.0`、`SCALE_FIXED 1.5`，`JUDGED_APIS` 仍是 vk、glx。

## 揭露
- 這兩個修正是**看過 GL-PRESENT-01 的判準資料之後**才決定的。所以門檻一個都不動。
- 特別是 vk 的 J3 比值：GL-PRESENT-01 量到 2.07／2.10，只比 2.0 高 3–5%。本 attempt 不能為了讓它通過而調整。如果這次判 `INCONCLUSIVE`，就照實記錄。
- 本次的新 cell 是獨立的 X3 生命週期，不重用 01 的任何數據。

## 自我測試
共 18 個情境，全部通過。新增的有：
- off 在協定層交出畫面 → 必須失敗；
- off 的協定直方圖缺少 → 必須失敗；
- 用合成的 xdbg cell 測 J1x：工具無效時要輸出 NULL，baseline 要輸出 CONFIRMS。

baseline 本身也改成模擬 01 實際觀察到的 glx-off：有 3 次建立 swapchain 的匯入、0 次 present。

反向檢查（都必須失敗，實際也都失敗了）：
- A：把 `SCALE_PER_PIXEL` 改成 5 → baseline 失敗。
- B：換回舊的 J0 第 2 條 → GL-PRESENT-01 的失敗方式原樣重現，9 個情境失敗。
- C：換回舊的 J1x → `j1x_null_when_tool_invalid` 失敗，輸出和 01 一樣的 CONTRADICTS。
