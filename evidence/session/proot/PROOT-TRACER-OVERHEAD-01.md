# PROOT-TRACER-OVERHEAD-01 — PRoot 追蹤器開銷從哪裡來（2026-09-24，量測＋原始碼，未改任何設定）

## 結論
**Termux proot 自 2026-05-23（commit `4abc88b5c`）起，把 `sendto`／`sendmsg`／`recvfrom`／`recvmsg` 全部加進 seccomp 攔截清單**，
只為了替 bubblewrap `--unshare-net` 模擬 NETLINK。seccomp 無法依 socket 類型過濾，所以 **PRoot 內所有程式的每一次 socket 收發**
都要停下來等單執行緒的追蹤器。實測代價：同一個 socket 上 `send+recv` 55.51 µs／組，`write+read` 1.56 µs／組（**約 35 倍**）。
Chromium／Electron（Claude Desktop、Cursor、Codex、Hermes）的程序間通訊（Mojo）、D-Bus、X11 客戶端的 `recvmsg` 都走這條。
同一批提交也把 `clone`／`clone3`（`064617fa1`）加進攔截。

## 證據
1. **安裝版本包含該提交**：Termux `proot` 5.1.107.92（`dpkg`），tag `v5.1.107.92` = `7266fb3e85`；GitHub compare：tag 比 `4abc88b5c` ahead 43、behind 0。
2. **原始碼**（termux/proot master `src/syscall/seccomp.c` `proot_sysnums[]`）：含 `PR_recvfrom`、`PR_recvmsg`、`PR_sendmsg`、`PR_sendto`、`PR_socket`(SYSEXIT)，
   也含 `PR_close`、`PR_brk`(SYSEXIT)、`PR_ioctl`(SYSEXIT)、`PR_clone`、`PR_clone3`、`PR_prctl`。沒有任何 `getenv` 開關。
   `4abc88b5c` 的 diff 正是新增那 5 行；提交說明：bubblewrap `loopback_setup()` 需要 NETLINK_ROUTE，Android 上沒有 CAP_NET_ADMIN。
3. **微基準**（PRoot 內、同一支程式、N=20000，`scratchpad/sysbench.c`）：
   | 呼叫 | 耗時 |
   |---|---|
   | `getpid` | 0.15 µs |
   | pipe `write+read` | 1.01 µs／組 |
   | socket `send+recv`（被攔） | **55.51 µs／組** |
   | 同 socket `write+read`（不被攔） | 1.56 µs／組 |
4. **當下追蹤器狀態**（proot pid 20095，Threads 1；seccomp 模式 2，未設 `PROOT_NO_SECCOMP`）：
   - 20 s 平均 0.40 核；在 PRoot 外（`adb run-as`，不被追蹤）以 ~20 ms 抽樣 30 s：追蹤器忙碌 27%，78% 時間沒有程式排隊。
   - 排隊（狀態 `t`）的主要是 Claude Desktop 的 gpu-process（`recvmsg` 64 次樣本）、Claude Code（`futex` 58）、Claude Desktop renderer（`epoll_pwait`／`futex`／`recvmsg`）。
     `futex`／`epoll_pwait` 不在攔截清單——推測是停在訊號傳遞或 ptrace 事件停止時剛好位於這些呼叫，**未證實**。
   - 抽樣工具：`/data/data/com.termux/files/usr/tmp/tracer_sampler.py`；結果 `tracer-sample-01.json`。
   - 09-23 晚上曾量到同一追蹤器 0.97–1.01 核（單執行緒滿載）——與今天的差別推測是當時負載較重（兩個 Serena 全樹掃描等），未重測。

## 取捨
- 這些攔截存在是為了 bubblewrap（`bwrap --unshare-net`）。本機：`bubblewrap 0.9.0` 有裝（推測是 xdg-desktop-portal 的相依）；
  Claude Code `sandbox` 未設定；Codex 設定無 sandbox 項、最後使用 09-04；Cursor 的代理沙箱在 PRoot 本來就失敗（`sandboxPreflight`）。
- 移除 socket 攔截的代價：bwrap 的 `--unshare-net` 在 PRoot 內會再度失敗（等於回到 2026-05 以前的行為）。

## 候選修法（都未做）
1. 自編 proot（tag v5.1.107.92）加一個小修補：socket 收發與 clone 的攔截改成**環境變數開啟**（預設關），bwrap 需要時再開。
   先裝成獨立的 `proot-fast`，不動系統 proot；以微基準與 Electron 負載做 A/B。換掉日常桌面用的 proot 要整個 PRoot 重啟，另外決定。
2. 不改 proot：把重的程式放進各自的 `proot-distro login`（每個 login 是獨立的追蹤器，可分散到多核）；但每次呼叫的代價不變。
3. 回報 termux/proot 上游（對外發文，需使用者同意）。

## 修法 1 的原型：proot-fast（2026-09-24，已建置、**尚未取代任何東西**）
- 原始碼：`termux/proot` `v5.1.107.92.zip`（481 443 bytes），SHA256 `29385d1d…32135` ＝ termux-packages `08b49b3ce0` 的 `TERMUX_PKG_SHA256`。
- 修補 `proot-fast-bwrap-compat.patch`（66 行，只改 `src/syscall/seccomp.c`）：把 `clone`、`clone3`、`recvfrom`、`recvmsg`、`sendmsg`、`sendto`、`socket`
  移出預設清單，放進 `bwrap_compat_sysnums[]`，只有追蹤器環境有 `PROOT_BWRAP_COMPAT` 時才合併。fake_id0 自己仍攔 `sendmsg`（身分憑證轉換）與 `socket`。
- 建置：Termux 原生 clang 21（`adb run-as`），旗標同 Termux 套件（`PROOT_WITH_LIBANDROID_SHMEM`、`-DARG_MAX=131072`），VERSION `5.1.107.92-fast`，
  loader 放在私有目錄 `~/build/proot-fast/out/libexec`。產物 `~/build/proot-fast/out/bin/proot-fast`。
  第一次建置失敗是我把 CPPFLAGS 放在 make 命令列、蓋掉了 makefile 的 `-I`，改由環境變數傳入後成功（36 條編譯警告，未確認是否都是既有的）。
- 微基準 A/B（同 42 個參數、同 rootfs，從 PRoot 外啟動；`proot-fast-bench-03.txt`，每組兩次）：
  | | send+recv | sendmsg+recvmsg |
  |---|---|---|
  | 系統 proot | 54.8／55.1 µs | 55.8／55.8 µs |
  | proot-fast | **0.85／1.05 µs** | **28.7／29.5 µs** |
  | proot-fast＋`PROOT_BWRAP_COMPAT=1`（對照，應該要慢） | 55.5／54.7 µs | 55.9／55.8 µs |
  對照組回到慢速 → 差異確實來自修補。
- 作廢紀錄：`proot-fast-bench-01.INVALID-ldpreload-leak.txt`——我把 Termux 的 `LD_PRELOAD=libtermux-exec.so` 漏進 guest，三種 proot 都載入 libc 失敗；改 `env -u LD_PRELOAD` 後正常。
