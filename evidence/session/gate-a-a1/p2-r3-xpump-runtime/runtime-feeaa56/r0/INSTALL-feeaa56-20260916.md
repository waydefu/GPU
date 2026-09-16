# feeaa56 experimental install — 2026-09-16 stall-notify-function diagnostic

Installed **only** over `com.waydefu.x11gpu`. Never `com.termux.x11`.
Not B-2. Not R7. Frozen `runtime-1f85b80/` / `runtime-27d8d1b/` / `runtime-0d72332/` / `runtime-a7528bd/` not overwritten.

| Field | Value |
|---|---|
| serial | `10.191.48.13:45645` live-fetched via `_adb-tls-connect._tcp.local.` |
| HEAD | `feeaa569b86216126116c9bd99037a014efe0b79` |
| CI | **35076884763** `workflow_dispatch` success |
| APK SHA256 | `a2d92ff9ecb948c5b3ac3c424727d12e97b9991f3b1b68d068a6828d744f3210` MATCH local=staged=installed |
| versionName | `1.03.01-feeaa56-16.09.26` versionCode 15 |
| Build ID | `62d4a3f66adf3326513b7b79868c21c3ad8310f2` MATCH installed arm64 libXlorie |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` CONTINUITY PASS |
| lastUpdateTime | 2026-09-16 17:21:53 |
| pm session | 2016772719 create/write/commit Success |
| Screen | Awake, unlocked |
| HDMI | observe-only; dumpsys showed mDisplayId=0 |
| Stable | `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03 PID **14604** UNTOUCHED |
| Marker strings | `STALL_PHASE phase=` / `NOTIFY_ENTER` / `NOTIFY_EXIT` / `SWAP_ENTER` / `NEXT_FENCE_ENTER` / `x-exa-composite-wait` present |

Replaced experimental `1f85b80` on the device only. Notify-diag source worktree remains `1f85b80`.
R7 remains **NOT STARTED**. B-2 remains **BLOCKED**.
