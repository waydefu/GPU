# F8 Claude Desktop 更新閃退：完整調查、隔離修復與驗收報告

更新時間：2026-11-12（Asia/Taipei；已補入 08:30 正式部署與日常開窗驗證）

## 1. 結論與完成邊界

**根因已定位；隔離修復、主代理獨立驗收、正式替換及日常 Claude 開窗均已通過。**

Claude Desktop 從 3.6556.2 更新為 5.1231.2 後，在開窗前觸發 SIGTRAP。不是登入資料損壞，也不是必要啟動旗標遺失。直接觸發原因是新版共享記憶體流程需要真正唯讀的檔案描述符，而 Android 的 memfd reopen 限制與本機 PRoot 的 openat→dup 相容補丁相互衝突。

Terra（gpt-5.6-terra）完成隔離修復；主代理審查最終 diff，親自從 Termux host 重跑原版/候選版回歸測試，並在獨立 Xvfb :98、乾淨資料目錄中實際啟動 Claude。

**調查與隔離驗收期間未更換正式 tracer；使用者後續明確要求替換後，已備份原版並原子替換 out8/bin/proot-fast8。** 日常 Claude 已沿用原資料目錄成功開窗；未改 /usr/local/bin、桌面啟動鏈、登入資料或 X server / APK / GPU Gate A。正式部署詳第 9 節。

## 2. 本機權威與環境

本機文件優先於一般 Linux 或上游安裝指南：

- `/root/Desktop/F8-工作站維護紀錄.md`
- `/root/.claude/skills/claude-desktop-update/SKILL.md`
- `/root/projects/GPU加速/AGENTS.md`
- `/root/projects/GPU加速/F8-LOCAL-ENV.md`
- `/root/projects/GPU加速/HANDOFF-NEXT-SESSION-20260926-AUTOSHARD.md`
- `/root/projects/GPU加速/HANDOFF-NEXT-SESSION-20260924-PROOT.md`
- `/root/projects/GPU加速/ADB-CONNECT.md`

| 項目 | 本次證據 |
|---|---|
| 裝置 | 型號代碼 25102PCBEG，device=myron，ARM64 |
| 執行環境 | Termux + Ubuntu 24.04.4 PRoot + XFCE；日常有自訂 proot-fast8 與 f8-shard 自動分流 |
| 舊版 Desktop | 維護紀錄及 dpkg.log 記錄 3.6556.2 曾正常使用 |
| 更新 | dpkg.log：2026-11-11 22:01:51，3.6556.2 → 5.1231.2 |
| 新版 runtime | `/usr/lib/claude-desktop/version`：Electron 45.2.1 |
| 新版內嵌 Claude Code | app.asar manifest：2.1.321；舊版紀錄為 2.1.284 |
| 正式 tracer | `/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8` |
| 對應來源 | `/data/data/com.termux/files/home/build/proot-fast/proot-5.1.107.92-v8/` |
| ADB | native binary、isolated 5038；每次核對裝置身份。端點會變，不可把本次值當作未來 authority |
| 桌面旗標 | 桌面與使用者選單的 password-store / no-sandbox / disable-gpu / disable-dev-shm-usage / ozone-platform=x11 均存在 |

沒有直接運行舊版 Desktop 做前後差異對照，不能宣稱已證明舊版每一步的 syscall 路徑。

## 3. 根因鏈與可重現證據

1. Chromium `CreateAnonymousRegion()` 建立名為 `shared-memory-region` 的 memfd（匿名記憶體檔案），再以 `open("/proc/self/fd/N", O_RDONLY | O_CLOEXEC)` 取得真正唯讀的描述符。
2. 不經 PRoot 的原生 Android/Termux 測試，對 memfd 使用 `/proc/self/fd/N`、`/proc/thread-self/fd/N`、`/dev/fd/N` 重新開成唯讀均回 EACCES；一般具名稱檔案則可正常重新開成唯讀。故不能再把 EACCES 全部歸因於巢狀 tracing。
3. 本機 `fake_id0.c` 的相容補丁，對 fake root 的 `/proc/<pid>/fd/N` openat 原本幾乎一律改成 dup。dup 保留來源的 O_RDWR，沒有真的產生 O_RDONLY，亦遺失 O_CLOEXEC。
4. GDB 在權限檢查捕捉到 FD 67：`actual_flags=0x20002`、`expected_access=0`、目標 `/memfd:shared-memory-region (deleted)`；繼續即在 `0x3007f09d0c` 的 `brk #0` 觸發 SIGTRAP。
5. 原版與候選前的合成對照：普通 pathname 唯讀開啟會正確拒絕 write；同一檔案與 memfd 經 proc-fd reopen 卻保留可寫。這是描述符語意問題，不是應該被跳過的 Claude 安全檢查。

官方參照：`https://raw.githubusercontent.com/chromium/chromium/main/base/memory/platform_shared_memory_region_posix.cc`。此為取得時的 main 來源，不當作精確版本 release tag；實際崩潰二進位的來源路徑、fcntl 分支、參數及斷點另由本機 GDB 交叉核對。

## 4. 隔離修復內容

最終 patch：`terra-claude-host-fix.patch`。

### src/syscall/enter.c

- memfd 名稱緩衝區由 20 bytes 改為 64 bytes，避免長度恰好 20 的 `shared-memory-region` 在含結尾 NUL 的讀取中被截斷。
- 僅限 Android/Bionic 且名稱完全等於 `shared-memory-region`，回報 ENOSYS，讓 Chromium 使用其既有、安全的具名稱暫存檔備援實作。
- 不偽造唯讀旗標、不跳過 brk、不改 Chromium 的權限檢查。其他 memfd 不偽裝成功。

### src/extension/fake_id0/fake_id0.c

- 一般 proc-fd reopen 保留真實 openat 語意。
- 只針對 stdin/stdout/stderr 的常規開啟方式保留窄相容例外，使用 fcntl(F_DUPFD) / fcntl(F_DUPFD_CLOEXEC)，保留來源的真實 access mode，正確處理 close-on-exec。
- 不把可讀寫描述符宣稱為唯讀。反常重接 stdio 的完整相容性尚未覆蓋，列為正式部署風險。

### tests/test-terra-proc-fd-reopen.c

回歸測試包含一般路徑、proc-fd、raw memfd 真實 EACCES、Chromium named-file fallback、O_PATH、stdio、FD_CLOEXEC 與 fork/exec 後關閉。

## 5. 真實驗證結果

### Terra 建置與測試

- 使用既有 Android clang 與 libandroid-shmem 編譯隔離 tracer，exit 0；未新增依賴。
- patch 在新隔離來源中套用並逐檔比對，exit 0。
- host RED：原版 exit 1；host GREEN：候選 exit 0。
- 私有 Xvfb :97、乾淨 HOME/XDG/user-data-dir 實測 Claude 開窗，exit 0；核對 app 的 TracerPid 對應候選 binary；已清理測試程序。

### 主代理獨立驗收

原版與候選使用相同合成測試程式與 rootfs，直接由 ADB run-as com.termux 在 Termux host 啟動。

- **原版 exit 1**：重現 proc-fd 得到 O_RDWR、raw memfd 語意與 O_CLOEXEC 不符。
- **候選 exit 0**：stdio、一般 pathname、proc-fd、raw memfd 拒絕、Chromium fallback、O_PATH 全部通過；唯讀 FD 的 write 必須 EBADF，fork/exec 之後 FD 必須已關閉。
- 完整可重跑命令及 exit code：`main-review-results.json`。
- 主代理視窗測試使用獨立 :98 與私有 /tmp bind，不與 Stable :1 共用測試 socket 目錄。

主代理視窗實測輸出：

```text
PASS app_pid=9791 tracer_pid=9774
tracer_exe=/root/.hermes/cache/scratch/terra-claude-fix/proot-5.1.107.92-v8-terra-claude-fix/src/proot
window=2097154
Claude
exit=0
```

測試要求取得該 app PID 擁有的可見視窗，並再保持存活 5 秒；不是只數任意視窗。結束後確認 app PID 9791、tracer PID 9774 均不存在。這些 PID 只是本次證據，不能再次拿來 kill。

主代理測試腳本第一次因 guest PATH 未設定找不到 Xvfb、第二次因 Xvfb lock 建立權限失敗；分別修正驗收腳本的 guest PATH、改用私有 /tmp 與 -nolock 後成功。這些是測試環境錯誤，不隱藏，也不算作 Claude 修補成功的證據。

## 6. 最終雜湊

| 產物 | SHA-256 |
|---|---|
| 原版備份 proot-fast8.original | `10121cc433473db826c75d84a703d989114cb3d2eff4baf7cfd0ebdc912bdbe5` |
| 已正式安裝版本／最終候選 | `e401eb6caa126f1e36dbb66d23c55735082af3688dfb1752972dda0146f8267c` |

第一輪候選的舊雜湊不是最終版本；部署只可比對本節及證據包 manifest。

## 7. 未完成、風險與正式部署邊界

- **已正式部署**：使用者後續批准後，已原子替換正式 binary 並實測日常 Claude 開窗；其他原已運行的 tracer 未重啟，仍可能使用舊映像。
- 尚未操作原帳號登入、既有 Code sessions、MCP 或長時間日常穩定性；已測乾淨隔離啟動與沿用日常資料目錄開窗，但未讀取認證或執行帳號操作。
- 未跑完整 PRoot make check：既有 ARM64 測試 rootfs 缺 -m32 工具鏈。不可宣稱完整套件測試全綠，亦未修改 CI 門檻。
- stdio 的反常 access mode 重接情境尚未覆蓋；一般 proc-fd 補丁收窄可能讓其他應用重新遇到原本被 dup 掩蓋的 Android 存取錯誤。
- Chromium 的精確 memfd 名稱將來若改變需重新驗證，不能無限制拒絕所有 memfd。
- 正式安裝屬於日常核心 tracer 的行為變更；本次已獲使用者獨立批准，保留原 binary 與雜湊並原子替換，沒有安排整桌面重啟。未來仍不得直接覆寫執行中的 binary。
- 不做任何關機、手機重啟、Stable APK 安裝、GPU Gate 重跑。

## 8. 報告保存與雲端狀態

- 本報告保存於 GPU 專案 evidence；桌面提供相同內容副本。
- 桌面 `F8-工作站維護紀錄.md` 補入本次摘要、狀態邊界與踩坑紀錄；本次詳細踩坑另存同目錄的 `CLAUDE-DESKTOP-MEMFD-20261112-PITFALLS.md`。
- 證據包只包含經選擇的合成測試、patch、候選 binary、校驗與報告；不包含 auth、.env、keyring、使用者 profile、聊天紀錄、worker transcript 或真實客戶資料。
- Google Drive 既有授權檢查回報 `invalid_grant` / `TOKEN_REVOKED`，目前尚未上傳。需使用者重新授權，不能宣稱雲端已完成；不自行讀取、更換或撤銷憑證。

Documentation impact：Updated。結案分類：**調查完成／隔離修復驗收通過／正式部署及日常開窗通過／雲端同步待授權**。

## 9. 使用者批准後的正式部署（2026-11-12 08:30）

- 已用使用者提供的新端點重新驗證 device=myron。
- 正式路徑：`/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8`。
- 持久備份：`/data/data/com.termux/files/home/build/proot-fast/releases/claude-memfd-20261112-083006/proot-fast8.original`；同目錄另存候選與最終 patch。
- 替換前候選回歸 exit 0，正式 binary 原子替換及雜湊驗證 exit 0，從正式路徑再跑回歸 exit 0。
- 日常 Claude（非隔離空白 profile）成功開窗：app PID 26603、tracer PID 26601、window 56623107；X11 `_NET_WM_PID=26603`，WM_CLASS 為 Claude，尺寸 1200×2205。
- `/proc/26601/exe` 和正式路徑的 SHA-256 都等於最終候選 `e401eb6c…67c`，證明正在執行的是修正版。
- 未重啟桌面。原版仍有持久備份；已運行的其他 tracer 不會自動換掉映像。未來從原來源重建 out8 前須先套用保存的 patch，否則會重建回未修復版本。
- 不宣稱登入、聊天、Code/MCP 或長期穩定性已驗證；未讀取日常認證資料。

完整部署與回退注意事項：`CLAUDE-DESKTOP-MEMFD-20261112-DEPLOYMENT.md`；正式日誌：`production-deploy.log`。Google Drive 授權仍失效，未宣稱雲端已同步。
