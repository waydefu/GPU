# Stable 桌面端到端驗收（2026-11-27 03:16–03:18 CST）

## 性質與邊界

這是對 [PR #43](https://github.com/waydefu/GPU/pull/43)／[#44](https://github.com/waydefu/GPU/pull/44) 修正的**事後驗收紀錄**，只做唯讀查驗，沒有送出任何訊號、沒有重啟任何桌面程序。

**重要：** 本次驗收時桌面已經被重啟過，但不是由 `restart-stable-desktop.py` 執行，也不是由本 session 執行；X server、XFCE session 與 desktop tracer 的 pid 都換了新的（見下表）。重啟方式沒有被記錄，因此：

- 「修正後桌面帶有 Android 執行環境變數」**已驗證**。
- `restart-stable-desktop.py --apply` **仍未在真實桌面實跑**，只有 `--dry-run` 與非破壞性測試的證據。
- 由於 X server 本身也換了新 pid，無法作出「Stable X server 在重啟前後不變」的比對；這次是使用者端的重啟，不是本專案腳本造成。

## 驗收結果

| 項目 | 結果 | 證據 |
|---|---|---|
| 新桌面程序 | X server pid `28218`（`termux-x11 com.termux.x11 :1 -legacy-drawing`）、`xfce4-session` `28262`、desktop tracer `28175`；`.X1-lock` 內容 `28218`，X1 socket 與 lock 時間 03:14:39 | `/proc/<pid>/comm`、`.X1-lock` |
| 7 個 Android 變數在新桌面程序中 | `28175`、`28262`、`28218`、`28709`（survivor tracer）、`17875`（`shard-daemon.sh`）與本 shell 均為 7/7 | 逐程序統計 `/proc/<pid>/environ` 中 `ANDROID_ART_ROOT／ANDROID_I18N_ROOT／ANDROID_TZDATA_ROOT／ANDROID_ROOT／ANDROID_DATA／BOOTCLASSPATH／DEX2OATBOOTCLASSPATH` |
| `termux-bg-run` 不借變數 | `TERMUX_BG_RUN_DONE rc=0 elapsed_s=0.14`；原生端執行 `restart-stable-desktop.dryrun.sh`，輸出 `STABLE_RESTART_DRYRUN_PASS (no signal sent)`（腳本內部斷言 `TracerPid == 0`） | `~/.cache/termux-bg-run/run-1795720589-30472.rc` |
| 預檢輸出 | `xserver=28218 socket_inode=812663 session=28262 desktop_tracer=28175 survivor_tracers=16923,17917,27492,28709 old_tracees=44`；現役與 desktop tracer SHA256 皆 `4a6bc67723d9517771ea602e61caa98a4ac7cb7cf75f932d85fa1a5038ae7660` | dry-run 輸出；`sha256sum /proc/28175/exe` |
| main 上的版本即手機上的版本 | `restart-stable-desktop.py`、`.dryrun.sh`、`.apply.sh`、`termux-bg-run` 與 `main`（`1604699`）逐位元組相同 | `cmp` |
| 測試（取自 `main` 的檔案） | `ANDROID_ENV_GUARD_PASS`、`RESTART_STABLE_DESKTOP_TEST_PASS` | 在本桌面實跑 |
| fast9+09c 基準 | 現役 `proot-fast8` SHA256 同上；凍結副本 5/5 OK、現役對凍結清單 5/5 OK | `sha256sum -c` |
| shard daemon | 單一實例 `17875`，只有它握有 `daemon.lock` 與 `ctl.fifo` | HANDOFF 單行檢查的等價版本 |

## 結論

`termux-bg-run` 失效的根因（桌面環境缺 7 個 Android 變數）在目前的桌面上已不存在，修正有效。未驗證的是 `restart-stable-desktop.py --apply` 的實戰行為；它保留為下次正常維護的選做項目，不阻擋任何其他工作。
