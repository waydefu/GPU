# ADB 標準連線 SOP（F8 本機無線偵錯）

來源：`ROLLBACK.md §4` 實戰踩坑＋`F8-LOCAL-ENV.md`＋`HANDOFF.md` 安全規則。IP 與 port 都會變，一律當次現抓，勿寫死。

## 0. 手機端前置

- 設定 → 開發人員選項 → 無線偵錯 → 開啟。
- 本機與手機在同一網路（歷史 IP：`10.129.215.219`、`10.56.180.219`、`192.168.1.100`，僅供認網段參考；2026-09-14 Gate A 輪曾用 `192.168.1.100:46385`，resume 必須現抓 IP/port）。

## 1. 連線（native adb，isolated 5038）

- authority binary：`/data/data/com.termux/files/usr/bin/adb`（ARM64／Bionic，35.0.2）。
- `/usr/local/bin/f8-adb-port` 是 PRoot wrapper（用 Ubuntu `/usr/bin/python3` 跑 Termux helper），不可作 authority；直接跑 Termux helper 會 `dlopen failed: library "libc.so.6" not found`，不代表 adb 壞掉，不要改 helper。
- prompt 顯示 `.../ubuntu/rootfs $` 是自動進 PRoot，不用 `exit`；直接用絕對路徑呼叫 native adb。
- key 注意：pair 跟 connect 必須用同一組 key（同一 `HOME`）。實測手機授權的是 Termux 家目錄 key；isolated server 須加 `HOME=/data/data/com.termux/files/home`，否則 TLS 指紋對不上（`CERTIFICATE_UNKNOWN`）。
- isolated listener：`-L tcp:5038`（此版本 `-L tcp:127.0.0.1:5038` 會拒絕指定 hostname）。不碰 5037，不 kill 5037 server。

```bash
TADB=/data/data/com.termux/files/usr/bin/adb
env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
  "$TADB" -L tcp:5038 server nodaemon   # 背景跑，只屬於本次 lane
"$TADB" -H 127.0.0.1 -P 5038 server-status
"$TADB" -H 127.0.0.1 -P 5038 devices -l
PORT="$(f8-adb-port)"          # 僅在真正 native Termux 下可信；PRoot wrapper 結果無效
"$TADB" -H 127.0.0.1 -P 5038 connect <手機IP>:"$PORT"
"$TADB" -H 127.0.0.1 -P 5038 devices -l   # 須顯示 device
```

後續所有 adb 一律加 `-H 127.0.0.1 -P 5038 -s <HOST:PORT>`，禁裸 `adb shell`／`adb install`。

## 2. 身份驗證（連上後必做，結果記入當次 evidence）

```bash
TADB=/data/data/com.termux/files/usr/bin/adb
"$TADB" -H 127.0.0.1 -P 5038 devices -l                       # device 上線
"$TADB" -H 127.0.0.1 -P 5038 -s <HOST:PORT> shell getprop ro.product.model    # 須為 F8（POCO F8 Ultra）
"$TADB" -H 127.0.0.1 -P 5038 -s <HOST:PORT> shell getprop ro.product.device   # 須為 myron
"$TADB" -H 127.0.0.1 -P 5038 -s <HOST:PORT> shell dumpsys package com.termux.x11 | grep -iE "versionName|firstInstallTime"
"$TADB" -H 127.0.0.1 -P 5038 -s <HOST:PORT> shell dumpsys package com.waydefu.x11gpu | grep -iE "versionName|firstInstallTime"
```

## 3. 踩坑表

| 症狀 | 解法 |
|---|---|
| `f8-adb-port` exit 1 | 手機無線偵錯沒開，或不在同網段 |
| PRoot 下 adb 起不來 | PRoot 勿加 `fakeroot`（libc 預載衝突）；直接用 native 絕對路徑，不用 `exit` 離開 PRoot prompt |
| `connect` 失敗但 TCP 通（`</dev/tcp/IP/PORT` 能開） | 先確認是否連到 5037 舊 server；改用 isolated `-L tcp:5038` lane 後重連，不 kill 5037 |
| adb 35.0.2 `mdns check`／`track-services`／`services` 不支援 | 此 client 無 mDNS discovery；改由手機無線偵錯主頁拿 fresh connect endpoint，不掃 port、不猜 port |
| `SSLV3_ALERT_CERTIFICATE_UNKNOWN`／transport offline | DEVICE AUTH FAILURE：endpoint 拒收，不重試同一 endpoint；回手機重配對 |
| 配對 port vs 連線 port | `adb pair` 只能用 pairing port；連線必須用配對完成後主頁的新 connect port，兩者不可混用；配對碼只在本機互動提示輸入，禁貼聊天、禁寫檔 |
| 重連仍不行 | 手機要重配對：無線偵錯 → 使用配對碼配對裝置，取配對 port＋6 位碼跑 `adb pair <IP:配對port>`（碼只打在本機提示），再回 §1 |
| port 對不上 | port 每次會變（曾見 46415／35859／42761），每次重抓 |

## 4. 安全鐵律（HANDOFF.md §Runtime，連上後任何操作前重讀一次）

- 實驗／CI APK 只准裝進 `com.waydefu.x11gpu`，永禁覆蓋 `com.termux.x11`（Stable `:1` 日用，不碰）。
- Kill 實驗 X 只認 cmdline 前綴 `termux-x11gpu com.waydefu.x11gpu :3`。
- 禁 `pkill -f f8-x11gpu`，禁 `logcat -c`。
- 同簽名覆蓋才可用 `-r`；簽名不同停下回報（會清資料）。

## 5. 事後

- 連線參數（IP／port／device 狀態／兩包版號）寫入當次 `evidence/session/<area>/`，勿改寫 `F8-LOCAL-ENV.md` 的歷史時間戳。
