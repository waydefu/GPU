# HANDOFF — 2026-09-24 15:00：PRoot 追蹤器開銷（進行中）＋ 今天 GPU／Electron 的結論

**新對話先讀：** 本檔 → `evidence/session/proot/PROOT-TRACER-OVERHEAD-01.md` → `evidence/session/proot/PROOT-BENCH-01-FREEZE.md`（含文末「凍結後、資料前的發現」）。
GPU 的脈絡在 `HANDOFF-NEXT-SESSION-20260924-GL.md`（兩次更新都在檔尾）。回覆用繁體中文、使用者要**白話簡單**；指令、檔名、verdict token 保持英文。

## 使用者目標（今天的走向）
「讓平常用的程式（Codex、Claude、Hermes、Cursor 以及之後所有程式）用上 GPU」→ 查完結論是：路通了但 Electron 沒收益 →
使用者選「**查開銷**」→ 追到 PRoot 追蹤器 → 選「**1：先做實際程式的對照測試**」（PROOT-BENCH-01），**正在做工具，尚未有受判資料**。

## 今天的結論（都有證據、判準先凍結）
| 項目 | 結果 | 文件 |
|---|---|---|
| glmark2／vkmark 安裝 | 經 `adb run-as com.termux`（Termux 是 debuggable；PRoot 的假 root 會被 Termux apt 拒絕） | 記憶 termux-pkg-via-adb-run-as |
| 3D benchmark | GL-BENCH-01 觸控作廢；**GL-BENCH-02：GL_GPU_BENEFIT、VK_GPU_BENEFIT**（快 4–5×、每幀 CPU 0.1–0.18×） | `evidence/session/gl/GL-BENCH-02-RESULT.md` |
| Ubuntu 程式碰到 GPU | 自編 `/opt/mesa-kgsl`（Mesa 26.0.6 Turnip KGSL＋Zink，打 Termux 0017/0018/0019）；關鍵：手機 `UBWC_MODE=6` | `gl/MESA-KGSL-UBUNTU-BUILD-01.md` |
| Electron 開 GPU 會死 | ANGLE 載入 libpci 找不到 `/proc/bus/pci` 就 `exit(1)`；`libnopci.so` 攔截 | `gl/ELECTRON-GPU-PROBE-RESULT.md` |
| Cursor 開 GPU | **ELECTRON_GPU_NO_BENEFIT**（安全但 CPU 只少 3.5%；Cursor CPU 幾乎全是 JS；閒置就吃 0.33 核） | `gl/ELECTRON-BENCH-01-RESULT.md` |
| 滑掉實驗版 → X 結束 | Gate A `GATEA_FATAL_HALT what=x-hup reason=6` **設計停機**；我一度誤判為 EXA FatalError，已在文件開頭更正 | `gl/INCIDENT-20260924-X3-EXA-BUG-FATAL.md` |
| `EXA bug: devPrivate.ptr` 警告 | 非致命、幾乎每次都有；兩份 RCA（使用者啟動的背景 session 產出，**我只看過判決表、未完整審閱**）：不畫錯、不洩漏、違反 EXA 契約，附修法 | `gl/RCA-EXA-DEVPRIVATE-WARNING.md`、`gl/RCA-X3-EXA-DEVPRIVATE-SWIPE.md` |
| **PRoot 追蹤器開銷** | termux/proot `4abc88b5c`（2026-05-23，只為 bwrap `--unshare-net`）把 send/recv 全攔；PRoot 內 socket send+recv 55.5 µs vs write+read 1.56 µs | `proot/PROOT-TRACER-OVERHEAD-01.md` |
| proot-fast 原型 | 同版本＋`proot-fast-bwrap-compat.patch`（socket／clone 攔截改 `PROOT_BWRAP_COMPAT` 才開）；微基準 send+recv 55→1 µs、sendmsg+recvmsg 56→29 µs（fake_id0 仍攔 sendmsg）；對照組（開關開）回到 55 µs | 同上、`proot/proot-fast-bench-03.txt` |

## 進行中：PROOT-BENCH-01（Cursor 在 proot-fast 對系統 proot）
- 判準 **FROZEN**：`S`＝捲動＋打字 CPU（Cursor session＋它的追蹤器＋X3），`PF ≤ P0 × (1 − max(0.10, 2×noise))`，閒置 ≤ +0.05 核，幀不變差，功能正常；兩次重複；
  順序 rep01 P0→PF→P0'、rep02 PF→P0→PF'。
- 工具（fork `waydefu/termux-x11` worktree `src/f8-ahb-exa-async`，commit **`22137ff` WIP**，本地未 push）：
  `tests/proot/proot_bench_launch.sh`（PRoot 外、run-as 啟動新 proot＋Cursor）、`proot_bench.sh`（cell）、`proot_bench_judge.py`（`--selftest` 8/8）、
  `proot_meter.py`（**新寫、未整合**）、`proot-args.txt`（日常 proot 的 42 個參數）。driver `tests/gl/electron_bench_drive.mjs` 多了選用的 `EXTRA_PIDS`。
- **乾跑 `evidence/session/proot/proot-bench-dryrun-01` 發現**（詳見凍結文件文末）：
  1. run-as 啟動的程序是 SELinux `runas_app`，日常 PRoot 讀不到它們的 `/proc` → session CPU 0、追蹤器 null。**計量必須在 run-as 側做**。
  2. P0 的 Cursor 在新 proot 裡功能正常（焦點、翻頁、打字都生效）。
  3. PF 開始後 mem-guard 觸發（2995 < 3000 MB）→ runner 中止。當時 5 個 Claude Code 程序＋Claude Desktop 佔很多記憶體。
- **下一步（照順序）**：
  1. 把 `proot_meter.py` 接進 `proot_bench.sh`：每輪 launch 前用 `adb run-as` 背景啟動 meter（Termux python，CSV 寫到 `$PREFIX/tmp/proot-bench/`，
     stop 檔結束），結束後把 CSV 複製進 cell 目錄；`tracer_arg0` 改讀 CSV 表頭。
  2. judge 改用 CSV：以 driver 各快照的 `t` 在 CSV 上線性內插 session／tracer／x3 ticks；有效性加「CSV 樣本涵蓋每個階段邊界（±0.5 s）」與「tracer ticks 非空」。
     合成測試加 CSV 版本，必須含會紅的案例。
  3. `proot_bench.sh` 每輪開跑前等 MemAvailable ≥ 4600 MB（20 s，最多 300 s）並記錄。
  4. 乾跑 02（P0、PF 各一輪，只看欄位）→ commit（非 WIP）→ 把雜湊補進凍結文件 → 正式兩次重複（約 25–30 分鐘，請使用者不要碰手機）。
  5. 有收益才討論「換掉日常桌面的 proot」（要整個 PRoot 重開；先問使用者）。另可考慮回報 termux/proot 上游（對外發文，需同意）。

## 目前環境狀態（2026-09-24 14:58 核對）
```
實驗版         1.03.01-f592241-24.09.26（APK f9e35b69…075c），MODE=G；X root 1200×2416（按鍵列隱藏）
包包模式       evidence/session/gl/exp-pocket-prefs.sh 仍套用中（按鍵列隱藏／下滑、返回無動作／Never keep screen on）；restore 還原
桌面圖示       「F8 鍵盤列（實驗版）」＝ /usr/local/bin/f8-ekbar-toggle com.waydefu.x11gpu（原腳本備份 .bak-20260924）
ADB            lane 5038，10.191.48.13:38869（會變；mdns 重探，舊 endpoint 會被一起廣播）
proot-fast     ~/build/proot-fast/out/bin/proot-fast（SHA256 2a513992…5aba），loader 在 ~/build/proot-fast/out/libexec；未取代系統 proot
日常 proot     pid 20095（系統 5.1.107.92），沒有動
/opt/mesa-kgsl 自編 Mesa（opt-in 環境變數，見 MESA-KGSL 文件）；日常啟動器都沒改（仍 --disable-gpu）
殘留          無 Cursor／X3／proot-fast／meter 程序
fork commits  8b905a2（GL-BENCH）、a4440fa（ELECTRON-BENCH）、22137ff（PROOT-BENCH WIP）——全部本地、未 push
```

## 會咬人的事（今天真的踩過）
- **不要在 PRoot 裡跑 Cursor／Chromium**：我這個 shell 的 `DISPLAY=:1.0`（使用者日常桌面）。所有 Cursor 都只經 runner 在 `:3` 啟動。
- **用 `$!` 當 pgid 會打偏**：本機除錯留下 4 組 Cursor（5.3 GB）。一律用 session id（`setsid bash -c 'echo $$ > file; exec …'`）並在結束後掃殘留。
- **`$(...)` 是子 shell**：在裡面設定的全域變數（例如錄製器 pid）會遺失。
- **Termux 的 `LD_PRELOAD=libtermux-exec.so` 不能漏進 glibc guest**（proot-fast-bench-01 全部 libc 載入失敗）。
- **`am broadcast` 會吃 stdin**：在 `while read` 迴圈裡要 `</dev/null`。
- **meson 會自動下載子專案**：一律 `--wrap-mode=nofallback`。
- **make 命令列上的 CPPFLAGS 會蓋掉 makefile 的 `-I`**：改用環境變數。
- **使用者手機**：跑測試時會碰到（Cursor 的 EFAULT 告警視窗、通知）；要事先講「不要碰、不要切 App、不要滑掉實驗版」。滑掉實驗版＝Gate A 停機、整個 :3 結束。
- **量 PRoot 追蹤器要在 PRoot 外量**（`adb run-as`＋Termux python）；PRoot 內的量測程式本身會被追蹤。
- Cursor 的 EFAULT 告警（`execSync` 轉寫子程序 stderr 時失敗）是舊毛病、每次開機幾乎都有、不影響自動操作；我測過「長度 0 的寫入」假設，**被推翻**，根因未查。

## 更新 2026-09-24 晚（session 51abd7ec）：PROOT-BENCH-01 結案 → `PROOT_FAST_NO_BENEFIT`
- 結果：`evidence/session/proot/PROOT-BENCH-01-RESULT.md`。PF 讓追蹤器少約 30%（0.40 → 0.28 核），但總量只少 5–9%，未達 10% 門檻；六輪全 VALID、Stable 不變、殘留 0。
  **不建議換掉日常 proot**。若續攻 PRoot：先拆解追蹤器剩下 0.28 核花在哪些 syscall（新方向，要問使用者）。
- 工具：fork `9f7bad4`（WIP 標籤、本地未 push）＝乾跑 02 驗證過的版本；計量與結束都改在 run-as 側（乾跑 01 的 `survivors=0` 是假的，已記入凍結文件）。
- ADB：PRoot 內重起 adb server 要帶 `ADB_VENDOR_KEYS=/data/data/com.termux/files/home/.android/adbkey`，否則 `CERTIFICATE_UNKNOWN`（記憶 device-run-hazards）。
- 儲存空間：清掉舊 APK、ChatGPT 舊 deb、結案測試的 Cursor profile、npm/uv/pnpm/pip/chromium 快取，可用 42.4 → 45.8 GB。
  Claude Code `2.1.275` 等本 session 結束後可刪（`/root/.config/Claude/claude-code/2.1.275`）。
- 包包模式仍套用中（`evidence/session/gl/exp-pocket-prefs.sh restore` 還原）。

## 使用者授權（2026-09-24 19:32:59 +0800，session 51abd7ec）
「這兩小時內測試都不用問我，我完全授權並且不碰手機，若有要決議你決定即可，以目前能解放的全效能為最終目標，若成功後看能否轉為日常使用」
→ 有效到 2026-09-24 21:32:59。範圍：效能測試與可還原的日常環境調整；不含 root、不碰 Stable X server 本身（com.termux.x11 / :1 程序）。

## 更新 2026-09-24 20:50（授權時段內）：kompat 根因＋proot-fast v2＋PROOT-BENCH-02
- 根因：`--kernel-release` 啟用 kompat，白攔 futex／epoll_pwait 等並拿掉 vDSO → `evidence/session/proot/PROOT-KOMPAT-OVERHEAD-01.md`。
- proot-fast v2（`~/build/proot-fast/out2/bin/proot-fast2`，sha `8a30e9d6`）：微基準 futex 31.6→0.23 µs；smoke 與原版逐字相同；AGENT-MIX 時間／CPU −53%／−54%。
- PROOT-BENCH-02（Cursor，判準同 01）：**`PROOT_FAST_NO_BENEFIT (rep02:FRAMES_NOT_WORSE)`**——追蹤器 −94%、S −24%、閒置 −76% 都過，
  但 r02-3-pf 一輪捲動 p95 33.3 ms（高一格 8.3 ms）使 rep02 幀條件失敗。判決凍結 → `PROOT-BENCH-02-RESULT.md`。
- 日常：`f8desk`／`f8desk-external` 已有 PD_PROOT_BIN 區塊，但 `~/.f8-proot-stock` 預設關閉；捷徑 08 開、07 關，重開桌面生效。**要不要開是使用者的選擇。**
- 可能的下一步：預先登記、專看捲動幀的 PROOT-BENCH-03（更多輪），釐清 p95 那一格是否真實。
