# 治理檢查與證據保護

這份文件補充 2026-11-26 的[稽核紀錄](../evidence/session/proot/GOVERNANCE-AUDIT-FIX-20261126.md)。

## CI 與凍結證據

- PR 使用事件的 base SHA 和 checkout 的合併結果。推送到 `main` 時，使用事件的前一個 SHA 和實際 checkout 的提交。資料缺失或歷史無法比對時，檢查失敗。
- 已發布的 `evidence/` 檔案採僅新增原則，禁止修改、刪除或改名。已關閉的 Gate A、GL/VK、P2 與其他登記目錄也拒絕新增檔案。凍結根目錄和掃描範圍由 [治理程式](../scripts/check-governance.py) 定義。舊紀錄的後續說明寫在 `docs/`。
- Push 檢查在 GitHub 接受更新後執行。倉庫規則需要另行設定，才能在提交進入 `main` 前強制執行。
- 現役入口、腳本、工作流及本文件會檢查含 port 的 RFC 1918 私有端點、IPv4 link-local、共享位址、IPv6 ULA 或 link-local 位址，以及常見憑證與私鑰格式。CI 只回報命中位置與類別。掃描此範圍可發現已知格式，仍有格式與範圍限制。
- Workflow 的 checkout 固定至上游 v4.4.0 的完整 commit SHA。 [上游版本](https://github.com/actions/checkout/releases/tag/v4.4.0)

## 日誌壓縮

`scripts/zlogs-safe.sh <目錄> <manifest.tsv>` 預設保留來源。它比對來源的檔案身分、時間、大小及雜湊，驗證解壓內容，並在清理之前提交 manifest。失敗會回報並保留來源。若封存已發布但 manifest 提交失敗，後續執行會回報未登記的封存，保留兩份檔案供人工核對。

只對已停止寫入和輪替的來源使用 `--remove-source`。它適用於尚未封存的檔案，並在刪除前再次檢查來源身分。無法確認寫入者已停止時，用預設模式。若需要查看候選清單，可用 `--dry-run`。

## ADB 與 Stable

`run_tiny_pixmap.py` 使用 Termux native ADB 並固定 `-H 127.0.0.1 -P 5038`。可指定 `ADB_SERIAL` 或 `ANDROID_SERIAL`，也可從該 lane 選擇唯一的線上網路裝置。所有裝置操作明確指定 serial，並先確認目標為 `myron`。Stable 鎖檔、server、XFCE session、window manager 和 X1 socket 以執行當下的身分比對。無法確認 Stable 或實驗啟動失敗時停止測試。
