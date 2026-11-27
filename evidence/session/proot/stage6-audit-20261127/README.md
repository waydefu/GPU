# Stage 6.1 唯讀基線快照（2026-11-27，本機，未推 GitHub）

三次都是同一支腳本 `src/f8-proot-fast/scripts/android-host-audit-readonly.sh`，經 `termux-bg-run` 在原生端執行，只讀取、未寫入任何 Android 設定。

| 檔案 | 時間 | 省電模式 | 說明 |
|---|---|---|---|
| `audit-baseline-current.txt` | 09:42 | **開**（`low_power=1`） | 檔名的 `current` 指「當時狀態」，不是正常模式；cpu6／7 上限 768 MHz、cpu0–5 上限 2.61 GHz |
| `audit-baseline-normal.txt` | 省電關閉後 | 關（`low_power=0`） | cpu0–5 上限 2.7456 GHz、cpu6／7 上限 2.88 GHz，與 11-26 稽核相同 |

| `audit-baseline-performance.txt` | 使用者切到效能模式後 | 關（`low_power=0`） | `POWER_PERFORMANCE_MODE_OPEN=1`；cpu0–5 上限 3.6288 GHz、cpu6／7 上限 4.608 GHz，等於 `cpuinfo_max_freq` |

三份共通（`POWER_PERFORMANCE_MODE_OPEN` 只有效能那份是 1）：`POWER_PERFORMANCE_MODE_OPEN=0`、`speed_mode=0`；`/proc/pressure/*` 與 `zram0/mm_stat` 即使經 `adb shell` 也 Permission denied（記為 null，不是 0）；ZRAM 取自 `dumpsys meminfo`。

三份都是單次、閒置時的快照，不是 A/B 對照：只證明電源模式會移動頻率上限；`cur` 頻率是當下瞬間值，溫度會受快照前的操作影響，都不能用來比較效能。判定門檻尚未凍結，6.2 的負載測試尚未開始。
