# 狀態交接 — 2026-09-16 13:55（UTC+8）

這是狀態快照，不是開工手冊，也不是授權。
倉庫：https://github.com/waydefu/GPU（docs 紀錄；**沒有** PR status checks）
工作站：`/root/projects/GPU加速`
程式碼遠端：https://github.com/waydefu/termux-x11（fork artifact CI ≠ 本倉庫 PR）

```text
R6:       PASS（凍結 0f1e546 / CI 34999213228；歷史資格，裝置已換走）
B-2:      BLOCKED（權威 FAIL = 0d72332 serial 2370 + rerun1 1810 fail-stop）
stall-obs-01: STALL_NOT_OBSERVED（27d8d1b；1000/1000；timeout=0）
              這不是 B-2 PASS，也不能推翻 0d72332 fail-stop
R7 support artifact: a7528bd COMMITTED + termux-x11 CI 35007764673 QUALIFIED
R7 qualification: NOT STARTED（沒有任何 R7 cell）
Production Gate A: BLOCKED
裝置 APK: 27d8d1b / 1.03.01-27d8d1b-16.09.26 / CI 35056388284
          com.waydefu.x11gpu / experimental only
Stable :1 PID 17922 / HDMI: 未碰
timeout:  2000 ms 未改
```

先讀本檔。細節見 `HANDOFF.md`、
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md`、
`evidence/session/gate-a-a1/p2-r7-design/WAYDEFU-GPU-PR-MAP-20260916.md`。

`main` 已合併 [PR #1](https://github.com/waydefu/GPU/pull/1)（R6 PASS 證據）與 [PR #3](https://github.com/waydefu/GPU/pull/3)（現況；含 #2）。
[PR #2](https://github.com/waydefu/GPU/pull/2) **不 merge 關閉**。歷史 `5580e73` 過期。

---

## 現在停在哪

裝置 experimental 是 stall-phase diagnostic `27d8d1b`。一次授權 observation **沒有**出現 >2 s EXA Composite wait。這**不是** B-2 PASS。B-2 仍 BLOCKED。R7 **資格格未開**（只有 support artifact）。

不准 retry `stall-obs-01`。不准開 B-2 矩陣。不准改 timeout。不准開 R7 qualification。

---

## 已完成（只記狀態）

- 凍結 R6 `0f1e546` 三格 PASS（歷史資格）。
- Artifact B `a7528bd` 源碼 + fork CI；B-2 在其上 FAIL；**不是 R7 qualification**。
- EXA Composite wait-false fail-stop `0d72332`：B-2 FAIL REPRODUCED（serial 2370 / 1810）。
- stall-obs-01 **STALL_NOT_OBSERVED**。
- waydefu/GPU docs：`#1`+#3 已 merge；`#2` 不 merge 關閉。本倉庫仍 **無 status checks**。

---

## 還沒做

- 下一次 stall observation（需新授權；本格禁止 retry）。
- B-2 重資格（仍 BLOCKED）。
- R7 qualification cells。

**後面沒開、現在也不該開**

- R7 裝置 qualification、R8–R10、Gate H、Production enable、termux-x11 origin PR／merge。

---

## 工作樹快照

| 路徑 | HEAD | 角色 | 狀態 |
|---|---|---|---|
| `src/f8-ahb-gatea-r6-retire` | `0f1e546` | 凍結 R6 | 乾淨；不要改 |
| `src/f8-ahb-gatea-exa-timeout` | `0d72332` | timeout 修復源 | 不再是裝置 APK |
| `src/f8-ahb-gatea-stall-diag` | `27d8d1b` | 已安裝標記源 | 觀察完成 |
| `src/f8-ahb-gatea-r7` | `a7528bd` | R7 **support** artifact | 未安裝；qualification 未開 |

---

## 紅線（狀態，不是步驟）

Stable `:1`、HDMI、termux-x11 origin、merge、force、production enable 都沒動。
不准 `±1 UNORM` 當 PASS。不准 silent-retry `r1-unset-oracle`／`stall-obs-01`。
不准把 stall-obs 1000/1000 當成 B-2 PASS。不准把「R7 support CI PASS」或「GPU PR 開著」當成 R7 已開始。不准現在開 R7 qualification。
