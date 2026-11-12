# Claude Desktop 正式套用與日常開窗紀錄

日期：2026-11-12。使用者明確要求「換啊不然怎開」，批准正式替換已驗收候選；當次提供的新 ADB endpoint 為 192.168.1.100:45617。此為歷史連線證據，未來必須重新確認端點與裝置身份。

## 正式替換

裝置身份重新確認：model=25102PCBEG、device=myron。native ADB isolated 5038。

正式路徑：
`/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8`

替換前原版 SHA-256：
`10121cc433473db826c75d84a703d989114cb3d2eff4baf7cfd0ebdc912bdbe5`

替換後修正版 SHA-256：
`e401eb6caa126f1e36dbb66d23c55735082af3688dfb1752972dda0146f8267c`

持久備份與 patch：
`/data/data/com.termux/files/home/build/proot-fast/releases/claude-memfd-20261112-083006/`

- `proot-fast8.original`：原版，雜湊核對一致。
- `proot-fast8.candidate`：驗收候選副本。
- `terra-claude-host-fix.patch`：對應來源變更。

先以候選再跑一次完整有界回歸測試，exit 0；複製原版至備份、驗證；在同目錄建立臨時 binary、chmod 755、核對候選雜湊後以 mv -T 原子替換；換後雜湊再次核對，並從正式路徑跑回歸測試，exit 0。整段 deployment script exit 0。

實際日誌：`production-deploy.log`。沒有直接覆寫執行中的 inode、沒有殺桌面或重啟手機。

## 日常 Claude 驗證

從 Termux host 用新正式 tracer 建立獨立的 PRoot 執行日常 Claude：

- 真實 HOME=/root，沿用現有日常資料目錄，沒有另設空白 user-data-dir。
- 沿用 password-store=gnome-libsecret、no-sandbox、disable-gpu、disable-dev-shm-usage、ozone-platform=x11。
- 接既有日常 DISPLAY=:1.0 與該 session bus；不修改 X server、APK 或 keyring。
- 不讀取、搬移、修改認證與登入資料；沒有執行聊天或 Code/MCP 工作驗證。

native Android ps 與 X11 交叉核對：

```
app pid = 26603
tracer pid = 26601
window id = 56623107
_NET_WM_PID = 26603
WM_CLASS = com.anthropic.claude / com.anthropic.Claude
window geometry = x=0 y=34 width=1200 height=2205
sha256(/proc/26601/exe) = e401eb6caa126f1e36dbb66d23c55735082af3688dfb1752972dda0146f8267c
sha256(out8/bin/proot-fast8) = e401eb6caa126f1e36dbb66d23c55735082af3688dfb1752972dda0146f8267c
```

因此不是只更新磁碟檔案或只顯示隔離視窗，日常資料目錄的 Claude 已真正由修正版 tracer 開窗。PID 只供本次紀錄，不可用作未來 kill 目標。

## 生效與回退注意

- 原子替換只影響之後啟動的新 tracer；已在跑的其他 PRoot 程序仍映射舊 inode。本次沒有重啟整個桌面，也不宣稱所有既有程序已換版。
- 本次正式變更是 binary 發布，沒有覆寫原本來源樹；未來重建 out8 前必須先套用並檢查 release 目錄的 patch，否則可能重建回未修復版本。
- 回退必須用持久備份先複製到同目錄臨時檔、驗證原版雜湊再原子替換；不直接 cp 覆蓋執行中的 binary。只有出現實際回歸且經確認才執行；本次沒有回退。
- 尚未驗證既有登入是否仍有效、聊天/Code/MCP 功能、長時間穩定性或完整 make check。不可把成功開窗等同上述全過。
- Google Drive 既有授權失效，雲端尚未上傳；不得把桌面更新當成雲端同步完成。
