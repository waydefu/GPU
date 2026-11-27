# Stage 6.2 原始區塊資料索引與去敏紀錄（2026-11-27）

本目錄保存 Stage 6.2 乾跑（`DRYRUN`）、第一輪 ABBA（`B1 P1 P2 B2`）、紅色對照（`S1`）與判決輸出之逐批原始 JSON 產物。

## 去敏處理說明

- **保留不變**：所有批次時間戳、`wall_ms`、`inner_total_ms`、`tracer_cpu_ms`、`launch_ms`、`click_p50/p95`、`rAF p50/p95/p99`、掉幀、`peak_pss_mb`、`rc`、`orphan_pids`、5 秒頻率／溫度／電量／`Thermal Status` 取樣、`vmstat_delta`、`zram`、`termux_kills`（皆為 `[]`）及 `lmkd` `am_cpu` 行。
- **去敏處理**：僅將 `new_event_lines` 中非 `com.termux` 第三方 Android App 之 `am_kill` 套件名稱替換為 `<redacted-non-termux-pkg>`（保留時間戳、`normal_mem_pressure` 原因與觸發總行數）；另無任何私網 IP、憑證或本地工作區內部路徑。
- **權限限制標記**：`psi` 為 `null`、`zram0/mm_stat` 不可讀（`UNAVAILABLE_DUE_TO_PERMISSION`）；`zram` 取自 `dumpsys meminfo`。

## 檔案與 SHA256 對照

完整雜湊清單見 [`SHA256SUMS`](SHA256SUMS)（公開去敏檔）與 [`ORIGINAL_ON_DEVICE_SHA256SUMS`](ORIGINAL_ON_DEVICE_SHA256SUMS)（手機本機原始檔 `/data/data/com.termux/files/home/build/proot-fast/stage6_2_runs/`）。

| 檔案 | 說明 | 批數／狀態 |
|---|---|---|
| [`DRYRUN_attempt1.json`](DRYRUN_attempt1.json) | 30 秒乾跑（`Charge counter` 步階校準、不計入結果） | `13/13` 批、`BLOCK_VALID` |
| [`B1_attempt1.json`](B1_attempt1.json) | 第一輪均衡模式區塊 1（`balanced`） | `74/74` 批、`BLOCK_VALID` |
| [`P1_attempt1.json`](P1_attempt1.json) | 第一輪效能模式區塊 1（`performance`） | `79/79` 批、`BLOCK_VALID` |
| [`P2_attempt1.json`](P2_attempt1.json) | 第一輪效能模式區塊 2（`performance`） | `75/75` 批、`BLOCK_VALID` |
| [`B2_attempt1.json`](B2_attempt1.json) | 第一輪均衡模式區塊 2（`balanced`） | `74/74` 批、`BLOCK_VALID` |
| [`S1_attempt1.json`](S1_attempt1.json) | 省電模式紅色對照（`power_saver`） | `68/68` 批、`BLOCK_VALID` |
| [`series_verdict.json`](series_verdict.json) | `stage6_2_judge.py` 對上述 5 塊輸出（缺 `B3–B4` 故為 `INVALID`） | 證據保留 |
