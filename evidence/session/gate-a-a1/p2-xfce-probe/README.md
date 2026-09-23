# XFCE PRE-FREEZE PROBES — probe-01 / probe-02

DATE 2026-09-23 · PRODUCT `dc94485` / APK `1bd8bef0…b8a3` · SERIAL `10.191.48.13:33331`
（mdns 同時廣播 41637（refused，舊）與 33331（活）——要逐筆試，不能只取第一筆）
Stable `com.termux.x11` `:1` pid 20881 全程未動（stable-before/after.json）。

**這不是 XFCE session。** 計畫書 §11 規定 freeze 之前不得執行任何 XFCE session；這兩次只起
X3 + Activity、跑一個 R10 workload unit（p_r10_ledger）讓畫面有幀，再用 R10 的 terminate 關閉。
不消耗任何 attempt，不判定任何東西，數字是 V2-XFCE-DESIGN-FREEZE 的輸入。

```
script   probe-xfce-env.sh      v2（probe-02 用）
         probe-xfce-env.v1.sh   v1（probe-01 用，sha 7fe0212e…），保留作錯誤留痕
```

## 量到的事實

| 問題 | 結果 | 證據 |
|---|---|---|
| X root | 開機 1280x1024，Activity 綁上後 **1200x2191**（native） | xdpyinfo-pre-activity.txt / xdpyinfo.txt / xrandr.txt |
| extension | GLX、Present、Composite、DAMAGE、DRI3、RENDER、XTEST… 共 24 | xdpyinfo.txt |
| frame timing | `(BLAST)` layer 的 `--latency` 可讀，9 幀，lag 12–18 ms | probe-02/sf-latency-blast-{1,2}.txt |
| GPU busy | kgsl gpubusy 可讀、會動 | gpubusy-*.txt |
| Activity CPU | /proc/<pid>/stat 可讀 | act-stat-*.txt |
| thermal | HAL 區段可讀；Cached 區段是舊值 | thermal-*.txt |
| clean close | 兩次都平衡、c27=1、Activity 存活 | gatea-summary.txt |

## probe-01 的工具錯誤

v1 在 `while read` 迴圈中呼叫 `adb shell`，adb 讀 stdin 把剩下的 layer 名吃掉，只查到第一個
（沒有 buffer 的 Background layer，全 0）。若照 v1 下結論會是「frame timing 不可觀測」——錯的。
v2 加 `</dev/null` 並單獨查 BLAST layer。probe-01 其他檔案不受影響，保留不改。
