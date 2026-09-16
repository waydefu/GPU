# 狀態交接 — 2026-09-16 10:42（UTC+8）

這是狀態快照，不是開工手冊，也不是授權。
倉庫：https://github.com/waydefu/GPU
工作站：`/root/projects/GPU加速`

```text
裝置 APK: a7528bd / 1.03.01-a7528bd-15.09.26 / CI 35007764673
          com.waydefu.x11gpu / experimental only
凍結 R6:  0f1e546 PASS（src/f8-ahb-gatea-r6-retire，勿改）
B-2:      BLOCKED（權威 FAIL = runtime-a7528bd/r1-unset-oracle/ 999/1000）
R7:       NOT STARTED
Production Gate A: BLOCKED
Stable :1 PID 17922 / HDMI: 未碰
EXA Composite timeout 修復: 本機 worktree，未授權裝置重跑
本倉庫不是 termux-x11 源碼遠端，也不授權開 R7
```

先讀本檔。細節見 `HANDOFF.md`、
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md`、
`evidence/session/gate-a-a1/p2-r7-design/GATE-A-P2-EXA-COMPOSITE-TIMEOUT-REPAIR-20260916.md`。

歷史 R6 PASS 快照另見尚未合併的 [PR #1](https://github.com/waydefu/GPU/pull/1)（`r6-pass-0f1e546`）。

---

## 現在停在哪

裝置 experimental 是 Artifact B `a7528bd`。B-2 R1-unset 第一次資格 **FAIL**（stress 999/1000）。
diagnostic-01 未重現（1000/1000）。diagnostic-02 **RCA IDENTIFIED**：3× `PIXEL_RGB_MISMATCH`（`got == dst_px`）綁定 3× EXA Composite wait-timeout 後仍 `Gcomp Done`。

修復在隔離 worktree `src/f8-ahb-gatea-exa-timeout` / `fix/gatea-exa-composite-timeout-20260916`：
wait-false → `gateAXFatal("x-exa-composite-wait", TIMEOUT)`。Host verifier RED→GREEN。
**未 commit 到 termux-x11 fork、未 CI、未裝機、未授權 B-2 重跑。** R7 未開始。

本倉庫只放 Markdown + 核心 patch／judge，不含 APK、logcat dump、完整 worktree。

---

## 已完成（只記狀態）

- 凍結 R6 `0f1e546` 三格 PASS（歷史資格）。
- Artifact B commit／fork CI **35007764673**／只裝 experimental。
- B-2 R1-unset 權威 FAIL 已保存，不可 silent-retry。
- diagnostic-02 證明 timeout→Done→GetImage 舊 dest。
- EXA Composite Done 的 fail-stop 補丁已在隔離 worktree 通過 host 靜態測試。

---

## 還沒做

- 修復 lineage 的 commit／fork push／CI／只裝 experimental（需另授權）。
- 新 APK 上的 B-2 重資格（不可覆寫 `r1-unset-oracle/`）。
- R7 cells。
- DoneSolid／DoneCopy 同型 wait-false→ack（FINDING，未修）。

**後面沒開、現在也不該開**

- R7 裝置 cells、R8–R10、Gate H、Production enable、termux-x11 origin PR／merge。

---

## 工作樹快照

| 路徑 | HEAD | 角色 | 狀態 |
|---|---|---|---|
| `src/f8-ahb-gatea-r6-retire` | `0f1e546` | 凍結 R6 | 乾淨；不要改 |
| `src/f8-ahb-gatea-r7` | `a7528bd` | 已安裝源 | 乾淨；不要就地改 |
| `src/f8-ahb-gatea-exa-timeout` | `a7528bd` + 未提交 | Composite timeout 修復 | 髒 `InitOutput.c` |

---

## 紅線（狀態，不是步驟）

Stable `:1`、HDMI、termux-x11 origin、merge、force、production enable 都沒動。
不准 `±1 UNORM` 當 PASS。不准 silent-retry `r1-unset-oracle`。
不准把 diagnostic 1000/1000 或本修復 host 綠當成 B-2 PASS。不准現在開 R7。
