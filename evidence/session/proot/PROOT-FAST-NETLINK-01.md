# PROOT-FAST-NETLINK-01 — proot-fast 讓 getifaddrs 失敗（回歸）與修正（2026-09-25）

## 發現
使用者開啟日常加速版（proot-fast2）後，mdns 探測（python zeroconf）失敗：`ifaddr.get_adapters()` → `OSError EINVAL`；
Node `os.networkInterfaces()` 丟例外（`uv_interface_addresses ... error 22`）；`ip addr` → `Cannot send dump request`。
PROOT-KOMPAT-OVERHEAD-01 的功能 smoke **沒有涵蓋網路介面列舉**——這是 smoke 的漏洞。

## 根因（原始碼 `src/syscall/enter.c`）
Android 拒絕本 App 的 rtnetlink（連讀取也不行，見下表 v3）。stock termux/proot 在 `socket(AF_NETLINK, NETLINK_ROUTE)` 時換成 AF_UNIX DGRAM，
並攔 bind／sendto／sendmsg／recvfrom／recvmsg，以 tracer 端（bionic）`getifaddrs` 的真實資料合成 netlink 回應。
proot-fast v1 起這些收發只有 `PROOT_BWRAP_COMPAT` 才攔，但 socket() 的替換仍發生（fake_id0 的 socket 過濾讓它停下）→ 送出 sockaddr_nl 到 AF_UNIX → EINVAL。

## 量測 `proot-fast3-netcheck-01.txt`（PRoot 外經 run-as，日常 42 參數）
| | stock | v2 | v3（無替換） | v3＋`PROOT_BWRAP_COMPAT=1` |
|---|---|---|---|---|
| ifaddr／Node／ip | ✅ 5 個介面 | ❌ EINVAL | ❌ EACCES | ✅ 5 個介面 |
| futex_wake µs | 28.2 | 0.31 | 0.25 | 0.22 |
| socket send+recv µs | 60.0 | 1.15 | 1.17 | 57.7 |
v3 = v2 ＋「沒有相容旗標就不替換」（`out3/bin/proot-fast3`，sha `557a48bd`）：證明真 netlink 在此機一定被拒；**不部署**。

## 修正：f8ifaddrs（guest 端 getifaddrs 後備，`tests/proot/f8ifaddrs.c`，fork `git log` 最新）
先呼叫真的 getifaddrs；失敗才用 ioctl `SIOCGIFCONF`／`SIOCGIFFLAGS`／`SIOCGIFNETMASK`／`SIOCGIFBRDADDR` 組 IPv4 清單（Android 允許）；
單一 malloc 區塊，glibc 的 freeifaddrs（=free）可直接釋放。安裝：`/usr/local/lib/libf8ifaddrs.so`（sha `6530de35`）＋`/etc/ld.so.preload`。
- Node `os.networkInterfaces()`：`lo 127.0.0.1/255.0.0.0`、`wlan0 10.191.48.13/255.255.255.0` ✅（不需環境變數）。
- 同環境 smoke 有／無 shim 逐字相同（23 行）。
- 限制：只有 IPv4；Python `ifaddr`（ctypes 直接向 libc 取符號，繞過 preload）仍失敗；`ip` 仍失敗（直接用 netlink）。
- 還原：刪 `/etc/ld.so.preload`。日常維持 proot-fast2（不需重開桌面）。
- ADB 探測在 ifaddr 失敗時的替代：UDP connect 取本機 IP ＋ TCP 掃 30000–50000（本次找到 45503）。
