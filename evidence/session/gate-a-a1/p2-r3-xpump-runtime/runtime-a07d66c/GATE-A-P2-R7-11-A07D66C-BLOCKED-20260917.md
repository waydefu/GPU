# a07d66c R7-11 裝置資格格 — 2026-09-17 `R7_11_A07D66C_QUALIFICATION_BLOCKED`

授權：恰好一次全新 R7-11 / `serial-wrap` / `direct`，候選 `a07d66c`，使用已 qualified dedicated `run-r7-11-a07d66c.sh`。
本輪 **未啟動 cell**。不是 FAIL。不是 INVALID。不是產品 RCA。不是 R7-10+。
未改 source / judge / timeout / ABI / classifier / dedicated runner / generic runner。
未碰 Stable / HDMI。未重裝 APK。未覆寫任何已凍結 R7 / B-2 cell。

## 主判決

`R7_11_A07D66C_QUALIFICATION_BLOCKED`

阻擋點：孤立 ADB 5038 nodaemon 仍活著，但 **live `_adb-tls-connect._tcp.local.` 無 IPv4 endpoint**，因此沒有可信 `SERIAL=HOST:PORT`。依技能與本輪授權，不得硬編碼上一格 `10.191.48.13:44985`。

因此：未連裝置、未核對 live APK pull、未 invoke dedicated runner。

法定 cell 目錄 `runtime-a07d66c/r7-11/` **仍不存在**。本輪證據在
`runtime-a07d66c/r7-11-preflight/`，避免污染下次 `test ! -e "$CELL"`。

---

## 狀態

| 項目 | 值 |
|---|---|
| R6 | PASS / frozen `0f1e546` |
| B-2 | PASS 凍結 |
| R7-04 / 歷史 R7-05 FAIL / a07d66c R7-05 | 凍結未重跑 |
| R7-01 / R7-02 / R7-03 / R7-06 / R7-07 / R7-08 / R7-09 | PASS 凍結（未重跑） |
| R7-11 dedicated runner | **R7_11_A07D66C_RUNNER_QUALIFIED**（未改） |
| `a07d66c` R7-11 device | **NOT RUN / BLOCKED**（ADB authority） |
| R7 overall | **IN PROGRESS** / 仍 9/13 |
| next frozen cell | 仍是 **R7-11 / serial-wrap**（須先恢復 live mDNS，再另開單格授權） |
| Production Gate A | BLOCKED |
| R8/R9/R10 | NOT STARTED |

---

## Artifact / runner（host 核對；live pull 未達）

| 欄位 | 值 |
|---|---|
| candidate | `a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82` |
| dedicated runner | `run-r7-11-a07d66c.sh` SHA256 `74385947cbcef8dbeeb1deea9722b424828d9bf3780a4dd0279290df5310c453` size 25716 **HASH_MATCH**；**未執行** |
| classifier | `classify_r7_11_serial_wrap.py` SHA256 `3a0af4ff367bf18da2edd0888bda898b10c079c6e0bc93b95e3a111e5dd6b107` **HASH_MATCH**；**未執行** |
| generic runner | 未使用；SHA 仍 `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded`；r7-11 仍 REVIEW_REQUIRED / live REFUSE |
| judge | SHA256 `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17` host `test-judge-r7.py` **16/16**；未對裝置 cell 執行 |
| fixture / holder | `p_r3_single_direct` `b424a634…8c13`；`p_b3a_hold` `3417abbf…b5ca` HASH_MATCH；未啟動 |
| CELL | `runtime-a07d66c/r7-11` 執行前與執行後皆 **ABSENT** |
| live APK | **未達**（無 SERIAL）。last known installed（R7-09 凍結）：`1.03.01-a07d66c-17.09.26` / 15 / SHA256 `a25861b4…ace5` / Build ID `ad3509c0…43f2`。本輪未重裝、未 mismatch 判定。 |

---

## ADB / mDNS

孤立 5038 nodaemon PID **3065** LIVE：`adb -L tcp:5038 server nodaemon`。未另開第二個 5038。未碰 5037。

| 探測 | 結果 |
|---|---|
| `mdns-address.py` 6s | `MDNS_ENDPOINTS` 無 `address=` |
| `mdns-address-15s.py` | 同樣空 |
| zeroconf dump 20s | `raw_count=0` |
| 再一次 15s | 空 |
| `avahi-browse -rpt _adb-tls-connect._tcp` | `Failed to create client object: Daemon not running` |
| local `getprop service.adb.tls.port` | **EMPTY** |
| host `wlan0` | `192.168.1.101/24`（與歷史 R7-09 `10.191.48.13:44985` 不同網段） |

**未**把歷史 `10.191.48.13:44985` 當本輪 SERIAL。`adb devices` 在 connect 前為空。

---

## Stable / X3 / HDMI

Stable 主機 PID **20146**；`termux-x11 com.termux.x11 :1 -legacy-drawing`。前後相同。未 kill / force-stop / 重裝。
因無 SERIAL，無法 dumpsys `versionName` / `lastUpdateTime`；host PID/cmdline 與 R7-09 記錄一致。

X3 process / socket / lock：**ABSENT**（pre 與 after）。

HDMI：observe-only；無 SERIAL 故無 dumpsys；未做任何 HDMI mutation。

---

## 未執行項目

- dedicated `run-r7-11-a07d66c.sh`
- generic `run-r7-one-cell-a07d66c.sh`
- classifier / device judge
- holder `p_b3a_hold` / fixture `p_r3_single_direct`
- R7-10 或任何後續 cell
- 任何已凍結 cell 重跑

---

## Next

恢復 live `_adb-tls-connect._tcp.local.`（無線偵錯 advertisement + IPv4 endpoint），再另開 **一格** R7-11 授權。
不要從本 packet 執行 cell。不要 silent-retry 本 preflight。不要把 BLOCKED 當 FAIL。
不要開始 R7-10。Production Gate A 仍 BLOCKED。
