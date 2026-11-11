# 交接（2026-09-27 00:10）— F6 複製結案＋F8 空間整理

上一份：`HANDOFF-NEXT-SESSION-20260926-AUTOSHARD.md`。那份頂端的 F6 段落和自動分流段落仍然有效，細節以那份為準。本檔只記「現在的狀態」和「還沒做的事」。

## 1. 下次一開始要做的事
- ~~驗證 `setsid -f`~~ **2026-09-27 10:37 冷啟動情境已驗證通過**（使用者重開 Termux；手機本身沒重開，Android 開機已約 64 小時）：
  - Termux `$PREFIX/tmp` 被清空（只剩本次的 job 目錄），常駐程式是這次新起的：`daemon.pid`=16178，比日常追蹤器晚 0.06 s 啟動。
  - 檢查 1 PASS：16178（`shard-daemon.sh`）`PPid: 1`。整台上已經沒有任何 cmdline 含 `f8desk` 的 bash（f8desk 的 bash 已 exec 成 proot-distro → proot）。
  - 檢查 2 PASS：只有 2 個 `proot-fast8`，都不是 0 tracee——日常 16170（父＝`com.termux` 19958，44 個 tracee：xfce4-session、dbus、copyq…）、分流 16971（父＝常駐程式 16178，24 個 tracee：claude-desktop×12、claude、serena、clangd…）。日常追蹤器唯一沒被追蹤的子程序是 termux-x11 `:1`（16214），這是正常結構。
  - `autoshard.log`：10:33:25 `shard electron /usr/lib/claude-desktop/claude-desktop`，之後都是正確的 skip（same_app／chromium_child／stdio_pipe）。
  - 工具：`/proc` 掃描腳本在`evidence/session/daily/list-proot-tracers.py`（讀 status 的 Name／PPid／TracerPid）。注意 PRoot 內 `/proc/uptime`（124 s）和 `/proc/stat` 的 btime（2023 年）都是 proot-distro 假造的，**不能拿來換算程序啟動時間**；只能用 stat 第 22 欄彼此相減。
- **10:41 使用者第二次重開 Termux**：追蹤器仍正常（日常 22450＋分流 23918，沒有 0 tracee）。**但發現常駐程式會累積**：`shard-daemon.sh` 有 3 個（31233、16178、22459）。
  - 原因：Termux 重開會清空 `$PREFIX/tmp`，flock 用的 lock 檔跟著被刪；`setsid -f` 起的舊常駐程式活下來，睡在已刪除的 fifo 上，新 f8desk 又起一個新的。
  - 已修（fix 3，10:44 部署、測試 `DAEMON_FIX3_TEST_PASS`，含必須變紅的對照組）：lock 被換掉 60 s 內自行退出。詳見 `evidence/session/proot/SHARD-DAEMON-FIX3-20260927.md`。
  - 10:53 使用者同意後，三個舊的都已依 pid 收掉。**我原本判斷錯了**：新常駐程式起不來，因為分流會繼承 fd 9（lock）和 fd 3（fifo），整棵 Claude Desktop 分流樹一直握著 lock。這是原本就有的 bug。
  - **fix 4**（開分流時 `3>&- 9>&-`）：10:55 部署，對照組 fix3 FAIL、fix4 PASS。移開被握住的 lock／fifo 之後，新常駐程式 **18265** 跑的是 fix4，分流走 `via=daemon`，活分流的 lock／fifo fd 數為 0。
  - 現役 `shard-daemon.sh` sha256 `8becae04…`，備份在 `.bak-20260927-fix3`（修正前）。fork 副本已同步，未 commit。
  - 10:58 F8 關開桌面（常駐程式已在跑）PASS；新 Claude Desktop 分流樹沒握 lock（fix 4 真機 PASS）。11:02 在現役常駐程式上模擬 Termux 清 tmp：26 s 內自行退出、新常駐程式 30328 接手（fix 3 真機 PASS）。還欠一次「真的 Termux 重開、tmp 被清」。數常駐程式時要比對 cmdline 開頭，否則會把執行檢查的 shell 自己算進去。
  - **F6（10.128.106.111:41707）11:04 已部署 fix 4**（備份 `.bak-20260927-fix3`），舊碼常駐程式 31785 已依 pid 收掉。11:07 F6 驗證 PASS（新常駐程式 7822 是 fix4、只有它握 lock）。細節見 `evidence/session/proot/SHARD-DAEMON-FIX3-20260927.md`。

- **Google Drive 文件資料夾 09-27 已更新**：6 份持續文件換成新版（原生彩色表格／色塊條），舊版在垃圾桶。新 ID 與匯入的坑見記憶 `drive-docs-refresh`。

## 2. 現在的狀態
### F8 空間整理（09-26 23:50 → 09-27 00:06，使用者要求）
- 起點：Android 統計的 Termux data 是 59.6G（diskstats 大約一天更新一次，只能當參考）。實測 rootfs 53.2G；`/data` 可用 52G。
- 終點：`/data` 可用 **67G**（477G 用 87%）。證據資料夾從 16.7G 降到 6.9G。

| 項目 | 釋放 | 做法 |
|---|---|---|
| GPU 證據 raw log 無損壓縮 | 約 9.8G | 275 個 `*.txt`／`*.log`（≥1 MiB、24 小時內沒改過）用 zstd -9 壓縮，10348 MiB → 312 MiB。**每個檔案都先解壓驗 sha256，相符才刪原檔**，0 個失敗。清單在 `evidence/COMPRESSED-LOGS-20260927.tsv`，說明在同目錄的 `.md`，工具存成同目錄的 `.zlogs.sh`。 |
| clinic 的 14 個 worktree | 約 2.8G | `git worktree remove`，沒有用 --force，branch 都保留。 |
| cursor-agent 舊版 4 個 | 約 2.1G | 09-02／09-08／09-10／09-15，另外清掉 159 個下載失敗留下的暫存資料夾；保留使用中的 2026.09.23-86fc751，`--version` 正常。 |
| 我的暫存 | 約 0.7G | `f6-p1.tgz`（內含 F8 的 adb 私鑰）、`xfer-src` 測試資料、`f6-apk`、量測輸出。 |

- 讀壓縮過的證據：`zstdcat <檔>.zst | less`；要還原成原檔用 `zstd -d <檔>.zst`，還原後 `sha256sums.txt` 照樣驗得過。frozen 證據只換了儲存格式，內容沒有任何改變。
- 壓縮工具先用假資料測過，包含一個故意弄壞、必須保留原檔的案例。第一次測試抓到參數順序錯誤（`-o` 放在 `--` 後面），當時只碰到假資料。
- clinic 保留的 3 個 worktree 和原因：
  - `doc-truth`：HEAD `9b6ea47` 不在任何遠端 branch 上。它沒有設定上游，所以 `@{u}..` 的檢查會誤判成「已 push」，改用 `branch -r --contains HEAD` 才抓到。
  - `scm-js-yaml`：有 1 個 commit 還沒 push。
  - `scm-r04`：有 1 個檔案還沒 commit。
  - `luna-d006` 被 git 忽略的檢查點 `output/evidence/luna-checkpoint.txt`（PR #117 的進度）已另存到 `clinic/.claude/worktrees/_archive-20260926/`，這個位置已被 ignore。
- **使用者沒選、還留著的大項**（要做的話先問使用者）：
  - Chromium 的 `OptGuideOnDeviceModel` 2.7G。這是 hermes-chrome／ChatGPT Web 用的 Playwright Chromium 自己下載的本機 AI 模型；刪掉的話要另外加 policy 擋住，不然會再下載回來。**使用者這次沒選。**
  - Cursor 的 `state.vscdb` 3.0G：幾乎全是聊天紀錄（bubbleId 1.5G、agentKv 1.0G），VACUUM 回收不到空間。要瘦身只能在 Cursor 裡刪舊對話。
  - `/root/.gradle` 1.3G、`/root/build` 1.0G、`/root/android-sdk` 0.6G：本機建置工具。
  - `ms-playwright` 1.2G：hermes-chrome 會用到，**不要刪**。
  - `/.l2s` 2.7G：hardlink 的替身，**不能刪**。

### POCO F6 Pro（結案）
- 使用者已驗收：桌面、桌布、Claude（保持登入）、輸入法都正常。細節在上一份交接頂端的「F6 複製結果」。
- 桌面「開一下就關」的原因是 **Android 子程序限制**。使用者自己在開發人員選項關掉後就好了。查法：`getprop persist.sys.fflag.override.settings_enable_monitor_phantom_procs` 要是 `false`，兩台現在都是。記憶 `phantom-process-killer`。
- 兩台上的分割檔已刪：F8 的資料夾整個移除；F6 的 `Linux ` 只清檔案，資料夾保留。
- F6 已換成自己的 adb 金鑰（Termux `991774c0…`、rootfs `a098a8df…`），F8 私鑰的複本和 `adb_known_hosts.pb` 都已刪。F8 仍然可以用 F8 的金鑰控制 F6（使用者配對的）。**F6 本機的 adb 還沒配對**，F6 沒有外接螢幕所以用不到。
- F6 桌面上的「F8 鍵盤列（實驗版）」已移到 `/root/.local/share/f8-removed-20260926/`。
- F6 的 IP 和埠會變，最後一次是 `10.128.106.111:41707`（09-27 11:01，掃埠＋adb 協定驗證找到；mDNS 查不到）。每次都要重新探測，只用 5038 通道。

### 其他
- PR #37（X3-DIRECT-FEAS＋AUTO-SHARD-01）**已合併**（2026-09-26 11:29Z）。不要再 push 到那個 branch。
- fork `src/f8-ahb-exa-async`（HEAD `8423f0a`）**還沒 commit** 的 auto-shard 工具：`tests/tracer_shard/` 底下修改了 f8-shard、shard-run.sh、smoke_electron.sh，新增 autoshard_inner.sh、autoshard_judge.py、autoshard_real_inner.sh、shard-daemon.sh、test_autoshard.sh、test_autoshard_real.sh。使用者要求時再 commit／push。
- 5038 通道：本次最後會 `kill-server`。

## 3. 等使用者決定或提供的
- **主線方向**：使用者日常主要跑 agent、不跑 3D、可能會剪片。#3（X3 端 DRI3＋AHB）可行性結果是收益小（`evidence/session/gl/X3-DIRECT-FEAS-RESULT.md`）。下一步做什麼等使用者選。
- **Eden／BOTW**：F6 上的 `.nsp` 是 BOTW 1.9.0 更新檔。缺本體遊戲和韌體，要使用者從自己的 Switch 提供。拿到後可以幫忙把韌體 NCA 平鋪打包成 zip，並把檔案放進 Eden 的遊戲資料夾。
