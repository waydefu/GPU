# X3-DIRECT-FEAS-01 — 凍結（跑之前寫）

目的：主線 #3（X3 端）方向 (a) 的前提——**Android 系統 EGL（lorie renderer 用的那個）能不能把 client 的 dma-buf 直接當貼圖取樣（零複製）**。
這是能力探測，不是效能判決；沒有門檻數字，只有「是／否」與逐像素完全相等。

## 受測物
- 探針 `egl_dmabuf_probe.c`（bionic，dlopen `/system/lib64/libEGL.so`、`libGLESv2.so`；不連 X、不碰 app、不碰 Stable）。
- dma-buf 來源：`/dev/dma_heap/system`——和 Turnip KGSL 分配可分享 BO 的來源相同（`tu_knl_kgsl.cc` `bo_init_new_dmaheap`；本機 `/dev/ion` 不存在）。
- 版面照 X3 實際收到的：LINEAR、32 bpp、1200×128、pitch 4864（Turnip 1200 px 的 stride）。

## 判讀規則（先定）
| 項目 | 成立條件 |
|---|---|
| IMP | `eglCreateImageKHR(EGL_LINUX_DMA_BUF_EXT)` 回傳非 NULL，且 `glEGLImageTargetTexture2DOES` 無 GL error |
| PIX | 取樣結果和 CPU 寫入的位元組**每個像素完全相等**（依 fourcc 換算通道；`mismatch=0`，另報上下翻轉版本） |
| LIVE | 匯入後 CPU 改寫 buffer，不重新匯入就能取樣到新內容（`mismatch_vs_new=0`）→ 真零複製；若仍是舊內容 → 匯入時複製（不算零複製） |
| C1（應該紅） | memfd（不是 dma-buf）匯入**必須失敗**；若成功，IMP 的「成功」不具鑑別力，整個探針 INVALID |
| C2（應該紅） | 比對器拿錯誤圖樣比，`mismatch` 必須 > 0；否則比對器無效，整個探針 INVALID |

## 結論對應
- 任一 fourcc 在 XR24 或 AR24（X3 收到的 depth 24／32 格式）上 IMP＋PIX＋LIVE 全成立，且 C1、C2 都紅 → **`DMABUF_IMPORT_ZERO_COPY`**：方向 (a) 可行。
- IMP 成立但 LIVE 不成立 → **`DMABUF_IMPORT_COPIES`**：可行但不是零複製。
- XR24／AR24 都 IMP 失敗 → **`DMABUF_IMPORT_UNAVAILABLE`**：方向 (a) 要走別條路（Vulkan、AHB 反向等）。
- C1 或 C2 沒紅 → **`PROBE_INVALID`**。
- VK／AHB 兩行只是資訊，不進結論。

## 限制（先寫明）
- 探針跑在 PRoot 內（被追蹤、com.termux 的 SELinux domain），renderer 實際跑在 `com.waydefu.x11gpu` 的 app domain。EGL 驅動行為相同；跨 app 傳 fd 已是現有路徑（AHB handle 就是這樣送的），但**這次沒有驗證跨 process**。
- 只測 system heap 直接分配的 buffer，不是真的 Turnip 匯出的 buffer（同一個 heap、同一種 fd）。
