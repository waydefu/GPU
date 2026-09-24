# RCA — 滑掉實驗版後 X3 結束，與 `EXA bug: pPixmap->devPrivate.ptr ... should have been NULL`（2026-09-24）

**性質：唯讀 RCA（只讀原始碼與凍結證據）。沒有 build、install、裝置操作，沒有改產品原始碼。**
事件紀錄：`INCIDENT-20260924-X3-EXA-BUG-FATAL.md`（不改寫）。證據：`electron-bench-dryrun-02/`（凍結，不重跑、不改判）。

## 0. 判決

| 項目 | 判決 |
|---|---|
| 事件假說「renderer 消失 → pixmap 的 CPU 映射沒還 → exa.c FatalError → X3 中止」 | **FALSIFIED**（被推翻） |
| X3 在 13:46:14 結束的原因 | **PROVEN**：`GATEA_FATAL_HALT what=x-hup reason=6` → `_exit(127)`。這是 `TERMUX_X11_GATEA_PROTO=1`（MODE=G）下 P1 Gate A 的 HUP 圍堵，**照設計運作**；只要 renderer 端 socket HUP 而 generation 已綁定就會觸發，跟 GPU pixmap／EXA 無關 |
| `EXA bug: ... 0x76bc6a0000 ...` 那行 | **PROVEN 非致命**（這個 build 是 `ErrorF`，不是 `FatalError`），而且是 **13:44:28.81** 寫的——比滑掉早 **106 秒**，之後 X3 還繼續服務 Cursor |
| EXA 那行的機制 | **PROVEN（原始碼）**：lorie 內部**直接**呼叫 `loriePrepareAccess()`/`lorieFinishAccess()`，繞過 EXA 自己的 access slot；`lorieFinishAccess` 不把 `devPrivate.ptr` 設回 NULL |
| EXA 那行在本次是哪個呼叫點留下的 | **INFERRED（刪去法，強）**：`lorieExaDoneSolid` → `lorieExaRepairSolidXByte`，發生在 646×435 depth-24 pixmap 的同步 GPU solid 之後 |

一句話：**使用者滑掉實驗版會讓整個 X session 結束，是因為 dry-run 用了 PROTO=1；在 PROTO=1 下任何 renderer 斷線（滑掉、LMK、force-stop、App crash）都會刻意讓 X `_exit(127)`。** EXA 那行是另一個獨立、早就發生的非致命 bookkeeping 缺陷。

## 1. 範圍與原始碼權威

- 已安裝產物：`1.03.01-f592241-24.09.26`，APK SHA256 `f9e35b69…075c`（`installed-apk.sha256.txt`）。
- 讀的 worktree：`src/f8-ahb-exa-async`，branch `feat/exa-async-proto-20260923`。開始時 HEAD `8b905a2`（未追蹤 `tests/gl/electron_bench*`）；
  分析期間另一個 session 把那 3 個檔提交為 `a4440fa`（2026-09-24 13:59:03，只含 `tests/gl/electron_bench*`，538 行新增）。
  `git diff --stat f592241 a4440fa -- lorie` 為空 → **產品原始碼 = `f592241`**，下面所有行號都以此為準。
- xserver submodule 在該 worktree **沒有 checkout**；pin 的 SHA 是 `65d790bd`。exa 原始碼讀自 `src/upstream/lorie/src/main/cpp/xserver`
  （同一 SHA `65d790bd`、乾淨），再對照 `lorie/src/main/cpp/patches/xserver.patch` 的 exa hunk
  （`@@ -288`、`-299`、`-330`、`-344` 只加 `p2a2_emit` 儀表；**下面引用的 exa.c:313-316 不在任何 hunk 內**）。
- 證據檔 SHA256（取自凍結的 `sha256sums.txt`）：
  `x3-launcher.log 48ed36a5…aa2`、`raw-logcat.txt 91dc1ec2…53eb`、`dry-v0.stderr d80e2c2d…3769`、`mem-guard.log b0278d35…3ea9`、`env-x3.txt 690bd6a4…1323`。

## 2. 修正後的時間線

以 logcat 毫秒為準；檔案 mtime 與 logcat 出自同一顆 kernel 時鐘（PRoot 與 Android 同機，時區都是 +0800）。

| 時間 | 事件 | 證據 | 標記 |
|---|---|---|---|
| 13:44:13.176 | X3 pid 15027 以 **uid 10365（Termux）** 啟動（app_process） | logcat `AndroidRuntime: START ... uid 10365` | OBSERVED |
| 13:44:14.495 | renderer 連上；root 1200×2416 | logcat `tx11-request: window changed: 1200 2416` | OBSERVED |
| 13:44:28.804 | 第一次進入 REGULAR→AHB 升級分支（static 只印一次） | logcat `E LorieNative: GPU min pixels 4097` | OBSERVED |
| 13:44:28.80x | `LorieBuffer_convert` 把 646×435 升級成 AHB；convert 內 lock 映射 `dst=0x76bc6a0000` | `x3-launcher.log` 第 1–2 行 `R3 S1_AHB` / `R3 S2_AHB_COPY` | OBSERVED |
| 13:44:28.806 | `lorieRegisterBuffer` 把這個 AHB 送給 renderer | logcat `Sent shared buffer width 646 stride 704 height 435 format 2 type 3 id 5` | OBSERVED |
| **≤ 13:44:28.812** | **`EXA bug: pPixmap->devPrivate.ptr was 0x76bc6a0000, but should have been NULL.`** | `x3-launcher.log` 第 3 行（最後一行）；`stat` mtime `13:44:28.812975171`；runner 以 `cp -a` 複製（`run-gl-bench.sh:232`），**保留來源 mtime** | **PROVEN**（寫入時間上限） |
| 13:44:28–33 | 這 5 秒內：1 次 GPU copy、2 次 GPU solid、0 個 CPU copy rect、0 個 CPU solid rect、composite prepare 0 次成功 | logcat 統計行 `1/1 EXA copies offloaded (0 CPU rects), exa_solid_gpu=2 ... solid_rects=2 cpu_solid_rects=0 ... prepare=0/1` | OBSERVED |
| 13:44:33 → 13:46:14 | X3 沒有再印統計行（每 5 秒一次，只在計數非 0 時印）→ 這段時間沒有 frame、沒有 EXA op | `awk '$3==15027'` 只有 13:44:18、13:44:33 兩行統計 | OBSERVED；解讀為「Cursor 停在告警對話框、畫面靜止」是 **INFERRED** |
| 13:45:54 | Lens 啟動，實驗版 task 進背景 | logcat（見事件紀錄） | OBSERVED |
| 13:46:14.748 | 使用者從最近使用清單滑掉 task 140（`com.waydefu.x11gpu`） | logcat 44994 `RecentsContainer: removeTask ... com.waydefu.x11gpu` | OBSERVED |
| 13:46:14.752 | `ActivityManager: Killing 29627:com.waydefu.x11gpu/u0a503 (adj 400): SwipeUpClean` | logcat 45005 | OBSERVED |
| **13:46:14.773** | X3 tid 15329：`GATEA_SUMMARY where=x-hup ... generation=1 nextSequence=0 ... generationFatal=6 fatalReason=6 c0=0 … c20=0`，接著 `F gatea-a1: GATEA_FATAL_HALT what=x-hup reason=6` | logcat（X3 在 13:46 只有這兩行） | **OBSERVED** |
| 13:46:14.784 | mem-guard：`x3_rss_mb=0`，`# mem-guard end: x3 15027 gone`（前一筆 .254 時 rss 212 MB、MemAvailable 5111 MB） | `mem-guard.log` 尾端 | OBSERVED |
| 13:46:14.789 | Cursor：`X connection to :3 broken (explicit kill or server shutdown).` | `dry-v0.stderr` | OBSERVED |

重點：
1. X3（uid 10365）與被殺的 App 程序（u0a503）是不同 uid、不同程序；`SwipeUpClean` 只殺 29627。X3 是 **21 ms 後自己結束**的。
2. X3 結束時 **stderr 沒有任何新內容**（launcher log 最後寫入仍是 13:44:28.81）。若是 exa.c `FatalError`，stderr 會有 `Fatal server error:` 等字樣；沒有，因為 `lorieGateAFatalHalt` 只寫 logcat 就 `_exit(127)`（見 §3）。

## 3. 發現 A — X3 死因：PROTO=1 的 `x-hup` 停機（PROVEN）

### 3.1 證據鏈（原始碼，`f592241`）

| # | 位置 | 內容 |
|---|---|---|
| A1 | `electron-bench-dryrun-02/env-x3.txt`、`start-x3.out` | `TERMUX_X11_GATEA_PROTO=1`（`run-gl-bench.sh` MODE=G） |
| A2 | `lorie/src/main/cpp/lorie/lorie.h:256-259` | `lorieGateAProtoEnabled()`：env 剛好是 `"1"` |
| A3 | `cmdentrypoint.cpp:1364-1372` `handleLorieEvents` | PROTO 開 → `handleLorieEventsProto`；PROTO 關 → `handleLorieEventsLegacy` |
| A4 | `cmdentrypoint.cpp:1309-1320` `handleLorieEventsProto` | `ready & X_NOTIFY_ERROR`（POLLHUP/POLLERR）→ `closeLorieConnection(fd)` → **`if (lorieGateAActive()) gateAFatalFromInput(LORIE_GATEA_FAIL_GENERATION, "x-hup")`** |
| A5 | `cmdentrypoint.cpp:612-624` `gateAFatalFromInput` | publish fatal → `lorieGateADumpSummary(st, what)`（= logcat 的 `GATEA_SUMMARY where=x-hup`）→ `gateABroadcastGateAFailed()` → `lorieGateAFatalHalt(what, reason)` |
| A6 | `lorie.h:1414-1417` `lorieGateAFatalHalt` | `__android_log_print(FATAL, "gatea-a1", "GATEA_FATAL_HALT what=%s reason=%u")`；**`_exit(127)`** |
| A7 | `lorie.h:287` | `LORIE_GATEA_FAIL_GENERATION = 6` → 對上 `reason=6` |
| A8 | `InitOutput.c:638-649` `lorieGateAActive` | 只要求 PROTO 開、atomics lock-free、`sessionNonce != 0`、`generation != 0`、沒有已 publish 的 fatal。**完全不看有沒有 Gate A 交易在進行** |
| A9 | `cmdentrypoint.cpp:1519-1531` → `InitOutput.c:590-619` `lorieActivityConnected` | **每次** renderer 連線都 `lorieGateAProtocolInit(..., generation + 1)` → 連上就有 generation（本次 `generation=1`） |

所以在 PROTO=1 下，renderer 一連上，`lorieGateAActive()` 就是真；之後任何 HUP 都走 A4 → A6。
本次 summary 的 `nextSequence=0`、`c0..c20` 全為 0，表示這個 generation **一次 Gate A 交易都沒做過**，照樣停機。

### 3.2 是哪一個 `x-hup` 呼叫點

`x-hup` 共有四處：`cmdentrypoint.cpp:1317`（ospoll HUP，本節 A4）、`cmdentrypoint.cpp:862`（legacy handler 內，只在 PROTO 開時執行，但 PROTO 開時根本不會進 legacy handler → 實際上是死碼）、
`InitOutput.c:2003/2007`（`lorieGpuCopyWait` 迴圈）、`InitOutput.c:3474/3476`（`gateAWaitTerminal`，R7-10 的路徑）。
後兩者只在「X 正在等某個 GPU serial」時才會跑；X3 從 13:44:33 起就沒有任何 op（§2），所以本次是 **`cmdentrypoint.cpp:1317`：INFERRED（強）**。
不論是哪一處，結果都一樣是 `x-hup/6` → `_exit(127)`，所以判決不受影響。

### 3.3 為什麼這是「照設計」

- `cmdentrypoint.cpp:854-857` 的註解：*"P1 Gate A supplement: an active generation cannot survive HUP ... then halt without normal cleanup."*
- R7-10 的判準本來就是 `x-hup reason=6`（`GATE-A-P2-R7-10-RCA-REPAIR-20260917.md`，8545b26 R7-10 PASS `last halt x-hup/6`）。
  但 **R7-10 構造的是「有交易在飛」的 HUP**（PUBLISH seq=28 → CONSUME_DIRECT seq=29 → renderer `_exit`），判準路徑是 Done 等待內的 `gateAWaitTerminal`。
  本次是 **idle HUP**（沒有任何交易），P1 仍然一律停機。
- 對照 PROTO 關（`cmdentrypoint.cpp:847-866` `handleLorieEventsLegacy`）：`X_NOTIFY_ERROR` → `closeLorieConnection(fd)` → Gate A 分支條件 `lorieGateAProtoEnabled() && ...` 為假 → `return`，**X 繼續活著**；下次 App 開起來 `getXConnection` 會建新 socketpair 重連。
  → 「Stable 被滑掉 X 應該繼續活著」這個直覺，在原始碼層級對 PROTO 關的路徑成立（**SOURCE PROVEN，本機未實測**），但**有 §5 R-1 的例外**。

## 4. 發現 B — `EXA bug` 那行：非致命、早 106 秒、機制已證實

### 4.1 為什麼不是 FatalError（PROVEN）

| # | 位置 | 內容 |
|---|---|---|
| B1 | `xserver/exa/exa.c:313-316`（65d790b） | `if (pPixmap->devPrivate.ptr != NULL) EXA_FatalErrorDebug(("EXA bug: pPixmap->devPrivate.ptr was %p, but should have been NULL.\n", ...));` |
| B2 | `xserver/exa/exa_priv.h:85-95` | `#ifdef DEBUG` → `FatalError`；`#else` → **`ErrorF`**（`EXA_FatalErrorDebug` 不 return，只印） |
| B3 | `xserver/exa/exa_priv.h:29-30` | 先 `#include <dix-config.h>` |
| B4 | `lorie/src/main/cpp/patches/dix-config.h.in:151`、`recipes/xserver.cmake:2` | **`#undef DEBUG`**；該檔經 `configure_file` 原樣產生 `dix-config.h`（`#undef` 行不會被 CMake 改寫）；`recipes/xserver.cmake` 的 compile options 也沒有 `-DDEBUG` |

→ 這個 build 的那行只是 `ErrorF`。印完之後 `ExaDoPrepareAccess` 照常往下跑：`exa.c:318-327` 覆寫 `devPrivate.ptr`，接著呼叫 driver 的 `loriePrepareAccess` 再設一次正確值（`InitOutput.c:4281`）。**會自我修正，不會終止程序。**
X3 在那之後還活了 106 秒（mem-guard 持續量到 rss 212 MB），也證實這一點。

### 4.2 機制：lorie 內部直接存取繞過 EXA bookkeeping（PROVEN，原始碼）

EXA（driver mode：`EXA_OFFSCREEN_PIXMAPS | EXA_HANDLES_PIXMAPS`，`InitOutput.c:4317`）的不變式是：**pixmap 不在 `exaPrepareAccess` 裡時，`devPrivate.ptr` 必須是 NULL。**
EXA 自己在三個地方維持它：

- `exa.c:420-423` `exaFinishAccess`：`/* We always hide the devPrivate.ptr. */ pPixmap->devPrivate.ptr = NULL;`（在呼叫 driver `FinishAccess` **之前**）
- `exa_driver.c:183-185` `exaModifyPixmapHeader_driver`：`/* Always NULL this, we don't want lingering pointers. */`
- `exa.c:313-316` 在 prepare 時檢查（B1）

lorie 的 hook：

- `InitOutput.c:4281` `loriePrepareAccess`：`pPix->devPrivate.ptr = priv->locked ?: priv->mem;`
- `InitOutput.c:4296-4312` `lorieFinishAccess`：處理 mutex 與 `wasLocked`，**不碰 `devPrivate.ptr`**（被 EXA 呼叫時不需要，因為 EXA 已先清掉）。

但 lorie 有 **7 個呼叫點在 EXA 的 access slot 之外直接呼叫這對 hook**，結束後 `devPrivate.ptr` 就停在 `priv->locked`：

| 呼叫點 | 何時執行 | 本次 13:44:28–33 有沒有跑 |
|---|---|---|
| `lorieExaRepairSolidXByte` `InitOutput.c:2319-2345`（prepare 2326、finish 2344） | 同步 `lorieExaDoneSolid`（`2462-2483`，呼叫在 2475/2477）：只要有 GPU solid 被排程且 `dst->drawable.depth < 32` 就一定跑（修 RGBX 的 X byte） | **有**：`exa_solid_gpu=2 solid_rects=2`；`lorieExaPrepareSolid` 只收 bpp 32 且 depth < 32（`2347-2382`）→ 必定進修補 |
| `lorieExaCpuSolidRect` `2296-2317` | GPU solid 排不進去時的 CPU 補畫 | 沒有：`cpu_solid_rects=0` |
| `lorieExaCpuCopyRect` `2485-2510` | GPU copy 排不進去時的 CPU 補畫 | 沒有：`(0 CPU rects)` |
| `lorieExaCpuOverRect` `3876-3899`（呼叫 3974/4032） | 只在 GPU composite prepare 成功之後 | 沒有：`prepare=0/1` |
| `lorieExaRepairDestXByteZero` `3901-3935`（呼叫 3835/3837/4067/4069） | 同上 | 沒有：`prepare=0/1` |
| `lorieExaAsyncFlushPixmap` `2161-2168`、`lorieExaAsyncFlushAll` `2172-2190` | 只在 `TERMUX_X11_EXA_ASYNC=1` | 沒有：`exa_async_engaged_lines=0`，env 無此變數 |

另外還有 Gate A pair 路徑**刻意**在 slot 外寫 `devPrivate.ptr`：`InitOutput.c:3383/3389`（reserve 時）、`3685-3686`（轉移時清 NULL）、`gateAPairRelockCpu` `3788/3796`（Done 後留著）。
註解寫明是設計（*"Fresh locks restore devPrivate.ptr immediately so every reader sees a valid mapping"*）。本次 Gate A 計數全為 0，**沒跑**；它屬於凍結的 Gate A 語意，本 RCA 不建議動它，只記錄它會產生同一行警告。

### 4.3 本次是哪個呼叫點（INFERRED，刪去法）

1. 升級與那行警告在同一個 X 請求序列內：logcat `.804`（升級分支）→ `.806`（註冊 646×435）→ launcher log mtime `.812`（警告）。
2. 警告裡的位址 `0x76bc6a0000` 等於 `LorieBuffer_convert` 內 lock 這個 646×435 AHB 得到的映射（S1/S2 的 `dst=`）。
   convert 之後 `buffer.c:359` unlock，`lorieEnsureGpuSampleable` 再 `LorieBuffer_lock(priv->buffer, &priv->locked)`（`InitOutput.c:274`）。
   gralloc 對同一個 buffer 重 lock 回傳同一個位址是 **INFERRED**（與位址相等一致，但沒有直接量到 `priv->locked`，p2a2 stamp 預設關）。
3. 在這 5 秒窗內，7 個直接呼叫點中**只有 `lorieExaRepairSolidXByte` 的前提成立**（上表）。
4. 所以最可能的序列：Cursor 對 646×435 backing pixmap 做 `FillRectangle` → `lorieExaPrepareSolid` → `lorieEnsureGpuSampleable`（升級＋印 S1/S2）→ `lorieExaSolid` → `lorieTryScheduleGpuSolid` → `lorieRegisterBuffer`（`Sent shared buffer`）→ `lorieExaDoneSolid` → 等待完成 → `lorieExaRepairSolidXByte` 留下 `devPrivate.ptr = 0x76bc6a0000` → 下一次 CPU 存取（例如 `PutImage`：lorie 沒設 `UploadToScreen`，`exa_accel.c:152-154` 回 FALSE → `ExaCheckPutImage` → `exaPrepareAccess`）→ `exa.c:313-316` 印出警告。

「對象是 646×435 且觸發者是 solid 修補」= **INFERRED（強）**；「這個類別的缺陷存在且會產生這行」= **PROVEN**。

### 4.4 這個缺陷的實際風險

- 本 build：只印警告、會自我修正。**跟 renderer 死亡、跟 X3 結束都沒有因果關係。**
- 若哪天以 `-DDEBUG` 或定義 `DEBUG` 的設定 build xserver，這行會變成真的 `FatalError`：只要 GPU solid 打到 depth-24 pixmap、之後 CPU 再碰它，X 就會死。
- 殘留指標可能懸空：`lorieFinishAccess` 在 `wasLocked == FALSE` 時會 unlock 並把 `priv->locked` 設 NULL，但 `devPrivate.ptr` 還指著舊映射。目前樹內沒有在 access 外讀 `devPrivate.ptr` 的正式路徑（只有預設關閉的診斷 stamp），所以這是**潛在**風險，不是已觀察到的錯誤。
- 已檢查並排除：殘留指標被 `exaModifyPixmapHeader_driver:170-172` 鎖存進 `sys_ptr`。這需要對已升級的 pixmap 再呼叫一次 `ModifyPixmapHeader(..., NULL)`，而 lorie 只在第一次 REGULAR→AHB 時呼叫（`InitOutput.c:273`），以及 DRI3 匯入建立時呼叫（`4355/4382`，那時還沒有殘留）→ **原始碼層級不可達**。

## 5. 相關、本次沒觸發的殘留風險（SOURCE PROVEN，裝置 NOT RUN）

**R-1 PROTO 關也不是完全「滑掉不死」。** `gateAXFatal`（`InitOutput.c:3484-3505`）沒有 PROTO 閘門，最後一樣呼叫 `lorieGateAFatalHalt` → `_exit(127)`。
`lorieGpuCopyWait`（`InitOutput.c:1985-2012`）遇到 `lorieGateAClassifyWaitWake`（`lorie_gatea_wait_wake_class.h:34-56`）回 `X_HUP`（socket 斷）或 `SURFACE_LOSS`（`lorieRendererAvailable()` = `surfaceAvailable` 為假，`InitOutput.c:1611-1613`，App 進背景就會發生）時回 FALSE；
下面兩個包裝在回 FALSE 時會直接停機：

- `lorieGpuCopyWaitForPresentOrFatal`（`InitOutput.c:2015-2019`，由 `patches/xserver.patch` 的 `present_gpu_copy_retire_or_fatal` 呼叫）→ `x-present-copy-wait` reason=4
- `lorieGpuCopyWaitForCompositeOrFatal`（`InitOutput.c:2024-2031`，由 `lorieExaDoneComposite` `4057` 呼叫；來自 `0d72332` 刻意的 fail-stop）→ `x-exa-composite-wait` reason=4

所以只要**有 GPU Present copy（例如 DRI3/Present 的 GL app）或 GPU composite 正在等完成**時滑掉、或把 App 切到背景，即使 PROTO 關，X 也會停機（**可達性 INFERRED**：新的 op 在 `!surfaceAvailable` 時會被拒絕排程，所以窗口是「排程後、完成前」那一段；renderer 在沒有 surface 時會不會繼續清 queue，沒有驗證）。
EXA copy／solid 走的 `lorieExaDoneCopy`／`lorieExaDoneSolid` 只記 `wait timeout` 就繼續，不會停機（但該次 GPU 寫入可能沒發生，畫面內容會少一塊）。

**R-2** `handleLorieEventsProto` 的 `LORIE_RECORD_PEER_CLOSED` 分支（`cmdentrypoint.cpp:1348-1360`）同樣在 `lorieGateAActive()` 時停機（`x-eof`）。修 §6 Fix-1 時必須兩個分支一起處理，否則只是把 `x-hup` 換成 `x-eof`。

**R-3** `priv->wasLocked` 是單一旗標。若直接存取巢狀在同一個 pixmap 的 EXA access 裡，內層會蓋掉外層的 `wasLocked`。目前沒有找到會巢狀的呼叫序列，只記錄。

## 6. 修補提案（未實作；每一項都需要明確授權）

### Fix-0（運維，不改碼）— 日常使用不要開 PROTO=1

`TERMUX_X11_GATEA_PROTO=1` 是 Gate A 資格測試用的原型協定（Production Gate A 仍 BLOCKED）。它的 P1 規則讓任何 renderer 斷線都讓 X 結束。
日常用或長時間 benchmark 時用 PROTO 未設（legacy handler，§3.3），就不會因為 idle 時滑掉而結束；**R-1 的例外仍然存在**。
對 ELECTRON-BENCH：MODE=G 這一格本來就含 PROTO=1 的語意，runner 已規定「正式跑不得切 App／滑掉」，這條規則要保留。

### Fix-1（X 端，Gate A 政策變更，需 Sol 等級授權）— idle HUP 不停機

**不變式論證**：lorie 不呼叫 `InputThreadPreInit()`，`handleLorieEvents` 是 X 主執行緒上的 ospoll callback，只在 `WaitForSomething` 內、兩個請求之間執行。
Gate A direct 交易是同一執行緒上同步的 Prepare→Composite→Done（`InitOutput.c:2627` lease 註解），Done 只在 SUCCESS 或停機時才 return。
因此 callback 執行時 `gateAPairActive()`（`InitOutput.c:2648-2650`）應為假；有交易在飛時的 HUP 由 Done 內的 `gateAWaitTerminal` 自己處理（`InitOutput.c:3474`，R7-10 路徑）。
重連本來就有處理：`lorieActivityConnected`（`InitOutput.c:590-619`）在舊 generation 仍綁定時會先 poison、`lorieGateARegistryCloseGeneration`，再 init `generation + 1`。

**最小改動**（示意，不是 patch）：

```c
/* cmdentrypoint.cpp, handleLorieEventsProto — both X_NOTIFY_ERROR and PEER_CLOSED */
if (lorieGateAActive()) {
    if (lorieGateAPairActiveForHup())          /* new extern accessor of gateAPairActive() */
        gateAFatalFromInput(LORIE_GATEA_FAIL_GENERATION, "x-hup");   /* unchanged: in-lease HUP */
    /* idle generation: poison it so nothing admits, close its registry, survive like legacy;
     * lorieActivityConnected() starts generation+1 on reconnect */
    lorieGateAPublishFatal(lorieGateAShared(), LORIE_GATEA_FAIL_GENERATION);
    lorieGateARegistryCloseGeneration(nonce, generation);
    gateABroadcastGateAFailed();
    log(ERROR, "GATEA_HUP_IDLE_SURVIVE generation=%llu", generation);
}
closeLorieConnection(fd); lorieRecordDecoderDestroy(...); gateARecordDecoderReady = 0; lorieGateACancelDeferred(0, 0);
return;
```

必須先確認的前提（寫碼前的 static audit 項目）：
(a) publish fatal 之後 `lorieGateAActive()` 為假 → 所有 admission 退回 D0a／CPU（`InitOutput.c:649`）；
(b) `lorieActivityConnected` 在 fatal 已 publish 時仍能正確 re-init（它先檢查 `generation != 0` 再 publish 一次，需確認重複 publish 是冪等的）；
(c) 被 poison 的 generation 的 registry 關閉，不會讓舊 READY slot 在新 generation 被沿用；
(d) legacy GPU queue（copy/solid/D0a composite）的在途 entry 在斷線後由既有 timeout／`lorieConnectionAlive` 路徑處理（與 PROTO 關相同）。
這會改變「P1: an active generation cannot survive HUP」這條凍結規則的適用範圍，**必須由使用者或 Sol 明確授權**，並且要重跑下面 §7 的 K1/K3。

### Fix-2（X 端，低風險）— 內部直接存取後還原 `devPrivate.ptr`

在 `InitOutput.c` 加一對 static helper，讓 7 個直接呼叫點改用它（**不動** Gate A pair 的 3383/3389/3788/3796）：

```c
/* lorie-internal CPU access outside exaPrepareAccess: EXA requires devPrivate.ptr to be NULL
 * whenever the pixmap is not inside an EXA access (exa.c ExaDoPrepareAccess). Put back what was
 * there: NULL, or the pointer of an enclosing EXA access. */
static Bool lorieInternalPrepareAccess(PixmapPtr p, int index, void **saved) {
    *saved = p->devPrivate.ptr;
    if (loriePrepareAccess(p, index))
        return TRUE;
    p->devPrivate.ptr = *saved;
    return FALSE;
}
static void lorieInternalFinishAccess(PixmapPtr p, int index, void *saved) {
    lorieFinishAccess(p, index);
    p->devPrivate.ptr = saved;
}
```

為什麼用「存回原值」而不是在 `lorieFinishAccess` 無條件設 NULL：若直接存取剛好巢狀在同一個 pixmap 的 EXA access 內，無條件設 NULL 會讓外層 fb 拿到 NULL 而當機；存回原值在兩種情況都正確。
被 EXA 呼叫的 `lorieFinishAccess` 不受影響（EXA 在呼叫前已清 NULL）。

## 7. 測試設計（可決定性重現；before 必紅、after 必綠）

### 7.1 對立假說

- **H0（事件假說）**：renderer 死亡讓 GPU pixmap 的映射沒還，所以才出現 `EXA bug` 並終止。
- **H1（本 RCA）**：`EXA bug` 由「同步 GPU solid 打到 depth-24 pixmap → X-byte 修補直接存取」造成，與 renderer 死活無關；X 結束只在 PROTO=1（或 R-1 的等待中）且是 `x-hup/6`。

### 7.2 Fixture（新寫，小型 Xlib C 程式 `p_devptr_hup`）

1. `XCreatePixmap` depth 24、**646×435**（> 4096 px，會被升級）。
2. `XFillRectangle` 整張，GC `GXcopy`、fg `0x336699` → GPU solid ＋ X-byte 修補。`XSync`，stdout 印 `STEP fill_done`。
3. 等 runner 的 go 訊號（stdin 一行），讓 runner 決定這格要不要殺 renderer。
4. `XPutImage` 8×8 於 (10,10)，內容 `0x00cc00`（走 `ExaCheckPutImage` → `exaPrepareAccess`）。`XSync`，印 `STEP put_done`。
5. `XGetImage` 整張 → 逐像素比對：8×8 區 = `0x00cc00`，其餘 = `0x336699`，**完全相等**（不接受 ±1）；印 `PIXELS mismatch=<n>`。

Runner 每個 STEP 後記下 launcher log 的位元組長度，`EXA_BUG_LINES(step)` = 該段新增內容中符合
`^EXA bug: pPixmap->devPrivate\.ptr was 0x[0-9a-f]+, but should have been NULL\.$` 的行數。

### 7.3 Cells（全部只在 `com.waydefu.x11gpu`／`:3`；每格一個新 X3；Stable `com.termux.x11`／`:1` 前後比對）

| Cell | 設定 | 構造 | 修補前預期（H1） | 修補後預期 | H0 預測 |
|---|---|---|---|---|---|
| **D1** devptr-nokill | PROTO 未設、GPU EXA 開 | 不殺 renderer | `EXA_BUG_LINES(put)=1`、X 活著、mismatch=0 | Fix-2 後 `EXA_BUG_LINES=0`、X 活著、mismatch=0 | 0（沒殺就不該有） |
| **D2** devptr-cpu-control | `TERMUX_X11_DISABLE_EXA_GPU=1` | 不殺 | `EXA_BUG_LINES=0` | `EXA_BUG_LINES=0` | 0 |
| **K1** hup-idle-proto1 | PROTO=1 | `fill_done` 後殺 renderer | 2 s 內 X3 logcat 出現 `GATEA_FATAL_HALT what=x-hup reason=6`、X3 死、`fill_done`→死亡之間 `EXA_BUG_LINES=0` | Fix-1 後：無 `GATEA_FATAL_HALT`、有 `GATEA_HUP_IDLE_SURVIVE`、5 s 後 X3 活著；`am start` 重連後 generation=2，fixture 繼續 → mismatch=0 | 死亡時應出現 `EXA bug` |
| **K2** hup-idle-legacy | PROTO 未設 | 同 K1 | X3 活著、重連後 mismatch=0；`EXA_BUG_LINES(put)=1`（Fix-2 前） | 同左但 `EXA_BUG_LINES=0` | 殺了之後才出現 |
| **K3** hup-inflight-proto1（回歸防護） | PROTO=1＋test-support 產物 | R7-10 式構造（renderer 在 CONSUME_DIRECT 後 `_exit`），**新 cell id** | `x-hup` reason=6 | **不變**：`x-hup` reason=6 | — |

- **必紅對照**：D1 在 `f592241` 上必須是 `EXA_BUG_LINES=1`；K1 在 `f592241` 上必須停機。若修補前沒紅，代表構造沒走到那條路 → 該格 **INVALID**，不是 PASS。
- **H0 的判別**：D1（沒殺卻有警告）與 K1（殺了、死因是 `x-hup/6`、死前沒有新增警告），兩格合起來推翻 H0。
- **殺 renderer = construction**：用 `adb shell am force-stop com.waydefu.x11gpu`（只影響 u0a503；X3 是 Termux uid 10365，不會被一起殺），殺之前記下 Activity pid 與 `/proc/<pid>/cmdline`；不用 broad pkill。也可以請使用者親手滑掉以還原原始觸發，兩種構造要分開記錄，不能混在同一格判。

### 7.4 先凍結的判準（看到資料前定案）

- `X_ALIVE` = 構造後 5.0 s `/proc/<x3pid>` 存在。
- `HALT` = X3 pid 的 logcat 精確字串 `F gatea-a1: GATEA_FATAL_HALT what=<w> reason=<r>`。
- `EXA_BUG_LINES` = 上面 regex 在該 STEP 區段的精確行數。
- `PIXELS` = `mismatch == 0`。
- **INVALID**（沒資訊，不是 FAIL）：X3 被 trace（`TracerPid != 0`）；該格沒有 `R3 S1_AHB ... w=646 h=435`（沒升級＝沒走到 AHB 路徑）；D1/K* 在 fill 那 5 s 的統計行 `exa_solid_gpu=0`（solid 沒走 GPU）；K* 構造後 Activity pid 仍存在（沒殺成）；Stable 前後不同 → 立即中止。

## 8. 未知／未證實

- 本次 `x-hup` 是 `cmdentrypoint.cpp:1317` 而不是等待迴圈（§3.2）：INFERRED（強），沒有 trace 直接證明。
- `priv->locked == 0x76bc6a0000`（gralloc 重 lock 回同一位址）：INFERRED。
- 646×435 是 Cursor 的 backing pixmap、13:44:33 之後畫面靜止是因為停在告警對話框：INFERRED（使用者在 13:45:53 翻譯了 Cursor 的 EFAULT 告警，與此一致）。
- R-1 在實機的可達頻率：NOT RUN。
- Fix-1 前提 (a)–(d)：尚未 audit。

## 9. 這份 RCA 沒做、也不授權的事

- 沒有 build、install、adb、裝置操作；沒有修改 `src/` 任何檔案；沒有重跑或改寫 `electron-bench-dryrun-02/` 與事件紀錄。
- 不重判 dry-run 02（維持「工具檢查不成立（X3 中止）」；本 RCA 只更正它的**原因**：X3 中止是 PROTO=1 的 `x-hup/6`，不是 EXA）。
- Fix-0/1/2 與 §7 任何一格，都需要使用者明確授權後才能動手。
