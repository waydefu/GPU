# RCA-XFCE-2 — bfb5769 上 XFCE workload 仍無法執行：是 harness 的拓樸，不是產品

DATE 2026-09-23 · PRODUCT `bfb5769`（PGA-GAP-1 已修）· FREEZE `XFCE_DESIGN_FROZEN_V2`

## 1. 觸發

```
xfce2-c1-02   凍結 judge → BASELINE_DEFECT
              crash    terminals_exited（close 的 rc 為 None）
              validity choreo_every_step_ok / choreo_no_step_late
              hard     全過：c12..c17 560/560、registry/lease 0、c27=1、零 fatal
              diag_stamps_absent = PASS（0 行）→ PGA-GAP-1 修補在實機生效
series-v2     依 §19 在第一個非 VALID 停下
```

PGA-GAP-1 的效果是真的：同一個 workload 在 dc94485 上 X 只做了 1011 個 composite、468 幀；
在 bfb5769 上是 7903 個 composite、3322 幀（SF p50 16.7 ms）。但 T2/T3 的視窗仍在 10 s 內找不到。

## 2. 量測（RCA 對照實驗，非 baseline，永不與 baseline 合併）

同一個凍結 V2 workload（C1），兩個 arm，各配 `tests/pga/rca_sampler.py`：

```
                         G（照凍結，EXA GPU 開）   C（TERMUX_X11_DISABLE_EXA_GPU=1）
X 往返（GetInputFocus）
  XFCE 之前（只有 X+Activity） p50 0.25 ms          —
  choreography 期間     p50 18.5  p90 58.5          p50 15.3  p90 31.1
                        p99 470   max 671 ms        p99 95    max 167 ms
xdotool search（choreo 用的查找）
  p50 / max             13.4 s / 18.9 s             5.6 s / 15.4 s
  > 3 s（choreo 的單次上限）12/13                  14/18
X dispatch 執行緒       69% S:do_epoll_wait（閒置）  76% S:do_epoll_wait
                        12% ptrace_stop · 6% hrtimer_nanosleep
CPU（核）               X 0.31 · 所有 XFCE client 合計 < 0.03（兩 arm 相同量級）
```

判讀：

1. **中位數延遲在沒有任何 GPU 工作時也存在**（C arm p50 15.3 ms，是 idle 的 60 倍），而 X
   大部分時間是閒置的——延遲不是 X 忙出來的。
2. X 執行緒有 ~12% 的樣本停在 `ptrace_stop`：**X3 被 PRoot 追蹤**（`TracerPid` = proot 20859；產品
   log `Tracer detected`）。整個 PRoot 只有一個 tracer，它同時服務使用者的日常桌面 client、Claude
   本身、以及我們的 XFCE session。
3. Stable `:1` 的 X **不被追蹤**（`TracerPid: 0`）：它的 shell 先 fork 出 termux-x11 再 `exec` 成
   proot，proot 從未 attach 它。**產品在真實使用時的拓樸是「X 不被追蹤、client 在 PRoot 內」**；
   harness 量到的是「X 也被追蹤」——不代表產品。
4. GPU arm 的**尾端**確實較差（p90 2×、p99 5×）。這是 EXA `Done*` 的同步完成等待
   （`lorieGpuCopyWait`：`usleep(200)` 輪詢，InitOutput.c:1946；renderer 最多 8 ms 才重看佇列，
   lorie.h:673）的真實成本 → 交給 B.3 量化、Gate H 判斷，不在此下產品缺陷結論。

## 3. 分類（§19.1）

```
Q5 → INVALID_CONSTRUCTION：凍結 workload 的構造（X3 在 PRoot tracer 下執行，choreo 依賴每次 3 s 內完成的
     xdotool search）在這個 harness 裡不成立——全 CPU 對照組同樣做不到，所以失敗不能歸因於產品。
xfce2-c1-02 的凍結 classifier 仍是 BASELINE_DEFECT，不改寫；本文件記錄它「不可歸因於產品」的依據。
```

## 4. 修正：讓實驗 X 以產品拓樸執行

`p2-runtime-phase1/runner/start-x3-untraced.sh`：用 Termux 自己的 app_process `am`（以 Termux
uid 執行）啟動 app 內部的 `TermuxService`（`com.termux.service_execute`），命令成為 Termux app
的子程序，不在 proot 樹內。

```
驗證（p2-xfce-probe/probe-03）  X3 PPid 8415（com.termux）· TracerPid 0 · 無 "Tracer detected"
                                idle RTT p50 0.37 ms · clean close 正常 · Activity 存活
產品語意                        tracer 偵測只決定是否替 X 的子程序設 LD_PRELOAD=libtermux-exec
                                （cmdentrypoint.cpp:458-460），不影響 render 路徑
                                → R7–R10 在被追蹤狀態下取得的正確性證據不受影響
安全                            `bash -c`（非 login，不讀使用者 profile），環境變數明確傳入且只允許
                                純 token（--esa 以逗號分隔）；不碰 Stable
```

## 5. 同時發現的環境問題

**probe-03 在螢幕已暗、鎖屏時執行**：Activity surface 變成 1200×2464、X root 1200×2239、renderer 0 幀、
workload 的 composite 沒有被 Gate A 處理。probe-03 對「untraced 啟動可用」仍有效，其餘量測無效。
現有 runner 只在 install 時檢查螢幕，**執行時不檢查** → V3 runner 在 preflight 與收尾都檢查
`mWakefulness=Awake` 與 `isKeyguardShowing=false`，中途暗掉 = INVALID（環境），不是產品結果。

## 6. 下一步

XFCE-FREEZE-V3：與 V2 只差「X3 啟動拓樸（untraced）」與「螢幕狀態檢查」；workload、時間表、
所有 timeout（含 10 s 視窗查找）與判準不變。需要裝置解鎖且螢幕保持亮著才能執行。
