# Phase 1B-1 結果：`:2` non-legacy xterm A/B（2026-09-07 01:36–01:46 CST）

> **快照。** 後續 debug5 P0 已 CLOSED。現況見 `HANDOFF.md`。

變數唯一：同一 Stable binary（`1.03.01-6`），`:2` 不加 `-legacy-drawing`。
`f8-control` 未 merge（已 tag `f8-control-20260907`）；control APK 未安裝；
`f8desk`／`f8desk-external`／全域 GPU env／Mesa／PR／Chromium／Cursor 全未動。

##  verdict：FAIL（visual），但不是黑屏

- server 存活、X protocol 正常、字形正常渲染；**視窗內容被畫到錯誤偏移 (+770,+2)**。
- 屬 P0 blocker（non-legacy root/AHB/presentation 路徑）已收斂，未到 fence 層。

## Trial 1（01:36–01:43）

- server PID 20514（PPID wrapper 20494），X2 socket 正常建立，`xdpyinfo :2` OK。
- 啟動 log（`logs/x11-nonlegacy-trial1.log`，logcat 混合；server 行摘於
  `evidence/nonlegacy/trial1-server-startup.txt`）：
  `libXlorie.so` 載入 OK → AdrenoGLES `/vendor/lib64/egl/libGLESv2_adreno.so` →
  qdgralloc IMapper5 → `Xlorie: Initialized EGL version 1.5` → gles-renderer 存活。
- xterm 可 map（`xwininfo -tree` 位置正確），雙視窗、explicit geometry（`+100+100`）皆 honored。
- 截圖（`trial1-root.png`／`trial1b-root.png`／`trial1c-root.png`）：
  +0+0 的 484x316 xterm 實際畫在 (770,2)-(1252,316)；第二窗 +100+100 相對偏移正確，
  但整組再平移 (+770,+2)，超出右緣部分被 root 邊界裁掉。
- 全刪窗後 root 非全黑：僅剩 y=0 一列 178 像素（x 52–767）殘留。
- CPU：server 7 分鐘約 19 秒 CPU；收尾 kill server＋xterm（精確 PID），X2 stale socket 已清。

## Trial 2（01:44–01:46，全新 server＋單窗＋0+0，對照重現）

- server PID 30768，單一 xterm `OFFSET-B` +0+0。
- 截圖 `trial2-root.png`： painted bbox 與 trial1e **完全一致**
  `(770,2)-(1252,316)`，前景像素數同為 38097；y=0 殘留列亦一致 `(64,0)-(766,0)`。
- **2/2 重現，確定性偏移，非偶發。**

## 判定（對應 completion gate）

1. `:2` non-legacy xterm：**FAIL**（protocol 活、畫面位置錯）
2. 失敗型態：系統性 paint offset (+770,+2)＋1px 頂列殘留；**不是黑屏**，AHB/EGL 初始化成功
3. 穩定重現：是，2/2，像素級一致
4. log 最深位置：EGL 1.5 init OK（Adreno 路徑）＋ renderer cursor 更新持續；
   缺 AHB desc／root pixmap 註冊值／Present rect／fence 等幾何資訊
5. 需要進 `f8-ahb-debug`：**是**（最小 instrumentation：root pixmap origin/size、
   AHB desc、Present copy rect；XFCE 在此之前不啟動）
6. XFCE：未測（按 gate，FAIL 即停）
7. `:1` Stable：全程正常（同 PID 10718；裸 llvmpipe＋f8-gpu Adreno 840 與基線一致；僅剩 X1 socket）

## 副作用紀錄

- `:2` 啟動會送 ACTION_START 給 MainActivity，手機前景可能切到 Termux:X11（屬預期，收尾已退場）。
- `pkill -f xterm` 會誤殺自身，後改精確 PID kill（教訓已記）。
- 測試用 apt 補了 `xterm`、`python3-pil`（環境工具，不影響 Stable／Mesa）。
