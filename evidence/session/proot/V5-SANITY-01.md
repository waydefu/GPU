# V5-SANITY-01 — 日常程式在 proot-fast5 下的功能健康檢查（2026-09-25，非判決測試）

使用者決定把日常切到 v5（`f8desk`／`f8desk-external` 的 PD_PROOT_BIN 區塊改為 v5 → v2 → 原版，備份 `*.bak-20260925-v5`），並要求「簡單檢查加速版還有沒有問題」。

## 1. 日常程式開啟檢查（`proot/v5-sanity-01`，`app_idle.sh` `APP_IDLE_SANITY=1`，PF_BIN=`out5/bin/proot-fast5`，DISPLAY :3）
每個程式一輪：新開 v5 proot、載入 60 s、閒置 60 s、run-as 側結束。
| 程式 | 追蹤器 | 視窗 | 閒置窗程序數 t0／t1 | 觸控 | 殘留 | 追蹤器結束 |
|---|---|---|---|---|---|---|
| claude（Claude Desktop，拋棄式設定檔） | proot-fast5 | 1 | 18／18 | 0 | 0 | true |
| chatgpt（含 Codex） | proot-fast5 | 2 | 18／18 | 0 | 0 | true |
| chatgptweb（Chromium） | proot-fast5 | 2 | 23／23 | 0 | 0 | true |
| hermes | proot-fast5 | 1 | 16／16 | 0 | 0 | true |
| cursor | proot-fast5 | 1 | 22／22 | 0 | 0 | true |
runner `CMD_CAPTURED` rc=0；97 次 TERM、0 KILL；Stable 前後 JSON 相同；事後 run-as 側殘留 0（唯一命中是本檢查指令自己的 shell）。

## 2. 日常操作對照（`daily_check.sh`，PRoot 外經 run-as）
Node 網路介面、Python venv、`git clone --local`（硬連結 → link2symlink，物件 nlink 2）＋`git fsck`／status／log、tar 含硬連結、`cp -a`、`find -links 2`、`apt-get -s`、pathlib rglob：
- **v5 與 v2 逐字相同**（14 行）。
- **原版與 v2** 只差 Node 介面清單：原版 `dummy0,lo,r_rmnet_data0,rmnet_data0,wlan0`，加速版＋f8ifaddrs `lo,wlan0`（shim 只有 IPv4；那三個介面只有 IPv6 link-local，本機不允許讀 IPv6 介面資訊）。
- **原本就有的問題（原版也一樣）**：tar 解開含硬連結的目錄時 `Cannot change mode to rwxrwxrwx: No such file or directory`（link2symlink 與 tar 的互動），非加速版引入，未處理。
