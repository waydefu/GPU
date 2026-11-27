# 勘誤聲明：Stage 5 Native Hybrid 重型掃描加速倍率應為 `1.89×`（釐清 `5.55×` 誤植）

- **日期**：2026-11-27
- **勘誤對象**：[`STAGE6-3-4-CLOSURE-20261127.md`](STAGE6-3-4-CLOSURE-20261127.md)（§1.2 第 68 行及 §二 第 85 行）——該文件依 append-only 治理規則維持原樣不覆寫，由本勘誤獨立更正。

## 誤植與實測對照

`STAGE6-3-4-CLOSURE-20261127.md` 曾寫入「Stage 5 Step 5 單次重型 `python3` 全樹掃描 `5.55×`（`1542.5 → 277.9 ms`）」。經回查 Stage 5 全數原始 JSON 與驗收紀錄，該組數值**無對應之 Stage 5 原始 JSON 佐證**，屬前輪文字誤植。

各 Stage 5 原始檔案實際記載之實測數據如下：

| 來源報告與原始 JSON | 量測架構（是否經橋接器） | 工作負載 | 實測中位數 | 倍率與統計 |
|---|---|---|---:|---:|
| [`STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md`](STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md)<br>[`stage5-step5-20261126/step5-workstation-abba.json`](stage5-step5-20261126/step5-workstation-abba.json)（`hybrid_heavy_probe`） | **經橋接**：PRoot `fast9-combined` 內呼叫 `f8-hybrid-run` → `f8-hybrid-daemon.py`（`TracerPid=0`） | 單次重型 `python3` 全樹掃描（15 輪走訪 `src/f8-proot-fast` 讀檔雜湊） | `123.7 ms` → **`65.4 ms`**（`-46.9%`） | **`1.89×`**（`5/5` 勝，`sign_p = 0.0625`） |
| [`STAGE5-PHASE3-STEP2-HYBRID-20261126.md`](STAGE5-PHASE3-STEP2-HYBRID-20261126.md)<br>[`stage5-hybrid-20261126/hybrid-bench.json`](stage5-hybrid-20261126/hybrid-bench.json) | **經橋接**：逐次 `f8-hybrid-run` 包裝短命 CLI | `git_ops_20x` / `python_scan_10x` / `trivial_jq_50x` / `zstd_jq_5x` | `746.6→748.5` / `396.1→418.4` / `474.4→764.7` / `246.9→521.1 ms` | **`1.00×` / `0.95×` / `0.62×` / `0.47×`**（短 CLI 有反效果） |
| [`STAGE5-PHASE2-ACCEPTANCE-20261126.md`](STAGE5-PHASE2-ACCEPTANCE-20261126.md) §四（`native-hybrid-ab.json`） | **不經橋接**：Termux 原生直接執行（無 `f8-hybrid-run`） | `python_scan`（10×）／`git_ops`（20×） | `python_scan`: `498.58`（`fast8`）／`392.48`（`fast10`）→ `61.33 ms` | **`8.13×`**（vs `fast8`）／**`6.40×`**（vs `fast10`）；`git_ops` `1.57×`／`1.43×` |

## 結論

自 Stage 7.1 起，所有 Native Hybrid 橋接比較與可行性基準**一律以實測 `1.89×`（含橋接開銷）為準**；不再引用 `5.55×`，亦不以未實測比例推估整體工作站節省百分比。
