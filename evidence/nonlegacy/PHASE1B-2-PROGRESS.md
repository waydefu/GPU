# Phase 1B-2 進度（2026-09-07 ~02:50 CST，尚未收尾）

> **快照，不要當現況。** +768 後續在 debug5 上 Case A/B/C 未重現，P0 CLOSED。現況見 `HANDOFF.md`。

工作樹：`src/f8-ahb-debug`（獨立 worktree，基於 upstream `9df8b76`，`f8-control` 未動）。
instrumentation commit `2516d8a` 已推送到 fork `f8-ahb-debug`（未 build、未安裝、未測）。

## 量測結論（無需修即可確定）

- Root 繪製偏移：**(+768, 0)，Case A constant translation**，與視窗位置／尺寸無關：
  +0+0→768；+100+0→872；+0+100→776；+100+100→870。尺寸精確保留。
- 先前 `+2` 是 xterm 內框假影，dy 實為 0（raw fill y0=200→200）。
- Root AHB = 1280x1024x4 bytes 精確（dmabuf 5242880），無 padding 嫌疑。
- Android 側 BLAST 1920x1059、IDENTITY、全幅 crop——排除 SurfaceFlinger/HWC letterbox。
- GPU copy 路徑零執行（trial log 無 `rendererApplyPendingGpuCopies: rect`），排除 renderer。
- lorie 程式碼內無任何 drawable.x/y 賦值；root 預設 1280x1024 來自 InitOutput 寫死值。
- 768 候選公式全滅：(1920-1280)/2=320 不是；letterbox 不是；stride padding 不是
  （dmabuf 精確）。`768 = 0x300` 來源仍未知，需 runtime log。
- 視窗本體異常（xterm/xclock/xeyes 重影、xeyes 像素出現在 xterm pixmap 內），
  但視窗 pixmap 全是 REGULAR calloc（dmabuf 列表無對應項）——指向 heap/生命週期或重複繪製，
  待 CreatePixmap log 驗證（重複 locked ptr 即為實錘）。
- xlogo 靜態多邊形視窗乾淨；y=0 殘留列＋destroy 後碎片指向 damage/clear 次要問題。
- Raw X11 客戶端手刻驗證了 setup/GC/fill 路徑可用（踩過 length/ID/fieldset 三個坑，已記入 patches/）。

## 已做

- `:2` 退場原因不明（01:53–02:28 間消失，log 無 crash；疑似另一工作階段收尾）。
  協調：`evidence/COORDINATION.md`，`:2` 留給對方，本工作階段改用 `:3`（offset 在 `:3` 同樣重現，具一般性）。
- adb 無線已連（10.129.215.219:46485，只跑 dumpsys/screencap 唯讀命令）。
- 外接實為 AOC 1920x1080（displayId 2），不是 MSI；App 在此外屏 1920x1059 surface。
- 幾何矩陣工具：patches/xfillrect.py、patches/xpixmaptest.py（後者卡在 server client-ID 分區，暫棄）。

## 待決策（見回報）

instrumented APK 要上機測試有兩條路：A. side-by-side applicationId（乾淨、3–6h）；
B. 備份 Stable→暫裝 debug→測完還原（快、有動 daily driver 風險，需明示批准）。

## 2026-09-07 ~03:30 追記：A 已執行，首版 experimental 上機但啟動即死

- `com.waydefu.x11gpu` 與 Stable 共存安裝成功（versionName `1.03.01-c2ec25f`）；`:1` 未動。
- 獨立 loader（`libexec/x11gpu/loader.apk`）＋`f8-x11gpu` 就緒；Stable 四檔 SHA 驗證未動。
- f8dbg setViewport 正常流入（`0,0,1200,2416`——實驗 App 落在手機直屏，X 屏會跟著變，
  與 1280x1024 對照組不同，留待第二輪比對）。
- **首版 X server 啟動即死**：X3 socket 殘留、無後續行程；log 止於 MainActivity，
  X native 零輸出。根因：本工作階段 instrumentation 在 `lorieCreateScreenResources`
  直接解參考 `pScreen->root`，而該時點 root window 尚不存在（NULL deref）。
  已修（NULL guard）＋ early log 改雙寫 `/tmp/x11gpu-f8dbg.log`（避開 logcat-fd 競態），
  commit `d91da04`（append-only，不改已推歷史），rebuild 中。

## f8dbg 第一批台帳（commit `d91da04`，`:3`，2026-09-07 ~03:46）

- Root drawable origin **(0,0)** 兩次 RRSetSize 皆確認——位移不是 drawable origin。
- Screen mapping 穩定：`ptr=0x7329dbf000 devKind=5120`（1280 屏）。
- **Stride 證據**：1200 寬 AHB 的 desc stride=**1216**（gralloc padding 實錘，devKind 路徑處理）。
- X 屏被 activity 連 resize 兩次：1280x1024 → 1200x2416 → **1200x2191**（bufid 4/5/6，locked ptr 皆不同）。
- 同 locked ptr 的小 pixmap（16x16 bufid 2/3、glyph 群 bufid 10–21）出現——需 Destroy log
  判定是 sequential reuse 還是 concurrent aliasing（下一版 instrumentation 已加）。
- **xterm 484x316 window pixmap 從未經過 lorieCreatePixmap**——路徑未知（ZERO-size＋
  ModifyPixmapHeader sysmem 嫌疑），下一版已加這三處 log。
- 新偏移數據點（1200 寬 root）：xterm 畫在 772–1200（被右緣裁）、另有 0–52 殘塊；
  768+484=1252>1200 溢出 52px **恰好等於殘塊寬**——wrap 假說（`768 mod 484 = 284 ≈ seam`）。
- 螢幕尺寸變化不改變偏移量級（1280 屏 +768，1200 屏 +772≈768）——仍是 Case A。
- commit `f6584c1`（ledger 補完：ZERO/Modify/Destroy log）已推，build `34056252079` 進行中。

## 2026-09-07 ~05:00 追記：視窗 drawable 繪製靜默消失（與 root 位移並列第二戰場）

- xrestop 證明 xterm **不擁有** window-sized pixmap（pixmap bytes 僅 9216，glyph/cursor 等級）。
- BackingStore NotUseful；ledger 從未出現 484x316（任何尺寸、ZERO 路徑亦無）。
- Raw PolyFillRectangle 進 window drawable：X 零錯誤，但 window-read／root-read 皆無痕跡
  （可見區亦然，排除 occlusion/clip；不同顏色、整窗填滿皆然）。
- Raw fill 進 root drawable：正常出現（+768 平移）。
- xterm 文字（同一個 window drawable！）卻正常出現（+768 平移）。
- 初步區分：CORE fill 進 window 消失 vs RENDER glyph／core polygon／root fill 出現。
  待 PrepareAccess census（commit `c698164`，build `34060173746`）裁決：
  window access 是否到達、lock 是否失敗（舊 dprintf 在 logcat 不可見，現已鏡像到 f8dbg）。

## 2026-09-07 ~06:16 追記：B 戰場已解釋；本輪 presentation 未見 +768

- **「沒有 484×316 CreatePixmap」不是異常。** `fbCreateWindow` 把每個 window 的 pixmap private 設成 screen pixmap；window 像素在 root 上。xrestop 只見 glyph 是預期。
- **`0x20000c` CORE 靜默消失 = 正常 clip。** 外框 484×316、border 1；VT `0x20001b` 同尺寸蓋滿內部。打 `0x20001b`：FillRect/PutImage/Segment 寫入 root 正確座標。
- GetImage：`(21,21)=綠` `(789,21)=黑` `(301,11)=紅` `(1069,11)=黑` → CORE 沒有在 +768 寫第二份像素。
- 未重啟 `:3`、未改 code。手機截圖綠 40×40 在 screenshot (21,165)=X(21,21)；紅 FillRect 起點 (301,155)=X(301,11)。**在本次快照中這條 presentation 正常。** 當時的 +768 疑點後續已降為 historical，現況見 `HANDOFF.md`。
- `c698164` 本輪活過 50+ min。Stable `:1` PID 10718 未動。

## 2026-09-07 ~06:38 追記：Case C fresh `:3` 3/3 未見 +768；A 降為 historical

只改變量：長命 process → fresh process。其餘鎖死：HDMI fullscreen、exact 1280×1024、單一 xterm、立即 marker、第一次截圖。

| Run | 第一次 presentation | 綠 bbox left | GetImage 789 |
| --- | --- | --- | --- |
| C1 trial10 PID 29181 | 正常 | 381 | 黑 |
| C2 trial11 PID 6699 | 正常 | 381 | 黑 |
| C3 trial12 PID 11957 | 正常 | 381 | 黑 |

381 = extra-keys letterbox（`setViewport x=361 w=1198 ew=1280`），不是 content +768。未加 renderer instrumentation。

A 不再是 current bug。B 不要重開。Stable 10718 未動；測完 experimental 已還原 Display0 native，`:3` 現 PID 11957 / 1200×2191。

## 2026-09-07 ~04:30 追記：experimental 啟動後 ~1–2 分鐘必死（Thread-1, SEGV 0x8）

- `c2ec25f`、`f6584c1` 皆死；`d91da04` 活過 1 小時；stock 6 次全活。tombstoned 已壞，
  無 backtrace；dropbox 無今日記錄。
- 健康 `:1` 也有同名 Thread-1（另一個 Java 未命名執行緒），故 Thread-1 是特定執行緒，
  非 main。f8dbg file 在死前零行——死於首個 screen pixmap log 之前（AHB allocate 附近）。
- 嫌疑排序：① Modify-during-create 半成品 pixmap（f6584c1 獨有，已靜音，build
  `34058386300` 驗證中）；② 堆腐敗時序問題（logging 改變 race window）；
  ③ EGL-in-X-process。若 ① 無效，下一步是零 native diff 的純 side-by-side build
  做乾淨 bisect（程式碼 vs 包裝/環境）。
