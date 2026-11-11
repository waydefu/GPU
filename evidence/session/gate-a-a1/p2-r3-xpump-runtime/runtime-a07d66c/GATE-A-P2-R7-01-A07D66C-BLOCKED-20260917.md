# a07d66c R7-01 裝置資格格 — 2026-09-17 `R7_01_A07D66C_QUALIFICATION_BLOCKED`

授權：恰好一次 R7-01 / `src-ready-miss`。本輪 **未啟動 cell**。
不是 FAIL。不是 INVALID。不是 R7-02+。未改 source / judge / timeout / ABI。
未碰 Stable / HDMI。未重裝 APK。未覆寫 `r7-05-requalification-01/`。

## 主判決

`R7_01_A07D66C_QUALIFICATION_BLOCKED`

阻擋點：沒有可信、已審查、可跑 **R7-01 / `src-ready-miss` / `runtime-a07d66c/r7-01`** 的 a07d66c runner。

唯一 a07d66c-aware runner 是 R7-05 專用腳本，硬鎖 cell 與 fault，dry-run 對 R7-01 直接 REFUSE。
fdfb1ce / 7549e36 runners 硬編舊 version 與舊 evidence root，本輪禁止使用、禁止 sed、禁止複製改幾行當權威。

Live artifact binding **MATCH**。X3 **ABSENT**。凍結 judge / fixture **存在**。R7-05 PASS 證據 **可確認**。
這些不足以授權在本任務內發明新 runner。

法定 cell 目錄 `runtime-a07d66c/r7-01/` **仍不存在**。本輪證據在
`runtime-a07d66c/r7-01-blocked-preflight/`，避免污染下次 `test ! -e "$CELL"`。

---

## 狀態（不變）

| 項目 | 值 |
|---|---|
| R6 | PASS / frozen `0f1e546` |
| B-2 | PASS 凍結 |
| `fdfb1ce` R7-04 | PASS 凍結 |
| 歷史 `fdfb1ce` R7-05 | VALID FAIL 凍結 |
| `a07d66c` R7-05 | PASS 凍結 |
| R7-01 | **NOT RUN / BLOCKED** |
| R7 overall | **IN PROGRESS** |
| next frozen cell | 仍是 **R7-01 / src-ready-miss**（需另開 runner 審查後再授權執行） |
| Production Gate A | BLOCKED |
| R8/R9/R10 | NOT STARTED |

---

## Runner authority

| 檔案 | SHA256 | 可否跑本格 |
|---|---|---|
| `run-r7-05-requal-a07d66c.sh` | `46c24fc94228bbc622886b51f45f1fcbd1580cc6a6ebbc9b64e09fc472096473` | **否**：EXPECT_VERSION=a07d66c，但 CELL 鎖 `r7-05-requalification-01`、FAULT 鎖 `post-draw-gl`；標頭寫 Not R7-01+ |
| `run-r7-one-cell-fdfb1ce.sh` | `f4fb89d6…f471` | **否**：EXPECT_VERSION=fdfb1ce；CELL 必須在 `runtime-fdfb1ce/` |
| `run-r7-04-requal-fdfb1ce.sh` | `b19831f6…58e9` | **否**：R7-04 only |
| `run-r7-one-cell.sh` | `d675b999…5e32` | **否**：EXPECT_VERSION=7549e36 |

Dry-run（未連 ADB 業務、未建目錄）：

```
REFUSE CELL must be .../runtime-a07d66c/r7-05-requalification-01 got=.../runtime-a07d66c/r7-01
exit 9
```

---

## Live binding（read-back，未重裝）

ADB live mDNS `adb-51c6f1fe-ZtRPH4` → `10.191.48.13:45697`；isolated 5038；`myron`；Awake。

| 欄位 | 值 |
|---|---|
| package | `com.waydefu.x11gpu` |
| versionName / versionCode | `1.03.01-a07d66c-17.09.26` / 15 |
| lastUpdateTime | 2026-09-17 13:03:17（與 R7-05 安裝相同） |
| APK SHA256 | `a25861b41fe9088a7163e5d882909ca0a292780e418e1278665a436b27bface5` MATCH |
| signer | `b6da0148…e5e1` MATCH |
| Build ID | `ad3509c0e64d4de3c7846117978881995b2543f2` MATCH |

`LIVE_BINDING_MATCH`

---

## Stable / X3（observe-only）

Stable PID **20146**；`termux-x11 com.termux.x11 :1 -legacy-drawing`；`1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03。
未 kill / force-stop / 重裝。

X3 process ABSENT；socket ABSENT；lock ABSENT。
HDMI observe-only `mDisplayId=0`。

凍結 `judge-r7.py` SHA `fba3c10f…cc17` 未改；`test-judge-r7.py` 16/16 PASS。
fixture SHA 與 R7-05 相同。

---

## 未執行

未啟動 experimental Activity、未啟動 X3、未 export Gate A env、未跑 holder / `p_r3_single_direct`、未呼叫 judge 對新 cell。

因此 Runtime / Environment / Sequence / Fatal / Forbidden 皆 **NOT RUN**。

---

## 下一步（建議，本任務不執行）

另開明確工具審查任務：寫一份 **a07d66c R7-01** runner（可參數化 FAULT/CELL，或專用 `run-r7-01-a07d66c.sh`），審查後再授權單格執行。
不要把 R7-05 runner 放寬成本任務的一部分。不要 sed fdfb1ce runner。
