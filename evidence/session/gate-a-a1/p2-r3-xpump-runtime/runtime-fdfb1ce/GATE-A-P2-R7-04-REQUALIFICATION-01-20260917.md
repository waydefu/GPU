# fdfb1ce R7-04 裝置複測格 01 — 2026-09-17 `R7_04_REQUALIFICATION_PASS`

授權：恰好一次全新 R7-04 / `fbo-incomplete`，候選 `fdfb1ce`。
不是完整 R7、不是 R7-05+、不是 B-2、不是歷史 `r7-qualification-01` 重跑。
未改 source、未重建、未改 2000 ms / judge / 契約。觸發恰好一次，無 retry。

## 主判決

`R7_04_REQUALIFICATION_PASS`

R7-04 transitions from historical FAIL on 7549e36 to PASS on fdfb1ce; R7 overall remains in progress.

---

## 狀態

| 項目 | 值 |
|---|---|
| R6 | PASS / frozen `0f1e546` |
| RCA-1 | FIXED / DEVICE-PROVEN `0d72332` |
| CASE_LOOP | DEVICE-VALIDATED `7549e36`（`327b028` SUPERSEDED） |
| B-2 | PASS `runtime-7549e36/b2-requalification-02/`（本格未重跑、未降級） |
| 歷史 R7-04 on `7549e36` | 有效 FAIL `halt_mismatch` / **凍結未覆寫** |
| 新候選 `fdfb1ce` R7-04 | **PASS**（本格） |
| R7 overall | **IN PROGRESS / NOT YET PASS** |
| Production Gate A | BLOCKED |
| R8/R9/R10 | NOT STARTED |

凍結 judge 對歷史 `runtime-7549e36/r7-qualification-01/r7-04/logcat-follow.txt` 仍判
`R7_FAIL halt_mismatch what=x-direct-not-success reason=4`。

---

## Artifact provenance / installed binding

| 欄位 | 值 |
|---|---|
| SHA | `fdfb1ce44b429897eda17c43bf33fbd37afe67f3` |
| parent | `7549e36` |
| CI | **35103216566** success |
| package | `com.waydefu.x11gpu` |
| versionName / versionCode | `1.03.01-fdfb1ce-16.09.26` / **15** |
| APK SHA256 | `5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c` local=staged=installed MATCH |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` CONTINUITY PASS |
| Build ID | `1d6bf3cd0eb06d12804e690679211ee7f34f998e` embedded == pulled installed MATCH |
| lastUpdateTime | 2026-09-17 00:54:07 |
| ABI | arm64-v8a armeabi-v7a x86 x86_64 |
| 安裝格 | `runtime-fdfb1ce/r0/` `INSTALL_FDFB1CE_BIND_PASS` |

---

## Stable before

| 欄位 | 值 |
|---|---|
| PID | **24999**（現場讀取；非歷史 16485） |
| package | `com.termux.x11` `1.03.01-11b82d9-06.09.26` versionCode 15 |
| lastUpdateTime | 2026-09-07 22:55:03 |
| cmdline | `termux-x11 com.termux.x11 :1 -legacy-drawing` |

未 kill / 未 force-stop / 未安裝覆蓋 Stable。

---

## Installation

| 欄位 | 值 |
|---|---|
| 先前 experimental | `1.03.01-7549e36-16.09.26` lastUpdateTime 2026-09-16 19:03:48 |
| ADB | live-fetch `_adb-tls-connect._tcp.local.` `adb-51c6f1fe-ZtRPH4` → `10.191.48.13:41361`；identity `myron` / `25102PCBEG`；Awake；keyguard false |
| 預先 X3 | 無；`am force-stop com.waydefu.x11gpu` 僅 experimental |
| pm session | 1122673318 create/write/commit Success |
| 新 installed | `1.03.01-fdfb1ce-16.09.26` lastUpdateTime 2026-09-17 00:54:07 |
| HDMI | observe-only `mDisplayId=0` |

---

## Runtime

| 欄位 | 值 |
|---|---|
| X PID | **9891** |
| DISPLAY | `:3` |
| cmdline | `termux-x11gpu com.waydefu.x11gpu :3` |
| Activity PID | **23139** `com.waydefu.x11gpu` Display #0 `display=0` |
| renderer TID | Activity GLES **8877**（event 35 / renderer halt）；X TID **11104**（`x-observe-fatal` dump） |
| 新鮮 X | ALIVE_8S；非舊 X 重用 |

---

## Environment

`/proc/9891/environ` GATEA 恰好 4 個：

```
TERMUX_X11_GATEA_PROTO=1
TERMUX_X11_GATEA_TELEMETRY=1
TERMUX_X11_GATEA_TEST_FAULT=fbo-incomplete
TERMUX_X11_GATEA_TEST_ARM=1
```

無 R6 OOM、無 Present requeue、無其他 R7 selector、無 `TERMUX_X11_GATEA_A1`。

**EXACT_R7_04_ENV**

---

## Trigger

| 欄位 | 值 |
|---|---|
| harness | `p2-r1-diag-runtime/fixtures/p_r3_single_direct` |
| SHA256 | `b424a6340aac9140114ef70b4eb80cdbaa17cf8762b730963b865cd947cd8c13` |
| 命令 | `p_r3_single_direct` DISPLAY=:3 |
| executions | **1** |
| client | `FAIL GetImage`（R7 注入 GPU fatal 後預期；非資格失敗） |
| holder | `p_b3a_hold` HOLD READY |

---

## Fault sequence（follow 序列權威）

PUBLISH seq=42 serial=9 → CONSUME seq=43 → LOOKUP_OK seq=44 →
event 35 seq=45 role=2 src=4 dst=2 serial=**9** → event 16 seq=46 →
renderer `GATEA_FATAL_HALT what=r-gatea-DIRECT_LOOKUP_FAIL reason=2`

受影響 serial **9** generation=1 src=8 dst=9。

---

## Fatal propagation audit

follow 時間序（權威）：

1. `GATEA_FATAL_HALT what=r-gatea-DIRECT_LOOKUP_FAIL reason=2`（PID 23139 TID 8877）

其後 **沒有** 第二筆 `GATEA_FATAL_HALT`。

診斷（非 halt）：X PID 9891 `GATEA_SUMMARY where=x-observe-fatal`；
`generationFatal=2 fatalReason=2`。preserve dump，不是衝突分類。

| 計數 | 值 |
|---|---|
| `x-direct-not-success reason=4` | **0** |
| `x-direct-not-success` 任何 reason | **0** |
| 最後權威 halt | `r-gatea-DIRECT_LOOKUP_FAIL reason=2` |

歷史缺陷（reason=2 被 reason=4 覆蓋）**未再出現**。

---

## Frozen judge

```
python3 p2-r7-design/judge-r7.py fbo-incomplete logcat-follow.txt \
  --ring gatea-ring.txt --summary gatea-summary.txt --x-alive 0 --exit-signal 0
```

判決：`R7_PASS fbo-incomplete`

judge SHA256 `fba3c10f…cc17` 未改。`test-judge-r7.py` 16/16 PASS。

---

## Forbidden-success audit（serial 9，event 35 之後）

| 項目 | 值 |
|---|---|
| success completion / event 17 | 0 |
| Gcomp Done | 0 |
| ACK event 21 | 0 |
| pending-- event 22 | 0 |
| RELOCK / REPAIR / LEASE_RELEASE | 0 |
| later PUBLISH serial>9 | 0 |
| event 32 | 0 |
| 35 之後僅 event 16（GENERATION_FATAL） | 1 |
| fault→Done | **0** |
| timeout→Done | **0** |

`forbidden-audit.txt` 的 `event35_count=2` 是 follow+unfiltered dump **重複擷取**；
follow unique event 35 = **1**。

---

## One-shot

- arm：觸發前 `TEST_ARM=1` 在 X environ
- event 35：**恰好 1 次**（follow）
- 未再射、未 rearm
- 觸發 executions=1

---

## Timeout

| 項目 | 值 |
|---|---|
| EXA completion timeout / `x-exa-composite-wait` | 0 |
| timeout serials | none |
| TIMEOUT reason-4 halt | **0** |
| 2000 ms 契約 | 未改 |

---

## Cleanup / Stable after

X 9891 在 trigger 後 1 s 內 `_exit`（預期 fail-stop）。teardown `am force-stop com.waydefu.x11gpu`。

**NO_X3_RESIDUE**

| Stable after | 值 |
|---|---|
| PID | **24999** 不變 |
| version | `1.03.01-11b82d9-06.09.26` |
| lastUpdateTime | 2026-09-07 22:55:03 不變 |
| cmdline | `termux-x11 com.termux.x11 :1 -legacy-drawing` |
| HDMI | observe-only `mDisplayId=0`；未改設定 |
| experimental APK | **仍安裝** `1.03.01-fdfb1ce-16.09.26`（依契約不卸載） |

---

## 狀態含義

R7-04 在 `fdfb1ce` 上 **PASS**。R7 **尚未**整體 PASS。下一 mandatory 格是 R7-05 `post-draw-gl`，需**另開授權**。本格 **STOP**。
