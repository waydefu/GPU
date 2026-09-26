# X3-DIRECT-FEAS-03 — 凍結（跑之前寫）

## 前情
- FEAS-02 run-01 判決 **`VK_DMABUF_GPU_COPY_FAIL`**（凍結，不重判）：停在匯入。dma-buf 622592 bytes，
  但綁它的 VkBuffer 要 627892。
- 診斷 `vk-req-diag-01.txt`：Adreno 專有 Vulkan 對**帶 external-memory 資訊的** buffer／linear image 一律要求
  **size + 5300 bytes**（一般 buffer 剛好等於 size）。linear image 的 rowPitch 是 64 bytes 對齊，寬度＝pitch/4 時 rowPitch 等於該 pitch。
- 所以：dma-buf 剛好等於 pitch×高度（Turnip 的 BO 只做 page 對齊，常常沒有 5300 的餘裕）時，
  **任何** binding 都蓋不到最後 5300 bytes（約 1–2 列）。

## 受測（同 FEAS-02 的 buffer 版面與 AHB）
| case | dma-buf 大小 | 做法 | 合規 |
|---|---|---|---|
| **S**（有餘裕） | pitch×H＋8192，page 對齊 | 整張 VkBuffer 綁上，GPU 複製全部列 | 合規 |
| **T**（剛好，分段） | pitch×H，page 對齊（622592，與 FEAS-02 相同） | VkBuffer 只蓋前 R 列（R = 使 `末列結尾 + 5300 ≤ dma-buf 大小` 的最大值），GPU 複製這 R 列；剩下的列用 CPU 從 mmap 複製進 AHB | 合規 |
| O（剛好，硬綁） | pitch×H | allocationSize＝dma-buf 大小，硬綁 req 比它大的整張 buffer | **違反規格**，只當資訊 |

## 判讀規則（先定；PIX／LIVE／C1–C3 定義與 FEAS-02 相同）
- PIX_CPU：AHB CPU lock 讀出，每像素 4 bytes 與 dma-buf 相等；PIX_GL：EGLImage 取樣 RGB 相等。
- LIVE：CPU 改寫 dma-buf（v=1 有 `DMA_BUF_IOCTL_SYNC`；v=2 沒有，後者只當資訊）後重做，PIX_CPU 看到新內容。
- C1（應該紅）：AHB 清 0、送沒有複製的 command buffer → PIX_CPU mismatch > 0。
- C2（應該紅）：比對錯誤圖樣 → mismatch > 0。
- C3（應該紅）：memfd 當 dma-buf 匯入必須失敗。

## 結論對應
- S 和 T 的 PIX_CPU＋PIX_GL＋LIVE(v=1) 都成立，C1／C2／C3 都紅 → **`VK_DMABUF_GPU_COPY_OK`**
  （任何 page 對齊的 client buffer 都能用 GPU 複製；剛好大小時最後 ≤ 2 列要 CPU 補）。
- 只有 S 成立 → **`VK_DMABUF_GPU_COPY_SLACK_ONLY`**。
- S 不成立 → **`VK_DMABUF_GPU_COPY_FAIL`**。
- 任一對照組沒紅 → **`PROBE_INVALID`**。
- O 不進判決。

## 資訊（不進判決）
- 1200×2464 剛好大小（11984896 bytes）：CPU memcpy 整張（X3 現在的做法；有／無 sync）對 T 做法（GPU 前 R 列＋CPU 尾巴），
  各 20 次中位數（牆鐘、本執行緒 CPU、GPU timestamp）。PRoot 內被追蹤，Vulkan 的 ioctl 多付追蹤成本 → **偏袒 CPU 路徑**。

## 限制（同 FEAS-02）
單一 process、沒有跨 app 傳 fd、沒有接進 renderer 的畫面迴圈、Vulkan↔GL 用 fence 等完再讀（沒有 sync fd）。
