# X3-DIRECT-FEAS-01..03 — 主線 #3（X3 端）可行性調查結果（2026-09-26）

接續 `HANDOFF-NEXT-SESSION-20260926-GL.md`「主線 #3（X3 端）下一步」。這一輪**只讀產品碼**，沒有改產品、沒有碰 X3、沒有碰實驗 app 或 Stable。
裝置探測用的是獨立的 bionic 探針，直接呼叫系統的 EGL／GLES／Vulkan，在 PRoot 內執行。判讀規則在每次執行前都已凍結，凍結檔的時間都早於執行時間，雜湊記在 `x3-direct-feas/sha256-before-run.txt`。

## 一句話
- **不能零複製**：Android 的 EGL 不收 dma-buf，GLES 的 memory object 匯入後也綁不上去。所以 renderer 沒辦法直接把 client 的 dma-buf 當貼圖用。
- **可以用 GPU 複製**：系統 Vulkan（Adreno 專有驅動）能匯入 client 的 dma-buf，用 GPU 複製進 X3 用的那種 AHB，逐像素完全正確（`VK_DMABUF_GPU_COPY_OK`）。
- 缺點：驅動要求多 5300 bytes，dma-buf 剛好大小時，最後 1–2 列要用 CPU 補。
- **收益不大**：全螢幕每幀 X3 的 CPU 大約從 0.8–1.9 ms 降到約 0.3 ms，但 GPU 每幀要多做約 1.2 ms 的複製。

## 原始碼事實（產品 `f592241`，fork worktree `src/f8-ahb-exa-async`）
| 事實 | 位置 |
|---|---|
| DRI3 匯入的 LINEAR buffer 會被包成 `LORIEBUFFER_FD`，也就是 mmap 出來的 CPU 記憶體 | `InitOutput.c:4354`（`loriePixmapFromFds`）、`buffer.c:151` |
| GPU present copy 會先要求來源「可以當 AHB 取樣」，FD 型別回 NULL，所以一律退回 CPU 的 `present_copy_region` | `InitOutput.c:1839`（`lorieTryScheduleGpuBlit`）、`:232`（`lorieEnsureGpuSampleable`）、`:1622` 註解 |
| flip 的尺寸判斷寫成 `root.width != pixmap.height`，只有正方形的 root 才可能 flip。**上游也有這個 bug**（`upstream/.../InitOutput.c:1028`） | `InitOutput.c:4101` |
| 匯入的 FD 預設不 flip；就算用 `TERMUX_X11_FORCE_FLIP=1`，renderer 對 FD 型別每幀仍是 `glTexSubImage2D` 從 mmap 上傳，**複製只是從 X 主執行緒搬到 renderer**，沒有消失 | `InitOutput.c:4105-4107`、`buffer.c:674-675` |
| X3 **早就支援** client 直接交 AHB：DRI3 modifier 1255／1256（`AHARDWAREBUFFER_SOCKET_FD`），收到的是 `LORIEBUFFER_AHARDWAREBUFFER`，可以走 GPU present copy，修好尺寸判斷之後也能零複製 flip | `InitOutput.c:4340-4390` |
| root 是持續 lock 的，imported FD 的 lock 只回傳 mmap 位址，所以每幀沒有 AHB lock 的成本 | `InitOutput.c:4236-4294`、`buffer.c:429` |

## 裝置探測
| attempt | 問題 | 判決 |
|---|---|---|
| **FEAS-01** | 系統 EGL 能不能直接匯入 dma-buf（`EGL_LINUX_DMA_BUF_EXT`） | **`DMABUF_IMPORT_UNAVAILABLE`**：extension 字串裡沒有；XR24／AR24／XB24／AB24 × EXT／2D 八種組合全回 `EGL_BAD_MATCH`。C1 memfd 對照組也回同一個錯誤，表示驅動根本沒看 fd 就拒絕了。C2 沒有執行，因為沒有任何影像可以比對。 |
| FEAS-01 診斷 | 驅動到底認不認得這個 target | 未知 target 回 `EGL_BAD_PARAMETER`，dma-buf target 回 `EGL_BAD_MATCH`，所以驅動認得這個 token，但 pitch、寬度、modifier 怎麼換都拒絕。另外 `GL_EXT_memory_object_fd` 有提供：dma-buf 當 opaque fd 匯入**不報錯**（memfd 對照組被拒，`0x502`），但 `glBufferStorageMemEXT`／`glTexStorageMem2DEXT` 在 10 種組合（尺寸、dedicated、linear／optimal、寬度＝pitch/4）下全回 `GL_INVALID_VALUE`，所以用不了。 |
| **FEAS-02** | 系統 Vulkan：dma-buf → VkBuffer → GPU 複製進 AHB | **`VK_DMABUF_GPU_COPY_FAIL`**（凍結）：停在匯入。dma-buf 是 622592 bytes，但 VkBuffer 要 627892 bytes。 |
| FEAS-02 診斷 | 為什麼多要 | Adreno 對**帶 external-memory 資訊**的 buffer／linear image 固定要求 **size + 5300 bytes**；一般 buffer 剛好等於 size。linear image 的 rowPitch 是 64 bytes 對齊（1200 px 是 4800；寬度 1216 時是 4864，等於 Turnip 的 pitch）。 |
| **FEAS-03** | 繞過 +5300：S＝有餘裕，整張 GPU 複製；T＝剛好大小，GPU 複製前 R 列、CPU 補尾巴 | **`VK_DMABUF_GPU_COPY_OK`**：S 和 T 的 PIX_CPU、PIX_GL 都是 0／153600 不相符，LIVE（v=1，有 sync）也是 0。C1（沒複製）153600 不相符，C2（錯圖樣）153600，C3（memfd）回 `-3`，三個對照組都紅了。T 在 1200×128 時 GPU 複製 126 列、CPU 補 2 列；在 1200×2464 時是 2462 列加 2 列，逐像素 0 不相符。 |

資訊（不進判決）：
- O（硬綁 req 比配置大的整張 buffer，違反規格）實際上也能用，但**不採用**。
- 沒有 `DMA_BUF_IOCTL_SYNC` 的 v=2 也對。X3 現在讀 client buffer 時本來就沒有 sync。
- 系統 Vulkan 沒有 `VK_EXT_image_drm_format_modifier`，所以沒辦法用 VkImage 明確指定 pitch。改用 VkBuffer 加 `bufferRowLength`，任意 pitch 都能複製。
- `AHardwareBuffer_createFromHandle` 在 `libnativewindow.so` 裡找得到符號，但要偽造 QTI gralloc handle，**不列入考慮**。

## 數字（資訊；1200×2464 整張，12 MB；PRoot 內被追蹤，Vulkan 的 ioctl 會多付追蹤成本，所以**偏袒 CPU 路徑**）
| 項目 | 中位數 |
|---|---|
| CPU memcpy（dma-buf mmap → 已 lock 的 AHB，模仿 X3 現在的做法），沒有 sync | 0.823 ms，**0.28 ns/px** |
| 同上，有 `DMA_BUF_IOCTL_SYNC` | 牆鐘 0.790 ms，CPU 0.699 ms |
| Vulkan：錄指令、submit、等 fence 的 CPU（`vk-timing-diag-01.txt`） | 0.032 + 0.217 + 0.029 ≈ **0.28 ms**；fence 等待會睡，不空轉。改用 poll 是 0.34 ms |
| Vulkan：尾巴 2 列 CPU（AHB 已 lock） | 0.002 ms |
| Vulkan：GPU 執行時間（timestamp） | **1.19 ms** |
| 參考：12 MB AHB 做一次 lock＋unlock | CPU 0.106 ms，牆鐘 0.228 ms。FEAS-03 的計時表每幀都付了這個加上 12 MB 的 sync，所以那張表的 0.63 ms 高估了 |

和 GL-PRESENT 對照：GL-PRESENT-01～03 量到 X3 實際每像素 0.22–0.64 ns，比這裡的純 memcpy（0.28）慢到 2.3 倍。**原因還沒查**，可能是 pixman 的路徑，也可能是 X3 主執行緒被排在小核上。

## 對主線 #3 三個方向的結論
- **(a) renderer 直接匯入 client 的 dma-buf**：零複製**不可行**（EGL、GLES 都不收）。改用系統 Vulkan 做 GPU 複製**可行**（FEAS-03），但它不是零複製，而且 renderer 要多開一個 Vulkan device。
- **(b) 讓匯入的 buffer 可以 flip**：對 dma-buf client **沒有幫助**，因為 renderer 對 FD 只能 CPU 上傳。尺寸判斷的 bug 是真的（上游也有），修掉之後**只對 AHB client（modifier 1255）**有零複製 flip 的效果。
- **(c) 讓 CPU 複製變便宜**：純 memcpy 已經接近記憶體頻寬。可以撈回的空間在 X3 實測和純 memcpy 之間，最多約 2 倍，但原因未查。

## 收益估算（外推，不是量測）
全螢幕 1200×2464（2.96 Mpx）時：
- 現在 X3 每幀約 0.82 ms（純 memcpy 的速率）到 1.9 ms（GL-PRESENT-03 的速率）。60 fps 時約 0.05–0.11 核，120 fps 時約 0.10–0.23 核。
- 換成 Vulkan GPU 複製後，每幀約 0.3 ms CPU，60 fps 時約 0.02 核，而且 X 主執行緒每幀少卡 0.8–1.9 ms。
- **代價**：GPU 每幀多 1.2 ms 的複製。在 120 fps（每幀 8.3 ms）下約占 14% 的 GPU 時間，GPU 吃重的程式會掉幀。
- 小視窗不划算。submit 的固定成本約 0.25 ms，視窗小於約 0.5–1 Mpx 時，GPU 路徑的 CPU 反而比 memcpy 多。

## 需要使用者決定
1. **做 X3 端 Vulkan GPU 複製原型**：這次已證明可行。工作量大，要動 renderer：Vulkan device、跨 process 傳 fd、完成通知接 Present、生命週期。收益如上，不是零複製。
2. **先做便宜的 (c)**：查 X3 的複製為什麼比純 memcpy 慢 1.1–2.3 倍，順便解 handoff 裡「0.45 對 0.86 ms」那個未解的差異。以量測為主，風險低。
3. **回頭做 client 端 AHB（modifier 1255）**：這是唯一的真零複製加 flip，但要改 Mesa WSI，還要一個 Android 端的 AHB 配置 helper。09-26 已決定不做。
4. **主線 #3 暫停，先做「EGL 不上屏」**。

## 限制
- 探針全在同一個 process、PRoot 內（com.termux 的 domain、被追蹤）。renderer 實際在 `com.waydefu.x11gpu` 的 app process；跨 app 傳 fd 是現有路徑（AHB handle 就是這樣送的），但**這次沒有驗證**。
- dma-buf 是探針自己從 `/dev/dma_heap/system` 配的，跟 Turnip 配 shareable BO 用同一個 heap（`tu_knl_kgsl.cc` `bo_init_new_dmaheap`），但不是真的 Turnip 匯出的 buffer。
- 沒有接進 renderer 的畫面迴圈。Vulkan↔GL 是用 fence 等完再讀，沒有 sync fd；GL 端沒有 `GL_EXT_semaphore_fd`，要走 `EGL_ANDROID_native_fence_sync`，這條也還沒驗。

## 檔案（`evidence/session/gl/x3-direct-feas/`）
- 凍結檔：`X3-DIRECT-FEAS-0{1,2,3}-FREEZE.md`。
- 探針：`egl_dmabuf_probe.c`（01）、`egl_dmabuf_diag.c`、`egl_dmabuf_diag2.c`（01 診斷）、`vk_dmabuf_to_ahb_probe.c`（02）、`vk_req_diag.c`（02 診斷）、`vk_dmabuf_split_probe.c`（03）、`vk_timing_diag.c`（03 資訊）；`*_body.inc` 是把前一支探針的 `main` 改名後的副本（`sed`）。
- 原始輸出：`run-01.txt`、`diag-01.txt`、`diag-02.txt`、`feas02-run-01.txt`、`vk-req-diag-01.txt`、`feas03-run-01.txt`、`vk-timing-diag-01.txt`，stderr 全部是空的。
- 重現方式（Termux clang 21.1.8，target android24；Vulkan／GLES3 標頭取自 `/root/build/mesa-kgsl/mesa-26.0.6/include`；執行檔只連 libc／libdl，GL／VK 全用 dlopen 載入系統庫）：
  `clang -O2 -Wall -Wno-unused-function -idirafter <inc> -o <probe> <probe>.c -ldl`，執行時 `env -u LD_LIBRARY_PATH -u LD_PRELOAD ./<probe>`。
