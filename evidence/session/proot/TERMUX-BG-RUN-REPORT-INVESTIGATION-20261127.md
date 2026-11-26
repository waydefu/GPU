# termux-bg-run 失效調查（2026-11-27）

僅診斷，未修改任何檔案、未 kill 任何 process、未碰 adb、未碰 `com.termux.x11` / `:1`。
探針目錄：`/data/data/com.termux/files/usr/tmp/bgrun-probe-20261127-015000/`（僅此目錄內新增檔案）。

## 結論摘要（主代理複核後，取代下方子代理的原始假設排序）

**根因 PROVEN：現役桌面工作階段遺失 Android runtime 環境變數，Termux `am` 的 `app_process` 啟動後約 5 ms 靜默退出，intent 從未送出。TermuxService 本身正常。**

1. `restart-desktop.py:178-184`（`/data/data/com.termux/files/home/build/proot-fast9-09c-20261127.yXdNteSr/`）以手寫的 5 個變數（`PATH`、`HOME`、`PREFIX`、`TMPDIR`、`PD_PROOT_BIN`）啟動 Stable 桌面（`launcher_pid=24811`）。`ANDROID_ART_ROOT`、`ANDROID_I18N_ROOT`、`ANDROID_TZDATA_ROOT`、`ANDROID_ROOT`、`ANDROID_DATA`、`BOOTCLASSPATH`、`DEX2OATBOOTCLASSPATH` 七個變數因此遺失，之後由這個桌面啟動的所有程式都繼承這個缺損環境。
2. 環境比對（`/proc/<pid>/environ` 中 `BOOTCLASSPATH|ANDROID_ROOT|ANDROID_DATA` 計數）：舊 tracer 16923、`shard-daemon.sh` 17875、`com.termux` 16964 皆為 3；新桌面 tracer 24811 與 claude-desktop shard tracer 26094 皆為 0。
3. 對照實驗（同一 shell、不觸發 service）：`am bogus-subcommand` 在缺損環境下 rc=0、無任何輸出；只補 `BOOTCLASSPATH`/`ANDROID_ROOT`/`ANDROID_DATA` 三個仍然靜默；從 16923 補齊上述 7 個變數後印出 `Activity manager (activity) commands provided by the com.termux app.` usage，rc=1（Java 端確實執行）。
4. 端到端驗證（launch 3/6）：`env <7 vars> /usr/local/bin/termux-bg-run --timeout 30 probe.sh` → `TERMUX_BG_RUN_DONE rc=0 elapsed_s=0.08`；`marker.txt` 顯示 `uid=10365(u0_a365)`、`TracerPid: 0`。另一次（launch 4/6）確認 TermuxService 子程序本身帶有這些變數（計數 2/2）。
5. 因此子代理假設 1（TermuxService 不再派送）**REFUTED**；假設 2（am 靜默）與假設 3（PRoot 呼叫端狀態改變）由本根因解釋；09b 與 09c 對照同樣失敗，是因為兩者都從同一個缺損桌面環境呼叫，與 tracer 版本無關。
6. 影響範圍：在現役桌面內呼叫 Termux `am`（含 `termux-bg-run`、任何 `termux-*` 經 `am` 的工具）都會靜默失敗。從 Termux:Widget 或 Termux 終端原生啟動的流程不受影響。下一次以正常途徑（`f8desk`／小工具）重啟桌面即恢復。
7. 調查階段未修改任何現役檔案，未重啟桌面；`restart-desktop.py` 保持原樣。
8. **修正（使用者核准後，2026-11-27）**：`/usr/local/bin/termux-bg-run` 在呼叫 `am` 前檢查上述 7 個變數，缺任一個即以 exit `4` 立即結束並列出缺少的變數（不再靜默等到逾時）。原檔備份 `/usr/local/bin/termux-bg-run.bak-20261127`（SHA256 `1d03735c…`）。驗證（launch 5/6）：
   - 缺損環境（應為紅）：exit `4`，0.09 s，cache 檔數 66 → 66（未建 wrapper、未呼叫 `am`）。
   - 只補 3 個變數：exit `4`，列出其餘 4 個。
   - 補齊 7 個變數：`TERMUX_BG_RUN_DONE rc=0 elapsed_s=0.09`，`marker.txt` 顯示 `TracerPid: 0`。
   - `termux-native-runner` skill（`~/.claude`、`~/.hermes`、`~/.gemini/config` 三份）同步補上 exit code 表與此陷阱。
9. **版本管理**：兩個腳本原本只在手機上。已提交 [waydefu/GPU PR #43](https://github.com/waydefu/GPU/pull/43)，分支 `fix/termux-am-android-env`：`0195194` 原樣匯入部署版本（保留錯誤版本），`b8de28d` 修正兩支腳本並新增 `tests/test_android_env_guard.py`。最終審查時把 `restart-desktop.py` 從「繼承整個 `os.environ`」收窄為允許清單：只從呼叫端帶入 7 個 Android 變數，加上原本 5 個覆寫值，避免呼叫端的秘密與 `LD_*`／`PROOT_*` 進入 Stable 桌面；缺任一變數即在 `pidfd_open(session)`／SIGTERM 之前中止。非破壞性測試：`termux-bg-run` exit 4、環境區塊單獨執行（不含任何 `Popen`／`pidfd_*` 呼叫）、AST 順序檢查、整支腳本在 run 目錄外執行必須失敗且 Stable X server 與 XFCE session 的 pid 和 start time 不變。紅色對照：原版（無檢查）、繼承整個 `os.environ` 版（洩漏測試 FAIL）、檢查移到 SIGTERM 之後（順序測試 FAIL）。手機上 run 目錄內的原檔保持原樣，作為實際執行紀錄；正式桌面重啟驗收留待下一次正常維護。

---

以下為子代理（Haiku）原始調查紀錄，保留原文。

## 子代理原始結論

分類 **B**：`am startservice` 回傳 exit 0，但 TermuxService 沒有執行探針腳本（無 `marker.txt`、無 run log、無 rc）。
am 本身對無效子命令也靜默回傳 0，因此「am exit 0」不能作為 intent 已送達的證據。
失效起點與 2026-11-27 00:47–00:48 的 `restart-desktop.py` 兩次嘗試重疊；但因果未證實。

## Step 1：讀取的內容

- `/usr/local/bin/termux-bg-run` 全文：wrapper 寫入 `CACHE_DIR/wrap-<ts>-<pid>.sh`，`am startservice ... -d file://<wrapper>`，以 inotify + 2 s select 等待 `run-<stamp>.rc`，`finally` 刪除 wrapper。
- `termux-native-runner/SKILL.md`：要求由 PRoot 以外執行的 TermuxService 路徑；腳本必須位於 `/data/data/com.termux/`。
- 證據 1（`FAST9-09C-LIVE-QUALIFICATION-20261127.md:43`）：「桌面工作階段切換後，原 `termux-bg-run` 路徑未收到 TermuxService 執行回報。以相同啟動方式對照 09b 與 09c 皆未出現執行標記」。
- 證據 2（`STAGE5-FAST9-LIVE-DEPLOYMENT-AND-SOAK30M-20261126.md:52`）：「透過原生 `termux-bg-run`（`TracerPid=0`）執行部署，耗時 `6.64s`，`rc=0`，輸出 `DEPLOY_PASS`」。

## Step 2：環境事實

- `grep TracerPid /proc/self/status` → `TracerPid:	26094`（本 agent 的 shell 在 PRoot 內，TracerPid 非 0，與 launcher 的呼叫方式一致）。
- `ls -la /data/data/com.termux/files/usr/bin/am` → `-rwx------ root:root 700 1.4K`；`head -5` 顯示為 `sh` script，`exec /system/bin/app_process ... com.termux.termuxam.Am "$@"`。
- `am.apk`：580170 bytes，`zipfile.testzip()` 回傳 `None`，sha256 `fe4a39b01c8efd633364bb1916828cb409dd4f3872f1405675127b50a877c039`，11 個 entry，含 `classes.dex`。
- cache 目錄 `/data/data/com.termux/files/home/.cache/termux-bg-run/` 共 62 檔。最新 rc / wrapper 時間線（檔名 stamp 與 mtime 對得上）：

| 時間（+0800） | 檔案 | 內容 / 說明 |
|---|---|---|
| 2026-11-26 22:28–22:30 | `run-1795703287/320/374/418-*.log/.rc` | 有 log 與 rc；22:30:22 的 log 含 `LIVE_3B_ALL_DONE`、`DAEMON_PROCS=17875` |
| 11-26 23:58 – 11-27 00:24 | 多個 `run-*.rc` | 只有 rc、無 `run-*.log`（推測呼叫端用 `--log-file` 指到別處） |
| 11-27 00:35–00:45:35 | 多個 `run-*.rc` | 最後一個 rc=0：`run-1795711513-19919.rc`（00:45:35） |
| 11-27 00:47:04.722 | `run-1795711623-23790.rc` = `1` | 與 `restart-desktop.log`（00:47:04.710）時間吻合 |
| 11-27 00:48:14.958 | `run-1795711692-24759.rc` = `1` | 與 `restart-desktop-retry.log`（00:48:14.946）吻合 |
| 11-27 00:48:12.234 | `wrap-1795711692-24759.sh` **殘留** | 正常情況 `finally` 會刪除；此檔未被刪除，表示 launcher 的 Python process 未走到 `finally` |
| 00:48:14 之後 | 無新 `run-*.rc` | 至 01:49 為止，cache 內沒有任何完成的 bg-run 紀錄（我的探針不產生 rc） |

- `restart-desktop-retry.log` 內容：`STABLE_DESKTOP_LAUNCH launcher_pid=24811` 後拋出 `AssertionError: ('process identity changed', 22266)`（`restart-desktop.py` line 197 → line 61 `assert_original(codex_tracer)`）。
- 00:55 之後的長時間任務改走 `f8-shard`（`sharded-soak-launch.txt`：`via=daemon`），`sharded-preflight.log` 顯示 `SHARDED_SOAK_PREFLIGHT_PASS`，`sharded-soak.rc` 於 01:25:41 寫入。這表示 native 執行的替代路徑在 00:55 後仍可用（我未讀該 rc 的數值）。
- `/proc/uptime` 顯示 124 s，與 days 前啟動的 process 不一致，`/proc/stat btime` 亦不可信（符合 memory 中「PRoot 內 /proc/stat 不可信」），因此無法用 /proc 推算 TermuxService 重啟時間。
- `com.termux` 主 process（pid 16964）存在，狀態 S；`termux-x11 :1`（pid 30202）存在，未觸碰。
- `dumpsys` 不存在（rc=127）。

## Step 3：探針

`/data/data/com.termux/files/usr/tmp/bgrun-probe-20261127-015000/probe.sh`，寫入 `marker.txt`（date、id、TracerPid、PREFIX），`chmod +x`。

## Step 4：Launch 記錄（共 2/6）

**Launch #1**：`/usr/local/bin/termux-bg-run --timeout 30 <probe>/probe.sh`
- 起訖：01:49:37.0 → 01:50:07.6（約 30.6 s）
- stdout：`TERMUX_BG_RUN_TIMEOUT timeout_s=30 elapsed_s=30.00 rc_file=/data/data/com.termux/files/home/.cache/termux-bg-run/run-1795715377-5380.rc log_file=.../run-1795715377-5380.log`
- stderr：空；exit code：**124**（`am startservice` 未失敗，因為沒有 `ERROR: am startservice failed`）
- `marker.txt`：不存在
- 新 rc / log：無。cache 目錄 mtime 於 01:50:07.56 更新，代表 wrapper 被建立並被 `finally` 刪除（符合程式流程）。

**Launch #2**（raw am，與腳本相同參數，直接指向 probe.sh）：`am startservice --user 0 -n com.termux/com.termux.app.TermuxService -a com.termux.service_execute -d file://<probe>/probe.sh --ez com.termux.execute.background true`
- 01:50:18.30 → exit **0**（耗時約 0.26 s）
- stdout、stderr 皆空
- sleep 10 s 後 `marker.txt` 仍不存在

**非 launch 的 am 探測**（不呼叫 startservice，不計入配額）：
- `am --version` → `0.8.0`，rc=0
- `am`（無參數）→ rc=0，stdout/stderr 皆空
- `am bogus-subcommand` → rc=0，stdout/stderr 皆空（對無效子命令仍無任何輸出，正常 CLI 通常會報錯，這是本次最關鍵的異常）

**Logcat（唯讀）**：
- 本次 am 呼叫對應 `D/AndroidRuntime(7520): START com.android.internal.os.RuntimeInit uid 0` 於 01:50:18.543，`I/app_process(7520): hook_module_exit libgui_unisoc_utils.so over` 於 01:50:18.549。整個 app_process 生命週期約 6 ms。
- 01:50:10 之後，非 avc 的行中沒有任何 `ActivityManager`、`TermuxService`、`termuxam`、`Background`、`not allowed` 等字樣；只有我自己的三次 am 呼叫產生的 `RuntimeInit` 行。
- 注意：logcat main buffer 只剩今天的 4 筆 `RuntimeInit START`（01:49:37、01:50:18、01:50:33、01:50:39），無法比對 00:45 成功時的 am 記錄（buffer 已被 avc 洪水或其他因素清掉）。

## Step 5：分類

**B**：am 回報成功（exit 0 / 非 3），但沒有 marker，也沒有 wrapper 執行痕跡（無 log、無 rc）。
- 不是 A：am 沒有 exit 3，也沒有 stderr。
- 不是 C：沒有 marker，所以腳本沒有跑。
- 不是 D：沒有 marker，也沒有 DONE。

## Step 6：深入（B）

1. **raw am 直接指向 probe.sh**：已執行（Launch #2），仍無 marker。
2. **wrapper 是否可從 native 端讀取**：建立了 wrapper 副本 `<probe>/wrap-copy.sh`（mode 755，內容同 termux-bg-run 的格式，指向 probe.sh）。`ls -la` 可見。但 native 端是否實際能讀，無法在不啟動的情況下證實。Launch #1 的 wrapper 與 Launch #2 的 probe.sh 兩種形式都失敗，所以「wrapper 路徑不可讀」不是唯一解釋，也不足以解釋全部。
3. **am 是否印出任何訊息**：完全沒有（見上）。
4. **am 本身是否啟動**：`app_process` 有啟動（logcat 有 RuntimeInit START），但 Am main 的輸出未出現在 stdout/stderr，也沒有 AMS 日誌。
5. **TermuxService 狀態**：com.termux 主 process 存在，但無法查 TermuxService 的 ServiceRecord（dumpsys 不可用）。

## Ranked hypotheses

1. **LIKELY**：am 把 intent 寫入 binder 後，TermuxService 沒有派送，或派送後被丟棄；失效與 00:47–00:48 的桌面重啟（`restart-desktop.py` 兩次失敗，第二次留下殘留 wrapper）同時期開始。證據：B 類現象、00:48 之後 cache 無任何完成紀錄、長任務改走 f8-shard 後 native 路徑仍可用（代表問題在 bg-run 這條路，而非整個 native 執行環境）。**未證實**。
   - 測試：由使用者在 Termux native shell（PRoot 外）手動執行一次同樣的 `am startservice`（一次性、不由我執行）。若 native 也無 marker，則 TermuxService 本身；若 native 有 marker，則問題在「從 PRoot tracee 呼叫」這一層。
2. **LIKELY（現象已證實，原因未證實）**：am 的 Java 端或其輸出通道失效，對無效子命令也靜默 exit 0，所以 am 的 exit code 不可信。已證實：`am bogus-subcommand` 無任何輸出、rc=0；apk 完整（testzip OK）。未證實：是 Am main 未執行、stdout 被吃掉，還是 vendor hook（`libgui_unisoc_utils.so`）提早結束 process。
   - 測試：在 native shell（使用者執行）比對 `am bogus-subcommand` 的輸出；若 native 會報錯而 PRoot 內不會，則問題在 PRoot 內呼叫 app_process 的路徑。
3. **UNTESTED**：從 PRoot tracee（TracerPid≠0）呼叫 `am` 時，intent 或 binder 呼叫被 PRoot 影響。證據反面：00:45 之前同樣由 PRoot 呼叫並成功（rc=0 紀錄存在），所以這需要 00:47–00:48 之後的某個狀態改變（新的 `proot-fast8 --kill-on-exit` launcher pid 24811 等），而非一般 PRoot 呼叫方式本身。未測。
   - 測試：同上，由使用者在 native shell 執行一次。
4. **PROVEN（殘留）/ 原因 UNTESTED**：00:48:12 的 `wrap-1795711692-24759.sh` 沒有被刪除，表示該次 bg-run 的 Python launcher 在 `finally` 前即結束（可能被桌面重啟的 process 清理打斷）。這解釋了 00:48 之後 cache 沒有正常收尾的紀錄，但不直接解釋 01:50 的兩次 B 類失敗（那時已無 wrapper 殘留）。
5. **UNTESTED**：Android 背景啟動限制（BFSL / background start）使 TermuxService 忽略 service_execute。證據：logcat 無相關訊息，但 AMS 在多數情況下會留下 W 級記錄，故此項不能排除，也無法確認。測試：有 native 端執行後，搜尋 logcat 的 `background` / `BFSL` / `allowlist` 字樣。
6. **排除或弱化**：
   - 腳本路徑或 exec bit：probe.sh 為 `-rwx------`，位於 Termux 自己的 `usr/tmp`，並且 wrapper 形式與直接形式都失敗，因此不是唯一原因。
   - am 不存在或 apk 損壞：am 存在、可執行、apk 通過 zip 完整性檢查，可排除「檔案損壞」。

## 建議（僅建議，未執行）

- 讓使用者在 native Termux shell 手動跑一次 `am startservice`（同參數指向 probe.sh），確認是 TermuxService 問題還是 PRoot 呼叫問題。
- 若 native 也無 marker，考慮重新啟動 Termux app 或 TermuxService（需使用者決定；我未做）。
- 在此之前，native 執行可走已驗證可用的 `f8-shard` daemon 路徑（00:55 之後的 soak 與 preflight 已使用）。

## Unknown / risk

- logcat buffer 已無 00:45 成功時的 am 紀錄，無法做成功與失敗的差異比對。
- `/proc` start time 不可靠，無法確認 com.termux / TermuxService 的重啟時間。
- `dumpsys` 不可用，無法查 ServiceRecord 或 BFSL 狀態。
- am 對無效子命令靜默，代表 am 的 stdout / stderr 不可作為成敗依據；這本身可能就是故障的一部分。
- 本次未讀取 `sharded-soak.rc` 的數值，只確認了檔案存在與 preflight PASS。
- 探針目錄與 `wrap-copy.sh` 留在 `/data/data/com.termux/files/usr/tmp/bgrun-probe-20261127-015000/`，屬本次建立物，未清理（依指示只在自己的探針目錄內建立檔案）。
- 未刪除任何 cache 檔（含殘留 `wrap-1795711692-24759.sh`）。

## 配額

launch 次數：2/6（兩次皆為 termux-bg-run 或 raw am startservice）。am `--version`、無參數、`bogus-subcommand` 不呼叫 startservice，未計入。
