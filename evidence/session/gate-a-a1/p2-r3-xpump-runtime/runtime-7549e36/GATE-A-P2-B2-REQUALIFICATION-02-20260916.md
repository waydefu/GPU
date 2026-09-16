# 7549e36 B-2 重資格格 02 — 2026-09-16 `B2_REQUALIFICATION_PASS`

這是無線偵錯 TLS 恢復後的**第一個可判定** B-2 格。
凍結格 `runtime-7549e36/b2-requalification-01/` 維持 **INVALID**（當時無 live TLS），**未覆寫、未開 rerun1**。
不是 `0d72332` 歷史 FAIL 重跑，不是 `repair-validation-01` 重跑，不是 R7。

## 主判決

`B2_REQUALIFICATION_PASS`

B-2 transitions BLOCKED → PASS on 7549e36.

## 候選 provenance（本格重綁）

| 欄位 | 值 |
|---|---|
| SHA | `7549e3667ec03b8b5e50d2e5befe03065840bbd9` |
| CI | **35084701124** |
| package | `com.waydefu.x11gpu` |
| versionName / versionCode | `1.03.01-7549e36-16.09.26` / **15** |
| lastUpdateTime | 2026-09-16 19:03:48 |
| APK SHA256 | `45500894023208963b3b1cd51fb7f3aa61807a25e1d70b322f7a7fdad7e14bc3` MATCH |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` MATCH |
| Build ID | `4c5b7b86c18ec4e9bb14720c4615a25c1d6a8f81` MATCH |
| installed binding | **PASS** |

Harness：`p-b2-oracle` SHA256 `19154bf2…c726`；`p_b2_stress` SHA256 `3e79b5cf…3c56`。

## ADB

Live-fetch `_adb-tls-connect._tcp.local.` `adb-51c6f1fe-ZtRPH4` → `192.168.1.101:46061`。
identity `myron` / `25102PCBEG`。Awake；keyguard false。HDMI observe-only `mDisplayId=0`。

## Runtime

| 欄位 | 值 |
|---|---|
| X PID | **32228** |
| DISPLAY | `:3` |
| cmdline | `termux-x11gpu com.waydefu.x11gpu :3` |
| Activity PID | **10703** `com.waydefu.x11gpu` displayId=0 |
| renderer TID | Activity `gles-renderer` **32162**；X Gcomp/EGL **32667** |
| environ | `NO_GATEA_ENV`（`/proc/32228/environ` 無 `TERMUX_X11_GATEA*`） |

## B-2 序列（各 1 次）

| Stage | Executions | Result | X alive | Timeout | Fatal | Exactness |
|---|---|---|---|---|---|---|
| Oracle 1514 | 1 | PASS 1514/1514 | yes 32228 | 0 | 0 | maxΔ=0 ±1=0 Xnz=0 |
| stress100 | 1 | `ok=100 fail=0 n=100 alive=1` mixed=0 | yes | 0 | 0 | 無 mismatch |
| mixed100 | 1 | `ok=100 fail=0 n=100 alive=1` mixed=1 | yes | 0 | 0 | 無 mismatch |
| stress1000 | 1 | `ok=1000 fail=0 n=1000 alive=1` mixed=0 | yes | 0 | 0 | 無 mismatch |

Oracle NEG（software 預期）：src-op / mask-a8 / dst-argb / bilinear / repeat 皆 completed。
GATEA_EVENT=0；event=35=0。

## Composite / liveness

- Gcomp Prepare TRUE = 2715；RECT = 2715；Done = 2715
- `rendererApplyPendingGpuCopies` = 2717（無 serial；RECT→apply 為 wall-clock proxy）
- RECT→Done n=2715 max=**0.111 s** ≥2000 ms = **0**
- RECT→apply proxy n=2714 max=**1.451 s** ≥2000 ms = **0**
- PIXEL_RGB_MISMATCH = 0
- PIXEL_XBYTE_MISMATCH = 0
- stale destination = 0
- EXA timeout = 0；`x-exa-composite-wait` = 0；GATEA_FATAL_HALT = 0；timeout→Done = 0
- SUMMARY `where=x-close-screen` generationFatal=0（正常 teardown，非 timeout fatal）

## Cleanup / Stable

- killed X 32228；`am force-stop com.waydefu.x11gpu`
- **NO_X3_RESIDUE**
- Stable PID **16485** 前後不變；`1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03
- HDMI observe-only；未改設定

## 狀態含義

R6 = PASS / frozen
RCA-1 = FIXED / DEVICE-PROVEN
CASE_LOOP historical = DEVICE-PROVEN
7549e36 CASE_LOOP repair = DEVICE-VALIDATED
**B-2 = PASS**
R7 = NOT STARTED
Production Gate A = still BLOCKED

不准從本格自動開 R7。timeout 2000 ms 未改。`327b028` 仍 SUPERSEDED。
