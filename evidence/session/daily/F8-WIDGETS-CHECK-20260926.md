# F8 小工具檢查與修正（2026-09-26 晚上）

使用者要求「每個都檢查，有問題就修，外接螢幕和滑鼠插著，歡迎自行測試」。
- 實測全程用隔離的 ADB 通道 5038（`ANDROID_ADB_SERVER_PORT=5038`，從 Termux 那側不被追蹤地執行），沒有碰使用者的 5037 伺服器；測完用 `adb -P 5038 kill-server` 收掉。
- 素材：`daily/f8-widgets-20260926/`，包括探針、各項輸出、修正腳本，還有修正後各工具的現況副本（`*.now`）和 `sha256.txt`。

## 找到的問題與修正
| # | 問題 | 影響 | 修正 | 備份 |
|---|---|---|---|---|
| 1 | f8desk／f8desk-external 用 `setsid 常駐程式 &` 啟動 shard-daemon：常駐程式變成 f8desk 背景子程序的子程序，子程序一直等它；桌面的 proot 又在等這個子程序 | 叫起常駐程式的那次開機，舊桌面追蹤器永遠結束不了（31217 殘留，0 個 tracee） | 改成 `setsid -f`（用模擬腳本驗證：父程序變成 1）；殘留的 31217 已處理，方法是以確切 pid 結束它的 f8desk 子程序 31231，之後 31217 就退出了，常駐程式照常活著 | `.bak-20260926-v8fix2` |
| 2 | `f8-adb-port` 只靠 mDNS | **這支手機上 mDNS 查不到 `_adb-tls-connect`**（原版在 adbd 開著時也逾時 6 s），所以要用 ADB 的選項全部失敗；另外 5037 伺服器一直在重連失效的舊埠 39589 | 重寫：① 先試上次成功的埠（`~/.cache/f8-adb-port.last`）；② 平行掃描 Wi-Fi 位址的 30000–50000；③ 候選埠必須在本機也連得上、不是 TCP 自己連到自己，而且**送 adb CNXN 要收到 adb 封包**（STLS／CNXN／AUTH）；④ mDNS 當備援。實測找到 33063（STLS）：第一次約 2.4 s，有快取時約 0.08 s。無線偵錯關著時正確回報找不到（44319、42935 雖然開著，但都不是 adbd） | `.bak-20260926-v8fix2`（原版）、`.bak-20260926-v8fix3`（fix2 版） |
| 3 | f8-mouse-external 寫死 `127.0.0.1:37985` | 埠一變就失敗 | 改用 f8-adb-port，connect 時的前綴跟其他工具一樣 | `.bak-20260926-v8fix2` |
| 4 | f8-mouse-external 的描述碼抓法 `/Descriptor:/` | Android 16 的 InputReader 區塊沒有單獨的 Descriptor 行，結果比對到 `AssociatedDisplayUniqueIdByDescriptor: <none>`，送出去的綁定是 `<none>` | 改成從 Event Hub 區塊，取第一個 `CURSOR`＋`EXTERNAL` 裝置的 Descriptor（不再綁死 Logitech M350）。另外確認這個 build 的 transaction 42 = `addUniqueIdAssociationByDescriptor`（用 baksmali 反組譯 `/system/framework/framework.jar` 的 `IInputManager$Stub`） | `.bak-20260926-v8fix4` |
| 5 | f8-fullscreen connect 之後沒有 `-s` | 同時連著多個 adb 裝置時整串失敗，而且失敗時沒有任何提示 | 加上 `-s 127.0.0.1:$PORT`，每種失敗都會跳 toast 說明原因 | `.bak-20260926-v8fix2` |

## 實測結果（外接 HDMI 螢幕，displayId 19，1920×1080，Logitech M350）
- **外接 Linux 桌面**（f8desk-external）：Termux:X11 從螢幕 0 移到螢幕 19；X `:1` 沒有中斷，裡面的程式（包括 Claude）都還在。
- **滑鼠綁到外接螢幕**：修正 4 之前送的是 `<none>`，綁定前後 Pointer Display ID 都是 0（失敗）；修正之後 `AssociatedDisplayUniqueIdByDescriptor=local:4613343222092698389`、Pointer Display ID 變成 19，小工具也回報「外接滑鼠已套用」。
- **外接 App 改成滿版**：Termux:X11 在螢幕 19 上重開成滿版；X `:1` 沒有中斷；滑鼠綁定還在。
- **外接 App**：使用者自己點選測試，**成功開到外接螢幕**（走日常的 5037 通道，所以 5037 那條也驗證到了）。
- **F8 工作站、F8 設定**：靜態檢查沒問題。
- 使用者換了另一台螢幕之後，Android 看到的仍是同一個「HDMI 螢幕」（編號 19、uniqueId 一樣，推測是跟著轉接頭），1920×1080；滑鼠綁定仍然有效。

## 注意
- Linux 桌面在外接螢幕上的 X root 是 1920×980：Android 桌面模式的工作列佔掉 100 px。「滿版」是 windowingMode fullscreen，不會隱藏系統列。
- 換了轉接頭或改用 USB-C 直連，uniqueId 可能會變。滑鼠要是綁在已經不存在的螢幕上，重新點一次「滑鼠綁到外接螢幕」就好。
- 自動分流之後（沒有 `--kill-on-exit`），用「關閉桌面」時，終端機裡 nohup 或放到背景的工作不會跟著結束（v7 時會）。

## 新增：「F8 自動」（使用者要求，現有三個小工具保留不動）
- 捷徑是 `~/.shortcuts/F8 自動`，主程式是 `$PREFIX/bin/f8-auto`。
- 流程：`timeout 4 f8-adb-port` → 找不到就跳 toast「沒有無線偵錯，桌面開在手機上」，然後執行 `f8desk`。
  找到了就讀 `dumpsys display`：沒有外接螢幕 → `f8desk`；有 → toast，然後執行 `f8desk-external`。
  同時在背景等 Termux:X11 出現在外接螢幕上（最多 20 s）；Event Hub 裡如果有外接游標裝置，就再跑 `f8-mouse-external`。
- 假工具測四條路：A 逾時 → 手機＋toast；B 沒有外接螢幕 → 手機；C 有外接螢幕和滑鼠 → 外接＋綁滑鼠（約 3.5 s 後）；D 有外接螢幕、沒有滑鼠 → 外接、不綁。全部正確。
- 實測（5038）：rc 0、6 s；Termux:X11 在螢幕 19（t533）；`Pointer Display ID: 19`（`test-auto.out`）。
