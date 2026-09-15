# U4-L1 preflight — ADB endpoint unavailable

範圍：尚未跨越 device-operation boundary；沒有啟動 Activity、X server、holder、oracle、cell 或 benchmark。

## 已完成的本地準備

- `patches/p_b3a_hold.c` 與 `patches/p_b3a_cost.c` 已由目前工作區用
  `cc -O2 -Wall -Werror` 重建，rc=0。
- `p2b3a_session.sh` 已以 `bash -n` 驗證。它只接受 explicit serial，且
  一個 session 固定為 `com.waydefu.x11gpu`／`DISPLAY=:3`；所有 output prefix
  必須不存在，避免覆寫既有 raw evidence。
- 尚未改 native renderer/Xserver/telemetry source；Stable 未操作。

## Fresh ADB attempts

1. 已知舊 serial 的 `adb -s ... get-state`：

```text
error: device '192.168.1.101:45279' not found
```

2. 現有 adb 的 mDNS discovery：

```text
error: unknown host service 'mdns:services'
List of discovered mdns services
```

沒有列出服務，不能據此猜 port。

3. `/data/data/com.termux/files/usr/bin/f8-adb-port`（在目前 Ubuntu PRoot
context）失敗於 native-Termux Python extension loader：

```text
OSError: dlopen failed: library "libc.so.6" not found
```

完整 traceback 由 terminal execution log 保存。這與已知 PRoot/Termux native
boundary 一致；不是可藉由重試或掃描 port 解決的 B3a 問題。

## Verdict

```text
U4-L1: ADB_FRESH_PREFLIGHT_BLOCKED
Device/runtime mutation: NONE
Stable: UNTOUCHED
```

在原生 Termux 取得並驗證新的 Wireless ADB endpoint 前，不得開始 U4-L1、cold-N5
或 C2。不得使用失效的舊 serial、掃描 LAN port，或更動 ADB/PRoot 安裝。
