# Stable 桌面實戰重啟驗收（`restart-stable-desktop.py --apply`，2026-11-27 10:06–10:08 CST）

## 性質與邊界

這是 `core-src/f8-proot-fast/scripts/restart-stable-desktop.py`（手機副本 `/data/data/com.termux/files/home/build/proot-fast/tools/restart-stable-desktop.apply.sh`）首次在真實日常 Stable 桌面上執行 `--apply --confirm-stable-restart` 的實戰驗收紀錄。

- 先前在 PRoot（`TracerPid != 0`）直接執行 `.apply.sh` 時，預檢在 line 144 以 `AssertionError: must run natively (TracerPid 0)` 安全中止，未送出任何訊號。
- 實戰前已先關閉從舊桌面開啟的 Antigravity 與 `xfce4-terminal`（其 `f8-shard` wrapper 原本掛在舊桌面 tracer `28175` 底下），再從原生 Termux（`TracerPid=0`）執行 `.apply.sh`。

## 執行紀錄與產物

來源：`/data/data/com.termux/files/usr/tmp/stable-restart-20261127-100640/`

### `stable-runtime.txt`

```text
x11_server=28218
x1_inode=812663
old_xfce_tracer=28175
new_xfce_session=20772
new_xfce_tracer=20766
survivors=16923,17917,27492
survivors_gone=none
sha256=4a6bc67723d9517771ea602e61caa98a4ac7cb7cf75f932d85fa1a5038ae7660
android_env_missing=none
```

### `stable-desktop-session.log` 摘要

- `xfce4-session`（`20772`）與 `fcitx5` / `xfsettingsd` / `xfdesktop` 於 10:06:42–10:06:44 正常啟動完成，X11 連線 `:1.0` 成功。
- 僅見 PRoot 環境預期之無 system D-Bus / `upower` / `colord` / `polkit` / `logind` / `/proc/self/mountinfo` 非致命警告。

## 新桌面端到端複檢（2026-11-27 10:07–10:08 CST）

| 項目 | 結果 | 證據 |
|---|---|---|
| `termux-bg-run` 不借變數 | `TERMUX_BG_RUN_DONE rc=0 elapsed_s=0.14`；輸出 `NATIVE_PIDFD_PROBE_PASS` 與 `STABLE_RESTART_DRYRUN_PASS (no signal sent)` | `/usr/local/bin/termux-bg-run --timeout 120 --tail 40 .../restart-stable-desktop.dryrun.sh` |
| Stable X11 伺服器不變 | `xserver=28218`、`socket_inode=812663`、`.X1-lock=28218`、命令行 `termux-x11 com.termux.x11 :1 -legacy-drawing`（重啟前後完全一致） | `stable-runtime.txt`、新桌面預檢輸出、`/proc/28218/cmdline`、`.X1-lock` |
| 新 XFCE session 與 tracer | `new_xfce_session=20772`、`new_xfce_tracer=20766`；`sha256sum /proc/20766/exe` = `4a6bc67723d9517771ea602e61caa98a4ac7cb7cf75f932d85fa1a5038ae7660` | 新桌面預檢輸出、`/proc/20766/exe` |
| 獨立 shard 存活 | `survivors=16923,17917,27492`、`survivors_gone=none`（Hermes、ADB `-P 5038`、PulseAudio 皆保留；重開後 Antigravity shard `21784` 亦在線） | `stable-runtime.txt`、`/proc/<pid>/comm` |
| 7 個 Android 執行環境變數 | `xserver`（`28218`）、`new_tracer`（`20766`）、`new_xfce`（`20772`）與新桌面 shell 皆 `7/7`；`android_env_missing=none` | `/proc/<pid>/environ`、`stable-runtime.txt` |
| `shard-daemon.sh` | 單一實例 `17875` 持續在線 | `/proc/*/cmdline` |

## 結論

`restart-stable-desktop.py --apply` 已在真實 Stable 桌面完成實戰驗證：可在**不觸碰 Stable X11 `:1` 伺服器（`28218`）與獨立 shard（`16923`, `17917`, `27492`）**的前提下，安全回收舊桌面 tracer（`28175`）並以現役 `fast9+09c` 及完整 7/7 Android 執行環境變數拉起新 XFCE session（`20772` / `20766`）。
