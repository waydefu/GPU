# P2-A 深度報告：RENDER Composite SIGSEGV 文獻封版

**P2-A 已 CLOSED（2026-09-08，A.3/A.4）。** 文獻階段把嫌疑指向 fb/pixman pointer／pitch；runtime 後來證明 crash 是 histogram probe double-wrap，那些路徑在 A.3 **根本沒走到**。本檔保留為文獻封版，不再當 open root-cause 文件。裁決見 `evidence/session/p2-a4/GATE-P2-A.md` 與 A.3–A.4e。P2-B.1 census 與 P2-B.2 narrow Over 已完成；下一階段是 **P2-B.3 real-workload performance qualification**，不是再猜 backing。

**日期：** 2026-09-08  
**範圍：** 本檔以 experimental `:3` / fork `f8-exa-solid` `a401b4f` 的當時證據封版；目前 fork 已前進至 `f8-p2-b2-over` `9822435`。文獻與本地釘選源碼對照；**不含**程式修正、`sys_ptr` 捕獲、`PixmapIsOffscreen` 改寫、P2STAGE instrumentation。  
**視覺摘要：** 可在 Cursor 旁開 canvas 閱讀（狀態、嫌疑排名、指標鏈、取證順序）。完整可引用正文以本檔為準。

```
P0  CLOSED
P1  已完成的既有成果保持
P2-A literature/research  CLOSED
P2-A root cause           CLOSED  (probe wrap cycle; 6182b94)
Active blocker: none for P2-A
Next gate at report time: P2-B.1 Composite dispatch + fallback census (completed; see current gates)
Current next gate: P2-B.3 real-workload performance qualification
```

> **一句話裁決（文獻當時）：** 文獻把兇器從「AHB／compositor／探針」移開，指向 EXA CPU fallback → fb/pixman bits 可見性這條窄鏈；但還差一個 runtime pointer snapshot 才能定罪。  
> **一句話裁決（A.3/A.4 之後）：** runtime 定罪的是探針二次安裝造成的 hook 環；fb/pixman 在修好後才第一次走到並回來。文獻對 crash 根因的 pointer/pitch 指向 **已撤回**。

研讀量（本輪封版，不再加源）：40+ 頁面全文或大部、15 次主題檢索約 90 筆掃描、本地釘選 xserver **21.1.24** 與 pixman **0.46.4**。來源分級見文末。

---

## 0. 封版邊界：已封印 vs 未關閉

| 類別 | 狀態 | 內容 |
|---|---|---|
| P0 / P1 / GPU Present / Fence / EXA Copy / EXA Solid | **封印（既有成果）** | 見 `HANDOFF.md`；本報告不重開 |
| 案情基線（Composite 矩陣） | **封印為裁決事實** | 見 §1；不重複論證 |
| 文獻／協議／契約／法醫學 | **P2-A research CLOSED** | 50+ 來源已過飽和點 |
| 根因假設 | **SUPERSEDED** | A.3/A.4 已以 probe double-wrap runtime evidence 關閉；pointer／pitch ranking 只保留作歷史分析 |
| 修法選擇 | **SUPERSEDED / NOT APPLICABLE** | A.3/A.4 已在不改 `sys_ptr`／`PixmapIsOffscreen` 的情況下關閉 P2-A；本檔不再提出修法選擇 |

### 0.1 本輪撤回、不得再封版的原主張

交叉核對公開 Xorg 21.1.x EXA、本地釘選 `ExaDoPrepareAccess`、LLVM Scudo、Android GWP-ASan 後，下列句子**已撤回**。後續章節若與本表衝突，以本表為準。

| 撤回 | 為什麼不能封 |
|---|---|
| `fb_ptr == NULL` ⇒ driver `PrepareAccess` hook 從不被呼叫 | 本地 `ExaDoPrepareAccess` 以 `has_gpu_copy` 決定是否進 hook；`fb_ptr` 只影響**初始** `devPrivate.ptr` 選 `fb_ptr` 還是 `sys_ptr`。見 §2.3。 |
| 1×1 / 5×24 Primary 小塊溢寫「撞 Scudo guard page」 | LLVM：Primary 是 size-class region；**Secondary** 大映射才被 guard pages 包夾。見 §2.8。 |
| `SEGV_ACCERR` 或 fault addr `…ffe0` 是分配器指紋 | ACCERR 只區分「已映射但權限拒絕」vs MAPERR；不識別 owner。見 §2.8。 |
| `android:gwpAsanMode="always"` 跑一次 repro 即可判 heap overflow | `always`＝GWP-ASan **永遠啟用**，仍只 sample 子集；一次 miss 不能排除。見 §2.9、§4。 |
| 「三條免重編驗證路」 | 真正零成本免重編只有 `adb logcat -b crash`。GWP-ASan manifest 與 Sprep/S7a 都要 diagnostic rebuild。見 §4。 |
| GPU MVP 可吃掉桌面 workload「90%+」 | 文獻支持 Over/Src × solid/A8/無 mask × nearest 是合理第一階段；百分比須等 xfwm histogram。見 §2.2。 |
| 立刻在 (a) `ModifyPixmapHeader` 捕獲進 `sys_ptr` 與 (b) `PixmapIsOffscreen` 僅在有 GPU copy 時為真 之間二選一 | 二者互斥；須等 Sprep。見 §4。 |

---

## 1. 本案基線（裁決事實，不重複論證）

來源：`evidence/session/composite-matrix/`（`run.txt`、`PROVENANCE.txt`）、`evidence/session/flight/`、`HANDOFF.md`。每格 3/3、無 xfwm、fresh `:3`。

- `RENDER 138.8 Composite` 進 handler 即 `SIGSEGV` **code 2 (`SEGV_ACCERR`)**。
- Flight last request：phase **ENTER**（死在 handler，不是 LEAVE 之後）。最小 repro `patches/p_render_last.c` mode `1x1` 與 xfwm `--compositor=off` 同一 last opcode。
- Backing RR / AR / RA / AA、尺寸 1×1 / 5×24、op **Src / Over / Clear 全滅**；dst 為 pixmap 或 window **全滅**。
- 唯一活口：真 no-op **`PictOpDst`**（`1x1-aa-dst` 3/3 PASS）。
- Solid-fill source 也死。`DISABLE_EXA_GPU` 也死。
- `PrepareComposite = FalseNoop`：死的是 **software / EXA fallback Composite**，不是未實作的 GPU Composite op。
- 對照（已隔離、非本殺手）：同一 1×1 的 DRI3 convert／register／Solid／Copy **3/3 PASS**。

典型 fault addr（default logcat，**未經** `-b crash`）：

| 現場 | fault addr | 備註 |
|---|---|---|
| Gate 2 xfwm compositor-off | `0x6f64d3ffe0` | 頁對齊附近 |
| 1×1 repro（flight） | `0x7525826ff8` | 非 `ffe0` |
| xfwm flight window | `0x70c140dff8` | 非 `ffe0` |
| composite-matrix Clear | `0x7840156ff8` | 非 `ffe0` |

`…ffe0` **有時**出現，不是穩定指紋；不得單獨用來指定分配器。見 §8。

以上 `PrepareComposite=FalseNoop`、GPU Composite **未實作** 與 histogram 未收集，都是本報告所封版的 pre-A.3/pre-B.2 歷史狀態。後續 P2-B.2 已加入窄 Over GPU slice 並通過 R3 exact oracle；mask、two-pass、transform、bilinear、repeat、componentAlpha 等其餘 cases 仍屬 software。

---

## 2. 各領域學到什麼

### 2.1 Render 協議（Keith Packard + 官方 spec）

Packard USENIX 論文與 `renderproto.txt`（v0.11）定義：

```text
dest = (source IN mask) OP dest
```

mask 為 None 時等同常數 alpha 1。本案 repro（`mask=None`）是**合法最小式**，不是畸形請求。

XCB Render API 的 op 編號：Clear=0、Src=1、Dst=2、Over=3。與 flight `head` 位元組（Over=`03`、Src=`01`）及解碼器一致，解碼器可信。

Composite 的官方 workload 維度：目標矩形、repeat（None/Normal/Pad/Reflect）、filter、transform、componentAlpha。histogram 探針記錄的正是這些維度；探針設計有 spec 背書。尚未收集到的是 **xfwm 真實分佈**，不是維度清單。

### 2.2 真實 workload（第二未知數的上界，不是百分比）

不必等 histogram 也能定 **hot-path 上界**（文獻支持方向，**不**支持覆蓋率數字）：

- **Xft** man：文字走 `CompositeGlyphs`；src 是單色 solid（`XftDrawSrcPicture` 由顏色產生）、mask 是 a8/a1 glyph、op 為 Over。文字 = 大量小尺寸 `Over + solid src + alpha mask`。
- **cairo**：預設 operator 為 `OVER`（`cairo.h`）；Xlib 後端把 drawing 送進 server 端 XRender。GTK App 以 Over 為主、偶發 Src。
- **picom**：依賴 composite、damage、xfixes、shape、render、randr、present、glx + pixman。compositor workload ≈ RedirectSubwindows + NameWindowPixmap + Damage + 每幀 Over（全屏或損傷區）。
- **xfwm4 `compositor.c`**：CWindow 逐窗存 picture／shadow／alphaPict；gaussian 陰影（`SHADOW_RADIUS 12`）；XComposite + XDamage + XRender，可選 Present/GLX。啟動瞬間 = 建影子圖 + 全窗 Over，尺寸從圖示到全屏——與 flight 的 `5×24 nearest` 同一**形狀類**，不是同一請求。

複雜度在 mask 種類（a8 glyph、componentAlpha 次像素文字）、transform + filter、尺寸跨度（1×1～全屏），**不在**奇特 op。

**GPU MVP 第一階段（文獻支持，待 histogram 定量）：**

```text
Over / Src
  × solid / A8 mask / no-mask
  × nearest
```

預期覆蓋主要桌面 hot path（Cairo 預設 OVER、Xft CompositeGlyphs、xfwm4 compositor）。**實際 coverage 百分比由 xfwm histogram 定量。** 不得寫 90%+。

### 2.3 EXA 契約（保留）與 `ExaDoPrepareAccess` 控制流（已修正）

#### 契約（`exa.h` doxygen；本地釘選與公開註解一致）

`PrepareAccess`（`src/upstream/lorie/src/main/cpp/xserver/exa/exa.h`）：

- CPU 存取 offscreen pixmap 前呼叫。
- 可用來調整 `devPrivate.ptr`（不同 aperture／untiling／byteswap）。
- **可以失敗**；失敗則 EXA 把 pixmap 遷到系統記憶體。
- **screen pixmap 不可失敗**（可見畫面不能遷移）。

`PixmapIsOffscreen`（同檔）：

- 可選，用來取代 `exaPixmapHasGpuCopy()`。
- `TRUE` 表示 drawable **在 framebuffer memory**，意味著可能被加速，且 CPU 存取時**需要 Prepare/Finish 包裹**。

契約本身正確，繼續作為 #1 嫌疑的文件背書。

#### 控制流：本地 xserver 21.1.24 核對結果

釘選樹：`src/upstream/lorie/src/main/cpp/xserver/meson.build` → `version: '21.1.24'`。  
函式：`exa.c` **`ExaDoPrepareAccess`**。

**確認：原主張「`fb_ptr == NULL` ⇒ 不呼叫 driver hook」與本地源碼矛盾。本報告採用修正後控制流。**

實際順序（摘要，非逐字抄錄）：

1. 若 `EXA_OFFSCREEN_PIXMAPS` 未設 → `FALSE`。
2. 巢狀／重複：同一 pixmap 已在 `access[]` → 只加 count、回傳**快取的** `retval`（不再重設 ptr、不再重入 hook）。
3. 預期此時 `devPrivate.ptr == NULL`（非 NULL 則 debug fatal）。
4. `has_gpu_copy = exaPixmapHasGpuCopy(pPixmap)`。
5. **初始指標選擇（注意：這一步不是 hook 門檻）：**
   - `has_gpu_copy && pExaPixmap->fb_ptr` → `devPrivate.ptr = fb_ptr`，`ret = TRUE`
   - **否則** → `devPrivate.ptr = sys_ptr`，`ret = FALSE`
6. 記錄 `access[index]`。
7. **`if (!has_gpu_copy) goto out;`** ← 這才是跳過 driver hook 的條件。
8. `exaWaitSync`。
9. `PrepareAccess == NULL` → `goto out`（沿用步驟 5 的 ptr／ret）。
10. AUX 且驅動不支援 → 可能 `exaMoveOutPixmap`，`ret = FALSE`。
11. **呼叫** `(*PrepareAccess)(pPixmap, index)`。失敗則 move-out，`ret = FALSE`；成功則 `ret = TRUE`。
12. `access[index].retval = ret` 並回傳。

因此：

```text
if has_gpu_copy && fb_ptr:
    devPrivate.ptr = fb_ptr
else:
    devPrivate.ptr = sys_ptr
if !has_gpu_copy:
    return fallback/system path          # 不呼叫 hook
if driver PrepareAccess exists:
    call driver PrepareAccess()          # 可覆寫 devPrivate.ptr
```

**`fb_ptr == NULL` 本身不會阻止 hook**，只要 `has_gpu_copy == true`。

`exaFinishAccess`（同檔）在 count 歸零時把 `devPrivate.ptr` 設回 `NULL`；僅當當初 Prepare **成功**（`retval`）才呼叫 driver `FinishAccess`。

Driver scheme 選擇（同檔 `exaDriverInit`）：`EXA_OFFSCREEN_PIXMAPS | EXA_HANDLES_PIXMAPS` 且**無** `EXA_MIXED_PIXMAPS` → `exaPixmapHasGpuCopy = exaPixmapHasGpuCopy_driver`、`ModifyPixmapHeader = exaModifyPixmapHeader_driver`、`prepare_access_reg = NULL`。

`exaPixmapHasGpuCopy_driver`（`exa_driver.c`）暫時把 `devPrivate.ptr` 設成 `ExaGetPixmapAddress`，再問 driver `PixmapIsOffscreen()`。

本 fork 驅動（`src/f8-ahb/lorie/src/main/cpp/lorie/InitOutput.c`）：

```c
.flags = EXA_OFFSCREEN_PIXMAPS | EXA_HANDLES_PIXMAPS,
.PrepareComposite = FalseNoop,
.PixmapIsOffscreen = TrueNoop,
.PrepareAccess = loriePrepareAccess,
.FinishAccess = lorieFinishAccess,
.ModifyPixmapHeader = lorieModifyPixmapHeader,
```

`TrueNoop` 恆回 `TRUE` ⇒ **靜態上** `has_gpu_copy` 應對此 driver scheme 的 pixmap 為真 ⇒ **靜態上 hook 應被呼叫**。這與「hook 因 `fb_ptr==NULL` 沒跑」相反，是撤回該句的第二個獨立理由。

`exaCreatePixmap_driver` 把 `fb_ptr = NULL`、`sys_ptr = NULL`，再 `ModifyPixmapHeader(..., NULL)`。「Allow ModifyPixmapHeader to set sys_ptr appropriately.」

`exaModifyPixmapHeader_driver`：`pPixData` 非 NULL 則寫入 `sys_ptr`／`sys_pitch`；若 driver `ModifyPixmapHeader` 在 `pPixData==NULL` 時仍留下非 NULL 的 `devPrivate.ptr` 與 `devKind`，則捕獲為 `sys_ptr`／`sys_pitch`。結束時 **一律** `devPrivate.ptr = NULL`。

`lorieModifyPixmapHeader`：僅當 `data` 非 NULL 時寫入 `priv->mem`，**回傳 FALSE**。不填 EXA `sys_ptr`，也不填 `fb_ptr`。

`loriePrepareAccess`：必要時 `LorieBuffer_lock`，然後

```c
pPix->devPrivate.ptr = priv->locked ?: priv->mem;
return TRUE;
```

**不更新 `devKind`。** lock 失敗回 `FALSE`（EXA 可 move-out）。

靜態能說的是：EXA 帳本、`has_gpu_copy`、`fb_ptr`／`sys_ptr` 初值、hook、hook 後 `devPrivate.ptr`、`devKind` 必須自洽，否則 `fbGetPixmapBitsData` 會把壞的 `(bits, stride)` 交給 pixman。靜態**不能**說 hook 沒跑，也不能在沒有 snapshot 時選定修法。

#### 未解矛盾（誠實保留，Sprep 必須回答）

`GetImage` 同樣經 `ExaCheckGetImage` → `exaPrepareAccess` → **同一個** `ExaDoPrepareAccess`（driver scheme 的 `prepare_access_reg` 為 NULL，與 Composite fallback 相同）。GetImage 在既有 P0/P1 證據上存活，Composite 全滅。可能解釋（皆未證實）：

- 某些 pixmap 路徑上 `sys_ptr`／`priv->mem` 已被 `ModifyPixmapHeader` 捕獲，GetImage 剛好打到那些物件；
- Composite 同時 Prepare src+dst（solid src 則 dst 為主），幾何／pitch 組合不同；
- 巢狀 `access[]` 快取 retval、未重設 ptr；
- GetImage 走的 pixmap 與 Render picture 的 backing 不是同一份 CPU 可見狀態。

這是 OPEN 項，不是文獻能關閉的。

### 2.4 fb／pixman（死亡現場）

釘選：xserver `fb/fbpict.c`、`fb/fb.h`；pixman **0.46.4**（`pixman/meson.build`）。

`fbComposite`：三次 `image_from_pict`，然後

```c
if (src && dest && !(pMask && !mask)) {
    pixman_image_composite(...);
}
```

NULL image **不會**進 composite（直接 skip + `free_pixman_pict`）。因此「`pixman_image_create_bits` 回 NULL 後解引用」作為**單獨**死因偏弱——至少 `fbComposite` 這層有 guard。剩餘死點：`create_bits_picture`／`image_from_pict` 內部、`pixman_image_composite` 內部、`FinishAccess`／lifetime（guard 過了之後）。

`create_bits_picture`：

```c
fbGetPixmapBitsData(pixmap, bits, stride, bpp);
image = pixman_image_create_bits(..., (uint32_t *) bits, stride * sizeof(FbStride));
```

`fbGetPixmapBitsData`（`fb.h`）：

```c
(pointer) = (FbBits *) (pixmap)->devPrivate.ptr;
(stride)  = ((int) (pixmap)->devKind) / sizeof(FbBits);
```

與 §2.3 的供給鏈銜接：`devPrivate.ptr` + `devKind` → pixman `(bits, rowstride_bytes)`。

pixman `_pixman_bits_image_init` / `pixman_image_create_bits`（`pixman-bits-image.c`）：

- 註解：「If bits is NULL, a buffer will be allocated and initialized to 0」——`bits==NULL` **自己配置，不死**。
- `rowstride_bytes` 必須對齊；`return_val_if_fail` 失敗回 NULL。
- Søren Sandmann（xorg-devel，2011）：回 NULL 幾乎總是因為**傳入參數錯誤**。對應「`devKind`／stride 與 bits 不自洽」的病徵，但 NULL 回傳本身被 `fbComposite` 擋下。

`PIXMAN_OP_DST` 在 `pixman-noop.c` 註冊為 `noop_composite`。這比「Dst 碰巧沒碰 bits」更硬：官方 fast path 對 Dst **刻意 no-op**。與「唯一活口是 Dst、碰像素的 op 全死」相容，且同時支持「真正碰 bits 才炸」——仍不指定哪一個 `(bits,stride)` 錯。

### 2.5 AHardwareBuffer（NDK + AOSP）

- allocate 時 **忽略** 呼叫端 `stride`；真值只能 `AHardwareBuffer_describe`。本案 1×1 出現 `Sent shared buffer width 1 stride 64 height 1` 與「allocator 決定 stride」一致；先前排除「allocate stride 填錯」是對的。
- lock：fence 為負時，**呼叫者負責保證 producer 寫入已完成**。與創建 usage 不相容的 lock＝未定義，**可含程序終止**。
- Ensure-time lock 永不 unlock、同時 renderer GPU 持續寫同一 buffer：官方未定義。  
  **`DISABLE_EXA_GPU` 3/3 仍死** → 本條降為嫌疑 #4（中），不是當前 #1。GPU 路徑修好前仍必須處理 fence，否則是下一顆雷。

### 2.6 EGL／同步（Khronos）

- Fence sync、`EGL_SYNC_PRIOR_COMMANDS_COMPLETE`：沒 flush 的 `eglClientWaitSync` 可能**永遠等**。`DoneCopy` 2000ms 超時 + log 作為逃生口，設計方向正確。
- Khronos issue **#566**（EGLImage 跨 context 可見性）：上游承認 producer/consumer 快取可見性語義模糊。支持「CPU/GPU 並行、無明確同步是高風險」——用於未來 GPU 路，不解釋 `DISABLE_EXA_GPU` 仍死。
- `EGL_ANDROID_image_native_buffer` + `eglGetNativeClientBufferANDROID`：renderer texture 綁定鏈有 spec 背書，無協議違規可指為本案殺手。

### 2.7 dma-buf／DRI3／Present

- DRI3 = dma-buf ↔ pixmap 互換；`BufferFromPixmap` 契約 `size ≥ height × stride`。P1 讀值（1×1 `nfd=1` stride0=256 mmap OK）符合契約；P1 保持 CLOSED。
- Present：VBLANK + damage 呈現。LWN Present Redirection 討論對應 **未來** xfwm-ON（compositor 直接收 pixmap），不是現在的 1×1 fallback crash。
- 核心 dma-buf：exporter/importer、dma-fence、dma-resv 隱式同步。與已 QUALIFIED 的 Present 等待模型相容；不把 Present 拉回 #1。

### 2.8 `SEGV_ACCERR` 法醫學（修正後）

Linux / AOSP / NDK 一致：

| `si_code` | 含義 |
|---|---|
| `SEGV_MAPERR`（1） | 位址**沒有** mapping（含典型 NULL） |
| `SEGV_ACCERR`（2） | mapping **存在**，權限不允許此次存取 |
| `SEGV_MTESERR` | MTE tag 失敗 |

本案 code 2 ⇒ **fault class = 已映射但 permission denied**。這比純 NULL dereference 更支持「碰到了某塊不可寫／不可讀的 mapping」。  
它**不能**識別：Scudo / jemalloc / AHB mmap / 棧 guard / GWP-ASan / `PROT_NONE` / 壞指標落入他人 mapping。

**MTE 排除：** AOSP 明定 MTE 走 `SEGV_MTESERR`，不是 code 2。

`…ffe0`／`…ff8` 仍**可能**是 protection 邊界（AHB/mmap 尾、`PROT_NONE`、GWP-ASan、棧 guard、Scudo **Secondary**、或其他不可存取 mapping）。**不得**寫成「1×1/5×24 Primary 溢寫撞 Scudo guard」。LLVM Scudo：

- **Primary：** 小配置，從 size-class region 切 block，**不是**每塊外包一圈 guard page。
- **Secondary：** 大映射，**才**由 guard pages 包圍。

嫌疑 #2 的正確名稱見 §3。

### 2.9 Android 取證（流程）

- `tombstoned Permission denied`：HyperOS 政策，無解。不要再卡在這條。
- `debuggerd -b`：AOSP 有 root 要求分支；此環境不通。不必再試。
- **`adb logcat -b crash`：** 官方獨立 crash buffer。既有 runner 只 dump 預設 buffer，**從未讀過它**。debuggerd 輸出進 crash buffer。這是**唯一**零成本、免重編的第一行動；歷史殘留可能仍在。
- Xorg `OsSigHandler`（`os/osinit.c`）：先 `xorg_backtrace()`，再 `FatalError("Caught signal %d... Server aborting")`（約 L135–157）。`os/backtrace.c` 有 libunwind 後端。`meson_options.txt`：`option('libunwind', … value: false)`。崩潰目前進 debuggerd 而非這段 log（原因待查：signal 被 Android 擋、或 Lorie/loader 未走此路徑）。重編時開 libunwind、確認 handler 能寫進 logcat，是 diagnostic rebuild 的一部分，不是免重編。
- `adb bugreport`：免 root、含行程堆疊；適合「活著但卡住」，不適合已死的 X。xfwm-ON 階段標配，不是現在第一槍。

### 2.10 Termux 上游

維護者仍活躍。issue 區有各類 crash，**沒有與本案相同的 Render-Composite-ENTER 即死**。旁證：較像 fork 引入（或上游組合尚未爆發），不是已知上游 bug。`-legacy-drawing`、DRI3/AHB 路徑的官方描述與 P0/P1 結論一致。

探針／flight／`xserver.patch`：Dst 經過探針仍活；Gate 2 早於 flight recorder。排除為 #1。

---

## 3. 修正後嫌疑排名

排名是 **假設強度**，不是已定罪級。#1 仍是 EXA CPU 可見指標鏈，但機制已從「hook 沒跑」改為「狀態不自洽」。

| # | 假設 | 強度 | 依據 | 什麼能推翻 |
|---|---|---|---|---|
| 1 | **EXA CPU-access pointer／pitch 狀態不自洽** | **極高** | `PixmapIsOffscreen=TrueNoop` 可能讓 EXA 視 pixmap 為 GPU-backed；`ExaDoPrepareAccess` 期間 `devPrivate.ptr` 在 `fb_ptr`／`sys_ptr` 與 driver `PrepareAccess` 映射之間切換。若 hook 未正確覆寫 ptr、回傳值與映射狀態不一致、或 `devKind` 未同步到真實 CPU mapping pitch，fb/pixman 得到壞的 `(bits,stride)`。契約 + `fbGetPixmapBitsData` 鏈足以維持 #1。 | Sprep 顯示 ptr+pitch 在進 fb 前完全自洽 → 降級，改看 #2/#3 |
| 2 | **fb/pixman 收到可解析但錯誤的 `(bits, stride, geometry)`，造成越界／protection fault** | **高** | ACCERR、偶發 `…ffe0`、Src/Over/Clear 死而 Dst 活（pixman DST noop）。**不**指定 Scudo Primary。可能來源：AHB/mmap 邊界、`PROT_NONE`、GWP-ASan、棧 guard、Secondary、壞指標。 | GWP-ASan **命中**報告、或 Sprep 證明 stride 與 mapping 一致而仍炸 |
| 3 | **Prepare/FinishAccess lifecycle 或 stale mapping** | **中高** | 靜態上 hook **應該**跑（`TrueNoop` ⇒ `has_gpu_copy`）。核心變成 hook 後 `devPrivate.ptr`、`FinishAccess` 清 ptr、巢狀 count、lock/unlock 不對稱。 | Sprep：`PrepareAccess_called=0`（意外）或 called=1 且 post-hook 狀態乾淨、仍炸 → 看 #2 |
| 4 | **AHB CPU/GPU synchronization misuse** | **中** | NDK：負 fence 時 caller 保證 writes 完成；usage 不符＝UB。Ensure-time lock 永不 unlock + GPU 寫入。**`DISABLE_EXA_GPU` 仍死 ⇒ 不是當前 #1。** GPU 路修復前必須處理。 | 僅 CPU 路徑修好後、開 GPU 又炸 |
| 5 | **pixman image construction failure／次要錯誤路徑** | **低～中** | `fbComposite` 有 src/dest/mask NULL guard；單純 `create_bits` 回 NULL 不足以解釋整體 crash。仍可能有未護住的分支或 composite 內部。 | Sprep 顯示進 pixman 前 bits/stride 合法，fault 在 pixman 內 |

供給鏈（#1 的取證對象）：

```text
EXA bookkeeping
  → has_gpu_copy
  → sys_ptr / fb_ptr 初始選擇
  → PrepareAccess hook
  → devPrivate.ptr（post-hook）
  → devKind
  → fbGetPixmapBitsData
  → pixman
```

---

## 4. 下一步（只記錄計畫；本報告不實作）

**不要改行為。** 不要立刻選原步驟 4 的 (a) `ModifyPixmapHeader` 捕獲進 `sys_ptr`，或 (b) `PixmapIsOffscreen` 只在真有 GPU copy 時為真。二者互斥，等 Sprep。

取證成本（措辭已收斂）：

> **1 條零成本免重編取證 + 2 條低成本 diagnostic rebuild。**

| 順序 | 動作 | 成本 | 目的 |
|---|---|---|---|
| 1 | `adb logcat -b crash -d`（並納入往後 runner） | **零成本、免重編** | 歷史 debuggerd 殘留、往後每 trial 必存 |
| 2a | P2STAGE pointer-transition probe（Sprep + fb 入口） | diagnostic rebuild | 一次 Composite 的完整 ptr 轉換 |
| 2b | 同 rebuild：libunwind + 確認 `Caught signal` 進 logcat | 同上 | 繞過 tombstoned 拿第一幀 |
| 2c | 同 rebuild 或平行 debug APK：`gwpAsanMode="always"` | diagnostic rebuild | 若 **sample 命中**，報告極有價值；miss **不能**排除 heap overflow |
| 3 | 讀到第一個壞 pointer／pitch 狀態 | — | 切 A/B/C/D |
| 4 | **然後**才決定 `sys_ptr` / `PixmapIsOffscreen` / `PrepareAccess` 修法 | 行為變更 | evidence-driven |

```text
1. crash buffer（現在）
   ↓
2. P2STAGE pointer-state probe + libunwind + GWP-ASan
   ↓
3. first bad pointer / pitch state
   ↓
4. THEN decide sys_ptr / PixmapIsOffscreen / PrepareAccess fix
```

### 4.1 P2STAGE 探針（設計；未落地）

Sprep 單行至少：

```text
pix, index, has_gpu_copy, fb_ptr, sys_ptr, sys_pitch, fb_pitch,
dev_ptr_before, devKind_before, PrepareAccess_called, PrepareAccess_ret,
dev_ptr_after, devKind_after, width, height, bpp
```

進 `fbComposite` / `create_bits_picture` 前再印：

```text
src/dst, bits, devKind, pixmap w/h/bpp, stride passed to pixman
```

一次 repro 切四支：

| 支 | 含義 | 下一步 |
|---|---|---|
| A | hook 根本沒跑 | 查 `has_gpu_copy`／`PrepareAccess==NULL`／巢狀快取；**不是**「因為 fb_ptr NULL」這句已撤回的機制 |
| B | hook 有跑，但 `dev_ptr` 仍 NULL／stale | hook 實作、lock 失敗卻回 TRUE、或未覆寫 EXA 初值 |
| C | hook 修好了 ptr，但 `devKind`／pitch 錯 | 同步 AHB describe stride 與 `devKind` |
| D | ptr+pitch 都對 | fault 已在 pixman / FinishAccess / lifetime |

修完 crash 之後（仍屬後續閘門，非本報告）：xfwm OFF frozen → ON → histogram（workload 上界見 §2.2）→ 才做 GPU Composite MVP（Over/Src × solid/A8/無 mask × nearest）。

---

## 5. 來源（50+，分級誠實）

### 全文／大部研讀

renderproto 官方 spec；Keith Packard USENIX Render 論文；DRI3 部落格；LWN〈DRI3 and Present〉；LWN〈DMA buffer sharing〉；核心 dma-buf 文件；NDK AHardwareBuffer 參考（lock / isSupported / Desc）；AOSP `hardware_buffer.h`；AOSP `debuggerd.cpp`；EGL `fence_sync` / native fence / EGLImage / `eglGetNativeClientBufferANDROID` / `eglClientWaitSync` / `eglCreateSync`；ARM 隱式同步；Khronos #566；XCB Render / Present / Composite API；EXA `driver.txt` + man；XQuartz 鏡像 `exa.h` / `fbpict.c`；xfwm4 `compositor.c`；cairo 文件 + Xlib 後端說明；Xft man（多頁）；pixman bits-image 源碼；Xorg man；damageproto；picom README／架構；Perfetto 文件；Android vitals / logcat / bugreport；Android MTE；GWP-ASan；LLVM Scudo（Primary vs Secondary）；freedreno/Turnip 背景；DeepWiki troubleshooting。

### 實質片段

xorg-devel 2011（Sandmann / pixman NULL）；Anholt 部落格；AOSP insider／Mintlify／NDK crash 文件；Meta／Frida ACCERR 實戰；termux-x11 repo + issues（含 #874 等，無相同 Composite-ENTER 案例）；SPICE QXLComposite；MagicLeap／Rust／Impeller 的 AHB 用法；Khronos forum flush 討論；DRI3 spec 郵件串；renderproto／compositeproto 鏡像；15 次主題檢索約 90 筆掃描。

### 本地釘選（一手；本輪對控制流有決定性）

| 樹 | 用途 |
|---|---|
| `src/upstream/lorie/src/main/cpp/xserver/` **21.1.24** | `exa.h` 契約；`exa.c` `ExaDoPrepareAccess` / `exaFinishAccess` / driver-scheme 選擇；`exa_driver.c` `exaModifyPixmapHeader_driver` / `exaPixmapHasGpuCopy_driver`；`exa_unaccel.c` `ExaCheckComposite` / `ExaCheckGetImage`；`fb/fbpict.c` `fbComposite` / `create_bits_picture`；`fb/fb.h` `fbGetPixmapBitsData`；`os/osinit.c` `OsSigHandler`；`os/backtrace.c`；`meson_options.txt` libunwind 預設 false |
| `src/upstream/lorie/src/main/cpp/pixman/` **0.46.4** | `pixman-bits-image.c` NULL-bits 自配、stride fail；`pixman-noop.c` `PIXMAN_OP_DST` |
| `src/f8-ahb/lorie/src/main/cpp/lorie/InitOutput.c` | `lorieExa`：`TrueNoop`、`FalseNoop` PrepareComposite、`loriePrepareAccess`／`FinishAccess`／`ModifyPixmapHeader` |

本輪 **確認** 本地 `ExaDoPrepareAccess` 與公開 EXA 修正控制流一致；本地源碼沒有改回「hook 因 fb_ptr 跳過」那套錯誤機制。

### 未能取得

GitLab freedesktop（bot 牆；改鏡像補足）；`libXrender` man（404；以 XCB API + spec 覆蓋）；keithp Present 部落格（404；以 LWN 覆蓋）。

不打算再為本假設加 70–80 篇文獻。

---

## 6. 與專案文件的關係

| 檔 | 角色 |
|---|---|
| `HANDOFF.md` | 執行現況權威（P0/P1/P2-A/P2-B.1 CLOSED；P2-B.2 PASS R3） |
| `TEST-MATRIX.md` | 目前閘門表；舊 P2 FAIL 列已標成 historical |
| `README.md` | 全域 GPU 研究背景；頂部 Current Snapshot 覆蓋後續歷史章節 |
| `evidence/session/composite-matrix/` | 本報告 §1 的矩陣證據 |
| `evidence/session/flight/` | 138.8 ENTER 飛行紀錄 |
| 本檔 | **P2-A 文獻封版 + 已被 A.3/A.4 supersede 的根因分析**；不可當作 current open blocker |

本報告不修改 `HANDOFF.md`／程式／探針，也不授權重新開啟 crash-buffer 或 P2STAGE。現行下一步是 `HANDOFF.md` 所列的 P2-B.3 real-workload performance qualification。
