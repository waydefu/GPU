# X3-DIRECT-FEAS-02 — 凍結（跑之前寫）

FEAS-01 判決 `DMABUF_IMPORT_UNAVAILABLE`（EGL 不收 dma-buf；GL memory object 匯入後無法綁定）。
FEAS-01 的資訊行顯示系統 Vulkan（Adreno 專有驅動）有 `VK_EXT_external_memory_dma_buf`，而且匯入配置成功。
本探測問：**renderer 能不能用系統 Vulkan 把 client 的 dma-buf 用 GPU 複製進 AHB**（X3 root 用的同一種 AHB），完全不經 CPU 逐像素。
這仍是能力探測；時間數字只是資訊，不進判決。

## 受測物
- 探針 `vk_dmabuf_to_ahb_probe.c`（bionic；dlopen 系統 `libvulkan.so`、`libEGL.so`、`libGLESv2.so`、`libnativewindow.so`）。
- 來源：`/dev/dma_heap/system` 的 dma-buf，LINEAR，1200×128，pitch 4864（跟 Turnip 相同）。
- 目的：AHB `R8G8B8X8_UNORM`，usage `CPU_READ_OFTEN|CPU_WRITE_OFTEN|GPU_SAMPLED_IMAGE|GPU_FRAMEBUFFER`，
  與 `buffer.c` 配置 root／pixmap AHB 的參數相同。
- 複製：`vkCmdCopyBufferToImage`，`bufferRowLength = 4864/4`（任意 pitch 都能用），原始位元組照搬，
  和 X3 現在 CPU memcpy 進 root 的語意相同（root 本來就是「BGRX 位元組放在 RGBX AHB 裡」）。

## 判讀規則（先定）
| 項目 | 成立條件 |
|---|---|
| CPY | Vulkan 匯入 dma-buf（VkBuffer）與 AHB（VkImage）、提交複製、fence 等到，全部 `VK_SUCCESS` |
| PIX_CPU | 用 `AHardwareBuffer_lock` 讀 AHB（X3 讀 root 的方式），每個像素 4 個位元組和 dma-buf 完全相等 |
| PIX_GL | 用 EGLImage（`EGL_NATIVE_BUFFER_ANDROID`，renderer 的方式）取樣 AHB，RGB 三個位元組完全相等（X 通道取樣成 255） |
| LIVE | CPU 改寫 dma-buf 後重送同一個 command buffer，PIX_CPU 看到新內容 |
| C1（應該紅） | AHB 先清成 0，送一個「沒有複製指令」的 command buffer，PIX_CPU 必須不相等（mismatch > 0） |
| C2（應該紅） | 比對器拿錯誤圖樣比，mismatch 必須 > 0 |
| C3（應該紅） | memfd 當 dma-buf 匯入（`vkGetMemoryFdPropertiesKHR` 或配置）必須失敗 |

## 結論對應
- CPY＋PIX_CPU＋PIX_GL＋LIVE 全成立，C1／C2／C3 都紅 → **`VK_DMABUF_GPU_COPY_OK`**：方向「renderer 用 Vulkan 做 dma-buf → AHB 的 GPU 複製」可行（不是零複製，但沒有 CPU 逐像素）。
- CPY 失敗或任一 PIX 不成立 → **`VK_DMABUF_GPU_COPY_FAIL`**（記下是哪一步）。
- 任一對照組沒紅 → **`PROBE_INVALID`**。

## 資訊（不進判決）
- 1200×2464（12 MB）整張：CPU memcpy（dma-buf mmap → AHB lock，模仿 X3 現在的路）對 Vulkan 提交＋等待的牆鐘與本執行緒 CPU 時間，各 20 次取中位數。
  探針在 PRoot 內被追蹤：Vulkan 路徑的 ioctl 會多付追蹤成本，memcpy 路徑沒有 syscall，所以這組數字**偏袒 CPU 路徑**。

## 限制
- 同一個 process 內做完，沒有跨 process（renderer 在 app process，client 在 PRoot）；跨 app 傳 fd 是現有路徑，但這次沒驗。
- 沒有接進 renderer 的 GL 畫面迴圈，也沒有處理 Vulkan↔GL 的同步（sync fd）；這裡用 fence 等完再讀。
