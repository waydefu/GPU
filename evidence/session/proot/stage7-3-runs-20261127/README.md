# Stage 7.3 受控 ABBA 基準測試原始數據索引（2026-11-27）

本目錄保存 Stage 7.3（`fast9+09c` PRoot 常駐 MCP vs Native Hybrid 2.0 `TracerPid=0` Daemon）受控 ABBA 對照實測產物。

## 產物與校驗清單

- **公開去敏版本**：[`stage7-3-abba.public.json`](stage7-3-abba.public.json)（已將 `meta.adb_serial` 私有端點去敏為 `REDACTED_MYRON_ADB_5038` 並附記原始檔 SHA-256；無憑證或路徑外洩）。
- **SHA256 清單**：[`SHA256SUMS`](SHA256SUMS)（針對 `stage7-3-abba.public.json`）。
- **手機本機原始未改動檔**：`stage7-3-abba.json`（`211,816` bytes，SHA-256 `83fa3ce044b71eefbf5a4620102e3015dfcb76aeb19700606a1f1f647907d4e2`，保留本機對核，不推送至公開 repo 以符治理紅線）。
- **實測涵蓋內容**：
  1. Layer A（5 項短命令／小呼叫 × 每輪 30 calls，`n = 10` ABBA 配對，共 20 runs / 項）。
  2. Layer B（10 項重型／混合作業負載，`n = 10` ABBA 配對，全部附真實 `content[0]["text"]` SHA-256 100% 一致性檢查）。
  3. Arm A2（3 項代表工作之 PRoot 逐次一次性啟動參考組，`n = 5`）。
  4. 4 客戶端並發混合負載對照（`4x_PRoot_Fallback` vs `4x_Native_Shared`，`n = 5` ABBA 配對）。
  5. `--auto-start` 冷啟動端到端延遲（保留 7 Android 變數 `n = 10` vs 剝除 7 變數安全退回 PRoot `n = 5`）。
  6. `tracer_sched_cpu_ms`（`/proc/<pid>/schedstat`）、`peak_pss_total_mb`（含 PRoot + Native Daemon + `SwapPss`）、行程級 `majflt`（`0/0`）、ADB `-P 5038` `/proc/vmstat` `pgmajfault`、`hw-trip` 過濾後之真實 CPU 溫度與 `MemAvailable`。
