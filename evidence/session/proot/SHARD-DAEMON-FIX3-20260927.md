# shard-daemon fix 3 — Termux 重開會多留一個常駐程式（2026-09-27）

## 發現
驗 `setsid -f`（交接 09-26 第 3 步）時，使用者第二次重開 Termux 後（10:40）：
- 追蹤器正常：只有日常 22450（父 `com.termux` 19958，44 tracee）＋分流 23918（父常駐程式 22459，20 tracee），沒有 0 tracee 的 proot。
- 但 `shard-daemon.sh` 有 **3 個**，PPid 都是 1：

| pid | 開機後秒數 | fd 9 / fd 3 | 狀態 |
|---|---|---|---|
| 31233 | 167652 s（09-26 約 16:4x，自動分流套用那次） | `daemon.lock (deleted)` / `ctl.fifo (deleted)` | 沒有子程序，永遠卡在 read，RSS 3.2 MB |
| 16178 | 231875 s（09-27 10:33 第一次重開） | 同上（deleted） | 同上，RSS 3.9 MB |
| 22459 | 232288 s（10:40 第二次重開） | 現役 lock／fifo | 子程序＝分流追蹤器 23918 |

## 機制
- 常駐程式靠 `flock $PREFIX/tmp/f8-shard/daemon.lock` 保證只有一個。
- Termux 重開（兩次 `com.termux` 都是同一個 pid 19958，但 `$PREFIX/tmp` 都被清空）會把 lock 檔和 fifo 刪掉。
- 常駐程式用 `setsid -f` 自成 session，不會被一起收掉。它握著已刪除的 lock，自己又用 `<>` 開 fifo（永遠不會讀到 EOF），所以會一直睡在 read(2)，而且沒有任何寫入端找得到它。
- 下一次 f8desk 對新的 lock 檔 flock 會成功，於是又起一個新的。結果是**每重開一次 Termux，就多一個閒置的 bash**。不吃 CPU，每個約 3–4 MB。

## 修正（fix 3）
`~/build/proot-fast/shard2/shard-daemon.sh`：`read -t $CHECK`（預設 60 s）。逾時時如果 `/proc/$$/fd/9` 已經不是 `$BASE/daemon.lock` 同一個檔（`-ef` 比 dev＋inode）就 `exit 0`；讀到 EOF 或出錯也照舊退出。
- 另加 `F8_SHARD_BASE`／`F8_SHARD_DAEMON_CHECK_S`，**只供測試用**，f8-shard 的 BASE 仍然寫死。
- 睡著的舊 inode 還被佔用，檔案系統不會重用它，所以 `-ef` 不會誤判成「同一個檔」。
- 工作行是 f8-shard 的一次 `printf` 寫入（小於 PIPE_BUF），逾時不會切在一行中間。

## 測試（`shard-daemon-fix3/test_daemon_wipe.sh`，CHECK=1 s，Termux bash 5.3.15，假 shard-run）
```
PASS T0 control reproduces leak (old 30886 and 30901 both alive)
PASS T1 job ran
PASS T2 second instance exits 0, pid file kept
PASS T3 still alive after 4 checks with lock intact
PASS T3b job after timeouts ran
PASS T4 exited .583 s after wipe
PASS T5 old 31634 gone, new 31718 alive
PASS T5b new daemon serves jobs
PASS T6 exited after lock file replaced
cleanup killed test daemon 30886
cleanup killed test daemon 30901
DAEMON_FIX3_TEST_PASS
```
T0 是必須變紅的對照組：舊版在刪檔、再啟動後，兩個都還活著。清理時只殺測試自己啟動、而且 cmdline 含 scratchpad 路徑的 pid，結束後沒有殘留。

## 部署（10:44）
- 先 `cp` 到 `.shard-daemon.sh.new` 再 `mv`，是原子替換。
- 新檔 sha256 `a9b4f1cf…`；備份在 `shard-daemon.sh.bak-20260927-fix3`（`a07eae43…`，等於修正前）。
- 正在跑的 22459 讀的是舊 inode（`/proc/22459/fd/255 … (deleted)`），不受影響，**但它仍然是舊碼**：下次重開 Termux，它會變成最後一個殘留。
- fork `src/f8-ahb-exa-async/tests/tracer_shard/shard-daemon.sh`（untracked）已同步成新版，同樣未 commit。
- 素材：`shard-daemon-fix3/`。`shard-daemon.before.sh`（`a07eae43…`）是修正前，`shard-daemon.fix3.sh`（`a9b4f1cf…`）是 fix 3，`shard-daemon.after.sh`（`8becae04…`）是 fix 4＝現役；測試腳本是 `test_daemon_wipe.sh` 和 `test_daemon_inherit.sh`。

## 收掉舊常駐程式（10:53，使用者選「三個都處理」）
- 屬於 construction。逐一核對 cmdline 是 `…/bin/bash …/shard2/shard-daemon.sh` 後，依 pid 各送一次 `kill`（SIGTERM）：
  - 31233：fd9＝`daemon.lock (deleted)`
  - 16178：fd9＝`daemon.lock (deleted)`
  - 22459：fd9＝現役 `daemon.lock`
- 三個 1 s 內都結束；分流追蹤器 23918 還活著。
- **我原本判斷錯了**：我說過殺 22459「下一次分流走 am 就會起新常駐程式」，實際上**起不來**。
  - 10:53:12／10:53:17 兩次 `f8-shard /bin/sleep 1` 都是 `via=am`。`daemon.lock` 的 mtime 有更新到 10:53:19，代表新常駐程式確實跑到 `exec 9>`，但 `daemon.pid` 還停在 22459。
  - （中途的「daemon 9166」是誤判：`/proc` 掃描比對到我自己的 shell，因為指令字串裡含有 `shard-daemon.sh`。）

## Fix 4 — 分流繼承了 lock 和 fifo（原本就有的 bug，這次被 kill 觸發）
- 查 fd：23918 proot-fast8、23930 claude-desktop、24227、24719 cowork、24960 claude，全都有 `fd3 -> ctl.fifo`、`fd9 -> daemon.lock`。
- 原因：常駐程式用 `setsid "$RUN" "$J" … &` 開分流，fd 3 和 fd 9 被一路繼承到整棵 app 樹。flock 綁的是「開啟的檔案」，所以只要分流還有任何程式活著，lock 就一直被握著。常駐程式一旦死掉，新的 `flock -n` 會失敗並 `exit 0`，之後每次分流都走 am（約多 1 s），直到整個分流結束為止。
- 修正：`setsid "$RUN" "$J" < /dev/null > /dev/null 2>&1 3>&- 9>&- &`。shard-run.sh 本來就沒用到 fd 3 和 9。
- 測試 `test_daemon_inherit.sh`（T7：常駐程式死了、分流還活著，新常駐程式要拿得到 lock）：
  ```
  == control (fix3, must FAIL)
  fix3 daemon=17143 shard-child=17158 child fds: 2 refs to lock/fifo
  FAIL T7 fix3 no new daemon (lock still held by shard 17158)
  == fix4 (must PASS)
  fix4 daemon=17236 shard-child=17252 child fds: 0 refs to lock/fifo
  PASS T7 fix4 new daemon 17264 took the lock while shard 17252 lives
  ```
  用 fix4 重跑 `test_daemon_wipe.sh`：T0–T6 全部 PASS（`DAEMON_FIX3_TEST_PASS`），沒有殘留。
- 部署（10:55）：一樣用 cp＋mv 原子替換，sha256 `8becae04…`；fork 裡的副本已同步，未 commit。
- 恢復：確認沒有任何常駐程式在跑之後，`rm` 掉被 Claude Desktop 那棵分流樹握住的 `daemon.lock`、`ctl.fifo`（等於 Termux 重開時會做的事）。接著：
  - 10:56:03 `f8-shard /bin/sleep 1` 走 `via=am`，並啟動常駐程式 **18265**：fix4 的 inode 442314、`TracerPid 0`、父＝`com.termux`（am 啟動的都是這樣）。
  - 10:56:08 下一次分流 `via=daemon`。
  - 10:56:20 的活分流（`sleep 6`，追蹤器 18473、app 18487）：兩者都是 **0 refs to lock/fifo**。
- 殘留影響：現有的 Claude Desktop 分流樹（23918…）仍握著**已刪除**的舊 lock／fifo。它們彼此隔離，不影響新常駐程式；Claude Desktop 關掉後就會消失。

## 還沒驗
- 下次重開 Termux：60 s 內應該只剩 1 個 `shard-daemon.sh`；新開的 Claude Desktop 分流樹不該有 `daemon.lock`／`ctl.fifo` 的 fd。
- 陷阱：用 `/proc/*/cmdline` 數常駐程式時，要比對開頭的 `/data/data/com.termux/files/usr/bin/bash …shard-daemon.sh`，否則會把執行檢查的那個 shell 自己也算進去。

## F8 第三次重開（10:58）：常駐程式已經在跑的情況 PASS
- 這次 `$PREFIX/tmp` **沒有**被清（`daemon.pid` 還是 10:56:05 那份，常駐程式 18265 活著），代表 TermuxService 沒有真的重啟。所以這次只測到「常駐程式已在跑、關掉再開桌面」這個情況。
- f8desk 在 10:58:00 對 lock 做了 `exec 9>`（mtime 有更新），`flock -n` 失敗就退出了。常駐程式仍然只有 18265。
- 新開的 Claude Desktop 分流 20615 父程序是 18265。整台只有 18265 自己握著 `daemon.lock`／`ctl.fifo`，**fix 4 在真的 Claude Desktop 程式樹上 PASS**。

## F8 fix 3 真機驗證（11:02，模擬 Termux 清 tmp，使用者要求「先處理 fix3」）
- 對現役常駐程式 18265（fix4 inode 442314）做了 `rm daemon.lock ctl.fifo`，也就是 Termux 清 `$PREFIX/tmp` 時對它造成的效果。
- 11:02:47 刪除 → **18265 在 26 s 內自行退出**（上限是 60 s 的 read 逾時），常駐程式數量變成 0，沒有殘留。
- 11:03:13 分流走 `via=am`，並起了新常駐程式 30328（inode 442314、`TracerPid 0`）；11:03:19 分流走 `via=daemon`。Claude Desktop 分流 20615 沒有受影響。
- 還欠一次「真的 Termux 重開」：`$PREFIX/tmp` 被清時應該只剩 1 個常駐程式。機制跟這次模擬的相同，差別只在觸發的是 Termux 本身。

## POCO F6（10.128.106.111:41707，5038 通道，使用者要求「f6 也處理一下」）
- 連線：mDNS 查不到，所以直接掃 F6 IP 的 30000–50000，只有 41707 回 adb 協定。server 用 `ADB_VENDOR_KEYS=<Termux adbkey>` 起。
- 部署前的唯讀狀態（11:03，使用者剛在 F6 開桌面）：
  - `shard2/shard-daemon.sh` 是 `a07eae43`（修正前），f8desk／f8desk-external 已經有 `setsid -f`。
  - 日常追蹤器 31738（proot-fast8，父＝`com.termux` 31470，env 有 `PROOT_F8_AUTOSHARD=1`）。
  - 常駐程式 31785 的 `PPid` 是 1，底下沒有分流，也沒有別的程式握著 lock。
  - 還沒有 `autoshard.log`，也就是還沒發生過分流。
- 11:04 部署：先 `adb push` 到 `/data/local/tmp`，再用 run-as `cp` 成 `.new`，驗 sha（`8becae04`）後 `mv`；備份 `shard-daemon.sh.bak-20260927-fix3`（`a07eae43`）。暫存檔已刪。新 inode 2092992。
- 11:04:53 核對 cmdline 後 `kill 31785`（舊碼常駐程式；construction），1 s 內結束。之後沒有程式握著 lock，所以不用移開 lock／fifo。
- **待驗**：F6 下一次分流（開終端機或 Claude Desktop）應該走 `via=am`，並起一個 inode 2092992 的新常駐程式；分流樹不應握有 lock／fifo 的 fd。

## F6 真機驗證（11:07，PASS）
- 使用者在 F6 開 Claude Desktop（autoshard.log 11:07:41 `shard electron /usr/lib/claude-desktop/claude-desktop`）。第一次分流走 am（分流追蹤器 7698 的父程序＝com.termux，因為是 TermuxService 起的），同時啟動新常駐程式 **7822**：inode 2092992（fix4）、`TracerPid 0`。
- 整台 F6 只有 7822 自己握著 `daemon.lock`／`ctl.fifo`；日常追蹤器 31738（45 tracee）、分流 7698（9 tracee）都沒有 lock／fifo fd。
