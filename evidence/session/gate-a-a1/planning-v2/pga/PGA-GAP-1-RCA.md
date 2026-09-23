# PGA-GAP-1 — 熱路徑上的診斷 stamp 讓 X 在真實桌面負載下飽和

DATE 2026-09-23 · PRODUCT `dc94485` · 發現於 `V2-XFCE-BASELINE-RUN`（XFCE-FREEZE-V1，變體 C1）
§13.2 第 1 步（RCA）與第 2 步（root cause proof）。**本文件先於任何修補寫成。**

## 1. 哪一格、哪一份 evidence、哪一個 predicate 為假

```
cell       XFCE-FREEZE-V1 / C1
evidence   p2-xfce-runtime/runtime-dc94485/xfce-c1-03/   (sha256sums.txt 76 檔)
verdict    judge-xfce.py (凍結) → BASELINE_DEFECT
           crash   : terminals_exit_0                 (5 次 close 全部 rc=None：10 s 內沒結束)
           validity: choreo_every_step_ok / choreo_no_step_late / logout_clean
           hard    : 全過（c12..c17 = 560/560 ×3，c18/c19/c20 = 0，c27 = 1，generationFatal 0）
predicate  「XFCE workload 能照凍結時間表執行」為假：
           三個 terminal 的視窗都要 12.3–12.9 s 才映射（上限 10 s），
           之後 terminal 連自己的 pty 都讀不動，term_load.sh 卡在 printf，永遠看不到 close flag。
決策樹     §19.1 Q6 → VALID_FAIL（構造與證據都可信，是產品讓 workload 無法進行）
```

**Gate A 本身沒有錯。** 560 對 AHB／EGLImage／texture 全數平衡、registry 與 lease 歸零、
generation 恆為 1、零 fatal。壞掉的是整個 X 的吞吐量。

## 2. 現象（量測，不是推測）

X3（pid 27324）在整段 session 的 LorieNative 輸出：

```
                    有輸出的秒數   中位數 行/秒   峰值 行/秒   總行數
xfce-c1-03 (XFCE)       337           2123         3494       658,904
r10-a-01   (R10)         12            195          346         2,015
probe-02                  6             21          344           626
```

行種類（xfce-c1-03，前 8 名）：

```
Sprep-pre / Sprep     53,002 × 2   exa PrepareAccess（每次 CPU 存取 pixmap）
Sfb role              48,772       fb 路徑
E0u EXA_UNACCEL_ENTER 24,072       unaccelerated op（glyph 等）
E1 PRE_SWAP / PRE_FB  24,071 × 2
Probe/D0-D3/E0         1,743 × 7   每個 composite
```

XFCE 的文字繪製幾乎全走 unaccelerated 路徑，每個 op 印約 6 行。X 主執行緒採樣時是 `R`。
launcher log 在 6 分鐘內從 17 MB 長到 132 MB（本輪片段），`/tmp/x11gpu-p2a3.snap` 已 133 MB。

## 3. 機制（source）

`p2a2_emit()` 定義在 `lorie/src/main/cpp/patches/dix-config.h.in:222`，**無任何開關**，每呼叫一次：

```
__android_log_print(...)                        liblog → logd
write(2, msg) ; write(2, "\n")                  X 的 stderr = launcher log 檔
open("/tmp/x11gpu-p2a3.snap", O_APPEND|O_CREAT) ← 帶路徑：PRoot 用 ptrace 攔截轉譯
write ; write ; fsync ; close                   ← 每一行一次 fsync
```

呼叫點：`lorie/*.c` 11 處、`patches/xserver.patch` 15 處（exa.c、exa_unaccel.c、exa_render.c、
fb/fbpict.c、miext/damage/damage.c、os/osinit.c、os/backtrace.c）。來源是 P2-A.2/A.3 的
「observe-only」診斷，B.2 時明文「A.3/A.4 stamps left on」，之後一直沒關。

## 4. Root cause proof

`tests/pga/emit_cost.c` 在同一個 PRoot 裡重放 `p2a2_emit` 的 syscall 序列（**不含** liblog，
所以是下限），n = 2000，訊息是 xfce-c1-03 裡真實的一行 `Sprep`（150 bytes）：

```
A 完整序列          mean 331.7 µs   p50 317.0   p95 433.5   → 上限 3,015 次/秒
B 去掉 fsync        mean 175.1 µs   p50 158.6               → 5,710 次/秒
C 只寫 stderr       mean   4.3 µs                           → 234,755 次/秒
D 空迴圈            mean   0.7 µs
```

1. 成本幾乎全在 **snap 檔的 open/close（PRoot 對帶路徑 syscall 走 ptrace 轉譯）＋ fsync**；
   write 本身只要 4 µs。
2. X 在 XFCE 下的實測輸出（中位 2123、峰值 3494 行/秒）**落在或超過**這個 3015 次/秒的下限天花板
   ——也就是 X 主執行緒的時間幾乎全部花在寫診斷行上。
3. 對照組：同一個 artifact、同一個 PRoot，R10-A 與 probe 的峰值只有天花板的 11%，client
   從未餓死。差別只在 workload 會不會大量觸發 fallback 路徑的 stamp。

因此：**client 餓死 ← X 主執行緒飽和 ← 每個 fallback op ≈6 次 p2a2_emit × 每次 ≥332 µs。**
這不是推測：天花板是量出來的，X 的輸出率是量出來的，兩者吻合。

反證條件（若成立則本 RCA 不成立）：若 X 的輸出率遠低於天花板而 client 仍然餓死，根因就在別處。
實測輸出率是天花板的 0.70–1.16 倍，反證不成立。

## 5. 不是根因的東西（已排除）

```
Gate A 協定         counter 全平衡、零 fatal；direct composite 只有 15 次（c0），量級太小
GATEA_EVENT logging 157,676 行 ≈ 470 行/秒，每行一次 liblog write、不開檔、不 fsync
R8_OBS              8,501 行
PRoot 本身          C 變體證明單純 write 只有 4 µs；貴的是「帶路徑的 syscall」
X startup JIT 崩潰  另一件事（xfce-c1-02，VM-JIT 類，R-31），與本缺口無關
```

## 6. 影響範圍

- **任何真實桌面 workload 都跑不動**：XFCE baseline、B.3 的大量 fallback cell、Gate W 全部被擋。
- `/tmp/x11gpu-p2a3.snap` 無上限成長（每輪 ~130 MB）。
- R7–R10 的判定**不受影響**：它們的 judge 不讀這些 stamp（只有新的 XFCE collector 讀
  `Probe ENTER` / `Gcomp FDCLONE`，那份 freeze 綁在 dc94485 上，新 artifact 要新版 freeze）。
- crash 鑑識**不依賴** `p2a2_emit`：`p2a3CrashHandler` 用自己的 `p2a3WriteLine`
  （InitOutput.c:315-325）寫 Uctx／Upid／Uraw／Ssig；`xorg_backtrace` 另有 `ErrorFSigSafe`。

## 7. 下一步（§13.2 第 2 步起）

最小設計：`p2a2_emit` 預設不輸出，只有 `TERMUX_X11_P2A_DIAG` 恰為 `"1"` 時才照舊行為；
crash handler 路徑不動。細節見 `PGA-GAP-1-DESIGN.md`。
