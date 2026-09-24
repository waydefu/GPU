# ELECTRON-GPU-PROBE — Cursor（Chrome 144）的 GPU 程序能不能用 Adreno 840（2026-09-24，探索性，非判準 cell）

## 結論
**能。**加上 libpci 攔截器（`libnopci.so`）與 `/opt/mesa-kgsl`，Cursor 在實驗版 X `:3` 上，Chromium 自己回報：
- V1（ANGLE→EGL→Zink）：`ANGLE (Mesa, zink Vulkan 1.4(Adreno (TM) 840 (MESA_TURNIP)), OpenGL ES 3.2 Mesa 26.0.6)`
- V2（ANGLE→Vulkan）：`ANGLE (Qualcomm, Vulkan 1.4.335 (Adreno (TM) 840 (0x44050A31)), turnip Mesa driver-538.0.6)`
- 兩者 `gpu_compositing`、`rasterization`、`2d_canvas`、`webgl`、`webgpu`、`opengl` 都是 `enabled`；影片編解碼仍是 software。
**這只證明「路通了」，還沒證明變順或省 CPU**——沒有量任何互動負載。

## 根因：09-09「Electron 開 GPU 會空轉／失敗」的真正原因
probe-01（無攔截器）V1／V2 的 GPU 程序每次啟動都退出（`exit_code=256`＝`exit(1)`），崩潰到上限後主程序 `FATAL: GPU process isn't usable. Goodbye.`（SIGTRAP）。
每次退出前最後一行都是 `pcilib: Cannot open /proc/bus/pci/devices`：ANGLE 以 dlopen 載入 `libpci.so.3` 列舉 GPU，
PRoot／Android 沒有 PCI 匯流排，libpci 預設錯誤處理直接 `exit(1)`。**不接新驅動（Ubuntu 原本 Mesa）也一樣崩潰**，所以與 GPU 驅動無關。
修法：`/root/build/electron-probe/nopci/nopci.c`——LD_PRELOAD 攔截 `dlopen`，名稱含 `libpci.so` 時回傳 NULL；ANGLE 會跳過 PCI 列舉。
（`libdiag.so`＝同一攔截＋gpu-process 呼叫 exit／_exit 時印堆疊，僅供診斷。）

## probe-02（`electron-gpu-probe-02`；runner 層級全部正常）
`CMD_CAPTURED`；Stable 前後相同；螢幕亮、無鎖屏；mem-guard 未觸發；每組結束後 `survivors_killed=0`，最後沒有殘留 Cursor 程序。
每組 GPU 程序唯一一次結束都是收尾送的 SIGTERM（`exit_code=15`，約第 50 秒），期間沒有崩潰。

| 組 | 攔截器 | 驅動 | Chromium 回報的 GL | 合成／光柵 | GPU 程序閒置 20 s 的 CPU（描述） |
|---|---|---|---|---|---|
| V0 日常 `--disable-gpu` | 無 | — | `Disabled` | software | 0.35 s（約 0.02 核） |
| V1 `--use-angle=gl-egl` | 有 | mesa-kgsl（Zink） | Zink on Adreno 840 | **enabled** | 5.50 s（約 0.28 核） |
| V2 `--use-angle=vulkan` | 有 | mesa-kgsl（Turnip） | Turnip Adreno 840 | **enabled** | 2.92 s（約 0.15 核） |
| V3 GPU 開、Ubuntu 原本 Mesa | 有 | llvmpipe（CPU） | llvmpipe | 名義上 enabled（實為 CPU） | **52.64 s（約 2.6 核）** |

- V3 對照組說明：只修 libpci 而不換驅動，Chromium 會把 llvmpipe 當 GPU 用，GPU 程序閒置就吃掉約 2.6 核——這很可能就是 09-09 看到的「gpu-process 原地空轉」。
- V1／V2 的閒置 CPU 高於 V0（0.15–0.28 核對 0.02 核）；量測窗在啟動後第 30–50 秒，可能還在載入，**未作結論**。
- V2 比 V1 少一層（不經 Zink），閒置 CPU 也較低 → 下一步優先以 V2 當候選。

## 過程中的錯誤（照實記錄）
- 本機 headless 除錯時，我以 `$!` 當 pgid 結束程式，實際 pgid 不同，**4 組除錯用 Cursor（約 5.3 GB）殘留**，導致 probe-02 第一次等記憶體逾時
  （`electron-gpu-probe-02.wait-timeout-leak.log`）。已依 `--user-data-dir=/root/build/electron-probe/*` 以精確 pgid 結束，
  使用者自己的 Cursor（`/root/.cursor-data`）未受影響；腳本收尾加上殘留檢查。
- probe-01 第一次啟動因主機可用記憶體 < 4500 MB 被 runner 擋下（`electron-gpu-probe-01.blocked-host-memory.runner.log`）。
- `safe-run.sh` 拒絕時印訊息的 `$1` 未定義（set -u）——判斷正確、訊息不完整；該工具的雜湊記錄在其他證據中，未修改。

## 下一步（需先凍結判準）
在 `:3` 上以 V2 對 V0 比較實際互動：捲動長檔案、打字、開關分頁時的 CPU（Cursor 全部程序＋X3）、幀時間、閒置穩定後的 CPU，
以及畫面正確性；兩次重複、A/A 對照，門檻以 A/A 實測波動為依據（見 GL-BENCH-02 的教訓）。

## 補記（使用者回報）
probe-02 期間畫面跳出幾個通知，使用者手動按掉（種類與時間點未記錄；這個探測腳本沒有錄觸控）。
Chromium 自我回報的 GPU／功能狀態是啟動時決定，不受影響；「閒置 20 s CPU」一欄可能受互動影響，本來就只作描述。
正式比較時要沿用 GL-BENCH 的觸控錄製，有觸控即 INVALID。
