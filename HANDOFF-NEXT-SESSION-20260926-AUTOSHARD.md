# HANDOFF — 2026-09-26（傍晚～晚上）：主線 #3 可行性有結果；使用者日常＝agent；**自動分流已上線（日常 proot-fast8＋包裝程式，Claude Desktop 已自動分流）**

## F6 複製結果（22:55，先讀這段）
- **F6 = POCO F6 Pro 23113RKC6G，Android 16，核心 5.15.194。** 使用者換了網路：F6 現在是 `10.128.106.111`，無線偵錯連線埠 40639（5038 通道）；F8 是 10.191.48.13。**IP 和連線埠都會變，每次都要重新探測。**
- 完成：
  - 四個 Termux App、Termux prefix＋home、Termux:X11 偏好設定。
  - Ubuntu rootfs 以分割檔互傳到 F6 `/storage/emulated/0/Linux `（**資料夾名稱結尾有一個空格**），雜湊全部相符，解開 rc=0，約 32G，F6 剩 108G。
  - `.l2s`：F6 100646 筆，F8 100647 筆（打包後 F8 自己多一筆）；之前的「0 筆」是 `ls` 沒加 `-A` 造成的誤判。
  - 桌布：F8 的 `F8-Wallpapers/0[1-4].jpg` 是指到 F8 `/sdcard/Download/X/` 的連結，圖片本身不在 rootfs 裡。**在 F6 上改成實體檔案**，SHA256 跟 F8 原檔相同。
  - 身分標記：`$PREFIX/tmp/f8-shard/f6-identity.py`。改動的檔案有 CLAUDE.md、`.codex/AGENTS.md`、`Documents/F8-WORKSTATION-STATE.md`、Serena `f8-workstation.md`、Hermes `MEMORY.md`，以及兩份 `.machine-identity`；每個都有 `.bak-20260926-f6id` 備份。
    - 陷阱：`adb exec-in` 在本機 stdin 關閉時就返回，**F6 那頭的 cat 可能還沒寫完**，讀回驗證必須用輪詢。第一次驗證失敗時檔案其實是對的，雜湊跟本機預期值相同。
  - 冒煙測試（F6 自己的 Termux，run-as）：proot-fast8 和 stock proot 都能進 Ubuntu 24.04.4；claude-code 2.1.275／2.1.280、claude-desktop 2.2553.13、Hermes v0.21.2、keyring 都在。
    - `claude`／`codex` 不在 PATH 上，這跟 F8 相同，不是漏掉。
- 權限比對（F8 對 F6）：
  - F6 缺 Termux 的 SYSTEM_ALERT_WINDOW（F6 是 ignore）、Termux:X11 的電池白名單、Termux 的儲存空間權限（READ_EXTERNAL_STORAGE granted=false）、Termux:X11 的通知權限。
  - 桌面模式和 freeform 不用做：**使用者說 F6 本身不支援外接螢幕**。
  - 這些都要使用者自己在 F6 上點；Claude 不用 adb 代改系統權限。
- **23:05 桌面「開一下就自己關」（每次約 3 秒）**：
  - 原因是 Android 的子程序限制（phantom process killer）。F6 的 logcat 被 HyperOS 壓到幾乎沒有 App 訊息，只能靠 `$PREFIX/tmp` 的殘留回推：fcitx5 log 顯示連上 `:1` 後 3 秒就開始卸載；22:59 那次甚至已經自動啟動並分流了 Claude。
  - 使用者在開發人員選項打開「停用子程序限制」後就正常了。
  - 驗證：`getprop persist.sys.fflag.override.settings_enable_monitor_phantom_procs` 在 F8 和 F6 都是 `false`。`settings get global ...` 是 null，Android 14 以後不存在 settings 表裡。
  - **以後在別台手機裝這套時，第一步就要做這個。**
- **23:15 F6 驗收通過（使用者確認正常）**。兩台上的分割檔已依使用者同意刪除：F8 `Download/F6-clone-20260926/` 連同資料夾移除（F8 剩 51G）；F6 `Linux ` 只清檔案、保留資料夾（F6 剩 121G）。F6 logcat 暫存已刪，5038 已 kill-server。F6 複製**結案**；下面清單只剩標為可選的項目。
- **23:41 兩個可選項目也完成了（使用者說「可以」）**：
  - F6 上從 F8 帶過去的兩把 ADB 私鑰已刪除：Termux `~/.android/adbkey`（`d755cfc2…`）和 rootfs `/root/.android/adbkey`（`064903b0…`）。一併刪掉 `adb_known_hosts.pb`（F8 配對過的主機清單）。
  - 換成 F6 自己的新金鑰：Termux `991774c0…`、rootfs `a098a8df…`，comment 都是 `u0_a633@vermeer`。
  - F8 上的原檔沒有動。F8 從 5038 連 F6 仍然正常：F6 信任的是 F8 的金鑰，這是使用者自己配對的。
  - **F6 自己的 ADB 工具目前沒有配對。** F6 沒有外接螢幕，用不到；「F8 自動」會回到手機桌面。以後要用的話，由使用者在 F6 的 Termux 自己輸入配對碼，執行 `adb pair 127.0.0.1:<配對埠>`。
  - 「F8 鍵盤列（實驗版）」已從 F6 桌面移到 `/root/.local/share/f8-removed-20260926/`，要恢復時搬回 `/root/Desktop/` 即可。
- （已完成的歷史清單）：
  - 使用者點完權限後，在 F6 上用「F8 工作站」開一次桌面驗收。第一次開 Claude Desktop 會跳 keyring 密碼，密碼跟 F8 相同。
  - 驗收通過後刪掉兩台手機上的分割檔：F8 `Download/F6-clone-20260926/`（13.5 GB；F8 磁碟 89%）和 F6 `Linux /`。**先問使用者再刪。**
  - `adb -P 5038 kill-server`。
  - 可選：拿掉 F6 桌面上的「F8 鍵盤列（實驗版）」（F6 沒有 `com.waydefu.x11gpu`）；F6 另外產生一把自己的 adb 金鑰（目前兩台共用一把）。

## 最新狀態（20:40，先讀這段）— 小工具修好＋F8 自動＋F6 複製準備
**待驗證（使用者要求寫成交接）：常駐程式的 `setsid -f` 修正**
- 背景：原本 `f8desk` 用 `setsid shard-daemon.sh &`，常駐程式會變成 f8desk 背景子程序的子程序，那次開機的桌面 proot 就一直在等而殘留（09-26 的 31217）。已改成 `setsid -f`（`$PREFIX/bin/f8desk{,-external}`，備份 `.bak-20260926-v8fix2`），殘留的 31217 已清掉。
- **只有「常駐程式還沒在跑」時才會用到新寫法**：常駐程式活著的話，flock 會讓那一行立刻結束。所以要在 **Termux 或手機重開後第一次用 F8 工作站／F8 自動開桌面** 之後驗證：
  1. `DP=$(cat /data/data/com.termux/files/usr/tmp/f8-shard/daemon.pid); grep PPid /proc/$DP/status` → 父程序**不是**跑 `f8desk` 的 bash（`tr '\0' ' ' < /proc/<ppid>/cmdline` 裡不該有 `/bin/f8desk`）；
  2. 列出所有 comm 是 `proot-fast8` 的程序，數各自的 tracee（`TracerPid` 等於它的程序）。除了日常桌面那個和各分流以外，**不該有 0 個 tracee、而且子程序是 f8desk bash 的 proot**；
  3. 一般關開桌面（常駐程式已在跑）之後，也順手跑一次第 2 步。
  不過就回頭查 `f8desk` 那一行，**不要**直接 kill 使用者的程序（上次是 apply-v8-fix2.sh 第 5 步有條件地處理）。
- 同一批其他修正都已實測：`f8-adb-port`（mDNS 查不到 → 快取＋掃埠＋adb 協定驗證）、`f8-mouse-external`（自動找埠、描述碼改從 Event Hub 抓）、`f8-fullscreen`（加 `-s`、失敗時跳 toast）。外接 Linux、滑鼠、滿版由 Claude 實測（5038 通道）；**外接 App 由使用者實測成功（走 5037）**。F8 設定只做靜態檢查。紀錄：`evidence/session/daily/F8-WIDGETS-CHECK-20260926.md`。
- 新增第 4 個小工具「**F8 自動**」（`$PREFIX/bin/f8-auto`）：有外接螢幕就開到外接螢幕並綁滑鼠，否則開在手機上；原本三個不動。
- 全域文件已更新：`/root/Documents/F8-WORKSTATION-STATE.md`（§4、§5、§13、§14）、`F8-BASELINE-V2.md`（開頭註記）、Serena `mem:global/f8-workstation`、`~/.claude/CLAUDE.md`（都有 `.bak-20260926`）。

**POCO F6 完整複製（使用者晚點接上；決定如下）**
- 做法：把 F8 的 Termux＋Ubuntu 複製到 F6，**登入資料全部帶過去**（使用者選的）。應用只要工作站相關：Termux、Termux:X11（Stable）、Termux:API、Termux:Widget，APK 直接從 F8 已安裝的版本取（`cmd package path <pkg>`）；Ubuntu 裡的程式、XFCE 設定、桌布跟著 rootfs 一起過去。
- **排除**：`/root/projects/GPU加速`（18.8 GB，使用者說不用搬）、`/root/build`（GPU／bench 的 build 樹 1.0 GB）、`/root/android-sdk`（0.6 GB）、`/root/.gradle`（1.3 GB，重建得出來）。其他 clinic worktree 各約 0.5 GB，保留。
  大小（09-26 20:30 從 Termux 那側 du）：rootfs 53.2 GB（projects 19.8、usr 8.7、.cursor-data 7.3、.config 4.3、.hermes 1.9、.local 1.7、.cache 1.7）；Termux prefix（不含 rootfs）1.3 GB；Termux home 0.09 GB。排除後約 **31–32 GB**。
- 連線：F8 的 adb 不能直接操作 USB（`LIBUSB_ERROR_IO`），所以要在 F6 開**無線偵錯**，由使用者在 Termux 自己輸入配對碼（`adb -P 5038 pair <F6 IP>:<配對埠>`，HOME 要是 Termux home；**配對碼不經過 Claude**），再 `connect` 到 F6 無線偵錯畫面上的連線埠。兩台要在同一個 Wi-Fi。
- 步驟草案：① 在 F6 上 `adb install` 四個 APK；② 在 F6 開一次 Termux（bootstrap）；③ 用 `tar c … | adb exec-in run-as com.termux tar x -C /data/data/com.termux/files` 串流過去（F8 的 Termux 是 debuggable，裝同一個 APK 所以 run-as 能用；串流不用先在 F6 上存一份 tar）；④ 權限和系統設定要使用者在 F6 上自己點：Termux:API 權限、電池最佳化例外、開發人員選項「在外接螢幕強制使用桌面模式」；⑤ 在 F6 上開桌面驗證，並注意 F6 的 GPU（Adreno 735）跟 F8 不同，`/opt/mesa-kgsl` 可能不能用，Electron 本來就走軟體渲染所以不影響。
- **先確認**：F6 的剩餘空間（至少 ~40 GB，串流不另外多佔）、Android 版本、RAM。

## 17:05 狀態
- **自動分流已在日常生效**（使用者執行 fix1 並重開後驗證）：日常追蹤器 10369 是 proot-fast8，有 `PROOT_F8_AUTOSHARD=1`；Claude Desktop 被自動分流（autoshard.log `shard electron …/claude-desktop`）；常駐程式活著。細節見 `AUTO-SHARD-01-RESULT.md`「修正 1 生效」。
- 下一步候選（使用者還沒選）：每個終端機視窗各自一個追蹤器（`--disable-server`）；量 agent 工作時的 CPU／記憶體（先前建議的 1）；剪片硬體編碼查證；EGL 不上屏。

## 16:50 狀態
- **16:50：第一次套用沒讓自動分流生效**（proot-distro 會丟掉 f8desk export 的 PROOT_F8_*）。修正 1 已做好並測過：包裝程式 `out8/auto/proot-fast8` 加上腳本 `shard2/apply-v8-fix1.sh`，**等使用者在 Termux 執行後再重開 F8 工作站**。
  重開後驗證：日常追蹤器 environ 有 `PROOT_F8_AUTOSHARD=1`、Claude Desktop 的 TracerPid ≠ xfce4-session 的、`autoshard.log` 有 `shard electron /usr/lib/claude-desktop/claude-desktop`。細節見 `AUTO-SHARD-01-RESULT.md`「套用紀錄」。

## 16:25 狀態
- 使用者說「開始」後做完了。結果：`evidence/session/proot/AUTO-SHARD-01-RESULT.md`；凍結：`AUTO-SHARD-01-FREEZE.md`；素材：`evidence/session/proot/auto-shard-01/`。
- proot-fast8（`out8`，sha `10121cc4…`）＋ f8-shard v2 ＋ `shard2/`（shard-run v2、shard-daemon）。分流啟動 1.1 s → **0.12 s**；3 秒 bug 已修；Claude Desktop 和 Cursor 真實 app 都通過（real-02）。real-01 FAIL 是工具缺陷（Chromium setproctitle），凍結保留。
- **16:41 已套用（重開 F8 工作站才生效）**：f8-shard v2 已裝（v1 備份 `.bak-20260926-v1`），f8desk／f8desk-external 已改（備份 `.bak-20260926-v8`）。原本這行：還沒換進日常，`/usr/local/bin/f8-shard` 仍是 v1，f8desk 仍選 v7。套用：在桌面終端機跑 `~/build/proot-fast/shard2/apply-v8-autoshard.sh`，再關掉並重開「F8 工作站」（會關掉所有 app，包括 Claude Desktop）。**要使用者自己決定、自己執行。**
- 套用之後要做：確認日常追蹤器是 proot-fast8（`/proc/<tracer>/cmdline`）、`autoshard.log` 有 `shard electron`／`shard terminal`、常駐程式活著；Cursor／Hermes／ChatGPT 的舊啟動器區塊不用拿掉（規則會判 `explicit_shard` 跳過，不會分兩層）。
- 已知限制：自動分流的程式輸出寫到 job log、exit code 為 0；所有 xfce4-terminal 視窗共用一個分流追蹤器（每個視窗各自一個要加 `--disable-server`，還沒做）。
- fork worktree `src/f8-ahb-exa-async` 的 `tests/tracer_shard/` 有未 commit 的修改：f8-shard v2、shard-run v2、新增 shard-daemon 和測試腳本。使用者沒有要求 commit，所以沒 commit。


接續 `HANDOFF-NEXT-SESSION-20260926-GL.md`（下午）。那份與上午 `HANDOFF-NEXT-SESSION-20260926.md` 的待辦仍然有效。

## 1. 主線 #3（X3 端）可行性：做完了，只讀／探針，沒有改產品
- 結果：`evidence/session/gl/X3-DIRECT-FEAS-RESULT.md`；素材：`evidence/session/gl/x3-direct-feas/`（凍結檔、探針原始碼、原始輸出、雜湊）。**本地，尚未推 GitHub。**
- FEAS-01 `DMABUF_IMPORT_UNAVAILABLE`：Android EGL 和 GLES 都不收 dma-buf，所以 X3 端做不到零複製。
- FEAS-02 `VK_DMABUF_GPU_COPY_FAIL`（凍結）：Adreno Vulkan 對 external 資源固定多要 5300 bytes。
- FEAS-03 `VK_DMABUF_GPU_COPY_OK`：系統 Vulkan 可以把 dma-buf 用 GPU 複製進 AHB；剛好大小時，最後 1–2 列要用 CPU 補。
- 另一條路（AHB 方案）：X3 配 AHB，client 用 DRI3 `BuffersFromPixmap` 拿 fd 直接畫。X3 端已經有 `lorieFdsFromPixmap`（`InitOutput.c:4401`）加非同步的 GPU present copy，只要修 flip 的尺寸 bug（`InitOutput.c:4101`，上游也有）；主要要改的是自編 Mesa 的 `wsi_common_x11.c` `x11_image_init`。這條還沒驗證。
- 收益：全螢幕 60 fps 約省 0.03–0.11 核。**使用者 09-26 說平常不跑 3D、基本都在跑 agent、可能會剪片** → 主線 #3 對日常收益小。使用者沒有明確下令暫停，但也沒有選任何一個 #3 選項。

## 2. 下一步候選：自動分流（使用者已同意方向，**說「等等處理，我可以了再叫你」**）
**目標**：不用再一個一個改啟動器。新程式、程式自己重寫啟動器（例如 Claude Desktop 會重生 `.desktop`）都能自動分流。

**現況缺口**：Claude Desktop 沒有分流（桌面圖示 `Exec=claude-desktop ...` 直接啟動），它和它開的 Claude Code 都擠在日常追蹤器 pid 29525（proot-fast7）。已分流的有 Cursor、Hermes、ChatGPT／Codex、hermes-chrome，都是在啟動器開頭加區塊。

**計畫**（照 v7 的慣例：獨立建置，不動日常，最後由使用者自己套用）：
1. **proot-fast8**：在 proot 處理 `execve` 的地方加規則。遇到 Chromium／Electron 類執行檔（執行檔同目錄有 `v8_context_snapshot.bin`；已確認 `/usr/lib/claude-desktop`、`/usr/share/cursor`、`/usr/lib/chatgpt` 都有），就把 exec 改寫成 `f8-shard <原 argv>`。
2. **終端機也分流**（使用者同意）：每個終端機視窗一個追蹤器，裡面跑的 CLI agent 就不會拖慢桌面。
3. 要擋的例外：
   - Electron 自己的子程序（zygote、gpu、utility，會 re-exec `/proc/self/exe`）→ 靠 `F8_SHARDED` 環境變數擋。
   - `--remote-debugging-pipe`（Playwright 預設）→ 分流後拿不到繼承的 fd，要跳過。
   - 小指令不分。
4. **先修 f8-shard 的 3 秒 bug**：程式立刻結束時，TracerPid 檢查迴圈照樣重試滿 30×0.1 s（`/usr/local/bin/f8-shard` 第 64–72 行，缺「`/proc/$APP` 不在就停」）。實測 `f8-shard /bin/true` 要 4.1 s。Electron 第二實例轉交（點 claude:// 連結）、`cursor --version` 都會踩到。
5. **縮短每次分流的 1 秒**：實測 `f8-shard /bin/sleep 3` 在 +1.05–1.12 s 才看到 app，推測是 app_process 版 `am` 的啟動。候選做法：常駐的 Termux 端小程式（只經 TermuxService 啟動一次），用 FIFO／socket 接工作。未驗證。
6. 驗證：先用假啟動器，再用真的 Claude Desktop 在測試追蹤器裡跑；**判準先凍結**（自動分流是否和手動一樣消掉卡頓，對照 TRACER-SHARD-01 的數字）；跑之前工具先用真實資料驗過（見記憶 verify-before-device-runs）。

**已量到的分流數字**（給使用者看的白話版已經講過）：
- 啟動多約 1 s；跑起來之後程式本身速度不變。
- 桌面卡頓 18–20 次 → 0；fstatat p99 71–80 ms → ~1 ms；日常追蹤器約 1 核 → 0.02–0.04 核（TRACER-SHARD-01）。
- 總 CPU 大致不變（是分散到多核，不是省）；每個追蹤器約 9 MB RSS。

## 3. 其他待辦（沒動）
- 剪片：瓶頸是編解碼，PRoot 用不到硬體影片引擎。候選是查 Termux 原生 ffmpeg 能不能用 MediaCodec 硬體編碼（**未查證**）。等使用者真的要剪片再做。
- EGL 不上屏：見下午那份 handoff。
- X3-DIRECT-FEAS 證據要不要推 `waydefu/GPU`：要問使用者。

## Stable／裝置
這一輪沒有碰 Stable `:1`、實驗 app、X3、ADB。只在 PRoot 內跑了 bionic 探針（系統 EGL／GLES／Vulkan）和 5+3 次 `f8-shard /bin/true`／`sleep 3` 的計時。
