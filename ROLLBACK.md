# Termux:X11 Stable 回退說明書（ROLLBACK）

> 適用：`com.termux.x11` 被誤裝實驗／CI 包導致 `:1` 無法啟動。
> 原則：只覆蓋、不卸載，資料原地保留。實績：2026-09-07 P2STAGE 誤裝 → control 回退，設定無損。

## 1. 鐵律（禁止）

- 任何實驗／CI APK 只准裝進 `com.waydefu.x11gpu`，永禁覆寫 `com.termux.x11`。
- 回退禁「刪掉重裝」——同簽名下 `adb install -r` 即可保留資料，卸載反而清掉 App 設定。
- 目前 Stable 凍結包：`1.03.01-11b82d9-06.09.26`（control build，SHA256 見 §3）。舊版 `1.03.01-6d3c688-27.08.26` 只屬 2026-09-07 歷史凍結標籤，不作為目前回退目標。

## 2. 確認裝錯（唯讀，先做）

```bash
adb shell dumpsys package com.termux.x11 | grep -iE "versionName|versionCode|lastUpdateTime|firstInstallTime"
```

- `versionName` 若是實驗字尾（例 `1.03.01-6721db9`）即中招。
- 進階：比對 `/data/app/~~*/com.termux.x11-*/base.apk` 的 sha256 與 `unzip -p … lib/arm64-v8a/libXlorie.so | od` 讀 BuildId，
  再用 `readelf -n`／`objdump -d` 在實際出事庫上定位崩潰偏移（勿拿別的建置的符號來套）。

## 3. 回退包取得與驗證（唯讀）

- 預設目標：`evidence/control/termux-x11-universal-debug.apk`（`1.03.01-11b82d9`，versionCode 15）。
- 必驗兩項，任一不合即停：
  - `sha256sum` ＝ `aad3d433f47cf7757d959166ce187b8b679e989289049b73f09a732889ea98e9`
  - `apksigner verify --print-certs` 的 SHA-256 ＝已安裝包的簽名（`b6da0148…`；可用同指令讀已安裝 base.apk）。
- 簽名不同＝不可 `-r` 覆蓋（會丟資料），停下回報。

## 4. adb 連線（本機踩坑記錄）

```bash
PORT="$(f8-adb-port)"          # mDNS 找無線偵錯 port
adb kill-server               # 清掉陳舊 server（安全，會自起）
sleep 2
env ANDROID_NO_USE_FWMARK_CLIENT=1 HOME=/data/data/com.termux/files/home \
  /data/data/com.termux/files/usr/bin/adb connect 10.129.215.219:"$PORT"
adb devices                   # 須顯示 device
```

- PRoot 下 `fakeroot` 會讓 adb 起不來（libc 預載衝突），不要加。
- `connect` 報失敗但 TCP 通（`</dev/tcp/IP/PORT` 能開）：先 `kill-server` 再連；仍不行＝手機要重配對，
  在手機「無線偵錯 → 使用配對碼配對裝置」取 port＋6 位碼跑 `adb pair`。
- port 會變（曾用 46415／35859），每次重抓，勿寫死。

> 2026-09-12 註記（上方原文保留，09-07 實戰流程不動）：現行 isolated lane SOP 見 `ADB-CONNECT.md`（`-L tcp:5038`，不碰 5037；adb 35.0.2 無 mDNS 子命令；pairing port ≠ connect port；配對碼只打本機提示，禁落檔）。

## 5. 執行回退

```bash
adb install -r evidence/control/termux-x11-universal-debug.apk
```

- 同 versionCode 免 `-d`；若目標版號較低才加 `-d`（`install -r -d`）。
- 成功的唯一判準：輸出 `Success`。

## 6. 驗證回退

```bash
adb shell dumpsys package com.termux.x11 | grep -iE "versionName|firstInstallTime"
```

- `versionName` 回到 `1.03.01-11b82d9`。
- `firstInstallTime` 必須是原日期（被改＝資料被清，回報）。
- 手機開 Termux:X11 App，下 `termux-x11 :1 -legacy-drawing` 起 XFCE，確認 xfwm 存活不再閃退。

## 7. 資料說明（回答「重裝資料還在嗎」）

- 留得住：PRoot／XFCE／專案／sdcard（根本不在此包）、App 設定（`-r` 原地保留）。
- 留不住的只有一種情況：被迫卸載重裝（簽名不同時）——會清 App 偏好，需手動重設顯示選項。
- 本次回退採同簽名覆蓋，無此問題。

## 8. 事後記錄

- 在 `evidence/COORDINATION.md` 追加事故＋回退＋版號／sha／時間。
- 複查是誰裝錯的（CI 出處、下午對話紀錄），把缺口補進本文件。
