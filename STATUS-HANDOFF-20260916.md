# 狀態交接 — 2026-09-16（UTC+8）R6 PASS `0f1e546`

這是狀態快照，不是開工手冊。
倉庫：https://github.com/waydefu/GPU
工作站：`/root/projects/GPU加速`
程式碼遠端：https://github.com/waydefu/termux-x11 分支 `fix/gatea-r6-present-retirement-20260915`

```text
裝置 APK: 0f1e546 / com.waydefu.x11gpu / experimental only
version:  1.03.01-0f1e546-15.09.26
CI:       34999213228
APK SHA256: 2bc4c8ba2b6a11928a3a6b76e04fcd9acf0bacfe11f88afd0a698c8c81b10851
Build ID: 263bee5f7d41087b0bd7fa180d47fdafd12b2ecf
Source:   src/f8-ahb-gatea-r6-retire HEAD 0f1e54699d0b11a781f2c044fbc77505f8a53bd8
          branch fix/gatea-r6-present-retirement-20260915（fork 已推；origin 無此分支）
R6: PASS（D1 / D2-INFLIGHT QUIESCENT-ADMIT / D2-OOM，皆首次）
Production Gate A: BLOCKED
R7–R10 / Gate H: 未跑（R7 已另授權，不在本快照寫碼）
Stable :1 / HDMI: 未碰
```

先讀 `HANDOFF.md`。規劃歷史見 `PLANNER-BRIEF-20260915.md`（已 SUPERSEDED）。
R6／R7–R10／Gate H 計畫書：`GATE-A-R6檢查與R7-R10-GateH計畫書-20260915.md`。

---

## 現在停在哪

Gate A P2 裝置資格：**R1–R6 PASS**。Production Gate A 仍 BLOCKED。
歷史 `9369553` D1 與 `95e6f96` D2 五格保持原檔，不可 silent-retry、不可覆寫。

termux-x11 fork 的 qualified source 是 `0f1e546`。不要把誤開的 fork PR 當成要 merge 進 origin 的路徑。

---

## 已完成

- R3 self-wait：`d9b7f60` PASS
- R5 backpressure：`37d8393` PASS
- R6 retirement：`0f1e546` COMMITTED + CI **34999213228** + experimental INSTALLED
- R6-D1 X 29152 first-attempt PASS
- R6-D2-INFLIGHT X 31369 first-attempt PASS，分支 QUIESCENT-ADMIT
- R6-D2-OOM X 2638 first-attempt PASS（env armed 且 event 33 執行）
- Present ACK 集中在 `present_gpu_copy_retire_or_fatal`

## 還沒做（不是本 PR 的工作）

- R7 `TERMUX_X11_GATEA_TEST_FAULT` Artifact B（另開 worktree）
- R8–R10、Gate H、Production enable
- timeout／renderer-loss／scrap／destroy／CloseScreen 的裝置格仍多為 SOURCE-PROVEN
- 不准 merge 進 `termux/termux-x11` origin、不准碰 Stable／HDMI

## 工作樹快照

| 路徑 | HEAD | 角色 | 狀態 |
|---|---|---|---|
| `src/f8-ahb-gatea-a1` | `88e3f17` | 凍結 control | 乾淨 |
| `src/f8-ahb-gatea-xpump` | `d9b7f60` | R3 X-pump | 乾淨 |
| `src/f8-ahb-gatea-r5-fix` | `37d8393` | R5 回滾點 | 乾淨 |
| `src/f8-ahb-gatea-r6` | `95e6f96` | 歷史 R6 source | 乾淨；不要改 |
| `src/f8-ahb-gatea-r6-retire` | `0f1e546` | R6 qualified source | 乾淨 vs fork |
