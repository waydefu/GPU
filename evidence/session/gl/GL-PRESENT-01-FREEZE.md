# GL-PRESENT-01 凍結 — 2026-09-26：Ubuntu 程式的 GL／VK 畫面上屏時，CPU 花在哪裡（主線 #3 第一步）

狀態：**FROZEN**（寫於任何裝置 cell 之前）。工具 fork `feat/exa-async-proto-20260923` @ `6649316`（本地，未 push）。
判準常數以 `tests/gl_present/gl_present_judge.py`（sha256 `21d41fe211bfa67f…`）開頭的常數為準，本文逐字引用。

## 1. 要回答的問題
GL-BENCH-02 記錄了一個描述值：Zink 上屏時，X3 吃掉 55–74 CPU 秒；畫面外渲染只有 4–5 秒。
舊記憶把原因推測成「Zink 走 drisw，每幀由 client 用 CPU 複製」，但**從來沒有證實**。另外當時的條件和現在的目標不同：
- 當時跑的是 **Termux 原生**的 glmark2／vkmark（bionic Mesa），不是使用者要用的 Ubuntu 程式（`/opt/mesa-kgsl`）。
- 當時開著 Gate A（`GATEA_PROTO=1`）。telemetry 沒開：`env-x3.txt` 只有 PROTO，raw logcat 裡 `gatea-telemetry` 只出現 1 行。

所以這些舊數字只能當背景，不能直接引用。這次要回答三件事：
1. **路徑（J1）**：Ubuntu 的 Vulkan（Turnip）、EGL（Zink）、GLX（Zink）程式，是用哪一種方式把畫面交給 X3？
2. **成本在哪（J2）**：上屏時 X3 本身會不會吃掉明顯的 CPU？對照組是不上屏的畫面外渲染。
3. **機制（J3）**：X3 每幀的成本，會不會隨像素數成比例增加？會的話就是逐像素的複製，不是每幀固定的額外開銷。

## 2. 事前從原始碼得到的預測（還沒實測）
- Turnip 用 `sw_device = false` 初始化 WSI（`mesa-26.0.6/src/freedreno/vulkan/tu_wsi.cc:40`）。
- X3 的 DRI3 Open 不給裝置 fd（Termux 修補 0017 的說明）。`wsi_x11_check_dri3_compatible` 在 `dri3_fd == -1` 時會直接回傳「相容」（`src/vulkan/wsi/wsi_common_x11.c:160-162`），所以 Turnip 應該會走 **DRI3 PixmapFromBuffers**。
- X3 的 DRI3 只宣告支援 `DRM_FORMAT_MOD_LINEAR`（`lorie/.../InitOutput.c` `lorieGetModifiers`）。收到 LINEAR 的 fd 時會呼叫 `LorieBuffer_wrapFileDescriptor`，在 `buffer.c:151` 用 `mmap(PROT_READ|PROT_WRITE, MAP_SHARED)` 映射，之後把它當一般 CPU pixmap 使用，中間沒有 `DMA_BUF_IOCTL_SYNC`。
- `loriePresentFlip` 對匯入的 FD buffer 一律回傳 FALSE（除非設了 `TERMUX_X11_FORCE_FLIP=1`，註解是「does not work fine with turnip」）。xserver 本身也要求視窗蓋滿整個 root 才會 flip。所以每一幀都會走 Present 的**複製**。
  - 附帶一提：那一行的尺寸判斷寫成 `root.width != pixmap.height`，看起來是寫錯了，但本實驗的 1200×1200 不會因此改變結果，因為下一行一律拒絕匯入的 buffer。
- 已確認手機上的產品碼就是這份：裝的是 `1.03.01-f592241`，而 fork 在 `f592241..a72669c` 之間沒有動過 `lorie/`。

**預測結果**：`PATH_DRI3`（modifier 0）＋`X3_PRESENT_COST`＋`X3_COST_PER_PIXEL`，也就是 `STEP1 = PRESENT_COST_IS_X3_PER_PIXEL_COPY`。
這是要被檢驗的預測，**不是判決**。

## 3. 環境與綁定
- 產物：`com.waydefu.x11gpu` `1.03.01-f592241-24.09.26`，APK sha256 `f9e35b6907df36fc4f4d5a0440147c3e9b746356776beb3217431b48fa01075c`。
- Runner：`evidence/session/gl/run-gl-bench.sh`（sha256 `c5e03c2e16da5b47…`，沿用不改）。參數是 `KIND=cmd MODE=C`（`TERMUX_X11_DISABLE_EXA_GPU=1`），Gate A 關、telemetry 不設、R8 不 arm。
  X3 由 `start-x3-untraced.sh`（`411b862e675a573a…`）啟動，TracerPid 0，由 runner 檢查。
- Stable `:1` 的前後比對、螢幕亮且沒鎖、mem-guard、用確切 pid SIGTERM 結束 X3，都照 runner 原本的做法。
- `EXPECT_ROOT=1200x2416`（GL-BENCH-02 實測值）。如果 dry-01 量到的 root 不同，就記錄下來，main 改用 dry-01 的值。**這是操作參數，不是門檻**。
- Client 環境：`/usr/local/bin/f8-gpu`（`f4f6e53d475ad799…`），也就是使用者平常的 Ubuntu GPU 環境：`/opt/mesa-kgsl` 的 Turnip on KGSL＋Zink。另外加上 `vblank_mode=0`。
- 工具（`build.sh` `d35f8a288e2cc1c7…`，連續編兩次 hash 相同）：

  | 檔案 | sha256 |
  |---|---|
  | `present_count.so` | `3e0299f6cfe69231065ff034c0e7a8198b54bf706d33c26307ab7714abae1301` |
  | `vk_present` | `aeb348e8de527f3c79e7595131672eecf17d48c19d2271cef1c9a525d27e408b` |
  | `gl_present_egl` | `00d343ad662a7e11a588058b78359129295caa075b219f1be82274eb290f939a` |
  | `gl_present_glx` | `0a3cb22be5c99f39d58ec757ff41bb169749f6f6ae5f0079259082fb840c0b1f` |
  | `gl_present_cell.sh` | `2393ca57c30bb1a2…` |
  | `gl_present_judge.py` | `21d41fe211bfa67f…` |

  helper 函式抄自 `tests/gl/gl_bench.sh`（`393491b86b61adb2…`）。差別只有：segment 間隔從 30 s 改成 15 s，另外新增各執行緒 tick、牆鐘時間和觸控裝置名稱的檢查。
- 主機驗證（`gl-present-01/host-qual-20260926.txt`，私用的 Xvfb `:97`）：Vulkan 走 PutImage、EGL 走 ShmPutImage、GLX 走 XShmPutImage，每一幀都有對應的計數；offscreen 全部是 0。
  驗證時抓到一個 bug：glvnd 用 `RTLD_LOCAL` 載入驅動，shim 因此找不到下一層的 `XShmPutImage`，client 在第一次 swap 就 SIGSEGV。已經修好（shim 改成自己連結被包裝的函式庫），這組 hash 就是修好之後的版本。

## 4. Cell
依序是 dry-01 → main-01 → main-02 → xdbg-01。證據放在 `evidence/session/gl/gl-present-01/<cell>`。
- **dry-01（不進判準）**：`GL_PRESENT_SET=dry`，跑 idle 5 s、vk-l 5 s、egl-l 5 s。用途是在 :3 上檢查工具和 harness，並量 root 尺寸。它的數值不進判定器，也不會改動任何門檻（門檻在它執行前就已經凍結在本文）。
- **main-01、main-02（判準）**：`GL_PRESENT_SET=main`，`GL_PRESENT_SECS=20`，各自是一個獨立的 X3 生命週期（A/A）。
- **xdbg-01（X3 端的旁證）**：`GL_PRESENT_SET=xdbg`，X3 額外帶 `TERMUX_X11_DEBUG=2`，跑 vk-l、egl-l、glx-l 各 10 s。
  `=2` 會打開 `lorieServerDebugEnabled`（DRI3 匯入的 log），但不會打開 renderer 的 debug（那個只在 `=1` 時開）。另外 X3 會多 fork 一個 `logcat --pid` 子程序，所以這個 cell **不拿來量 CPU**。

main 的 segment（固定順序；L = 1200×1200，M = 600×600）：

| segment | 內容 |
|---|---|
| `idle` | `sleep 20`，量 X3 閒置時的 CPU |
| `vk-off` | `vk_present --size L --offscreen`：每幀清畫面再等 fence，不建 swapchain（**紅色對照**） |
| `vk-l`、`vk-s` | `vk_present`，immediate 模式，L 和 M |
| `egl-off` | `gl_present_egl --size L --offscreen`：FBO 加 `glFinish`（**紅色對照**） |
| `egl-l`、`egl-s` | `gl_present_egl`，swap interval 0，L 和 M |
| `glx-l` | `gl_present_glx`，L（只判路徑，CPU 只描述） |
| `vk-l-sw` | 同 vk-l，另加 `MESA_VK_WSI_DEBUG=sw`（**shim 的紅色對照**：路徑必須換掉） |

## 5. Segment 有效性（任何一項不符就 INVALID，量不到的值一律記 null）
`rc=0`；`touch_selftest=true`，而且觸控裝置名稱要含 `focaltech`；`touch_events=0`；segment 前後焦點都在實驗版 app、亮屏、沒鎖屏；開始時 `thermal_start=0`；X3 tick 和時間窗都讀得到。
非 idle 的 segment 還要：client 有回報幀數且大於 0；驅動身分要對（VK：裝置名稱含 `Adreno`、driver 含 `turnip`；GL：`GL_RENDERER` 含 `zink` 和 `adreno`）；`<seg>.present.jsonl` 剛好一行（缺少就是 null，不是 0）。

## 6. 判準（引用判定器的常數）
- 共用的量：`x3_cores = ΔX3 ticks / CLK_TCK(100) / 時間窗秒數`；`x3_ms_per_frame = ΔX3 ticks × 10 ms / frames`。

- **路徑分類**（`COVER = 0.90`）：
  - `DRI3`：匯入次數 ≥ 1，`present_pixmap` ≥ 0.9×幀數，而且沒有任何 SHM pixmap、PutImage 或 ShmPutImage。
  - `SHM_PIXMAP_PRESENT`：SHM pixmap ≥ 1，`present_pixmap` ≥ 0.9×幀數，沒有匯入也沒有 PutImage。
  - `SHM_PUT`：ShmPutImage（xcb 加 Xlib）≥ 0.9×幀數。
  - `CORE_PUT`：PutImage（xcb 加 Xlib）≥ 0.9×幀數。
  - 以上都不成立就是 `UNEXPLAINED`。

- **J0 工具有效性**：下面三項全部成立才是 `GL_PRESENT_TOOL_VALID`，否則是 `GL_PRESENT_TOOL_INVALID`，其餘判決全部 INVALID。
  1. 所有有效的上屏 segment 都不是 `UNEXPLAINED`。
  2. 有效的 off segment，除了 `dri3_open` 之外的計數全部是 0。
  3. `vk-l-sw` 至少一個 rep 有效，而且每個有效 rep 的路徑都屬於 {`SHM_PIXMAP_PRESENT`, `SHM_PUT`, `CORE_PUT`}，不能是 DRI3。

- **J1 路徑**（分 vk、egl、glx）：把兩個 rep 的 -l 和 -s（glx 只有 -l）有效 segment 的路徑放在一起看。全部相同就是 `PATH_<路徑>`；不一致是 `PATH_UNSTABLE`；沒有任何有效 segment 是 `PATH_INVALID`。
  - **J1x（xdbg 旁證）**：看每個 API 的 segment 時間窗裡，X3 log 有幾行 `DRI3: imported`。
    - J1 是 DRI3 時：有 ≥ 1 行是 `X_WITNESS_CONFIRMS`，0 行是 `X_WITNESS_CONTRADICTS`。
    - J1 不是 DRI3 時：有 ≥ 1 行是 `X_WITNESS_CONTRADICTS`，0 行是 `X_WITNESS_CONSISTENT`。
    - xdbg 沒有資料就是 `X_WITNESS_NULL`。
    - 出現 CONTRADICTS 的話，該 API 的路徑結論在結果文件裡必須標成有矛盾，不可以只引用 J1。

- **J2 X3 上屏成本**（分 vk、egl；一個 rep 要 idle、off、on-l 三段都有效才算數）：
  - 對照組必須安靜：`off x3_cores ≤ idle x3_cores + 0.05`（`OFF_CTRL_MARGIN`）。只要有一個 rep 不成立，就是 `CONTROL_FAILED`。
  - 算數的 rep 少於 2 個：`INSUFFICIENT_REPS`。
  - 兩個 rep 都滿足 `on-l ≥ 0.10`（`ON_MIN_CORES`）而且 `on-l ≥ 3 × max(off, idle, 0.01)`（`ON_OVER_OFF`、`FLOOR_CORES`）：`X3_PRESENT_COST`。
  - 兩個 rep 的 `on-l` 都 `< 0.05`（`CHEAP_MAX`）：`X3_PRESENT_CHEAP`。
  - 其他情況：`INCONCLUSIVE`。

- **J3 隨像素增加**（分 vk、egl）：`r = x3_ms_per_frame(L) / x3_ms_per_frame(M)`，像素比是 4。
  - 兩個 rep 的 r 都 ≥ 2.0（`SCALE_PER_PIXEL`）：`X3_COST_PER_PIXEL`。
  - 兩個 rep 的 r 都 ≤ 1.5（`SCALE_FIXED`）：`X3_COST_PER_FRAME_FIXED`。
  - 其他情況：`INCONCLUSIVE`。可用的 rep 少於 2 個：`INSUFFICIENT_REPS`。

- **STEP1**：
  - J0 無效：`GL_PRESENT_INVALID`。
  - vk 和 egl 都是 `X3_PRESENT_COST` 加 `X3_COST_PER_PIXEL`：`PRESENT_COST_IS_X3_PER_PIXEL_COPY`。
  - vk 和 egl 都是 `X3_PRESENT_CHEAP`：`PRESENT_COST_NOT_IN_X3`。
  - 任一個是 CONTROL_FAILED 或 INSUFFICIENT_REPS：`GL_PRESENT_INVALID`。
  - 其他情況：`PRESENT_COST_MIXED`。

- **只描述、不判決**：glx-l 的 X3 CPU、各 segment 的 fps、client 每幀 CPU、X3 最忙的執行緒及它的占比、Activity 的 CPU。

## 7. 對照組（每一個都必須有辦法變紅）
- `vk-off`／`egl-off`：同一支程式、同樣的 GPU 工作，只是不上屏。如果 X3 在這裡也忙，就代表 X3 的 CPU 不是上屏造成的，J2 判 `CONTROL_FAILED`。
- `vk-l-sw`：強制走軟體上屏。如果 shim 還是回報 DRI3，或者看不出路徑，J0 判 `TOOL_INVALID`。
- 判定器的 `--self-test` 有 11 個情境：shim 看不到路徑、sw 沒換路徑、off 有上屏計數、off 很忙、觸控、shim 缺檔、固定成本、X3 很便宜、驅動錯誤、SHM 路徑分類，全部照預期變紅或變綠。
  反向檢查：把 `SCALE_PER_PIXEL` 改成 5，baseline 情境就會失敗，證明自我測試本身會失敗。
- 主機驗證：Xvfb 上的三種非 DRI3 路徑，每一幀都算得到。DRI3 的計數在主機上無法驗證（Xvfb 沒有 DRI3），所以靠三道保護：J0 的覆蓋率規則（幀數解釋不了就判無效）、`vk-l-sw` 的換路徑檢查、xdbg 的 X3 端旁證。

## 8. 事先寫好的讀法
- **`PRESENT_COST_IS_X3_PER_PIXEL_COPY`，且 vk 和 egl 都是 `PATH_DRI3`**：client 其實已經用 DRI3 把 GPU buffer 交出去了，CPU 複製發生在 **X3 的 Present**，也就是從 mmap 出來的 LINEAR dma-buf 逐像素複製。
  這樣第二步的重點就從「client 端」移到「X3 端」：可能的方向是讓 renderer 直接把 client 的 dma-buf 匯入成 EGLImage 或 AHB，或是讓匯入的 buffer 可以 flip。Mesa／client 可能完全不用改。
  主線 #3 原本叫「DRI3＋AHB **client** 端」，這個名稱要**跟使用者確認後再改**。
- **路徑是 `SHM_*` 或 `CORE_PUT`**：複製發生在 client（軟體上屏），照原本「client 端」的方向走。
- **`PRESENT_COST_NOT_IN_X3`**：GL-BENCH-02 的 X3 成本來自別的地方（Termux client 或 Gate A PROTO=1），要重新想。
- **`MIXED`／`INCONCLUSIVE`**：只照各 API 分開報告，不外推。
- 不管結果如何，**都不能**拿來推論 glmark2 分數、遊戲、Blender 的實際體驗。這裡只回答「上屏的 CPU 在哪裡、怎麼隨尺寸變化」。

## 9. 已知限制
- X3 的量測窗包含 client 的啟動和結束（建立 Vulkan instance、開視窗），這些都算進每幀成本。20 s 裡有上千幀，影響很小，但不是 0。
- client 在 PRoot 追蹤器底下執行，所以 client 的 CPU 只描述、不判決。X3 不受影響（TracerPid 0，由 runner 確認）。
- 工作量只有清畫面，GPU 幾乎不做事。真實程式的 GPU 時間會更多，但 X3 每幀的複製成本和畫面內容無關。
- 用 immediate／swap interval 0，X3 可能被塞滿，但每幀成本仍然有效。實際以 vsync 跑的程式，X3 的核數大約是每幀成本 × fps。
- tick 的解析度是 10 ms。20 s 的時間窗在 0.1 核時有約 200 tick，精度足夠。

## 10. 執行規則
- 每個 cell 只跑一次。exit 3（BLOCKED）代表沒有消耗掉，可以修正前提後用 `<cell>-r2` 重跑一次。
- exit 2（INVALID）或 segment 無效的 cell **保留並凍結**。每個 main rep 最多補一個替代 cell（`main-0Nb`），原因要寫進結果文件，判定只用有效的 rep。
- ADB 在中途斷線（Wi-Fi 漫遊會關掉無線偵錯，見記憶 `adbwifi-roaming-disable`）時，受影響的 segment 會因為讀不到狀態而成為 null，進而 INVALID，照上一條處理。
- 手機要接電，執行期間不要碰手機（觸控會讓 segment 無效）。實驗版 app 會切到前景。Stable `:1` 不會被碰到。

---

## 修訂 1（2026-09-26，寫於任何判準 cell 之前）

**起因（兩個都是不進判準的 cell）：**
- `dry-01` 被 runner 擋下（BLOCKED `x_root_size 1200x2464`）。runner 當時量到螢幕是亮的、沒鎖（`screen-pre.json`），所以 1200×2464 是現在真實的 root 尺寸。依第 3 節，main 改用 `EXPECT_ROOT=1200x2464`。
- `dry-01-r2`（CMD_CAPTURED）：vk-l 的路徑和第 2 節的預測一樣，是 `pixmap_from_buffers` ×4、modifier 0、`present_pixmap` = 幀數。
  **但 egl-l 的 3569 幀沒有任何一個被 shim 算到**，照原判準會觸發 J0 `UNEXPLAINED`，整批判成 TOOL_INVALID。
- `diag-egl-01`（診斷用，`tests/gl_present/diag_egl.sh`，工具 `req_count.so`、`px_probe`）：
  - EGL（Zink kopper）在協定層每幀只送 1 個 `GetGeometry`，沒有 Present、PutImage 或 CopyArea。
  - 視窗中心像素 4 次都是 `0x00000000`，**畫面沒有交給 X**。
  - 同一個 X3 上，GLX 和 VK 都是 DRI3 `PixmapFromBuffers`（modifier 0）加上每幀一次 `PresentPixmap`，像素也出現 client 的顏色。

**揭露：** 寫這份修訂之前，我已經看過 dry-01-r2 的 vk-l 描述值：5 s 內 X3 約 0.72 核、1623 fps。
所以本修訂**不改任何門檻數值**（`COVER`、`ON_MIN_CORES`、`ON_OVER_OFF`、`FLOOR_CORES`、`OFF_CTRL_MARGIN`、`CHEAP_MAX`、`SCALE_PER_PIXEL`、`SCALE_FIXED` 都和第 6 節一樣），只改下面這些結構：

1. **判準 API 從 {vk, egl} 改成 {vk, glx}**（`JUDGED_APIS`）。EGL 根本沒上屏，沒有上屏成本可以量；GLX 則代表 Blender 這類程式。STEP1 的條件同樣改成 vk 和 glx。
2. **新增路徑類別 `NOT_PRESENTED`**。條件是下面三項**同時成立**：
   - present_count 看不到任何路徑（原本會判 `UNEXPLAINED`）；
   - 協定層沒有任何交畫面的 request：extension 的 Present/1、MIT-SHM/3、MIT-SHM/5、DRI3/2、DRI3/7，以及 core 的 major 72、62、63，全部是 0，而且直方圖不是空的；
   - 像素探針 4 次都讀得到，而且沒有一次是 client 的顏色（`0x0080ff`／`0xff8000`）。

   任何一個見證缺少，或者和其他見證矛盾（例如計數是 0 但畫面出現 client 的顏色），都維持 `UNEXPLAINED`，也就是 J0 `TOOL_INVALID`。
3. **main 的 segment 改成**：`idle`、`vk-off`、`glx-off`（新增，GLX 的 FBO 加 `glFinish`）、`vk-l`、`vk-s`、`glx-l`、`glx-s`（新增）、`egl-l`（只判 J1）、`vk-l-sw`。
   `egl-s` 和 `egl-off` 刪除。每個上屏 segment 在跑到一半時，於 root (300,300) 讀 4 次像素（間隔 150 ms），這個點落在兩種視窗尺寸之內。
4. **每個 segment 同時掛兩個 shim**（`LD_PRELOAD=present_count.so:req_count.so`）。xdbg 跑 vk-l、glx-l、egl-l。
5. 判定器的自我測試增加到 **14 個情境**，新增的有：`NOT_PRESENTED` 本身、畫面出現顏色但計數是 0、協定層有 Present 但計數是 0、像素缺少。
   反向檢查（`SCALE_PER_PIXEL=5`）照預期失敗。

**修訂後的工具**（fork `bb45c12`，`build.sh` `f25e62245303272b…`，編兩次 hash 相同）：

| 檔案 | sha256 |
|---|---|
| `present_count.so` | `3e0299f6…`（沒變） |
| `vk_present` | `aeb348e8…`（沒變） |
| `gl_present_egl` | `00d343ad…`（沒變，編出來的結果一模一樣） |
| `gl_present_glx` | `27fd211f587774267abd926899d524e28d4fec35579c2c078b8d75722d04bbd9` |
| `req_count.so` | `199786b4624caf0b6bc81c14bf42f8b8cae56d51f2295ca115b4482255268367` |
| `px_probe` | `f86f109e3a4eddf1c15c4564051f8900d6646c0a0e3dedbc251fa5583ed8bbc4` |
| `gl_present_cell.sh` | `326e7da07264c83e…` |
| `gl_present_judge.py` | `2124e1cd77d35836…` |

主機驗證紀錄：`gl-present-01/host-qual-amendment1-20260926.txt`。
- glx-l（llvmpipe）：`XShmPutImage` = 幀數，像素出現 client 的顏色。
- glx-off：沒有任何上屏計數，像素維持黑色。

**讀法補充（在第 8 節之外另外加的）：** J1 如果判 `egl = PATH_NOT_PRESENTED`，代表「Ubuntu 程式透過 `/opt/mesa-kgsl` 開 EGL 視窗，在 `:3` 上畫面不會出現」。Chromium、Electron、WebGL 走的就是這條路，所以這本身就是主線 #3 要處理的問題，要另外列出來，不能跟上屏成本混在一起談。
