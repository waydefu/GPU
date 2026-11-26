# Stage 5 — `proot-fast9` 現役正式部署與 30 分鐘穩定性壓測結案報告（2026-11-26）

> **最新裁決狀態（2026-11-26 22:28）：`LIVE_REDEPLOY_AND_VERIFY_PASS`**。`proot-fast9 + 09b`（`5.1.107.92-fast9`，補丁 `01..09 + 09b-terra-claude-host-fix.patch`，`out8/bin/proot-fast8` SHA256 `2524856b351a740021c189a32bbf94c7393af51e5ef4f6dcb304833c8e313af3`）已完成原子重部署至現役 `out8/`，通過全部部署閘門、C 回歸、live `f8-shard` 啟動 `claude-desktop` + `org.freedesktop.secrets` 與全應用實機驗收，詳見**第十節（Section X）**。`src/f8-proot-fast` `main` HEAD 更新至 `ab18e49`；最新 `fast8` 備份位於 `backups/out8-fast8-20261126-222816`（`205447` 備份亦完整保留）。
>
> **歷史脈絡紀錄**：初版 `proot-fast9`（`01..09`）於 30 分鐘壓測獲 `DEPLOY_AND_SOAK30M_PASS`，隨後因使用者重啟桌面觸發回歸回退至 `fast8`（`ROLLBACK_PASS`）並合入 `09b` 修復（見**第九節 Addendum**），現已由**第十節**之 `fast9+09b` 現役重部署與全應用驗收接替生效。Stage 6 後續請見 [`STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md`](./STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md)。

---

## 一、裁決總覽（`DEPLOY_AND_SOAK30M_PASS`）

| 項目 | 結果 / 數值 | 說明 |
|---|---|---|
| **日期** | `2026-11-26` | POCO F8 Ultra（`myron`），Ubuntu 24.04 ARM64 PRoot |
| **部署目標** | `/data/data/com.termux/files/home/build/proot-fast/out8/` | 現役 `proot-fast8` 路徑升級為 `proot-fast9`（`5.1.107.92-fast9`） |
| **主動二進位版本** | `5.1.107.92-fast9` | `bin/proot-fast8` SHA256 `e12dc41e3caf0178e91027e178b0639ce6c9cffd5ddba1d976447388ec35fd6c` |
| **選擇性合入 Git HEAD** | `src/f8-proot-fast` `main` @ `8b043ff` | 由 `ee603b8` 前進 7 筆 commit；隔離倉 `src/f8-proot-fast-stage5` 保持 `5541ef7` 潔淨 |
| **部署與壓測總裁決** | `DEPLOY_AND_SOAK30M_PASS` | 產物一致性 `PARITY_PASS` → `DEPLOY_PASS` → 即時驗收 `6/6 PASS` → 30 分鐘壓測 `500/500 PASS` |
| **後續階段指標** | Stage 6 Android 宿主最佳化 | [`STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md`](./STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md) |

---

## 二、部署前產物一致性與窗口稽核（`PARITY_PASS`）

1. **補丁集一致性**：`01`–`06` 補丁檔之 SHA256 於 `src/f8-proot-fast/patches/`、`src/f8-proot-fast-stage5/patches/` 與 `fast8/patches.sha256` 三處完全一致。
2. **源碼與編譯參數一致性**：以乾淨 `proot-5.1.107.92.zip` 搭配 `01`–`09` 補丁（`patch -p1 --fuzz=0`）展開後，與已驗證之 `$STAGE/fast9-combined/source` 比對為 `0 diff`，編譯旗標（含 `PROOT_UNBUNDLE_LOADER` 與 `-DVERSION="5.1.107.92-fast9"`）完全一致。
3. **部署窗口潔淨度**：
   - 無重型編譯或 `apt`/`dpkg` 鎖定進行中。
   - `shard-daemon.sh`（PID `17875`）處於單實例閒置狀態。
   - 部署前基準 `/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp/live.sha256` 檢查 `6/6 OK`。
   - 採用 `cp *.new && mv -f` 原子替換，確保執行中之舊行程維持既有 inode 不中斷。

---

## 三、`fast8` 完整備份與正式部署雜湊紀錄

### 3.1 `fast8` 備份與歷史證據保護

- **備份目錄**：`/data/data/com.termux/files/home/build/proot-fast/backups/out8-fast8-20261126-205447`
- **`backup.sha256` 驗收**：**`4/4 OK`**

| 檔案（相對於備份目錄） | SHA256 |
|---|---|
| `bin/proot-fast8` | `e401eb6caa126f1e36dbb66d23c55735082af3688dfb1752972dda0146f8267c` |
| `libexec/loader` | `eab6b2135421a2e0268832cf171d877146a9e816d7b060ce425e5017d65f08a6` |
| `libexec/loader32` | `91381891fa2627a4573705a754eced936b3ba1159c9f6d041b6472f26189f46a` |
| `auto/proot-fast8` | `f1c211fd6571d29bd4cde93a2f13a49b0463c2e5b1e288e5f1dd27c27183e552` |

- 歷史 `$STAGE/live.sha256`（`/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp/live.sha256`）完整保留未改寫。

### 3.2 原生部署與全量 SHA256 清單

- **部署執行**：透過原生 `termux-bg-run`（`TracerPid=0`）執行部署，耗時 `6.64s`，`rc=0`，輸出 **`DEPLOY_PASS`**，客體 `dpkg-query` 驗證 **`1514` packages**。
- **`live-fast9.sha256`（`7/7 OK`）與 `out8/deployed.sha256`（`3/3 OK`）**：

| 檢查檔案 | 目標路徑 | SHA256 | 狀態 |
|---|---|---|---|
| `live-fast9.sha256` | `/data/data/com.termux/files/home/build/proot-fast/out8/auto/proot-fast8` | `f1c211fd6571d29bd4cde93a2f13a49b0463c2e5b1e288e5f1dd27c27183e552` | OK |
| `live-fast9.sha256` / `deployed.sha256` | `/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8` | `e12dc41e3caf0178e91027e178b0639ce6c9cffd5ddba1d976447388ec35fd6c` | OK |
| `live-fast9.sha256` / `deployed.sha256` | `/data/data/com.termux/files/home/build/proot-fast/out8/libexec/loader` | `eab6b2135421a2e0268832cf171d877146a9e816d7b060ce425e5017d65f08a6` | OK |
| `live-fast9.sha256` / `deployed.sha256` | `/data/data/com.termux/files/home/build/proot-fast/out8/libexec/loader32` | `91381891fa2627a4573705a754eced936b3ba1159c9f6d041b6472f26189f46a` | OK |
| `live-fast9.sha256` | `/data/data/com.termux/files/home/build/proot-fast/shard2/shard-daemon.sh` | `8becae04d2d1e58b544727741f87b6af8fd7d72a230d56dd138ab63af9bd2c87` | OK |
| `live-fast9.sha256` | `/data/data/com.termux/files/home/build/proot-fast/shard2/shard-run.sh` | `03a249873b4e29a04546d78ab96fbb1a4b4f04330f104c168dcbc9d490a35955` | OK |
| `live-fast9.sha256` | `/usr/local/bin/f8-shard` | `7158e011aa07db1c4b5031dd64b3e2529e6aace3c99445768bda830d96fa2e3d` | OK |

- **`ubu-core.sha256`（`4/4 OK`）**：
  - `usr/bin/true`: `a82c1b5fd392d72148d53992a860224ff3753cb2dc8909e9bdd1620e54ee1b88` (`OK`)
  - `usr/lib/aarch64-linux-gnu/libc.so.6`: `6e3cc56b98887cb3cc2a9fe78b6dd4610184aa27bd05d592cb287db93e82d494` (`OK`)
  - `etc/os-release`: `01af466feb100306498c86aa6bad1815e33036019aa34d4362c20f374ea5c829` (`OK`)
  - `bin/sh`: `c883d9c27228339580994a1d0ea960645368c7d1b960a712bd0c655860c2d0d7` (`OK`)
- **執行期過渡行為**：既有執行中之 Stable `:1` 桌面行程繼續於原 `fast8` inode 上無縫運行不中斷，待使用者下次手動重開桌面後自動切換為 `fast9`；新生成之 `f8-shard` worker 則已即時運行現役 `5.1.107.92-fast9`。

---

## 四、部署後 6 項實機即時驗收（6/6 PASS）

| 驗收項目 | 實測結果 |
|---|---|
| **1. 版本與 Loader 綁定** | `out8/bin/proot-fast8` 與 `out8/auto/proot-fast8` 皆回報 `5.1.107.92-fast9`，內嵌參考 `out8/libexec/loader`（無任何 `proot-stage5` 或 `PROOT_SYSCALL_STATS` 殘留）。 |
| **2. `fast9_regress` 4 模式** | 預設 `109 ms`、`PROOT_BWRAP_COMPAT=1` `107 ms`、`PROOT_NO_SECCOMP=1` `117 ms`、`PROOT_STAT_AT_ENTER=0` `102 ms`（4/4 PASS）。 |
| **3. Electron `44.9.1`** | `E_OK 44.9.1`（`342 ms`，`rc=0`）。 |
| **4. Playwright Chromium 153** | `libnopci.so`，3 並發分頁：`PW_RESULTS=PAGE_0_OK,PAGE_1_OK,PAGE_2_OK`（`1162 ms`，`rc=0`）。 |
| **5. Adreno 840 Vulkan** | `/opt/mesa-kgsl` Mesa `26.0.6`：`VK_KGSL_OK`，`submit` `204.48 ms`、`render1080p` `158.23 ms`（`rc=0`）。 |
| **6. Live `shard-daemon.sh`** | 單實例 PID `17875`（`FD 0,3 -> ctl.fifo`、`FD 9 -> daemon.lock`）；`/usr/local/bin/f8-shard` 生成 shard `24277` 運行 `5.1.107.92-fast9`，`0` 孤兒 PID。 |

---

## 五、30 分鐘現役工作站連續穩定性壓測（`SOAK_STATUS: PASS`）

原始產物位於 `/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp/`：
- [`live-fast9-soak30m-summary.json`](/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp/live-fast9-soak30m-summary.json)
- [`live-fast9-soak30m.jsonl`](/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp/live-fast9-soak30m.jsonl)
- [`live-soak30m.log`](/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp/live-soak30m.log)
- [`live-soak30m.rc`](/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp/live-soak30m.rc)（`0`）

| 指標維度 | 實測數值（62 筆採樣 / 500 批次） |
|---|---|
| **總時長與批次** | `elapsed_s = 1805.48 s`；`500/500` batches PASS（`batches_fail = 0`） |
| **批次與 Tracer 延遲** | `batch_ms` 中位數 `2505.81 ms`（p95 `2808.48 ms`，min `2103.85 ms`，max `3424.12 ms`）；`tracer_cpu_ms` 中位數 `630.0 ms`（p95 `740.0 ms`） |
| **Chromium 153 `rAF` 與互動** | 共 `90,000` `rAF` 幀：`p50 = 16.7 ms`、`p95 = 16.7 ms`、`p99 = 16.8 ms`（max `166.7 ms`）；`jank > 20ms = 45`（`0.050%`）、`jank > 33ms = 26`（`0.029%`）；啟動中位數 `195.34 ms`（p95 `259.56 ms`）、點擊 `p95` 中位數 `92.28 ms` |
| **Adreno 840 Vulkan 檢查點** | `7/7` checkpoints PASS（`failed = 0`） |
| **記憶體與 Swap 趨勢（無洩漏）** | 整樹 `peak_pss_mb`：`318.8 -> 311.8 -> 309.9 MB`（中位數 `296.4 MB`，max `327.9 MB`）；`MemAvailable`：`3866.6 -> 3716.5 -> 3959.0 MB`（min `3254.5 MB`）；`SwapFree`：`9151.1 -> 8994.9 -> 9259.3 MB`（min `8305.5 MB`） |
| **溫度與時脈** | CPU 溫度 `49.0–71.4 °C`（中位數 `56.3 °C`）；GPU 溫度 `45.1–62.9 °C`（中位數 `49.8 °C`）；`cpu6` max freq `1862.4–2880.0 MHz`（中位數 `2227.2 MHz`） |
| **Daemon 與殘留稽核** | `shard-daemon.sh` PID `17875` count `1..1`、FD `7..7`（`fds_drift = 0`）；`max_orphan_pids = 0` |
| **壓測後完整性驗證** | `ubu-core.sha256` `4/4 OK`；`out8/deployed.sha256` `3/3 OK` |

---

## 六、`src/f8-proot-fast` `main` 選擇性合入紀錄（`ee603b8` -> `8b043ff`）

### 6.1 合入 Commit 清單（7 筆）

| Commit | 訊息 |
|---|---|
| `e1adf15` | `fix(tests): propagate daemon wipe failures` |
| `d2d9370` | `fix(tests): prove daemon exit independently of command line reads` |
| `9968a00` | `feat(fast9): add isolated ioctl BPF, GETEVENTMSG, and no-close-stop patches` |
| `1d680c4` | `fix(tests): return nonzero exit code on fail/invalid verdicts in shard judges` |
| `4128208` | `feat(scripts): add read-only Android host audit script and fix thermal parsing` |
| `344b676` | `feat(deploy): add verified fast9 deploy and fast8 one-key rollback scripts` |
| `8b043ff` | `docs(readme): record live proot-fast9 deployment SHA256s, patches 07-09, and fast8 rollback` |

### 6.2 異動檔案清單（13 檔）

- 修改（`M`，5 檔）：`README.md`、`tests/autoshard_judge.py`、`tests/daemon/test_daemon_wipe.sh`、`tests/shard_judge.py`、`tests/test_shard_judge.py`
- 新增（`A`，8 檔）：`deploy/deploy-proot-candidate.sh`、`deploy/rollback-to-fast8.sh`、`patches/07-proot-fast9-ioctl-bpf.patch`、`patches/08-proot-fast9-geteventmsg.patch`、`patches/09-proot-fast9-no-close-stop.patch`、`scripts/android-host-audit-readonly.sh`、`tests/fast9_regress.c`、`tests/test_autoshard_judge.py`

### 6.3 明確排除與合入前驗證

- **明確排除項目**：`fast10`（patches `10`–`11`）、`hybrid/`、`Mesa 27`、`bench_workstation_abba.py` 均未合入 `main`（保留於研究檔案或 `stage5/isolated-fast8-20261126` 歷史分支）。
- **合入驗證**：`29/29` judge 單元測試 PASS、`bash -n` 語法檢查 PASS；`deploy-proot-candidate.sh` 之 `TracerPid=0` 守門於 PRoot 環境內實測阻擋生效（`rc=2`）。

---

## 七、一鍵回退與即時降級開關

- **一鍵還原至已驗證 `fast8` 備份**（需透過 `termux-bg-run` 於原生 Termux `TracerPid=0` 執行 [`rollback-to-fast8.sh`](../../../src/f8-proot-fast/deploy/rollback-to-fast8.sh)）：
  ```bash
  # 先行 dry-run 驗證 backup.sha256 與備份二進位
  /usr/local/bin/termux-bg-run -- /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/root/projects/GPU加速/src/f8-proot-fast/deploy/rollback-to-fast8.sh --dry-run

  # 確認需回退時再執行正式還原
  /usr/local/bin/termux-bg-run -- /data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/root/projects/GPU加速/src/f8-proot-fast/deploy/rollback-to-fast8.sh --apply --confirm-live
  ```
- **免換檔即時降級開關**：
  - `F8_NO_SHARD=1`：單次指令略過 `f8-shard` 自動分流。
  - `PROOT_STAT_AT_ENTER=0`：停用 `stat`/`fstat`/`statx` enter-time 代答。
  - `touch ~/.f8-proot-stock`：於 Termux 建立標記檔後重開桌面，全桌面切回原版 `proot`。

---

## 八、後續階段

- **Stage 6 Android 宿主效能與電源最佳化計畫**：[`STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md`](./STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md)（待開啟無線偵錯後透過隔離 `-P 5038` 先取證再對照三電源模式）。
- **Stage 5 Phase 3 收斂與隔離驗收報告**：[`STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md`](./STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md)。

---

## 九、Addendum（2026-11-26 21:52–22:20）：重啟回歸、緊急回退、`09b` 修復與隔離 `fast9+09b` 實機全應用驗收

### 9.1 桌面重啟後回歸現象、鑑識根因與立即回退（21:52–22:00）

- **回歸現象**：使用者重啟桌面切換至初版 `proot-fast9`（`e12dc41e…`，僅含補丁 `01..09`）後，`claude-desktop`（`SIGTRAP`、`rc=133`）、`chatgpt`（`GPU process exited unexpectedly: exit_code=5`）與 `cursor` 皆無法開啟；因 `claude-desktop` 在進入 D-Bus 流程前即已崩潰，D-Bus `org.freedesktop.secrets`（`gnome-keyring`）亦未被觸發。
- **鑑識根因**：2026-11-12 現役 `fast8`（`e401eb6c…`）曾帶入一筆樹外補丁 `/data/data/com.termux/files/home/build/proot-fast/releases/claude-memfd-20261112-083006/terra-claude-host-fix.patch`，於潔淨 `01..09` 重建時遺漏。完整二進位／ELF／loader／腳本鑑識比對確認：**僅** `terra-claude-host-fix.patch` 屬實質功能遺漏，`loader`、`loader32`、`auto/proot-fast8`、`shard2/` 與 `f8-shard` 均為 `0 diff`。
- **緊急回退**：立即於原生 Termux 執行 `rollback-to-fast8.sh --apply --confirm-live --backup-dir .../backups/out8-fast8-20261126-205447` 還原 `out8/`，耗時 `0.18 s`，輸出 **`ROLLBACK_PASS`**：
  - `live.sha256`：**`6/6 OK`**（`out8/bin/proot-fast8` 恢復為 `e401eb6caa126f1e36dbb66d23c55735082af3688dfb1752972dda0146f8267c`）
  - `ubu-core.sha256`：**`4/4 OK`**
  - `shared-memory-region` 符號處理行為恢復，`claude-desktop` 探針已可通過啟動階段、不再發生 `SIGTRAP`。

### 9.2 `src/f8-proot-fast` `main` 修復收斂（`8b043ff` -> `e1894a8`）

| Commit | 變更內容 |
|---|---|
| `f06621a` | 新增 `patches/09b-terra-claude-host-fix.patch`（SHA256 `7ad407ce…`，於 `01..09` 之上以 `--fuzz=0` 潔淨套用）；擴充 `tests/fast9_regress.c`（驗證 `memfd_create("shared-memory-region")->ENOSYS`、`/proc/self/fd` `O_RDONLY\|O_CLOEXEC` + `O_PATH`、`/dev/fd/1` `O_CLOEXEC`）；硬化 `deploy/deploy-proot-candidate.sh`（強制檢查 `shared-memory-region` 字串、fail-closed `fast9_regress` 閘門、Xvfb `claude-desktop` non-SIGTRAP 閘門）。 |
| `e1894a8` | 更新 [`src/f8-proot-fast/README.md`](../../../src/f8-proot-fast/README.md)，補齊 `09b` 補丁表、擴充回歸測試說明與現役 `out8/` 已回退狀態。 |

- **倉庫驗證**：`bash -n` 通過、`29/29` judge 單元測試 PASS、`deploy-proot-candidate.sh` 之 `TracerPid != 0` 守門實測阻擋生效（`rc=2`）。隔離倉 `src/f8-proot-fast-stage5` 維持 `5541ef7` 潔淨。

### 9.3 隔離 `fast9+09b` 重建與實機全應用驗收（`ALL_REAL_APPS_PASS`）

- **隔離編譯與 Dry-Run**：
  - 隔離產物 `$STAGE/fast9-memfd-20261126/bin/proot-fast8`（版本 `5.1.107.92-fast9`，SHA256 `19831b8a5f485d106c73984b1602b3c50f36bcf792b28b64d6ba813f5e7adbf6`，已含 `shared-memory-region`）。
  - `deploy-proot-candidate.sh --dry-run --regress-bin $STAGE/fast9-memfd-20261126/fast9_regress`：**PASS**（`rc=0`，`DRY_RUN_PASS`，dry-run 候選 SHA256 `2524856b351a740021c189a32bbf94c79393af51e5ef4f6dcb304833c8e313af3`）。
- **C 語言回歸套件**：
  - `fast9_regress`：**4/4 模式 PASS**
  - `test_terra_proc_fd_reopen`：**7/7 PASS**
- **隔離實機桌面應用與工作負載測試（`Xvfb :94` + `dbus-run-session`，`F8_NO_SHARD=1`）**：

| 測試對象 | 實測結果 |
|---|---|
| **`claude-desktop`**（`--password-store=gnome-libsecret`） | 無 `SIGTRAP`，順利進入 `WebContentsViewAura` + `GNOME_LIBSECRET`；D-Bus `ListNames` 確認成功啟動 `org.freedesktop.secrets`（`:1.4`）、`org.gnome.keyring`、`org.gnome.keyring.SystemPrompter`、`org.gnome.keyring.PrivatePrompter`。 |
| **`chatgpt`** | `rc=124`（持續存活），`startupElapsedMs=4431`，Codex CLI 與 React root render 正常，無 `exit_code=5` / `Network service crashed`。 |
| **`cursor`** | `rc=124`（持續存活），成功載入 `workbench.glass.main.js`，無 `SIGTRAP`（非致命 `write(2, len=0) -> EFAULT` 已確認於現役 `fast8` 既有並記錄於 `cursor-startup-lag-case.md`）。 |
| **Electron `44.9.1`** | `E_OK 44.9.1`。 |
| **Playwright Chromium 153（3 分頁）** | `PAGE_0_OK,PAGE_1_OK,PAGE_2_OK`。 |
| **Adreno 840 Vulkan** | `submit` `173.69 ms`、`render1080p` `140.57 ms`。 |

- **目前部署狀態**：現役 `/data/data/com.termux/files/home/build/proot-fast/out8/` 維持未改動且停留在已回退之 `fast8`（`live.sha256` **`6/6 OK`**），靜待使用者明確授權後再部署已驗證之 `fast9+09b`。

---

## 十、Section X（2026-11-26 22:28）：`fast9+09b` 現役重部署與實機全應用驗收（`LIVE_REDEPLOY_AND_VERIFY_PASS`）

### 10.1 現役重部署狀態與備份

- **裁決狀態**：**`STATUS: LIVE_REDEPLOY_AND_VERIFY_PASS`**（`2026-11-26 22:28`）
- **現役版本**：`proot-fast9 + 09b`（`5.1.107.92-fast9`，補丁 `01..09` + `09b-terra-claude-host-fix.patch`）
- **二進位特徵核對**：`out8/bin/proot-fast8` 確認 `shared-memory-region` PRESENT、`PROOT_SYSCALL_STATS` ABSENT
- **備份紀錄**：已新建 `/data/data/com.termux/files/home/build/proot-fast/backups/out8-fast8-20261126-222816`（前次備份 `out8-fast8-20261126-205447` 完整保留）
- **Git 狀態**：[`src/f8-proot-fast/`](../../../src/f8-proot-fast/) `main` HEAD 更新至 `ab18e49`（`docs(readme): record live proot-fast9+09b re-deployment SHA256s and verification`）；隔離倉 `src/f8-proot-fast-stage5` 維持 `5541ef7` 潔淨
- **Daemon 狀態**：`shard-daemon.sh` 單實例 PID `17875`，FD count `7`

### 10.2 現役 SHA256 全量校驗

- `live-fast9-09b.sha256`（`/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp/live-fast9-09b.sha256`）：**`7/7 OK`**
- `out8/deployed.sha256`：**`3/3 OK`**
- `ubu-core.sha256`：**`4/4 OK`**

| 目標路徑 | SHA256 | 校驗清單 |
|---|---|---|
| `/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8` | `2524856b351a740021c189a32bbf94c7393af51e5ef4f6dcb304833c8e313af3` | `live-fast9-09b.sha256` / `deployed.sha256` |
| `/data/data/com.termux/files/home/build/proot-fast/out8/libexec/loader` | `eab6b2135421a2e0268832cf171d877146a9e816d7b060ce425e5017d65f08a6` | `live-fast9-09b.sha256` / `deployed.sha256` |
| `/data/data/com.termux/files/home/build/proot-fast/out8/libexec/loader32` | `91381891fa2627a4573705a754eced936b3ba1159c9f6d041b6472f26189f46a` | `live-fast9-09b.sha256` / `deployed.sha256` |
| `/data/data/com.termux/files/home/build/proot-fast/out8/auto/proot-fast8` | `f1c211fd6571d29bd4cde93a2f13a49b0463c2e5b1e288e5f1dd27c27183e552` | `live-fast9-09b.sha256` |
| `/data/data/com.termux/files/home/build/proot-fast/shard2/shard-daemon.sh` | `8becae04d2d1e58b544727741f87b6af8fd7d72a230d56dd138ab63af9bd2c87` | `live-fast9-09b.sha256` |
| `/data/data/com.termux/files/home/build/proot-fast/shard2/shard-run.sh` | `03a249873b4e29a04546d78ab96fbb1a4b4f04330f104c168dcbc9d490a35955` | `live-fast9-09b.sha256` |
| `/usr/local/bin/f8-shard` | `7158e011aa07db1c4b5031dd64b3e2529e6aace3c99445768bda830d96fa2e3d` | `live-fast9-09b.sha256` |

### 10.3 部署閘門、C 回歸與實機全應用驗收

- **內建部署閘門**：`DEPLOY_PASS`、`dpkg-query` = `1514` packages、`claude-desktop` non-SIGTRAP smoke PASS（`rc=124`）。
- **C 回歸（運行於現役 `out8/bin/proot-fast8`）**：`fast9_regress` **4/4 模式 PASS**；`test_terra_proc_fd_reopen` **7/7 PASS**。
- **實機桌面應用與工作負載驗收（運行於現役 `out8/bin/proot-fast8`，`Xvfb :94`，隔離 `--user-data-dir`）**：

| 測試對象 | 實測結果 |
|---|---|
| **`claude-desktop`（經由現役 `f8-shard`）** | `tracer=14904`（非 deleted live `out8/bin/proot-fast8`，`APP_ALIVE_T3=1`）；進入 `WebContentsViewAura` + `GNOME_LIBSECRET`；D-Bus `ListNames` 確認 `org.freedesktop.secrets`（`:1.8`）、`org.gnome.keyring.SystemPrompter`、`org.gnome.keyring`、`org.gnome.keyring.PrivatePrompter`；無 `SIGTRAP`/`rc=133`。 |
| **`chatgpt`** | `rc=124`，無 `exit_code=5` / `Network service crashed` / `SIGTRAP`。 |
| **`cursor`** | `rc=124`，workbench 載入，無 `SIGTRAP`。 |
| **Electron `44.9.1`** | `E_OK 44.9.1`。 |
| **Playwright Chromium 153（3 分頁）** | `PAGE_0_OK,PAGE_1_OK,PAGE_2_OK`。 |
| **Adreno 840 Vulkan** | `submit` `183.57 ms`、`render1080p` `142.34 ms`。 |
