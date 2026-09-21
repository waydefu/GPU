# V1-CORE EXECUTOR-GRADE MASTER PLAN V2
### POCO F8 Ultra / Termux:X11 / Adreno 840 — Production Gate A / V1-Core GPU acceleration

| | |
|---|---|
| 版本 | V2.3（2026-09-21，measurement pass：V-7R 實測修正；**P007 / P008 / P003 已於同日關閉**） |
| 取代 | V2.0 樹狀版（29 檔）— 內容全部併入本檔 |
| 上游快照 | `waydefu/GPU` PR #10，HEAD `697e16f3dab21946d77860b82c7e4ceeb8fe761e` |
| 狀態 | **DESIGN ONLY — 未 commit、未執行、未授權任何 runtime** |
| 目前進度 | R7 13/13 PASS · **R8 8/10 PASS**（C1·C2·C3-window·C3-disconnect·C4·C5-full·C5-overflow·D）· **P1/P2 = `INVALID_CONSTRUCTION` / `DESIGN_REQUIRED`（GAP-9：Gate A pair-lease 路徑從未進入，`EVENT_LEASE_GPU_OWNED` 在任何 cell 皆 0 次）** · Production Gate A **BLOCKED** · V1-Core **NOT QUALIFIED** |

---

## 0. 本輪執行邊界

本輪只做：`READ` `RECONCILE` `TRACE` `VERIFY` `DESIGN` `PLAN` `WRITE DOCS` `WRITE FUTURE PACKETS`

本輪**未做**，且不得被下游解讀為已做：

| 動作 | 狀態 |
|---|---|
| ADB runtime mutation | NOT PERFORMED |
| R8-C1 attempt-09 | NOT STARTED / NOT AUTHORIZED |
| `runtime-b984ded/r8-c1/attempt-09/` | NOT CREATED |
| C2 / R9 / R10 | NOT STARTED |
| APK build / install / CI dispatch | NOT PERFORMED |
| source / tooling / judge / collector mutation | NOT PERFORMED |
| merge / runtime grant | NOT PERFORMED |
| frozen attempt reclassification | NOT PERFORMED |
| git commit | NOT PERFORMED |

任何 command 若其 exact form 尚未在 repo 中確認存在，一律標 `PROPOSED / NOT YET EXECUTABLE`。

---

## 1. 交叉查驗紀錄（CROSS-CHECK LEDGER）

本節由 V2.1 的外部交叉查驗延伸為 V2.2 correction pass。前九項維持以**官方／上游第一手來源**為主；
V2.2 另加入 current repo / PR 實際內容對帳與 executor 語意修正。
結論分四類：`CONFIRMED`（原文可用）、`CORRECTION`（原文需改）、`PARTIALLY_RESOLVED`（已縮小但仍需 current product source 完整綁定）、
`UNRESOLVED`（仍不可下 product verdict）。

---

### V-1 `CONFIRMED` — `DE_TERMINATE` 與 `ddxGiveUp` 的因果關係

X.Org 上游 `include/opaque.h`：
```c
#define DE_RESET          1
#define DE_TERMINATE      2
#define DE_PRIORITYCHANGE 4
```
上游 DDX 文件原文（dmx 為例）：`ddxGiveUp()` 由 `Xserver/dix/main.c` 的 `main()` 在
`dispatchException & DE_TERMINATE` 時呼叫，而這是**唯一**能不經中斷離開 main loop 的路徑。

→ 終止契約中 `DE_TERMINATE → … → ddxGiveUp` 的因果鏈成立。無需修改。

來源：`x.org` / `xorg-server` `include/opaque.h`、`hw/dmx/dmxinit.c` doxygen 註解。

---

### V-2 `CONFIRMED`（且強化）— `GiveUp(0)` 的真正語意

上游 `os/utils.c`：
```c
SIGVAL GiveUp(int sig)
{
    int olderrno = errno;
    dispatchException |= DE_TERMINATE;
    isItTimeToYield = TRUE;
    errno = olderrno;
}
```

`GiveUp` 是 Xserver 的 termination handler/function，會被 signal path 使用，也可被程式內直接呼叫。
契約裡的 `GiveUp(0)` 代表 **以 sig=0 直接 in-process 呼叫該函式**，不是遞送 SIGTERM。

→ 這**強化**了既有禁令。SIGTERM 與 opcode 3 最終都寫同一個 `dispatchException` 變數，
所以「結果看起來一樣」——但 provenance 完全不同：
一個經 signal handler 進入，一個由 `ProcLorieR8Terminate` 同步進入。

**新增判準（寫入每個 R8 packet 的 `FORBIDDEN_TRACE`）：**
> 不得僅以 `dispatchException` 最終值相同，論證 terminate 路徑正確。
> 必須證明**進入點**是 `ProcLorieR8Terminate` 而非 signal handler。
> 兩者在 semantic stream 中必須可區分；若不可區分，該 harness 為 `INVALID`。

---

### V-3 `PARTIALLY_RESOLVED` ⚠ — terminal contract 已縮小，但 C1 前仍必須 source-bind

上游 `dix/main.c` 顯示 DIX teardown 中 `FreeAllResources()` 與 `CloseScreen()` 的順序，與舊文件裡模糊的
「CloseScreen → resource teardown」字面並不等價。這個衝突不能直接拿來判 product FAIL，因為 `resource teardown`
可能是指 **Gate A / lorie 自有 registry drain**，不是 DIX `FreeAllResources()`。

V2.2 重新檢查 current product `b984ded` 的 `InitOutput.c`，已確認：

- `lorieCloseScreen()` 進入後先 emit `X_CLOSE_ENTER`。
- 若 Gate A enabled，`lorieCloseScreen()` 會直接呼叫 `gateACloseGeneration()`。
- `gateACloseGeneration()` 會停止新 admission、等待 terminal、檢查 queue drain、逐一 retire registry、送 generation close，最後把 generation / nonce 清零。
- 之後 `lorieCloseScreen()` 才 destroy screen pixmap 並 delegate 回 wrapped `CloseScreen`。
- `ddxGiveUp()` 是 X `END` producer；current source 註解明確把它定位在 `CloseScreen` / `FreeFonts` / `ClearWorkQueue` 之後的 DE_TERMINATE terminal hook。

因此已可排除一件事：**Gate A resource drain 不是 ddxGiveUp 之後的事；它位於 lorie CloseScreen 內。**
但 pinned xserver `dix/main.c` 的 exact current-product 版本與 `ClearWorkQueue()` 的 terminate-path 程式位置仍需要 source-level 綁定，
不能只靠上游版本或註解替代。

**V2.2 處置：**
- `V2-P007-TERMINAL-CONTRACT-SOURCE-BIND` 從「軟前置」升為 **R8-C1 的 HARD prerequisite**。
- P007 必須讀 current `b984ded` 對應的 pinned xserver source / patch lineage，產出唯一的 terminal sequence。
- P007 完成前，`V2-R8-C1-09` 只能是 `FULL_SPEC_EXECUTION_BIND_PENDING`，**不得簽 runtime grant、不得 invoke runner**。
- P007 不得改 frozen evidence；只裁決「哪個 event/函式必須出現、哪些只是 DIX 內部順序、ClearWorkQueue 是否是 terminate-path 必經點」。
- 只有 P007 的 source-bound sequence 可以進 C1 `EXPECTED_TRACE`；V2.1 內硬寫的 `CloseScreen → resource drain → ClearWorkQueue` 不再直接當 judge 規則。

這個修正避免 attempt-09 因 specification false-red 再被浪費。

---

### V-4 `CONFIRMED`（且大幅強化）— C3-window 的兩種合法 trace 有協定層依據

`presentproto` 官方協定文字：

```
PRESENTOPTION { PresentOptionAsync, PresentOptionCopy, PresentOptionUST,
                PresentOptionSuboptimal, PresentOptionAsyncMayTear }
```
```c
#define PresentOptionAsync        (1 << 0)
#define PresentOptionCopy         (1 << 1)
#define PresentOptionUST          (1 << 2)
#define PresentOptionSuboptimal   (1 << 3)
#define PresentOptionAsyncMayTear (1 << 4)
```
→ **`ASYNC|COPY` == `0x3`**（packet 必須寫死這個值，不得由 executor 自行組合）

協定原文三句關鍵規定：
1. 帶 `PresentOptionCopy` 時，pixmap 會 idle，且 `idle-fence` 在操作發生時即觸發。
2. **若 window 在 presentation 發生前被 destroy，該 presentation action 就不會完成。**
3. `PresentPixmap` 會持有 pixmap 的 reference 直到 presentation 發生，
   所以 pixmap 可在 request 執行後立即 free，即使 presentation 尚未發生。

→ 第 2 句是 `waited = 0` 合法的**協定層依據**；第 1、3 句說明
「pixmap 已 free」與「presentation 未完成」可以同時為真而不違反協定。

**C3-window acceptance 因此修訂為（新增三項必證）：**
```
既有：waited ∈ {0,1} 皆合法，judge 不得以 waited 值本身判 FAIL
新增：Copy 語意下 idle-fence 必須在操作發生時觸發（或證明操作未發生）
新增：PresentPixmap 對 pixmap 的 reference 必須在 presentation 完成或取消時釋放，不得提早、不得殘留
新增：window destroy 導致 presentation 未完成時，該 present 必須走「取消」路徑退休，
      不得被記為「完成」，也不得留在 pending
```

---

### V-5 `CONFIRMED` — AHB fence 契約在 NDK 層有具體形狀

Android NDK 官方簽名：
```c
int AHardwareBuffer_lock(AHardwareBuffer *buffer, uint64_t usage,
                         int32_t fence,            // ← 輸入 fence fd，lock 前等待
                         const ARect *rect, void **outVirtualAddress);
int AHardwareBuffer_unlock(AHardwareBuffer *buffer,
                           int32_t *fence);        // ← 輸出 fence fd
void AHardwareBuffer_acquire(AHardwareBuffer *buffer);
void AHardwareBuffer_release(AHardwareBuffer *buffer);
int  AHardwareBuffer_sendHandleToUnixSocket(AHardwareBuffer *buffer, int fd);
int  AHardwareBuffer_recvHandleFromUnixSocket(int socketFd, AHardwareBuffer **outBuffer);
```

→ Production Gate A 缺口 #6「producer-fence contract for imported / client-owned AHB」
**在 API 層是可實作的**，且 lock 的入向 fence 與 unlock 的出向 fence 正好對應
「CPU 取得前等待 GPU」與「CPU 釋放後通知 GPU」兩個方向。
→ `sendHandleToUnixSocket` / `recvHandleFromUnixSocket` 確認 AF_UNIX 是官方傳輸機制，
與先前查出的 AF_UNIX tiny-record backpressure bug 屬同一條路徑，不是偶然。

**新增到 Gate A 缺口 #6 的最小設計要求：**
```
lock 必須傳入真實的 producer fence fd（不得傳 -1 當作「沒有 fence」而略過等待）
unlock 必須取出 fence fd 並交給下一個 consumer（不得 close 掉就當作同步完成）
fence fd 的所有權轉移必須在 R10 ledger 中以 fd 計數可觀測
```

---

### V-6 `CONFIRMED` — EGL fence / EGLImage 擴充存在且有明確 enum

Khronos EGL registry（ANDROID 目錄）確認存在：
```
EGL_ANDROID_native_fence_sync          EGL_SYNC_NATIVE_FENCE_ANDROID          0x3144
                                       EGL_SYNC_NATIVE_FENCE_FD_ANDROID       0x3145
                                       EGL_SYNC_NATIVE_FENCE_SIGNALED_ANDROID 0x3146
EGL_ANDROID_image_native_buffer        EGL_NATIVE_BUFFER_ANDROID              0x3140
EGL_ANDROID_get_native_client_buffer   （HardwareBuffer → EGLClientBuffer → EGLImageKHR）
```
`EGL_ANDROID_native_fence_sync` 依賴 `EGL_KHR_fence_sync`。

→ R10 ledger 的 `EGLImage create/destroy` 與效能遙測的 `fence wait` 欄位有實體依據。
→ 靜態稽核既有修正項「EGL fence capability / PFN / `EGL_NO_SYNC` 未完全 fail-closed」
   指的正是這組擴充的能力查詢；該修正必須在 R9 design 階段重新確認仍然成立。

---

### V-7 `SUPERSEDED BY V-7R` ⚠ — adb 的 `-L` 用錯了（原判定，已被實測推翻）

`adb(1)` 官方 man page：
```
-P PORT     Smart socket PORT of adb server        [default = 5037]
-L SOCKET   Listen on given socket for adb server  [default = tcp:localhost:5037]
```
環境變數 `ANDROID_ADB_SERVER_PORT` 確認存在（上游 commit 範例：
`export ANDROID_ADB_SERVER_PORT=1234; ./adb server`）。

**問題：** V2.0 的 C1 packet 寫成
`adb -L tcp:5038 -s "$SERIAL" shell …`。
`-L` 的文件語意是「**server 要監聽哪個 socket**」，屬於啟動 server 的選項；
client 端連線到既有 server 的文件選項是 `-P`。
且 socket spec 的文件預設形式含 host（`tcp:localhost:5037`），裸 `tcp:5038` 不是文件形式。

**修正：**
```
原（V2.0）：  adb -L tcp:5038 -s "$SERIAL" shell …          狀態 EXISTS_EXECUTABLE
改（V2.1）：  ANDROID_ADB_SERVER_PORT=5038 adb -s "$SERIAL" shell …
         或： adb -P 5038 -s "$SERIAL" shell …
         狀態一律降級為 PROPOSED / NOT YET EXECUTABLE，待 host 實測確認
```
啟動隔離 server 時（若需要）才用：`adb -L tcp:localhost:5038 server`。

**連帶：** `5037` 的「絕不觸碰」規則不變，但實作方式從「靠 `-L` 指定」
改為「靠 `ANDROID_ADB_SERVER_PORT` 或 `-P` 指定」，且每個 device packet 的
`ENV_ALLOWLIST` 必須明列 `ANDROID_ADB_SERVER_PORT=5038`。

> ⚠ **以上 V-7 全段已由 V-7R 推翻，僅作歷史保留。**
> `ENV_ALLOWLIST` 明列 `ANDROID_ADB_SERVER_PORT` 的要求**已作廢**，
> 現行規定見 V-7R 與 §22.6（該變數任何值皆入 `ENV_DENYLIST`）。

---

### V-7R `MEASURED CORRECTION` — V-7 的結論超出其證據等級

**量測日期：** 2026-09-21　**量測對象：** 本機 `/data/data/com.termux/files/usr/bin/adb`
Android Debug Bridge 1.0.41 / Version 35.0.2-android-tools（ARM64，於 Ubuntu PRoot 內直接執行）

**來源等級說明：** V-7 引用通用 `adb(1)` man page 與 AOSP commit。依附錄 A 的限制，
那是**發現矛盾**用的二手來源，不能裁決本機行為。V-7R 用的是該 binary 自身 `--help`
加上本機實際行為量測，rank 高於 V-7 所依據的來源。

**量測方法：** 指向三個確定無 server 的 port，觀察 adb 於何處自動拉起 server
（`pgrep -af 'adb -L tcp'`）；再以 `-P <port> kill-server` 反向逐一收回。

```
adb -P 5039 devices                      → 生成 adb -L tcp:5039 fork-server   ✔ 到達 5039
ANDROID_ADB_SERVER_PORT=5040 adb devices → 生成 adb -L tcp:5040 fork-server   ✔ 到達 5040
adb -L tcp:5041 devices                  → 生成 adb -L tcp:5041 fork-server   ✔ 到達 5041
adb -P <port> kill-server                → 每次精準終止對應 PID；5037 PID 31022 全程未動
```

**結論一（推翻 V-7）：** 三種形式在本機 adb 35.0.2 上**功能全部正確**。
`-L` 作為 client 形式**沒有壞**。V-7 察覺矛盾是對的，但「所以是錯的」超出了其證據能證明的範圍。

**結論二（保留 `-P`，理由改為 provenance 而非功能）：**
```
-P 5038                       ← packet 唯一合法形式
ANDROID_ADB_SERVER_PORT=5038  ← 功能可行，但不出現在 command trace，損害 EXACT_COMMANDS provenance
-L tcp:5038                   ← 功能可行，但 binary help 稱其為 server listen spec，語意上會反覆招致 review 挑戰
```

**結論三（本輪真正的新風險，見 R-27）：**
`adb -P <port>` 在該 port 無 server 時**會自動拉起一個空 server**：
```
* daemon not running; starting now at tcp:5038
* daemon started successfully
List of devices attached
                            ← 空
exit=0                      ← 成功
```
一條**已死的 lane 會偽裝成健康的 lane 並回傳 exit 0**。
因此 preflight 不得以 exit code 判定 lane 存活，**必須斷言探索到的 SERIAL 逐字出現在
`adb -P 5038 devices` 輸出中**。

**結論四（env 形式的必要性）：** 本機裸測確認，`-P <port> devices|kill-server` 這類
local client 呼叫**不需要任何環境變數**。`ANDROID_NO_USE_FWMARK_CLIENT=1` 與
`HOME=/data/data/com.termux/files/home` 只與 `pair` / `connect` 的金鑰歸屬有關，
不得攜入不需要它們的 `EXACT_COMMANDS`。

**結論五（環境層，兩項與既有紀錄相反）：**
```
1. Termux native adb 可直接於 Ubuntu PRoot 內執行（--version 正常）；不需為 adb 另做 PRoot wrapper。
2. PRoot 下 ss 與 /proc/net/tcp 皆無法看見 adb listener（前者空、後者 EACCES）。
   偵測 adb server 只能用 pgrep -af 'adb -L tcp'；以 port scan 判定 lane 狀態會得到假陰性。
```

**mDNS 相關環境變數（納入 ENV 規範）：**
```
ADB_MDNS_AUTO_CONNECT      允許自動連線的 mdns 服務清單
ADB_MDNS_OPENSCREEN        切換內建 mDNS-SD 後端
ADB_TRACE                  可含 mdns，僅診斷用，不得影響判準
```

---

### V-8 `CONFIRMED` — `-legacy-drawing` 與 Stable 的「退出不等於結束」

termux-x11 官方 README 確認：
- `-legacy-drawing`：某些裝置只輸出黑畫面加游標時使用，文件形式 `termux-x11 :1 -legacy-drawing`。
- `-force-bgra`：某些裝置顏色互換時使用。
- **從通知列「Exit」離開 Termux:X11 後，`termux-x11` 指令仍在執行，且無法用該方式結束。**

→ 最後一條直接支持 Stable identity 的三元組判準：
「app 看起來關了」**不等於** process 消失。
因此 `STABLE_PRECHECK` / `STABLE_AFTER` 必須比對 **PID + cmdline**，不能只看 package 狀態。

→ Stable 的 cmdline 快照 `termux-x11 com.termux.x11 :1 -legacy-drawing` 比官方文件形式
多一個 `com.termux.x11` argv 元素。這是**實測觀察值**，予以保留。
packet 必須**逐字比對快照**，不得比對官方文件形式。

---

### V-9 `CONFIRMED` + 新增一個設計缺口 — 硬體

官方與多來源一致：
```
POCO F8 Ultra   發表 2025-11-26
SoC             Qualcomm SM8850-AC Snapdragon 8 Elite Gen 5（3nm）
CPU             Octa-core Oryon V3，2×4.6GHz Phoenix L + 6×3.62GHz Phoenix M
GPU             Adreno 840（三個 slice，各 1.2GHz；較 Adreno 830 快約 23%）
RAM/Storage     12/16GB LPDDR5X · 256/512GB UFS 4.1
OS              Android 16 / HyperOS 3
內建面板        1200 × 2608，120Hz AMOLED
```
與專案既有假設（myron / Android 16 SDK 36 / Adreno 840）一致。

**新發現的設計缺口 —— `fullscreen` 是歧義值：**
```
內建面板   1200 × 2608  =  3,129,600 px
外接目標   3440 × 1440  =  4,953,600 px   （約 1.58×）
```
P2-B.3 矩陣裡的 `fullscreen` rectangle 沒有指明是哪一個。
兩者像素量差 1.58 倍，落在完全不同的成本區間，結論不可互換。

**修正：** `fullscreen` 拆成兩個列舉值
```
fullscreen-internal   1200 × 2608
fullscreen-external   3440 × 1440
```
並在 `V2-B3-MATRIX-BIND` 中明訂哪些 cell 用哪一個；
若某輪只測 internal，其結論**不得**外推到 Gate W 的外接螢幕情境。

**連帶（thermal）：** 三個 GPU slice 在手機散熱條件下，thermal throttling 是一級混淆因子
（已列 R-21）。查驗結果讓這條風險從「理論上可能」升級為「結構上必然需要控制」。

---

### V-10 `CORRECTION` — C1 fresh pair B 的「新」是 identity 新，不是 allocator 永不重用數值

PR #8 machine-readable spec 的 forbidden predicate 是 `stale_pair_A_reuse_as_pair_B`。
V2.1 把它擴張成「slot / handle / mapping 皆不得重用」過度嚴格，可能把合法 allocator reuse 誤判成 FAIL。

V2.2 改為：
- pair A 必須完整 retirement / ACK / ownership release。
- pair B 必須是新的 **object identity + current generation/tuple binding**。
- 不得把仍屬於 pair A 的 stale object / stale tuple / stale generation state 當 pair B。
- numeric slot / virtual address / allocator token 若在完整 retirement 後被 allocator 合法重配，**本身不是 FAIL**；必須同時證明它已對應新的 object identity 且沒有 stale ownership。

---

### V-11 `CORRECTION` — R9-F1 必須是 expected containment fatal

R9-F1 `stale-ready-replay` 的 frozen方向是：
`enum16 / side2 → x-wrong-generation / reason6`。
因此 F1 的成功命題不是「拒絕且不得 fatal」，而是**精確觸發 expected fatal 並阻止 stale generation 被接受**。
R9-F2 才負責證明該 fatal session 之後 fresh session 可以乾淨 recovery。

---

### V-12 `CORRECTION` — Gate H 不得用「router 驗證失敗」逃回 NOT_REQUIRED

Gate H 的 evidence decision 與 router implementation 必須分開：
- `NOT_REQUIRED_FOR_V1`：只有 B.3 / workload evidence 證明 router 不需要時才合法。
- `PASS_ROUTER`：evidence 證明 router 需要，且設計/實作/驗證全部通過。
- `REQUIRED_BUT_NOT_ACCEPTED`：evidence 顯示 router 需要，但設計/實作/驗證尚未通過；此狀態**阻擋 V1-Core**。

不得把 implementation failure 重新敘述成「其實不需要 router」。

---

### V-13 `CONFIRMED` — current repo / PR 可讀後，三個 planning gap 已可關閉

V2.2 已完成 read-only repo 對帳：
- PR #10 實際 `changed_files = 121`：`AGENTS.md` 1、`HANDOFF.md` 1、`TEST-MATRIX.md` 1、`docs/` 1、`evidence/` 117。副檔名為 md/txt/json/jsonl；PR patch 無 binary patch、無 product source tree、無 `tests/r8/` tooling implementation、未命中常見 secret/key/token pattern。
- PR #7 的 38 個 packet 已可讀取並逐項分類；R7 13 個 packet 已完成，R8 5 個 packet 被 PR #8/tooling-v2 supersede，其餘 R9→V1 packet 保留意圖但需要 current binding rewrite。
- attempt 01–04 frozen classifier 可回填：01 `INVALID/MISSING_END_x`；02 `BLOCKED/SCREEN_NOT_AWAKE`；03 `BLOCKED`（tooling JSON emit construction）；04 `INVALID/END_COUNT_MISMATCH_x`。只回填 frozen classifier，不重新詮釋 verdict。

---

### 1.1 查驗結論總表

| # | 主題 | 結論 | 對計劃的影響 |
|---|---|---|---|
| V-1 | `DE_TERMINATE` → `ddxGiveUp` | CONFIRMED | 無需修改 |
| V-2 | `GiveUp(0)` direct-call provenance | CONFIRMED + | 精確化為 termination handler/function；必證入口 |
| V-3 | terminal teardown/current product order | **PARTIALLY_RESOLVED ⚠** | `V2-P007` 升為 C1 HARD prerequisite |
| V-4 | Present ASYNC\|COPY 與 window destroy | CONFIRMED ++ | `0x3` 寫死；C3-window 新增三項必證 |
| V-5 | AHB lock/unlock fence | CONFIRMED | Gate A 缺口 #6 新增三條最小要求 |
| V-6 | EGL fence / EGLImage 擴充 | CONFIRMED | R10 / 遙測欄位有依據 |
| V-7 | `adb -L` 用法 | **SUPERSEDED → V-7R** | 原判定「`-L` 用錯」已被本機實測推翻 |
| V-7R | adb client form（本機實測） | **MEASURED CORRECTION** | 三形式功能等效；packet 固定 `-P 5038`；新增 auto-start 陷阱 R-27 |
| V-8 | `-legacy-drawing` / 退出不等於結束 | CONFIRMED | Stable 三元組判準獲直接支持 |
| V-9 | 硬體規格 | CONFIRMED + | `fullscreen` 拆成 internal / external |
| V-10 | C1 fresh-pair identity | **CORRECTION** | 禁 stale identity；不禁止已退休後 numeric reuse |
| V-11 | R9-F1 stale replay | **CORRECTION** | expected fatal `x-wrong-generation/6` |
| V-12 | Gate H state machine | **CORRECTION** | 新增 `REQUIRED_BUT_NOT_ACCEPTED`，不可失敗後逃回 NOT_REQUIRED |
| V-13 | PR/current repo 對帳 | CONFIRMED | GAP-1/2/3 關閉；更新 packet inventory |

### 1.2 Evidence gaps / bind gaps（V2.2）

| ID | 狀態 | 缺口 | 處置 |
|---|---|---|---|
| GAP-1 | **CLOSED** | PR #10 changed-files/scope | 121 files read-only audit（117 added / 4 modified）；無 binary/product-source/tooling-impl/secret-pattern hit；4 modified 僅 AGENTS/HANDOFF/TEST-MATRIX/PR-map |
| GAP-2 | **CLOSED** | PR #7 38 packets 分類 | 已逐項 reconciliation，見 §4.1 |
| GAP-3 | **CLOSED** | attempt 01–04 classifier | frozen classifier 已回填，見 §5.1 |
| GAP-4 | **OPEN** | `a4c8177` → `b984ded` touched-symbol diff | `CF-PENDING-001/002`；P2 closure 前必關 |
| GAP-5 | **CLOSED** | pinned current-product terminal sequence / ClearWorkQueue | `V2-P007` = `SOURCE_BOUND`（2026-09-21，見 `evidence/session/gate-a-a1/planning-v2/p007-terminal-contract/`） |
| GAP-9 | **OPEN / DESIGN_REQUIRED / BLOCKS P1·P2** | `judge_p1/p2` 要求 `EVENT_LEASE_GPU_OWNED`，該事件只在 Gate A direct EXA composite 的 publish 路徑發出；實測所有 cell 皆 0 次，且 `DIRECT_ADMIT_REJECT` 亦 0 次 → 該路徑不是被拒絕而是從未被嘗試 | 需 `V2-R8-P-SRC-TRACE`，見 `planning-v2/r8-p1-p2-construction-gap/` |
| GAP-8 | **OPEN / PRODUCT DEFECT / BLOCKS C1·C5-full·C5-overflow** | `ProcLorieR8Checkpoint` 的 R8_OBS 載荷出現重複鍵 `phase`，觀測種類被 checkpoint 相位編號覆蓋；另 `total_actual_buffer_pending` 硬寫 null | `planning-v2/product-defect-r8-obs-phase-collision/`。§2.2 的 product-defect 證據條件已成立；收容方案為 collector/judge 端修正，不重建產品 |
| GAP-7 | **CLOSED**（D-17 已實作；P009 = `CONTRACT_CONSISTENT` 10/10）| ~~judge_c1 / cell_c1 契約不一致~~ |
| ~~GAP-7~~ | ~~OPEN / DESIGN_REQUIRED / BLOCKS C1~~ | `judge_c1` 要求 `R_DESTROY_STAGE` / `R_ACK_SETTLED` / `X_CHECKPOINT`，但 `cell_c1` 只做 pair composite，不 register 也不 checkpoint——那三個向量是 `cell_c4` 才產生的。C1 結構上不可達 | Astra/Sol 決策 D-17，見 `planning-v2/r8-c1-second-blocker/finding.md` |
| GAP-6 | **CLOSED** | ADB-5038 client form（V-7R）+ runner/collector/judge CLI binding | `V2-P008` = `INTERFACE_BOUND`（2026-09-21，見 `.../planning-v2/p008-execution-interface/`）。runner 為 **env-driven，無任何 flag**；CELL_ID 詞彙為 `R8-C1`…`R8-P2` |

---

## 2. CURRENT AUTHORITY（凍結常數）

> 任何 packet 的 `EXACT_INPUT_SHA` 必須**逐字複製**本節數值。
> 不得寫「見上文」「同前」。本節任一行變動 → 觸發 carry-forward 評估。

### 2.1 快照

```
CURRENT SNAPSHOT = waydefu/GPU PR #10
TITLE            = Record b984ded install and R8-C1 ADB restored
PR #10 HEAD      = 697e16f3dab21946d77860b82c7e4ceeb8fe761e
PR #10 BASE      = 06eff51bc69f2685083746b68f55786e30a854da
```
PR #10 **是** current continuation / evidence snapshot。
PR #10 **不是** R8 PASS、不是 Gate A PASS、不是 V1-Core PASS、**不是 runtime authorization**。

```
R7                = GATE A P2 R7 PASS, COMPLETE 13/13
R7 FINAL SOURCE   = a4c8177f4b059fddd111717255e9d23cf0e15e1e   (historical)
R8                = 0/10
R8-C1             = NOT STARTED（attempt-09 未開始、未消耗）
PRODUCTION GATE A = BLOCKED
V1-CORE           = NOT QUALIFIED
```
R7 不再是 current execution work。所有歷史 FAIL / INVALID 永久保留。**不得要求重跑 R7。**

### 2.2 PRODUCT AUTHORITY（已安裝、已再證明）

```
PRODUCT_SHA          = b984dedcac731b77ca4cf8899f8a78b7848ad083
CI_RUN               = 35347497216
PACKAGE              = com.waydefu.x11gpu
VERSION              = 1.03.01-b984ded-18.09.26
APK_SHA256           = 0d06de68025ca41d91e316d55f6f77ba9d5b3ba1a90b6a2bfacb65add0d398d3
BUILD_ID             = 3658dd1f8047bfbb9d4671b269305313adaf1aa7
SIGNER               = b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1
EXPERIMENTAL_DISPLAY = :3
```
**規則：** 除非新 evidence 證明 product defect，後續規劃**不得預設需要 rebuild / reinstall**。
任何 packet 若填 `CI_POLICY = REQUIRED` 或 `INSTALL_POLICY = REQUIRED`，
必須在同一 packet 內附上 product-defect evidence 引用，否則該 packet 不合格。

### 2.3 TOOLING AUTHORITY（與 PRODUCT 永遠分開）

```
TOOLING_COMMIT = 2a14ab2f7a5d81e7cd72d5308f5865b81b22881f
```

| 角色 | 檔案 | SHA256 | 狀態 |
|---|---|---|---|
| RUNNER（current） | `run-r8-one-cell-b984ded-v5.sh` | `c3dde31c96fa43dd37a91c1e6fd4269f1c95ff32e537f5e9cebfea2885ac6a67` | **USE**（D-17 contract rebind）|
| RUNNER（superseded） | `run-r8-one-cell-b984ded-v4.sh` | `45741bfd3d98d045cb011f247410efdbd4ba95952ceccdf2fd7d0cc024efbfd8` | **SUPERSEDED** |
| RUNNER（superseded） | `run-r8-one-cell-b984ded-v3.sh` | `16808107886123e8b7b3de4e1654df227185ff2f838d258e350d62caecc164ce` | **SUPERSEDED**（F1 已含於 v4）|
| RUNNER（superseded） | `run-r8-one-cell-b984ded-v2.sh` | `53e0c6b8ac613eab7dcce970438e7adc071bddcde4d7e1e202763bfe62de44e5` | **SUPERSEDED**，非 FORBIDDEN。它本身正確，只是不驗 installed artifact |
| RUNNER（historical） | `run-r8-one-cell-b984ded.sh` | `f22546b7f42aa9f45c4bdee5e7ce675efe6b1fae4e9709e15696e59262dab7b0` | **FORBIDDEN**（綁 frozen judge） |
| ORCHESTRATION | `r8_orchestration_v2.py` | `27af4a6253bcc021f3da2494b99045c754fb27f2b815b23cbbe1e0744760a536` | USE |
| JUDGE（current） | `judge-r8-v2.py` | `d60432c6ef9d640a3738421c2960da8ab65d0bb4b099a05ed644aabeb3d47cd6` | **USE**（D-17：judge_c1 移除 registration-coupled helper，改直接斷言 X_DESTRUCTOR_EXIT）|
| JUDGE（frozen historical） | `judge-r8.py` | `f021048da3c1b729c6f9bf560eba52609b2f980336dd4fab77ad1700438c0e31` | **FORBIDDEN as current** |
| COLLECTOR | `collect-r8.py` | `e6df519a75c872c8a56fac00146585853eec7f17a3f424e70e5d4736340666c8` | USE |
| SPEC | `lifecycle-cell-spec.json` | `ff22a1521d23a8954b0b4f3a603dbb19af98b3e8b3727342caf5e107b639b3ba` | USE |
| OBS STREAM | `r8_obs_stream.py` | `72d7517737a009a588f0c25d685db252a32081c4a9e750adaf4f0f2932eb5041` | USE |
| FIXTURE ELF | `/tmp/p_r8_lifecycle`（tmpfs，`f8-r8-fixture` 重建）| `a4c8099fd748f13b2ed0f354847310f9916087cd8b5e06aaa0da0966a119e4ac` | USE（D-17）|
| FIXTURE SOURCE | `tests/r8/p_r8_lifecycle.c` | `d44abe9466cdac802154799176be4dd5b090fe0091e48e3b42e6ef39ca3a8cfd` | USE（D-17：cell_c1 / cell_c5_overflow 加入唯讀 checkpoint）|

Runner 路徑前綴：`evidence/session/gate-a-a1/p2-r8-runtime/`
MANIFEST（current）：`p2-r8-runtime/runtime-b984ded/r8-runtime-tooling-manifest-v5.json`
**其餘工具的路徑前綴（P008 補記，§2.3 原本未記錄）**：
`src/f8-ahb-gatea-r7-p1-arm/tests/r8/`（runner 內 `HERE=` 寫死；SPEC / JUDGE / COLLECT / ORCH 全由此解析）
FIXTURE SOURCE = 該目錄下 `p_r8_lifecycle.c`；FIXTURE ELF 於 `/tmp/p_r8_lifecycle`（tmpfs，重開機即失，用 `f8-r8-fixture` 重建）
`build_id 3658dd1f…` 在 fb4f017 與 b984ded 兩個 product 上相同，**不具鑑別力**，不得用於 artifact identity；
鑑別力來自 `apk_sha256`，v3 runner 已在 preflight 區強制比對。

**ANTI-CONFUSION RULE（強制）**
```
TOOLING-only commit  ≠  PRODUCT SHA
PRODUCT SHA          ≠  TOOLING generation
```
若某份 evidence 把 `2a14ab2…` 寫進 product 欄，或把 `b984ded…` 寫進 tooling 欄
→ 該 evidence **INVALID**，不得 dedupe、不得事後改欄位再重用。

### 2.4 STABLE SACRED BOUNDARY

```
package  = com.termux.x11
DISPLAY  = :1
PID      = 20146                                          (snapshot)
cmdline  = termux-x11 com.termux.x11 :1 -legacy-drawing    (逐字比對此快照)
HDMI     = UNTOUCHED
```
永遠禁止：`NO INSTALL` `NO KILL` `NO RESTART` `NO FORCE-STOP`
`NO CONFIG MUTATION` `NO BENCHMARK` `NO QUALIFICATION` `NO EXPERIMENT`

**Identity 三元組（三者全等才算 unchanged）：**
```
1. package present 且未被 force-stop
2. PID 連續（before PID == after PID）
3. cmdline 逐字相同
```
缺 before 或 after 任一 → 該 attempt 直接 `INVALID`，不論 product 行為多正確。

> 查驗 V-8 支持這條：官方文件明載從通知列 Exit 後 `termux-x11` 指令仍在執行。
> 「看起來關了」不是證據，PID + cmdline 才是。

### 2.5 ADB LANE（含 V-7R 實測綁定）

```
isolated adb server     = 5038         （絕不觸碰 5037）
指定方式（BOUND V-7R + P008） = adb -H 127.0.0.1 -P 5038      ← packet 唯一合法形式
                          （harness-lib.sh ADB() 的實際形式，含 -H；且它主動
                            env -u ANDROID_ADB_SERVER_PORT，故 env 形式不只較弱而是不相容）
                          env / -L 形式功能上等效（2026-09-21 實測），但不得寫入
                          EXACT_COMMANDS；理由為 provenance，非功能，見 V-7R
FIXTURE（P003 補）       = /tmp/p_r8_lifecycle，來源 src/f8-ahb-gatea-r7-p1-arm/tests/r8/p_r8_lifecycle.c
                          （§2.3 原本只釘 hash 未給檔名；已由 hash 反查確認）
                          /tmp 是 tmpfs → 每次重開機必失，runner 會 R8_BLOCKED fixture_sha。
                          重建：f8-r8-fixture（2026-09-21 實測可 byte-identical 重現 ad93f2ba…）
AUTO-START 陷阱          = -P <port> 在該 port 無 server 時會自動拉起空 server，
                          回 exit 0 + 空 device list → 死 lane 偽裝成活 lane。
                          preflight 必須斷言 SERIAL 逐字出現，不得只看 exit code。（R-27）
SERIAL snapshot         = 10.191.48.13:46847     ← EPHEMERAL，不得 hardcode
device                  = myron       (ro.product.device)
screen                  = Awake / Display ON
frozen failed endpoint  = 10.191.48.13:45165     ← 永久 frozen，禁止 silent retry
```

**每個 device packet 的 preflight 必須 fresh 重做全部 8 項：**
```
1. mdns resolve（不得重用快取 endpoint）
2. adb connect（隔離 server，非 5037）
3. adb -s <SERIAL> 可達
4. getprop ro.product.device == myron
5. screen Awake / Display ON
6. package readback（版本 / APK SHA256 / BUILD ID / SIGNER 四項全中）
7. Stable identity 三元組
8. no :3 residue（process / socket / lock 皆不存在）
```
SERIAL 只能 runtime-discovered。任何 packet 把 SERIAL 寫成 literal 並直接執行 → 不合格。

### 2.6 R8 OBSERVATION CONTRACT

```
x-observations.jsonl         = 唯一 X semantic stream
renderer-observations.jsonl  = 唯一 renderer semantic stream
```
raw logcat / ring buffer / summary 只可作：
`provenance` `producer proof` `cross-check` `diagnostics` `synthetic-END detection`

**永久禁止：** 把 semantic JSONL 與 raw 串流 concatenate 後重新計數。
（這正是 attempt-08 被判 INVALID 的 host ingestion duplication 成因。）

**真 duplicate 在 JSONL 內 → 必須 `INVALID`。**
不得用 dedupe 蓋掉真正的 producer defect；dedupe 只能出現在 diagnostics 註記，不得進入 judge 輸入。

### 2.7 R8 TERMINAL CONTRACT（含 V-2 / V-3 修訂）

```
LORIE-R8-TEST opcode 3
  → ProcLorieR8Terminate          ← 進入點必須可證明（V-2）
  → reply
  → GiveUp(0)                     ← in-process 直呼，非 signal 遞送
  → DE_TERMINATE                  (dispatchException |= 2)
  → X server normal teardown
  → CloseScreen           ┐
  → resource teardown     ├─ 相對順序 UNRESOLVED（V-3），暫不作為 FAIL 依據
  → ClearWorkQueue        ┘
  → ddxGiveUp
  → lorieR8ObsEnd("x")
  → process exit
```

X `END` 只能由真正的 terminal producer emit。

**FORBIDDEN（出現任一 → `INVALID`，不是 FAIL）：**
```
runner fake END / collector synthetic END
移動 END 的位置 / truncate logs / 忽略 post-END observation
SIGKILL 結束正常流程 / SIGTERM 代替 opcode 3
-enable product -terminate
僅以 dispatchException 最終值相同論證路徑正確（V-2 新增）
```

renderer END：沿用目前 published terminal logic，本輪不重新定義。

### 2.8 CLASSIFIER SET（全域唯一）

```
PASS             清潔通過，可進下一格（且 authorization scope 允許）
VALID_FAIL       可信 construction + 完整 evidence，證明 product predicate 為假
INVALID          test / harness / evidence 無法形成可信的 product judgment
BLOCKED          安全開始前 dependency 不成立
INFRA_BLOCKED    ADB / screen / network / host / tool availability
DESIGN_REQUIRED  需要 architecture decision（Astra/Sol），Luna 不得自解
```
R8-D 專屬追加：`INVALID_CONSTRUCTION`（overlap 未形成 → 不是 FAIL）。

### 2.9 ATTEMPT CONSUMPTION RULE（唯一定義）

```
ATTEMPT_CONSUMED = TRUE   iff  runtime cell dir 已建立  OR  runner 已被 invoke
ATTEMPT_CONSUMED = FALSE  iff  上述兩者皆未發生
```
推論：preflight 在 runner invoke 前失敗且未建立 cell dir → **NOT CONSUMED**，
下次仍使用**同一個** attempt 編號，**不得跳號**。

### 2.10 MANDATORY CELL ORDER

```
C1 → C2 → C3-window → C3-disconnect → C4 → C5-full → C5-overflow → D → P1 → P2
```
第一個 `FAIL` / `INVALID` / `BLOCKED` / `INFRA_BLOCKED` → **freeze + STOP**，禁止 silent retry。
只有 clean `PASS` 才能進下一格，且 authorization scope 必須涵蓋下一格。

10/10 後才是 `R8 COMPLETE 10/10`。**即使如此，Production Gate A 仍 BLOCKED。**

不得發明新 cell、不得合併 cell、不得改變順序。
（C5-full 的 baseline occupancy 量測是 C5-full **cell 內的 phase 0**，不是新 cell。）

---

## 3. AUTHORITY DAG

### 3.1 優先序（高 → 低）

```
A  最新 frozen runtime evidence
B  最新 canonical HANDOFF / next-agent brief
C  current exact product source
D  accepted / frozen Gate design
E  published current host tooling manifest
F  installed artifact provenance
G  latest docs PR snapshot
H  merged historical planning PR
I  older PDF / roadmap / historical notes
```
**低層不得覆蓋高層。** 任何 packet 引用 rank ≤ H 作為 current authority → 不合格，
除非該欄位明確標在 `FILES_NOT_TO_USE_AS_CURRENT` 作對照。

### 3.2 當前綁定

```
A ← runtime-b984ded/ 下 attempt 01-08 evidence
    + attempt-09-preflight (INFRA_BLOCKED) + attempt-09-adb-restore (ADB_LANE_RESTORED)
B ← PR #10 continuation snapshot / next-agent brief
C ← PRODUCT_SHA b984dedcac731b77ca4cf8899f8a78b7848ad083
D ← merged PR #8（R8 lifecycle qualification design）
E ← TOOLING_COMMIT 2a14ab2f7a5d81e7cd72d5308f5865b81b22881f
F ← APK 1.03.01-b984ded-18.09.26 / SHA256 0d06de68… / CI 35347497216
G ← PR #10 docs/evidence snapshot（V2.2 read-only scope audit = SCOPE_CLEAN_DOCS_EVIDENCE）
H ← merged PR #7（38 packets, scaffold）、merged PR #9（attempt-05 snapshot）
I ← 舊 PDF / roadmap / P0–P12 草案 / GATE-A-P2-RUNTIME-QUALIFICATION-DESIGN-20260913
```

### 3.3 衝突解析範例

| 衝突 | 勝方 | 理由 |
|---|---|---|
| PR #7 說用 historical runner；tooling manifest 說 v2 | **v2 runner (E)** | E > H |
| PR #8 以 pairs 為 capacity 單位；current spec 以 buffer slots | **buffer slots (D+A)** | D 為 frozen gate design，A 層 evidence 以 slot 計 |
| PR #10 body 說 docs-only；changed_files 顯示 source mutation | **changed_files (A/C)** | body 是敘述，不是 evidence |
| 舊 roadmap 說 R9 可直接接 R7；current source lineage 已變 | **current source (C)** | C > I，且 R9 必須先 DESIGN FREEZE |
| 某文件把 attempt-08 描述為 product bug | **frozen classifier (A)** | attempt-08 = INVALID（host ingestion duplication），永不 reclassify |
| 某文件宣稱 attempt-09 已消耗 | **runtime dir 不存在 (A)** | 檔案系統事實 > 敘述 |
| **上游 xserver 順序 vs 凍結終止契約（V-3）** | **兩者皆不勝** | 上游不是本 product 的 rank-C；需 `V2-P007` 讀 b984ded 裁決 |

### 3.4 不可覆蓋清單（IMMUTABLE）

```
attempts 01-08 classifiers
attempt-09-preflight = INFRA_BLOCKED / ADB_CONNECT_FAILED
R7 = PASS 13/13
歷史 FAIL / INVALID 全部保留
frozen failed endpoint 10.191.48.13:45165
frozen historical judge judge-r8.py 的判決範圍
Stable sacred boundary
```

### 3.5 Authority 升級規則

只有兩種方式讓某事物成為 current authority：
1. **產生新的 rank-A evidence**（在授權下執行 packet 並凍結結果）
2. **Astra/Sol 明確 decision**（記入決策登錄，並註明覆蓋哪一 rank）

Luna 永遠不能升級 authority，只能消費 packet 內已綁定的 authority。
**外部官方文件（本輪查驗來源）不是任何 rank**，只能用來發現矛盾、產生 packet，不能直接覆蓋。

---

## 4. PR 對帳

### 4.0 進度基準宣告（本計劃唯一的「現在在哪」）

> **本計劃的進度基準 = PR #10，不是任何其他來源。**
>
> ```
> BASELINE  = waydefu/GPU PR #10
>             HEAD 697e16f3dab21946d77860b82c7e4ceeb8fe761e
>             BASE 06eff51bc69f2685083746b68f55786e30a854da
>             「Record b984ded install and R8-C1 ADB restored」
> ```
>
> PR #10 記錄的進度恰好是兩件事，計劃只能從這兩件事往前推：
> ```
> 1. b984ded 已安裝並 re-proven      → 後續不預設 rebuild / reinstall
> 2. R8-C1 的 ADB lane 已 restored   → 下一個候選是 C1 attempt-09，且它尚未開始
> ```
> PR #10 **沒有**記錄任何 cell 通過。因此：
> ```
> R8 = 0/10
> R8-C1 attempt-09 = NOT STARTED / NOT CONSUMED
> Production Gate A = BLOCKED
> ```
> 任何文件（含 PR #7 的 roadmap、PR #8 的設計、PR #9 的 attempt-05 敘述、舊 PDF）
> 若暗示進度超前於此，一律以 PR #10 為準，並視該文件為 historical。

六問格式：`authoritative` / `historical` / `superseded` / `immutable evidence` /
`must not be executed` / `feeds V2`

| PR | 角色 | rank | 可執行性 |
|---|---|---|---|
| #7 | 舊 master roadmap / historical scaffold | H | **不可照 current state 執行** |
| #8 | R8 lifecycle design authority | D | 設計可用；內嵌 command 需重綁 v2 tooling |
| #9 | historical attempt-05 snapshot | A（evidence）/ H（敘述） | evidence 不可丟、不可重跑 |
| #10 | **current continuation snapshot（進度基準）** | B/G | V2.2 scope audit = `SCOPE_CLEAN_DOCS_EVIDENCE` |

---

### 4.1 PR #7 — Plan V1-Core execution from post-R7-04 state

**定位：** 38 packets × 34 fields，現在只當三件事：
`ARCHITECTURE SCAFFOLD` / `DEPENDENCY SCAFFOLD` / `RELEASE ROADMAP`

它建立時的世界狀態全部已失效：
```
R7 尚未完成            → 現在 R7 PASS 13/13
R8 design 尚未 final   → 現在 PR #8 已 merge 並 final
b984ded 尚不存在       → 現在為 current PRODUCT_SHA 且已安裝（PR #10 記錄）
judge-v2 尚不存在      → 現在為唯一 current judge
tooling v2 尚不存在    → 現在 TOOLING_COMMIT = 2a14ab2…
attempt01-08 尚未發生  → 現在全部 frozen
```

**逐項分類：V2.2 已完成 read-only extraction。**

| PR #7 packet | 名稱（縮寫） | V2.2 disposition | V2 successor / 理由 |
|---|---|---|---|
| NEXT-001..013 | R7 12 cells + aggregate | `PR7_ALREADY_COMPLETED` | R7 已 frozen PASS 13/13 |
| NEXT-014 | R8-DESIGN | `PR7_SUPERSEDED` | PR #8 accepted/frozen R8 design |
| NEXT-015 | R8-IMPLEMENT | `PR7_SUPERSEDED` | current R8 support lineage/tooling v2 |
| NEXT-016 | R8-VERIFY | `PR7_SUPERSEDED` | current judge-v2 / collector / tooling authority |
| NEXT-017 | R8-CI/artifact | `PR7_SUPERSEDED` | current product `b984ded` / CI 35347497216 |
| NEXT-018 | R8-DEVICE | `PR7_SUPERSEDED` | PR #8 ten-cell order + V2 packets |
| NEXT-019 | R9-DESIGN | `PR7_NEEDS_REWRITE` | current `b984ded` lineage must DESIGN FREEZE first |
| NEXT-020 | R9-DEVICE | `PR7_NEEDS_REWRITE` | depends on rewritten R9 design/harness/judge |
| NEXT-021 | R10-DESIGN | `PR7_NEEDS_REWRITE` | V2 measurable ledger contract |
| NEXT-022 | R10-DEVICE | `PR7_NEEDS_REWRITE` | V2 warm/cold K0..K3 series |
| NEXT-023 | P2 runtime closure | `PR7_NEEDS_REWRITE` | current-candidate/carry-forward two-state binding |
| NEXT-024 | bounded XFCE | `PR7_NEEDS_REWRITE` | V2 design-freeze + baseline/final split |
| NEXT-025 | B.3 measurement design | `PR7_NEEDS_REWRITE` | V2 matrix + internal/external fullscreen |
| NEXT-026 | B.3 paired workload | `PR7_NEEDS_REWRITE` | current telemetry/thermal binding required |
| NEXT-027 | Production Gate A gap design | `PR7_NEEDS_REWRITE` | evidence-backed gap inventory only |
| NEXT-028 | production corrections | `PR7_NEEDS_REWRITE` | eight-step minimal repair pipeline |
| NEXT-029 | production CI/artifact | `PR7_NEEDS_REWRITE` | exact future PRODUCT_SHA binding |
| NEXT-030 | production lifecycle qual | `PR7_NEEDS_REWRITE` | affected-gate requal + carry-forward |
| NEXT-031 | refresh workload | `PR7_NEEDS_REWRITE` | final-candidate-only evidence |
| NEXT-032 | Gate H evidence decision | `PR7_NEEDS_REWRITE` | V2 three-state Gate H decision |
| NEXT-033 | Gate H router design | `PR7_NEEDS_REWRITE` | only if evidence says router required |
| NEXT-034 | router implementation/qualification | `PR7_NEEDS_REWRITE` | cannot auto-fallback to NOT_REQUIRED on failure |
| NEXT-035 | Gate W contract freeze | `PR7_NEEDS_REWRITE` | final artifact + thresholds pre-freeze |
| NEXT-036 | Gate W workload qual | `PR7_NEEDS_REWRITE` | final artifact only |
| NEXT-037 | failure→repair→requal | `PR7_NEEDS_REWRITE` | intent retained；V2 classifier/attempt/grant rules supersede bindings |
| NEXT-038 | V1 acceptance | `PR7_NEEDS_REWRITE` | V2 19-point acceptance + Sol release decision |

**機械式判斷結果：** PR #7 的粗粒度 DAG/里程碑仍可當 scaffold，但不存在可直接照原 packet 執行的 current packet。
R7 已完成；R8 已被 PR #8 + tooling-v2 取代；R9 之後全部必須 current-binding rewrite。

**六問：**
- authoritative：只有 stage 間的粗粒度依賴順序 / milestone 意圖。
- historical：全部 38 packet 的舊 binding / command / SHA。
- superseded：R8 全部；R7 執行狀態。
- immutable evidence：無（planning 本身不是 runtime evidence）。
- must not be executed：所有 PR #7 原始 EXACT_COMMANDS、runner/judge/artifact binding。
- feeds V2：dependency DAG、release milestones、failure-pipeline intent。

---

### 4.2 PR #8 — Design and plan R8 lifecycle qualification（merged）

**定位：** 目前 R8 design authority 的主要來源（rank D）。建立：
```
R8-C1 / R8-C2 / R8-C3-window / R8-C3-disconnect / R8-C4
R8-C5-full / R8-C5-overflow / R8-D / R8-P1 / R8-P2
53 host negative vectors
```

**六問：**
- authoritative：cell 定義、cell 順序、negative vector 集合、terminal contract 的**語意骨架**、PASS/FAIL 的**語意層**
- historical：其中對 tooling 的引用（撰寫時 v2 尚不存在）
- superseded：任何 runner / judge / collector 綁定 → 改綁 §2.3；任何以 **pairs** 為 capacity 單位的敘述 → 改為 **buffer slots**
- immutable evidence：無
- must not be executed：PR #8 內任何直接可執行片段（未綁 v2 tooling）
- feeds V2：§7 全部十格的 acceptance 語意；53 negative vectors 併入每格 `FORBIDDEN_TRACE`

**待辦 `V2-P006-NEGATIVE-VECTOR-BIND`：** 把 53 vectors 逐條 map 到十格的
`FORBIDDEN_TRACE` / `INVALID` 條件，產出 `negative-vector-map.json`。
未完成前，每格的 `FORBIDDEN_TRACE` 只是本檔列出的子集，需標 `PARTIAL`。

---

### 4.3 PR #9 — historical attempt-05 snapshot（merged）

current-state-wise **已 superseded**（之後有 06/07/08 與兩代 tooling），
但其 evidence **不可丟、不可覆寫、不可重新分類**。

**六問：**
- authoritative：無（不得作為 current runtime state）
- historical：全部敘述
- superseded：其對「當前 R8 狀態」的描述
- immutable evidence：attempt-05 的 `POST_END_OBSERVATION` 判決與原始 JSONL / logs —— **post-END 禁令的原始證據來源，永久保留**
- must not be executed：重跑 attempt-05、以 attempt-05 tooling 產生新判決
- feeds V2：R-02 風險、每格 `FORBIDDEN_TRACE` 的 `no semantic obs after END`

---

### 4.4 PR #10 — Record b984ded install and R8-C1 ADB restored（current）

**六問：**
- authoritative：b984ded 已安裝並 re-proven 的事實；ADB lane 已 restored 的事實；attempt-09 runtime dir 仍 ABSENT 的事實
- historical：無（最新一層）
- superseded：無
- immutable evidence：install 證據（APK SHA256 / BUILD ID / SIGNER / CI run）、attempt-09-preflight 的 INFRA_BLOCKED 記錄、attempt-09-adb-restore 的 SERIAL 記錄
- must not be executed：把 SERIAL `10.191.48.13:46847` 當永久常數重用；把 ADB restored 當成 runtime grant
- feeds V2：§2.2 §2.5 全部常數、`V2-R8-C1-09` 的全部綁定

**必須反覆重述的界線：**
> **ADB lane restored ≠ runtime authorization。**
> PR #10 沒有授權任何 cell 執行。`V2-R8-C1-09` 仍需 explicit grant。

---

### 4.5 PR #10 SCOPE AUDIT — **READ-ONLY AUDIT COMPLETE (V2.2)**

PR #10 實際 changed files = **121**。路徑分布：

```
AGENTS.md      1
HANDOFF.md     1
TEST-MATRIX.md 1
docs/          1
evidence/    117
```

副檔名：`md=66` / `txt=46` / `json=7` / `jsonl=2`。
PR patch scan：
- binary patch：0
- `.apk/.so/ELF/zip/tar/...`：0
- product source tree / `tests/r8/` tooling implementation path：0
- 常見 private-key / GitHub token / Google key / AWS key / pairing-code pattern：0
- compare 結果：117 added / 4 modified；4 modified 僅 `AGENTS.md`、`HANDOFF.md`、`TEST-MATRIX.md`、`p2-r7-design/WAYDEFU-GPU-PR-MAP-20260916.md`；**沒有 frozen runtime verdict/evidence path 被修改或刪除**。

**九問裁決：**

| Q | 結果 | 說明 |
|---|---|---|
| Q1 docs/evidence/text/manifest only | YES | 121 paths 全落在 top-level docs/state files 或 `docs/` / `evidence/` |
| Q2 APK | NO | 無 |
| Q3 `.so` / ELF | NO | 無 |
| Q4 other binary blob | NO | patch 無 binary |
| Q5 credentials/token/key | NO HIT | patch-level secret pattern scan 無命中 |
| Q6 raw sensitive logs | NO BLOCKING HIT | 有 `pm-install-*.raw.txt` 安裝記錄，但無未過濾 logcat / pairing code / secret-pattern 命中 |
| Q7 product source mutation | NO | 無 source tree path |
| Q8 historical evidence overwrite/delete | NO | compare 僅 4 個 modified path，皆非 frozen runtime verdict/evidence；其餘 117 為 added |
| Q9 current harness/tooling implementation included | NO | 有 tooling manifest / evidence，但無 `tests/r8/*` implementation |

`PR10_SCOPE_VERDICT = SCOPE_CLEAN_DOCS_EVIDENCE`

這個 verdict 只證明 PR #10 的 scope；**不等於 runtime grant、不等於 R8 PASS**。

---

## 5. R8 歷史 attempts（永久凍結）

> 本表不得被任何後續文件覆蓋、重新分類或「修正」。
> 任何 agent 若改動 `CLASSIFIER` 欄 → 視為違反 authority，立即 STOP。

### 5.1 Frozen table（R8-C1 attempts 01–08）

| # | PRODUCT | TOOLING GEN | CLASSIFIER | ROOT CAUSE | PROVED | DID **NOT** PROVE | SUPERSEDED BY | RETRY |
|---|---|---|---|---|---|---|---|---|
| 01 | pre-b984ded | gen-1 | **INVALID / MISSING_END_x** | frozen producer-finalization failure；只回填 classifier，不重寫 RCA | harness 可進入 cell | clean terminal completeness | 02–08 | **PROHIBITED** |
| 02 | pre-b984ded | gen-1 | **BLOCKED / SCREEN_NOT_AWAKE** | pre-runtime screen dependency 不成立 | safety preflight fail-closed | 任何 product predicate | 03–08 | **PROHIBITED** |
| 03 | pre-b984ded | gen-1 | **BLOCKED / TOOLING_JSON_EMIT** | host/tooling JSON evidence construction 不成立 | tooling failure 可被 fail-closed 捕捉 | product lifecycle | 04–08 | **PROHIBITED** |
| 04 | pre-b984ded | gen-1 | **INVALID / END_COUNT_MISMATCH_x** | END placement 與 teardown observation 不一致 | clean shutdown已進一步暴露 terminal-boundary 問題 | terminal correctness | 05–08 | **PROHIBITED** |
| 05 | 見 PR #9 | gen-1 | **POST_END_OBSERVATION** | END 之後仍有 semantic observation 被 emit / 採計 | post-END 是真實可發生的污染模式 | clean terminate 成立 | 06–08 | **PROHIBITED** |
| 06 | gen-1 末期 | gen-1 → **reset 進 gen-2** | **MISSING_END_x** | X semantic stream 缺 END | END 缺失可由 producer 側造成 | teardown path 完整性 | 07–08 | **PROHIBITED** |
| 07 | b984ded lineage | gen-2 | **PRODUCERS_NOT_FINALIZED** | TERMINATE 已送出，server 未 dispatch | terminate 送達路徑存在 | dispatch → teardown 銜接 | 08 | **PROHIBITED** |
| 08 | `b984ded…` | gen-2 | **JUDGE_NOT_PERMITTED / MULTI_BEGIN_x** | **host ingestion duplication** | **product teardown path 現在成立**（見 5.2） | C1 完整 acceptance | — | **PROHIBITED** |

V2.2 已把 01–04 的 frozen classifier 回填。對 RCA 欄只使用既有 frozen handoff/summary 能直接支持的粒度；
未被 frozen evidence 明確支持的細節仍不得補寫。`V2-P004` 現降為「索引/manifest 整理」用途，不再是 classifier blocker。

### 5.2 attempt-08 的關鍵意義（不得被稀釋）

attempt-08 雖判 `INVALID`，其 runtime 證據顯示：
```
server TEST_CONTROL TERMINATE   observed
ddxGiveUp                        observed
X END                            = 1
renderer END                     = 1
wait-finalized                   OK
POST_END observation             none
```
**因此 attempt-08 證明：product teardown path 現在成立。**

同時必須同樣大聲地說：
- `INVALID` 成因是 **host ingestion duplication**，不是 product defect。
- `INVALID` **永久不 reclassify** 為 PASS，也不為 VALID_FAIL。
- attempt-08 **不能**當作 C1 PASS 的替代證據。C1 仍須從 attempt-09 重新取得完整證據。
- 修正方向已固化為 §2.6 的 observation contract，由 tooling gen-2 承載。

### 5.3 attempt-09 — 兩個 frozen 子狀態

```
attempt-09-preflight
  CLASSIFIER : INFRA_BLOCKED / ADB_CONNECT_FAILED
  ENDPOINT   : 10.191.48.13:45165    ← 永久 frozen failed，禁止 silent retry
  runner invoked           : NO
  runtime cell dir created : NO
  cell runtime started     : NO

attempt-09-adb-restore
  CLASSIFIER : ADB_LANE_RESTORED
  SERIAL     : 10.191.48.13:46847    ← ephemeral snapshot，非永久常數
  runtime-b984ded/r8-c1/attempt-09/ : ABSENT
```

**唯一合法解讀：**
```
R8-C1 attempt-09 = NOT STARTED
```
依 §2.9：preflight 在 runner invoke 前失敗且未建立 cell dir → **NOT CONSUMED**。因此：
```
禁止建立 attempt-10
禁止把 preflight BLOCKED 當成已消耗的 runtime cell
下一次真正執行仍使用編號 attempt-09
attempt-09 需要 explicit grant；本計劃任務不授權
```

### 5.4 從歷史直接導出的永久禁令

| 禁令 | 來源 |
|---|---|
| 不得在 END 之後採計任何 semantic observation | attempt-05 |
| 不得偽造 / 搬移 / 補上 END | attempt-05, attempt-06 |
| 不得把 semantic JSONL 與 raw 合併後計數 | attempt-08 |
| 不得用 dedupe 掩蓋真 duplicate | attempt-08 |
| 不得以 SIGTERM / SIGKILL 取代 opcode 3 | terminal contract + V-2 |
| 不得僅以 dispatchException 最終值論證路徑正確 | V-2（查驗新增） |
| 不得使用 historical runner / frozen judge | tooling gen 分離 |
| 不得 silent retry 已 frozen 的 endpoint | attempt-09-preflight |
| 不得重跑任何已 frozen 的 attempt | 全部 |
| 不得因 INVALID 就跳號到下一個 attempt 編號 | attempt-09 consumption rule |

---

## 6. CRITICAL PATH V2 與 DEPENDENCY DAG

### 6.1 現在在哪（= PR #10 的進度）

```
R7   ██████████ PASS 13/13          frozen，不重跑
R8   ░░░░░░░░░░ 0/10                C1 attempt-09 NOT STARTED / NOT AUTHORIZED
R9   ░░░░░░░░░░ DESIGN FREEZE 未做
R10  ░░░░░░░░░░ LEDGER DESIGN 未做
P2   ░░░░░░░░░░ closure 未開始
B.3  ░░░░░░░░░░ 未綁 current architecture
GateA(prod) BLOCKED · GateH HOLD · GateW 未定義 final artifact · V1-Core NOT QUALIFIED
```

### 6.2 臨界路徑（唯一序列）

```
[HOST-ONLY，無需 grant]
  P001 PR10 scope audit
  P002 PR7 packet extraction
  P003 tooling hash reverify
  P006 negative-vector bind
  P007 terminal-contract source bind        ← 本輪查驗新增
        │
        ▼
[RUNTIME GRANT #1 — 單格授權]
  R8-C1 attempt-09 ──PASS──► C2 ──► C3-window ──► C3-disconnect ──► C4
        │                      ▲
        │                      └── 需先完成 C2-SRC-TRACE（host）
        └─FAIL/INVALID/BLOCKED─► FREEZE + STOP + RCA + 新 grant
                                     │
                                     ▼
  C5-full ──► C5-overflow ──► D ──► P1 ──► P2 ──► R8-AGG (10/10)
                              ▲
                              └── 需先完成 D-SRC-TRACE + D-HARNESS-DESIGN（host）
        │
        ▼
[R9 DESIGN FREEZE — 不得沿用 PR #7]
  R9-DESIGN → FIXTURE → JUDGE → HOST-VERIFY
            → (PRODUCT-SUPPORT → CI → INSTALL)   ← 僅在 source-trace 證明缺支援時
            → WARM-1/2/3 → COLD-1/2/3 → (RESET) → F1 → F2 → R9-AGG
        │
        ▼
[R10 LEDGER]
  R10-DESIGN → PROBE-INVENTORY → HOST-VERIFY → WARM R1..R5 → COLD R1..R5 → R10-AGG
        │
        ▼
[P2 CLOSURE]  R0..R10 + COUNTERS + UNEXPECTED_FATAL + STABLE + NO_X3_RESIDUE
              + EVIDENCE + CARRY_FORWARD  逐項重新綁定
        │
        ▼
[WORKLOAD]  BOUNDED XFCE (design→baseline)  ∥  P2-B.3 (matrix bind→telemetry→run→analysis)
        │
        ▼
[PRODUCTION GATE A]  只修 R8/R9/R10/workload 證明存在的 gaps
        │
        ▼
[GATE H]  PASS_ROUTER / NOT_REQUIRED_FOR_V1 / REQUIRED_BUT_NOT_ACCEPTED(blocking)
        │
        ▼
[GATE W]  final artifact, real XFCE
        │
        ▼
[V1-CORE ACCEPTANCE]  → QUALIFIED（需 Sol release decision）
```

### 6.3 Host-only 前置層

```
V2-P001-PR10-SCOPE-AUDIT ────┐
V2-P002-PR7-PACKET-EXTRACTION┤
V2-P003-TOOLING-HASH-REVERIFY┼─► V2-P004-EVIDENCE-INDEX-BUILD
V2-P006-NEGATIVE-VECTOR-BIND ┤
V2-P007-TERMINAL-CONTRACT-BIND┤  ← HARD before C1
V2-P008-C1-EXECUTION-INTERFACE-BIND┘ ← HARD before C1
```
`V2-P003` 是所有 R8 device packet 的**軟前置**：未跑仍可執行 C1（C1 自帶 hash precheck），
但 P003 FAIL → 全部 R8 packet 立即 `BLOCKED`。
`V2-P007` 與 `V2-P008` 是 **C1 硬前置**：兩者任一未完成，`V2-R8-C1-09` 只能保持
`FULL_SPEC_EXECUTION_BIND_PENDING`，不得簽 grant、不得 invoke runner。

### 6.4 R8 主鏈（硬順序，不可並行）

```
V2-R8-C1-09 → C2-01 → C3W-01 → C3D-01 → C4-01 → C5F-01 → C5O-01 → D-01 → P1-01 → P2-01 → AGG
```
Host-only 支線（可在等 grant 時先做）：
```
V2-R8-C2-SRC-TRACE  ──► V2-R8-C2-01
V2-R8-D-SRC-TRACE ──► V2-R8-D-HARNESS-DESIGN ──► V2-R8-D-01
```

### 6.5 全域邊（每個 device packet）

```
∀ device packet P:
    ADB-PREFLIGHT(P)          → P
    STABLE-IDENTITY-BEFORE(P) → P → STABLE-IDENTITY-AFTER(P)
    X3-RESIDUE-CHECK(P)       → P → X3-RESIDUE-CHECK-POST(P)
```
這三組不是獨立 packet，是每個 device packet 內的 mandatory phase。缺任一 → 該 attempt `INVALID`。

### 6.6 四個 STOP-THE-LINE 條件

任一成立 → 全線凍結，只允許 RCA，不允許任何 runtime：
```
S1  historical evidence 被覆寫（append-only 違反）
S2  Stable identity before/after 不一致
S3  :3 residue 在 cleanup 後仍存在（process / socket / lock）
S4  同一 attempt 編號出現兩份 runtime evidence
```

---

## 7. R8 十格 ACCEPTANCE（含查驗後修訂）

全域前提（每格皆適用，不再重述）：
PRODUCT `b984ded…` / TOOLING `2a14ab2…` / runner v2 / judge v2 /
semantic JSONL 為唯一語意來源 / END 只能由真 terminal producer emit /
Stable before-after identity 為 mandatory。

### 7.1 C1 — clean pair lifecycle + clean test-control terminate

必須證明的 18 項，缺一不可：
```
 1. pair A direct exact success
 2. pair A resource free / destruction
 3. renderer reverse destruction
 4. ACK / removal correctness
 5. registry / resource balance
 6. fresh distinct pair B（新的 object identity + current generation/tuple binding）
 7. pair B direct exact success
 8. no stale pair A reuse（不得重用仍屬 pair A 的 stale object / tuple / generation ownership；
    完整 retirement 後 allocator 合法重配同一 numeric slot/address 本身不是 FAIL）
 9. clean test-control terminate
10. server TEST_CONTROL TERMINATE observed
11. GiveUp(0)      ← 必須證明進入點為 ProcLorieR8Terminate，非 signal handler（V-2）
12. DE_TERMINATE
13. terminal sequence segment = `V2-P007` source-bound result（不得在此預設 ClearWorkQueue）
14. Gate A generation drain / CloseScreen / DIX cleanup 皆依 P007 綁定的程式位置驗證
15. ddxGiveUp（必須是 P007 綁定 terminal sequence 的末端 DDX hook）
16. X END exactly once
17. renderer END exactly once
18. no semantic obs after END
```
再加：semantic streams complete / judge-v2 PASS / Stable unchanged /
X3 process absent after cleanup / socket 與 lock absent。

**最重要的負向規則：**
> 不得用 cleanup kill 補 product clean exit。
> 若必須 kill 才能結束 → 這本身就是 finding，該 run 最好也只是 `VALID_FAIL`，永遠不是 PASS。

### 7.2 C2 — retained resource + CLIENT_HOLD + requested terminate

**先做 source trace（`V2-R8-C2-SRC-TRACE`，host-only）：**
回答「現有 Class-B orchestration 是否真的足以構造這個狀態？」
需輸出：哪個檔、哪個 symbol、哪條 call path 建立 CLIENT_HOLD；holder 生命週期由誰控制；
terminate 請求如何與 holder 並存。若答案是「不足」→ `DESIGN_REQUIRED`，不得硬跑。

construction：
```
live retained resource + CLIENT_HOLD + requested LORIE-R8 terminate
```
proof（9 項）：
```
clean CloseScreen / gateAClosing / no new admissions / submitted work terminal
registered resource retirement / generation close / renderer unbind / both END
process exit + socket absence
```
明文禁止（三個常見偷渡）：
```
holder death 自動當 clean close       ← 不成立
force-stop 當 proof                   ← 不成立
cleanup signal 當 clean exit          ← 不成立
```

### 7.3 C3-window — Present ASYNC|COPY → 立即 DestroyWindow（查驗後強化）

**option 值寫死（V-4）：**
```
PresentOptionAsync  (1<<0)
PresentOptionCopy   (1<<1)
ASYNC|COPY  ==  0x3        ← packet 必須寫死，不得由 executor 自行組合
```

**兩種合法 trace：**
```
LEGAL-A : waited = 0
LEGAL-B : waited = 1
```
協定依據：presentproto 明載「若 window 在 presentation 發生前被 destroy，
該 presentation action 就不會完成」。因此 judge **不得**以 waited 值本身判 FAIL。

兩者皆必須同時滿足（七項既有 + 三項查驗新增）：
```
既有：
  correct completion coverage
  retirement complete
  no event32
  pending clear
  no fatal
  survivor operation usable
  clean final terminate
新增（V-4）：
  Copy 語意下 idle-fence 在操作發生時觸發（或證明操作未發生）
  PresentPixmap 對 pixmap 的 reference 在完成或取消時釋放，不提早、不殘留
  window destroy 導致未完成時，該 present 走「取消」路徑退休，
    不得記為「完成」，也不得留在 pending
```

非法 trace（出現任一 → 非 PASS）：
```
waited 值不在 {0,1}
completion coverage 不完整
retirement 未完成即 terminate
出現 event32
pending 未清
任何 fatal
survivor operation 不可用
terminate 非 clean
END 缺失 / 重複 / 移位
post-END semantic observation
idle-fence 在操作未發生時被觸發，或操作已發生卻未觸發
pixmap reference 提早釋放或在取消後仍殘留
```

### 7.4 C3-disconnect — Present client disconnect

必須證明：
```
disconnected client 的 pending work 完成退休
server generation 仍然 healthy
另一個 survivor client（同一 generation）可完成 direct exact success
之後 clean terminate
```
**最關鍵禁令：**
> 不能拿「新的 X process 成功」替代「same-generation survivor proof」。

換 process 等於換 generation，證明的是別的命題。
`FORBIDDEN_TRACE` 必須明列：`survivor proof obtained from a new X process / new generation` → `INVALID`。

### 7.5 C4 — REGISTER_BUFFER only

construction：
```
REGISTER_BUFFER only / source 與 dst READY / no Composite / no direct submit / then free
```
exact forbidden list（出現任一即非 PASS）：
```
LEASE_RESERVED · GPU_OWNED · UNLOCK · PUBLISH · CONSUME · terminal wait for target
```
require：
```
lastSubmittedSerial = 0 · pending = 0 · proper unregister · renderer destroy · ACK · balance zero
```
C4 的意義：證明「只註冊、不使用」不會偷偷觸發 lease / GPU ownership。
因此 judge 必須以 **forbidden 為主判**，require 為輔。

### 7.6 C5-full — capacity fill

**容量單位（重大更正）：**
```
capacity unit = BUFFER SLOTS      ← 正確
capacity unit = pairs             ← 錯誤，PR #8 的敘述需被覆蓋
```
凍結值：
```
X registry capacity = 16 · renderer READY = 16 · pending import = 8
```
**Phase 0（cell 內，不是新 cell）—— 先量 baseline occupancy：**
```
usable slots = capacity - actual occupied
```
occupancy ≠ 0 → **不得硬塞 16 個 new buffer**，必須以 measured usable slots 為上限。
Phase 0 量測結果寫入 evidence，並成為 C5-overflow 的輸入。

執行：`只 sequential register（不得並行）` → `填到 measured usable slots` → `close 後 all tracked resources 歸零`

常見誤判：occupancy 原本為 3 卻硬塞 16 → 實際在測 overflow，不是測 full →
判 `INVALID_CONSTRUCTION`，不是 FAIL。

### 7.7 C5-overflow — refusal 證明

construction：`fresh X` → `fill measured free capacity（用 C5-full phase 0 的值）` → `attempt one extra buffer`

必須證明：
```
refusal 發生在 pre-lease 階段 · no unlock · no publish · no GPU ownership · no silent eviction
```
fallback：合法 fallback **必須 exact**，packet 要列出允許的具體形式與 trace；
未列出的形式 → 非 PASS。

recovery：`free one slot` → 新的 allocation / admission 必須成功，
且必須證明這是真正的 recovery（新 slot 被使用），不是 refusal 的殘留狀態。

### 7.8 R8-D — 真實 overlap（本格寫最細）

Goal：
```
Gate A resource retirement   ⟂ 同時 ⟂   Present GPU completion / wakeup 進入 deferred path
```

**先決條件：兩個 host-only DESIGN packet**

`V2-R8-D-SRC-TRACE` 必須以 source 為據回答（不得臆測）：
```
哪個 event producer 觸發 deferred path
哪個 thread 擁有該 producer
哪個 queue 承載該 event
exact schedule seam 在哪（哪一行、哪兩個狀態之間）
如何 deterministic 地讓兩者在該 seam 相遇
```
`V2-R8-D-HARNESS-DESIGN` 把該 seam 轉成可重現的構造步驟。

未完成這兩個 packet 前，`V2-R8-D-01` 永遠 `DESIGN_REQUIRED`，不得執行。

構造禁令（這格最容易被作弊）：
```
arbitrary sleep · retry-until-hit · fake event
renderer delay just for timing · manual log injection
```
特殊分類：
```
overlap 未形成 → INVALID_CONSTRUCTION（不是 FAIL）
```
必須寫進 packet 的 `INVALID` 欄與 `LUNA_PROMPT` ——
executor 最容易把「沒撞上」誤報成 product FAIL。

### 7.9 R8-P1 — destroy-while-gpu-owned

```
enum14, side = X
before hook : GPU_OWNED proven（不是假設，是證明）
expected    : x-destroy-in-lease, reason 7
forbidden   : ACK / normal release / later success / normal generation close
```
**scope 誠實聲明（必須寫進 packet 與報告）：**
> 本格是 **synthetic containment proof**。
> **不得宣稱**「任意真實世界非同步 destructor race 已被完整證明」，
> 除非 actual call path 真的執行了 destructor。

### 7.10 R8-P2 — close-while-lease

```
enum15
active lease → close generation → fatal
expected  : x-close-in-lease, reason 8
forbidden : normal CLOSED / lease release / success continuation
```

### 7.11 R8 AGGREGATE（`V2-R8-AGG`）

10/10 才 aggregate PASS。aggregate **不是**把 judge 輸出收集起來，
必須重新驗證 12 項：
```
 1. product binding（每格都綁 b984ded…，無例外）
 2. tooling binding（每格都綁 2a14ab2… 與九個 hash）
 3. 每格 cell attempt ID 完整且唯一
 4. no duplicate attempts（同編號不得有兩份 evidence）
 5. Stable before/after（每格都有，且皆 unchanged）
 6. unexpected signal audit（全域為 0）
 7. fatal expected-only audit（只有 P1/P2 允許 fatal，且必須是 expected 的那一個）
 8. no X3 residue（每格 cleanup 後）
 9. evidence hashes（每格 sha256sums.txt 可重算且相符）
10. judge authority（全部 judge-r8-v2.py，無一格用 frozen judge）
11. collector authority（全部 collect-r8.py）
12. tooling amendments（期間若有 tooling 變更 → 逐筆列出並評估是否使先前格失效）
```
**即使 12 項全過且 10/10 PASS：Production Gate A 仍 BLOCKED。**
R8 只是 P2 runtime closure 的一個輸入，不是 Gate A 的替代品。

---

## 8. R9

### 8.1 為什麼不能直接沿 PR #7 跑

PR #7 的 R9 建立在舊 source snapshot 上。必須先對 **current b984ded lineage**
重新 source-inspect，再建 harness。

### 8.2 DESIGN FREEZE 必須 resolve 的 11 個問題

| # | 問題 | 依據 | 未解的後果 |
|---|---|---|---|
| Q1 | warm new X with same Activity：Activity 保留了什麼？ | source trace | warm/cold 界線不明 |
| Q2 | cold Activity restart：什麼被真正重建？ | source trace | cold 可能其實是 warm |
| Q3 | generation nonce lifecycle：何時配、何時失效、誰比對 | source symbol | stale generation 無法判定 |
| Q4 | renderer retained state：跨 generation 保留什麼 | source trace | F1 無法設計 |
| Q5 | stale READY：舊 generation 的 READY 是否可能被新 generation 看到 | source + runtime | 最危險的 UAF 面 |
| Q6 | stale generation frames：舊 frame 進新 generation 的路徑是否存在 | source trace | F1 判準不成立 |
| Q7 | PID reuse：PID 是否足以識別 process | 不足 → 必須加 starttime | 身分誤判 |
| Q8 | process starttime：可否穩定取得 | probe 驗證 | 退回單用 PID，造成身分誤判 |
| Q9 | socket lifecycle：何時建立/移除，是否跨 generation 殘留 | source + runtime | residue 判定不成立 |
| Q10 | same-process reset support：product 是否支援 | source trace | 決定 R9-RESET 是否存在 |
| Q11 | fresh recovery after fatal：fatal 後可否乾淨重來 | source + runtime | F2 判準不成立 |

### 8.3 身分識別規則（由 Q7/Q8 導出）

```
process identity = (PID, starttime)      ← 兩者皆必須
process identity = PID                   ← 禁止（PID reuse 造成偽陽性）
```
starttime 不可得 → `DESIGN_REQUIRED`（D-13），由 Astra 決定替代識別，
**不得**退回單用 PID。

### 8.4 warm / cold 的嚴格定義

```
WARM : Activity 未重啟，X server 為新；Activity 側保留狀態存在
COLD : Activity 重啟；Activity 側狀態應全部重建
```
每個 R9 runtime packet 必須在 evidence 中證明自己落在哪一邊
（Activity identity + process identity + generation nonce 三者同時記錄），
**不得**以「我們是這樣啟動的」作為證明。

> 查驗 V-8 相關：官方文件明載通知列 Exit 不會結束 `termux-x11` 指令。
> 因此 R9 的 cold 判定必須確認 **process 真的消失**，不能只看 Activity 狀態。

### 8.5 conditional 分支：R9-PRODUCT-SUPPORT

只有在 §8.2 的 source trace 證明 current lineage **缺少**必要支援時才啟用。
啟用即代表會產生新 PRODUCT_SHA，連鎖觸發：
```
CARRY-FORWARD 新條目（touched-symbol matrix 強制）
R8 是否需要 requal 的評估（Astra 決策 D-12）
新 CI + 新 artifact + 新 install + 新 grant
```
**不得**為了讓 R9 好跑而順手改 product。

### 8.6 DESIGN FREEZE 產出物

```
r9-design-freeze.md        11 問的逐題答案 + source 引用
r9-identity-contract.json  process identity / generation nonce 判定規則
r9-cell-spec.json          每個 R9 cell 的 construction + proof + forbidden
r9-decision-log.md         Astra/Sol 決策（Q10 scope、Q4 ownership）
```
四者齊備前，R9 任何 runtime packet 一律 `BLOCKED`。

### 8.7 Packet 序列（不要一個 packet「完成 R9」）

| # | PACKET_ID | 類型 | 前置 |
|---|---|---|---|
| 1 | `V2-R9-DESIGN` | DESIGN（Astra/Sol） | `V2-R8-AGG` PASS |
| 2 | `V2-R9-FIXTURE` | host | 1 |
| 3 | `V2-R9-JUDGE` | host | 1 |
| 4 | `V2-R9-HOST-VERIFY` | host | 2,3 |
| 5 | `V2-R9-PRODUCT-SUPPORT` | DESIGN，conditional | 1（僅缺支援時） |
| 6 | `V2-R9-CI` | CI，conditional | 5 |
| 7 | `V2-R9-INSTALL` | device，conditional | 6 |
| 8–10 | `V2-R9-WARM-1/2/3` | device | 4（或 7），逐輪串接 |
| 11–13 | `V2-R9-COLD-1/2/3` | device | 10 PASS，逐輪串接 |
| 14 | `V2-R9-RESET` | device，conditional | 13 PASS + Q10 支援成立 |
| 15 | `V2-R9-F1-STALE-REPLAY` | device | 13（或 14）PASS |
| 16 | `V2-R9-F2-RECOVERY` | device | 15 PASS |
| 17 | `V2-R9-AGG` | ASTRA | 16 PASS |

每個 warm/cold packet 的共同必證項：
```
Activity identity（warm 同一個 / cold 新的）
process identity = (PID, starttime)
generation nonce 正確更新，舊 nonce 不被接受
renderer retained state 與設計一致
no stale READY 被新 generation 消費
no stale generation frame 被接受
socket lifecycle 正確（舊 socket 不殘留）
resource balance 歸零 · Stable unchanged · no X3 residue
```

### 8.8 F1 / F2 的判準差異（最容易混淆）

```
F1 stale replay : 目標是「精確 containment」。
                  construction 必須把舊 generation READY/frame 真正送入 current path。
                  expected fatal = x-wrong-generation / reason6（enum16 / side2）。
                  exact expected fatal + stale state 未被 current generation 接受 → PASS。
                  stale state 被接受 / current state 被污染                  → VALID_FAIL。
                  payload 根本沒送進去 / hook 沒命中                        → INVALID_CONSTRUCTION。
                  fatal type/reason 不符                                      → VALID_FAIL 或 INVALID，依 evidence 完整性分類。

F2 recovery     : 只在 F1 已取得 expected fatal 後執行 fresh session recovery。
                  必須 new nonce / empty registry / clean direct exact SUCCESS。
                  fresh session 有 stale residue / 無法 direct success         → VALID_FAIL。
                  F1 expected fatal 前提不存在                                 → BLOCKED（不得自行製造另一個 fatal）。
```

---

## 9. R10 — measurable resource ledger

### 9.1 取樣點（每輪 4 個，固定）

```
K0  pre-work        （workload 尚未開始）
K1  after workload  （workload 完成，尚未釋放）
K2  after frees     （明確釋放後）
K3  after close     （generation close / process exit 後）
```

### 9.2 輪數與模式

```
>= 5 rounds · warm + cold 各自成套
```
輪數不足 5 → 不得宣稱 R10 accepted（趨勢無法與雜訊區分）。

### 9.3 Metrics（每個取樣點都要採，缺者填 null）

```
X fd · Activity fd · RSS · PSS
X registry · renderer registry · lease current · endpoint pending · root pending
AHB acquire/release · EGLImage create/destroy · GL texture create/delete
thread count · maps count · process identity · socket · lock · generation nonce
```
> 查驗 V-5 / V-6 支持其中三項：`AHardwareBuffer_acquire/release`、
> `EGL_ANDROID_get_native_client_buffer` → `EGLImageKHR` 的 create/destroy、
> 以及 AHB lock/unlock 的 **fence fd 所有權轉移**（新增，見 §9.4）。

### 9.4 新增 metric（由 V-5 導出）

```
ahb_lock_in_fence_fd_count      傳入 AHardwareBuffer_lock 的 fence fd 數
ahb_unlock_out_fence_fd_count   自 AHardwareBuffer_unlock 取出的 fence fd 數
ahb_fence_fd_leaked             取出但未被 close 也未被轉移的 fd 數
```
理由：fence fd 是真正的 fd，會計入 process fd 上限；
若 unlock 取出後被直接 close 當作「同步完成」，既是 correctness bug 也是 fd 會計黑洞。

### 9.5 不可觀測的處理（唯一規則）

```
not observable  →  null
not observable  →  0        ← 永久禁止
```
`0` 是一個測量結果，代表「量到了，值是零」。
把未量到寫成 `0` 會讓 leak 被稀釋成「沒有 leak」，是最危險的測量偏誤。

`V2-R10-PROBE-INVENTORY` 逐一判定每個 metric 是 observable 還是 null 並凍結該判定；
之後任何一輪若某 metric 從 null 變成有值（或反之），必須觸發重新檢視，不得靜默接受。

### 9.6 leak 判定

```
K3 相對 K0 的差值，跨 >=5 rounds：
  單調上升      → 疑似 leak
  上升後持平    → 一次性配置，非 leak（但需說明）
  雜訊範圍內    → 需事先定義該 metric 的雜訊範圍，否則不得下結論
```
「雜訊範圍」必須在 `V2-R10-DESIGN` 中為每個 metric **事先**定義，
不得在看到數據後才決定。leak disposition 是 Astra 決策（D-04）。

### 9.7 Packet 序列

| # | PACKET_ID | 類型 | 前置 |
|---|---|---|---|
| 1 | `V2-R10-DESIGN` | DESIGN（Astra） | `V2-R9-AGG` accepted |
| 2 | `V2-R10-PROBE-INVENTORY` | host | 1 |
| 3 | `V2-R10-HOST-VERIFY` | host | 2 |
| 4–8 | `V2-R10-WARM-R1..R5` | device | 3，逐輪串接 |
| 9–13 | `V2-R10-COLD-R1..R5` | device | 8 PASS，逐輪串接 |
| 14 | `V2-R10-AGG` | ASTRA | 13 PASS |

每輪 packet 的固定結構：
```
phase 0  preflight（ADB / screen / stable / X3 / artifact）
phase 1  K0 採樣
phase 2  workload（由 design 凍結，每輪完全相同）
phase 3  K1 採樣
phase 4  明確釋放
phase 5  K2 採樣
phase 6  close / exit
phase 7  K3 採樣
phase 8  stable after + X3 residue after + hash manifest
```
workload 每輪必須**完全相同**。任何一輪改動 workload → 該 series 全部作廢，不是只作廢那一輪。

evidence 格式：`ledger.json { round, mode: warm|cold, K0:{...}, K1:{...}, K2:{...}, K3:{...} }`
每個 metric 為數字或 `null`。**禁止**出現 `"0"`、`"unknown"`、`"-"`。

---

## 10. P2 RUNTIME CLOSURE

R8 10/10 + R9 accepted + R10 accepted **全部成立之後**才重新審 P2。
提前審 = 拿一個會變動的狀態下結論。

每一項必須標註為 **`CURRENT_CANDIDATE_BOUND`** 或 **`ACCEPTED_CARRY_FORWARD`**。第三種狀態不存在。

| # | 項目 | 綁定要求 |
|---|---|---|
| 1–7 | R0 / R1 / R2 / R3 / R4 / R5 / R6 | 需綁 current PRODUCT_SHA 的證據，或明確 carry-forward 批准；R6 另須確認 design-complete 現況（歷史上曾未被宣稱） |
| 8 | R7 | PASS 13/13，historical source `a4c8177f…`；需 carry-forward 決策（CF-PENDING-001） |
| 9 | R8 | 10/10，綁 current PRODUCT_SHA |
| 10 | R9 | accepted，綁 current PRODUCT_SHA |
| 11 | R10 | accepted，綁 current PRODUCT_SHA |
| 12 | COUNTERS | 全域 counter 一致、無重複 attempt |
| 13 | UNEXPECTED_FATAL | 全域為 0（P1/P2 的 expected fatal 除外且須逐一對應） |
| 14 | STABLE | 每個 device attempt 的 before/after 皆 unchanged |
| 15 | NO_X3_RESIDUE | 每個 cleanup 後皆成立 |
| 16 | EVIDENCE | hash 可重算且相符；append-only 未被違反 |
| 17 | CARRY_FORWARD | 每一筆皆有 matrix 條目與 review decision |

**核心原則：**
> **historical pass 不自動有效。**

R0–R7 是在舊 PRODUCT_SHA 上取得的。要嘛在 current PRODUCT_SHA 上重新取得，
要嘛經 touched-symbol matrix 證明不受影響並由 Astra 明確批准。
「看起來不相關所以應該沒事」不是批准。

產出：`p2-closure-ledger.json`（17 項 × {status, evidence_ref, decision_ref}）、`p2-closure-report.md`。
任一項既非 bound 也非 accepted → P2 closure 未完成，後續 workload / Gate 階段一律 `BLOCKED`。

---

## 11. BOUNDED XFCE

在 `V2-XFCE-DESIGN-FREEZE` 之前不得執行任何 XFCE session。
XFCE 是變異度最高的 workload，未凍結參數的兩次執行不可比較。

**必須凍結的 13 項：**
```
duration                 精確秒數
resolution               精確像素（必須指明 internal 1200×2608 或 external 3440×1440）
compositor               開/關與版本
window choreography      開窗順序、數量、位置（腳本化，不得手動）
terminal                 哪個 terminal、什麼指令
open / close             次數與時機
resize                   起訖尺寸與次數
redraw                   觸發方式與次數
expected Gate A traffic  預期會走到哪些 Gate A 操作
shutdown path            如何結束（必須是 clean path）
metrics                  採哪些、在哪些時點
resource proof           K-point 對應（與 R10 ledger 對齊）
crash proof              crash 判定與證據形式
```

**Baseline vs Final 的分界（關鍵）：**
```
若後續 PRODUCT_SHA 還會變 → 本次結果只能是 BASELINE，不得直接當 final Gate W
```
判定不靠猜：
```
Production Gate A 的 gap inventory 尚未關閉 → 必然還會變 → BASELINE
Gate A 已 CLOSE 且 PRODUCT_SHA 凍結         → 才可能是 final
```
這條規則存在，是因為 bounded XFCE 跑一次成本高，
很容易產生「反正跑過了就當 Gate W」的誘惑。**不允許。**

產出：`xfce-design-freeze.json` / `xfce-run-<sha>.json` / `xfce-verdict.md`（BASELINE 或 FINAL_CANDIDATE，附理由）

---

## 12. P2-B.3 效能

保留歷史矩陣概念，但**綁 final / current architecture**。
舊的 B.3a cost census 結論（staging path 於 batch16 中位數較 CPU 慢 1.299×）
是歷史輸入，不是 current 判決。

### 12.1 掃描矩陣（含 V-9 修正）

```
rectangle (11)   1x1 · 5x24 · 16x16 · 32x32 · 64x64 · 128x128 · 256x256 · 512x512 · 1024x1024
                 · fullscreen-internal (1200×2608) · fullscreen-external (3440×1440)
src/rect  (4)    1x · 4x · 16x · large redirected source
reuse     (4)    1 · 4 · 16 · 64
batch     (4)    1 · 4 · 8 · 16
residency (4)    cold · warm · resize · destroy/recreate
readback  (3)    GPU-only · immediate GetImage · delayed CPU read
```
完整笛卡兒積 = 11 × 4 × 4 × 4 × 4 × 3 = **8448 cells**。

> **V-9 修正：** 原本單一的 `fullscreen` 是歧義值。
> 內建面板 1,200×2,608 = 3,129,600 px；外接 3,440×1,440 = 4,953,600 px，相差約 1.58×，
> 落在完全不同的成本區間，結論不可互換。
> 若某輪只測 internal，其結論**不得**外推到 Gate W 的外接螢幕情境。

`V2-B3-MATRIX-BIND` 必須決定取樣策略（全掃 / 分層 / 剪枝），並**說明剪掉的組合為何不影響結論**。
未說明的剪枝 = 結論不成立（Astra 決策 D-11）。

### 12.2 Telemetry（每 cell 都要，缺者 null）

```
prepare · promotion · clone bytes/time · upload bytes/time · queue latency
GPU exec (nullable) · fence wait · DoneComposite · repair bytes/time
wall · CPU · GPU activity · RSS · FD · correctness
frame p50/p95/p99 · jank · temperature · thermal throttling state · copy amplification
```
鐵則與 R10 相同：`missing != 0`，`missing == null`。
`V2-B3-TELEMETRY-VERIFY` 必須先證明哪些欄位可觀測並凍結該判定。

### 12.3 結論形式

B.3 的產出不是「快了幾倍」，而是：
```
在哪些 (rect, ratio, reuse, batch, residency, readback) 區域 GPU 路徑勝出
在哪些區域落後
交叉點在哪（若存在）
交叉點是否穩定（跨 thermal state、跨 residency、跨 internal/external 解析度）
```
這份結論是 Gate H 的**唯一合法輸入**。

---

## 13. PRODUCTION GATE A

### 13.1 範圍鐵則

> **只修 V1-Core 真正被 R8 / R9 / R10 / workload 證明存在的 production gaps。**

明文禁止：`speculative redesign` · `large cleanup refactor` · `Full Global GPU expansion`

一個 gap 要進 inventory，必須指出**哪一格、哪一份 evidence、哪一個 predicate 為假**。
沒有 evidence 指向的 gap → 不進 inventory（可記入 deferred）。

### 13.2 每個 gap 的固定八步

```
1. RCA                 root cause 必須被證明，不是被推測
2. minimal design      能關掉這個 gap 的最小改動
3. host tests          先在 host 側驗證（含負向向量）
4. source patch        實作
5. CI                  僅在 product 變更時
6. artifact            僅在 product 變更時
7. install             僅在 product 變更時
8. affected requal     受影響 gate 重新驗證 + carry-forward review
```
步驟不得合併、跳過、換序。特別是 **1 不得在 4 之後補寫**——「先改好再解釋」不是 RCA。

### 13.3 已知六個 production-contract 缺口（歷史輸入，需重新確認仍缺）

```
1. CPU ownership release transition
2. import-ready acknowledgment
3. per-serial success/failure with quiesced replay
4. acquire/release publication
5. generation-bound drain/unregister lifecycle
6. producer-fence contract for imported / client-owned AHB
```
若 R8/R9/R10 的證據顯示其中某項**其實已成立** → 不進 inventory，
並在 `p2-closure-ledger` 標為已由 runtime 證據覆蓋。

**缺口 #6 的最小設計要求（由查驗 V-5 新增）：**
```
AHardwareBuffer_lock 必須傳入真實的 producer fence fd
  （不得傳 -1 當作「沒有 fence」而略過等待）
AHardwareBuffer_unlock 必須取出 fence fd 並交給下一個 consumer
  （不得 close 掉就當作同步完成）
fence fd 的所有權轉移必須在 R10 ledger 中以 fd 計數可觀測（§9.4）
```

### 13.4 連鎖效應（每次 product 變更的代價）

```
新 PRODUCT_SHA
  → CARRY-FORWARD 強制新條目（touched-symbol matrix）
  → 受影響 gate 的 requal 範圍由 Astra 決定
  → 已跑完的 XFCE / B.3 結果降級為 baseline
  → R8 是否需重跑（可能部分格，也可能全部）
```
這條連鎖就是「只修被證明的 gap」的真正理由——每一次多餘的改動都會讓整個 R 系列的證據失效。

### 13.5 關閉條件（`V2-PGA-CLOSE`，Sol 決策）

```
inventory 內每個 gap 皆完成八步
每個 requal 皆 PASS
CARRY-FORWARD 每條皆有 review decision
沒有任何 gap 以「暫時接受」狀態留下（要嘛關、要嘛明確 deferred 並記錄）
```

---

## 14. GATE H

### 14.1 三個合法狀態

```
PASS_ROUTER                evidence 證明 router 需要，且設計/實作/驗證全部通過
NOT_REQUIRED_FOR_V1        evidence 證明沒有穩定 crossover，或單一路徑已足夠，因此 V1 不需要 router
REQUIRED_BUT_NOT_ACCEPTED  evidence 顯示 router 有必要，但設計/實作/驗證尚未通過；阻擋 V1-Core
```

**禁止狀態漂移：** router implementation / verification 失敗，不得自動改寫成 `NOT_REQUIRED_FOR_V1`。
`NOT_REQUIRED_FOR_V1` 只能由 **evidence decision 本身** 得出。

### 14.2 Router 的輸入（至少 10 項）

```
semantic support · residency · dirty bytes · src/rect ratio · reuse
batch · queue occupancy · readback hazard · ownership state · measured cost
```

### 14.3 明文禁止

```
pixel-size-only heuristic       ← 禁止
```
除非 B.3 的 evidence **量化證明**單靠像素大小已足夠
（即在全部其他維度上，像素大小的預測力不低於完整模型）。

理由有二：
1. B.3a 歷史結論已顯示 staging path 在 batch16 上比 CPU 慢 1.299× ——
   像素大小之外的維度會主導成本。
2. 查驗 V-9 顯示 `fullscreen` 本身就有 internal / external 兩個相差 1.58× 的值——
   以「像素大小」為單一輸入時，連這個維度自己都不是良定義的。

### 14.4 決策歸屬

`V2-GH-MODEL-DECISION` 是 **Astra 決策**（D-07）。Luna 不得選模型、不得調閾值。

---

## 15. GATE W

### 15.1 必須是 final artifact

前提：`Production Gate A CLOSE` + `PRODUCT_SHA 凍結（Gate W 期間不得變動）`。
期間若 PRODUCT_SHA 變動 → Gate W 結果作廢，重跑。

### 15.2 Real XFCE 必測項目

```
GPU hit rate · CPU fallback · fbComposite/pixman 使用量 · Gate A operations 分布
CPU/frame · wall/frame · upload bytes · GPU activity
p50/p95/p99 · jank · RSS · FD · thermal · crash
resize · destroy/recreate · Activity lifecycle
```

### 15.3 最重要的一句

> **hit rate 高不等於 PASS。**

高 hit rate 可以與以下任一併存，而任一都足以讓 Gate W 不通過：
```
p99 惡化（平均變好、最差變壞）· jank 增加 · RSS/FD 隨時間上升
thermal throttling 提早進入 · resize / destroy-recreate 路徑不穩
Activity lifecycle 事件後行為異常 · crash（任何一次）
```
因此 Gate W 的驗收必須是**全指標同時達標**，不是單指標最佳化。

### 15.4 門檻設定

各指標門檻由 `V2-GW-DESIGN-FREEZE` **事先**凍結（Astra 決策 D-08），
不得在看到結果後調整。看到結果才訂門檻 = 沒有門檻。

產出：`gw-design-freeze.json` / `gw-run.json` / `gw-verdict.md`（PASS / NOT PASS + 逐指標對照）

---

## 16. V1-CORE ACCEPTANCE

### 16.1 QUALIFIED 的必要條件（19 項，全部成立，無例外）

```
 1. R7 13/13
 2. R8 PASS 10/10
 3. R9 accepted
 4. R10 accepted
 5. P2 closure 完成（17 項皆 bound 或 accepted carry-forward）
 6. exact narrow Over correctness（pixel-exact，無模糊容差）
 7. safe lifecycle（restart / teardown / recreate 全程安全）
 8. clean resource balance（無殘留、無 UAF、無跨 generation 狀態）
 9. unsupported fallback safe（不支援的 mask/transform/repeat/filter 安全退回）
10. final-artifact performance evidence（非 microbenchmark）
11. Production Gate A required gaps closed
12. Gate H = PASS_ROUTER 或 evidence-backed NOT_REQUIRED_FOR_V1；REQUIRED_BUT_NOT_ACCEPTED 會阻擋 V1
13. Gate W PASS
14. p95 / p99 / jank acceptable
15. RSS / FD no regression
16. thermal sustained acceptable
17. Stable untouched（全程、每一格）
18. no X3 residue（全程、每一格）
19. complete provenance（每份 evidence 可追溯到 product + tooling SHA）
```
全部成立 → 才可宣告 `F8 Termux:X11 GPU Acceleration V1-Core QUALIFIED`。

### 16.2 誰能宣告

`V2-V1-RELEASE-DECISION` 是 **Sol 決策**（D-09）。Luna 不得宣告，Astra 不得單獨宣告。

### 16.3 部分達成的處理

19 項中有任一未達成 → 狀態為 `NOT QUALIFIED`。
**不存在**「條件式 QUALIFIED」或「除了 X 以外都過了」這種發布狀態。

### 16.4 終極目標（V1-Core 之後）

```
MSI 3440×1440@60 外接螢幕上的日常可用 Termux:X11 桌面
```
V1-Core 是通往該目標的第一個可驗收里程碑，不是目標本身。

### 16.5 DEFERRED WORK（不阻塞 V1-Core）

```
V1-UWQHD · 3440x1440@60 · 90/120 Hz · high-refresh tuning
Full Global GPU · general mask · two-pass · transform · bilinear · repeat
componentAlpha · full XRender coverage · A8 mask · Glamor · ANGLE Vulkan
```
**Deferred 的意思是：不在 V1-Core 的 acceptance 條件內，也不得在 V1-Core 期間開工。**
任何一項若被提前動工 → 觸發 §13.4 的連鎖失效代價。

> 查驗 V-9 補充理由：裝置內建面板為 1200×2608@120Hz，外接目標 3440×1440@60。
> 兩者像素量差 1.58×、刷新率不同、熱行為不同——
> 這正是把 UWQHD 與 high-refresh 留在 deferred 的具體依據，不只是排程取捨。

---

## 17. RISK REGISTER

格式八欄：`mechanism` / `likelihood` / `impact` / `detection` / `preventive` / `recovery` / `blocking stage` / `evidence`
值域：`LOW` `MED` `HIGH`

| ID | 風險 | mechanism | L | I | detection | preventive | recovery | blocking | evidence |
|---|---|---|---|---|---|---|---|---|---|
| R-01 | R8 teardown 未完成 | dispatch → ddxGiveUp 鏈條中斷（attempt-07 型） | MED | HIGH | EXPECTED_TRACE 逐元素比對 | terminal contract 寫死於每個 packet | freeze + RCA，需新 SHA + grant | R8 全線 | 完整 trace + 退出證明 |
| R-02 | post-END observation | END 後仍有 semantic record 被採計 | MED | HIGH | counter expected 0 tol 0 | END 只能由真 terminal producer emit | INVALID，不得 dedupe | R8/R9 | 兩條 stream 完整尾段 |
| R-03 | judge integrity | 誤用 frozen judge，或在不完整輸入上下判 | MED | HIGH | JUDGE_HASH 前置比對 | 每 packet 綁 hash；historical 列黑名單 | INVALID，不得改判 | R8 | hash 驗證 + verdict 原文 |
| R-04 | tooling/product 身分混淆 | SHA 填錯欄位 | HIGH | HIGH | schema V-04 | ANTI-CONFUSION RULE | evidence INVALID | 全線 | 欄位對照 |
| R-05 | R9 stale generation | 舊 generation 的 READY/frame 被接受 | MED | HIGH | nonce 比對；F1 | Q3/Q5/Q6 必須先答 | VALID_FAIL → 修復 | R9 起 | nonce 序列 + 拒絕記錄 |
| R-06 | PID reuse | PID 回收造成身分誤判 | LOW | MED | (PID, starttime) 雙元組 | identity contract 禁止單用 PID | 重採；不可得則 DESIGN_REQUIRED | R9/R10 | identity 雙元組 |
| R-07 | Activity retained state | warm/cold 實際無差別 | MED | MED | 分類需在 evidence 層證明 | §8.4 嚴格定義 | 該 series 作廢重跑 | R9 | 三者同時記錄 |
| R-08 | HUP | 連線中斷造成非預期 teardown | LOW | MED | unexpected_signals counter | ENV_DENYLIST；穩定 lane | INFRA_BLOCKED | 任何 device packet | signal audit |
| R-09 | surface loss | Activity surface 中途失去 | MED | MED | screen precheck + surface 事件 | Awake/Display ON 前置 | INFRA_BLOCKED | 任何 device packet | screen 前後記錄 |
| R-10 | socket lifecycle | :3 socket/lock 跨 session 殘留 | MED | HIGH | X3 前後雙向檢查 | 每 packet 強制前後檢查 | 前置→BLOCKED；後置→INVALID + S3 | 全線 | x3-residue-before/after |
| R-11 | AHB ownership | CPU/GPU 持有權轉移不完整 | MED | HIGH | lease 於每 boundary 必為 NONE | C4 forbidden list；P1/P2 | VALID_FAIL → 修復 | C4/P1/P2 | ownership 狀態序列 |
| R-12 | fence 契約缺失 | producer fence 未建立或未等待 | MED | HIGH | fence wait telemetry；缺口 #6 | Gate A 八步 + §13.3 三條 | RCA → minimal design | Gate A | fence telemetry |
| R-13 | Present cross-op | Present 與 Gate A 操作順序錯亂 | MED | HIGH | R8-D overlap 構造 | D-SRC-TRACE 先找 seam | INVALID_CONSTRUCTION 或 VALID_FAIL | R8-D | seam + overlap 證明 |
| R-14 | resource leak | K3 相對 K0 單調上升 | MED | HIGH | R10 ledger ≥5 rounds | 每 metric 雜訊範圍事先定義 | Astra disposition（D-04） | R10/P2 | ledger series |
| R-15 | queue drain | ClearWorkQueue 時仍有未完成工作 | MED | HIGH | pending=0 於 teardown boundary | C1/C2 必證項 | VALID_FAIL | C1/C2 | pending gauge 序列 |
| R-16 | ADB endpoint churn | SERIAL 變動；舊 endpoint 被 silent retry | HIGH | MED | 每次 preflight fresh 探索 | 禁止 hardcode；frozen endpoint 黑名單 | INFRA_BLOCKED，且 NOT CONSUMED | 任何 device packet | preflight.json |
| R-17 | screen / keyguard | 休眠或鎖定造成 session 異常 | MED | MED | SCREEN_PRECHECK | 執行前確認 Awake | INFRA_BLOCKED | 任何 device packet | screen 記錄 |
| R-18 | artifact drift | 裝置上 APK 與 packet 綁定不符 | LOW | HIGH | ARTIFACT_PRECHECK 四項 | 每 packet 強制 readback | BLOCKED（不得 reinstall 後續跑） | 全線 | dumpsys 原文 |
| R-19 | carry-forward drift | historical pass 被默默當 current | HIGH | HIGH | P2 closure 二選一強制 | touched-symbol matrix 強制 | 重新綁定或撤回 | P2 closure 起 | matrix review decision |
| R-20 | measurement bias | 不可觀測填 0；事後訂門檻 | HIGH | HIGH | schema 禁 0 代 null；門檻需事先凍結 | PROBE-INVENTORY / DESIGN-FREEZE 先行 | 該 series 作廢 | R10/B.3/Gate W | freeze 時間戳先於 run |
| R-21 | thermal throttling | 長工作負載降頻污染效能比較 | HIGH | MED | temperature + throttling 為必測 | 每 run 記錄熱狀態；同熱狀態才比較 | 標註並於可比熱狀態重跑 | B.3 / Gate W | 每 cell thermal 欄位 |
| R-22 | desktop workload variance | XFCE 兩次執行不可比較 | HIGH | MED | 13 項凍結參數比對 | DESIGN-FREEZE 先行；choreography 腳本化 | 作廢重跑 | XFCE / Gate W | freeze 與 run 一致性 |
| **R-23** | **terminal contract 順序誤判**（查驗新增） | 上游 DIX 與凍結契約的 resource-teardown / CloseScreen 順序相反，judge 可能把正確的 run 判成 FAIL | **HIGH** | **HIGH** | V-3 已偵測 | `V2-P007` 先行；該項暫不得單獨判 FAIL | 升級為 DESIGN_REQUIRED，不得判 VALID_FAIL | R8-C1 起 | b984ded 原始碼 trace |
| **R-24** | **adb 旗標語意錯誤**（V-7 提出，**V-7R 已證偽並關閉**） | 原假設：`-L` 被當 client 旗標會連到非預期 server。2026-09-21 本機實測三形式皆正確到達目標 port，機制不成立 | **CLOSED** | — | V-7R 實測 | 保留 `-P` 為唯一 packet 形式，理由改為 provenance | 不再適用 | — | V-7R 量測紀錄 |
| **R-25** | **C1 allocator reuse false-red** | 把已完整退休後的 numeric slot/address 重配誤判為 stale pair reuse | **MED** | **HIGH** | object identity + generation/tuple + ownership retirement | V-10 identity contract | INVALID spec / BLOCKED grant until packet corrected | R8-C1 | pair A retirement + pair B identity evidence |
| **R-26** | **Gate H bypass** | router 驗證失敗被錯改為 NOT_REQUIRED，使 V1 繞過必要 router | **LOW** | **HIGH** | Gate H evidence-decision 與 implementation verdict 分離 | V-12 三態 state machine | REQUIRED_BUT_NOT_ACCEPTED，阻擋 V1 | Gate H/V1 | B.3 decision + router verify verdict |
| **R-27** | **ADB `-P` auto-start 使死 lane 偽裝成活 lane**（V-7R 新增） | `adb -P <port>` 在該 port 無 server 時自動拉起空 server，回 `daemon started successfully` + 空 device list + exit 0；已中斷的 lane 因此被判為健康，整格測試建立在假前提上 | **HIGH** | **HIGH** | preflight 斷言 SERIAL 逐字出現（V-23） | EXACT_COMMANDS 固定 `adb -P 5038`；preflight 第 5 項改為 SERIAL 斷言而非 exit code | INFRA_BLOCKED，attempt NOT CONSUMED，不建立 attempt 目錄 | 任何 device packet | `adb -P 5038 devices` 原始輸出存入 evidence |
| **R-28** | **tooling provenance 單點失效**（P003 新增） | `TOOLING_COMMIT 2a14ab2` 不在任何 remote branch 上，僅存在於本機未推送 commit；`PRODUCT_SHA b984ded` 已推送。本機或該 worktree 遺失即無法重現 R8 evidence 的 tooling 端 | **MED** | **HIGH** | `git branch -r --contains 2a14ab2` 為空 | 推送 tooling 分支至 fork（對外動作，需使用者決定） | 既有 evidence 不失效，但 V1-Core 驗收第 19 項 complete provenance 無法成立 | R8 全線 · P2 closure | P003 verdict.txt |
| **R-29** | **EPHEMERAL 值被當常數比對**（P008 實測新增） | §22.5 把 Stable PID `20146` 寫成 precheck 比對值，與 SERIAL 同類。2026-09-21 實測本機 Stable `:1` 健康但 PID 為 8430，照原文必得 false BLOCKED，浪費 grant | **HIGH** | **MED** | precheck 改為 runtime 探索 + cmdline 逐字比對 | 所有 EPHEMERAL 值（SERIAL / Stable PID / endpoint）一律 runtime 探索，snapshot 僅供回報 | INFRA_BLOCKED，attempt NOT CONSUMED | 任何 device packet | stable-before.txt 記錄實際探索值 |
| **R-30** | **STABLE_AFTER 晚於 judge（六代回歸）** | 自 `5a782f6` 起 runner 於 CLEANUP 才寫 stable-after.json，judge 的 `check_stable()` 結構上讀不到 → 每一格必然 `R8_INVALID STABLE_EVIDENCE_MISSING`。attempt-09 是第一個乾淨到能暴露它的 run | **CLOSED** | — | attempt-09 evidence | runner v4 恢復 `65938a4` 順序（after 在 judge 之前，cleanup 另存 stable-post-cleanup.json）| 已修；attempt-09 仍凍結 INVALID | R8 全十格 | `planning-v2/r8-c1-attempt-09-rca/` |
| **R-31** | **judge 與 fixture 對 cell 定義不一致** | `judge_c1` 要求的觀測向量只有 `cell_c4` 會產生；`cell_c1` 永遠不會 emit。重跑無法解決，且此不一致被 R-30 遮蔽了六代八次 attempt | **HIGH** | **HIGH** | v4 離線診斷（未消耗 attempt）| 需 Astra/Sol 在「放寬 judge_c1」與「擴充 cell_c1」之間擇一，兩者都動 frozen contract | DESIGN_REQUIRED，不得以再跑一次 attempt 代替決策 | R8-C1；其餘各格需同樣對照 | `planning-v2/r8-c1-second-blocker/finding.md` |

---

## 18. CARRY-FORWARD MATRIX

### 18.1 硬規則

```
CF-01  tooling-only commit 永遠不當 product SHA，也不產生 carry-forward 條目
CF-02  每條需 11 個欄位齊全；缺欄 → 條目 REJECTED，該 gate 結果不得 carry forward
CF-03  unaffected_gates 必須以 symbol-level delta 證成，不得以「主題不相關」證成
CF-04  fresh_requal=false 需明確 review_decision（載明批准者與理由）
CF-05  條目只能在 diff 存在後撰寫，不存在預先授權的 carry-forward
CF-06  任一 gate 若既不在 affected 也不在 unaffected → 條目不完整
```

### 18.2 欄位

```
old_sha · new_sha · files · symbols · semantic_delta
affected_gates · unaffected_gates · reason · evidence · fresh_requal · review_decision
```

### 18.3 gate universe（31 項）

```
R0 R1 R2 R3 R4 R5 R6 R7
R8-C1 R8-C2 R8-C3-window R8-C3-disconnect R8-C4 R8-C5-full R8-C5-overflow R8-D R8-P1 R8-P2
R9-WARM R9-COLD R9-RESET R9-F1 R9-F2
R10-WARM R10-COLD
P2-CLOSURE BOUNDED-XFCE P2-B3 PRODUCTION-GATE-A GATE-H GATE-W
```

### 18.4 current binding

```
product_sha    = b984dedcac731b77ca4cf8899f8a78b7848ad083
tooling_commit = 2a14ab2f7a5d81e7cd72d5308f5865b81b22881f   （僅供辨識，非 carry-forward 主體）
entries        = []   （尚無任何 carry-forward 條目）
```

### 18.5 待決事項

| ID | 主題 | 問題 | blocking | owner | 狀態 |
|---|---|---|---|---|---|
| CF-PENDING-001 | R7 PASS 13/13 取得於 `a4c8177f…` | R7 是否可 carry forward 到 `b984ded…`，或部分 cell 需重綁？ | P2-CLOSURE | ASTRA | **OPEN**（需 touched-symbol diff，GAP-4） |
| CF-PENDING-002 | R0–R6 取得於 pre-b984ded lineage | 哪些在 symbol 層不受影響？ | P2-CLOSURE | ASTRA | **OPEN**（同 GAP-4） |

---

## 19. FAILURE / REPAIR PIPELINE

### 19.1 決策樹（依序問，第一個 YES 即定案）

```
Q1  是否缺少 architecture decision 才能繼續？              → DESIGN_REQUIRED
Q2  是否為 ADB/screen/network/host/tool 不可用？            → INFRA_BLOCKED
Q3  是否為開始前的 dependency 不成立
    （artifact 不符 / hash 不符 / X3 殘留 / 無 grant）？     → BLOCKED
Q4  evidence 是否不足以形成可信判斷
    （duplicate / END 異常 / post-END / 缺 stable 記錄
     / 流合併計數 / judge 未被允許下判）？                  → INVALID
Q5  構造是否根本沒成立（該撞的沒撞上）？                    → INVALID_CONSTRUCTION（D 格 / F1 / F2）
Q6  構造與證據皆可信，但 product predicate 為假？            → VALID_FAIL
Q7  以上皆否，且全部 PASS 條件成立？                        → PASS
```

**最常見的兩個誤判，必須背下來：**
```
把 INVALID 報成 VALID_FAIL   → 會誣賴 product 有 bug（attempt-08 若被誤判即是此類）
把 VALID_FAIL 報成 INVALID   → 會掩蓋真實 product defect
```
**查驗新增的第三個（R-23）：**
```
把 UNRESOLVED 報成 VALID_FAIL → 把「我們還沒確認契約順序」誤當成「product 錯了」
                                 遇 teardown 相對順序爭議 → DESIGN_REQUIRED，不是 FAIL
```

### 19.2 修復管線（任何非 PASS 一律適用）

```
1. freeze          證據凍結，不得修改、不得補跑
2. STOP            本輪結束

若需要修：
3. RCA → 4. root cause proof → 5. minimum repair → 6. host/static 驗證
→ 7. new tooling or product SHA
→ 8. CI（僅 product 變更）→ 9. artifact（僅 product 變更）→ 10. install（僅 product 變更）
→ 11. explicit new runtime grant → 12. fresh attempt（若上一個已消耗）
```
**鐵則：** 禁止同輪修完直接重跑。修復與驗證必須跨輪，且需要新的 grant。

### 19.3 非 PASS 報告模板

```
PACKET_ID / GRANT_REFERENCE / CLASSIFIER / 決策樹命中點（Q1..Q7）
失敗的確切 predicate 或缺失的確切 dependency
ATTEMPT_CONSUMED : true|false（附理由）
EVIDENCE_PATH / HASH_MANIFEST
STABLE before/after / X3 residue before/after
凍結狀態 : 已 freeze / 未 freeze（未 freeze 必須說明）
下一步   : 'FREEZE_AND_STOP' 或一個具體 packet id
需要新 grant : yes|no
```
**報告中不得出現：** 建議重跑、建議放寬判準、建議延長 timeout、建議改用其他 signal、「應該只是偶發」。

---

## 20. EXECUTOR PACKET SCHEMA（69 欄）

每個 future packet 必須包含全部 69 欄。缺欄 → packet REJECTED，不得預設值。

```
PACKET_ID · TITLE · STAGE · OWNER_MODEL · CURRENT_AUTHORITY · ENTRY_STATE · DEPENDENCIES
EXACT_INPUT_SHA · PRODUCT_SHA · TOOLING_SHA
FILES_TO_READ · FILES_NOT_TO_USE_AS_CURRENT
SOURCE_FILES · SOURCE_SYMBOLS · CALL_PATH · THREAD_OWNERSHIP · RESOURCE_OWNERSHIP
FIXTURE · FIXTURE_HASH · RUNNER · RUNNER_HASH · JUDGE · JUDGE_HASH
COLLECTOR · COLLECTOR_HASH · SPEC · SPEC_HASH
ADB_PRECHECK · SCREEN_PRECHECK · STABLE_PRECHECK · X3_PRECHECK · ARTIFACT_PRECHECK
ENV_ALLOWLIST · ENV_DENYLIST · ALLOWED_MUTATIONS · FORBIDDEN_MUTATIONS
EXACT_COMMANDS · EXPECTED_RC · EXPECTED_TRACE · LEGAL_ALTERNATIVES · FORBIDDEN_TRACE
COUNTERS · GAUGES · RESOURCE_BALANCE
PASS · VALID_FAIL · INVALID · BLOCKED · INFRA_BLOCKED · DESIGN_REQUIRED
ATTEMPT_CONSUMPTION · EVIDENCE_PATH · EVIDENCE_FILES · HASH_MANIFEST
CLEANUP · POST_CLEANUP · STABLE_AFTER
RETRY_POLICY · CI_POLICY · INSTALL_POLICY · CARRY_FORWARD_POLICY
STOP · NEXT_IF_PASS · NEXT_IF_FAIL · NEXT_IF_INVALID · NEXT_IF_BLOCKED · NEXT_AUTH_REQUIRED
LUNA_PROMPT · REPORT_FORMAT
```

### 20.1 驗證規則（23 條，V2.3 新增 V-23）

```
V-01  69 欄全present。缺欄 → REJECTED，不得預設。
V-02  禁止填充語：'same as previous' 'see above' 'unchanged' 'as before' 'N/A' 'TBD' 'etc'
V-03  EXACT_INPUT_SHA 每個 SHA 逐字寫出，不得 cross-reference
V-04  PRODUCT_SHA ≠ TOOLING_SHA，且不得互換；相等 → REJECTED
V-05  exact form 尚未確認存在的指令，狀態必須是 PROPOSED_NOT_YET_EXECUTABLE
V-06  可執行指令中不得出現 literal SERIAL；device packet 必須 serial_binding=RUNTIME_DISCOVERED
V-07  COUNTERS tolerance 永遠為 0；非 0 → REJECTED
V-08  GAUGES 不可觀測用 null；寫 0 → evidence INVALID
V-09  OWNER_MODEL=LUNA 要求 DESIGN_REQUIRED 為空陣列
V-10  device packet 的五個 PRECHECK 欄位皆不得為空
V-11  host-only packet 必須 CI_POLICY=FORBIDDEN, INSTALL_POLICY=FORBIDDEN, attempt_id='NONE'
V-12  RUNNER_HASH 不得等於 f22546b7…62dab7b0（historical runner）
V-13  JUDGE_HASH 不得等於 f021048d…0438e7031（frozen judge）
V-14  每個 R8 packet 的 FORBIDDEN_TRACE 必須含：fake END / moved END / truncated logs /
      post-END semantic / SIGKILL·SIGTERM 替代 / raw+JSONL 合併計數
V-15  STABLE_PRECHECK 與 STABLE_AFTER 各自必須斷言 package / PID / cmdline 三項
V-16  LUNA_PROMPT 必須可獨立閱讀：只讀它就能判定五種 classifier
V-17  NEXT_IF_* 必須指名具體 packet id 或字面值 'FREEZE_AND_STOP'，不得寫 'continue'
V-18  改變 PRODUCT_SHA 的 packet，CARRY_FORWARD_POLICY 必須要求 touched-symbol matrix 條目
V-19  （V2.3 依 V-7R 改寫）device packet 的 EXACT_COMMANDS 必須以字面 `adb -P 5038`
      選擇隔離 server。以 ANDROID_ADB_SERVER_PORT 或 adb -L 選擇 server → REJECTED。
      理由為 provenance（前者不出現在 command trace、後者語意為 server listen spec），
      非功能缺陷——三者在本機 adb 35.0.2 上皆可正確到達目標 port
V-20  （查驗新增）凡以 Present option 為構造的 packet，必須寫死數值（ASYNC|COPY == 0x3），
      不得以名稱讓 executor 自行組合
V-21  EXPANSION=FULL_EXECUTABLE 時，EXACT_COMMANDS 不得含 PROPOSED_NOT_YET_EXECUTABLE；若仍有任何未綁 command，只能標 FULL_SPEC_EXECUTION_BIND_PENDING
V-22  V2-R8-C1-09 的 hard dependencies 必須同時含 V2-P007=SOURCE_BOUND 與 V2-P008=INTERFACE_BOUND；缺任一 → BLOCKED before grant
V-23  （V2.3 新增，由 V-7R 導出）任何以 adb 判定 device 可達性的 packet，其 preflight 必須
      斷言探索到的 SERIAL 逐字出現在 `adb -P 5038 devices` 輸出中。僅以 exit code 或
      「指令成功」作為 lane 存活證據 → REJECTED（`-P` 會自動拉起空 server 並回 exit 0）
```

---

## 21. PACKET INVENTORY

圖例：`DEV` 需裝置 · `CI` 需 CI · `INS` 需 install · `GRANT` 需新 grant · `ATT` 消耗 attempt
`EXPANSION`：`FULL_EXECUTABLE`（69 欄 + exact interface 全綁，可施工）/ `FULL_SPEC_EXECUTION_BIND_PENDING`（規格完整但不可施工）/
`INVENTORY`（已定位，**不得施工**）/ `DESIGN_REQUIRED`（Astra/Sol）

### 21.1 Host-only 前置

| ID | TITLE | OWNER | DEV | CI | INS | GRANT | ATT | EXPANSION |
|---|---|---|---|---|---|---|---|---|
| `V2-P001-PR10-SCOPE-AUDIT` | PR #10 scope 九問稽核 | LUNA | – | – | – | – | – | **RESOLVED_IN_V2.2** |
| `V2-P002-PR7-PACKET-EXTRACTION` | PR #7 38 packets 逐項分類 | LUNA | – | – | – | – | – | **RESOLVED_IN_V2.2** |
| `V2-P003-TOOLING-HASH-REVERIFY` | 九個 tooling hash 重驗 | LUNA | – | – | – | – | – | INVENTORY |
| `V2-P004-EVIDENCE-INDEX-BUILD` | attempt 01-08 evidence 索引/manifest 整理 | LUNA | – | – | – | – | – | INVENTORY（classifier gap 已關） |
| `V2-P005-STABLE-BASELINE-READONLY` | Stable identity 唯讀基準 | LUNA | ✔ | – | – | ✔ | – | INVENTORY |
| `V2-P006-NEGATIVE-VECTOR-BIND` | 53 vectors → 十格 FORBIDDEN_TRACE | ASTRA | – | – | – | – | – | INVENTORY |
| **`V2-P007-TERMINAL-CONTRACT-SOURCE-BIND`** | **綁 current-product terminal sequence / ClearWorkQueue 真實位置** | **ASTRA** | – | – | – | – | – | **HARD_BEFORE_C1** |
| **`V2-P008-C1-EXECUTION-INTERFACE-BIND`** | **綁 runner/collector/judge exact CLI**（ADB5038 client form 已由 V-7R 關閉） | **ASTRA/LUNA host-readonly** | – | – | – | – | – | **HARD_BEFORE_C1** |

### 21.2 R8

| ID | TITLE | OWNER | DEV | GRANT | ATT | EXPANSION |
|---|---|---|---|---|---|---|
| **`V2-R8-C1-09`** | **R8-C1 attempt-09 clean pair lifecycle + clean terminate** | LUNA | ✔ | ✔ | ✔ | **FULL_SPEC_EXECUTION_BIND_PENDING** |
| `V2-R8-C2-SRC-TRACE` | Class-B orchestration 是否足以構造 CLIENT_HOLD | ASTRA | – | – | – | INVENTORY |
| `V2-R8-C2-01` | retained resource + CLIENT_HOLD + terminate | LUNA | ✔ | ✔ | ✔ | INVENTORY |
| `V2-R8-C3W-01` | Present 0x3 → 立即 DestroyWindow | LUNA | ✔ | ✔ | ✔ | INVENTORY |
| `V2-R8-C3D-01` | Present client disconnect + same-generation survivor | LUNA | ✔ | ✔ | ✔ | INVENTORY |
| `V2-R8-C4-01` | REGISTER_BUFFER only → free | LUNA | ✔ | ✔ | ✔ | INVENTORY |
| `V2-R8-C5F-01` | capacity fill（phase 0 = baseline occupancy） | LUNA | ✔ | ✔ | ✔ | INVENTORY |
| `V2-R8-C5O-01` | overflow refusal pre-lease + 釋放一格後恢復 | LUNA | ✔ | ✔ | ✔ | INVENTORY |
| `V2-R8-D-SRC-TRACE` | 找出 deterministic overlap 的 exact schedule seam | ASTRA | – | – | – | DESIGN_REQUIRED |
| `V2-R8-D-HARNESS-DESIGN` | 依 seam 設計可重現 overlap 構造 | ASTRA | – | – | – | DESIGN_REQUIRED |
| `V2-R8-D-01` | retirement × Present completion deferred path | LUNA | ✔ | ✔ | ✔ | INVENTORY |
| `V2-R8-P1-01` | destroy-while-gpu-owned, enum14, X side | LUNA | ✔ | ✔ | ✔ | INVENTORY |
| `V2-R8-P2-01` | close-while-lease, enum15 | LUNA | ✔ | ✔ | ✔ | INVENTORY |
| `V2-R8-AGG` | R8 10/10 aggregate 重驗 12 項 | ASTRA | – | – | – | INVENTORY |

### 21.3 R9 / R10 / Closure / Workload / Gate

| 群組 | Packets | 數量 | EXPANSION |
|---|---|---|---|
| R9 | DESIGN · FIXTURE · JUDGE · HOST-VERIFY · PRODUCT-SUPPORT · CI · INSTALL · WARM-1/2/3 · COLD-1/2/3 · RESET · F1 · F2 · AGG | 17 | DESIGN_REQUIRED（1,5）/ 其餘 INVENTORY |
| R10 | DESIGN · PROBE-INVENTORY · HOST-VERIFY · WARM-R1..R5 · COLD-R1..R5 · AGG | 14 | DESIGN_REQUIRED（1）/ 其餘 INVENTORY |
| P2 closure | CLOSURE-AUDIT · CARRY-FORWARD-REVIEW | 2 | INVENTORY / DESIGN_REQUIRED |
| XFCE | DESIGN-FREEZE · BASELINE-RUN · METRICS-AUDIT | 3 | DESIGN_REQUIRED（1）/ 其餘 INVENTORY |
| B.3 | MATRIX-BIND · TELEMETRY-VERIFY · RUN-SERIES · ANALYSIS | 4 | INVENTORY |
| Gate A | GAP-INVENTORY · RCA-`<n>` · PATCH-`<n>` · CI-`<n>` · INSTALL-`<n>` · REQUAL-`<n>` · CLOSE | 7+ | INVENTORY / CLOSE=DESIGN_REQUIRED |
| Gate H | EVIDENCE-ASSEMBLY · MODEL-DECISION · VERIFY | 3 | MODEL-DECISION=DESIGN_REQUIRED |
| Gate W | DESIGN-FREEZE · RUN · ACCEPT | 3 | FREEZE/ACCEPT=DESIGN_REQUIRED |
| V1 | ACCEPTANCE-AUDIT · RELEASE-DECISION | 2 | RELEASE=DESIGN_REQUIRED（Sol） |

**合計約 76 個 packet。当前 `FULL_EXECUTABLE = 0`；`V2-R8-C1-09` 為 `FULL_SPEC_EXECUTION_BIND_PENDING`。**

### 21.4 展開佇列（下一輪 planning 的順序）

```
1. V2-P007                              HARD：source-bind terminal sequence
2. V2-P008                              HARD：bind ADB/runner/collector/judge exact interface
3. V2-P003                              tooling hash reverify（soft，但 FAIL 會 block 全 R8）
4. V2-P006                              負向向量綁定，讓 FORBIDDEN_TRACE 脫離 PARTIAL
5. V2-R8-C2-SRC-TRACE                   C2 可執行的前提
6. V2-R8-C2-01                          C1 PASS 後第一個需要的 FULL_EXECUTABLE packet
7. V2-R8-D-SRC-TRACE → D-HARNESS-DESIGN 最深的 DESIGN_REQUIRED，越早開始越好
8. C3W / C3D / C4 / C5F / C5O           語意已定稿，展開成本低
9. D-01 / P1-01 / P2-01 / R8-AGG
10. R9-DESIGN                            必須先 freeze，才能展開 R9 其餘 packet
```
**不要預先展開 R9/R10 的 runtime packet。** 它們的綁定會隨 R8 結果與可能的新 PRODUCT_SHA 失效，
提前展開只會製造要作廢的文件。

---

## 22. FULL-SPEC PACKET DRAFT — `V2-R8-C1-09`

```
STATUS : FULL_SPEC_EXECUTION_BIND_PENDING / NOT_READY_FOR_GRANT / NOT_AUTHORIZED / NOT_STARTED
BASE   : PR #10 進度（b984ded 已安裝、ADB lane 已 restored、attempt-09 未開始未消耗）
```

### 22.1 身分與授權

```
PACKET_ID    V2-R8-C1-09
TITLE        R8-C1 attempt-09 — clean pair lifecycle and clean test-control terminate on b984ded
STAGE        R8
OWNER_MODEL  LUNA
```
`CURRENT_AUTHORITY`
```
snapshot              waydefu/GPU PR #10, HEAD 697e16f3dab21946d77860b82c7e4ceeb8fe761e,
                      BASE 06eff51bc69f2685083746b68f55786e30a854da
authority_ranks_used  A, B, C, D, E, F
must_not_use          PR #7 packets（rank H, scaffold only）
                      PR #9 attempt-05 敘述（evidence 不可變，但非 current state）
                      任何 pre-2a14ab2 tooling manifest
                      PR #10 scope audit 只證明 docs/evidence 範圍；不得把 scope clean 當 runtime/product qualification
                      上游 xserver 原始碼（非本 product 的 rank-C，僅供 V2-P007 對照）
```
`ENTRY_STATE`
```
R8 = 0/10。R8-C1 attempt-09 NOT STARTED。runtime-b984ded/r8-c1/attempt-09/ ABSENT。
attempt-09-preflight 凍結為 INFRA_BLOCKED/ADB_CONNECT_FAILED，runner 未 invoke、無 cell dir
  → attempt-09 NOT CONSUMED。
attempt-09-adb-restore 凍結為 ADB_LANE_RESTORED。
Product b984ded 已安裝並 re-proven。Stable com.termux.x11 :1 PID 20146 未被觸碰。
執行前必須存在一份 scope 為「R8-C1 attempt-09, single cell」的已簽 runtime grant。
```
`DEPENDENCIES`
```
V2-P003-TOOLING-HASH-REVERIFY          required_result = NONE（軟前置；若執行後 FAIL 則 block）
V2-P001-PR10-SCOPE-AUDIT                 required_result = RESOLVED_IN_V2.2 / SCOPE_CLEAN_DOCS_EVIDENCE
V2-P007-TERMINAL-CONTRACT-SOURCE-BIND    required_result = SOURCE_BOUND（HARD；未完成不得 grant）
V2-P008-C1-EXECUTION-INTERFACE-BIND      required_result = INTERFACE_BOUND（HARD；未完成不得 grant）
```
`NEXT_AUTH_REQUIRED`
```
required = true
scope    = 必須有一份明確寫「R8-C1 attempt-09, single cell」的已簽 runtime grant；
           C2 另需一份獨立 grant。
```

### 22.2 綁定（`EXACT_INPUT_SHA` 全文）

```
PRODUCT_SHA                          b984dedcac731b77ca4cf8899f8a78b7848ad083
TOOLING_COMMIT                       2a14ab2f7a5d81e7cd72d5308f5865b81b22881f
PR10_HEAD                            697e16f3dab21946d77860b82c7e4ceeb8fe761e
PR10_BASE                            06eff51bc69f2685083746b68f55786e30a854da
CI_RUN                               35347497216
APK_SHA256                           0d06de68025ca41d91e316d55f6f77ba9d5b3ba1a90b6a2bfacb65add0d398d3
BUILD_ID                             3658dd1f8047bfbb9d4671b269305313adaf1aa7
SIGNER                               b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1
VERSION                              1.03.01-b984ded-18.09.26
PACKAGE                              com.waydefu.x11gpu
EXPERIMENTAL_DISPLAY                 :3
RUNNER_SHA256                        53e0c6b8ac613eab7dcce970438e7adc071bddcde4d7e1e202763bfe62de44e5
ORCHESTRATION_SHA256                 27af4a6253bcc021f3da2494b99045c754fb27f2b815b23cbbe1e0744760a536
JUDGE_V2_SHA256                      baceae096fda8ffdb373267bc9c1e80c3e3e2985df278de3295a1bd8b73380a2
COLLECTOR_SHA256                     e6df519a75c872c8a56fac00146585853eec7f17a3f424e70e5d4736340666c8
SPEC_SHA256                          ff22a1521d23a8954b0b4f3a603dbb19af98b3e8b3727342caf5e107b639b3ba
OBS_STREAM_SHA256                    72d7517737a009a588f0c25d685db252a32081c4a9e750adaf4f0f2932eb5041
FIXTURE_ELF_SHA256                   ad93f2ba6adcaae53dbb750b9bdc928d32b1932c3e86ea1b4d2121a5c96f12de
FIXTURE_SOURCE_SHA256                f6f6a74054bbdc3668567887327bd5c405d666967088a7151fa2360ec13bf941
FORBIDDEN_HISTORICAL_RUNNER_SHA256   f22546b7f42aa9f45c4bdee5e7ce675efe6b1fae4e9709e15696e59262dab7b0
FORBIDDEN_FROZEN_JUDGE_SHA256        f021048da3c1b729c6f9bf560eba52609b2f980336dd4fab77ad1700438c0e31
SERIAL_SNAPSHOT_FOR_COMPARISON_ONLY  10.191.48.13:46847
FROZEN_FAILED_ENDPOINT               10.191.48.13:45165
STABLE_PID_SNAPSHOT                  20146
ADB_SERVER_PORT                      5038
```

### 22.3 讀 / 不讀

`FILES_TO_READ`（前綴 `evidence/session/gate-a-a1/p2-r8-runtime/`）
```
run-r8-one-cell-b984ded-v2.sh · r8_orchestration_v2.py · judge-r8-v2.py
collect-r8.py · lifecycle-cell-spec.json · r8_obs_stream.py
```
`FILES_NOT_TO_USE_AS_CURRENT`
```
run-r8-one-cell-b984ded.sh        historical runner，綁 frozen judge-r8.py
judge-r8.py                       frozen historical judge；判決僅對 attempt 01-08 有效
planning/（PR #7 packets）         rank H scaffold；綁定已失效
runtime-b984ded/r8-c1/attempt-0{1..8}/   frozen history；永不作為 current state，永不重判
PR #9 attempt-05 敘述              current-state-wise 已 superseded；evidence 本身不可變
```

### 22.4 Source / thread / resource ownership

```
SOURCE_FILES   lorie DDX test-control handler · lorie DDX screen teardown path
               · renderer observation emitter
SOURCE_SYMBOLS ProcLorieR8Terminate · GiveUp · DE_TERMINATE · lorieCloseScreen · gateACloseGeneration
               · pinned xserver DIX teardown symbols（由 V2-P007 精確綁定） · ddxGiveUp · lorieR8ObsEnd
CALL_PATH      LORIE-R8-TEST opcode 3 → ProcLorieR8Terminate → reply → GiveUp(0)
               → DE_TERMINATE → [TERMINAL_SEQUENCE_FROM_V2_P007]
               → ddxGiveUp → lorieR8ObsEnd("x") → process exit
               目前不得在 P007 前把 ClearWorkQueue 硬編成必經 event。
```
`THREAD_OWNERSHIP`
> X main thread 擁有 CALL_PATH 的完整 opcode-3 dispatch 與 teardown 鏈。
> lorie DDX **沒有** X input thread，因此任何步驟都不得預期出現在 input thread 上。
> renderer 側的 destruction 與 renderer END 在 renderer 自己的 thread 上 emit。
> 任何 observation 宣稱某 teardown 步驟發生在 X main thread 以外 → 是紅旗，必須回報，不得抹平。

`RESOURCE_OWNERSHIP`
> pair A 的 buffer 在 free 前由 X registry 擁有；free 後由 renderer 側 destruction 反向解除，
> ACK/removal 完成交接。pair B 必須是新的 object identity，綁 current generation / tuple，且不能承接 pair A 尚未退休的 ownership。
> 完整 retirement 後 allocator 若合法重配相同 numeric slot / address，必須用新的 object identity 證明；數值相同本身不構成 FAIL。
> terminate 時，每個 registry entry 與 renderer entry 都必須在 ddxGiveUp 前退休；
> lease 狀態在 teardown boundary 必須為 NONE。

### 22.5 Preflight（八項，fresh，缺一不可）

```
ADB_PRECHECK
  1  mdns resolve 裝置（不得重用快取 endpoint）
  2  在隔離 server（port 5038）上 adb connect；絕不觸碰 5037
  3  runtime 探索 SERIAL；snapshot 10.191.48.13:46847 僅供比對與回報
  4  絕不嘗試 frozen failed endpoint 10.191.48.13:45165
  5  adb -P 5038 devices 的輸出中，本次探索到的 SERIAL 必須逐字出現
     （V-23 / R-27：-P 會在該 port 無 server 時自動拉起空 server 並回 exit 0，
      只驗 exit code 會把已死的 lane 判成存活）
  6  adb -P 5038 -s <SERIAL> shell getprop ro.product.device == myron

SCREEN_PRECHECK    screen Awake · Display ON · 無 keyguard 阻擋 :3

STABLE_PRECHECK    com.termux.x11 present 且未被 force-stop
                   PID：**runtime 重新探索**，逐字寫入 stable-before.txt。
                     20146 是 EPHEMERAL snapshot，與 SERIAL 同類，**不得 hardcode 比對**。
                     2026-09-21 實測本機為 8430（機器已重開），若照原文比對必得 false BLOCKED。
                   cmdline == 'termux-x11 com.termux.x11 :1 -legacy-drawing' 逐字相符
                     ← 這一項才是 Stable 的不變量，PID 不是
                   STABLE_AFTER 必須與 STABLE_PRECHECK 探索到的同一個 PID 比對（V-15）

X3_PRECHECK        :3 無 X3 process · 無 X socket · 無 lock file
                   **必須用 runner `x3pid()` 的形式**（逐一比對 /proc/*/cmdline 前綴）。
                   禁用裸 `pgrep -f 'termux-x11gpu com.waydefu.x11gpu :3'`：
                   該 pattern 會出現在操作者自己的 shell 命令列而自我匹配，
                   2026-09-21 實測誤報過一次殘留 → false BLOCK。

ARTIFACT_PRECHECK  com.waydefu.x11gpu 已安裝
                   version == 1.03.01-b984ded-18.09.26
                   APK SHA256 == 0d06de68…d398d3
                   BUILD ID   == 3658dd1f8047bfbb9d4671b269305313adaf1aa7
                   SIGNER     == b6da0148…48ee5e1
                   PR #10 scope audit = SCOPE_CLEAN_DOCS_EVIDENCE（V2.2 已關）。
                     這只證明 PR scope；product 綁定仍必須來自已安裝 artifact readback（rank A/C/F）。
```

### 22.6 環境與變更權限（含 V-7R 修正）

```
ENV_ALLOWLIST      （不含任何 ADB server 選擇變數；V-7R 後一律用字面 adb -P 5038）
                   DISPLAY=:3（僅實驗用）
                   runner 自身設定的變數
                   ADB_MDNS_AUTO_CONNECT / ADB_MDNS_OPENSCREEN（僅 mdns 探索階段）

ENV_DENYLIST       ANDROID_ADB_SERVER_PORT（任何值，含 5037 與 5038）
                   ANDROID_NO_USE_FWMARK_CLIENT / HOME 覆寫（僅 pair/connect 需要，見 V-7R 結論四）
                   DISPLAY=:1
                   任何非 runner 設定的 TERMUX_X11_GATEA_* 覆寫
                   任何 timeout 覆寫
                   任何 judge 選擇覆寫
                   ADB_TRACE（僅診斷用；若開啟，其輸出不得進入 judge 輸入）

ALLOWED_MUTATIONS  由 runner 建立 evidence/.../runtime-b984ded/r8-c1/attempt-09/
                   在該目錄下寫入新的 evidence 檔
                   依 runner 定義 push R8 fixture ELF

FORBIDDEN_MUTATIONS
                   對 com.termux.x11 / DISPLAY :1 / HDMI 的任何寫入
                   logcat -c · pkill · killall
                   adb install · pm uninstall · pm clear
                   編輯 runner / orchestration / judge / collector / spec / obs stream
                   編輯或刪除任何 attempt-01..08 evidence
                   建立 attempt-10
                   建立 r8-c1/attempt-09 以外的任何 cell 目錄
                   git reset --hard · git push origin · git push --force · gh pr
                   修改任何 timeout
```

### 22.7 EXACT_COMMANDS（ADB lane 已由 V-7R 綁定；runner/collector/judge 仍待 V2-P008）

| # | 狀態 | 指令 | 說明 |
|---|---|---|---|
| 1 | `PROPOSED_NOT_YET_EXECUTABLE` | `<host> mdns resolve` + 在隔離 server 上 `adb connect <discovered-endpoint>` | host helper 名稱本輪未確認 |
| 2 | `EXISTS_EXECUTABLE` | `adb -P 5038 -s "$SERIAL" shell getprop ro.product.device` | **V-7R 實測綁定（2026-09-21）**。不得帶 ANDROID_ADB_SERVER_PORT。執行前必須先通過 preflight 第 5 項 SERIAL 斷言（V-23） |
| 3 | `EXISTS_EXECUTABLE` | `adb -P 5038 -s "$SERIAL" shell dumpsys package com.waydefu.x11gpu` | artifact readback；server 選擇方式與 step 2 同源，已由 V-7R 綁定 |
| 4 | `EXISTS_EXECUTABLE` | `sha256sum run-r8-one-cell-b984ded-v2.sh r8_orchestration_v2.py judge-r8-v2.py collect-r8.py lifecycle-cell-spec.json r8_obs_stream.py` | 任何 device mutation 前的 tooling hash 閘門 |
| 5a | `EXISTS_EXECUTABLE` | `CELL_ID=R8-C1 EVIDENCE=<attempt-09 dir> VALIDATE_ONLY=1 bash run-r8-one-cell-b984ded-v5.sh` | **P008 綁定**：零 device mutation 乾跑，在 SERIAL 檢查與 adb 檢查之前返回，不消耗 attempt。grant 後第一步 |
| 5b | `EXISTS_EXECUTABLE`（**唯一消耗 attempt 的呼叫**） | `CELL_ID=R8-C1 EVIDENCE=<attempt-09 dir> SERIAL="$SERIAL" bash run-r8-one-cell-b984ded-v5.sh` | **P008 綁定**：runner **無任何 flag**，純 env 驅動。`--cell c1 --attempt 09 --serial` 在真實介面不存在。`EVIDENCE` 必須**尚未存在**否則 `R8_BLOCKED evidence_exists`。exit 3=BLOCKED / 2=INVALID / 其餘為 judge rc |
| ~~6~~ | **REMOVED（P008）** | ~~`python3 collect-r8.py …`~~ | runner L329 已內部呼叫 collect-r8.py。操作者另行手動呼叫會重複寫 evidence，屬污染風險 |
| ~~7~~ | **REMOVED（P008）** | ~~`python3 judge-r8-v2.py …`~~ | runner L491 先 `permit-judge`、L502 才呼叫 judge。手動呼叫會繞過 permit gate |
| 8 | `EXISTS_EXECUTABLE` | `sha256sum <attempt-09 dir>/* > <attempt-09 dir>/sha256sums.txt` | evidence hash manifest |

`EXPECTED_RC`：全部步驟 `0`。
`serial_binding`：所有涉及裝置的步驟一律 `RUNTIME_DISCOVERED`。

### 22.8 EXPECTED_TRACE / LEGAL_ALTERNATIVES / FORBIDDEN_TRACE

`EXPECTED_TRACE`（25 元素，依序）
```
pair A direct exact success → pair A resource free/destruction → renderer reverse destruction
→ ACK/removal correctness → registry/resource balance → fresh distinct pair B allocated
→ pair B direct exact success → no stale pair A reuse
→ clean test-control terminate initiated (LORIE-R8-TEST opcode 3)
→ server TEST_CONTROL TERMINATE observed → ProcLorieR8Terminate → reply → GiveUp(0)
→ DE_TERMINATE → [TERMINAL_SEQUENCE_FROM_V2_P007] → ddxGiveUp
→ X END exactly once → renderer END exactly once → no semantic observation after END
→ both semantic streams complete → process exit
→ X3 process absent after cleanup → socket/lock absent after cleanup
```

`LEGAL_ALTERNATIVES`
```
1. renderer END 與 X END 的相對順序：只要兩者各恰好一次、且其後皆無 semantic observation
   → 仍 PASS
2. collector/judge 由 runner 內部呼叫而非獨立 step 6/7：只要使用相同 hash、evidence 佈局不變
   → 仍 PASS
3. V2-P007 未完成時：本 packet 不具執行資格，因此不存在「先跑再用 DESIGN_REQUIRED 留白」的合法路徑。
   V2-P007 完成後，terminal sequence 必須逐字綁入 packet；executor 不得自行補/刪 ClearWorkQueue。
```

`FORBIDDEN_TRACE`
```
runner 或 collector 產生的 synthetic END
X END 被移動、重複或缺席 · renderer END 被移動、重複或缺席
END 之後出現任何 semantic observation（POST_END_OBSERVATION）
truncated logs
以 SIGKILL 結束正常完成 · 以 SIGTERM 代替 opcode 3
僅以 dispatchException 最終值相同論證路徑正確（V-2）
-enable product -terminate
raw logcat 與 semantic JSONL 合併後計數
對 semantic JSONL 套用 dedupe
MULTI_BEGIN_x
以 cleanup kill 代替 product clean exit
pair B 接受 pair A 的 stale object / stale tuple / stale generation ownership（單純 numeric slot/address 重配不算）
PARTIAL：PR #8 的 53 host negative vectors 尚未綁入本清單；
        V2-P006 完成前，本清單僅為子集
```

### 22.9 COUNTERS / GAUGES / RESOURCE_BALANCE

```
COUNTERS（tolerance 一律 0）
  x_end                              = 1
  renderer_end                       = 1
  post_end_semantic_observations     = 0
  duplicate_records_in_semantic_jsonl= 0
  multi_begin_x                      = 0
  pair_a_direct_exact_success        = 1
  pair_b_direct_exact_success        = 1
  stale_pair_a_reuse                 = 0
  unexpected_fatal                   = 0
  unexpected_signals                 = 0

GAUGES
  x_registry_entries_at_terminate        = 0
  renderer_registry_entries_at_terminate = 0
  lease_state_at_teardown_boundary       = NONE
  pending_at_teardown_boundary           = 0
  peak_x_rss_bytes                       = null   （不可觀測，禁止填 0）
  peak_x_fd_count                        = null   （不可觀測，禁止填 0）

RESOURCE_BALANCE
  x_registry        registered == unregistered，最終 0
  renderer_registry created == destroyed，最終 0
  ack_removal       每個 removal 恰有一個 ACK
  lease             每個 boundary 與 teardown 皆為 NONE
  pending           teardown 時為 0；ClearWorkQueue 時無 outstanding work
```

### 22.10 五種 classifier 的判定

```
PASS
  judge-r8-v2.py 判 PASS，且
  EXPECTED_TRACE 每個元素皆出現且依 `V2-P007` source-bound terminal sequence，且
  COUNTERS 全部等於 expected（tolerance 0），且
  RESOURCE_BALANCE 全部成立，且
  STABLE identity 三元組 before == after，且
  cleanup 後無 X3 process / socket / lock，且
  evidence 完整且 sha256sums.txt 已產出

VALID_FAIL
  構造可信、evidence 完整，但某個 product predicate 為假。
  例：pair B 重用 stale pair A 資源；teardown 時 registry balance 非零；
      teardown 在 ddxGiveUp 前中止；ACK/removal 不匹配；boundary 上 lease 非 NONE。
  需要 cleanup kill 才能結束 product 的 run，最好也只是 VALID_FAIL，永遠不是 PASS。

INVALID
  semantic JSONL 內有重複紀錄；END 缺失/移位/重複/合成；任何 post-END semantic observation；
  raw 與 semantic 合併後計數；對 semantic 輸入套用 dedupe；
  缺 STABLE before 或 after；執行中才發現 hash 不符；judge 未被允許下判。

BLOCKED
  artifact readback 在 version / APK sha256 / build id / signer 任一不符；
  開始前 tooling hash 不符；開始前已有 X3 residue；
  runner 介面與本 packet 的 flag 不符；
  沒有 scope 為「R8-C1 attempt-09, single cell」的已簽 runtime grant。

INFRA_BLOCKED
  mdns resolve 失敗；在 5038 上 adb connect 失敗；device 非 myron；
  screen 非 Awake / display off；network 或 host tool 不可用。

DESIGN_REQUIRED
  僅可在 host planning/bind 階段使用。若 V2-P007 或 V2-P008 尚未完成，C1 應在 runner invoke 前分類 BLOCKED，
  不得消耗 attempt-09 再用 DESIGN_REQUIRED 收尾。
```

### 22.11 Attempt / evidence / cleanup / policy

```
ATTEMPT_CONSUMPTION
  consumed_when      runtime-b984ded/r8-c1/attempt-09/ 已建立
                     OR run-r8-one-cell-b984ded-v2.sh 已以 cell c1 被 invoke
  not_consumed_when  preflight 在上述兩者之前失敗，因此無目錄且 runner 從未被 invoke
  attempt_id         attempt-09
  renumber_on_not_consumed = false     ← 永不跳號

EVIDENCE_PATH   evidence/session/gate-a-a1/p2-r8-runtime/runtime-b984ded/r8-c1/attempt-09/
EVIDENCE_FILES  x-observations.jsonl · renderer-observations.jsonl
                runner.stdout.log · runner.stderr.log
                collector-output.json · judge-verdict.json · preflight.json
                stable-before.txt · stable-after.txt
                x3-residue-before.txt · x3-residue-after.txt · sha256sums.txt
HASH_MANIFEST   <EVIDENCE_PATH>/sha256sums.txt

CLEANUP         只做 runner 自身定義的 cleanup。
                若 product 已乾淨退出，就沒有東西要 kill。
                若需要 kill，該事實本身是 finding，必須記錄，永遠不得被抹平成 PASS。
POST_CLEANUP    驗證 :3 無 X3 process / 無 socket / 無 lock；寫 x3-residue-after.txt
STABLE_AFTER    com.termux.x11 仍在且未被 force-stop
                PID 與 stable-before.txt 相同
                cmdline 與 'termux-x11 com.termux.x11 :1 -legacy-drawing' 逐字相同

RETRY_POLICY          RETRY_ONLY_IF_NOT_CONSUMED
CI_POLICY             FORBIDDEN
INSTALL_POLICY        FORBIDDEN
CARRY_FORWARD_POLICY  本 packet 不改變 PRODUCT_SHA，故不產生 touched-symbol matrix 條目。
                      若日後修復改變 PRODUCT_SHA，C1 必須在新 grant 下以新的 attempt 編號重跑，
                      且 CARRY-FORWARD 條目為強制。

STOP              judge verdict 一寫出即停，無論 verdict 為何
                  任何 verdict 下都不得進入 C2
                  不得 retry，不得建立 attempt-10
                  任何非 PASS：凍結 evidence 並停止；修復在另一輪進行
NEXT_IF_PASS      V2-R8-C2-01（需 V2-R8-C2-SRC-TRACE PASS 且需新 grant）
NEXT_IF_FAIL      FREEZE_AND_STOP
NEXT_IF_INVALID   FREEZE_AND_STOP
NEXT_IF_BLOCKED   FREEZE_AND_STOP
```

### 22.12 `LUNA_PROMPT`

```text
CURRENT AUTHORITY
  Snapshot: waydefu/GPU PR #10 (HEAD 697e16f3dab21946d77860b82c7e4ceeb8fe761e).
  PR #10 records exactly two things: b984ded is installed and re-proven, and the
  R8-C1 ADB lane was restored. It records no cell passing. R8 is 0/10.
  Installed product: com.waydefu.x11gpu 1.03.01-b984ded-18.09.26,
    PRODUCT_SHA b984dedcac731b77ca4cf8899f8a78b7848ad083, CI run 35347497216,
    APK SHA256 0d06de68025ca41d91e316d55f6f77ba9d5b3ba1a90b6a2bfacb65add0d398d3,
    BUILD ID 3658dd1f8047bfbb9d4671b269305313adaf1aa7,
    SIGNER b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1.
  Tooling: TOOLING_COMMIT 2a14ab2f7a5d81e7cd72d5308f5865b81b22881f.
  Cell: R8-C1, attempt-09. attempt-09 has NOT been started and is NOT consumed.
  This packet is NOT self-authorizing. Execute only if a signed RUNTIME GRANT for
  'R8-C1 attempt-09, single cell' is present in your instruction.

GOAL
  Produce one complete, judgeable R8-C1 lifecycle cell run on the already-installed
  b984ded artifact, and let judge-r8-v2.py render a verdict. Nothing else.
  You are not fixing anything. You are not improving anything.

READ EXACTLY
  evidence/session/gate-a-a1/p2-r8-runtime/run-r8-one-cell-b984ded-v2.sh
  evidence/session/gate-a-a1/p2-r8-runtime/r8_orchestration_v2.py
  evidence/session/gate-a-a1/p2-r8-runtime/judge-r8-v2.py
  evidence/session/gate-a-a1/p2-r8-runtime/collect-r8.py
  evidence/session/gate-a-a1/p2-r8-runtime/lifecycle-cell-spec.json
  evidence/session/gate-a-a1/p2-r8-runtime/r8_obs_stream.py

DO NOT READ AS CURRENT AUTHORITY
  run-r8-one-cell-b984ded.sh   (historical runner, binds the frozen judge)
  judge-r8.py                  (frozen historical judge)
  PR #7 packets                (scaffold only)
  any attempt-01..08 evidence  (frozen history, not current state)
  any PDF / roadmap / P0-P12 draft
  upstream X.Org source        (not this product's source; reference only)

PRECHECK  (all must pass, in order, fresh - never reuse a cached value)
  0. HARD HOST BINDINGS: V2-P007 must be SOURCE_BOUND and V2-P008 must be INTERFACE_BOUND.
     If either is absent, classify BLOCKED BEFORE runner invocation. Do not create attempt-09 directory.
  1. mdns resolve the device; adb connect on the isolated server at port 5038 only.
     Select the server with the literal flag 'adb -P 5038'. Do NOT use
     ANDROID_ADB_SERVER_PORT and do NOT use 'adb -L'. Measured 2026-09-21 on this
     adb 35.0.2: all three reach the intended port, so this is a provenance rule,
     not a functional one - only -P is visible in the command trace and unambiguous
     on review. NEVER touch 5037.
  1b. CRITICAL (R-27): 'adb -P <port>' AUTO-STARTS an empty server when that port has
     none. A dead lane then prints 'daemon started successfully', an empty device
     list, and exits 0 - it looks healthy. You MUST assert that the SERIAL you just
     discovered appears verbatim in 'adb -P 5038 devices'. Exit code alone is NOT
     evidence the lane is up. If the SERIAL is absent: INFRA_BLOCKED, attempt NOT
     CONSUMED, do not create the attempt-09 directory.
  2. Discover SERIAL at runtime. The snapshot value 10.191.48.13:46847 is for
     comparison and reporting ONLY - never hardcode it into a command.
     The endpoint 10.191.48.13:45165 is permanently frozen-failed. Do not try it.
  3. adb -s <SERIAL> shell getprop ro.product.device  ==  myron
  4. Screen Awake and Display ON.
  5. Package readback: com.waydefu.x11gpu present, version 1.03.01-b984ded-18.09.26,
     APK SHA256 and signer match the values in CURRENT AUTHORITY above.
     Note: PR #10's file scope is unverified. That is a WARNING, not a blocker -
     your product binding comes from this readback, not from PR #10's file list.
  6. STABLE identity BEFORE: com.termux.x11 present, PID 20146,
     cmdline exactly 'termux-x11 com.termux.x11 :1 -legacy-drawing'.
     Note: exiting Termux:X11 from its notification does NOT kill the process.
     Compare PID and cmdline, not app state.
  7. No :3 residue: no X3 process, no X3 socket, no X3 lock file.
  8. sha256 of runner, orchestration, judge, collector, spec, obs stream and fixture
     match the hashes in this packet exactly.
  If ANY precheck fails: classify INFRA_BLOCKED (for 1-4) or BLOCKED (for 5-8),
  do NOT invoke the runner, do NOT create the attempt-09 directory, STOP.

DO
  Invoke run-r8-one-cell-b984ded-v2.sh for cell C1 exactly once.
  Let the runner create evidence/.../runtime-b984ded/r8-c1/attempt-09/.
  Let collect-r8.py collect. Let judge-r8-v2.py judge.
  Record STABLE identity AFTER. Record :3 residue AFTER.
  Emit sha256sums.txt over every evidence file.

DO NOT
  Do not fake, move, add or truncate any END record.
  Do not concatenate raw logcat with x-observations.jsonl or
    renderer-observations.jsonl and then count. They are separate streams.
  Do not dedupe. A true duplicate inside a semantic JSONL is INVALID.
  Do not use SIGTERM or SIGKILL to end a normal run. Terminate is LORIE-R8-TEST opcode 3.
    SIGTERM reaches the same dispatchException flag through a different entry point -
    identical end state is NOT evidence that the correct path was taken.
  Do not use cleanup kill to substitute for a product clean exit.
  Do not retry. Do not lengthen a timeout. Do not change signal, runner or judge.
  Do not build, install, or dispatch CI.
  Do not touch com.termux.x11, DISPLAY :1, PID 20146, or HDMI - for any reason.
  Do not start C2. Do not create attempt-10.

COMMANDS
  See EXACT_COMMANDS. Steps marked PROPOSED_NOT_YET_EXECUTABLE must have their exact
  form confirmed against the real interface before use; if it differs, classify
  BLOCKED and STOP - do not improvise flags.

EXPECTED TRACE
  pair A direct exact success -> pair A resource free/destruction ->
  renderer reverse destruction -> ACK/removal correct -> registry balance ->
  fresh pair B with new object identity/current tuple -> pair B direct exact success -> no stale pair-A object/tuple/generation reuse ->
  LORIE-R8-TEST opcode 3 -> ProcLorieR8Terminate -> reply -> GiveUp(0) ->
  DE_TERMINATE -> [exact terminal sequence frozen by V2-P007] -> ddxGiveUp ->
  lorieR8ObsEnd("x") -> process exit.
  X END exactly once. renderer END exactly once. No semantic observation after END.

  TERMINAL BINDING: do not execute this packet until V2-P007 has replaced
  [exact terminal sequence frozen by V2-P007] with the current-product sequence.
  ClearWorkQueue is required only if P007 proves it is a terminate-path required element.

PASS
  judge-r8-v2.py verdict PASS, AND every EXPECTED TRACE element present (order as
  above, except the ordering caveat), AND X END == 1 and renderer END == 1 and
  post-END semantic count == 0, AND resource balance zero, AND STABLE identity
  unchanged, AND no X3 process/socket/lock after cleanup.

VALID FAIL
  Construction and evidence are trustworthy and complete, but a product predicate is
  false - e.g. pair B reuses a stale pair A resource, registry balance is non-zero,
  or teardown stops before ddxGiveUp. Report the exact failing predicate.

INVALID
  Duplicate records inside a semantic JSONL; missing/moved/synthetic END; any post-END
  semantic observation; missing STABLE before or after; hash mismatch discovered
  mid-run; raw and semantic streams merged; judge not permitted to render a verdict.

BLOCKED
  Artifact readback mismatch, tooling hash mismatch, X3 residue present before start,
  a runner interface that does not match this packet, or no signed runtime grant.

INFRA BLOCKED
  mdns/adb/connect failure, device not myron, screen not Awake, network or host
  tool unavailable.

DESIGN REQUIRED
  Not a runtime verdict for this packet. Any unresolved architecture/interface dependency must block before runner invocation.

EVIDENCE
  evidence/session/gate-a-a1/p2-r8-runtime/runtime-b984ded/r8-c1/attempt-09/
  must contain: x-observations.jsonl, renderer-observations.jsonl, runner stdout/stderr,
  collector output, judge verdict, preflight record, stable-before.txt, stable-after.txt,
  x3-residue-before.txt, x3-residue-after.txt, sha256sums.txt.

CLEANUP
  Only the cleanup the runner itself defines. If the product has already exited
  cleanly there is nothing to kill. If a kill is needed, that fact is itself a
  finding - record it, and it makes the run VALID FAIL or INVALID, never PASS.

STOP
  Stop after the judge verdict is written, whatever it says.
  Do not proceed to C2 under any verdict. C2 requires its own grant.

REPORT EXACTLY
  1  PACKET_ID
  2  GRANT_REFERENCE
  3  ATTEMPT_ID and ATTEMPT_CONSUMED (true|false) with the reason
  4  SERIAL_DISCOVERED (and whether it matched the snapshot value)
  5  ADB_SERVER_PORT actually used, and how it was selected
  6  ARTIFACT_READBACK (version, APK sha256, build id, signer) - each PASS|MISMATCH
  7  TOOLING_HASHES_VERIFIED - one line per file, PASS|MISMATCH
  8  STABLE_BEFORE / STABLE_AFTER - package, pid, cmdline, and UNCHANGED|CHANGED
  9  X3_RESIDUE_BEFORE / X3_RESIDUE_AFTER - process, socket, lock
  10 TRACE_OBSERVED - ordered list, each element PRESENT|ABSENT, plus the observed
     relative order of CloseScreen / resource teardown / ClearWorkQueue verbatim
  11 COUNTERS - x_end, renderer_end, post_end_semantic, duplicate_records
  12 RESOURCE_BALANCE - registry, renderer registry, lease, pending
  13 JUDGE_VERDICT - verbatim
  14 CLASSIFIER - PASS|VALID_FAIL|INVALID|BLOCKED|INFRA_BLOCKED|DESIGN_REQUIRED
  15 EVIDENCE_PATH and HASH_MANIFEST digest
  16 STATUS_LINE - 'R8 remains N/10. Production Gate A remains BLOCKED.'
  Then stop. Do not recommend a next step. Do not offer to retry.
```

### 22.13 五個最容易被 executor 搞錯的點（V2.2）

```
1. PR #10 scope 已完成 read-only audit，但 scope clean ≠ runtime grant。

2. V2-P007 是 HARD prerequisite。
   terminal sequence 未 source-bind 前，C1 不得執行；不能用「跑了再 DESIGN_REQUIRED」消耗 attempt-09。

3. V2-P008 是 HARD prerequisite。
   ADB5038 client invocation 已由 V-7R 綁定（`adb -P 5038`）；runner flags、collector/judge
   真實介面未綁前，packet 仍只能 FULL_SPEC_EXECUTION_BIND_PENDING。

4. fresh pair B 是 identity 新，不是「數值永遠不能重用」。
   禁止 stale object/tuple/generation ownership；完整 retirement 後合法 allocator numeric reuse 不自動 FAIL。

5. attempt-09 未被消耗。
   renumber_on_not_consumed = false。下一次真正 runtime 仍叫 attempt-09；不得建立 attempt-10。
```

---

## 23. ASTRA / SOL 決策登錄

> 本登錄內的決策**不得委派給 Luna**。Luna 只執行，不決定。

| ID | 決策主題 | Owner | 觸發階段 | 狀態 | 阻擋什麼 |
|---|---|---|---|---|---|
| D-01 | R9 same-process reset scope | ASTRA | `V2-R9-DESIGN` | OPEN | `V2-R9-RESET` 是否存在 |
| D-02 | R9 retained-renderer ownership | ASTRA | `V2-R9-DESIGN` | OPEN | R9 F1 判準 |
| D-03 | R10 observability limitation | ASTRA | `V2-R10-DESIGN` | OPEN | 哪些 metric 為 null |
| D-04 | resource leak disposition | ASTRA | `V2-R10-AGG` | OPEN | R10 accepted 與否 |
| D-05 | carry-forward approval（R0–R7） | ASTRA | `V2-P2-CLOSURE-AUDIT` | OPEN | P2 closure |
| D-06 | production lifecycle redesign 範圍 | ASTRA/SOL | `V2-PGA-GAP-INVENTORY` | OPEN | Gate A 工作量 |
| D-07 | Gate H model selection | ASTRA | `V2-GH-MODEL-DECISION` | OPEN | router 是否存在 |
| D-08 | Gate W acceptance thresholds | ASTRA | `V2-GW-DESIGN-FREEZE` | OPEN | Gate W 可否判定 |
| D-09 | V1 release decision | SOL | `V2-V1-RELEASE-DECISION` | OPEN | V1-Core QUALIFIED 宣告 |
| D-10 | PR #10 若稽核出 source mutation 或 evidence overwrite 如何處置 | ASTRA/SOL | `V2-P001` | OPEN | PRODUCT_SHA 的 authority 基礎 |
| D-11 | B.3 8448-cell 矩陣的取樣策略 | ASTRA | `V2-B3-MATRIX-BIND` | OPEN | 效能結論是否成立 |
| D-12 | R9 若需 product 支援，是否接受新 PRODUCT_SHA 並重跑部分 R8 | ASTRA/SOL | `V2-R9-PRODUCT-SUPPORT` | OPEN | R8 是否重做 |
| D-13 | process identity 在 starttime 不可得時的替代方案 | ASTRA | `V2-R9-DESIGN` | OPEN | R9/R10 身分判定 |
| **D-14** | **terminal contract 的 teardown 順序以何者為準**（V-3 觸發） | **ASTRA** | **`V2-P007`** | **OPEN** | **C1 的 judge 判定能否完整生效** |
| **D-15** | **C1 execution interface bind（runner/collector/judge CLI；ADB5038 已由 V-7R 關閉）** | **ASTRA/LUNA host-readonly** | **`V2-P008`** | **PARTIALLY CLOSED** | **C1 是否能從 FULL_SPEC 升 FULL_EXECUTABLE** |
| **D-16** | **Gate H evidence 是否要求 router** | **ASTRA** | **`V2-GH-MODEL-DECISION`** | **OPEN** | **決定 NOT_REQUIRED vs REQUIRED；implementation failure 不得改寫此決策** |

決策記錄格式：
```
DECISION_ID / OWNER / DATE / CONTEXT（哪個 packet、哪份 evidence 觸發）
OPTIONS（至少兩個，含各自代價） / DECISION / RATIONALE
OVERRIDES（覆蓋了 AUTHORITY DAG 的哪一 rank，若有） / DOWNSTREAM（哪些 packet 因此改變）
```

---

## 24. 模板

### 24.1 RUNTIME GRANT

```
GRANT_ID        GRANT-<YYYYMMDD>-<NN>
ISSUED_BY       <人名>（只有人可簽發，模型不得自行簽發）
ISSUED_AT       <ISO8601>
SCOPE           <精確到單一 cell / 單一 attempt，例：R8-C1 attempt-09, single cell>
PACKET_ID       <對應的 FULL_EXECUTABLE packet id>
PRODUCT_SHA     <40-hex，必須與 packet 相同>
TOOLING_COMMIT  <40-hex，必須與 packet 相同>
ALLOWED_CELLS   <明確列舉，禁止寫 "and subsequent">
ALLOWED_ATTEMPTS<明確列舉編號>
DEVICE_MUTATION ALLOWED_WITHIN_SCOPE | FORBIDDEN
CI_DISPATCH     FORBIDDEN | ALLOWED（需附 product defect evidence 引用）
INSTALL         FORBIDDEN | ALLOWED（需附 product defect evidence 引用）
EXPIRES         <條件，例：完成一次 judge verdict 後立即失效>
ON_NON_PASS     FREEZE_AND_STOP（固定值，不得修改）
SIGNATURE       <簽發者確認語>
```
六條硬規則：
```
G-01  一個 grant 只授權一格。「順便把下一格跑掉」永遠不在授權內。
G-02  grant 在第一個 judge verdict 產生後即失效，無論 verdict 為何。
G-03  非 PASS 之後不得用同一個 grant 重跑。修復後需要新 grant。
G-04  grant 不得授權 Stable 相關的任何操作。Stable 永遠不可授權。
G-05  grant 不得授權建立 attempt-10 或任何跳號 attempt。
G-06  模型不得自行簽發、延展或推論 grant 的存在。
```
**目前待簽發（本計劃任務不簽發）：**
```
SCOPE            R8-C1 attempt-09, single cell
PACKET_ID        V2-R8-C1-09
PRODUCT_SHA      b984dedcac731b77ca4cf8899f8a78b7848ad083
TOOLING_COMMIT   2a14ab2f7a5d81e7cd72d5308f5865b81b22881f
ALLOWED_CELLS    R8-C1（僅此一格）
ALLOWED_ATTEMPTS attempt-09（僅此一個）
DEVICE_MUTATION  ALLOWED_WITHIN_SCOPE
CI_DISPATCH      FORBIDDEN
INSTALL          FORBIDDEN
EXPIRES          第一個 judge verdict 產生後
ON_NON_PASS      FREEZE_AND_STOP
STATUS           NOT ISSUED
```

### 24.2 NEXT-AGENT HANDOFF

> HANDOFF 是 append-only。**永遠不得改寫歷史條目**，包含 FAIL 條目。

```
TIMESTAMP / AUTHORING_AGENT / ROUND_TYPE（PLANNING|HOST_EXECUTION|RUNTIME_EXECUTION|REPAIR|DECISION）
CURRENT AUTHORITY（snapshot / PRODUCT_SHA / CI_RUN / TOOLING_COMMIT / installed artifact）
WHAT THIS ROUND DID              只寫實際發生的事
WHAT THIS ROUND DID NOT DO       逐條列出可能被誤以為已完成的事
STATE DELTA                      before → after，每項可驗證
FROZEN THIS ROUND                新增的 immutable evidence（路徑 + hash）
CLASSIFIERS ISSUED               本輪產生的任何 classifier
OPEN EVIDENCE GAPS               無法取得的證據 + 對應 packet id
NEXT SAFE ACTION                 packet id + 是否需要 grant + 需要什麼 grant
STOP BOUNDARY                    逐條列出下一個 agent 不得做的事
STATUS LINE                      R8 remains N/10. Production Gate A remains BLOCKED.
```
三個最常被省略、也最常造成事故的欄位：
```
WHAT THIS ROUND DID NOT DO   ← 沒有這欄，下一個 agent 會假設你做完了
OPEN EVIDENCE GAPS           ← 沒有這欄，缺證據會變成默認為真
STOP BOUNDARY                ← 沒有這欄，下一個 agent 會自行推論可以繼續
```

### 24.3 LUNA PROMPT 模板

固定章節順序（不得增刪、不得換序）：
```
CURRENT AUTHORITY / GOAL / READ EXACTLY / DO NOT READ AS CURRENT AUTHORITY
PRECHECK / DO / DO NOT / COMMANDS / EXPECTED TRACE
PASS / VALID FAIL / INVALID / BLOCKED / INFRA BLOCKED
EVIDENCE / CLEANUP / STOP / REPORT EXACTLY
```
**自足性測試（交付前必過）** —— Luna 只讀這一份，是否還可能問出下列任一問題？
```
我要看哪個 SHA？ · product 還是 tooling？ · 要 build 嗎？ · 要 CI 嗎？ · 要 install 嗎？
用哪個 runner？ · 用哪個 judge？ · 這算一次 attempt 嗎？ · 可以 retry 嗎？
BLOCKED 和 INVALID 怎麼分？ · 要存哪些 evidence？ · 哪個 cell 能接著跑？ · 需要新的 grant 嗎？
```
任何一題答案仍不明確 → packet 不合格，繼續細化。

Luna 永遠不得做的事（每份 prompt 的 DO NOT 必須涵蓋）：
```
自行 redesign · 自行 retry · 自行換 signal · 自行換 runner · 自行換 judge
自行 build · 自行 install · 自行進下一格
自行放寬判準或延長 timeout · 自行補上缺失的 END · 自行 dedupe · 自行推論 grant 存在
```

---

## 25. IMMEDIATE NEXT SAFE ACTION

**下一個 runtime candidate 仍是 `R8-C1 attempt-09`，但 V2.2 明確把它降為 `NOT READY FOR GRANT`。**

```
RUNTIME_CANDIDATE : R8-C1 attempt-09
PACKET            : V2-R8-C1-09
PACKET_STATE      : FULL_SPEC_EXECUTION_BIND_PENDING
RUNTIME_STATE     : NOT STARTED / NOT CONSUMED
GRANT_STATE       : NOT READY / NOT AUTHORIZED
```

在任何 runtime grant 之前必須完成的兩個 **hard host-only bind**，
**已於 2026-09-21 全部關閉**：

| 順位 | Packet | 目的 | 成功輸出 |
|---|---|---|---|
| 1 | ~~`V2-P007-TERMINAL-CONTRACT-SOURCE-BIND`~~ | **✅ CLOSED 2026-09-21** | `SOURCE_BOUND`。ClearWorkQueue = **REQUIRED as transit, FORBIDDEN as discriminator**（無條件執行，無法區分 DE_TERMINATE / DE_RESET）|
| 2 | ~~`V2-P008-C1-EXECUTION-INTERFACE-BIND`~~ | **✅ CLOSED 2026-09-21** | `INTERFACE_BOUND`。runner env-driven；§22.7 step 5 改 5a/5b、step 6/7 移除 |
| 3 | **`V2-P009-JUDGE-FIXTURE-CONTRACT-MATRIX`** | **STANDING GATE — 每次 grant 前必跑** | `CONTRACT_CONSISTENT`。逐格比對 `judge_*` 要求的 observation phase 與 `cell_*` 實際送出的 client request，回報 judge 要求但 fixture 結構上無法觸發者 |

> **`V2-P009` 是常設閘門，不是一次性 packet。**
> 執行：`evidence/session/gate-a-a1/planning-v2/p009-judge-fixture-contract-matrix/check-judge-fixture-contract.py`
> host-only、唯讀、零 device 互動。**exit 1 → 不得 grant。**
> 任何 `judge-r8-v2.py` 或 `p_r8_lifecycle.c` 的變更後必須重跑。
>
> 2026-09-21 基準結果：`CONTRACT_MISMATCH 2/10`
> ```
> R8-C1           judge_c1 要 R_ACK_SETTLED / R_DESTROY_STAGE / X_CHECKPOINT
>                 cell_c1 不送 r8_register、不送 r8_checkpoint
> R8-C5-overflow  judge_c5_overflow 要 X_CHECKPOINT
>                 cell_c5_overflow 不送 r8_checkpoint
> ```
> 其餘八格 contract-consistent。這道閘門若早存在，attempt-09 不會被花掉。
> **限制（避免過度解讀）：** 靜態源碼分析，只偵測「judge 要求 fixture 無法觸發的 phase」這一類。
> exit 0 不代表該格會 PASS。

完成後才允許把 `V2-R8-C1-09` 升為：

```
FULL_EXECUTABLE / READY_FOR_EXPLICIT_GRANT / NOT_STARTED
```

其他可並行 host-only 工作（不授權 device）：`V2-P003` hash reverify、`V2-P006` negative-vector bind、
`V2-R8-C2-SRC-TRACE`、`V2-R8-D-SRC-TRACE`。

PR #10 scope audit 與 PR #7 reconciliation 已在 V2.2 關閉，不再列為 C1 前待辦。
ADB-5038 client form 已在 V2.3 由本機實測關閉（V-7R），亦不再列為 C1 前待辦；
`V2-P008` 的剩餘範圍只有 runner flags 與 collector/judge invocation。

---

## 26. STOP BOUNDARY

```
DO NOT invoke run-r8-one-cell-b984ded-v2.sh before V2-P007=SOURCE_BOUND and V2-P008=INTERFACE_BOUND
DO NOT create runtime-b984ded/r8-c1/attempt-09/
DO NOT create attempt-10
DO NOT start R8-C2
DO NOT start R9 or R10
DO NOT build / install / dispatch CI
DO NOT touch Stable (com.termux.x11 / :1 / PID 20146 / HDMI)
DO NOT reclassify attempts 01-08
DO NOT treat "ADB lane restored" as authorization
DO NOT commit this document without explicit instruction

Progress baseline remains PR #10.
R8 remains 0/10.
Production Gate A remains BLOCKED.
V1-Core remains NOT QUALIFIED.
```

---

## 附錄 A — 查驗來源清單

| 查驗 | 來源類型 | 來源 |
|---|---|---|
| V-1 | 上游原始碼 / 官方文件 | xorg-server `include/opaque.h`（`DE_TERMINATE 2`）；`hw/dmx/dmxinit.c` doxygen（ddxGiveUp 由 `dix/main.c` 在 `dispatchException & DE_TERMINATE` 時呼叫） |
| V-2 | 上游原始碼 | xorg-server `os/utils.c` — `GiveUp(int sig)` 設 `dispatchException \|= DE_TERMINATE; isItTimeToYield = TRUE;` |
| V-3 | 上游原始碼 | xorg-server `dix/main.c` 主迴圈結尾（`FreeAllResources` → `CloseScreen` → `OsCleanup` → `ddxGiveUp`）；`ClearWorkQueue` 於 reset 路徑（xorg/xserver#670 修復） |
| V-4 | 官方協定文件 | `xorgproto/presentproto.txt`；`X11/extensions/presenttokens.h`（option 位元值） |
| V-5 | 官方 API 文件 | Android NDK `Native Hardware Buffer` group reference（`AHardwareBuffer_lock/unlock/acquire/release/sendHandleToUnixSocket`） |
| V-6 | 官方 registry | Khronos EGL Registry `ANDROID` 目錄；AOSP `frameworks/native/opengl/specs/README`（enum 保留值） |
| V-7 | 官方 man page + 上游 commit | `adb(1)`（`-P` vs `-L` 語意、`ANDROID_ADB_SERVER_PORT`、mdns 環境變數）；AOSP adb socket_spec commit |
| V-7R | **本機第一手量測（rank 高於上列二手來源）** | 本機 `adb 35.0.2` 自身 `--help` 輸出；2026-09-21 於本機以未占用 port 反證三種 client 形式之實際到達 port；`kill-server` 反向驗證；裸環境變數測試 |
| V-8 | 官方 README | `termux/termux-x11` README（`-legacy-drawing`、`-force-bgra`、通知列 Exit 不會結束 `termux-x11` 指令） |
| V-9 | 廠商官網 + 多家規格資料庫 | Xiaomi / POCO 官方產品頁；GSMArena（SM8850-AC、Adreno 840、1200×2608@120Hz）；Notebookcheck（Adreno 840 三 slice @1.2GHz） |

**重要限制：** 上述來源**不是任何 authority rank**。
它們只能用來發現矛盾、產生 packet、修正指令形式，
**不能**直接覆蓋 frozen evidence、frozen contract 或 product source。
唯一能裁決 V-3 的是 `b984ded` 的實際原始碼（`V2-P007`）。

---

## 附錄 B — V2.2 → V2.3 變更摘要

| # | 變更 | 來源 | 影響範圍 |
|---|---|---|---|
| 1 | 新增 `V-7R`：V-7 的「`-L` 用錯了」由本機實測推翻 | 2026-09-21 host 量測 | §1 §1.1 §2.5 §17 §20.1 §22.6 §22.7 §22.12 §25 附錄 A |
| 2 | ADB-5038 client form 由 `PROPOSED` 綁定為 `adb -P 5038` | V-7R | §2.5 §22.7 step 2/3 |
| 3 | C1 packet step 2/3 升級 `PROPOSED_NOT_YET_EXECUTABLE` → `EXISTS_EXECUTABLE` | V-7R | §22.7 |
| 4 | 選 `-P` 的理由由「功能正確性」改為「provenance」 | V-7R | §2.5 §20.1 V-19 |
| 5 | **新增 R-27：`-P` auto-start 使死 lane 偽裝成活 lane** | V-7R 結論三 | §17 §22.5 §22.12 |
| 6 | 新增 schema 規則 V-23：preflight 必須斷言 SERIAL 逐字出現 | R-27 | §20.1 §22.5 |
| 7 | R-24 證偽並關閉（機制不成立） | V-7R | §17 |
| 8 | V-19 改寫：禁用 env 與 `-L` 選 server，理由為 provenance | V-7R | §20.1 |
| 9 | `ENV_DENYLIST` 擴大為 `ANDROID_ADB_SERVER_PORT` 任何值 | V-7R 結論四 | §22.6 |
| 10 | GAP-6 / D-15 / `V2-P008` 範圍縮小為 runner/collector/judge | V-7R | §1.2 §21.2 §23 §25 |
| 11 | 記錄兩項環境層反直覺事實（PRoot 可跑 native adb；port scan 失效） | V-7R 結論五 | §1 |
| 12 | schema 驗證規則 22 → 23 條 | V-23 | §20.1 |

---

## 附錄 C — V2.1 → V2.2 變更摘要

| # | 變更 | 影響 |
|---|---|---|
| 13 | **`V2-P007` CLOSED = `SOURCE_BOUND`**；V-3 裁決完成，C1 EXPECTED_TRACE 改以 source-bound sequence 為準 | P007 | §1 V-3 · §1.2 GAP-5 · §7.1 · §22.8 · §25 |
| 14 | **`V2-P008` CLOSED = `INTERFACE_BOUND`**；runner 為 env-driven，`--cell/--attempt/--serial` 不存在 | P008 | §1.2 GAP-6 · §22.7 · §23 D-15 · §25 |
| 15 | §22.7 step 5 拆為 5a（VALIDATE_ONLY 乾跑）/ 5b（唯一消耗 attempt）；step 6/7 移除 | P008 | §22.7 |
| 16 | CELL_ID 詞彙更正為 `R8-C1`…`R8-P2`（原 `c1` 不被接受） | P008 | §22.7 · §7.x 全部十格 |
| 17 | ADB 綁定形式補上 `-H 127.0.0.1` | P008 §3 | §2.5 §22.7 |
| 18 | **新增 R-28：TOOLING_COMMIT `2a14ab2` 未推送至任何 remote** | P003 | §17 · §2.3 |
| 19 | `V2-P003` tooling hash 重驗完成：8/8 可驗者 MATCH | P003 | §2.3 |
| 20 | **RUNNER 升 v3（F1 amendment）**：preflight 區新增 installed-APK sha256 比對，mismatch → exit 3 BLOCKED、attempt 不消耗 | C1 preflight F1 | §2.3 · §22.7 |
| 21 | `artifact-binding.json` 新增 `provenance` 區塊（MEASURED / DERIVED / NON-DISCRIMINATING / BOUND） | F1 | §22.7 |
| 22 | `build_id` 標記為不具鑑別力（fb4f017 與 b984ded 相同），不得用於 artifact identity | F1 | §2.3 |
| 24 | **RUNNER 升 v4**：STABLE_AFTER 移至 judge 之前，修正 `5a782f6` 起的六代回歸（R-30）| attempt-09 RCA | §2.3 · §22.7 |
| 25 | **新增 GAP-7 / R-31 / D-17**：`judge_c1` 要求 `cell_c1` 不產生的向量，R8-C1 `DESIGN_REQUIRED` | v4 離線診斷 | 標頭 · §1.2 · §17 · §23 |
| 26 | R8-C1 attempt-09 執行並凍結為 INVALID；首次觀測到完整乾淨的 C1 生命週期與 P007 預測一致 | 實機 | §5.1 |
| 23 | §22.5 X3_PRECHECK 明定必須用 runner `x3pid()` 形式，禁裸 `pgrep -f`（會匹配操作者自身 shell → false BLOCK） | C1 preflight F3 | §22.5 |

本附錄後半為 V2.3 初版（measurement pass）條目：

| 1 | `V2-P007` 從 soft 升為 C1 hard prerequisite | 未 source-bind terminal sequence 前不得 grant / run |
| 2 | 新增 `V2-P008-C1-EXECUTION-INTERFACE-BIND` | ADB5038 / runner / collector / judge CLI 全綁後才可執行 |
| 3 | C1 fresh pair B 改為 object identity / tuple / generation 語意 | 避免合法 allocator numeric reuse false-red |
| 4 | R9-F1 改為 enum16 / `x-wrong-generation` reason6 expected fatal | 與 frozen R9 containment 方向一致 |
| 5 | Gate H 改三態 | implementation failure 不得逃回 NOT_REQUIRED |
| 6 | `V2-R8-C1-09` 從 FULL 降為 `FULL_SPEC_EXECUTION_BIND_PENDING` | 消除「commands 未綁卻可施工」矛盾 |
| 7 | PR #10 121-file scope audit 完成 | `SCOPE_CLEAN_DOCS_EVIDENCE` |
| 8 | PR #7 38 packet reconciliation 完成 | R7 completed / R8 superseded / R9→V1 rewrite |
| 9 | attempt 01–04 frozen classifier 回填 | GAP-3 關閉，不 reclassify |
| 10 | `GiveUp` 措辭精確化 | termination handler/function；`GiveUp(0)` 是 in-process direct call |
| 11 | schema 新增 V-21/V-22 | FULL_EXECUTABLE 必須無 proposed command；C1 必須 P007/P008 |
| 12 | immediate next safe action 改為 host-bind-first | attempt-09 仍 NOT STARTED / NOT CONSUMED |

---

## 附錄 D — V2.0 → V2.1 變更摘要

| # | 變更 | 來源 | 影響範圍 |
|---|---|---|---|
| 1 | 新增 §1 交叉查驗紀錄（九項） | 本輪查驗 | 全文 |
| 2 | 新增 packet `V2-P007-TERMINAL-CONTRACT-SOURCE-BIND` | V-3 | R8 全線 judge 判定 |
| 3 | C1 的 teardown 順序判定留白，升級為 DESIGN_REQUIRED | V-3 | §7.1 §22.8 §22.10 |
| 4 | 終止契約新增「必須證明進入點」判準 | V-2 | §2.7 §7.1 §22.8 |
| 5 | Present `ASYNC\|COPY` 寫死為 `0x3` | V-4 | §7.3 §21.2 schema V-20 |
| 6 | C3-window 新增三項必證（idle-fence / pixmap ref / 取消路徑退休） | V-4 | §7.3 |
| 7 | adb 指令從 `-L` 改為 `ANDROID_ADB_SERVER_PORT` / `-P`，並降級為 PROPOSED | V-7 | §2.5 §22.6 §22.7 §25 schema V-19 |
| 8 | Gate A 缺口 #6 新增三條最小設計要求 | V-5 | §13.3 |
| 9 | R10 新增三個 fence-fd metric | V-5 | §9.4 |
| 10 | B.3 `fullscreen` 拆成 internal / external，矩陣 7680 → 8448 cells | V-9 | §12.1 D-11 |
| 11 | 新增風險 R-23（順序誤判）與 R-24（adb 旗標語意） | V-3 / V-7 | §17 |
| 12 | 新增決策 D-14（teardown 順序以何者為準） | V-3 | §23 |
| 13 | schema 驗證規則 18 → 20 條 | V-7 / V-4 | §20.1 |
| 14 | 新增 §4.0 進度基準宣告（PR #10 為唯一基準） | 使用者確認 | §4 |
| 15 | 29 檔樹狀結構合併為單一檔案 | 使用者要求 | 全文 |
