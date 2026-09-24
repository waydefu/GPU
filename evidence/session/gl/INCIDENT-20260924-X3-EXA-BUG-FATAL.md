# INCIDENT 2026-09-24 13:46:14 — 實驗版 X3 以 `EXA bug: pPixmap->devPrivate.ptr ... should have been NULL` FatalError 中止

> ## 更正（2026-09-24，同日）— 下方原始分析的死因判斷是錯的，保留原文作為紀錄
> - **X3 的真正結束原因**：logcat 同一秒由 X3（pid 15027）自己寫出
>   `13:46:14.773 I gatea-a1: GATEA_SUMMARY where=x-hup ... generationFatal=6 fatalReason=6` 與
>   `13:46:14.773 F gatea-a1: GATEA_FATAL_HALT what=x-hup reason=6`——這是 Gate A 的 **HUP 圍堵（R7-10）**：renderer 端
>   （實驗版 App 程序，13:46:14.752 被 SwipeUpClean SIGKILL，Zygote 13:46:14.776 確認 signal 9）斷線時，X **刻意 fail-closed 停機**。
>   這是設計行為（R7-10 PASS 的判準就是 `x-hup/6` 要出現），**不是 bug**。
> - **`EXA bug: pPixmap->devPrivate.ptr ... should have been NULL` 是非致命警告**：f592241 幾乎每個證據目錄的 x3-launcher.log 都有
>   （gl-bench 各 4 次、electron-gpu-probe-02 219 次、oracle-g/ga 319–534 次），X 都活到收尾（`x_alive_after_fixture=true`）。
>   乾跑 02 只因它剛好是 X3 死前最後一行，被我誤當成死因。它仍是一個潛在問題（GPU 路徑的 CPU 存取配對不一致），但與 X 結束無關。
> - 因此：使用者滑掉實驗版 → X 整個 session 結束，是**目前 Gate A 設計的後果**；要不要改成「renderer 斷線時 X 存活、改走 CPU／等重連」屬於設計決策，需使用者決定。

**狀態：已更正（見上方）。X3 結束＝Gate A `x-hup/6` 設計停機；EXA 那行是非致命警告。**產物 `1.03.01-f592241-24.09.26`，MODE=G（預設分流 `TERMUX_X11_GPU_MIN_PIXELS=4097`）。
證據：`electron-bench-dryrun-02/`（ELECTRON-BENCH 乾跑，不計分）——`x3-launcher.log` 最後一行、`dry-v0.stderr`、`raw-logcat.txt`、`mem-guard.log`。

## 觀察到的
- X3（pid 15027）`x3-launcher.log` 結尾：
  ```
  R3 S1_AHB  ... w=646 h=435 srcStride=646 dstStride=704 format=2 ...
  R3 S2_AHB_COPY ... w=646 h=435 ...
  EXA bug: pPixmap->devPrivate.ptr was 0x76bc6a0000, but should have been NULL.
  ```
  （Xorg `exa.c` 在 prepare-access 時發現 pixmap 的 `devPrivate.ptr` 已非 NULL 就 FatalError——即「借出 CPU 映射」的配對記錄不一致。）
- Cursor（V0，`--disable-gpu`，客戶端純軟體）同一秒：`X connection to :3 broken`，主程序 FATAL 結束；driver `ws error`。
- mem-guard **未觸發**（結束前 mem_available 5040–5156 MB、x3_rss 212 MB → 0）：不是記憶體保護殺的。runner `x_alive_after_fixture=false`。
- Stable 前後相同（`STABLE_SAME`）。

## 時間線（logcat）
| 時間 | 事件 |
|---|---|
| 13:44:24 | 乾跑 02 啟動 Cursor（V0） |
| 13:45:53 | `com.google.android.apps.translate` moveTaskToFront（使用者翻譯 Cursor 的 EFAULT 告警） |
| 13:45:54 | Google Lens（`googlequicksearchbox/…lens.MainActivity`）START；Android 同時回收多個快取程序（Chrome、Gmail、設定…）；實驗版 task 140 進入背景 |
| 13:46:12 | 使用者打開最近使用清單 |
| 13:46:13.815 | `RecentsContainer: removeTask` Google 翻譯（使用者滑掉） |
| 13:46:14.748 | `RecentsContainer: removeTask` task 140 = `com.waydefu.x11gpu`（**使用者滑掉**，使用者本人確認「是我滑掉的」） |
| 13:46:14.752 | `ActivityManager: Killing 29627:com.waydefu.x11gpu/u0a503 (adj 400): SwipeUpClean`（實驗版 App 程序＝Activity／renderer 被 SIGKILL） |
| 13:46:14 | X3 FatalError（上面那行）；同一秒 Cursor `X connection to :3 broken` |

## 觸發條件（已確認）與根因（未證實）
- **觸發：使用者從最近使用清單滑掉實驗版 → Android 以 SwipeUpClean 殺掉 App 程序（renderer 端）→ 同一秒 X3 FatalError。**
  X3 本身在 Termux 程序樹下，沒有被殺；是它在 renderer peer 突然消失後自己中止。
- 根因推測：renderer 端消失時，GPU（AHB）路徑上某個 pixmap（646×435，大於 64×64 分流門檻）的 CPU 映射沒有歸還，
  `devPrivate.ptr` 殘留，下一次 prepare-access 觸發 exa.c 的一致性檢查 → FatalError。**未證實**（需讀 peer-death 清理路徑）。
- 使用者影響：依 Termux:X11 架構（X server 在 Termux 程序、App 只是畫面端），Stable 版被滑掉時 X 應繼續活著、重開可重連（**推論，未在本機實測**）；實驗版這次則是整個 X session（其上所有程式）一起結束。
  若實驗版要當日常使用，這是必修項目。

## 處置
- 不重跑、不改判。ELECTRON-BENCH 乾跑 02 記為「工具檢查不成立（X3 中止）」，需另跑乾跑 03。
- 正式跑期間不得切換 App、不得從最近使用清單滑掉實驗版。
- 根因（Activity 生命週期 × EXA AHB access 配對）另開題追查；可重現性待驗證（需要明確授權再構造「X 有 GPU pixmap 時滑掉實驗版」的案例）。
