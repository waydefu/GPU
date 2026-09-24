# PROOT-BENCH-01 結果：`PROOT_FAST_NO_BENEFIT`（2026-09-24）

判準：`PROOT-BENCH-01-FREEZE.md`（資料前凍結；工具修正與乾跑 02 都在受判資料之前，門檻未改）。
Cell：`proot-bench-01-rep01`、`proot-bench-01-rep02`（runner 皆 `CMD_CAPTURED` rc=0）。判定器輸出：`PROOT-BENCH-01-judge.txt`。

## 判決
```
VERDICT PROOT_FAST_NO_BENEFIT (rep01:CPU_BETTER, rep02:CPU_BETTER)
```
六輪全部 VALID。PF 的 Cursor 功能正常（非 FAIL）。IDLE_OK、FRAMES_NOT_WORSE 兩次都成立；**只有 CPU_BETTER 不成立**。

| rep | S(P0) | S(PF) | PF/P0 | 門檻 | 追蹤器 P0 → PF | 閒置 P0 → PF（核） |
|---|---|---|---|---|---|---|
| 01 | 101.92 s | 92.44 s | 0.907 | ≤ 0.900 | 23.71 → 16.28 s | 0.811 → 0.745 |
| 02 | 102.13 s | 97.02 s | 0.950 | ≤ 0.900 | 23.76 → 17.48 s | 0.815 → 0.770 |

A/A noise 0.003（P0/P0' 差 0.2%、PF/PF' 差 0.3%）→ 門檻由 10% 下限主導。rep01 差 0.7 個百分點未達；**不調門檻、不重跑**。

## 白話解讀（描述，不改判決）
- `S` 是捲動＋打字共 60 秒內，Cursor＋它的追蹤器＋X3 用掉的 CPU 秒數：P0 約 102 s ＝ 平均 **1.7 核**。
- proot-fast 讓**追蹤器**本身少了約 30%（23.7 → 16.3–17.5 s，即 0.40 → 0.28 核），但追蹤器只是總量的約 23%，
  換算到總量只少 5–9%（約 0.1–0.16 核）。Cursor＋X3（S 減追蹤器）兩組幾乎相同（六輪 76.2–79.9 s）。
- 追蹤器在 PF 下仍有 0.28 核：socket 收發不再攔之後，剩下的是其他仍被攔的 syscall（路徑轉換類、fake_id0 的 sendmsg 等），這次沒有拆解。
- rep01 與 rep02 的 PF 相差 5%（92.4 vs 97.0 s），比同 rep 內的 A/A 大；判準的 noise 定義只看同 rep 重複，這個跨 rep 差異照實記錄，不另行處理。

## 有效性摘要
- 觸控 0、thermal 0（未等待）、每輪開跑前 MemAvailable 5978–6211 MB、drive_rc 0、Cursor identity `Disabled`、焦點／翻頁／打字都生效。
- 追蹤器 arg0 六輪都正確；meter CSV 在每個階段邊界兩側 0.5 s 內有樣本、ticks 非空、session 程序數 ≥ 1。
- 結束：六輪 `survivors_after_kill=0 tracer_gone=true`，全部 TERM 即結束、0 次 KILL（`proot-bench-kills.txt`／`<run>.end.log` 逐 pid 記錄）；
  事後 run-as 側掃描殘留 0。Stable 兩個 cell 前後 JSON 相同。
- 工具雜湊與乾跑 02 完全一致（`TOOLS`／`PROOTS`／`WS_FILE` 三行 md5 相同）；judge `86f0159baf0dd593`（selftest 12/12 PASS）；fork `9f7bad4`，worktree clean。

## 對使用者目標的意義
- 以本判準，**不值得為了這個修補換掉日常桌面的 proot**（要整個 PRoot 重開，收益約 0.1 核）。
- 追蹤器仍是可觀的單執行緒負載（活動時 0.28–0.40 核）；若要再從 PRoot 下手，下一步應先**拆解追蹤器剩下的時間花在哪些 syscall**，
  再決定是否值得做更深的修補；這是新的方向，需使用者決定。
