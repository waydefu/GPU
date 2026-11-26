# fast9+09c 效能基準凍結（2026-11-27）

## 性質聲明

本文件是基準登錄，不是新實驗。不重跑既有量測，也不重判既有判決。所有數值都從來源文件逐字抄錄，並標註 `path:line`。來源沒有記載的欄位一律寫 `null`，不以 `0` 代替。

## 身分

| 項目 | 內容 | 來源 |
| --- | --- | --- |
| 版本 | `5.1.107.92-fast9` | `/root/projects/GPU加速/evidence/session/proot/FAST9-09C-LIVE-QUALIFICATION-20261127.md:7` |
| 補丁 | `01..09 + 09b + 09c` | 同上 `:7` |
| SHA256 | `4a6bc67723d9517771ea602e61caa98a4ac7cb7cf75f932d85fa1a5038ae7660` | 同上 `:7`；`/root/projects/GPU加速/HANDOFF.md:17` |
| 正式來源 commit | `d5ddc730156d5f82a81e8a56f9819a2641d789a5`（waydefu/GPU PR #42 merge commit，路徑 `core-src/f8-proot-fast/`） | 同上 `:5`；`HANDOFF.md:9` |
| 本機快照 commit | `23f9bdc`（worktree `src/f8-proot-fast-fast9-fixes`） | 同上 `:5`（來源文件聲稱；本次未獨立核對 worktree HEAD） |
| 實機路徑（live） | `/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8` | 本次 Step 2 實測 hash 符合 |
| 凍結副本路徑 | `/data/data/com.termux/files/home/build/proot-fast/baselines/fast9-09c-20261127/`（內含 `out8/`、`sha256sums.txt`、`README.txt`） | 本次 Step 4 建立 |
| 凍結副本清單 | `/data/data/com.termux/files/home/build/proot-fast/baselines/fast9-09c-20261127/sha256sums.txt`（5 個檔案，與 live out8 清單逐行相同） | 本次 Step 4 |
| 原始證據目錄 | `/data/data/com.termux/files/home/build/proot-fast9-09c-20261127.yXdNteSr` | `FAST9-09C-LIVE-QUALIFICATION-20261127.md:45` |

## 基準數值表

表中「09c」為本基準值；「09b」只作對照參考，不屬於本基準。

### A. 30 分鐘單一 workload tracer 壓測（09c）

| 指標 | 數值 | 來源 |
| --- | --- | --- |
| 壓測時長（整段） | 1805.76 秒 | `FAST9-09C-LIVE-QUALIFICATION-20261127.md:22` |
| 批次通過 | 514/514 | 同上 `:22` |
| Vulkan 通過 | 7/7 | 同上 `:22` |
| 最大活孤兒程序數 | 0 | 同上 `:23` |
| shard daemon 實例數 | 單一實例 | 同上 `:23` |
| shard daemon FD 數 | 7 | 同上 `:23` |
| Ubuntu core 驗證 | 4/4 | 同上 `:23` |
| 正式部署檔案雜湊 | 3/3 | 同上 `:23` |
| 批次牆鐘時間中位數 | 2489.54 ms | 同上 `:24` |
| 批次牆鐘時間 p95 | 2574.09 ms | 同上 `:24` |
| Chromium rAF p95 中位數 | 16.7 ms | 同上 `:24` |
| tracer CPU（壓測段） | null — 來源未記載 | — |

### B. 09b 對 09c 同機對照（每版 10 批）

| 指標 | 09b（對照） | 09c（基準） | 變化（來源原文） | 來源 |
| --- | ---: | ---: | ---: | --- |
| 批次時間中位數 | 2490.57 ms | 2495.91 ms | +0.21% | `FAST9-09C-LIVE-QUALIFICATION-20261127.md:32` |
| tracer CPU 中位數 | 860 ms | 860 ms | +0.00% | 同上 `:33` |
| 尖峰 PSS 中位數 | 291.0 MB | 282.6 MB | -2.89% | 同上 `:34` |
| Chromium 啟動中位數 | 173.59 ms | 179.78 ms | +3.57% | 同上 `:35` |
| rAF p95 中位數 | 16.7 ms | 16.7 ms | +0.00% | 同上 `:36` |
| 點擊 p95 中位數 | 79.22 ms | 68.66 ms | -13.33% | 同上 `:37` |

來源 `:39` 明確說明：樣本顯示整體時間及 tracer CPU 接近；首區塊溫度高於其餘區塊，啟動及點擊差異需更多樣本確認。因此本表的啟動與點擊數值不應被視為已定案。

`HANDOFF.md:20` 也記載同一組對照（2,490.57 → 2,495.91 ms，+0.21%；tracer CPU 860 ms；rAF p95 16.7 ms），與上表一致。

## 量測方法

**A. 壓測**：來源 `FAST9-09C-LIVE-QUALIFICATION-20261127.md:22` 記載：經 `f8-shard` 綁定正式版本，在單一獨立 workload tracer 上執行 Chromium、Electron Node 模式、Python、Git 與 Vulkan 負載；整段 1805.76 秒，514/514 批通過，Vulkan 7/7。
- 「批」的定義：null — 來源未記載。
- 批次牆鐘時間與 Chromium rAF 的量測工具：null — 來源未記載。

**B. 同機對照**：來源 `FAST9-09C-LIVE-QUALIFICATION-20261127.md:28` 記載：同機、相同 workload，以 09b → 09c → 09c → 09b 交錯執行，另有每區塊一次暖身，每版取 10 批。
- 量測工具名稱（計時、CPU、PSS、點擊延遲的工具）：null — 來源未記載。
- tracer CPU 的計算方式（單位 ms 是何種 CPU 時間）：null — 來源未記載。

## 後續比較規則

以下三條為本次凍結時訂定的程序規則（非來源文件內容），不另加數值門檻：

1. 任何候選版本與本基準比較時，必須在同一台機器、同一負載定義下取得數據。
2. 比較門檻必須在看到受判資料前，另立 FREEZE 文件凍結；本文件不預設門檻。
3. 本基準數值與凍結副本不得改寫；若量測工具日後修正，另立新文件說明，不回改本文件。

## 回退

- 上一版 fast9+09b 備份：`/data/data/com.termux/files/home/build/proot-fast/backups/out8-previous-20261127-004529.KNBzD8mu`，雜湊 5/5（`FAST9-09C-LIVE-QUALIFICATION-20261127.md:7`；`HANDOFF.md:19`）。本次凍結並未複製這份備份。
- 既有 `LATEST_FAST8_BACKUP` 仍指向 fast8，雜湊 4/4（`FAST9-09C-LIVE-QUALIFICATION-20261127.md:7`）。
- 手動回退演練：逐檔比對與套件探針通過（同上 `:13`）。
- 操作降級開關：`F8_NO_SHARD=1` 略過分流；`PROOT_STAT_AT_ENTER=0` 停用 enter-time stat（`HANDOFF.md:22`）。

## 驗證紀錄（本次 Step 2–4 實際執行）

1. `sha256sum <live>/bin/proot-fast8` 輸出 `4a6bc67723d9517771ea602e61caa98a4ac7cb7cf75f932d85fa1a5038ae7660`，與預期一致。
2. `du -sh <live>/out8/` 輸出 `314K`，遠低於 500M 門檻。
3. `ls -laR <live>/out8/` 結果：`auto/proot-fast8` 743 B；`bin/proot-fast8` 279464 B；`libexec/loader` 18232 B；`libexec/loader32` 6212 B；`deployed.sha256` 246 B。第一次執行的輸出被 RTK 過濾器縮減、缺少檔名，因此改用 `rtk bypass ls -laR` 重跑取得完整清單。
4. 目標路徑檢查：`NOT_EXISTS`，允許建立。
5. `mkdir -p` 後 `cp -a <live>/out8/. <target>/out8/` 輸出 `COPY_OK`。
6. 兩棵樹各 5 個 regular file 的 sha256 清單（`find . -type f | sort | sha256sum`）經 `diff` 輸出 `IDENTICAL`。凍結副本的 `bin/proot-fast8` 雜湊同為 `4a6bc677…7660`。
7. 寫入 `README.txt` 後執行 `chmod -R a-w <target>`，指令回傳 0，但實際未生效（見下方 UNKNOWN/RISK）。
8. 事後以 `sha256sum -c sha256sums.txt` 在凍結副本內逐檔驗證，5/5 `OK`。
9. 過程中曾在凍結副本的 `out8/` 內以 `touch` 建立 `_wtest` 作寫入測試後立即 `rm` 刪除；事後重新比對清單仍 `TREE_HASHES_IDENTICAL`。`out8/` 目錄的 mtime 因此變為 `Nov 27 01:50`。實機 live out8 未被寫入。

## UNKNOWN / RISK

- **唯讀保護未生效**：`chmod -R a-w` 回傳 0，但 `stat` 顯示權限位元未改變；在 scratchpad 的獨立探針檔案上同樣無效，判定為此 bind mount 的檔案系統不接受 chmod。另外本次以 uid 0 執行，即使權限位元生效，root 仍可寫入。因此目前「凍結」只能由 `sha256sums.txt` 的雜湊清單保證，不能靠權限保證。是否要改用其他機制（例如 `chattr +i`），需要使用者決定；本次未自行嘗試。
- 來源 `:43` 記載：桌面工作階段切換後，原 `termux-bg-run` 路徑未收到 TermuxService 執行回報，原因未確認。這與本基準無直接關係，但屬未解問題。
- 對照樣本只有 10 批，且首區塊溫度偏高（`:39`）。啟動與點擊的差異不足以作為定論。
- 本次未獨立核對本機 worktree `src/f8-proot-fast-fast9-fixes` 的 HEAD 是否為 `23f9bdc`，也未核對 GitHub PR #42 的狀態；上述內容皆來自來源文件。
- 凍結副本包含 `out8/` 全部 5 個檔案（含 `auto/proot-fast8` 包裝程式與 `libexec/loader*`），不只是 binary；`deployed.sha256` 的權限為 600，已照原樣複製。
