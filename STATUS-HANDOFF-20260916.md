# 狀態交接 — 2026-09-16 18:41（UTC+8）

這是狀態快照，不是開工手冊，也不是授權。
倉庫：https://github.com/waydefu/GPU（docs 紀錄；**沒有** PR status checks）
工作站：`/root/projects/GPU加速`
程式碼遠端：https://github.com/waydefu/termux-x11（fork artifact CI ≠ 本倉庫 PR）

```text
R6:       PASS（凍結 0f1e546 / CI 34999213228；歷史資格，裝置已換走）
B-2:      BLOCKED（權威 FAIL = 0d72332 serial 2370 + rerun1 1810 fail-stop）
stall-obs-01: CASE_LOOP DEVICE-PROVEN（feeaa56；X 23034；timeout serial 86）
              這不是 B-2 PASS，也不能推翻 0d72332 fail-stop
CASE_LOOP fix: `327b028` SUPERSEDED；唯一裝置 SHA = **7549e36** CI 35084701124 QUALIFIED / **未安裝**
repair-validation: DESIGNED / NOT STARTED / **不是 B-2**
R7 support artifact: a7528bd COMMITTED + termux-x11 CI 35007764673 QUALIFIED
R7 qualification: NOT STARTED（沒有任何 R7 cell）
Production Gate A: BLOCKED
裝置 APK: feeaa56 / 1.03.01-feeaa56-16.09.26 / CI 35076884763
          com.waydefu.x11gpu / experimental only
Stable :1 PID 14604 / HDMI: 未碰
timeout:  2000 ms 未改
```

先讀本檔。細節見 `HANDOFF.md`、
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md`、
`evidence/session/gate-a-a1/p2-r7-design/WAYDEFU-GPU-PR-MAP-20260916.md`。

`main` 已合併 [PR #1](https://github.com/waydefu/GPU/pull/1) 與 [PR #3](https://github.com/waydefu/GPU/pull/3)。
[PR #2](https://github.com/waydefu/GPU/pull/2) **不 merge 關閉**。
[PR #4](https://github.com/waydefu/GPU/pull/4) **OPEN**（docs snapshot；非 qualification）。

---

## 現在停在哪

裝置 experimental 是 notify-fn diagnostic `feeaa56`。一次授權 observation **CASE_LOOP DEVICE-PROVEN**：serial 86 已發布，renderer 未 consume 約 2 s。NOTIFY/SWAP/NEXT_FENCE 都遠小於 2 s。timeout→Done=0。直接 `pthread_cond_wait` 指令未被 instrument。Hardened source `7549e36` **未安裝**。這**不是** B-2 PASS。B-2 仍 BLOCKED。R7 **資格格未開**。

不准安裝 `7549e36`（需新的 install grant；下一步是獨立 repair-validation，不是 B-2）。不准安裝 `327b028`。不准 retry `runtime-feeaa56/stall-obs-01`。不准開 B-2 矩陣。不准改 timeout。不准開 R7 qualification。

---

## 已完成（只記狀態）

- 凍結 R6 `0f1e546` 三格 PASS（歷史資格）。
- Artifact B `a7528bd` 源碼 + fork CI；B-2 在其上 FAIL；**不是 R7 qualification**。
- EXA Composite wait-false fail-stop `0d72332`：B-2 FAIL REPRODUCED（serial 2370 / 1810）。
- stall-obs-01 on `27d8d1b` / `1f85b80` **STALL_NOT_OBSERVED**（歷史；未打到本 stall）。
- notify-fn `feeaa56` INSTALLED；stall-obs-01 **CASE_LOOP**。
- CASE_LOOP hardened `7549e36` CI **35084701124** QUALIFIED（CLOCK_MONOTONIC + C11 atomics；host RED 151 ms / GREEN 10 ms）。`327b028` **SUPERSEDED**。
- 下一步切法已鎖：獨立 repair-validation cell（experimental only / NO_GATEA_ENV / 證明 CASE_LOOP 關掉）。**尚未授權安裝。不是 B-2。**

---

## 還沒做

- 安裝 `7549e36` 並跑獨立 repair-validation（需新 grant；不是 B-2）。
- 該 cell PASS 之後，另開 B-2 重資格。
- R7 qualification cells。

**後面沒開、現在也不該開**

- R7 裝置 qualification、R8–R10、Gate H、Production enable、termux-x11 origin PR／merge。

---

## 工作樹快照

| 路徑 | HEAD | 角色 | 狀態 |
|---|---|---|---|
| `src/f8-ahb-gatea-r6-retire` | `0f1e546` | 凍結 R6 | 乾淨；不要改 |
| `src/f8-ahb-gatea-exa-timeout` | `0d72332` | timeout 修復源 | 不再是裝置 APK |
| `src/f8-ahb-gatea-stall-diag` | `27d8d1b` | 歷史 SWAP 標記源 | 觀察完成 |
| `src/f8-ahb-gatea-notify-diag` | `1f85b80` | 歷史 call-site notify | 觀察完成 |
| `src/f8-ahb-gatea-notify-fn` | `feeaa56` | 已安裝函式本體 notify | stall-obs-01 CASE_LOOP |
| `src/f8-ahb-gatea-case-loop` | `7549e36` | hardened CASE_LOOP wakeup | **未安裝** |
| `src/f8-ahb-gatea-r7` | `a7528bd` | R7 **support** artifact | 未安裝；qualification 未開 |

---

## 紅線（狀態，不是步驟）

Stable `:1`、HDMI、termux-x11 origin、merge、force、production enable 都沒動。
不准 `±1 UNORM` 當 PASS。不准 silent-retry `r1-unset-oracle`／`stall-obs-01`。
不准把本輪當成 B-2 授權。不准安裝 `327b028`。
