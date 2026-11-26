# 外部 PRoot 最佳化與替代 Runtime 橫向調查報告（2026-11-26）

> **目的**：以極低額度方式盤點 `termux/proot` 最新上游進展與外部 S+/S 級專案（`LinuxDroid`、`DSH Mobile`、`Pons`、`Sprout`、`Cortex`、`Tawc`），對照本機現役 [`f8-proot-fast`](../../../src/f8-proot-fast/README.md)（`proot-fast8` + `auto-shard`）與 F8 Ultra 工作站（非 Root Android 16 / kernel 6.12.23 / Termux + Ubuntu 24.04 ARM64 / Electron・Playwright・Node.js・Termux:X11・Turnip），制定「立刻可移植、補測試後評估、或明確跳過」的行動路線。
> **本地檢查快照**：所有外部倉庫採 `git clone --depth=1 --filter=blob:none --sparse` 精簡拉取至會話暫存區 ``scratch/proot-landscape/`` (local sparse snapshot)，未建置或執行任何未驗證外部程式，亦未改動 `src/f8-proot-fast`、`src/termux-proot-upstream` 或現役系統。

---

## 0. 極省額度的本機＋線上三層研究架構（可直接復用於 Wave 2）

面對動輒 30–55 MB、數萬行的多語言 Repo，直接讓高階 LLM 全庫掃描會瞬間燒光額度。本次驗證出一套**三層漏斗（3-Tier Funnel）**，實際成功將 6 個 Repo 壓縮後僅用 2 個輕量 `flash`（Hydrogen）子代理即完成深度精讀：

1. **Tier 0 — 零 LLM Token 本機預處理（`gh api` + `git sparse-checkout` + `rg`）**
   - 先用 `gh api repos/<owner>/<repo>/git/trees/<branch>?recursive=1` 取得全樹檔名，本機 Python 腳本自動剔除二進位、圖片、`.apk`、`.so`、`node_modules/` 等雜訊。
   - 再以 `git clone --depth=1 --filter=blob:none --sparse` 僅簽出關鍵子目錄（例如 `ultrapg/linuxdroid` 原 55.9 MB / 378 blobs 只抓出 `tools/proot/` 等 49 檔 / 7,100 行；`maiji1990/dsh_mobile` 原 34.3 MB / 801 blobs 只抓出 `docs/ADR/0030` 與 `native/proot/` 等 27 檔 / 3,212 行）。
   - 用 `rg -c` 統計核心關鍵字（`seccomp`, `ptrace`, `LD_PRELOAD`, `statx`, `close`, `brk`, `ioctl`, `Turnip`, `AHardwareBuffer`, `systrap`, `user_notif`, `vDSO`）命中檔與行數，輸出極簡索引 `00-digest-summary.md` 與上游 commit diff 摘要 `00-upstream-diff.txt`。
2. **Tier 1 — 雙路輕量平行精讀（嚴守 `AGENTS.md` 最多 2 個同時在線）**
   - 將檔案按主題切給 **2 個平行子代理**（本次依指示使用 Antigravity `research` + `flash`/Hydrogen 層；若要再把 Antigravity 額度降到接近零，可依 [`AGENTS.md`](../../../AGENTS.md) 改派本機 `hermes chat -m gpt-6-luna-900k` / OpenAI Codex 額度池，唯獨要注意不超過 2 併發）。
   - Prompt 嚴格限定**只能讀指定切片路徑**與**跳過 vendored 目錄**（例如 `cortex/app/src/main/cpp/zstd/`），要求固定只回傳「機制 + 收益數據 + 風險 + `file:line`」。
3. **Tier 2 — 主代理交叉裁決與收斂**
   - 主代理不重讀數萬行原文，僅綜合兩份結構化 packet，產出本決策報告。
4. **給 Wave 2（其餘 29 個專案與 300+ Fork 普查）的零額度自動化擴展建議**
   - 對剩餘 PRoot Fork 普查，可先寫一支本機 Python 腳本呼叫 `gh api` 比對各 fork `master`/`main` 相對 `termux/proot` 或 `proot-me/proot` 的 `compare`（ahead_by commits 與異動檔清單），凡 `ahead_by == 0` 或只改 CI/README/workflow 者**全部於 Tier 0 自動淘汰（0 token）**；只有真正動到 `src/syscall/`、`src/extension/fake_id0/`、`src/path/canon.c`、`src/tracee/` 的 repo 才進入稀疏簽出。

---

## 1. 上游 `termux/proot`（至 `0e4287546`）vs 本機 `proot-fast8` 差異矩陣

本機 [`f8-proot-fast`](../../../src/f8-proot-fast/README.md) 基於 Termux `proot 5.1.107.92`，而上游 `termux/proot` 至 `0e4287546` 已合入多批系統級最佳化（``00-upstream-diff.txt`` (local sparse snapshot)）。兩者對照如下：

### 1.1 重疊與本質差異

| 面向 | `f8-proot-fast`（`v1`–`v8`） | `termux/proot` 上游最新 | 結論與優勢方 |
|---|---|---|---|
| **舊核心相容停攔** | `v2`（`02-proot-fast2-kompat-lean.patch:22-49`）：在 `actual_release >= 2.6.29` 直接切到 3 個 syscall 並跳過 `adjust_elf_auxv`。 | `fcef73eee`（`00-upstream-diff.txt:642-682`）：逐 syscall 依 kernel threshold 過濾，永遠保留 `PR_execve` 調整 `auxv` 與 `PR_uname`。 | **兩者路線接近**，上游保留 `auxv` 調整更穩妥。 |
| **`newfstatat`/`fstat`** | `v5`（`03-proot-fast5-stat-at-enter.patch:176-297`）：於 **seccomp enter stop** 直接以 `pidfd_getfd`/host `newfstatat` + `l2s` + `fake_id0` 代答並改 `PR_void` + `PTRACE_CONT` 省整個 exit stop。 | `0af8715fc`（`00-upstream-diff.txt:530-567`）：仍進 sysexit stop，只合併 `st_uid`/`st_gid` 讀寫與快取 `get_host_uid/gid`。 | **`v5` 明顯更深**（少掉 sysexit stop）；但 `v5` 可順手借用上游 `get_host_uid()`/`get_host_gid()` 再省 2 次 host syscall。 |
| **`statx`** | `v6`（`04-proot-fast6-statx-at-enter.patch:59-124`）：於 seccomp enter stop 直接代答（含 `AT_EMPTY_PATH`）。 | `0ab53f205` + `c071fbd03`（`00-upstream-diff.txt:331-377,568-602`）：僅優化 sysexit fallback 與避免二次路徑翻譯。 | **`v6` 更勝一籌**；上游提交在 `v6` fallback 時互補無衝突。 |
| **`bwrap` 相容與 `ioctl`/`rlimit`** | `v1`（`01-proot-fast-bwrap-compat.patch:40-62`）：把 `clone`/`clone3`/`recv*`/`send*`/`socket` 全收進 `PROOT_BWRAP_COMPAT=1`。 | `9d3649aa7`（`00-upstream-diff.txt:479-529`）：未放行 `clone`/`send*`/`recv*`，但卸除了 `ioctl`/`prlimit64`/`setrlimit`/`socket` 的 `FILTER_SYSEXIT`。 | **`v1` 對 Electron/Node socket/clone 更激進**；上游在 `ioctl`/`prlimit64`/`setrlimit` 補充了條件式 exit 最佳化。 |

### 1.2 `proot-fast8` 尚未擁有的上游「免費收益」（Free Upstream Wins）

1. **移除 `PR_close` seccomp 攔截（`48c903d54` + `7dd8a4ac0`）**：
   - `proot-fast8` 目前仍攔截所有 `PR_close`（`01-proot-fast-bwrap-compat.patch:19`）。上游改於 `pipe`/`pipe2` exit 建 shadow pipe 讀端，並於 `open*`/`read(auxv_fd)`/`add_netlink_socket` 惰性清理已關 fd（`forget_closed_fd_paths`、`forget_closed_netlink_fds`）。實測 Android 15 `find` stops **`9,613 → 3,706`（`804 → 514 ms`）**（`00-upstream-diff.txt:263`）。
2. **免去每次 stop 的 `PTRACE_GETEVENTMSG`（`4006c630f`）**：
   - 改於 `handle_tracee_event()` 先 `fetch_regs()`（設 `regs_fetched_at_stop = true`）並查靜態表 `filtered_flags[PR_NB_SYSNUM]`。每個 seccomp stop 少 1 次 ptrace syscall，並順帶修正**tracee 內層 seccomp-bpf（如 Chromium sandbox）返回 `SECCOMP_RET_TRACE` 時覆寫 PRoot `FILTER_SYSEXIT` 旗標的 bug**（`00-upstream-diff.txt:455-462`）。
   - *移植注意*：若保留 `v1` `PROOT_BWRAP_COMPAT`，須將 `bwrap_compat_sysnums` 一併納入 `remember_filtered_sysnums()`。
3. **路徑解析與 `-0 -l` 冗餘 host syscall 減半（`32defc010` + `543566106` + `0e4287546`）**：
   - `fake_id0` 重用 `canonicalize()` 取得的 `lstat()`（非 symlink 不再補 `stat()`），`link2symlink` 略過已知非 symlink 的 `readlink()`（實測 `tar` `readlink` `5.9k → 752`、`dpkg` `15.4k → 3.7k`，`00-upstream-diff.txt:13-29`）。
   - *相容注意*：`32defc010` 將 `HOST_PATH` `data2` 型別從 `bool` 改為 `const HostPathAccess *`。
4. **`fake_id0` 條件式 sysexit + `get*id` enter 代答（`16e4d2a04`）**：
   - 省掉 `get[e][ug]id`、`prctl`（僅 `PR_SET_KEEPCAPS` 進 exit，放行高頻 `PR_SET_NAME`）、`getsockopt`（僅 `SO_PEERCRED` 進 exit，**與 `v7` `05-proot-fast7-peercred.patch` 完全相容**）、`socket` 的多餘 sysexit。
5. **`execve` 批次讀取 ELF phdr + 1 KiB chunk 讀寫 auxv（`a6f2dc7c3` + `29867df35`）**：
   - 100 次 fork+exec `/bin/true` 的 `process_vm_readv/writev` 從 `40k → 3.3k`、Android 15 fork+exec 快 **18%**、PRoot 自身 syscall 降 **66%**（`00-upstream-diff.txt:171-194`）。

---

## 2. PRoot Fastpath 路線深度對比（`LinuxDroid` / `DSH Mobile` / `Pons`）

### 2.1 `LinuxDroid` (`ultrapg/linuxdroid`)

- **Tracer 端核心補丁（`tools/proot/patches/`）**：
  - **`0001-tracee-lookup-by-pid.patch:48-113` + `0009-tracee-relatives-sweep.patch:38-60`**：O(1) 1024-bucket PID 雜湊表取代鏈表掃描、`talloc_free_children` 重用、`nb_children` 跳過空掃描——對多進程 Electron/Chromium 樹直接消除線性開銷。
  - **`0002-canon-resolve-parent-at-once.patch:39-128`**：深度 ≥ 3 落於 `/` binding 的絕對路徑一次 `open(O_PATH|O_DIRECTORY)` + `readlink(/proc/self/fd/...)` 驗證無 symlink 後跳過逐層父目錄迴圈。
  - **`0004-seccomp-filter-by-argument.patch:27-98` + `0013-seccomp-ioctl-by-request-and-kernel-exit-stops.patch:40-156`**：直接在 seccomp BPF 依參數過濾 `prctl`/`setrlimit`/`prlimit64`/`ioctl`（連 enter stop 都省去）。**缺口警示**：`0004:90` 僅放行 `PR_SET_DUMPABLE` 而**漏掉 `-0` 所需的 `PR_SET_KEEPCAPS`**；`0013:53-58` 過濾 `ioctl` **漏掉 `SIOCGIFINDEX` 與 `ashmem (0x77xx)`**。
  - **可靠性補丁備查**：`0015-lost-fork-events.patch`（`GETEVENTMSG` 回 0）、`0023-reused-pid-new-child.patch`（PID 重用）、`0016-robust-list-from-seccomp.patch`、`0026-fake-id0-fchmodat2.patch`。
- **Tracee 進程內快路徑（`tools/proot/fastpath/` + `0014-fastpath-trampoline.patch`）**：
  - `libblfastpath.so`（`fastpath.c` + `svc-patch.h:39-271` + `svc-dispatch.h` + `audit.c`）會在啟動期以 `mprotect(PROT_EXEC)` + `/proc/self/mem` 原地改寫 `libc.so.6` 與 `ld-linux-aarch64.so.1` 的 `svc #0` 跳至 `0xffff00000` trampoline（BPF `0014` 放行該頁 IP），搭配 `process_vm_readv/writev(getpid())` 與 512 槽 2s TTL 目錄快取。`linuxdroid/README.md:17` 宣稱路徑 syscall 由 `~25 µs → ~0.6 µs`（無完整 benchmark 腳本）。
  - **對 F8 Ultra 風險判斷：極高，不可直接移植 `fastpath/` + `0014`**。原因：① LinuxDroid 跑一般使用者（`0012-fake_id0-identity-only.patch`），`fastpath.c:1141-1291` **不偽造 uid/gid=0 也無 `CAP_DAC_OVERRIDE`**；② `/proc/self/mem` 寫入、`PROT_EXEC` 與 `process_vm_*` 會在 **Chromium/Electron renderer seccomp-bpf / `PR_SET_DUMPABLE=0` 沙盒直接觸發失敗或 `SIGSYS`**；③ 2 秒 TTL 快取在 Playwright/D-Bus 多進程併發有讀舊值風險。

### 2.2 `DSH Mobile` (`maiji1990/dsh_mobile`)

- **`01-statx-fast-exit.patch` & `02-seccomp-optional-skip-close.patch`**：分別被本機 `v6`（支持 `-0 -l` enter 代答）與上游 `48c903d54`（含惰性 fd 清理）完全超越，不需採用。
- **`03-canon-ro-prefix-cache.patch:29-336`（高價值思路）**：
  - 在 `canon.c` 建立 16,384-bucket 唯讀前綴（如 `/usr/lib:/usr/local`）dentry 快取（`PROOT_RO_CACHE_NONEXIST=0` 不快取負結果，絕不快取 symlink）。
  - **實測數據**（Honor PTP-AN10, Android 17, Node `26.13.1`, `2026-11-21-PTP-AN10-A17-P1-proot-fastpath.md:41-91`, `ADR/0030:73-74`）：A/B/A 配對 `n=12` 啟動耗時 **`7,797.9 ms → 5,842.4 ms（-25.1%, p=0.0005, 12/12 皆快）`**。
  - **對 F8 Ultra 適配限制**：原 patch `ro_cache_extensions_safe()`（`03:160-165`）在載入 `fake_id0`（`-0`）或 `link2symlink`（`-l`）時直接停用；若要給 `f8-shard` 的 Electron/Playwright/Node 子樹開啟，須改寫條件（只快取 host `lstat` 具 `S_IRWXU` 的唯讀目錄且避開 `apt` 寫入生命週期），並實測在已有 `v5`/`v6` 後的邊際效益。

### 2.3 `Pons` (`tedin7/pons`)

- **`0002-syscall-stats.patch:18-165`（必收診斷利器）**：以 `PROOT_SYSCALL_STATS=<file>` 每 10 秒及結束時輸出排序後的各 syscall seccomp vs ptrace 攔截次數，能立刻精準找出 F8 Ultra Electron/Playwright 剩餘熱點。
- **`0003-fastpath-marker.patch` + `pons-fastpath.c`（Skip）**：檢查 `args[5] == 0x48544150534e4f50ULL`（`"PONSPATH"`）無條件 `SECCOMP_RET_ALLOW`，具沙盒繞過疑慮且 `pons/README.md` 自述在 ColorOS Steam client 曾被安全攔截、缺 `CAP_DAC_OVERRIDE`、對靜態/Go 無效。
- **`0004-no-heap-emulation.patch:19-93`（`PROOT_NO_HEAP`）**：停用 PRoot 的 `mremap` `brk` 模擬（避免 glibc `malloc_trim` 與真實 `brk` 分歧損毀 heap，並消除所有 `brk` stop）。在 OnePlus Pad 3 `loadsim` 使 `brk` stops **`1,101 → 0`**、整體 **`1.5s → 0.7s`**（`pons/README.md:158-165`）。建議保留 `PROOT_NO_HEAP=1` 條件開關測試 Ubuntu 24.04 + Electron/apt 相容性。
- **`0005-ioctl-untraced.patch:18-56`（高性價比 BPF `ioctl` 過濾）**：在 `__aarch64__` seccomp BPF 層僅追蹤 `SIOCGIFINDEX`、`TCSETSF`、`TCGETS2`/`TCSETS*2`、`FICLONE` 與 `0x77xx`（`ashmem`），**補足了 LinuxDroid `0013` 遺漏的 `SIOCGIFINDEX` 與 `ashmem`**，且連 Node/Electron 高頻 `isatty`/`TIOCGWINSZ`/`FIONREAD` 的 **enter stop** 一併省掉。

---

## 3. 非 PRoot / 混合 Runtime 深度評估（`Sprout` / `Cortex` / `Tawc`）

### 3.1 `Sprout` (`YRangel/sprout`)

- **核心架構（三路分派、`README.md:54-70`, `interception.md:18-170`）**：
  1. **Lane 1 (`sprout-preload`，動態 glibc/musl，99% 場景零 `ptrace`)**：將 `~/.cache/sprout` 內複製的 `ld.so` / `libc.so.6` 之 `set_robust_list`(99) 與 `rseq`(293) `svc #0` 原地改寫為 `mov x0, xzr`，以 `LD_PRELOAD=libsprout-core.so:<sanitized-libc>` 在 PLT 層（`sprout_preload.c` 5,680 行）翻譯路徑、exec、socket（含 D-Bus `SCM_CREDENTIALS` 改寫與 `libandroid-shmem` 相容協議）並直接 tail-call host libc。
  2. **Lane 2 (`GoDynamic`) & Lane 3（Static / static-PIE）**：v0.6 起預設由無 libc `sprout-stub` 手動映射 ELF 與 auxv、安裝 in-guest `SIGSYS` + **`seccomp user-notify`**，把 listener fd 交給 `sprout-super`；`ptrace` 僅退居 `execve(221)` 改寫靜態為動態載入鏈時的 sub-ms 單點掛載。
- **25102PCBEG（同型號手機）`vkmark` 實測核對（`docs/src/benchmarks.md:32-47, 124-196`）**：
  - **環境**：Xiaomi `25102PCBEG`（Adreno 840），Android 16，kernel `6.12.23`，Mesa `25.0.7`（Turnip v1.4.354），`/dev/kgsl-3d0` world-open，Bare Termux-X11 `:0`，`vkmark 2025.01 --winsys xcb --size 1280x720`（預設無上限 `mailbox`）。
  - **數據**：Turnip Vulkan **Sprout `7,883` vs PRoot `755`（10.4×）**（2026-08-22 綜測為 `5,555` vs `559` = **9.9×**）；CPU `llvmpipe` **Sprout `339` vs PRoot `190`（1.8×）**（早場 `469` vs `259`，綜測 `267` vs `143`）。
  - **機制解釋與原作者 Caveats**：`mailbox` 模式下 GPU 驅動高速排隊提交 KGSL `ioctl` 與 XCB socket I/O，PRoot 每個 syscall 都要付 ptrace 往返稅，因此相差 ~10 倍；而 CPU 軟體渲染受算力瓶頸僅快 `1.8–1.9×`。作者亦明確提醒：實測未開 XFCE4 compositor（開合成器會吸收幀率）、熱節流會造成分數 ±30% 波動，且**作者自行更正早期 statics `13.5–15.4×` 宣稱**（因舊測法混入 `proot-distro login` 啟動時間；改以 raw `proot` 對比為 spawn `5.86×`、newfstatat `2.71×`、`open+read+close` `1.45×`）。
- **對 F8 Ultra 工作站的相容限制**：
  - 已驗證 Debian `apt`/`dpkg`、XFCE4、Firefox ESR（需 `MOZ_DISABLE_WASM_SIGHANDLERS=1`）、Node.js；支援 `--shared-tmp --termux-x11`。
  - **但對 Electron / Chromium / Playwright 無實測證據，且存在已知結構風險**：不支援 namespaces（`README.md:271`）、**Android seccomp `RET_KILL` 優先權高於 `user-notify`**（`README.md:264-268`），若 Chromium/V8/Crashpad 發出繞過 PLT 的 raw inline `svc` 或自行安裝 `seccomp-bpf` 都有崩潰風險（極可能仍需 `--no-sandbox`）；另 F8 Ultra 目前系統 `/dev/kgsl-3d0` 實際 SELinux 權限仍需實機探針確認（`x11-gpu.md:90-93` 記載有 Android 16 裝置會遇到 `EACCES`）。

### 3.2 `Cortex` (`ssfuisu/cortex`)

- **機制**：獨立打包 Ubuntu 24.04 的 Android APK（`README.md:41`），`libcortex-hook.so`（~200 libc hooks，無 ptrace）+ 建置期預打補丁的 `glibc 2.39`（且 **`apt` 鎖死 `libc6`**，`README.md:88`）+ 首次執行時**原地 `pwrite` 修改 static ELF 與 Go binary ELF cave**（`static_programs.c`、`go_programs.c`）。
- **為何不適合 F8 Ultra**：① 鎖死 `glibc 2.39` 阻斷系統安全更新且長期背負 ~200 個 hook 維護債（`RTLD_DEEPBIND`/`RUNPATH`/struct time64 等）；② **明言不支援 GPU**（只跑 CPU `Xvnc`，`README.md:97,152`、`docs/llms.txt:5`）；③ 綁定獨立 APK 終端 App，無法融入 Termux + `com.termux.x11` + Turnip 工作流。僅其 hook 細節（如 `close_range` 保護、`RTLD_DEEPBIND` 剔除）具參考價值。

### 3.3 `Tawc` (`wmww/tawc`)

- **機制**：TAWC 整體（Smithay Wayland compositor + `wmww/libhybris` 載入 Android bionic GLES/Vulkan）**不適用於我們的 `com.termux.x11` + Turnip Mesa 架構**。但其底層隔離執行器 **`tawcroot`** 可剝離成單一無依賴 C static binary：純以 **`SECCOMP_RET_TRAP`（`SIGSYS`）+ 指令指標白名單（`tawcroot_raw_syscall_ret`）+ 手動 `execve` ELF 載入**運作，**零 `ptrace`、零 `LD_PRELOAD`、零 `USER_NOTIF`**，且自動放行熱路徑 320 個 syscall 與 KGSL `ioctl`（`overview.md:3-181`, `architecture.md:22-185`），在作者裝置上甚至跑通無 `--no-sandbox` 的 Firefox（`phasing.md:641-660`）。
- **限制與評估**：完全禁止 32-bit；高度依賴 Android 16 `untrusted_app` stacked seccomp 不對其必經 syscall 觸發 `RET_KILL`；在 HyperOS Android 16 與 Ubuntu 24.04 `apt` 尚未有完整驗證（主測 Arch `pacman`）。可列為**次要長期技術觀察對象**。

---

## 4. 綜合結論與 F8 Ultra 優先行動路線

### 4.1 主力 vs 替代 Runtime 總裁決

| 目標路線 | 定位 | 理由 |
|---|---|---|
| **主力工作站（Electron / Playwright / Claude・AI Agent / Termux:X11）** | **繼續以 `f8-proot-fast`（`proot-fast8` + `auto-shard`）為唯一主力** | `proot-fast8` 已具備完整 `-0`、`l2s`、`SO_PEERCRED`、multi-tracer 分流與最高相容性；任何純 `LD_PRELOAD` 方案對 Chromium/Electron/static 二進位都有缺口。 |
| **Phase A（最低風險、立刻強化 `proot-fast8` → `proot-fast9/10`）** | **挑選 Upstream + Pons + LinuxDroid 結構性補丁** | 無須重寫架構，即可在同一個 ptrace+seccomp 模型上大幅削掉剩餘 stop 與 PRoot 自身 O(N) 開銷。 |
| **Phase B（針對性 Side-by-Side 實驗線）** | **在複製的獨立測試 rootfs 試測 `Sprout`（次選 `tawcroot`）** | 若某天需要跑高密度 Turnip Vulkan（如 3D/Wayland/Zink）或測試無 ptrace Node 速度，`Sprout`（與 `tawcroot`）才值得做 side-by-side 對照，**絕不直接替換生產 rootfs**。 |

### 4.2 `f8-proot-fast` 下一步移植優先序（按 收益／風險比 排序）

1. **P0（量測先行）**：先在 `f8-proot-fast` 加入 Pons **`0002-syscall-stats.patch`**（`PROOT_SYSCALL_STATS`），實際打一輪 F8 Ultra `Electron` + `Playwright` + `Node.js`，摸清 `proot-fast8` 之後剩餘的 seccomp stop 排行。
2. **P1（零風險高收益上游同期補丁）**：
   - Upstream **`48c903d54` + `7dd8a4ac0`**：移除 `PR_close` seccomp 攔截（加惰性 fd 清理）。
   - Upstream **`4006c630f`**：免 `PTRACE_GETEVENTMSG` 查表 + `regs_fetched_at_stop`（須同步讓 `remember_filtered_sysnums()` 納入 `v1` `bwrap_compat_sysnums`）。
   - Pons **`0005-ioctl-untraced.patch`**：AArch64 BPF 層放行高頻 `ioctl`（保留 `SIOCGIFINDEX`/`TC*2`/`FICLONE`/`0x77xx` ashmem）。
   - Upstream **`16e4d2a04`** + **`32defc010`/`0e4287546`/`0af8715fc`** + **`a6f2dc7c3`/`29867df35`**：`fake_id0` 條件式 exit（與 `v7` `SO_PEERCRED` 相容）、`v5`/`v6` 改用 `get_host_uid/gid()`、`lstat` 重用與 `execve` 批次 `auxv`/`phdr`。
3. **P2（針對多進程與記憶體）**：
   - LinuxDroid **`0001`（O(1) PID hash）+ `0009`（talloc 重用）**。
   - Pons **`0004`（`PROOT_NO_HEAP=1` 旗標化測試）**：驗證 Ubuntu 24.04 `apt` / `Electron` / `node` 無 `brk` 異常後考量預設開啟。
4. **P3（特定 Shard 選配評估）**：
   - 僅針對 `f8-shard` 的 Electron / Playwright / Node 分流器評估改寫版 DSH **`03-canon-ro-prefix-cache.patch`**（僅對具 `S_IRWXU` 的 `/usr/lib:/usr/share:/lib` 開啟且 `NONEXIST=0`，避開 `apt` 寫入期）。
5. **明確跳過（不進 `f8-proot-fast`）**：LinuxDroid `fastpath.c` / `svc-patch.h` / `0014`（無 `-0` 與 `CAP_DAC_OVERRIDE`、且 `/proc/self/mem` + `PROT_EXEC` + `process_vm_*` 撞 Chromium sandbox）；Pons `0003` magic marker；DSH `01`/`02`；Cortex。

### 4.3 若要在 F8 Ultra 實測 `Sprout` 與檢查 Wave 2 的最小步驟

- **F8 Ultra `Sprout` Side-by-Side 探針**：① Termux shell 檢查 `/dev/kgsl-3d0` `open(O_RDWR)` 實際 SELinux 權限；② 在**複製的測試 rootfs**（不動日常生產環境與 Stable `:1`）實測 `sprout` 跑 `apt-get update`、`node`、Turnip `vkmark` 及 `chromium/electron --no-sandbox` vs `proot-fast8` 實機對比。
- **Wave 2（`DroidDeck` / `WinNative` / `NeoPRoot` / `Shroot` / `fake-chroot-ng` 等）**：沿用本報告第 0 節三層漏斗，先以 0-token 腳本抓出各 repo 檔案樹與相對上游差異清單，只對仍有「**`proot-fast8` + 上游 `0e42875` 皆未涵蓋之新機制**」的專案派輕量 `flash`（或 Hermes `gpt-6-luna-900k`）進行針對性切片精讀。
