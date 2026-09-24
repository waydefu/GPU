# HANDOFF — 2026-09-24 午：下一步是 3D／GL benchmark（先安裝 glmark2 / vkmark）

**新對話先讀：** 本檔 → `HANDOFF-NEXT-SESSION-20260924.md`（前半天的完整脈絡）→ `evidence/session/gl/GL-FEASIBILITY-01.md`。
不要重讀整棵 evidence 樹。回覆用繁體中文；指令、檔名、verdict token 保持英文。

## 使用者目標
POCO F8 Ultra 真正的 Linux 全域 GPU 加速（不只 Gate A）。先以**內建螢幕**為目標（3440×1440 是理想，螢幕未購買）。
全程不碰 Stable `:1`（`com.termux.x11`），只用實驗版 `:3`（`com.waydefu.x11gpu`）。**不宣稱未經實測的效能提升。**

## 使用者最近的兩個決定（2026-09-24）
1. PGA-GAP-5 修正方向：**依尺寸分流**（≤64×64 的 pixmap 留在 CPU）→ 已實作並驗證（f592241）。
2. 下一階段：**3D／GL 程式與遊戲**。

## 新對話第一件事：安裝 benchmark（使用者已說要在新對話進行）
```
計畫指令     pkg install glmark2 vkmark        （Termux 原生；在 Termux 環境執行，不是 PRoot 的 apt）
安裝前       先查大小與來源（apt-cache show／pkg show），告訴使用者後再裝
             下載屬於需要明確同意的動作：使用者已同意「在新對話中進行安裝」，執行前仍要再確認一次
不要做       不要改系統設定、不要碰 Stable :1、不要從非官方來源下載
```
安裝後的測試腳本可以沿用 fork `tests/gl/gl_feasibility.sh` 的寫法（每種渲染器分別跑、以 rusage 記 client CPU）：
- GL：`llvmpipe`（`LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe`）vs **Zink+Turnip**
  （`MESA_LOADER_DRIVER_OVERRIDE=zink GALLIUM_DRIVER=zink VK_ICD_FILENAMES=<termux freedreno icd>`）
- Vulkan：lavapipe（`lvp_icd.aarch64.json`）vs **Turnip**（`freedreno_icd.aarch64.json`），ICD 都在 `/data/data/com.termux/files/usr/share/vulkan/icd.d/`
- **每個 Vulkan 相關執行都要設 `VK_LOADER_LAYERS_DISABLE=*`**（否則 Zink 因 PRoot 的 Ubuntu 隱式 layer 清單失敗）
- 比較前**先凍結判準**（例如：GPU 版 glmark2 分數 ≥ CPU 版 ×N，且 client CPU ≤ CPU 版 ×M，兩次重複都成立），寫進 `evidence/session/gl/`。
- 在 `:3` 上執行：`evidence/session/gate-a-a1/p2-pga-rca/run-async-proto.sh` 的 `KIND=cmd CMD_SCRIPT=<腳本>`（會起 untraced X3 + Activity、
  mem-guard、Stable 前後比對、以精確 pid 收尾）。

## 目前裝置與產物
```
實驗版            1.03.01-f592241-24.09.26   CI 35937188670   APK f9e35b69…075c   Build ID 1b80cabb…fedf
                  fork waydefu/termux-x11  branch feat/exa-async-proto-20260923（HEAD a8ce018，已 push）
                  worktree src/f8-ahb-exa-async
預設行為          TERMUX_X11_GPU_MIN_PIXELS=4097（≤64×64 不升級 AHB；0 = 舊行為）；TERMUX_X11_EXA_ASYNC=1 選用
ADB               lane 5038，上次 10.191.48.13:41757（會換，一律 mdns 重探：evidence/session/gate-a-a1/runtime/mdns-address-15s.py）
手機黑盒子        /data/local/tmp/f8-blackbox（pid 5963），凍結／重開機後讀 bb.log、events.log
手機方向          必須直向（橫向時 X root 變 2464×783，runner 會正確 BLOCKED）；使用者已關閉自動旋轉
儲存空間          約 30 GB 可用；XFCE 原始 logcat 每次約 1.2 GB（遙測造成），跑完用 gzip 壓縮（見下）
```

## 這兩天的結論（都已實測、判準先凍結）
| 項目 | 結果 |
|---|---|
| 同步 EXA 1–3 ms 的組成 | 主因是 renderer 忙於畫面迴圈沒來拿工作；GPU 本身 ~0.3 ms（PGA-GAP-2-DECOMPOSITION-01.md） |
| 非同步 EXA（11b3b79） | 正確性全過；op 層 client 延遲降到同步的 19–24%（ASYNC_LATENCY_IMPROVED）；XFCE 無改善 |
| PGA-GAP-4 | depth 32（BGRA）當 GPU 目的地時結果回不到 AHB（既有缺陷）→ 改走 CPU，已驗證 |
| PGA-GAP-5 | XFCE 尖峰來自小 pixmap 逐一升級＋登記；依尺寸分流後 **ROUTING_REMOVES_SPIKES**（p99 63–72 → 9–10 ms） |
| 2D 桌面 | 尾端與 CPU 同級，但 p50 仍約 CPU 的 2–3 倍、X CPU 0.5 核 > CPU 模式 0.34 核 → **2D 尚無 GPU 收益** |
| GL／Vulkan 可行性 | 預設 llvmpipe；Zink+Turnip 可在 Adreno 840 跑；demo 數據顯示 client CPU 約減半到 1/5（非結論） |
| Gate A | 預設分流下 oracle V3 correctness 全過、attribution 預期 FAIL（來源都 ≤64×64）；關閉分流 ORACLE_PASS |

## 會咬人的事（這兩天真的踩過）
- **執行緒身分不要猜**：X dix = X3 內被 client 叫醒最多者（X3 的 leader 是 Android Looper）；renderer = Activity 程序的 `Thread-7`。
- **runner 的 exit trap** 要寫成 `cleanup || true; ... || true; mg_stop`（舊 runner 失敗時會把 X3 留著）。
- **logcat 啟動競態**：`start_logcat` fork 後才 exec adb，`verify_logcat_pid` 太早檢查會在 set -e 下無聲結束；衍生 runner 已加 2 s 等待。
- **rca_sampler** 要用 9422f6b 之後的版本（x_rtt 連線失敗會重試）。
- **adb 不能放在 safe-run（RLIMIT_AS）底下**：會卡到 timeout。
- **產物流程**用 `evidence/session/gate-a-a1/p2-pga-artifact/bind-install.sh <sha7> <full_sha> <ci_run> <prev_sha7> "<說明>"`（每欄核對、衍生安裝腳本）。
- XFCE runner 的凍結工具要求產品樹 = bfb5769；衍生 runner（`run-xfce-v3-<sha>.sh`）只放行 `product_tree_unchanged_since_binding` 這一項。
- 大檔：`p2-xfce-runtime/runtime-*/xfce-c0-*/raw-logcat.txt` 壓成 `.gz`（解壓 sha256 與 sha256sums.txt 相同，目錄內有 POST-CAPTURE-CHANGES.md）。
  f592241 那批在本輪結束時已送背景壓縮（腳本在上個 session 的 scratchpad，結果看各目錄的 POST-CAPTURE-CHANGES.md）。

## 還沒做（GL 之外）
- 上屏延遲（GPU 結果仍要等 renderer 下一幀）尚未量；Zink 的呈現推測是 drisw（CPU 複製），DRI3／AHB 零拷貝是可能的下一刀（未證實）。
- burst16 仍約 CPU 3 倍（佇列容量 8 的推測）；PGA-GAP-3 mapping 殘差未解；日常桌面 PRoot 追蹤器負載（daily_sampler v2 未跑）。

## 更新 2026-09-24 12:10 — glmark2／vkmark 已裝、GL-BENCH-02 結果
```
安裝        glmark2 2023.01-3、vkmark 2025.01-3（+assimp、libjpeg-turbo、xcb-util-wm），經 adb run-as com.termux（Termux 是 debuggable）
判準        evidence/session/gl/GL-BENCH-01-FREEZE.md（FROZEN）；GL-BENCH-02-FREEZE.md 原樣沿用
GL-BENCH-01 GL_INVALID／VK_INVALID（放包包，判準段有觸控；凍結）
GL-BENCH-02 GL_GPU_BENEFIT（分數 5.38×／4.86×，每幀 CPU 0.10×／0.11×）、VK_GPU_BENEFIT（3.93×／4.99×，0.18×）；A/A 通過
限制        lavapipe 自身重複差 1.61×（1.5× 門檻不是「遠超雜訊」）；只到 benchmark 800×600，不代表遊戲
工具        fork 8b905a2（本地未 push）tests/gl/gl_bench.sh、gl_bench_judge.py；evidence/session/gl/run-gl-bench.sh（EXPECT_ROOT=1200x2416）
包包模式    evidence/session/gl/exp-pocket-prefs.sh（實驗版按鍵列隱藏／手勢無動作／保持亮屏）目前仍套用中；restore 還原
桌面        「F8 鍵盤列（實驗版）」＝ /usr/local/bin/f8-ekbar-toggle com.waydefu.x11gpu
```
描述（未證實）：Zink 上屏時 X3 吃 55–74 CPU 秒、off-screen 只有 4–5 秒 → drisw CPU 複製是下一刀（DRI3／AHB 零拷貝）的候選。

## 更新 2026-09-24 14:30 — Ubuntu 程式碰到 GPU、Electron 結論
```
Mesa        /opt/mesa-kgsl（自編 26.0.6 Turnip KGSL＋Zink，打 Termux 0017/0018/0019）→ Ubuntu 看到 Adreno 840（MESA-KGSL-UBUNTU-BUILD-01.md）
            關鍵：手機 KGSL 回報 UBWC_MODE=6，上游 26.0.6 只認 1–4 → 沒 0019 就靜默 0 裝置
Electron    GPU 程序啟動即死的根因＝ANGLE 載入 libpci 找不到 /proc/bus/pci 就 exit(1)；libnopci.so 攔截（ELECTRON-GPU-PROBE-RESULT.md）
            ELECTRON-BENCH-01：Cursor V2（Turnip）對 V0 → ELECTRON_GPU_NO_BENEFIT（CPU 0.963×/0.966×；幀／閒置／正確性 OK）
            Cursor CPU 幾乎全在 JS；閒置 0.33 核（未查）
事件        滑掉實驗版 → Gate A x-hup/6 設計停機（整個 :3 session 結束）；EXA「devPrivate.ptr」是非致命警告（INCIDENT-20260924…，開頭有更正）
            兩個唯讀 RCA session 由使用者啟動中（task_7bdaf674 前提錯誤、task_be769d75 前提正確）
工具        fork a4440fa（本地未 push）tests/gl/electron_bench*.{sh,mjs,py}
```

> **2026-09-24 15:00 之後的最新交接：`HANDOFF-NEXT-SESSION-20260924-PROOT.md`**（PRoot 追蹤器開銷、PROOT-BENCH-01 進行中）。
