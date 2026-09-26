# HANDOFF — 2026-09-26（傍晚）：主線 #3 可行性有結果；使用者日常＝agent；**自動分流已上線（日常 proot-fast8＋包裝程式，Claude Desktop 已自動分流）**

## 最新狀態（17:05，先讀這段）
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
