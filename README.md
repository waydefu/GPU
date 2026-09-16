# waydefu/GPU — POCO F8 Ultra Termux:X11 研究紀錄與接續包

完整 runtime 權威樹在工作站 `/root/projects/GPU加速`。
這裡是 GitHub 上可把專案交給下一手的切面：**Markdown + 凍結 judge + R7 證據 + harness + 修復 core-src + skills**。

本倉庫 **沒有** GitHub status checks。Docs PR 綠燈 ≠ 裝置 qualification。
`termux-x11` fork artifact CI 是 **另一個倉庫**。

## 先讀

1. **[`STATUS-HANDOFF-20260917.md`](STATUS-HANDOFF-20260917.md)** ← 入口
2. [`CONTINUATION.md`](CONTINUATION.md) — 怎麼接；R7-05 命令（**未授權，禁止從本 PR 執行**）
3. [`WORKTREE-MAP.md`](WORKTREE-MAP.md) — source SHA / 遠端
4. [`HANDOFF.md`](HANDOFF.md) — 完整 ledger
5. [`ADB-CONNECT.md`](ADB-CONNECT.md)

## 鎖定（2026-09-17）

| 項目 | 狀態 |
|---|---|
| R6 | PASS / 凍結 `0f1e546` |
| RCA-1 | FIXED / DEVICE-PROVEN |
| CASE_LOOP | DEVICE-VALIDATED `7549e36` |
| B-2 | PASS（`b2-requalification-02`） |
| 歷史 R7-04 `7549e36` | 有效 FAIL `halt_mismatch` 凍結 |
| 新 R7-04 `fdfb1ce` | **PASS**（X 9891） |
| R7 overall | **IN PROGRESS / NOT YET PASS** |
| Production Gate A | BLOCKED |
| 裝置 experimental | `1.03.01-fdfb1ce-16.09.26` CI **35103216566** |

## Docs PR 圖

見 [`evidence/session/gate-a-a1/p2-r7-design/WAYDEFU-GPU-PR-MAP-20260916.md`](evidence/session/gate-a-a1/p2-r7-design/WAYDEFU-GPU-PR-MAP-20260916.md)。

歷史：[#1](https://github.com/waydefu/GPU/pull/1) R6 PASS **merged**；[#3](https://github.com/waydefu/GPU/pull/3) stall-obs **merged**；[#5](https://github.com/waydefu/GPU/pull/5) B-2 PASS **merged**；[#2](https://github.com/waydefu/GPU/pull/2)/[#4](https://github.com/waydefu/GPU/pull/4) 不 merge 關閉。

不含：完整 git worktree、xserver submodule、APK、unstripped ELF、B-2 大 logcat、`.gradle`。
APK 從 [termux-x11 CI 35103216566](https://github.com/waydefu/termux-x11/actions/runs/35103216566) 下載，SHA256 必須是 `5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c`。
