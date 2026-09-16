# 7549e36 R7 資格格 01 — 2026-09-16 `R7_QUALIFICATION_BLOCKED`

授權：本輪為 `7549e36` 的**第一次** R7 fail-stop 資格判定。
不是 B-2、不是 CASE_LOOP repair-validation、不是 R8+。
未改 source、未重建 APK、未改 2000 ms / 8 ms、未重跑失敗格。

停止規則：計畫書 §4.5 fail-fast。第一個 mandatory 格 FAIL 後清理即停，其餘格 **NOT RUN**。

## 主判決

`R7_QUALIFICATION_BLOCKED`

R7 is BLOCKED; B-2 remains PASS.

---

## 狀態（進入本輪時）

| 項目 | 值 |
|---|---|
| R6 | PASS / frozen `0f1e546` |
| RCA-1 | FIXED / DEVICE-PROVEN `0d72332` |
| CASE_LOOP historical | DEVICE-PROVEN `feeaa56` stall-obs-01 |
| CASE_LOOP repair | DEVICE-VALIDATED `7549e36` |
| B-2 | PASS `runtime-7549e36/b2-requalification-02/` |
| R7 starting | NOT STARTED → 本輪開始 |
| Production Gate A | BLOCKED |

## R7 authority

讀過：

- `p2-r7-design/GATE-A-P2-R7-R10-SUPPORT-DESIGN-20260916.md`（凍結合約）
- `p2-r7-design/GATE-A-R6檢查與R7-R10-GateH計畫書-20260915.md` §4
- `p2-r7-design/judge-r7.py` / `test-judge-r7.py` / `verify_r7_support.py`
- case-loop source：`lorie.h` consume helper、`InitOutput.c` publish-from-env、`renderer.cpp` consume sites、`cmdentrypoint.cpp` R7-09、`xserver.patch` event 36 helper

Fault selectors（allow-list，本授權只跑前 13 個）：

`fbo-incomplete` `post-draw-gl` `src-ready-miss` `dst-ready-miss` `tuple-mismatch` `fence-create-fail` `fence-timeout` `renderer-fatal-pre-fence` `wrong-generation-frame` `serial-wrap` `renderer-exit-after-consume` `present-hold-complete` `present-renderer-exit`

**不跑**：`destroy-while-gpu-owned` `close-while-lease` `stale-ready-replay`（R8/R9）

source 與凍結合約：**同意**。計畫書表曾寫 R7-04 = FAILED_QUIESCED，凍結設計已明示「不重分類」，oracle 以 source `r-gatea-DIRECT_LOOKUP_FAIL` reason=2 為準。`test-judge-r7.py` 16/16 PASS。`verify_r7_support.py` 無法在 case-loop 直接跑（xserver submodule 未展開）；lorie hook + `xserver.patch` helper 順序 `event36 → wait → ACK` 已對上。

## Candidate provenance

| 欄位 | 值 |
|---|---|
| SHA | `7549e3667ec03b8b5e50d2e5befe03065840bbd9` |
| CI | **35084701124** |
| package | `com.waydefu.x11gpu` |
| version | `1.03.01-7549e36-16.09.26` / versionCode **15** |
| APK SHA256 | `45500894023208963b3b1cd51fb7f3aa61807a25e1d70b322f7a7fdad7e14bc3` MATCH |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` MATCH |
| Build ID | `4c5b7b86c18ec4e9bb14720c4615a25c1d6a8f81` MATCH |
| lastUpdateTime | 2026-09-16 19:03:48 未變 |
| installed lib R7 literals | TEST_FAULT / TEST_ARM / x-test-fault-env / r-test-fatal-pre-fence / x-serial-wrap / x-present-copy-wait / GATEA_FATAL_HALT 皆在 |

## Stable before

| 欄位 | 值 |
|---|---|
| PID | **16485** |
| package | `com.termux.x11` `1.03.01-11b82d9-06.09.26` versionCode 15 |
| lastUpdateTime | 2026-09-07 22:55:03 |
| cmdline | `termux-x11 com.termux.x11 :1 -legacy-drawing` |

## R7 matrix

執行順序（合約）：04 → 05 → 01 → 02 → 03 → 06 → 07 → 08 → 09 → 11 → 10 → P1 → P2。

| Cell | Fault selector | Arm | Trigger | Expected fail-stop | Executions | Verdict |
|---|---|---|---|---|---|---|
| R7-04 | `fbo-incomplete` | 1 | `p_r3_single_direct` ×1 | LOOKUP_OK → 35 → renderer FATAL `r-gatea-DIRECT_LOOKUP_FAIL` reason=2 | 1 | **FAIL** |
| R7-05 | `post-draw-gl` | 1 | `p_r3_single_direct` | X `x-direct-not-success` reason=2 | 0 | NOT RUN |
| R7-01 | `src-ready-miss` | 1 | `p_r3_single_direct` | `r-gatea-DIRECT_LOOKUP_FAIL` reason=2 | 0 | NOT RUN |
| R7-02 | `dst-ready-miss` | 1 | `p_r3_single_direct` | same | 0 | NOT RUN |
| R7-03 | `tuple-mismatch` | 1 | `p_r3_single_direct` | `r-gatea-direct-identity` reason=5 | 0 | NOT RUN |
| R7-06 | `fence-create-fail` | 1 | `p_r3_single_direct` | `r-gatea-fence-create` reason=3 | 0 | NOT RUN |
| R7-07 | `fence-timeout` | 1 | `p_r3_single_direct` | `r-gatea-fence-wait` reason=3；無 completed ≥ S | 0 | NOT RUN |
| R7-08 | `renderer-fatal-pre-fence` | 1 | `p_r3_single_direct` | `r-test-fatal-pre-fence` reason=6 | 0 | NOT RUN |
| R7-09 | `wrong-generation-frame` | 1 | first Gate A frame | `x-wrong-generation` reason=6 | 0 | NOT RUN |
| R7-11 | `serial-wrap` | 1 | first publish ++ | `x-serial-wrap` reason=6；無 PUBLISH serial=0 | 0 | NOT RUN |
| R7-10 | `renderer-exit-after-consume` | 1 | `p_r3_single_direct` | renderer `_exit(127)`；X `x-hup` reason=6 | 0 | NOT RUN |
| R7-P1 | `present-hold-complete` | 1 | `p_r6_d2_present inflight` | `x-present-copy-wait` reason=4；event 34=0 | 0 | NOT RUN |
| R7-P2 | `present-renderer-exit` | 1 | `p_r6_d2_present inflight` | X `x-hup`；event 34=0 | 0 | NOT RUN |
| R7-12/13/14 | allow-list only | — | — | R8/R9 | 0 | NOT AUTHORIZED |

## Cell details — R7-04

| 欄位 | 值 |
|---|---|
| fresh X PID | **31122** |
| Activity / renderer PID | **16922** TID 30832 |
| `/proc/31122/environ` GATEA | 恰好 4 個：`PROTO=1` `TELEMETRY=1` `TEST_FAULT=fbo-incomplete` `TEST_ARM=1`。無 R6 OOM / A1 |
| arm | 1，觸發前 armed；event 35 一次後未再射 |
| trigger | `p_r3_single_direct` SHA256 `b424a6340aac9140114ef70b4eb80cdbaa17cf8762b730963b865cd947cd8c13` 恰好一次 |
| fault marker | `GATEA_EVENT seq=31 role=2 event=35 generation=1 serial=5 src=4 dst=2` |
| affected serial | **5** generation=1 src=6 dst=7 |
| construction | PUBLISH seq=28 → CONSUME seq=29 → LOOKUP_OK seq=30 → 35 seq=31 |
| renderer halt | `GATEA_FATAL_HALT what=r-gatea-DIRECT_LOOKUP_FAIL reason=2`（凍結預期） |
| X halt（last） | `GATEA_FATAL_HALT what=x-direct-not-success reason=4`（`FAIL_TIMEOUT`） |
| process | X 在 trigger 後 1 s 內 `_exit`；無 Fatal signal |
| judge | `R7_FAIL halt_mismatch what=x-direct-not-success reason=4` |
| local verdict | **FAIL** |

`gateADoneDirect` 在 `gateAWaitTerminal` 得到 `RESULT_FATAL` 時，把 reason 合成 `LORIE_GATEA_FAIL_TIMEOUT`，再 `gateAXFatal("x-direct-not-success", 4)`。凍結 `judge-r7.py` 取**最後一筆** `GATEA_FATAL_HALT`，因此對不上 renderer 的凍結字串。

這是有效資格格（env、one-shot 35、構造鏈、X 死亡皆成立），不是 INVALID。

## Forbidden-success audit（serial 5）

| 事件 | 35 之後 |
|---|---|
| SEMANTIC_SUCCESS (17) | 0 |
| Gcomp Done | 0 |
| ACK (21) | 0 |
| Present retirement / event 34 | N/A（非 Present 格） |
| PENDING_DEC (22) | 0 |
| RELOCK / REPAIR / LEASE_RELEASE | 0 |
| later PUBLISH serial>5 | 0 |
| event 32 | 0 |
| fixture PASS / CLIENT_OK | 無（GetImage FAIL，預期） |

## One-shot semantics

- arm 觸發前：`TEST_ARM=1` 在 X environ
- fired：event 35 **恰好 1 次**（follow 權威；audit 檔的 2 是 follow+dump 重複擷取，不是二次射擊）
- 未在同格再射
- 下一 clean runtime：未開（fail-fast）。本格 teardown 後 `NO_X3_RESIDUE`，無殘留 X 帶著舊 env

## Timeout / fault→Done audit

| 計數 | 值 |
|---|---|
| injected failure（event 35） | 1 |
| EXA completion timeout | 0 |
| fault→Done | **0** |
| timeout→Done | **0** |

RCA-1 不變式在本格維持：失敗後沒有成功 Done。

## Clean control

`NOT REQUIRED BY R7 CONTRACT`（計畫書 R7 無 post-fault clean 格；B-2 已 PASS 且本授權禁止重跑 B-2）。因 04 FAIL，亦未另開。

## Cleanup

R7-04：killed/expired X 31122；`am force-stop com.waydefu.x11gpu`；**NO_X3_RESIDUE**。
Final：**NO_X3_RESIDUE**。APK 未卸載。

## Stable after

| 欄位 | 值 |
|---|---|
| PID | **16485** UNCHANGED |
| version | `1.03.01-11b82d9-06.09.26` |
| lastUpdateTime | 2026-09-07 22:55:03 UNCHANGED |
| cmdline | `termux-x11 com.termux.x11 :1 -legacy-drawing` UNCHANGED |
| HDMI | observe-only `mDisplayId=0`；未改設定 |

## 停止政策

遵循計畫書 §4.5：mandatory FAIL 後停止，不跑 05 起各格，不重試 04。

## 專案狀態（本輪後）

- R6 = PASS / frozen
- B-2 = PASS
- R7 = **BLOCKED**
- Production Gate A = BLOCKED
- R8 / R9 / R10 = NOT STARTED

Evidence：`runtime-7549e36/r7-qualification-01/`（`preflight/` + `r7-04/`）。
Harness：`p2-r3-xpump-runtime/run-r7-one-cell.sh`。
ADB：`192.168.1.101:46061` live-fetched `_adb-tls-connect._tcp.local.` `adb-51c6f1fe-ZtRPH4`。
