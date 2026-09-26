# HANDOFF — 2026-09-26（下午）：主線 #3 第一步有判決——上屏的 CPU 花在 X3 的 Present 複製；主線 #3 改做 X3 端；另開「EGL 不上屏」

接續 `HANDOFF-NEXT-SESSION-20260926.md`（上午：日常 v7＋追蹤器分流；XFCE 2D GPU 暫停）。本檔**只**寫下午的新進度，上午那份的待辦仍然有效。

## 先讀
1. `evidence/session/gl/GL-PRESENT-03-RESULT.md`：判決、數字、限制。
2. `evidence/session/gl/GL-PRESENT-01-FREEZE.md`（原始設計＋修訂 1）→ `GL-PRESENT-02-FREEZE.md` → `GL-PRESENT-03-FREEZE.md`（每一份只記改了什麼）。
3. `GL-PRESENT-01-RESULT.md`、`GL-PRESENT-02-RESULT.md`：這兩次都 INVALID，原因是判定器的漏洞，已凍結保留。

## 判決
| attempt | 判決 | 原因／數字 |
|---|---|---|
| GL-PRESENT-01 | `GL_PRESENT_INVALID` | J0 規則漏洞：Zink kopper 在 `glXMakeCurrent` 就建立 swapchain，glx-off 的 3 次 DRI3 匯入被當成上屏 |
| GL-PRESENT-02 | `GL_PRESENT_INVALID` | 02 新加的規則把 vk-off 的空直方圖（根本沒連 X）當成缺檔；另外 rep2 vk-off 有一次焦點讀到空值 |
| **GL-PRESENT-03** | **`PRESENT_COST_IS_X3_PER_PIXEL_COPY`** | vk／glx 都是 `PATH_DRI3`（modifier 0，X3 log 也證實），egl 是 **`PATH_NOT_PRESENTED`**。上屏時 X3 vk 0.98／0.90 核、glx 0.48／0.48 核，基準是 0.016。每幀成本的 L／M 比 vk 4.3／4.4、glx 3.2／3.5 |

**白話**：Ubuntu 的 GL／VK 程式早就用 DRI3 把 GPU 畫好的 buffer 交給 X3 了。但 X3 只收 LINEAR，把它 mmap 成 CPU 記憶體，而且對匯入的 buffer 一律不 flip，所以每一幀都在主執行緒用 CPU 整張複製一次。
舊的「client 端用 drisw 複製」推測**是錯的**。

**限制**：vk-l 每幀的 X3 成本在不同 attempt 之間差了將近一倍（01／02 是 0.45 ms，03 是 0.86 ms），**原因還沒查**。所以每像素的成本只能給範圍 0.22–0.64 ns/px；外推到 120 fps、1200×2400 的視窗，X3 大約 0.08–0.23 核。

## 使用者決定（09-26 下午）
1. **主線 #3 改做 X3 端**：讓 X3 直接把 client 的 GPU buffer 拿去顯示，不再每幀用 CPU 複製。原本的「DRI3＋AHB client 端」不做了。
2. **另開一條「EGL 不上屏」**。
3. 證據推 `waydefu/GPU`（本 PR）。

## 主線 #3（X3 端）下一步：先做可行性調查（唯讀），不寫產品碼
- **(a) renderer 直接匯入 client 的 dma-buf**：先查 Android／Adreno 的 EGL 有沒有 `EGL_EXT_image_dma_buf_import`，並在裝置上實際查詢 extension 字串。
  `lorie/.../renderer.cpp` 已經有「偵測 AHB 是不是由 dma-buf 撐著」的程式碼，`lorieFdsFromPixmap` 也用同一招。要查反方向（dma-buf 轉 AHB 或 EGLImage）有沒有公開或 vendor 的路。
- **(b) 讓匯入的 buffer 可以 flip**：`loriePresentFlip`（`InitOutput.c`）對匯入的 FD 一律拒絕（「does not work fine with turnip」，`TERMUX_X11_FORCE_FLIP=1` 可以繞過）。
  另外它的尺寸判斷寫成 `root.width != pixmap.height`，看起來是 bug。flip 只適用於全螢幕視窗，要查 FORCE_FLIP 為什麼不行。
- **(c) 先把 CPU 複製變便宜**：量 mmap 讀取的成本，看有沒有少做 `DMA_BUF_IOCTL_SYNC`、映射有沒有走快取。這也可能就是 vk 0.45 對 0.86 ms 差異的來源。
- 判準沿用 GL-PRESENT 的工具（`tests/gl_present`）：改動前後各量一次 X3 每幀成本，一樣要 A/A，而且門檻要先凍結。

## 另一條：EGL 不上屏（Chromium／Electron／WebGL）
- **現象**：`/opt/mesa-kgsl` 的 EGL（`platform_x11`，Zink kopper）在 `:3` 每幀只送 1 個 `GetGeometry`，沒有 swapchain，也沒有 Present，視窗一直是黑的。同一個 X3 上，GLX 的 kopper 就正常。
- **第一步（唯讀）**：
  - 讀 Mesa 26.0.6 的 `src/egl/drivers/dri2/platform_x11.c`（`dri2_initialize_x11_kopper`、`dri2_x11_kopper_swap_buffers`），以及 Zink 的 `zink_kopper.c`，找出為什麼 EGL 的 kopper 沒有建立 swapchain。
  - 要比對 Termux 修補 0017：它讓 `dri3_x11_connect` 在拿不到 DRI3 裝置時也回傳 true。
  - 候選環境變數（例如 `LIBGL_KOPPER_DRI2`）只能在 `:3` 上試，**不碰 Stable**。

## 工具（fork `src/f8-ahb-exa-async`，分支 `feat/exa-async-proto-20260923`，**本地、未 push**）
- 相關 commit：`6649316` → `bb45c12` → `5130cf2` → `40a1750` → `8423f0a`。
- 原始碼快照已推到 `evidence/session/gl/gl-present-tools-8423f0a/`。
- 內容：
  - `present_count.so`（上屏呼叫計數）、`req_count.so`（X 協定 request 直方圖）、`px_probe`（root 像素）；
  - `vk_present`、`gl_present_{egl,glx}`（只清畫面的 client，都有 `--offscreen`）；
  - `gl_present_cell.sh`、`gl_present_judge.py`（`--self-test`，18 個情境）、`gl_present_cellcheck.py`；
  - chain 在 `evidence/session/gl/gl-present-chain.sh`（用 `GLP_DIR` 指定輸出目錄）。

## 本輪新陷阱（都有記憶檔）
- **裝置 run 前要先驗完，跑的時候逐 cell 檢查**（使用者要求）：判定器要先在真實 cell 上重播過；新的 shell 函式要先用真的 adb 呼叫過；chain 每個 cell 做完檢查，不過就停。01 和 02 就是因為沒這樣做，白燒了兩次 15 分鐘。
- **Wi-Fi 漫遊會關掉無線偵錯**：家裡同一個 SSID 有兩台 BSSID，手機每 10–15 秒切換一次，`AdbDebuggingManager` 每次都會關掉 adbwifi。另外手機曾經「忘記配對」，要重新 `adb pair`。
  `adb_find.py` 掃到的埠可能是假陽性（對本機 IP 掃描時 TCP 自己連到自己）。5038 server 的 log 已刪但 fd 還開著，要讀 `/proc/<pid>/fd/2`。
- **實驗版的 X root 現在是 1200×2464**，不是 GL-BENCH 那時的 2416。runner 的 `EXPECT_ROOT` 要跟著改。
- **LD_PRELOAD shim 必須連結它包裝的函式庫**：glvnd 和 Vulkan loader 用 `RTLD_LOCAL` 載入驅動，否則 `dlsym(RTLD_NEXT)` 會回傳 NULL，接著 SIGSEGV。
- libxcb 自己的 core request 不經過 PLT，所以要在 libc 的 `writev`／`sendmsg` 那一層解析才看得到。
- Zink kopper 在 `MakeCurrent` 時就建立 swapchain，會產生匯入但不會 present。`vk_present --offscreen` 根本不連 X。

## Fork 與 Stable
- Stable `:1` 全程沒碰：pid 29603，`1.03.01-11b82d9-06.09.26`，每個 cell 前後都相同。
- 實驗版仍是 `f592241`。
- 每個 X3 都用確切 pid SIGTERM 結束（construction，記錄在各 cell 的 `x-end.txt`）。
