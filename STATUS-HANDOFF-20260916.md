# 狀態交接 — 2026-09-16 13:22（UTC+8）stall-obs **STALL_NOT_OBSERVED**

這是狀態快照，不是開工手冊，也不是授權。
倉庫：https://github.com/waydefu/GPU
工作站：`/root/projects/GPU加速`

```text
裝置 APK: 27d8d1b / 1.03.01-27d8d1b-16.09.26 / CI 35056388284
          SHA256 142b6e1f…45b0  Build ID e8d859dd…5e2c
          com.waydefu.x11gpu / experimental only
凍結 R6:  0f1e546 PASS（src/f8-ahb-gatea-r6-retire，勿改）
stall-obs-01: STALL_NOT_OBSERVED（X 16420；1000/1000；timeout=0）
              SWAP max 1.468 ms / NEXT_FENCE max 4.806 ms
              CASE_A/B/C NOT CLASSIFIED
B-2:      BLOCKED（權威 FAIL 仍是 0d72332 serial 2370 + rerun1 1810）
R7:       NOT STARTED
Production Gate A: BLOCKED
Stable :1 PID 17922 / HDMI: 未碰
timeout:  2000 ms 未改
本倉庫不是 termux-x11 源碼遠端，也不授權開 R7 / B-2 / retry
```

先讀本檔。細節見 `HANDOFF.md`、
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md`、
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-27d8d1b/GATE-A-P2-STALL-OBS-01-20260916.md`。

歷史快照：
- [PR #1](https://github.com/waydefu/GPU/pull/1) R6 PASS `0f1e546`
- [PR #2](https://github.com/waydefu/GPU/pull/2) B-2 RCA + EXA timeout 修復摘錄（當時裝置仍是 `a7528bd`）

---

## 現在停在哪

裝置 experimental 是 stall-phase diagnostic `27d8d1b`。一次授權 observation **沒有**出現 >2 s EXA Composite wait。標記有活（3712 筆），兩段被包住的 EGL 都很快。這**不是** B-2 PASS，也**不能**推翻 `0d72332` fail-stop。

不准 retry `runtime-27d8d1b/stall-obs-01`。不准開 B-2 矩陣。不准改 timeout。不准開 R7。

---

## 已完成（只記狀態）

- 凍結 R6 `0f1e546` 三格 PASS（歷史資格）。
- EXA Composite wait-false fail-stop 已 commit `0d72332`、CI、曾裝機；B-2 在該 APK **FAIL REPRODUCED**。
- stall-phase 標記 APK `27d8d1b` CI **35056388284** QUALIFIED 後已裝 experimental。
- stall-obs-01 **STALL_NOT_OBSERVED**；Stable PID 17922 未動。

---

## 還沒做

- 下一次 stall observation（需新授權；本格禁止 retry）。
- B-2 重資格（仍 BLOCKED）。
- R7 cells。

**後面沒開、現在也不該開**

- R7 裝置 cells、R8–R10、Gate H、Production enable、termux-x11 origin PR／merge。

---

## 工作樹快照

| 路徑 | HEAD | 角色 | 狀態 |
|---|---|---|---|
| `src/f8-ahb-gatea-r6-retire` | `0f1e546` | 凍結 R6 | 乾淨；不要改 |
| `src/f8-ahb-gatea-exa-timeout` | `0d72332` | timeout 修復源 | 不再是裝置 APK |
| `src/f8-ahb-gatea-stall-diag` | `27d8d1b` | 已安裝標記源 | 觀察完成 |
| `src/f8-ahb-gatea-r7` | `a7528bd` | 歷史 Artifact B | 未安裝 |

---

## 紅線（狀態，不是步驟）

Stable `:1`、HDMI、termux-x11 origin、merge、force、production enable 都沒動。
不准 `±1 UNORM` 當 PASS。不准 silent-retry `r1-unset-oracle`／`stall-obs-01`。
不准把本格 1000/1000 當成 B-2 PASS。不准現在開 R7。
