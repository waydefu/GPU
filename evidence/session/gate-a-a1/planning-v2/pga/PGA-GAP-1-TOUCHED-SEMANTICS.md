# PGA-GAP-1 — touched-semantics audit：dc94485 → bfb5769

方法同 GAP-4 / D-12：逐行判讀產品 diff，列出每個被碰到的符號，對每個 R 系列 predicate 問
「它的判定輸入有沒有被改變」。**先於任何新 artifact 的 runtime 結果寫成。**

## 1. 產品 diff

```
git diff --stat dc94485 bfb5769 -- lorie app shell-loader build.gradle settings.gradle gradle .github
  lorie/src/main/cpp/patches/dix-config.h.in | 20 +++++++++++++++++++-   （唯一的產品檔）
其餘 41 個檔全部在 tests/（xfce、pga）
```

touched 符號：

```
p2a2_emit          + 一行 gate：!p2a2_diag_enabled() 時提早 return
p2a2_diag_enabled  新增，static，讀一次 getenv("TERMUX_X11_P2A_DIAG")
#include <stdlib.h> 新增（getenv 的宣告）
```

`p2a2_emit` 無回傳值、不改任何產品狀態，唯一副作用是 liblog / stderr / snap 檔三種輸出。
旗標開啟（"1"）時的行為逐字不變（host 測試 `ON` 情境：2 liblog / 8 write / 2 fsync，與 dc94485 相同）。

## 2. 26 個呼叫點（旗標關閉後不再輸出的行）

```
lorie/InitOutput.c    R3 stamp · Probe ENTER/RETURN · InstallProbe ×2 · Gcomp Prepare TRUE/FALSE ×3
                      · Gcomp FDCLONE · Gcomp RECT · Gcomp Done                              （11）
xserver.patch         D0–D3（damage.c）· E0（exa_render.c）· E0u/E1（exa_unaccel.c）· Sprep/Sprep-pre
                      （exa.c）· Sfb（fbpict.c）· osinit · Sbt（backtrace.c）                   （15）
```

## 3. 誰在讀這些行

```
tests/r8  tests/r9  tests/r10  tests/p2  tests/common   → 0 處（grep Probe/Gcomp/Sprep/Sfb/E0/E1/D0/Sbt/p2a2）
tests/xfce/xfce_collect.py                             → Probe ENTER（composite_total）、Gcomp FDCLONE（d0a_staged）
                                                         ← XFCE-FREEZE-V1 綁在 dc94485；V2 改來源（見下）
R9 讀的 LorieNative 行                                 GATEA_BIND（activity.cpp:236 log()）、
                                                         GATEA_VALIDATE（renderer.cpp:369 log()）→ 不經 p2a2_emit
GATEA_FATAL_HALT                                       lorie.h:1415 __android_log_print → 不經 p2a2_emit
崩潰鑑識 Uctx/Upid/Uraw/Ssig                           p2a3WriteLine（InitOutput.c:315）→ 不經 p2a2_emit
```

## 4. 裁決（依授權直接簽）

```
R0–R6    CARRY_FORWARD   判定輸入不含任何 p2a2 行
R7       CARRY_FORWARD   judge-r7 讀 fatal halt / GATEA_*；13/13 predicate 所在的程式碼一行未動
R8       CARRY_FORWARD   judge-r8-v2 讀 R8_OBS / GATEA_*；claim scope 原樣（無 -noreset）
R9       CARRY_FORWARD   讀 GATEA_BIND / GATEA_VALIDATE / 事件 / epoch record，皆不經 p2a2
R10      CARRY_FORWARD   讀 counter / 事件 / 取樣器，皆不經 p2a2
smoke    R8-D + R8-P2（D-12 先例：一個 clean close、一個 fatal 路徑），在新 artifact 上各跑一次
XFCE     V1 不適用新 artifact → XFCE-FREEZE-V2（先凍結、後執行）
```

**唯一會改變行為的地方是「輸出量」**：這正是修補的目的，也是 XFCE 要驗證的東西。

## 5. 已知副作用

- `xorg_backtrace` 的 `Sbt` 行不再進 logcat（`ErrorFSigSafe` 的 `(EE)` 版本照常進 stderr /
  launcher log）。XFCE runner 從本輪起每輪保存 launcher log 片段，所以崩潰鑑識不受影響。
- `p2a2_emit` 在 signal context（xorg_backtrace）裡第一次呼叫時可能執行 getenv。bionic 的 getenv
  是對 environ 的唯讀掃描、不取鎖；而且只有旗標開時才會走到輸出。可接受。
- `/tmp/x11gpu-p2a3.snap`（已 133 MB）不再成長，除非崩潰或旗標開。舊內容保留不刪。
