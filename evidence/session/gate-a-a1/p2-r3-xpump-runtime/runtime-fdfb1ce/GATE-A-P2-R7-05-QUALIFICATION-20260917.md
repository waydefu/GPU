# fdfb1ce R7-05 裝置資格格 — 2026-09-17 `R7_05_QUALIFICATION_FAIL`

授權：waydefu/GPU PR #7 packet **NEXT-001**，恰好一次 `post-draw-gl`，候選 `fdfb1ce`。
不是 R7-04 重跑、不是 B-2、不是歷史 `r7-qualification-01`、不是 R7-01+。
未改 source、未改 2000 ms / judge / selector / 契約。觸發恰好一次，無 retry。

## 主判決

`R7_05_QUALIFICATION_FAIL`

VALID FAIL：artifact / env / 新鮮 X3 / 單次 fixture / event35 一次 / PUBLISH→DRAW→35 構造成立，但凍結 judge 看**最後一筆** `GATEA_FATAL_HALT`，觀測為 `r-hup reason=6`，不是契約要求的 `x-direct-not-success reason=2`。

R7 BLOCKED at R7-05. 歷史 R7-04 PASS 與 B-2 PASS 保持凍結。不准 retry。本任務不執行 NEXT-037。

---

## 狀態

| 項目 | 值 |
|---|---|
| R6 | PASS / frozen `0f1e546` |
| RCA-1 | FIXED / DEVICE-PROVEN `0d72332` |
| CASE_LOOP | DEVICE-VALIDATED `7549e36` |
| B-2 | PASS `runtime-7549e36/b2-requalification-02/`（本格未重跑） |
| 歷史 R7-04 on `7549e36` | 有效 FAIL `halt_mismatch` / **凍結未覆寫** |
| `fdfb1ce` R7-04 | PASS 凍結 `r7-04-requalification-01/` |
| `fdfb1ce` R7-05 | **FAIL**（本格） |
| R7 overall | **BLOCKED at R7-05** / NOT PASS |
| Production Gate A | BLOCKED |
| R8/R9/R10 | NOT STARTED |

---

## Artifact / device

| 欄位 | 值 |
|---|---|
| SHA | `fdfb1ce44b429897eda17c43bf33fbd37afe67f3` |
| CI | **35103216566** |
| package | `com.waydefu.x11gpu` `1.03.01-fdfb1ce-16.09.26` versionCode 15 |
| APK SHA256 | `5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c` live pull MATCH |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` CONTINUITY PASS |
| Build ID | `1d6bf3cd0eb06d12804e690679211ee7f34f998e` MATCH |
| lastUpdateTime | 2026-09-17 00:54:07（未重裝） |
| ADB | live `_adb-tls-connect._tcp.local.` `adb-51c6f1fe-ZtRPH4` → `10.191.48.13:35373`；isolated 5038；`myron` / `25102PCBEG`；Awake；keyguard false |
| 預先 X3 | ABSENT；socket/lock ABSENT |
| 證據目錄 | `runtime-fdfb1ce/r7-05/` 啟動前不存在 |
| 外層 preflight | `runtime-fdfb1ce/r7-05-outer-preflight/` |

未重裝。HDMI observe-only，未改設定。

---

## Runtime

| 欄位 | 值 |
|---|---|
| X PID | **22704** |
| DISPLAY | `:3` |
| cmdline | `termux-x11gpu com.waydefu.x11gpu :3` |
| Activity PID | **30140** `com.waydefu.x11gpu` Display #0 `display=0` |
| 新鮮 X | ALIVE_8S；觸發後 `X3_DIED_AFTER_TRIGGER elapsed=1` |
| env | `/proc/22704/environ` 恰好 4 個 GATEA：PROTO=1 TELEMETRY=1 TEST_FAULT=post-draw-gl TEST_ARM=1 |
| fixture | `p_r3_single_direct` ×**1**；GetImage FAIL（注入後預期）；holder `p_b3a_hold` HOLD READY |
| runner | `run-r7-one-cell-fdfb1ce.sh` shell exit **2** |

**EXACT_R7_05_ENV**

---

## Sequence（follow 序列權威，seq 0–36 無 gap）

PUBLISH seq=28 role=1 event=6 generation=1 serial=**5** src=6 dst=7 →
CONSUME seq=29 role=2 event=7 → LOOKUP_OK seq=30 role=2 event=8 →
DRAW seq=31 role=2 event=10 generation=1 serial=5 src=6 dst=7 →
event 35 seq=32 role=2 event=35 generation=1 serial=5 src=**5** dst=**2**（enum 5 / renderer）→
FENCE_SATISFIED seq=33 event=11 → FIRST_FAILED seq=34 event=15 → COMPLETED seq=35 event=14 →
GENERATION_FATAL seq=36 role=1 event=16。

SUMMARY `where=x-direct-not-success` `firstFailed=5`（**serial**）`generationFatal=2` `fatalReason=2`。
`firstFailed=5` 對上目標 serial，不是「缺少 DRAW」。reason=2 = `FAIL_DRAW`。reason=4 TIMEOUT = **0**。

event35 去重後 **恰好 1**。raw `forbidden-audit.txt` `event35_count=2` 是 follow+unfiltered 重複擷取。

---

## Fatal（follow 時間序）

1. `GATEA_FATAL_HALT what=x-direct-not-success reason=2` X PID 22704 TID 23191 — **此格契約期望身份**
2. `GATEA_FATAL_HALT what=r-hup reason=6` Activity PID 30140 — **最後一筆；凍結 judge 用這一筆**

`x-observe-fatal` = 0。`x-test-fault-env` = 0。

凍結 `judge-r7.py post-draw-gl` `--x-alive 0 --exit-signal 0`（pre-cleanup：X 已死、無 PID-bound crash）：
`R7_FAIL halt_mismatch what=r-hup reason=6`  exit **1**。

`test-judge-r7.py` 16/16 PASS。judge SHA256 `fba3c10f…cc17` 未改。

---

## Forbidden after event 35（seq-deduped, serial 5 / generation 1）

SUCCESS=0 RELOCK_SRC=0 RELOCK_DST=0 REPAIR=0 ACK=0 PENDING_DEC=0 LEASE_RELEASE=0
later PUBLISH=0 event32=0 event34=0 Gcomp Done=0 fallback=0

event 11/15/14 在 35 之後是本 selector 的 fence-satisfied / first-failed / completed，不在凍結 forbidden set。

---

## Crash / cleanup / Stable

SIGSEGV=0 SIGILL=0 SIGABRT=0；X 22704 與 Activity 30140 PID-bound crash lines=0。
未宣稱 wait-status exit127（double-fork；證據是 fatal marker + PID 消失）。

Cleanup 後：X process ABSENT；`/tmp` 與 Termux tmp 的 X3 socket ABSENT；X3 lock ABSENT；runner `NO_X3_RESIDUE`。

Stable before/after：PID **843**；cmdline `termux-x11 com.termux.x11 :1 -legacy-drawing`；`1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03 **unchanged**。未碰 Stable / HDMI 設定。

---

## 分類

不是 INVALID：artifact MATCH、env EXACT、目錄原先不存在、無既有 X3、fixture ×1、hook 有打到、pre-cleanup X 狀態已知。

是 VALID FAIL：最後 halt 身份不符凍結 oracle（期望 X `x-direct-not-success/2`，觀測 renderer `r-hup/6` 蓋過）。

不准 overlay 本目錄。不准 silent-retry。不准自動開 R7-01。下一步若另開授權才是 PR #7 **NEXT-037**。
