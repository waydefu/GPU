# PGA-GAP-3 RCA — staging 路徑每個 composite 的 FD 複本註冊給 renderer 後永不註銷

DATE 2026-09-23 · PRODUCT `bfb5769` · 狀態：§13.2 第 1 步（RCA）——原始碼證明＋既有 logcat 量化；不需要新的裝置執行

## 1. 觸發

```
b3-s-02   B.3 mode S（PROTO 未設 = D0a staging 路徑）開跑 45 秒內，手機記憶體耗盡
          lmkd 先殺 com.termux.x11（Stable :1，adj 400），再殺 com.termux（PRoot/Claude/adb/X3）
          INCIDENT-20260923-2-LMK-B3-S.md
```

## 2. 原始碼（bfb5769）

```
配置     lorieExaPrepareComposite（staging 分支）-> lorieCloneBgraAhbToFd（InitOutput.c:~1717）
         TERMUX_X11_D0A 未設時：每個 Prepare 都 LorieBuffer_allocate(src 寬×高, LORIEBUFFER_FD)
         並 memcpy 整張 src（不是只有要畫的矩形）。FD buffer = ASharedMemory / memfd（buffer.c:97/101）-> Shmem
註冊     lorieTryScheduleGpuBlit -> lorieRegisterBuffer(srcBuffer = exaCompSrcUpload)（InitOutput.c:1855）
         -> EVENT_ADD_BUFFER + 傳 fd（cmdentrypoint.cpp:1407），renderer addBuffer（activity.cpp:537）
釋放     lorieExaDoneComposite：LorieBuffer_release(upload)（InitOutput.c:3759-3801），沒有 lorieUnregisterBuffer
         refcount 到 0 -> __LorieBuffer_free：xorg_list_del（只離開 X 端 registeredBuffers）、munmap、close（buffer.c:377）
         不送 EVENT_REMOVE_BUFFER
renderer 只在 EVENT_REMOVE_BUFFER（activity.cpp:550）或斷線 removeAllBuffers（activity.cpp:463/579）時釋放
對照     D0a cache 版本（lorieCloneBgraAhbToFdCached）換 buffer 前有 lorieUnregisterBuffer（InitOutput.c:1678）
         整個 X 端 lorieUnregisterBuffer 只有兩個呼叫點：1678（D0a cache）與 3917（pixmap 銷毀）
```

結論（原始碼層）：非 cache 的 staging 上傳 buffer **一定**不會被註銷；renderer 端的副本（fd/mmap 與其 GL 資源）
活到 X 斷線為止。

## 3. 量化（既有 logcat；X 端每次註冊都印 `Sent shared buffer ... type 2`，type 2 = LORIEBUFFER_FD）

```
b3-s-02（S，45 s）   17:07:44    54 個   169 MB
                     17:08:00   675 個  2998 MB
                     17:08:16   896 個  5636 MB
                     17:08:28  1518 個  7382 MB   <- com.termux 被 lmkd 殺的同一秒
lmkd killinfo        17:08:00 -> 17:08:28：zram 使用 5.8 -> 12.9 GB，MemFree 30-200 MB
                     17:08:28 X3 死（斷線 -> renderer removeAllBuffers）-> 1.7 s 內 zram 少 5.8 GB
                     實驗版 Activity 活到 17:16（使用者滑掉）——記憶體跟著 X 的連線走，不跟著 Activity 程序走

XFCE（G 設定，每個 run 約 5 分鐘）：
                     FD 註冊          Activity maps_count K4-K0
xfce3-c1-01（G）      3348 / 4108 MB   +555
rca3-g-01（G）        3225 / 3958 MB   +563
rca3-c-01（C）           0 /    0 MB     +6
```

G 設定下，沒走 direct 的 composite 退回 staging；XFCE 裡 direct 只有 15 次，staging 約 3300 次。

## 4. 已證明 / 未證明

```
已證明  staging 上傳 buffer 註冊後 X 端永不註銷（原始碼，所有呼叫點）
已證明  S 模式的註冊量與記憶體耗盡同步（7.4 GB / 45 s；耗盡時點相同），釋放與 X 斷線同步
已證明  G 設定的 XFCE session 也走這條路（~3300 次 / 4 GB），C 設定為 0
未證明  renderer 端實際駐留的是哪一部分（fd+mmap、GL texture、兩者）以及為何 XFCE 只多 ~560 個 mapping 而非 ~3300；
        修補後以 mem-guard 記錄的 MemAvailable / swap 曲線與 Activity maps_count 驗證
```

## 5. 關聯

- R10 **D-04**（`activity.maps_count` 跨 session 上飄，OPEN）：G 設定 +555/+563、C 設定 +6——PGA-GAP-3 是最可能的來源，
  修補後以同一個 soft check 驗證（不得事後改 tolerance）。
- PGA-GAP-2（同步等待）：S 模式的 op 成本 19–69 ms 與這裡的整張 memcpy + 新配置 + 記憶體壓力同時發生，
  B.3 的 S 資料在修補前不具代表性；S 模式暫停。

## 6. 最小設計方向（第 2 步，待寫）

在 Done 釋放 upload 之前 `lorieUnregisterBuffer(upload)`（與 D0a cache 路徑相同的規則）；Done 已同步等到
completion（lorieGpuCopyWaitForCompositeOrFatal），此時 renderer 已用完。需確認 direct 分支（exaGpuComp.direct）
的 upload 也同樣處理，以及 Prepare 失敗路徑（InitOutput.c:2994）。
