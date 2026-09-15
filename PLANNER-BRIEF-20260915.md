# Gate A / GPU加速 — 後續規劃包（2026-09-15 22:00 UTC+8）

> **SUPERSEDED for current runtime.** Live authority is `HANDOFF.md` (2026-09-16):
> device `0f1e546` / CI **34999213228** / **R6 PASS** / Production Gate A BLOCKED /
> STOP BEFORE R7. Keep this 20260915 planner text as a historical planning
> snapshot. Do not treat its “未 CI／未裝機／NOT YET VERIFIED” sentences as current.

給尚未進入工作樹的規劃者。這不是 R6 PASS，也不是授權開 R7。

```text
裝置 APK: 95e6f96（experimental only）
Writer:   src/f8-ahb-gatea-r6-retire @ 0f1e546
           branch fix/gatea-r6-present-retirement-20260915
           本機已 commit；R6 NOT YET VERIFIED；未 CI／未裝機
Production Gate A: BLOCKED
R7: STOP / source-blocked
Stable :1 / HDMI: 未碰
```

先讀本檔，再讀 `PROJECT-PROGRESS-20260915.md`、`HANDOFF.md`。
`HANDOFF.md` 的 runtime 梯子仍停在「D2 physical race / 下一步 A·B·C」，
**尚未寫入** 這條未提交 retirement 工作樹。以本檔與 writer 磁碟為準。

---

## 1. 目前進度（一句話）

Gate A P2 裝置資格做到 **R5 PASS + 歷史 R6-D1 PASS（9369553）+ 新 APK D2-INFLIGHT 五格已跑完但舊 reject-only oracle 全 FAIL**。  
Present GPU-copy 提前 ACK 的修正 **已寫在隔離 worktree，未 commit、未 CI、未裝機**。  
Host 靜態／合成測試全綠。D2-OOM、timeout／loss、teardown runtime **未證明**。R7 未開始。

## 2. 工作樹地圖

| 路徑 | HEAD | 角色 | 狀態 |
|---|---|---|---|
| `src/f8-ahb-gatea-a1` | `88e3f17` | 凍結 control | 乾淨 |
| `src/f8-ahb-gatea-xpump` | `d9b7f60` | R3 X-pump | 乾淨 |
| `src/f8-ahb-gatea-r5-fix` | `37d8393` | R5 修正／回滾點 | 乾淨 |
| `src/f8-ahb-gatea-r6` | `95e6f96` | 已安裝 R6 源 | 乾淨；**不要改** |
| `src/f8-ahb-gatea-r6-retire` | `95e6f96` + 未提交 diff | 唯一 writer | parent 髒 `xserver.patch`；xserver submodule 為 patch-applied |
| `src/f8-ahb-d0b-r1` | `a6cc795` | 無關 D0b | 髒 6 檔；**不要 revert** |

`/tmp` 兩個 git worktree 記錄已 prunable，目錄不存在。

## 3. 目前架構

### 3.1 產品邊界

- Daily driver：`com.termux.x11` `:1` `-legacy-drawing`。永遠不換包、不拿來跑 Gate A。
- 實驗：`com.waydefu.x11gpu` `:3`。目前裝置 APK `1.03.01-95e6f96-15.09.26`。
- Composite predicate 仍窄：mask／two-pass／transform／bilinear／repeat／componentAlpha = software。
- Queue／P0 sideband／direct metadata ABI 凍結。不得為 R6/R7 重開。

### 3.2 Gate A 所有權模型（已在裝置上的 95e6f96）

Direct 路徑：LEASE_RESERVED（**serial=0**，src/dst 綁 pair）→ PUBLISH（才有 serial N）→ GPU → COMPLETED（renderer，`completedSerial` 是 batch watermark `T>=S`）→ SUCCESS。  
Busy 時 `gateAQueueSemanticallyQuiescent()` 為假則 `DIRECT_ADMIT_REJECT reason=1`。  
Present 遺留 GPU copy 是 `LORIE_GPU_OP_COPY`（`gateASeen=0`），**不是** direct 路徑。

### 3.3 Present GPU-copy 生命週期（writer 未提交）

問題：`queue_vblank` 失敗、scrap、destroy 曾在 GPU 完成前 `lorieGpuCopyAck`（pending--／放 extra ref／pixmap idle）。

凍結契約：

```text
唯一 helper: present_gpu_copy_retire_or_fatal(vblank)   在 present_vblank.c
dst_buffer == NULL 是合法 root destination
完成前不得 ACK／pending--／idle／scrap／destroy
timeout／renderer loss → lorieGpuCopyWaitForPresentOrFatal → fail-stop，不釋放
xserver/present 只准一個可執行 raw ACK（helper 內）
schedule 成功後立刻 gpu_copy_pending=TRUE
event 32 PRESENT_EARLY_ACK 凍結、禁止 runtime
event 33/34 只用於自然 requeue failure（先存 serial/dst，再 33→helper→34）
```

already-pending：

- 未完成 + renderer 健康 + requeue 成功 → 保持 pending、return queued
- 未完成 + 自然 requeue 失敗 → event 33 → helper → event 34
- 未完成 + renderer stall → helper（wrapper 不返回則不釋放）
- 已完成 → helper、不發 33/34

### 3.4 D2-INFLIGHT oracle（host 已改，歷史 cell 不可改寫）

舊 oracle：Present 還在 queue 時，下一個 overlapping Composite **必須** reason-1 reject。  
裝置事實：Adreno 830 上 GPU copy 常在 X 單執行緒走到 `gateADirectTryPrepare()` 前就完成，五格 `runtime-95e6f96/r6-d2-inflight*` 都是 **cover 先於 first lease**，沒有 reject。

新雙分支（judge 已落地，lease 認 production `serial=0`）：

```text
BUSY-REJECT:
  immediate Composite REQUEST/CALLBACK
  < reason=1 REJECT
  < completion cover T>=S
  < later Composite pair
  < LEASE(serial=0) / PUBLISH / COMPLETED / SUCCESS

QUIESCENT-ADMIT:
  immediate Composite pair
  cover.seq < first target LEASE(serial=0)
  完整 immediate lifecycle 必須在 later Composite REQUEST 之前結束
  然後才是 later pair + 第二筆 lifecycle
```

Cover 是 watermark：只綁 renderer、同 generation、`T>=S`，**不要**用 cover event 的 src/dst 去當 Present S 的 pair。  
Composite callback 本身不是 admission 證據。  
五格歷史 cell 保持 FAIL 檔案不動；host 測試證明新 judge 會把它們走 quiescent。

### 3.5 R6 OOM 與 R7 不得混用

- R6 Present OOM：`TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1`（一次性、只打 post-schedule requeue）。
- R7：`TERMUX_X11_GATEA_TEST_FAULT` **源碼裡不存在**。測 direct READY/FBO/fence/renderer-loss。
- 兩套都碰「注入故障後還能不能 ACK」。不可同時寫同一 worktree、不可同一 APK／同一 X 混 env。

## 4. 哪裡會有問題（請人規劃時優先看這些）

### P0 — 關帳未完成（規劃第一刀）

1. **`xserver.patch` 表示噪音**：基準 Present hunk 在檔案前段，retirement 被 **追加** 在檔尾（`+++ ./present/present_execute.c` 出現兩次：約 462 與 1232）。功能 round-trip 曾綠過，但 review／CI 會看起來像整檔重寫。規劃：在 commit 前把三個 Present 檔的語義 diff 併回既有 patch 方言，不要再整檔 regenerate。
2. **權威文件漂移**：`HANDOFF.md` 仍寫 D2「native 100% sound」與下一步 A/B/C。`GATE-A-P2-R6-DESIGN-20260915.md` §14 與 `GATE-A-P2-R6-D2-HOLD-20260915.md` 仍寫 wait C 未寫。writer 磁碟已經有 helper。規劃：獨立複核後才改 HANDOFF／TEST-MATRIX／AGENTS。
3. **未提交、雙寫痕跡**：Luna 寫 helper，Hermes 複核 HOLD 後又改 judge／execute／md，429 中斷。同一條 session 不宜當最終架構驗收。

### P1 — 還沒被 runtime 證明

4. **D2-OOM 未跑**。C 契約是 keep-pending + wait-or-fatal + 33/34；舊 early-ACK PASS 已撤回。新 APK 才有意義。
5. **timeout／renderer-loss fail-stop** 只有 source 路徑，沒有裝置格。
6. **scrap／destroy／CloseScreen teardown** 靜態順序有，runtime 無。
7. **新 APK 上的 D1 與 D2-INFLIGHT** 還沒用 retirement artifact 重跑。歷史 `9369553` D1 PASS 與 `95e6f96` 五格 D2 都 **不可 silent-retry、不可覆寫**。

### P2 — oracle／telemetry 架構縫

8. **LEASE_RESERVED 沒有 client sequence**。quiescent 的「immediate」只能用「lease 前不准插入下一筆 Composite REQUEST」保守綁定。若要更嚴，要改 telemetry payload（架構授權）。
9. **Judge 現在要求 quiescent 也有 later Composite + 第二 lifecycle**。比最初 dual-branch 更嚴。規劃時確認這是要保留的產品 oracle，還是 host 過度擬合 fixture。
10. **event 32 仍存在**（enum／prototype／`InitOutput.c` 定義）。禁止呼叫；不要刪、不要改號。

### P3 — 產品大邊界（不是這條 writer 能修）

11. **Production Gate A BLOCKED**：缺可驗證的 CPU ownership release、import-ready ACK、per-serial success／failure、acquire／release publication、generation drain／unregister、imported AHB producer-fence。A1 9/9 exact 不是 production enable。
12. **R7 仍缺 `TERMUX_X11_GATEA_TEST_FAULT`**。必須等 R6 關帳並凍結產物後，**另開 worktree**。與 R6 並行會撞 InitOutput／renderer／Present ownership。
13. **ART JIT 偶發 SIGSEGV**（PC `0x4800xxxx`、dalvik-jit、`si_addr=0`）：不是 libXlorie C bug。禁止為它改 pump／waiter／DDX。授權單次有界重跑；PASS 則 NON-REPRODUCED。

### P4 — 操作紅線

- 不准碰 Stable／HDMI／PR／merge／origin／force。
- 不准 `±1 UNORM` 當 PASS。
- 不准在 `d9b7f60` 再重試 R5。
- 不准重跑 `88e3f17`／`8479997`／`6c7ee6f`／`98b0011` 的 R3。
- 不准 silent-retry PROTO=0、R6-D1、`95e6f96` 既有 D2 格。
- 測試檔本輪凍結：不要改 `test-*.py`／`test-*.sh` 去遷就 source。

## 5. 建議規劃選項（未授權，只供選）

| 選項 | 內容 | 前置 | 風險 |
|---|---|---|---|
| A | 獨立複核 writer + 正規化 patch + 本機 commit | host 已綠 | 複核者不能是寫過 helper 的同一條線 |
| B | fork push／CI／只裝 experimental | A 通過 | 新 APK 才能跑 OOM／D2 |
| C | 新 APK：D1 → D2-INFLIGHT（雙分支）→ D2-OOM | B | 歷史格只當對照，不覆寫 |
| D | 停在未提交，不開裝置 | — | 文件與 HANDOFF 會繼續漂移 |
| 禁止 | R6 與 R7 同時寫 C／同 APK 混 fault env | — | 所有權與 ACK 契約衝突 |

## 6. 核心源碼（規劃包內副本）

Writer：

- `lorie/src/main/cpp/xserver/present/present_execute.c`
- `lorie/src/main/cpp/xserver/present/present_vblank.c`（helper）
- `lorie/src/main/cpp/xserver/present/present_priv.h`
- `lorie/src/main/cpp/patches/xserver.patch`

Host oracle（不在 git worktree 裡，在專案根）：

- `evidence/session/gate-a-a1/p2-r3-xpump-runtime/judge-r6-design.py`

Helper 本體：`present_vblank.c` `present_gpu_copy_retire_or_fatal`。  
唯一 raw ACK：同檔 `lorieGpuCopyAck(vblank->pixmap, vblank->gpu_copy_dst_buffer)`。

## 7. 這份規劃包刻意不含什麼

專案根約 17G。`evidence/` 約 7.8G（runtime logcat／APK／ELF），`src/` 約 1.9G（多棵完整 xserver）。  
手機副本 **只含 md + 核心 C／judge／技能**，不含：

- 各 worktree 完整樹、`.git`、submodule 物件
- `.gradle`／`build`／`.cxx`
- APK、ELF、logcat-follow、ring dump
- 本機 commit／CI／ADB 授權

完整磁碟仍在 workstation：`/root/projects/GPU加速`。
