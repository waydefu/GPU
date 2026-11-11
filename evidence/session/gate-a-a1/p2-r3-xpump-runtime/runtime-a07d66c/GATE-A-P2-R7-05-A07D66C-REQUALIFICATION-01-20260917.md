# a07d66c R7-05 裝置複測格 01 — 2026-09-17 `R7_05_A07D66C_REQUALIFICATION_PASS`

授權：恰好一次全新 R7-05 / `post-draw-gl`，候選 `a07d66c`。
不是完整 R7、不是 R7-01+、不是 B-2、不是 R7-04、不是歷史 `runtime-fdfb1ce/r7-05` 重跑。
未改 source、未改 2000 ms / judge / selector / ABI。觸發恰好一次，無 retry。

## 主判決

`R7_05_A07D66C_REQUALIFICATION_PASS`

X 已發布 `x-direct-not-success reason=2` 作為最終權威 fatal。Activity 收到後續 HUP 時發出診斷 `GATEA_HUP_PRESERVE published=2`，**沒有**第二個 `GATEA_FATAL_HALT r-hup reason=6`。X 與 Activity 在 cleanup 前均已 fail-stop。凍結 judge：`R7_PASS post-draw-gl`。

歷史 `fdfb1ce` R7-05 仍為 VALID FAIL / 凍結，本格不得覆寫、不得改判成 PASS。

R7 overall 轉為 **IN PROGRESS**。不是完整 R7 PASS。下一凍結格是 R7-01，本任務不執行。

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
| 歷史 `fdfb1ce` R7-05 | VALID FAIL `halt_mismatch r-hup/6` / **凍結未覆寫** |
| 新候選 `a07d66c` R7-05 | **PASS**（本格） |
| R7 overall | **IN PROGRESS / NOT YET PASS** |
| Production Gate A | BLOCKED |
| R8/R9/R10 | NOT STARTED |

凍結 judge 對歷史 `runtime-fdfb1ce/r7-05/logcat-follow.txt` 仍判
`R7_FAIL halt_mismatch what=r-hup reason=6`。
對歷史 `runtime-7549e36/r7-qualification-01/r7-04/` 仍判
`R7_FAIL halt_mismatch what=x-direct-not-success reason=4`。
對 `runtime-fdfb1ce/r7-04-requalification-01/` 仍判 `R7_PASS fbo-incomplete`。

---

## Artifact provenance / installed binding

| 欄位 | 值 |
|---|---|
| SHA | `a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82` |
| parent | `fdfb1ce44b429897eda17c43bf33fbd37afe67f3` |
| branch | `fix/gatea-r7-hup-fatal-preserve-20260917` |
| CI | **35171333149** success，headSha exact |
| package | `com.waydefu.x11gpu` |
| versionName / versionCode | `1.03.01-a07d66c-17.09.26` / **15** |
| APK SHA256 | `a25861b41fe9088a7163e5d882909ca0a292780e418e1278665a436b27bface5` local=staged=installed MATCH |
| GitHub ZIP digest | `3c3ca807…adcb`（**不是** APK SHA256） |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` CONTINUITY PASS |
| Build ID | `ad3509c0e64d4de3c7846117978881995b2543f2` embedded == pulled installed MATCH |
| lastUpdateTime | 2026-09-17 13:03:17 |
| 安裝格 | `runtime-a07d66c/r0/` `INSTALL_A07D66C_BIND_PASS` |
| 先前 experimental | `1.03.01-fdfb1ce-16.09.26` lastUpdateTime 2026-09-17 00:54:07 |

---

## Stable before

| 欄位 | 值 |
|---|---|
| PID | **20146**（現場讀取；非歷史 843） |
| package | `com.termux.x11` `1.03.01-11b82d9-06.09.26` versionCode 15 |
| lastUpdateTime | 2026-09-07 22:55:03 |
| cmdline | `termux-x11 com.termux.x11 :1 -legacy-drawing` |

未 kill / 未 force-stop / 未安裝覆蓋 Stable。

---

## Runtime

| 欄位 | 值 |
|---|---|
| X PID | **8418** |
| DISPLAY | `:3` |
| cmdline | `termux-x11gpu com.waydefu.x11gpu :3` |
| Activity PID | **27372** `com.waydefu.x11gpu` Display #0 `display=0` COLD |
| renderer / GLES TID | Activity **8356**（DRAW / event35 / gles-renderer）；X Adreno / halt TID **8926** |
| 新鮮 X | ALIVE_8S；觸發後 `X3_DIED_AFTER_TRIGGER elapsed=1` |
| env | `/proc/8418/environ` 恰好 4 個 GATEA：PROTO=1 TELEMETRY=1 TEST_FAULT=post-draw-gl TEST_ARM=1 |
| fixture | `p_r3_single_direct` ×**1**；GetImage FAIL（注入後預期）；holder `p_b3a_hold` HOLD READY |
| runner | `run-r7-05-requal-a07d66c.sh` shell exit **0** |
| ADB | live `_adb-tls-connect._tcp.local.` `adb-51c6f1fe-ZtRPH4` → `10.191.48.13:45697`；isolated 5038；`myron` / `25102PCBEG`；Awake；keyguard false |
| 證據目錄 | `runtime-a07d66c/r7-05-requalification-01/` 啟動前不存在 |

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
reason=2 = `FAIL_DRAW`。reason=4 TIMEOUT = **0**。

event35 去重後 **恰好 1**。raw `forbidden-audit.txt` `event35_count=2` 是 follow+unfiltered 重複擷取。

---

## Fatal chronology（follow 時間序）

1. `GATEA_FATAL_HALT what=x-direct-not-success reason=2` X PID 8418 TID 8926 — **此格契約期望身份 / 最後 applicable HALT**

`GATEA_HUP_PRESERVE published=2 nonce=12507998485584678728 generation=1` Activity PID 27372 — **診斷，不是 HALT**。

`r-hup reason=6` HALT count = **0**。

其他 conflicting `GATEA_FATAL_HALT` = **0**。

`x-observe-fatal` = 0。`x-test-fault-env` = 0。

凍結 `judge-r7.py post-draw-gl` `--x-alive 0 --exit-signal 0`（pre-cleanup：X 已死、Activity ABSENT、無 PID-bound crash）：
`R7_PASS post-draw-gl`  exit **0**。

`test-judge-r7.py` 16/16 PASS。judge SHA256 `fba3c10f…cc17` 未改。

---

## Forbidden after event 35（seq-deduped, serial 5 / generation 1）

SUCCESS=0 RELOCK_SRC=0 RELOCK_DST=0 REPAIR=0 ACK=0 PENDING_DEC=0 LEASE_RELEASE=0
later PUBLISH=0 event32=0 event34=0 Gcomp Done=0 fallback=0 replay=0

event 11/15/14 在 35 之後是本 selector 的 fence-satisfied / first-failed / completed，不在凍結 forbidden set。

觸發前 FPS 列有 `exa_solid_fallback=8`（13:04:09），屬 root/solid 啟動計數，不是 poisoned serial 5 的 fallback。

---

## Timeout / crash / fail-stop

EXA timeout=0；`x-exa-composite-wait`=0；reason=4 halt=0；timeout→Done=0。未改 2000 ms。

SIGSEGV=0 SIGILL=0 SIGABRT=0；X 8418 與 Activity 27372 PID-bound crash lines=0。
未宣稱 wait-status exit127（double-fork；證據是 X halt + `GATEA_HUP_PRESERVE` + pre-cleanup PID 消失）。

pre-cleanup：`x_pre_cleanup=DEAD pid=8418`；`activity_pre_cleanup=ABSENT expected_pid=27372`。
HUP 未走正常成功 cleanup。

---

## Cleanup / Stable after

Cleanup 後：X process ABSENT；`/tmp` 與 Termux tmp 的 X3 socket ABSENT；X3 lock ABSENT；runner `NO_X3_RESIDUE`。

Stable after：PID **20146**；cmdline `termux-x11 com.termux.x11 :1 -legacy-drawing`；`1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03 **unchanged**。未碰 Stable / HDMI 設定。HDMI observe-only `mDisplayId=0`。

---

## 分類

不是 INVALID：artifact MATCH、env EXACT、目錄原先不存在、無既有 X3、fixture ×1、hook 有打到、pre-cleanup X/Activity 狀態已知。

是 PASS：最後 applicable halt = `x-direct-not-success/2`；HUP preserve 診斷存在；r-hup/6 HALT=0；forbidden success=0；凍結 judge PASS。

不准 overlay 本目錄。不准 silent-retry。不准自動開 R7-01。下一步若另開授權才是凍結 matrix 的 R7-01。
