# PROOT-BENCH-02 結果：`PROOT_FAST_NO_BENEFIT (rep02:FRAMES_NOT_WORSE)`（2026-09-24 20:48）

判準：`PROOT-BENCH-02-FREEZE.md`（與 01 逐字相同的門檻；資料前凍結）。Cell：`proot-bench-02-dryrun2`（閘門 `DRYRUN_GATE_OK`）、
`proot-bench-02-rep01`、`proot-bench-02-rep02`（皆 `CMD_CAPTURED` rc=0）。判定器輸出：`PROOT-BENCH-02-judge.txt`。
`proot-bench-02-dryrun` 是 19:5x 被 runner 以 `OPSTREAM_BLOCKED screen_not_awake_or_locked` 擋下的格（未消耗，保留為紀錄）。

## 判決
```
rep01: S p0=108.49 pf=82.62 (0.762x) CPU_BETTER=True | tracer p0=24.71 pf=1.52 | idle p0=0.825 pf=0.202 IDLE_OK=True | FRAMES_NOT_WORSE=True
rep02: S p0=107.99 pf=82.85 (0.767x) CPU_BETTER=True | tracer p0=24.64 pf=1.51 | idle p0=0.846 pf=0.193 IDLE_OK=True | FRAMES_NOT_WORSE=False
VERDICT PROOT_FAST_NO_BENEFIT (rep02:FRAMES_NOT_WORSE)
```
六輪全部 VALID；A/A noise 0.022 → 門檻 10%。**不調門檻、不重跑。**

## 描述（不改判決）
| | P0 | PF2 | 變化 |
|---|---|---|---|
| 追蹤器（捲動＋打字） | 24.3–25.2 s | 1.48–1.54 s | **−94%** |
| S（Cursor＋追蹤器＋X3） | 107.3–109.7 s | 82.6–83.1 s | **−24%** |
| 閒置（三者合計） | 0.80–0.85 核 | 0.19–0.20 核 | **−76%** |
| 捲動 p95 | 25.0／25.0／25.0 ms | 25.0／25.0／**33.3** ms | rep02 平均 29.2 > 25.0×1.10 |
| 捲動 >50 ms | 2／1／3 | 1／0／1 | PF2 不多於 P0 |
| 打字 p95 | 16.7（全部） | 16.7（全部） | 相同 |
- 幀間隔以 8.3 ms（120 Hz）為一格：25.0 ms＝3 格、33.3 ms＝4 格。失敗來自 **r02-3-pf 一輪的 p95 高一格**；其餘兩輪 PF2 與全部 P0 都是 25.0。
  是雜訊還是真的變差，這組資料無法區分；01 的六輪（v1 與 P0）p95 全是 25.0／24.9。
- 功能：PF2 的 Cursor 焦點、翻頁、打字全部生效（非 FAIL）。

## 有效性
觸控 0、thermal 0、每輪開跑前 MemAvailable ≥ 4600（等 20 s）、drive_rc 0、identity `Disabled`、追蹤器 arg0 正確（PF2＝`…/out2/bin/proot-fast2`）、
meter 覆蓋每個邊界；結束 12 輪 `survivors=0 tracer_gone=true`、0 次 KILL；事後 run-as 側殘留 0；Stable 前後 JSON 相同（rep01／rep02）。
工具雜湊三個 cell 相同，且與 01 受判工具只差 PF 路徑（去掉 `pf=` 後 md5 相同）；PF2 sha256 前綴 `8a30e9d63aead905`；judge selftest PASS；fork `e4bf7d6`。

## 對日常的處置（依事先承諾）
事先對使用者說「不是 BENEFIT 就保持原狀」。日常啟動器 `f8desk`／`f8desk-external` 已加入 `PD_PROOT_BIN` 切換區塊（備份 `*.bak-20260924-pf2`），
但以 `~/.f8-proot-stock` **預設關閉**：下次開桌面仍用系統 proot。使用者可按捷徑「08 F8 proot 加速版」自行開啟（「07」關回），重開桌面後生效。
