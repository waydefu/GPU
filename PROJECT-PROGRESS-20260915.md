# GPU 加速專案進度

> 快照時間：2026-09-15 22:00（UTC+8）  
> 規劃入口：`PLANNER-BRIEF-20260915.md`  
> Runtime 梯子權威仍是 `HANDOFF.md`（尚未寫入未提交 retirement 樹）。

## 一頁摘要

- 裝置 experimental 是 `95e6f96`（`com.waydefu.x11gpu`／`:3`）。Stable `:1` 未碰。
- Gate A P2：R1–R5 PASS（R1 PROTO=0 首次 SIGSEGV 為 dalvik-jit，有界重跑 PASS／NON-REPRODUCED）。
- 歷史 **R6-D1 PASS** 在凍結 `9369553`。新 APK 上 D2-INFLIGHT 五格保留：舊 reject-only oracle FAIL；COMPLETED serial S PROVEN；物理上 GPU 常快於 X dispatch。
- D2-OOM **未跑**。KEEP CI FAIL **34943831800**。
- Present GPU-copy retirement helper **已在** `src/f8-ahb-gatea-r6-retire`，未提交；host 測試綠；關帳（patch 正規化、獨立複核、HANDOFF）未完成。
- R7 未開始（缺 `TERMUX_X11_GATEA_TEST_FAULT`）。不可與 R6 並行寫 C。
- Production Gate A 仍 BLOCKED。

## 目前版本與執行環境

| 項目 | 狀態 |
|---|---|
| 裝置 APK | `com.waydefu.x11gpu` `1.03.01-95e6f96-15.09.26` CI **34944171114** |
| APK SHA256 | `60c36b4f59c38d13db6fe6c366e6f115a720ec1d6946d057b3ec41551b12f628` |
| Native Build ID | `1188e1cabf3b78285e7e5fbedcf64f0b5e7d44f9` |
| 已安裝源 | `src/f8-ahb-gatea-r6` `qualification/gatea-r6-20260915` HEAD `95e6f9602b0146ee190870f84a34aad822ef666f` **乾淨** |
| Writer（未提交） | `src/f8-ahb-gatea-r6-retire` `fix/gatea-r6-present-retirement-20260915` 同 base；髒 `xserver.patch` |
| R5 回滾點 | `src/f8-ahb-gatea-r5-fix` `37d8393` 乾淨 |
| Frozen control | `src/f8-ahb-gatea-a1` `88e3f17` 乾淨 |
| R3 X-pump | `src/f8-ahb-gatea-xpump` `d9b7f60` 乾淨 |
| Stable | `com.termux.x11` `1.03.01-11b82d9-06.09.26` `:1` 未碰 |

## Gate 狀態

### 已關閉

P0、P1、P2-A、P2-B.1 CLOSED。P2-B.2 narrow Over PASS；predicate 維持狹窄。

### Gate A P2 runtime

| Round | 結果 |
|---|---|
| R1 unset | PASS |
| R1 PROTO=0 | 首次 SIGSEGV PID 21639（dalvik-jit）OBSERVED；有界重跑 PASS；NON-REPRODUCED |
| R2 | PASS |
| R3 | PASS on `d9b7f60`（歷史 `88e3f17` waiter deadlock 已 falsified） |
| R4 | PASS 1514/1514 exact |
| R5 | PASS on `37d8393`（hang falsified，4096 exact） |
| R6 bounded client | PASS on `37d8393`（CLIENT_OK；非 design-complete） |
| R6-D1 | 歷史 PASS `9369553` retry5；新 APK 未重跑 |
| R6-D2-INFLIGHT | `95e6f96` 五格 FAIL（舊 reject-only）；host 新 judge 可走 quiescent；**未**用 retirement APK 重跑 |
| R6-D2-OOM | NOT RUN |
| R7/R8 | NOT STARTED |

## 重要根因

- **R3**：lorie 未呼叫 `InputThreadPreInit()`，REGISTER waiter 與 conn_fd 讀取同一 X main thread → self-wait。`d9b7f60` record-aware pump 修正。
- **R5**：AF_UNIX tiny-record backpressure + lock-across-write。`37d8393` 修正。
- **R6-D2 COMPLETED 缺事件**：legacy GPU copy 曾不發 event 14。`54ff35b`／`95e6f96` 已補；裝置上 PROVEN。
- **R6-D2 無 reject**：GPU < X dispatch，queue 已 quiescent 時 admit 是合法的。舊 oracle 假紅。雙分支 judge 已寫在 host，尚未裝入新 APK。
- **Present 提前 ACK**：requeue fail／scrap／destroy 可在 completion 前 `lorieGpuCopyAck`。Writer 集中到 `present_gpu_copy_retire_or_fatal()`。未 commit。

## Production 為何仍 BLOCKED

A1 microprobe 9/9 exact 只證明 BGRA sampling capability。仍缺完整可驗證的 CPU ownership release、import-ready ACK、per-serial 成敗、acquire／release publication、generation drain、imported AHB producer-fence。這是 qualification prototype，不是 production enable。

## 不可越過

- Stable `:1`、HDMI、PR、merge、origin、force、production enable。
- 不重開 P0/P1/P2-A/P2-B.1/P2-B.2。不准 `±1 UNORM` PASS。
- 不在 `d9b7f60` 再重試 R5。不重跑 `88e3f17`／`8479997`／`6c7ee6f`／`98b0011` 的 R3。
- 不 silent-retry PROTO=0、R6-D1、既有 `95e6f96` D2 格。
- R6 與 R7 不可同時寫 C。R7 另開 worktree、另授權。

## 目前下一步（未授權）

見 `PLANNER-BRIEF-20260915.md` §5：獨立複核並正規化 patch → 才考慮 commit／CI／新 APK cells。STOP BEFORE R7。

## 主要證據

- `PLANNER-BRIEF-20260915.md`（規劃入口）
- `HANDOFF.md`、`TEST-MATRIX.md`
- `evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md`
- `evidence/session/gate-a-a1/p2-r6-design/` 下 DESIGN／HOLD／physical-race／retirement plan
- `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-PRESENT-RETIREMENT-IMPLEMENTATION-20260915.md`
- `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-D2-INFLIGHT-ORACLE-ADJUDICATION-20260915.md`
