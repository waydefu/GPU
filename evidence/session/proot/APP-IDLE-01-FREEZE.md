# APP-IDLE-01 — 日常程式閒置 CPU：系統 proot（P0）對 proot-fast2（PF）：判準凍結

**狀態：FROZEN（2026-09-24 22:4x，資料前）。** 使用者：「開始」＋「若數據極好直接開啟日常加速版」。
背景：PROOT-BENCH-02 只量 Cursor；使用者問其他程式。v2 修的是所有程式共用的 PRoot 追蹤器。

## 組態
- 程式（日常桌面圖示的啟動指令，`app_idle_cmd.sh`）：`chatgpt`（ChatGPT 桌面版含 Codex，真設定檔 ~/.config/Codex）、
  `chatgptweb`（chatgpt-web＝Playwright Chromium，真設定檔 ~/.config/chromium，開 chatgpt.com）、`hermes`（hermes-desktop-f8，真設定檔 ~/.config/Hermes）、
  `cursor`（日常無設定檔 → 每輪全新設定檔，旗標同 PROOT-BENCH）。
- 每輪：從 PRoot 外經 run-as 新開一個 proot（P0＝系統 `ea47e17d…`，PF＝`out2/bin/proot-fast2` `8a30e9d6…`），日常 42 參數，DISPLAY=:3（實驗版 X），
  獨立 XDG_RUNTIME_DIR＋dbus-run-session；啟動後 60 s 不量（載入），接著 **60 s 閒置窗 [t0, t1]、無任何輸入**。
- 順序：每個程式 ABBA（P0、PF、PF、P0），程式順序 chatgpt → chatgptweb → hermes → cursor。先乾跑 chatgpt P0＋PF 各一輪（閘門）。
- 計量：run-as 側 meter CSV（session＋追蹤器＋X3 ticks），邊界內插（同 PROOT-BENCH）；結束：run-as 側 end 腳本，失敗即中止 cell。

## 判準
- 閒置核數 = (Δsession＋Δtracer＋ΔX3) / (t1−t0)。noise = max(|P0a−P0b|/mean(P0), |PFa−PFb|/mean(PF))。
- **APP_BENEFIT**：mean(PF) ≤ mean(P0) × (1 − max(0.10, 2×noise))；否則 **APP_NO_BENEFIT**。
- **APP_FAIL**：PF 輪的無效理由全是功能性（t0 時沒有可見視窗、閒置窗內程式不在）而 P0 輪有效。其他無效 → **APP_INVALID**。
- 有效性：觸控 0（錄製器自測通過）、thermal 開跑前 0、t0 前／t1 後 亮屏＋無鎖屏＋實驗版前景、追蹤器 arg0 正確（RUN 行與 CSV 表頭）、
  meter 在 t0／t1 兩側 0.5 s 內有樣本且 ticks 非空、殘留 0、追蹤器結束、runner 層級（Stable 前後不變、mem-guard 未觸發）。
- **DAILY_ENABLE（使用者的「數據極好」）**：四個程式全部 APP_BENEFIT，且四者降幅的中位數 ≥ 30%。
  成立 → 刪除 `~/.f8-proot-stock`（日常桌面下次開啟即用 v2）；不成立 → 保持原狀，照實回報。
- 限制：只量閒置、不代表互動負載；Claude Desktop 無法用此法量（本 session 在其中），日常切換後另量。

## 工具
fork `tests/proot/`：`app_idle.sh`、`app_idle_launch.sh`、`app_idle_cmd.sh`、`app_idle_judge.py`（selftest 11/11，含必紅案例：相等、小幅、
雜訊、PF 無視窗＝FAIL、PF 程式死＝FAIL、P0 無視窗＝INVALID、觸控、缺樣本、殘留、降幅未達 30% 不開日常），沿用 `proot_meter.py`、`proot_bench_end.py`。

## 環境調整（資料前，22:5x）
第一次乾跑 `app-idle-01-dryrun` 被 runner 擋下（`OPSTREAM_BLOCKED x_root_size 1200x2464`，未消耗、保留）：使用者稍早設了
`hide_gesture_line=1`（隱藏底部手勢白條），實驗版可用高度多 48 px → X root 由 1200×2416 變 1200×2464（實體 1200×2608 − 狀態列 144）。
開跑時 `awake=true keyguard=false`（不是鎖屏時的 2239 狀態）。→ `EXPECT_ROOT=1200x2464`，乾跑改名 `app-idle-01-dryrun2`。判準不變。
