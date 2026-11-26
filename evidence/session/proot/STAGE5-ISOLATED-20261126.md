# Stage 5 隔離驗證與交接（2026-11-26）

## 身分與隔離

- 原始碼基線是 `f8-proot-fast` 的 `ee603b8f17560e3192654086e20643b8fbd919cf`。測試修正與 `fast9` 候選補丁放在 `src/f8-proot-fast-stage5` 的 `stage5/isolated-fast8-20261126`，最新本機提交為 `136c25dd30b128bceaae8182633e8487c4f7b759`。
- 工作目錄是 `/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp`。以下原始紀錄路徑相對於該目錄。
- 建置使用 Termux clang 與 llvm-objcopy 21.1.8。以 upstream tag `v5.1.107.92`（`7266fb3e8516535682f5a9c8f3a7e70f6506eddb`）加現役六個 patch 建出 AArch64 Android fast8。
- Native runner 以 TermuxService 啟動單次背景命令，核對 runner `TracerPid=0`。基線和微基準都使用獨立 rootfs、HOME、暫存目錄及明確傳入的環境。daemon 測試採獨立 lock、FIFO 與 PID 檔，只有確認命令身分後才送訊號。

## Daemon 測試修復

同一個隔離 fixture 注入 T1 工作遺失時，舊版印出 `DAEMON_FIX3_TEST_FAIL` 卻回傳 0。修正版（`4bbbc94`、`d2ec249`）的正常 T0–T6 回傳 0，注入 T1 工作遺失回傳 1，daemon 無法啟動也回傳 1。最終提交前重跑正常和 T1 注入，兩次皆無測試 daemon 殘留。退出確認使用獨立存活檢查，訊號仍需匹配隔離命令身分。

原始紀錄為 `daemon-red.log`、`daemon-abort.log`、`daemon-final-green.log`、`daemon-final-injected.log`。

## Stage 5.1 隔離 fast8 基線

`fast8/bin/proot-fast8` 和 loader 已通過 SHA256 驗證。隔離 rootfs 靜態探針成功，之後原生無外層 tracer 的路徑也執行了同一隔離建置的基準工作負載。裝置型號為 `25102PCBEG`，原生 runner 的 seccomp 狀態為 2。

原始紀錄為 `fast8/patches.sha256`、`fast8/artifacts.sha256`、`fast8/build.log`、`nested-smoke.log` 和 `native-stats-current.log`。

## Stage 5.2 計數正確性與開銷

以 [Pons 0002](https://github.com/tedin7/pons/blob/77369df51d3fc98b19ddb2385ebf6d5b7c620053/tools/proot/0002-syscall-stats.patch) 建立隔離診斷版。使用 `PROOT_SYSCALL_STATS_DIR` 指定新目錄，每個 tracer 寫入 `tracer-<pid>.tsv`。原始補丁在保存本次 `ORIGINAL` 前讀取該暫存器庫，隔離修正版改讀同一 stop 的 `CURRENT`。正式數值取自 `stats-current`。

| 對照 | 較一次迴圈的 openat | 較一次迴圈的 close | 額外 enter stop |
|---|---:|---:|---:|
| 11 次迴圈 | 10 | 30 | 40 |
| 37 次迴圈 | 36 | 108 | 144 |

各 tracer 的報表與 PID 綁定，行與總數加總一致。未攔截的 getpid 沒有被當成 enter stop。故意把報表路徑指向不存在的目錄時，guest 回傳 0 但沒有報表，驗收視為無有效資料。冷啟動有額外 syscall，需使用同路徑的短控制。

九組 3,000 次迴圈配對中，開啟統計相對同一 binary 關閉統計的配對中位差為 `-1.47%`，範圍 `-5.04%～+21.84%`。這組波動不足以確認單向開銷。正式效能採統計關閉，另留帶統計的功能驗證。

原始紀錄為 `native-stats-current.log`、`stats-current-runs/timing.json` 和同目錄的 per-tracer 報表。

## Stage 5.3 候選與採用決定

| 候選 | 同機隔離驗證 | 判定 |
|---|---|---|
| Pons ioctl | PTY `TIOCGWINSZ` 回傳預期 120 欄，3,000 次被攔截的 enter stop 降至 0。保留翻譯的 `TCGETS2` 仍是 37/37。九組停用計數器的配對牆鐘中位降幅 93.44%。 | 保留候選。仍需 ashmem、FICLONE 和實際工作站工作負載的相容性資料。 |
| GETEVENTMSG | 常規、bwrap 開啟、seccomp 加速關閉三種模式的 fake uid/getcwd 通過。重疊 filter 的 getcwd 從基線退出 92 到候選退出 0。短控制將 18 個差異定位在啟動階段，兩邊的工作負載增量皆 144。九組停用計數器的配對牆鐘中位降幅 5.13%。 | 保留候選。仍需 fork/exec、stat-at-enter、跨 tracer 和 Electron/Playwright 回歸。 |
| close 兩件組 | 同一套原生編譯器的上游父版 `c071fbd` 與合併後 `48c903d`。兩邊在上游指定 bind 順序都解析到 B，反轉順序都到 A。close 密集探針的九組配對中位降幅 69.14%。 | 上游參考通過。現役 fast8 缺上游的 netlink fd 模組，直接套用失敗，仍待移植及 pipe、auxv、netlink 回歸。 |

原始紀錄為 `native-ioctl.log`、`native-eventmsg-controlled.log`、`native-close-upstream-result.log`，對應的 `*-runs/timing.json` 有各組樣本。初次 GETEVENTMSG 檢查假設所有 stop 全等，已另保留 `native-eventmsg.log` 的失敗紀錄。初次 close 檢查的 bind 順序及基線預期均已訂正，原始異常保留於 `native-close-upstream*.log`。

### Stage 5.3b：fast9 三組候選移植與逐組歸因驗證

- 三組候選已切出獨立補丁並與 `tests/fast9_regress.c` 一併提交至 `src/f8-proot-fast-stage5`（`stage5/isolated-fast8-20261126` @ `136c25d`，不動 `src/f8-proot-fast` `main` 與現役 `out8/`）：
  - `patches/07-proot-fast9-ioctl-bpf.patch`（Pons `0005` AArch64 `ioctl` BPF，保留 `SIOCGIFINDEX`、`TCSETS+2`、`TCGETS2`/`TCSETS*2`、`FICLONE` 與 `0x77xx` ashmem）
  - `patches/08-proot-fast9-geteventmsg.patch`（上游 `4006c630f` 免 `PTRACE_GETEVENTMSG` + `regs_fetched_at_stop` + `collect_filtered_sysnums` 納入 `bwrap_compat_sysnums`）
  - `patches/09-proot-fast9-no-close-stop.patch`（上游 `7dd8a4ac0` `pipe_shadow` + `48c903d54` 移除 `PR_close` 攔截與 `auxv`/netlink fd 惰性清理）
- 隔離建置産物（`artifacts.sha256`，共用 `loader` `eab6b213…`）：`fast9-a-ioctl`（`3b70d498…`）、`fast9-b-eventmsg`（`ac8642df…`）、`fast9-c-close`（`cc5ed3fb…`）、`fast9-combined`（`9ff09ef2…`）。
- 測試訂正紀錄：初版 `fast9_regress.c` 的 `test_auxv_close_reuse` 在 `pfd[0] == target_fd` 時誤呼叫 `close(pfd[0])` 關閉已重用 fd 導致基線退回 `rc=6`，補上 `pfd[1] == target_fd` / `pfd[0] != target_fd` 守衛並以 `-Wall -Werror` 重編通過；初版 `run-fast9-attribution.sh` 預設 420 秒逾時於執行第 5 項 `sustained` 時回傳 `RC=124`，調升至 900 秒後完整執行結束 `RC=0`（`FAST9_ATTRIBUTION_DONE`）。
- **回歸測試（35/35 全數通過）**：`fast8`、`fast9-a-ioctl`、`fast9-b-eventmsg`、`fast9-c-close`、`fast9-combined` 共 5 支二進位 × 7 種案例（`default`、`bwrap_compat`、`no_seccomp`、`stat_enter_0`、`pipe_yes_head`、`pipe_seq_head`、`dpkg_query`）全部 `rc=0`。
- **5 組交替歸因實測（`fast9-attribution.json`，+1 warmup）**：

| 工作負載 | `fast8` | `fast9-a-ioctl` | `fast9-b-eventmsg` | `fast9-c-close` | `fast9-combined` |
|---|---:|---:|---:|---:|---:|
| **`ioctl_hot`**（30k `FIONREAD`） | `1630.85 ms` | `25.97 ms` (`-98.41%`) | `1652.45 ms` (`+1.32%`) | `1639.06 ms` (`+0.50%`) | `22.38 ms` (`-98.63%`) |
| **`stat`**（50k `stat` + 50k `statx`） | `5986.74 ms` | `6046.54 ms` (`+1.00%`) | `5932.49 ms` (`-0.91%`) | `5957.85 ms` (`-0.48%`) | `5941.36 ms` (`-0.76%`) |
| **`fileio`**（15k `open/read/close` + walks） | `1588.00 ms` | `1627.20 ms` (`+2.47%`) | `1570.59 ms` (`-1.10%`) | `1140.38 ms` (`-28.19%`) | `1160.87 ms` (`-26.90%`) |
| **`exec40`**（40× `/usr/bin/true`） | `88.70 ms` | `84.75 ms` (`-4.45%`) | `87.60 ms` (`-1.24%`) | `85.50 ms` (`-3.60%`) | `75.30 ms` (`-15.11%`) |
| **`sustained`**（5s 混合） | `14500 ops` (`5022.49 ms`) | `17450 ops` (`+20.34%`) | `14500 ops` (`0.00%`) | `17050 ops` (`+17.59%`) | `21950 ops` (`+51.38%`) |

## Stage 5.4 與 5.5

- Sprout 指定來源為 `ba8656fd28769a2477b6e3faed3e1cfc18bb9921` 的 CLI 0.6.1。完整來源和 Cargo.lock 已簽出至 `sprout-preflight/sprout-src`，對應的 AArch64 glibc interposer 已建置並驗證匯出符號。公開的 v0.5.4 release 有 guest interposer，但無對應的 Termux host binary，GitHub Actions 公開 artifact 清單為空。
- [Ubuntu Base 24.04.4 ARM64](https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release/) 核對 Canonical 簽章和映像 SHA256 後解包至 `sprout-preflight/ubuntu-noble-arm64`。fast8 在原生 Termux lane 執行該 rootfs，確認 `glibc 2.39` 和 `NOBLE_FAST8_OK`。
- 以 Termux 簽章索引確認 Rust `1.100.0-1` 兩個套件及 SHA256。原鏡站索引指定的舊套件 404，主站下載在 81,583 bytes 時逾時，官方 CDN 回傳 TLS 主機名錯誤。TUNA 的 1 MiB range 取樣為約 123 KB/s。網路恢復後由 TUNA 續傳完成，Rust 與 Android ARM64 標準庫合計 131,799,760 bytes，兩個套件皆通過簽章索引中的 SHA256，僅解包至隔離的 `sprout-preflight/toolchain`。
- `rustc` 與 `cargo` 都回報 1.100.0。用 Termux 原生 runner（`TracerPid=0`）離線編譯並執行最小 Cargo 專案，得到 `STAGE5_NATIVE_RUST_OK`，binary 為 AArch64 Android（`/system/bin/linker64`）。工作站套件與設定無變更。原始紀錄為 `sprout-preflight/rust-probe-native.log`。
- 另以官方同版 host/guest release 做 Sprout `0.5.0` 的 headless 預檢。SHA256、Bionic host 與 glibc interposer ABI 已驗證。fast8 在同一 rootfs 通過；Sprout 的 guest loader 無法開啟 `libsprout-core.so`，所以未執行計時。觀察記錄保存在 `sprout-preflight/sprout-headless-050-v2.log`，載入失敗根因尚未確認。
- 以 `sprout-preflight/build-sprout-061.sh` 建置鎖定提交 `ba8656fd28769a2477b6e3faed3e1cfc18bb9921` 之 Termux host binary：初次建置因 Rust `cc-rs` 傳入 `--target=aarch64-linux-android`（未帶 API 24，導致 bionic `<sys/uio.h>` 隱藏 `process_vm_readv`/`process_vm_writev`）回傳 `101`；僅於 `build-sprout-061.sh` 加上 `CFLAGS="--target=aarch64-linux-android24"`（`sprout-src` 維持乾淨未改）後以原生 `TermuxService`（`--user 0`）重跑通過，`RC=0`（1m 17s），產出 `sprout`（`040476fc…`）、`sprout-super`（`18c687ab…`）、`sprout-stub`（`e789a458…`），與 `glibc/libsprout-core.so`（`6a4646fb…`）紀錄於 `sprout-preflight/sprout-061-host.sha256`。
- 同步查明先前 `0.5.0` 與初跑 `0.6.1` 無法載入 `libsprout-core.so` 之根因：`sprout` 不會繼承呼叫端 `SPROUT_PASSTHROUGH`，只會自動納入 `$PREFIX` 與隔離 `$HOME`，因此置於 `$HOME` 外之測試 `host-061/` 會被 `sprout-super` 重複加上 `SPROUT_ROOTFS` 前綴而 `ENOENT`。將測試二進位整備於隔離 `$HOME/host-061` 後，以原生 runner（`TracerPid=0`）跑通 `sprout-headless-061.py`（`RC=0`）：`fast8` 回報 `MECHANISM=ORDINARY NOBLE_HEADLESS_OK`，`sprout-0.6.1` 回報 `MECHANISM=PRELOAD NOBLE_HEADLESS_OK`，4 個 rootfs 核心檔 SHA256 前後一致。
- 同日 5 組交替（+1 warmup）`40× /usr/bin/true` 短啟動微基準（`-0 --link2symlink`，記錄於 `sprout-preflight/headless-061.json`）：`fast8` 中位數 **`71.20 ms`**（`68.47`–`76.79 ms`）vs `sprout-0.6.1` 中位數 **`102.73 ms`**（`101.59`–`114.44 ms`），配對中位數差 **`-45.28%`**（`sprout-0.6.1` 在 `-0` shadow 模式下短行程 exec-chain 較慢）。
- **Sprout 0.6.1 完整無頭相容性與 5 組交替 A/B（記錄於 `sprout-preflight/sprout-061-full-ab.json`，對照基準為 `fast8`）**：
  - 相容性 4/4（`compat`、`static_probe`、`dpkg_query=91`、`pipe_seq=5`）在 `fast8`、`sprout-fakeroot`（`-0 --link2symlink`）與 `sprout-nofakeroot`（`--link2symlink`）皆 `rc=0` 通過；唯 `static_probe`（靜態二進位）在 `fast8` 回報 `uid=0`，而在 `sprout` 雙模式下皆回報真實 `uid=10365`。
  - **`stat`**（`50k stat + 50k statx`）：`fast8` 中位數 `5817.44 ms` vs `sprout-fakeroot` `224.53 ms`（降幅 **`96.14%`**）、`sprout-nofakeroot` `223.8 ms`（降幅 **`96.15%`**）。
  - **`fileio`**（`15k open/read/close + walks`）：`fast8` 中位數 `1585.05 ms` vs `sprout-fakeroot` `525.29 ms`（降幅 **`66.86%`**）、`sprout-nofakeroot` `518.54 ms`（降幅 **`67.29%`**）。
  - **`sustained`**（5 秒混合工作負載，均完成 `99 execs`）：`fast8` 中位數 `15500 ops`（`5018.55 ms`）vs `sprout-fakeroot` `112850 ops`（**`7.281×`**，`5026.25 ms`）、`sprout-nofakeroot` `95200 ops`（**`6.142×`**，`5029.22 ms`）。

目前的微基準不量測顯示呈現；外部記載之 `10.4× vkmark` 數據僅屬外部紀錄，**不得當成本機實測收益**。在完成固定 Mesa、解析度與畫質的本機顯示對照與後續規劃評估前，沒有開啟 5.5 的依據，Wayland 維持暫停；完整後續規劃與缺口核對見 [`STAGE5-ROADMAP-AND-GAP-AUDIT-20261126.md`](STAGE5-ROADMAP-AND-GAP-AUDIT-20261126.md)。

## 現役核對

`live.sha256` 涵蓋現役 fast8 wrapper、binary、loader、daemon、runner 和 `/usr/local/bin/f8-shard`，於 Track 1（Sprout 0.6.1 建置／A/B）與 Track 2（`fast9` 建置／歸因測試）全部完成後再次執行 `sha256sum -c` 6/6 全數 `OK`；隔離 `ubuntu-noble-arm64` 4 個核心檔（`usr/bin/true`、`libc.so.6`、`etc/os-release`、`bin/sh`）SHA256 4/4 前後一致。實驗全程未啟動顯示或使用 ADB。
