# GL-PRESENT-03 凍結 — 2026-09-26：第三個 attempt（修 02 的規則漏洞，加上狀態重讀；門檻不變）

狀態：**FROZEN**（寫於本 attempt 任何 cell 之前）。GL-PRESENT-01、02 都是 `GL_PRESENT_INVALID`，**永久保留、不重判**。本 attempt 的證據放在 `gl-present-03/`。

## 沿用
下列內容照 `GL-PRESENT-01-FREEZE.md`（第 1–10 節加修訂 1），以及 `GL-PRESENT-02-FREEZE.md` 的兩個修正（off segment 只算交出畫面的 request；J1 無效時 J1x 為 NULL）：
產物、runner、`MODE=C`、`EXPECT_ROOT=1200x2464`、`f8-gpu`、全部工具二進位（`present_count.so` `3e0299f6…`、`vk_present` `aeb348e8…`、`gl_present_egl` `00d343ad…`、`gl_present_glx` `27fd211f…`、`req_count.so` `199786b4…`、`px_probe` `f86f109e…`）、segment、有效性、判準、讀法。
chain 以 `GLP_DIR=gl-present-03` 呼叫（`gl-present-chain.sh` `12010472887a2418…`）。依序跑 main-01 → main-02 → xdbg-01。

## 改變（fork `40a1750`）
1. **判定器**（`gl_present_judge.py` sha256 `9c5ca53626853abd…`）：off segment 的協定直方圖只有在**缺檔或無法解析**時才判失敗。**空的直方圖是合法的**，代表量過了、什麼都沒送。
   理由：02 的 rep1 vk-off 因為 `vk_present --offscreen` 根本不連 X、直方圖是空的，被判成 `protocol_histogram_missing`。
2. **cell 腳本**（`gl_present_cell.sh` sha256 `85baf2c8d70522d9…`）：唯讀的狀態查詢（`dumpsys window`／`power`）如果回傳空值，最多重讀 2 次，間隔 0.5 s。每次重讀都記到 `state-retries.txt`，SEG 行會帶上 `state_retries_total`。
   理由：02 的 rep2 vk-off 有一次焦點讀到空值（adb 沒有斷線），因此判成無效。
   - 重讀**不會**改變有效性的定義：3 次都是空的，一樣記 null，一樣 INVALID。
   - 這只是重讀同一個當下的狀態，不是重跑 segment。
   - 已用假 adb（前兩次回空）在本機測過：確實重讀了 2 次、有記錄，最後讀到正確的焦點。

**門檻完全不變**：`COVER 0.90`、`ON_MIN_CORES 0.10`、`ON_OVER_OFF 3.0`、`FLOOR_CORES 0.01`、`OFF_CTRL_MARGIN 0.05`、`CHEAP_MAX 0.05`、`SCALE_PER_PIXEL 2.0`、`SCALE_FIXED 1.5`，`JUDGED_APIS` 仍是 vk、glx。

## 工具驗證（凍結前做的）
- **自我測試 18/18。** 合成資料裡的 vk-off 改成沒有 X 流量，和真實情況一致。原本的「直方圖是空的就失敗」測試，改成「缺檔才失敗」。
- **反向檢查**（都必須失敗，實際也都失敗了）：A `SCALE_PER_PIXEL=5`；B 換回 01 的 J0 第 2 條；D 換回 02 的直方圖規則。
- **用真實資料重播**（`gl-present-03/judge-replay-tool-check.txt`；**這只是工具驗證，不是判決**，01／02 的判決不變）：
  - 讀 01 和 02 的真實 cell，J0 都是 `TOOL_VALID`，不再因為規則漏洞判無效。
  - 02 剩下的唯一缺口，就是那次真的發生的焦點空讀（`J2_vk INSUFFICIENT_REPS`），這正是改變 2 要處理的。
  - 這一步是 01／02 都缺少的方法：判定器之前只用我自己假設的合成資料測過。

## 揭露
- 本 attempt 的每一項修正，都是在看過 01 和 02 的判準資料之後才決定的，所以門檻一個都不動。
- 用 01 的資料重播時，STEP1 會得到 `PRESENT_COST_IS_X3_PER_PIXEL_COPY`。但那是事後套用修正規則的結果，**不是判決**。判決只看本 attempt 的新 cell。
- vk 的 J3 比值在 01 是 2.07／2.10，在 02 是 2.46／2.32，離門檻 2.0 都不遠。如果本次判 `INCONCLUSIVE`，就照實記錄，不調整門檻。

## 補記（跑之前，2026-09-26，依使用者要求「先確認完再跑，或跑時檢查」）
- **跑之前確認**：把 cell 腳本新改的 `state()` 單獨取出來，用真的 adb（`192.168.1.100:35761`）呼叫 3 次，結果都是 `false true false`（當時前景是 Stable），沒有重讀，引號處理正確。
- **跑的時候檢查**：新增 `gl_present_cellcheck.py`（sha256 `bda27a013b4c02fc…`，fork `8423f0a`）。它 import 凍結的判定器，判定器本身沒改，hash 仍是 `9c5ca536…`。
  每個 main cell 結束就檢查所有 segment 的有效性和單一 cell 的工具條件；不通過就 `CHAIN_STOP`，不跑後面的 cell。
  已在真實 cell 上驗證：02 main-02 會被擋下（`vk-off:invalid:focus_pre=null`），01 main-01、01 main-02、02 main-01 都通過。
  chain 腳本改成 sha256 `fad88634073d5245…`。
- cell 檢查**不做判決**，只負責提早停下。判決仍然只由判定器讀兩個 rep 產生。門檻不變。
