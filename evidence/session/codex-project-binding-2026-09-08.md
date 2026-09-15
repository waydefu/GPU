# Codex 專案綁定紀錄 — 2026-09-08

## 範圍

本紀錄只描述本機 Codex 桌面端的 `GPU加速` 專案綁定，不描述 F8 GPU 功能結果。目標資料夾是 `/root/projects/GPU加速`；原本側欄專案使用的空佔位庫是 `/root/Documents/ChatGPT/GPU加速`。

## 故障證據

- 在故障歷程中，舊的專案資料庫根目錄曾是 `/root/Documents/ChatGPT/GPU加速`，而桌面端快取曾出現 `rootPaths: []`。這會讓側欄保留專案名稱，但沒有可用的資料夾根目錄。
- 2026-09-08 18:06 的快取備份 [`.codex-global-state.json.before-gpu-root-final-20260908-180600.bak`](/root/.codex/.codex-global-state.json.before-gpu-root-final-20260908-180600.bak) 已記錄目標新路徑；後續曾被清空。沒有證據能判定是哪個程序清掉它。
- Codex 0.153.1 的 `project-folder-picker` 警告記錄為 `Failed to stat project source`，錯誤是 `ENOENT: no such file or directory, stat ''`。這表示原生資料夾選擇器回傳空字串，未把選取的路徑交給專案更新流程。
- `/root/projects/GPU加速` 的 Markdown 檔案可讀；錯誤發生在資料夾選擇器回傳路徑之前，沒有證據顯示 `.md` 副檔名或檔案權限是原因。

## 最新驗證結果

- 專案資料庫 `project_roots`：`/root/projects/GPU加速`。
- 桌面端快取 `local-projects[GPU加速].rootPaths`：`["/root/projects/GPU加速"]`。
- `mcp__codex_app__list_projects`：`GPU加速` 的 `path` 為 `/root/projects/GPU加速`。
- 最新桌面程序及其 Codex app-server 已重新啟動；當次核對主程序 PID 為 27479，子程序 app-server PID 為 27698。
- `isGitRepository=false` 是目前上層整理資料夾的實際狀態；它不再阻止目前的專案根目錄綁定。

## 邊界與保留事項

- 沒有修改 F8 原始碼、Markdown 內容或三個 F8 子 repo。
- 先前為驗證而建立的臨時上層 `.git` metadata 已撤回。
- 「是哪個程序把路徑清空」仍無證據，不能定論。
- 原生檔案選擇器回傳空路徑的更底層原因（Electron/桌面入口或 PRoot/XDG portal）尚未單獨定位。
