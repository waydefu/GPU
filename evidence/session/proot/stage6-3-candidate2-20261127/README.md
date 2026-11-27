# Stage 6.3 候選 2 逐次 ABBA 原始數據索引（2026-11-27）

本目錄保存 Stage 6.3 候選 2（Node／Electron V8 heap 上限與 worker 併發上限）有界可逆實驗之逐次原始 JSON 產物。

## 內容摘要

- 原始檔案：[`candidate2_result.json`](candidate2_result.json)（無私網 IP、無憑證、無第三方套件名稱，與手機本機 `/data/data/com.termux/files/home/build/proot-fast/stage6_3_runs/candidate2_result.json` 逐位元組一致）。
- SHA256 清單：[`SHA256SUMS`](SHA256SUMS)（`ea6db78c17f8392ddd3c4d739fadba2b9e0a46d7ededeaf0541c6c9cdfb9e2cd`）。
- 內含逐次原始數據：
  - `2A_v8_cap`：`default` vs `cap_512`（`--max-old-space-size=512`）3 輪 ABBA 共 **6 對（12 次）** 逐次 `wall_ms`、`peak_pss_mb`、`peak_rss_mb`、`mem_avail_min_mb`、`pgmajfault_delta`、`pswpin_delta`、`pswpout_delta`、`psi: null`。
  - `2A_compat_probe`：`cap_512`、`cap_1024`、`default` 於 `250 MB`／`650 MB` 負載的 6 次相容性實測（`cap_512` 於 `650 MB` 回傳 `rc=255`，原生重現 `rc=134` `JavaScript heap out of memory`）。
  - `2B_concurrency_cap`：工作量等價 `seq_2x2`（兩波 2+2）vs `par_4x4`（單波 4+4）3 輪 ABBA 共 **6 對（12 次）** 逐次原始紀錄。
- **權限標記**：本裝置非 Root 下 `/proc/pressure/*`（PSI）與 `/sys/block/zram0/mm_stat` 皆 `Permission denied`，`psi` 明確記為 `null`（`UNAVAILABLE_DUE_TO_PERMISSION`）。
