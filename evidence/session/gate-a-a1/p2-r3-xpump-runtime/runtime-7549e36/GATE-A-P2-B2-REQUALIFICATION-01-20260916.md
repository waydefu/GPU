# 7549e36 B-2 重資格格 01 — 2026-09-16 `B2_REQUALIFICATION_INVALID`

這是**第一次**針對 `7549e36` 的 B-2 重資格授權格。
不是 `0d72332` 歷史 FAIL 的重跑，不是 `repair-validation-01` 重跑，不是 R7。

## 主判決

`B2_REQUALIFICATION_INVALID`

原因：預檢無法 live-fetch 無線偵錯 `_adb-tls-connect._tcp.local.` TLS 端點，因此**不能**重綁已安裝 APK SHA／signer／Build ID，也**不能**啟動新鮮 experimental `:3`。B-2 各強制階段（oracle／stress100／mixed100／stress1000）**未執行**。

這不是產品 FAIL，也不是 CASE_LOOP 回歸。B-2 狀態維持歷史 `0d72332` **BLOCKED**。

## 本格凍結

路徑：`runtime-7549e36/b2-requalification-01/`

- 無 `oracle.out`／`x1000.out`（階段未開）
- 不准覆寫本格
- 不准靜默開 `rerun1`
- 下一次 B-2 授權必須用**新格**（例如 `b2-requalification-02`），且必須先有 live TLS endpoint

## 候選（歷史已安裝；本格未重綁）

| 欄位 | 值 |
|---|---|
| SHA | `7549e3667ec03b8b5e50d2e5befe03065840bbd9` |
| CI | **35084701124** |
| 期望 package | `com.waydefu.x11gpu` |
| 期望 version | `1.03.01-7549e36-16.09.26` / 15 |
| 期望 APK SHA256 | `45500894023208963b3b1cd51fb7f3aa61807a25e1d70b322f7a7fdad7e14bc3` |
| 期望 signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` |
| 期望 Build ID | `4c5b7b86c18ec4e9bb14720c4615a25c1d6a8f81` |
| 本格 installed binding | **NOT RUN** |

上次成功安裝／repair-validation 綁定仍在凍結 `runtime-7549e36/r0/` 與 `repair-validation-01/`。本格不得沿用那些綁定當 B-2 證據。

## ADB 發現

| 檢查 | 結果 |
|---|---|
| isolated 5038 | PASS（adb 35.0.2，pidfile 10513） |
| `devices -l` | empty |
| mDNS 6s / 12s / 15s / 20s | `MDNS_ENDPOINTS` 空 |
| raw PTR `_adb-tls-connect._tcp.local.` 8s | 0 replies |
| pairing mDNS | 空 |
| 上次 live `10.191.48.13:36483` | ping 失敗；connect Connection timed out |
| 目前 wlan0 `192.168.1.101:36483`（舊 TLS port、新 IP，單次） | Connection refused |
| `service.adb.tls.port` | EMPTY |
| `persist.adb.tls_server.enable` | EMPTY |
| `sys.usb.config` | `adb`（USB tethering 已不在） |
| CERT_UNKNOWN | 未出現（端點根本連不上） |
| 端口掃描 | 未做 |

本機即 myron（`ro.product.device=myron`）。wlan0=`192.168.1.101`；閘道 `192.168.1.1` ping 通。無線偵錯 TLS 伺服器未在廣告。

## Stable / X3（本機 /proc，無 dumpsys）

| | |
|---|---|
| Stable PID | **16485**（repair-validation 當時為 14604；本程序未殺、未重啟、未 force-stop） |
| Stable cmdline | `termux-x11 com.termux.x11 :1 -legacy-drawing` |
| X3 | 無 |
| X3 socket/lock | 無 |
| HDMI | observe-only；無 ADB 故未 dumpsys display |

## B-2 序列

全部強制階段 executions = 0。沒有重試。

## 狀態不變

- R6 = PASS / frozen `0f1e546`
- RCA-1 = FIXED / DEVICE-PROVEN
- CASE_LOOP historical = DEVICE-PROVEN
- 7549e36 CASE_LOOP repair = DEVICE-VALIDATED（凍結 repair-validation-01）
- B-2 = **仍 BLOCKED**（權威仍是 `0d72332` serial 2370 / rerun1 1810）
- R7 = NOT STARTED
- Production Gate A = BLOCKED
