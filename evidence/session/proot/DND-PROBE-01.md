# DND-PROBE-01 — 拖曳中文路徑會關掉視窗？（2026-09-25）

使用者回報：中文路徑拖進視窗必定讓視窗／App 關閉（今天尚未操作過，Claude main.log 無當機紀錄，Crashpad 關閉）。
線索：日常桌面 `LANG` 未設（proot-distro login 不讀 `/etc/default/locale` 的 `LANG=C.UTF-8`）→ 整個桌面是 C locale。

## 實驗（`tests/proot/dnd_probe.sh`＋`dnd_source.py`，fork `0341c54`；cell `proot/dnd-probe-02`，`dnd-probe-01` 是 host_resources 擋下的未消耗格）
在實驗版 X `:3`（日常 `:1` 不動）以 GTK 拖曳來源（`text/uri-list`，同檔案管理員）＋xdotool 拖到目標，等 8 s 看目標程式與視窗是否還在。
| 目標 | LANG 未設＋ascii | LANG 未設＋中文 | C.UTF-8＋ascii | C.UTF-8＋中文 |
|---|---|---|---|---|
| xfce4-terminal（GTK） | 存活 | 存活 | 存活 | 存活 |
| Cursor（Electron，全新設定檔） | **無效**（抓到 Cursor 的「Error」對話框，sent=0） | 存活（Agents 視窗接收，sent=1） | 存活 | 存活 |
runner `CMD_CAPTURED` rc=0；56 次 TERM、0 KILL；殘留 0；Stable 前後相同。

## 結論
**未重現**。GTK 與 Electron（Cursor）在 C locale 下接收中文路徑的拖放都不會關閉。問題可能取決於特定來源（Thunar／桌面圖示）或特定目標（例如 Claude Desktop 的輸入框），需向使用者確認後再測。
