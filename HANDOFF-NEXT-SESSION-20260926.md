# HANDOFF — 2026-09-26：日常卡頓用「追蹤器分流」解掉（proot-fast7＋f8-shard 已上日常）；XFCE 2D GPU 加速暫停，主線移到 #3 DRI3＋AHB

**新對話先讀：** 本檔 → `evidence/session/proot/TRACER-SHARD-01-FREEZE.md`（§12 結果）→ `evidence/session/xfce-v6/XFCE-NOTEL-01-FREEZE.md`（§10 偏差、§11 結果）
→ `evidence/session/xfce-v6/XFCE-V6-BASELINE-01-FREEZE.md`（§10 Part A、§11 Part B）。上一份交接 `HANDOFF-NEXT-SESSION-20260925.md` 仍是 PRoot v2–v6 與 GL 的背景。
回覆用繁體中文、**白話簡單**；指令、檔名、verdict token、commit／PR 保持英文。

## 使用者目標（不變）
「解放手機效能，讓日常程式（Claude、ChatGPT／Codex、Hermes、Cursor…）的 CPU／GPU 收益最大化」，並把 Ubuntu 做成真正的 GPU 工作站
（Blender 3D viewport、Linux GL／VK、WebGL）。Android 遊戲不經 Ubuntu，不在範圍內。

## 日常現況（2026-09-26 03:30）

| 項目 | 狀態 |
|---|---|
| 日常 PRoot 追蹤器 | **proot-fast7**（`~/build/proot-fast/out7/bin/proot-fast7`，sha256 `4f9d10ad…`）＝ v6 ＋ `proot-fast7-peercred.patch`（跨追蹤器 D-Bus）。`f8desk`／`f8desk-external` 第一順位 out7（備份 `*.bak-20260925-v7`）。使用者 09-25 21:37 套用＋重開 |
| 追蹤器分流 | `/usr/local/bin/f8-shard`（sha256 `b2f11d3d…`）＋ Termux 端 `~/build/proot-fast/shard/shard-run.sh`：重 app 各用自己的 proot 追蹤器 |
| 已分流的入口 | `~/.local/bin/cursor-gpu`、`~/.local/bin/hermes-gpu`、`/usr/local/bin/hermes-desktop-f8`（備份 `*.bak-20260926-shard`）；新 `~/.local/bin/chatgpt-f8`＋三個 ChatGPT 選單／桌面入口；`/usr/local/bin/hermes-chrome`（ChatGPT Web／Hermes 自動化的 Chromium）。備份 `~/.local/share/f8-shard-backup-20260926/` |
| 略過分流 | 啟動時設 `F8_NO_SHARD=1`（**量「不分流」的實驗一定要設**，否則 P 組會被自動分流） |
| 沒分流 | Claude Desktop（它的 `.desktop` 會被 app 重生；本 Claude Code 也在它底下）、終端機、XFCE 本身 |
| 更新安全 | 改到的檔案都不屬於任何套件（`dpkg -S` 查過）；ChatGPT 套件檔（`/usr/bin/chatgpt`→`codex-launcher`）沒動 |
| 回退 | 各檔 `.bak-*` 複製回去；v7 → 刪 out7 或「F8 設定」切原版；桌面圖示信任＝`metadata::xfce-exe-checksum`（檔案 sha256），回退時一起 `gio set` 舊值（備份裡有） |
| 實驗 `:3` | `com.waydefu.x11gpu` `1.03.01-f592241-24.09.26`（未變） |
| 儲存 | 477G 用 90%、剩 51G；本輪 raw logcat 都已 gzip（使用者同意，解壓 sha256 驗過，`POST-CAPTURE-CHANGES.md` 留痕） |

## 本輪結果（全部凍結在資料之前）

| 實驗 | 判決 | 重點數字 | PR |
|---|---|---|---|
| XFCE-V6-BASELINE-01 Part A（日常 `:1`，v6） | `DAILY_STUTTER_REMAINS`、`X_SERVER_STALLS_PRESENT` | E：stock 148 → v6 48／14；剩下幾乎全是 fstatat 停頓 | #30 |
| XFCE-V6-BASELINE-01 Part B（實驗 `:3`） | `GT_NO_TAIL_STALLS`、`NO_SEPARATION` ×3 | X3 0.50–0.65 核（**被 telemetry 灌水**，見下） | #31→#34 |
| **TRACER-SHARD-01**（v7 日常） | **`SHARD_REMOVES_STUTTER`** | 其他程式的卡頓 E：P 20／20／18 → S **0／0／0**；日常追蹤器 0.23–0.26 → 0.02–0.04 核 | #32 |
| **XFCE-NOTEL-01** | **`TELEMETRY_COSTS_X_CPU`**；GT 對 C `NO_SEPARATION` ×3 | telemetry ＋0.18 核（＋60%）；關掉後 X3 僅 ~0.30 核，GPU＝CPU | #33（凍結）、#34（偏差＋結果） |

- 機制：日常所有 PRoot 程式共用**一個單執行緒**追蹤器；Electron 啟動塞滿它（60 次停頓 59 次在滿載秒）。分流讓每個重 app 用自己的追蹤器。
- 跨追蹤器 D-Bus 原本會失敗（fake_id0 的 `SO_PEERCRED` 只認自己的 tracee → dbus-daemon 拒絕），proot-fast7 修掉；已對真實日常 bus 實測。
- XFCE runner 預設 `GATEA_TELEMETRY=1`：X3 每秒 5.4 萬行 log（EXA `PrepareAccess` trace）。**往後 X CPU 量測一律關 telemetry**；
  R8 arm 必須同時開 telemetry（`lorie_r8_obs.c:130`，否則 `x-r8-env` 停機），關 telemetry 就不 arm R8（runner V5b）。

## 使用者決定（2026-09-26）
- **主線 #2「XFCE 2D 的 GPU 加速（Gate A／EXA）」暫停。** 原因：關掉 telemetry 後 GPU＝CPU；XFCE 的圖 89% ≤64×64 留在 CPU，送 GPU 的只有 53 張，
  全送（G0）反而更慢還會卡。程式碼、實驗 APK 保留；Production／Gate A 狀態不變。
- **主線移到 #3：DRI3＋AHB client 端。**
- 刪除 `docs/xfce-notel-01-freeze` 分支（已刪，見「待辦」）。

## 主線 #3 下一步（DRI3＋AHB client；尚未開始）
背景（09-25 交接 §3）：GL-BENCH-02 證明 GPU 算圖 4–5×，但 Zink 上屏時 X3 吃 55–74 CPU 秒、畫面外只有 4–5 秒；Zink/Turnip 目前走 **drisw**（推測每幀 CPU 複製，**未證實**）。
X 端 `loriePixmapFromFds`（`src/upstream/lorie/src/main/cpp/lorie/InitOutput.c:1170`）已認 modifier 1255／1256（socket 傳 AHB）與 1274／LINEAR（可 mmap 的 fd）。
1. **先證實瓶頸在哪**（凍結後量）：`:3`、telemetry 關、R8 不 arm，跑 Zink glmark2／vkcube 類負載，量 X3 各執行緒 CPU 與 client 的上屏呼叫（drisw 的 `PutImage`／`ShmPutImage` 次數與大小）。
   判準要有「應該要紅」的對照（例如畫面外渲染）。之前的 GL 資料都帶 telemetry 嗎？要先查，帶的話不能直接引用 CPU 數字。
2. **可行性調查（唯讀，先不寫產品碼）**：glibc Mesa 怎麼把 GPU buffer 交給 X3。候選：
   (a) Turnip 在 KGSL 上把 render target 匯出成 dma-buf fd → DRI3 `PixmapFromBuffers`（LINEAR/1274）→ renderer 用 EGLImage 匯入（零複製？X 端現在對 1274 是 mmap，renderer 端是否上傳要查）；
   (b) X3（bionic）代配 AHB、經 Unix socket 把 fd 給 client → Turnip 匯入 dma-buf（KGSL `GPUOBJ_IMPORT` dma-buf？）→ 1255 路徑（Gate A R2 fixture 已用）；
   (c) shim。每條先查原始碼與核心能力，再決定原型。
3. 原型前凍結 GL 上屏的判準（GL-BENCH 格式：不碰手機、A/A 波動實測、telemetry 關）。

## 其他待辦
- **PR #34** 待合併（Part B 結果＋NOTEL 偏差與結果補進 main；#31 當時合進疊層 base、#33 合併早於後續 commit）。
- **公開 repo 的 raw logcat**：失敗 preflight 的 raw logcat（含附近藍牙裝置 `originalAddress`，隨機位址）曾隨 `dc2a32e` 推到 `docs/xfce-notel-01-freeze`（從未進 main）。
  分支已刪（09-26，使用者同意），但 GitHub 仍可用完整 SHA 取到 `dc2a32e`；要徹底移除需請 GitHub Support 清除快取 commit（使用者決定）。
- 可選：`f8-doctor` 加「分流區塊＋v7 仍在」檢查；Claude Desktop 分流（需處理 `.desktop` 重生）；終端機分流（先評估 `--kill-on-exit` 對會 daemonize 的程式）；
  proot 內建自動分流（execve 名單攔截，估半天～一天；真正的追蹤器交接估數天、風險高，暫不做）。
- 舊證據壓縮（09-25 交接列的 `evidence/` ~9 GB）仍待使用者同意。

## 本輪新陷阱（都有記憶檔）
- 手機換 Wi-Fi 會關掉「無線偵錯」；端點會變（`tests/xfce_v6/adb_find.py` 掃埠＋逐一 `adb -P 5038 connect`）。
- 長測試手機要**接電**：螢幕常亮靠 `stay_on_while_plugged_in=15`（`mStayOn=true`），沒接電 10 分鐘就熄屏。
- 桌面重開會清 `/tmp`：`/tmp/p_r10_ledger` 要重建（`cc -O2 … tests/r10/p_r10_ledger.c tests/r8/r8_xcb_request.c -lxcb -lxcb-render`，sha `2aca8ae1…`）。
- Electron renderer 的 cmdline 因 app 而異（Cursor／Hermes 沿用 zygote；ChatGPT 改名 `--type=renderer`）；VS Code 系輔助程序無 `--type=`，別用 cmdline 猜主程序。
- 直接用 `f8-shard` 叫已加區塊的啟動器會分流兩層（測試設 `F8_SHARDED=1`）；`setsid` 可能 fork，`$!` 不一定是目標。
- 推證據：疊層 PR 進 base 不進 main；使用者常在建立後立刻合併（之後的 push 不會進 main）；**公開 repo 別推 raw logcat**（`tar --exclude`＋commit 前檢查）。
- 改日常檔案（啟動器、`f8desk`）會被 auto mode 擋：寫成套用腳本、先在假根目錄測、給使用者自己執行。

## Fork 狀態（`src/f8-ahb-exa-async`，`feat/exa-async-proto-20260923`，本地未 push）
`27f72e5`（tests/tracer_shard）、`7e9c752`／`a72669c`（tests/xfce_notel）；快照在 `evidence/session/proot/tools-27f72e5/`、`evidence/session/xfce-v6/tools-7e9c752/`、`tools-a72669c/`。
