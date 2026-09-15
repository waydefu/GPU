# 狀態交接 — 2026-09-16 00:49（UTC+8）

這是狀態快照，不是開工手冊，也不是授權。  
倉庫：https://github.com/waydefu/GPU  
工作站：`/root/projects/GPU加速`

```text
裝置 APK: 95e6f96 / com.waydefu.x11gpu / experimental only
Writer:   src/f8-ahb-gatea-r6-retire @ 95e6f96
          branch fix/gatea-r6-present-retirement-20260915
          未提交；host 測試綠；關帳未完成
Production Gate A: BLOCKED
R7: STOP
Stable :1 / HDMI: 未碰
本倉庫不是 R6 PASS，也不是 termux-x11 源碼遠端
```

先讀本檔。細節見 `PLANNER-BRIEF-20260915.md`、`PROJECT-PROGRESS-20260915.md`、  
`GATE-A-R6檢查與R7-R10-GateH計畫書-20260915.md`。  
`HANDOFF.md` 的 runtime 梯子尚未寫入這條未提交 writer 樹。

---

## 現在停在哪

Gate A P2 裝置資格：R1–R5 PASS。歷史 R6-D1 PASS 在凍結 `9369553`。  
新 APK `95e6f96` 上 D2-INFLIGHT 五格已跑完，舊 reject-only oracle 全 FAIL；COMPLETED serial S 已證明；物理上 GPU 常快於 X dispatch。D2-OOM 未跑。

Present GPU-copy 提前 ACK 的修正已寫在隔離 worktree，未 commit、未 CI、未裝機。  
Host 靜態／合成測試全綠。timeout／loss／teardown runtime 未證明。R7 未開始。

本倉庫 `fbbb70d` 起放的是規劃用 md + 核心 C／judge，不含 APK、logcat、完整 worktree。

---

## 已完成（只記狀態）

- R3 self-wait 已在 `d9b7f60` 修正並 PASS。
- R5 backpressure 已在 `37d8393` 修正並 PASS。
- `95e6f96` 已補 legacy COMPLETED telemetry 與 wait-or-fatal，並裝在 experimental。
- Writer 上有 `present_gpu_copy_retire_or_fatal()`；present 內可執行 raw ACK 只剩 helper 一處。
- Host judge 已改雙分支（busy-reject／quiescent-admit），LEASE 認 production `serial=0`。
- 五格歷史 D2 cell 檔案未改寫；host 重放會走 quiescent。
- 規劃 md 已寫、已推本倉庫；Documents 那份 R6／R7–R10／Gate H 計畫書也在根目錄。

---

## 還沒做

**Writer 關帳**

- `src/f8-ahb-gatea-r6-retire` 未 commit（本倉庫快照 ≠ 那棵樹）。
- `xserver.patch` 檔尾仍追加第二組 Present hunk，未併回既有 patch。
- 獨立複核未做。
- 工作站 `HANDOFF.md`／`TEST-MATRIX.md`／`AGENTS.md` 未更新。

**新 APK 之後才存在的資格**

- fork push、CI、只裝 experimental。
- 新 APK 上的 D1、雙分支 D2-INFLIGHT（歷史五格不可覆寫、不可 silent-retry）。
- D2-OOM。
- timeout／renderer-loss、scrap／destroy／CloseScreen 的裝置證明。

**後面沒開、現在也不該開**

- R7（缺 `TERMUX_X11_GATEA_TEST_FAULT`；不可與 R6 並行寫 C）。
- R8–R10、Gate H、Production enable、PR／merge／origin。

---

## 工作樹快照

| 路徑 | HEAD | 角色 | 狀態 |
|---|---|---|---|
| `src/f8-ahb-gatea-a1` | `88e3f17` | 凍結 control | 乾淨 |
| `src/f8-ahb-gatea-xpump` | `d9b7f60` | R3 X-pump | 乾淨 |
| `src/f8-ahb-gatea-r5-fix` | `37d8393` | R5 回滾點 | 乾淨 |
| `src/f8-ahb-gatea-r6` | `95e6f96` | 已安裝源 | 乾淨；不要改 |
| `src/f8-ahb-gatea-r6-retire` | `95e6f96` + 未提交 | writer | 髒 `xserver.patch` |
| `src/f8-ahb-d0b-r1` | `a6cc795` | 無關 D0b | 髒 6 檔；不要當 R6 去清 |

---

## 紅線（狀態，不是步驟）

Stable `:1`、HDMI、PR、merge、origin、force、production enable 都沒動，也還沒授權去動。  
不准 `±1 UNORM` 當 PASS。不准 silent-retry PROTO=0、R6-D1、既有 `95e6f96` D2 格。  
不准重跑 `88e3f17`／`8479997`／`6c7ee6f`／`98b0011` 的 R3，也不准在 `d9b7f60` 再重試 R5。  
測試檔在關帳那輪被凍結，沒改。
