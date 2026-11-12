# F8 踩坑記錄：Claude Desktop 更新後 SIGTRAP

日期：2026-11-12。最新狀態：隔離修復已驗收；使用者批准後已正式部署，日常 Claude 開窗通過。部署明細見 `CLAUDE-DESKTOP-MEMFD-20261112-DEPLOYMENT.md`。

完整報告：`CLAUDE-DESKTOP-MEMFD-20261112-REPORT.md`；桌面亦有同內容副本。

## 先看本機手冊，不先套一般環境假設

- 使用者提到桌面說明書時，先查 `xdg-user-dir DESKTOP`，讀 `F8-工作站維護紀錄.md`，沿用其列出的本機更新 skill 與 GPU 專案文件。
- 這台有 proot-fast8、f8-shard、自訂 syscall 補丁；同樣參數的 shell 啟動不一定等同桌面實際程序鏈。
- PRoot 下瞬間看到 tracing stop 不代表程序被除錯器永久凍結；必須查 TracerPid 與 tracer executable，不把正常 tracing 誤判成根因。

## 更新時間只是相關性，不能省略根因驗證

- 本次 dpkg.log 證實 3.6556.2 → 5.1231.2 後開始閃退；旗標仍完整。
- 不把 D-Bus、Netlink、udev 的警告直接當成致命錯誤；此次真正終止是共享記憶體 FD 的 access mode 不符。
- 不要先下載大包除錯符號或舊版。已裝的 GDB 即使面對 stripped binary，仍能看分支、fcntl、字串路徑與參數。
- ARM64 PAC 可能讓一般 backtrace 提前終止；可在只讀條件下走 frame pointer chain 並處理 PAC 位元，不可把 data pointer 當 return address。

## open(proc-fd) 不是 dup

- `open('/proc/self/fd/N', O_RDONLY | O_CLOEXEC)` 要求新開啟描述，不能一律改成 dup。
- dup 保留 O_RDWR 並遺失 O_CLOEXEC；禁止只修改 F_GETFL 回報成 O_RDONLY，必須真的 write→EBADF、exec 後 FD 關閉。
- 本機 Android 原生 memfd 唯讀 reopen 回 EACCES；修掉 PRoot 的 dup 之後仍會失敗，這是第二層限制，不能全怪巢狀 PRoot。
- 此次僅針對 Chromium 精確名稱 `shared-memory-region` 令 memfd 回 ENOSYS，使用上游已存在的具名稱檔案 fallback；原生唯讀檢查仍完整保留。
- 20 bytes 的名稱緩衝區不足以容納恰好 20 字元的名稱加 NUL，會使精確比對失效。
- 保留 stdio 窄相容性時，用 F_DUPFD_CLOEXEC 正確處理 close-on-exec；不要擴張到所有 FD。

## 真正外層與測試環境

- 最終必須由 Termux host 跑候選；在未修復 PRoot 裡啟動另一個 PRoot 不能證明外層不再干擾。
- RunCommandService 的 invalid source 必須當成授權邊界；本次取得使用者新提供的 ADB endpoint 後，依本機 SOP 使用已授權 run-as com.termux，未修改 Android 政策。
- ADB 使用 native binary、isolated 5038、精確 serial，先核對 device=myron；IP/port 每次會變。不要猜或掃連線埠，不碰 5037 舊服務。
- 主代理一次較早的裸 adb 查詢意外啟動了 5037；後續改為明確 isolated 5038，沒有為清理而 kill 既有服務。此錯誤保留紀錄，不作標準流程。
- 私有 Xvfb 使用獨立顯示器與私有 /tmp bind；PRoot 下建立 X lock 可能失敗，已驗證用 -nolock 且不接網路，不能去動日常 :1 的 socket 或 lock。
- env -i 進入 guest 時要設定 guest PATH，否則 Termux PATH 找不到 Ubuntu Xvfb；不讀取或複製 /proc/*/environ。

## 保留結果與完成宣稱

- 先紅（原版 exit 1）、再綠（候選 exit 0），主代理獨立重跑，另確認 Claude app-owned 可見視窗和候選 TracerPid；不是只看程序還在。
- 不把 raw memfd 的 EACCES skip 掉；測試需同時驗證真實拒絕與安全 fallback。
- 隔離成功、正式部署、原帳號驗證、完整套件測試、雲端同步是不同狀態，必須分開說。
- 目前完整 make check 未跑；正式 tracer 已在使用者獨立批准後原子替換並保留原版備份。Google Drive 授權已失效，未上傳，不得宣稱已備份雲端。
- 設定備份、桌面捷徑備份、完整舊版套件、未完成下載與仍在跑的 deleted executable 是不同東西，不能互當回退檔。
- 使用者要求停止慢速下載就停止該 job；不重啟另一個同等大下載。只清自己的暫存，不動既有備份。

## 後續

本次正式部署已獲批准並備份原版，以原子替換而非直接覆寫執行中 binary。未來來源重建前必須套用保存的 patch；其他已運行 tracer 的舊映像不會自動更新。更新後若換名稱或 runtime 需重新驗證，不能把此次 patch 當永久通用解。
