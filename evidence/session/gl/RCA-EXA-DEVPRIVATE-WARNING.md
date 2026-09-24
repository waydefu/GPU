# RCA：`EXA bug: pPixmap->devPrivate.ptr was 0x…, but should have been NULL.`（非致命警告，2026-09-24）

**性質：唯讀 RCA。** 只讀原始碼、只在主機上重算凍結證據。沒有 build／install／adb／裝置操作，沒有改任何產品原始碼，也沒有改寫任何既有證據。
本文件只新增兩樣東西：這份 `.md`，以及 `rca-exa-devprivate-warning/`（主機端工具與輸出，見 §8）。

**與其他文件的關係：**
- X3 結束的原因已另案定案：`GATEA_FATAL_HALT what=x-hup reason=6`，見 `INCIDENT-20260924-X3-EXA-BUG-FATAL.md` 頂端的更正，以及 `RCA-X3-EXA-DEVPRIVATE-SWIPE.md` §3。**本文不再討論**。
- `RCA-X3-EXA-DEVPRIVATE-SWIPE.md` §4 已證明 W1 機制（lorie 直接呼叫 hook），§6 也提出了 Fix-2。本文的焦點是**這行警告本身**，並補上該文沒有的部分：
  跨建置的決定性證據（§4.2）、R4 的逐筆追蹤證明（§2.4）、oracle 對照（§4.1）、指標與 buffer format 的對應（§4.3），
  以及 **Fix-2 對 Gate A direct 路徑無效，需要 Fix-3**（§5.2）。

---

## 0. 判決

| 問題 | 判決 | 標記 |
|---|---|---|
| 這行從哪裡來 | lorie 在 EXA 的 prepare/finish 配對**之外**，把 `devPrivate.ptr` 設成 AHB 的 CPU 映射，而且沒有清回 NULL。之後第一次由 EXA 管理的 CPU 存取碰到這個 pixmap，`ExaDoPrepareAccess` 就印出這行。共有三類寫入點：W1、W2、W3（§2.2） | **PROVEN**（原始碼＋靜態檢查器 RED） |
| 會不會畫錯像素（f592241） | **不會。** EXA 在使用前一定先覆寫這個指標（upstream `exa.c:320-326`），接著 lorie 的 hook 再設一次正確值（`InitOutput.c:4281`）。殘留的值從來不會被當成像素基底 | 機制 **PROVEN**；oracle 支持（§4.1：幾千次警告，0 個像素錯誤） |
| 會不會洩漏 | **不會。** `devPrivate.ptr` 不持有任何資源；lock 狀態記在 `priv->locked` 和 `LorieBuffer.locked` | **PROVEN** |
| 會不會 use-after-unmap | **潛在風險，目前沒有觸發。** 懸空狀態確實存在：指標指向已 unlock 的 AHB 映射（§3.3）。但目前沒有任何程式在 access 外讀它；lorie 端為 PROVEN，xserver 其餘部分只做了 grep，為 INFERRED | 潛在：**PROVEN**；觸發：**無**；gralloc 在 unlock 時會不會 unmap：**UNKNOWN** |
| 可決定性 | 同一 seed、同一模式，在 4 個建置（`0245ff3`、`d1c86dd`、`11b3b79`、`f592241`）上的次數**完全相同**：534／469／362／319 | **OBSERVED**（凍結證據，sha256 已核對） |
| 從什麼時候開始 | 第一個直接呼叫出現在 `8f357b8`。Gate A 最早的 R1 oracle（`88e3f17`、`d9b7f60`）每次就已經是 2714 行。upstream 對照 `11b82d9` 的靜態檢查為 GREEN | 引入點 **PROVEN**（`git log -S`）；upstream 執行期 **NOT RUN** |
| Fix-2（SWIPE RCA §6）夠不夠 | 對 solid／copy／async／D0a composite 路徑足夠。**對 Gate A direct 路徑不夠**：W3 寫進去的值會被 Fix-2 的「存回原值」保留下來 | **PROVEN**（檢查器對 M1 仍是 RED，W=4）；G0 有 645 次落在只可能是 W2/W3 造成的 BGRA 位址上（**INFERRED，強**） |
| 分類 | **對目前的像素、洩漏而言是無害的，但確實違反了 EXA 的契約。** 實際代價有兩個：(a) EXA 唯一的執行期「access 外殘留指標」偵測被幾千次良性命中淹沒；(b) 若 xserver 以 `DEBUG` 建置，第一次出現就會 `FatalError` | (a) 後果為 INFERRED；(b) **PROVEN**（`exa_priv.h:85-87`） |

---

## 1. 範圍與原始碼權威

- 產物：`1.03.01-f592241-24.09.26`。原始碼 `waydefu/termux-x11` `f592241`，worktree `src/f8-ahb-exa-async`（目前 HEAD `a4440fa`，`git diff --stat f592241 HEAD -- lorie` 為空；
  `InitOutput.c` 與 `git show f592241:…` 逐位元組相同）。**下面所有 `InitOutput.c` 行號都是 `f592241`**。
- xserver：submodule pin `65d790bd`。該 worktree 沒有 checkout，所以從 `src/upstream/lorie/src/main/cpp/xserver`（同一 SHA）讀取。
  我把 fork 的 `patches/xserver.patch` 中 exa／fb／damage 的 hunk 套到 scratchpad 的副本，確認 fork 對 `exa.c`、`exa_unaccel.c`、`exa_render.c`、`fbpict.c` 只加 `p2a2_emit` 儀表，
  **沒有改動任何 `devPrivate.ptr` 寫入**（`grep 'devPrivate\.ptr *=' xserver.patch` 為空）。
  引用格式是 `exa.c:N`，N 為 upstream `65d790b` 的行號；需要時另附「patched:M」，M 是實際編譯的那個檔案裡的行號。
- EXA 模式：`InitOutput.c:4317` `.flags = EXA_OFFSCREEN_PIXMAPS | EXA_HANDLES_PIXMAPS`（沒有 `EXA_MIXED_PIXMAPS`，所以是 driver 模式，走 `exa_driver.c`），
  `InitOutput.c:4324` `.PixmapIsOffscreen = TrueNoop`（因此 `has_gpu_copy` 恆為真），
  `InitOutput.c:4325` `.PrepareAccess = loriePrepareAccess, .FinishAccess = lorieFinishAccess`。

---

## 2. 機制

### 2.1 EXA 的契約（PROVEN，xserver 原始碼）

| 位置 | 內容 |
|---|---|
| `exa.c:313-316`（patched:336-339） | 非巢狀 prepare 時，若 `devPrivate.ptr != NULL` 就 `EXA_FatalErrorDebug(("EXA bug: … should have been NULL"))` |
| `exa_priv.h:85-95` | `#ifdef DEBUG` → `FatalError`；否則 → `ErrorF`。`patches/dix-config.h.in:151` 是 `#undef DEBUG`，recipes 裡沒有 `-DDEBUG` → **這個 build 只是 `ErrorF`** |
| `exa.c:320-326`（patched:343-349） | 印完之後**無條件覆寫**：driver 模式下 `fb_ptr` 恆為 NULL（`exa_driver.c:111`，而且 `exaModifyPixmapHeader_driver` 不會設它）→ `devPrivate.ptr = sys_ptr`（lorie pixmap 的 `sys_ptr` 是 NULL：`exa_driver.c:78,113`） |
| `InitOutput.c:4281` | 接著 driver hook `loriePrepareAccess` 設 `devPrivate.ptr = priv->locked ?: priv->mem` → CPU 真正使用的是這個新鮮的值 |
| `exa.c:422-423`（patched:479-480） | `exaFinishAccess`：*"We always hide the devPrivate.ptr."* 先設 NULL，**再**呼叫 driver `FinishAccess`（`exa.c:436`） |
| `exa_driver.c:184-185` | `exaModifyPixmapHeader_driver`：*"Always NULL this, we don't want lingering pointers."* |
| `InitOutput.c:4296-4313` | `lorieFinishAccess` 只處理 mutex、`lockDepth` 和 `wasLocked`（必要時 unlock 並設 `priv->locked = NULL`），**完全不碰 `devPrivate.ptr`**。被 EXA 呼叫時這沒問題，因為 EXA 已經先清掉了 |

### 2.2 誰在配對外留下非 NULL（完整列舉，PROVEN）

在 fork 裡對 `devPrivate\.ptr *=[^=]` 做 grep：lorie 只有 `InitOutput.c` 的 7 行，`xserver.patch` 則沒有。xserver 自身在 driver 模式下寫非 NULL 值的地方只有：
`ExaDoPrepareAccess`（配對的起點）、`exaPixmapHasGpuCopy_driver`（`exa_driver.c:224-227`，先存再還原，淨效果為零），以及 `mi/miscrinit.c:83,115`（只在 `pPixData != NULL` 時寫，之後 `exa_driver.c:185` 會清掉）。
classic／mixed 的寫入點在 driver 模式下不會執行。所以殘留只可能來自下面三類：

| 類 | 位置 | 何時執行 | 寫入的值 |
|---|---|---|---|
| **W1** | `InitOutput.c:4281`，由 lorie **直接**呼叫 hook 時觸發（呼叫點共 7 個函式、9 行 prepare）：`lorieExaAsyncFlushPixmap` 2166、`lorieExaAsyncFlushAll` 2181、`lorieExaCpuSolidRect` 2302、`lorieExaRepairSolidXByte` 2326、`lorieExaCpuCopyRect` 2491/2493、`lorieExaCpuOverRect` 3881/3883、`lorieExaRepairDestXByteZero` 3910 | 同步 GPU solid 寫進 depth < 32 目的地後的 X-byte 修補（`lorieExaDoneSolid` 2473-2478）；GPU 排程失敗時的 CPU 補畫；D0a composite 的 `lorieExaDoneComposite` 修補（4065-4070）；Gate A Done 的修補（3832-3838）；async flush | `priv->locked`（AHB 的 CPU 映射） |
| **W2** | `gateADirectTryPrepare` `InitOutput.c:3383`、`3389` | Gate A 准入時，若該端點剛好沒有 lock（`!sp->locked`／`!dp->locked`） | 新 lock 到的映射 |
| **W3** | `gateAPairRelockCpu` `InitOutput.c:3788`、`3796` | **每一次** Gate A direct 交易 SUCCESS 之後（`gateADoneDirect` 3831），src 與 dst 各寫一次；緊接著在 3790、3798 發出 `RELOCK_SRC`／`RELOCK_DST` trace，兩者都計入 `LORIE_GATEA_COUNTER_RELOCK`（`lorie.h:1726-1727`） | 重新 lock 到的映射 |
| （乾淨） | `InitOutput.c:3685-3686` | Gate A 所有權轉移時 | NULL |

W2/W3 的註解寫明這是刻意的（`InitOutput.c:3376-3379`：*"Fresh locks restore devPrivate.ptr immediately so every reader sees a valid mapping"*），屬於 Gate A 的所有權程式碼。

### 2.3 歷史來源（PROVEN，git）

- `git log -S'loriePrepareAccess(dst, EXA_PREPARE_DEST)'`：第一次出現在 `8f357b8`（*exa: accelerate GXcopy between distinct AHB pixmaps via GPU copy queue*），之後 `923116b`（GPU solid）、`ca8600a`（X-byte 修補）、`42d2e3b`（GPU composite）都加了新的呼叫點。
- W2/W3：`82a87f4`（*feat(gatea): implement P2 bounded ownership/direct-submission fixes*）。
- upstream 對照 `src/upstream` `11b82d9`：`loriePrepareAccess` 只由 EXA 呼叫（`InitOutput.c:1129-1165`），沒有直接呼叫，也沒有 W2/W3。靜態檢查器結果為 GREEN（§6.1）。
  所以 upstream 應該不會印這行（**INFERRED**；upstream 的執行期 **NOT RUN**）。

### 2.4 逐筆追蹤證明（PROVEN，`d9b7f60` R4，當時 p2a2 追蹤預設開啟）

`gate-a-a1/p2-r3-xpump-runtime/runtime-d9b7f60/r4-oracle/x3-launcher.raw.log`（sha256 `f73104c8…`；該目錄沒有 manifest）：

```
142  R3 S2_AHB pix=0xb4000074e1c19b70 … depth=24 … devptr=0x0 … locked=0x76966a0000 …
143  Probe RETURN depth=1 enter=5 return=5
144  D3 AFTER_CALL depth=1 …
145  EXA bug: pPixmap->devPrivate.ptr was 0x76966a0000, but should have been NULL.
146  Sprep-pre pix=0xb4000074e1c19b70 index=1 …
```

- 第 142 行：這個 depth-24 pixmap 剛升級成 AHB，`devptr=0x0`，`locked=0x76966a0000`。
- 第 142 到 145 行之間沒有任何 `Sprep` 行。patched `exa.c` 在每次非巢狀 prepare 都會 emit `Sprep-pre`，巢狀時則 emit `Sprep … nested=1`。
  所以這段期間 EXA 沒有做過任何 prepare，而指標從 0 變成了 `locked`。依 §2.2 的列舉，寫入者只能是 lorie 的 W1／W2／W3（這一格是加速 composite，所以是 W1 或 W3；兩者寫入的值相同）。
- 第 145 行印出的正是 `locked` 的值；第 146 行 `index=1`（`EXA_PREPARE_SRC`，`exa.h:632`）是 oracle 對目的地做 GetImage 讀回。
- 整份 log：`EXA bug` 1514 行，對應 R4 的 1514 個 cases，而 R4 **PASS 1514/1514 fail=0 maxΔ=0**（AGENTS.md）。每個 case 都是一次加速 composite 加一次讀回，所以剛好一 case 一行。

---

## 3. 影響評估

### 3.1 錯像素：不會（f592241）

- 殘留值只有「被 EXA 印出來」和「被 EXA 覆寫」兩種命運（`exa.c:314-326`）。之後 CPU 使用的指標來自 `InitOutput.c:4281`，而 `priv->locked` 本身是正確的映射。
- lorie 自己讀 `devPrivate.ptr` 的地方：2141（`lorieExaAsyncApplyXfix`，在 hook 內、4281 之後）、2304、2328、2497-2498、3888-3890、3912。每一處都在一次成功的 `loriePrepareAccess` 之後，也就是在 4281 重新設值之後（**PROVEN**）。
  220（`lorieP2b2Stamp`）只把值印出來，不做 dereference。
- 在 xserver 的 `Xext dri3 present render mi dix miext damageext composite glx` 裡 grep `devPrivate.ptr`：只有 `mi/miscrinit.c`（寫入）、`dix/pixmap.c:80`（寫 NULL）和 `miext/rootless`（沒有編進來）；fork patch 的 `exa_unaccel.c`、`fbpict.c` 只是把值印出來。
  所以「沒有 access 外的 dereference」：lorie 端 **PROVEN**，xserver 端 **INFERRED**（靜態 grep，沒有執行期追蹤）。
- 證據：§4.1。尤其同一 seed 下 MODE=G 與 MODE=GA 的警告次數不同（534 對 362），但 `xdigest` **完全相同**（`fc22db734a833dfc`，這個 digest 連 X byte 都涵蓋），所以警告次數與像素內容無關。

### 3.2 洩漏：不會（PROVEN）

`devPrivate.ptr` 只是複製過來的指標。buffer 的生命週期靠 `LorieBuffer_acquire`／`release` 的 refcount；CPU lock 狀態記在 `priv->locked`（lorie）和 `buffer->locked`（`buffer.c:421-461`）。
殘留的 `devPrivate.ptr` 不會延長任何 lock，也不會延長 buffer 的生命週期。

### 3.3 use-after-unmap：潛在，目前不會觸發

在下面這些情況，直接呼叫的 `loriePrepareAccess` 會拿新的 lock（`wasLocked = FALSE`，`InitOutput.c:4269-4277`）；之後 `lorieFinishAccess` 會 unlock，並設 `priv->locked = NULL`（4308-4312）。
但 `devPrivate.ptr` 仍然指著剛 unlock 的映射，也就是懸空。這些情況包括：

| 情境 | 為什麼 `priv->locked` 是 NULL | 可達性 |
|---|---|---|
| DRI3 匯入的 AHB pixmap | `loriePixmapFromFds`（4330-4394）完全不 lock，所以每一次直接存取都是新 lock 接著 unlock | `lorieExaPrepareCopy` 會接受它當 src（`lorieEnsureGpuSampleable` 對匯入的 AHB 回傳 buffer）；GPU copy 排不進去時走 `lorieExaCpuCopyRect` → **INFERRED 可達**，凍結證據裡沒觀察到 |
| `lorieUnlockBgraAhb`（2512-2520）之後的 BGRA src | PGA-GAP-4 刻意 unlock | 只有「BGRA 格式但 depth < 32」的來源才能通過 2531/2533 的檢查，只有匯入 buffer 會這樣 → **INFERRED 罕見** |
| root 換 pixmap（`lorieSetWindowPixmap` 1301-1305） | 舊 root 被 unlock | 舊 root 隨即被 destroy（1376）→ 無害 |
| Gate A GPU_OWNED 期間 | 3673-3684 unlock | **不會**懸空：3685-3686 明確清成 NULL |

目前沒有任何程式會 dereference 這些懸空值（§3.1）。而且 exa 內唯一會把 `devPrivate.ptr` **鎖存**進別處的地方（`exa_driver.c:170-172`，在 `ModifyPixmapHeader(…, NULL)` 時抄進 `sys_ptr`），只會在下面兩個時點執行：
第一次 REGULAR→AHB 升級（`InitOutput.c:273`，此時 pixmap 還沒被任何直接存取碰過，因為直接存取的前提是 `lorieEnsureGpuSampleable` 已經成功），以及 DRI3 匯入建立時（4355、4382）。
→ **原始碼層級不可達**（與 SWIPE RCA §4.4 的結論一致）。
gralloc（Adreno／HyperOS）在 `AHardwareBuffer_unlock` 時會不會真的 unmap 那段 VA：**UNKNOWN**。

### 3.4 真正的代價

1. **偵測器被淹沒（後果為 INFERRED）。** `exa.c:314` 是 EXA 在執行期抓「access 外殘留指標」的檢查點。
   目前一次 oracle 就有 319 到 2714 次良性命中，將來若真的出現 access 外的 dereference 或不配對的 access，會完全混在雜訊裡看不出來。修掉之後，這行才能恢復成一條硬性判準（§6.3）。
2. **`DEBUG` 建置會直接死（PROVEN）。** `exa_priv.h:85-87`：一旦定義 `DEBUG`，第一次出現就會 `FatalError`，而 MODE=G 一開始跑就會出現。
3. **Log 量。** f592241 各執行的次數：oracle 319 到 2624、Electron 最多 219、XFCE 102 到 105。`ErrorF` 在 X 主執行緒上執行；時間成本**沒有量 → null**（不能當成 0）。

---

## 4. 證據對照（凍結證據，主機端重算；逐檔清單見 `rca-exa-devprivate-warning/evidence-replay.txt`）

計數規則（事先固定）：以精確 regex `^EXA bug: pPixmap->devPrivate\.ptr was 0x[0-9a-f]+, but should have been NULL\.$` 逐行計數。
該清單共 250 個 launcher log；其中有 manifest 的，sha256 **全部 MATCH**，0 個 MISMATCH。

### 4.1 警告次數與像素判決

| 執行 | 建置 | 設定 | 警告 | 像素判決（來源） |
|---|---|---|---|---|
| `p2-pga-rca/runtime-f592241/oracle-g-s11-01` | f592241 | MODE=G（PROTO=1） | 534 | `rgb_mismatch_pixels=0 x_errors=0 xdigest=fc22db734a833dfc`（`oracle.out`） |
| `…/oracle-ga-s11-01` | f592241 | MODE=GA（＋ASYNC=1） | 362 | `rgb_mismatch_pixels=0`，**同一個 `xdigest` `fc22db734a833dfc`** |
| `…/oracle-g-s12-01` | f592241 | MODE=G | 469 | `rgb_mismatch_pixels=0 xdigest=6a0b5095d6c50ccb` |
| `…/oracle-ga-s12-01` | f592241 | MODE=GA | 319 | `rgb_mismatch_pixels=0`，**同一個 `xdigest` `6a0b5095d6c50ccb`** |
| `…/oracle-c-s11-01`、`-s12-01` | f592241 | `TERMUX_X11_DISABLE_EXA_GPU=1` | 0（檔案 0 bytes） | `rgb_mismatch_pixels=0` |
| `p2-oracle-runtime/runtime-f592241/oracle-g0-01` | f592241 | Gate A oracle V3，`GPU_MIN_PIXELS=0` | 2624 | `verdict PASS`，`fresh_direct_reported=36`（`oracle-verdict.json`） |
| `…/oracle-gt-01` | f592241 | Gate A oracle V3，預設分流 | 0（檔案 0 bytes） | `FAIL_ATTRIBUTION`（預期中的收窄；correctness 全過，見 `PGA-GAP-5-ROUTING-FREEZE.md:31`） |
| `p2-r3-xpump-runtime/runtime-d9b7f60/r4-oracle` | d9b7f60 | R4 | 1514 | R4 **PASS** 1514/1514 fail=0 maxΔ=0（AGENTS.md） |
| `…/runtime-d9b7f60/r1-unset-oracle`、`runtime-88e3f17/r1-unset-oracle` | d9b7f60／88e3f17 | R1 | 2714／2714 | R1 unset **PASS**（AGENTS.md） |

- **CPU 模式為 0 是 PROVEN（原始碼）：** W1 到 W3 都要先有某個 Prepare* hook 回傳 TRUE（或 Gate A 准入成功），而 `lorieGpuExaDisabled()` 為真時，這些入口全部回傳 FALSE（2353、2527、3216、3233、3356）。
- **GT 的 0 要打折：** 檔案是 0 bytes，單看這個檔案無法排除擷取失敗。它與模型一致（預設分流下 oracle 的來源都 ≤ 64×64，不會升級），但只能算弱證據。
- **同一建置內的 A/B：** G0（2624）對 GT（0），同一個 f592241、同一個 fixture，只差分流門檻。支持「一定要有 AHB 升級路徑才會出現」。

### 4.2 可決定性：同一 seed 跨建置次數相同（OBSERVED）

| cell | `0245ff3` | `d1c86dd` | `11b3b79` | `f592241` |
|---|---|---|---|---|
| oracle-g-s11 | 534 | 534 | 534 | 534 |
| oracle-g-s12 | — | 469 | 469 | 469 |
| oracle-ga-s11 | 362 | 362 | 362 | 362 |
| oracle-ga-s12 | — | 319 | 319 | 319 |
| oracle-c-s11 | 0 | 0 | 0 | 0 |

（`709dfac` 的 `oracle-gat-s11-01` 也是 362。）這表示次數完全由 op 串流決定，與時序無關。所以把「警告次數」當成 oracle 的判準是可行的（§6）。
另外，f592241 的 size routing 並沒有改變這些次數，推得產生警告的 pixmap 都大於 64×64（256×256 的 pixmap 和 root）。這一點為 **INFERRED**。

### 4.3 警告指標對應 buffer format（`join-output.txt`）

做法：把每一行警告印出的位址，對上同一份 log 裡 `R3 S1_AHB … dst=<位址> … format=<f>` 映射到該位址的升級紀錄。
format 2 = R8G8B8X8（depth < 32），format 5 = B8G8R8A8（depth 32）。`unmatched` 表示沒有任何升級紀錄映射過這個位址，推定是 root，因為 root 一出生就是 AHB，不會經過升級（**INFERRED**）。

| 執行 | 總數 | 只對上 format 2 | 同位址先後映射過 2 與 5 | **只對上 format 5（BGRA）** | unmatched（root） |
|---|---|---|---|---|---|
| oracle-g0-01（Gate A direct） | 2624 | 1333 | 646 | **645** | 0 |
| oracle-g-s11-01 | 534 | 288 | 0 | 0 | 246 |
| oracle-ga-s11-01 | 362 | 224 | 0 | 0 | 138 |
| electron-gpu-probe-02 | 219 | 216 | 0 | 0 | 3 |
| electron-bench-dryrun-02（事件那一筆） | 1 | 1（646×435 的 `dst=0x76bc6a0000`） | 0 | 0 | 0 |
| gl-bench-01 | 4 | 0 | 0 | 0 | 4 |
| xfce-c0-g0-01 | 105 | 101 | 1 | 0 | 3 |

判讀：

- **沒有 Gate A direct 的執行，BGRA 上是 0。** W1 的修補與 solid 只作用在 depth < 32 的目的地：`lorieExaPrepareSolid` 在 2366 拒絕 depth ≥ 32；`lorieExaPrepareCopy` 在 2533 拒絕 depth ≥ 32 的目的地，而且要求兩端同 depth。與模型一致。
- **G0 的 645 次落在只映射過 BGRA 的位址上。** Gate A direct 的 src 必須是 BGRA（3373）。能碰 depth-32 src 的非 NULL 寫入，只有 W2/W3（W1 在 direct 路徑只修 dst：3835/3837；`lorieExaCpuOverRect` 只在 publish 回 FALSE 時執行，而 G0 `c7 DIRECT_TO_LEGACY=0`）。
  → 至少 645 次是 **Gate A 所有權碼造成的**（**INFERRED，強**。前提是 gralloc 對同一 buffer 重新 lock 時回傳同一位址；§2.4 的 R4 追蹤中 `S1 dst` 與 `S2_AHB locked` 相等，支持這個前提）。
- G0 的 Gate A 計數（`gatea-summary.txt`）：`c0 DIRECT_PUBLISH=1334`、`c6 SEMANTIC_SUCCESS=1334`、`c8 RELOCK=2668`（剛好 2×1334，即 W3 寫了 2668 次），`c9 REPAIR=1334`。
  只對上 format 2 的 1333 次，幾乎等於 1334 次 dst 修補，也就是每筆交易的 dst 被讀回一次。

---

## 5. 最小修補提案（未實作；每一項都需要明確授權）

### 5.1 Fix-2（低風險；沿用 SWIPE RCA §6 Fix-2）

在 `InitOutput.c` 加一對 static wrapper：`lorieInternalPrepareAccess(p, idx, &saved)` 和 `lorieInternalFinishAccess(p, idx, saved)`。prepare 前先存下 `devPrivate.ptr`，finish 後（或 prepare 失敗時）存回原值。
然後把 §2.2 W1 的 7 個函式（共 20 行 prepare/finish 呼叫）全部改走這對 wrapper。

- **為什麼存回原值，而不是在 `lorieFinishAccess` 裡無條件設 NULL：** 如果直接存取剛好巢狀在同一個 pixmap 的 EXA access 裡，無條件設 NULL 會讓外層的 fb 拿到 NULL。存回原值在兩種情況下都正確。
  這也和 EXA 自己在 `exa_driver.c:224-227` 的寫法相同。
- 被 EXA 呼叫的 hook 不受影響（EXA 在呼叫前已經清成 NULL）。
- **預測（事先凍結）：** 在沒有 Gate A direct 的工作負載上（oracle-g/ga、Electron、gl-bench），`EXA_BUG_LINES` 會從 534／469／362／319／219／4 變成 **0**。

### 5.2 Fix-3（Gate A 所有權碼，**需要 Sol 等級授權**）：拿掉 W2/W3 的指標發布

- **問題：** W3 在 `gateAPairRelockCpu` 寫進 src 和 dst。Fix-2 之後，`lorieExaRepairDestXByteZero` 存回的「原值」正是 W3 的值，所以 dst 仍然殘留；src 則根本沒有任何 finish 會清它。
  → **只做 Fix-2 時，G0 預期仍然 > 0**，而且至少有 645 次（§4.3）。
- **提案：** 刪掉 `InitOutput.c:3383`、`3389`、`3788`、`3796` 這 4 行 `devPrivate.ptr = …locked` 的賦值。保留 `priv->locked` 的 lock、`wasLocked` 和所有 trace／counter；3685-3686 的 NULL 可以留著，屆時它們會變成 no-op。
- **為什麼安全（INFERRED，需要 static audit 複核）：** 「locked-at-rest」這個不變式是由 `priv->locked` 承載，不是由 `devPrivate.ptr` 承載。所有 CPU 讀取者都會先經過 `loriePrepareAccess`，由 4281 重新導出指標（§3.1 的讀取者列舉）。
  3376-3379 註解說的「every reader」，在目前的樹裡找不到任何一個不經過 prepare 的讀取者。
- **為什麼要授權：** 它改的是 Gate A 的 ownership 路徑，屬於 AGENTS.md 裡 Sol High 保留的決策。修完需要重跑 Gate A oracle V3（G0）以及 R7 相關 cells，才能宣稱沒有回歸。
- **預測：** Fix-2 加上 Fix-3 之後，G0 的 `EXA_BUG_LINES` 為 **0**，`verdict` 仍為 PASS，`fresh_direct_reported` 仍為 36，`RELOCK == 2 × SEMANTIC_SUCCESS` 仍成立（counter 在 trace 那裡累加，不受影響）。

### 5.3 範圍外，順帶記錄（沒有驗證）

`LorieBuffer_convert` 在 AHB lock 失敗時（`buffer.c:304` 的 `lock_err != 0`）會跳過複製，但 366-373 仍然把 type 改成 AHB，並 `free(desc.data)`。結果是 pixmap 的內容遺失；而且 `InitOutput.c:274` 重新 lock 的回傳值也沒有檢查。
這與本警告無關，實際發生頻率 **UNKNOWN**，只記錄下來供之後處理。

---

## 6. 可決定性重現／oracle 設計

原則：判準在看到受判資料之前就凍結；次數一律**精確相等**，沒有容差；每一層都要有一個**應該變紅**的案例。

### 6.1 O-1：主機端靜態契約檢查（**已執行**，不碰裝置）

工具：`rca-exa-devprivate-warning/check_devptr_contract.py`。規則：
**D** = 在允許的 wrapper（`lorieInternalPrepareAccess`、`lorieInternalFinishAccess`）以外直接呼叫 hook；
**W** = 在 `loriePrepareAccess` 和 wrapper 以外，寫入非 NULL 的 `devPrivate.ptr`。
驗證用的變體由 `make_mutants.py` 產生：只供檢查器驗證用，**從未編譯，也不是 patch**。

| 輸入 | 預期 | 結果（`checker-output.txt`） |
|---|---|---|
| `f592241` `InitOutput.c`（sha256 `01ac42d8…`） | RED | **RED** D=20 W=4 |
| upstream `11b82d9` `InitOutput.c`（`84d671c3…`） | GREEN（對照組） | **GREEN** 0 |
| M1 = f592241 ＋ Fix-2 | RED，只剩 W | **RED** D=0 W=4（3383/3389/3788/3796 的位移後行號） |
| M2 = M1 ＋ Fix-3 | GREEN | **GREEN** 0 |
| M3 = M2，把一個 wrapper 呼叫改回直接呼叫 | **必紅** | **RED** D=1 |

M3 證明這個檢查器有能力變紅，所以 M2 的 GREEN 是有資訊的。M1 的結果則證明 §5.2 的主張：只做 Fix-2 不夠。

### 6.2 O-2：凍結證據重放（**已執行**，不碰裝置）

`evidence-replay.txt` 以同一條 regex 重算了 250 份 launcher log，並逐一核對 manifest 的 sha256。§4.2 的表就是「修補前」的**凍結預期值**。
之後任何在 f592241 上新跑的同一 cell，都必須得到完全相同的次數；不同的話，代表 fixture／環境漂移，該格判 **INVALID**，而不是 PASS 或 FAIL。

### 6.3 O-3：裝置 cells（**NOT RUN**；需要使用者明確授權；每格用新的 cell id，不重跑任何凍結 cell）

一律只在 `com.waydefu.x11gpu`／`:3` 上跑，X3 由 TermuxService 啟動（不被 ptrace）。每格前後都比對 Stable `com.termux.x11`／`:1`。
fixture 沿用**已經過資格驗證**的 `p_async_oracle`（seed 11、12）和 Gate A oracle V3，不另寫新程式。單一 op 的最小重現沿用 SWIPE RCA §7 的 D1/D2。

| Cell | 產物 | 設定 | 判準（事先凍結） | 角色 |
|---|---|---|---|---|
| E0-red | f592241（已安裝） | MODE=G seed 11 | `EXA_BUG_LINES == 534` 且 `rgb_mismatch_pixels == 0` | **必紅對照**：在修補後的判準「`== 0`」下必須 FAIL；同時再次確認可決定性 |
| E0-ctl | f592241 | MODE=C seed 11 | `EXA_BUG_LINES == 0` | 不會紅的負對照（原始碼已證明為 0） |
| E1 | Fix-2 產物 | MODE=G／GA × seed 11／12 | `EXA_BUG_LINES == 0` 且 `rgb_mismatch_pixels == 0` 且 `xdigest` 等於凍結值（s11 `fc22db734a833dfc`、s12 `6a0b5095d6c50ccb`） | Fix-2 的主要判準；`xdigest` 相等表示像素逐位元組沒變 |
| E2-scope | Fix-2 產物 | Gate A oracle V3，`GPU_MIN_PIXELS=0` | `EXA_BUG_LINES > 0`（預測 ≥ 645）且 `verdict PASS` | **範圍對照（應維持紅）**：若變成 0，代表 §4.3 的模型錯了，要回頭查，不能當成 PASS |
| E3 | Fix-2＋Fix-3 產物 | 同 E2 | `EXA_BUG_LINES == 0` 且 `verdict PASS` 且 `fresh_direct_reported == 36` 且 `c8 RELOCK == 2 × c6 SEMANTIC_SUCCESS` | Fix-3 的判準；另外需要 R7 相關 cells 的授權 |

**INVALID 條件（沒有資訊，不是 FAIL）：**
- MODE=G／GA 的 cell 在 launcher log 裡沒有任何 `R3 S1_AHB`（沒有升級，代表沒走到 AHB 路徑）。
- 統計行顯示 `exa_solid_gpu` 全為 0。
- `x-end.txt` 顯示 X 沒有活到收尾。
- X3 的 `TracerPid != 0`。
- launcher log 沒有被擷取：判斷方式是 runner 沒有產生該檔。0-byte 的檔案本身不足以區分「確實沒有輸出」和「擷取失敗」，所以同一個 session 裡必須有一格 G 類 cell 的 log 是非空的，用來證明擷取路徑有效。
- Stable 前後不同 → 立即中止。

---

## 7. 未知／未證實

- 在 f592241 的各次執行中，每一行警告確切出自哪個呼叫點：**UNKNOWN**。p2a2 stamp 自 `bfb5769` 起預設關閉，沒有 `Sprep` 可以對時間線。目前只能做到 format 層級的歸因（§4.3），以及 d9b7f60 的追蹤證明（§2.4）。
- `unmatched` 是 root：**INFERRED**。
- 每次執行的 solid 總數：統計行每 5 秒印一次，X 被收掉前最後一個窗口不會印出 → **null**。所以不能用 `exa_solid_gpu` 去界定警告次數的上限。
- gralloc 在 unlock 時會不會 unmap：**UNKNOWN**。
- xserver 端「沒有 access 外的 dereference」：只做了靜態 grep，沒有執行期證據。
- Fix-3 的安全性論證還需要 static audit 複核；特別是 R8 的 test-support 路徑（`lorie_r8_test.c`）有沒有依賴 relock 後的 `devPrivate.ptr`。grep 只找到 `pScreenPtr->devPrivate`（screen pixmap），沒有 `devPrivate.ptr`，但還沒做 symbol 層級的複核。

## 8. 產出與可重現性

`evidence/session/gl/rca-exa-devprivate-warning/`（新目錄，只有新檔；sha256 見同目錄的 `sha256sums.txt`）：

| 檔案 | 內容 |
|---|---|
| `check_devptr_contract.py` | O-1 靜態檢查器 |
| `make_mutants.py` | 產生 M1、M2、M3 驗證變體（變體檔本身不入庫，可由 f592241 原始碼重建；sha256 列在 `checker-output.txt`，已確認能逐位元組重現） |
| `checker-output.txt` | O-1 的結果與輸入 sha256 |
| `join_warn_ptr_to_format.py`、`join-output.txt` | §4.3 |
| `evidence-replay.txt` | O-2：250 份 launcher log 的計數與 manifest 核對 |

重跑方式（純主機端，不需要 adb）：

```bash
python3 evidence/session/gl/rca-exa-devprivate-warning/check_devptr_contract.py <InitOutput.c ...>
```

## 9. 沒做的事

- 沒有 build、install、adb 或裝置操作。沒有修改 `src/` 下任何檔案（worktree `git status` 與開始時相同）。沒有重跑、重判或改寫任何既有證據，包括 `INCIDENT-…` 與 `RCA-X3-EXA-DEVPRIVATE-SWIPE.md`。
- Fix-2、Fix-3 以及 §6.3 的任何一格，都需要使用者明確授權才能動手；Fix-3 另外需要 Gate A 等級的架構裁決。
