# APP-IDLE-01 結果：`DAILY_ENABLE false`（2026-09-24 23:5x）

判準：`APP-IDLE-01-FREEZE.md`（資料前凍結；唯一調整是資料前的 EXPECT_ROOT 1200×2464，見該檔）。
Cell：`app-idle-01-dryrun`（BLOCKED x_root，未消耗）、`app-idle-01-dryrun2`（閘門 `DRYRUN_GATE_OK`）、`app-idle-01`（16 輪，`CMD_CAPTURED` rc=0）。
判定器輸出：`APP-IDLE-01-judge.txt`。工具雜湊兩個 cell 相同（launch `2cc164d3`、cmd `a43f2b4b`、meter `74ee1cdf`、end `102df646`）、
judge `d3c500e3`（selftest 11/11）、PF2 `8a30e9d6`；fork `9c190e7`。

## 判決
| 程式 | P0 閒置（兩輪） | PF2 閒置（兩輪） | mean 比 | noise → 門檻 | 判決 |
|---|---|---|---|---|---|
| chatgpt（ChatGPT 桌面版含 Codex） | 0.104／0.071 | 0.042／0.046 | 0.501（−50%） | 0.376 → −75% | APP_NO_BENEFIT |
| chatgptweb（Chromium，chatgpt.com） | 0.989／0.945 | 0.855／0.884 | 0.899（−10%） | 0.046 → −10% | **APP_BENEFIT** |
| hermes（Hermes 桌面版） | 0.170／0.170 | 0.101／0.121 | 0.652（−35%） | 0.176 → −35.2% | APP_NO_BENEFIT |
| cursor（全新設定檔） | 0.547／0.528 | 0.065／0.391 | 0.425（−58%） | 1.429 → −286% | APP_NO_BENEFIT |
（單位：核，閒置 60 s 的 session＋追蹤器＋X3。）
`DAILY_ENABLE false`（需四個都 APP_BENEFIT 且降幅中位數 ≥ 30%；中位數 42%，但只有 1/4 BENEFIT）。**日常保持原狀（`~/.f8-proot-stock` 仍在）。不調門檻、不重跑。**

## 描述（不改判決）
- 每個程式內，兩輪 PF2 **都低於**兩輪 P0：4 程式 × 4 組兩兩比較＝16/16 都是 PF2 較低。
- 未達標的原因都在 noise 項：閒置量小（0.04–0.2 核），兩輪間的絕對小差異變成大相對雜訊（chatgpt P0 0.104 vs 0.071；
  cursor 每輪全新設定檔，PF2 一輪 0.065、一輪 0.391）。hermes 差門檻 0.2 個百分點。
- **chatgpt-web 閒置就吃約 0.9–1.0 核**（chatgpt.com 頁面＋`--disable-gpu` 軟體合成），是四者中最大的閒置負擔；
  ChatGPT 桌面版同樣是 ChatGPT，閒置只有 0.04–0.10 核（約 1/10–1/20）。

## 有效性
16 輪全 VALID：觸控 0、thermal 0、t0 前／t1 後亮屏＋無鎖屏＋實驗版前景、每輪有視窗（chatgpt／chatgptweb 2、hermes／cursor 1）、
閒置窗內程序數 16–22、追蹤器 arg0 正確、meter 覆蓋邊界；結束 305 次 TERM、0 次 KILL、`survivors=0 tracer_gone=true`；
事後 run-as 側與 PRoot 側（前綴比對）殘留 0；Stable 前後 JSON 相同。
