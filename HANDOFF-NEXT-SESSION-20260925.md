# HANDOFF — 2026-09-25：PRoot 加速（proot-fast v6）已在日常上線（09:46 重開桌面後生效、09:52 核對通過）

**新對話先讀：** 本檔 → `evidence/session/proot/PROOT-FAST6-STATX-AT-ENTER-01.md` → `PROOT-FAST5-STAT-AT-ENTER-01.md` → `PROOT-KOMPAT-OVERHEAD-01.md`。
舊交接 `HANDOFF-NEXT-SESSION-20260924-PROOT.md`（檔尾有逐段更新）是本檔的詳細版；GPU／Electron 脈絡在 `HANDOFF-NEXT-SESSION-20260924-GL.md`。
回覆用繁體中文、**白話簡單**；指令、檔名、verdict token、commit／PR 保持英文。

## 使用者目標
「解放手機效能，讓日常程式（Claude、ChatGPT／Codex、Hermes、Cursor、之後所有程式）的 CPU／GPU 收益最大化」，成功的再轉為日常使用。
不考慮 root。GPU 路線對日常程式收益小（Electron 瓶頸在 JS；使用者沒有 3D 程式；影片用 Android Chrome 已是硬體解碼）。
**真正的瓶頸是 PRoot 追蹤器**（單執行緒、每個被攔的 syscall 停一次 ~30 µs），這兩天的成果都在這條線上。

## 目前狀態（2026-09-25 09:36 核對；09:52 更新日常 PRoot 一列）
| 項目 | 狀態 |
|---|---|
| 日常啟動器 | `$PREFIX/bin/f8desk`／`f8desk-external` 的 PD_PROOT_BIN 區塊：**v6 → v5 → v2 → 原版**（備份 `*.bak-20260924-pf2`、`*.bak-20260925-v5`、`*.bak-20260925-v6`） |
| **正在跑的日常 PRoot** | **v6**（`proot-fast6` pid 15010，09:46 重開桌面（推測經「F8 工作站」關閉→重開，未直接觀察）；`/proc/15010/exe` sha256 `2d5596dc…` 與 out6 一致；本 Claude session 的 TracerPid＝15010）。v2 已退役（pid 17477 已結束）；**v5 從未在日常上線過** |
| 切回原版 | 小工具「F8 設定」建立 `~/.f8-proot-stock` → 重開桌面 |
| getifaddrs 補丁 | `/etc/ld.so.preload` → `/usr/local/lib/libf8ifaddrs.so`（sha 6530de35）；還原＝刪 `/etc/ld.so.preload` |
| 小工具 | 8 → 3：`F8 工作站`（開／切到／關）、`F8 外接`（外接 App／外接 Linux／滿版／滑鼠）、`F8 設定`（proot 加速／原版）；舊的在 `~/.shortcuts-backup-20260925/` |
| 螢幕設定（使用者自己跑的） | `screen_optimize_mode=2`、`hide_gesture_line=1` → **實驗版 X root 變 1200×2464**（runner 的 `EXPECT_ROOT` 要用這個） |
| 儲存空間 | 可用 54 GB（今天清出 ~10 GB：logs/ zstd 無損、`.cursor-test`、Cursor snapshots、快取、舊 APK） |
| PR | #21（proot v1/v2）、#22（GL/Electron）、#23（v5＋日常切換）、#24（v6，2026-09-25 09:36 使用者合併）都已合併；本交接檔另開 PR |

## proot-fast 各版本（全在 `~/build/proot-fast/`；loader 路徑編死在各自 `outN/libexec`，**不要刪 out2/out5/out6**）
| 版本 | 內容 | 產物 sha256 前綴 | 狀態 |
|---|---|---|---|
| v1 `out/` | socket／clone 攔截改成 `PROOT_BWRAP_COMPAT` 才開 | 2a513992 | PROOT-BENCH-01 NO_BENEFIT |
| v2 `out2/` | v1＋kompat-lean（不再白攔 futex／epoll 等、vDSO 回來） | 8a30e9d6 | 前日常（09-24～09-25 09:46） |
| v3 `out3/` | v2＋無相容旗標時不替換 netlink | 557a48bd | 實驗用（證明真 netlink 被拒），不部署 |
| v4 `out4/` | v2＋waitpid 前忙等 | 4647b1b9 | **假設被推翻**，不部署 |
| v5 `out5/` | v2＋newfstatat／fstat 進入時代答 | adb3d6d6 | 驗證通過 |
| **v6 `out6/`** | v5＋statx 進入時代答 | **2d5596dc** | **日常現役（09-25 09:46 起）** |
對照開關：`PROOT_STAT_AT_ENTER=0`（關 v5/v6 代答）、`PROOT_KOMPAT_FULL=1`（kompat 原行為）、`PROOT_BWRAP_COMPAT=1`（socket 攔截＋netlink 模擬）。
v5/v6 程式裡留有 `VERBOSE(tracee, 2, "v5:/v6: ...")` 追蹤，只有 `-v 2` 才印，不影響效能。

## 量到的效果（詳見各證據文件）
- **日常追蹤器（v2）**：同情境 0.360 → **0.013 核**；平均 0.28 → 0.004 核（描述性）。
- Cursor（PROOT-BENCH-02，v2）：追蹤器 −94%、活動 CPU −24%、閒置 −76%（因一輪捲動 p95 高一格而判 NO_BENEFIT）。
- 日常程式閒置（APP-IDLE-01，v2）：16/16 兩兩比較 v2 較低（chatgpt −50%、chatgptweb −10%、hermes −35%、cursor −58%）。
- **查檔案**：v5 stat −41%、fstat −45%；v6 statx −37%；AI 工具類工作 v6 比 v2 **−28%**（wall 與 CPU）。
- 每版都有：逐字相同的 smoke（stat_smoke 59 行／smoke 23 行／daily_check 14 行）＋**故意寫壞的版本被抓到**（v5b、v6b），五個日常程式健康檢查（v5-sanity-01、v6-sanity-01）。

## 下一步（照優先）
1. ~~使用者重開桌面後確認 v6~~ **已完成（09:52，描述性核對，非對照測試）**：
   - 追蹤器：`proot-fast6` pid 15010，exe sha256 `2d5596dc…`（＝out6）。
   - `sysbench2`：`vdso present`、`futex_wake 0.25 µs`、`getpid 0.19 µs`（kompat-lean 生效）。
   - `statxloop 3000` ×3：路徑 46.7–48.1 µs、nofollow 45.9–50.9、fd 29.8–29.9、不存在 45.5–46.9（預期路徑 ~60 而非 ~90；fd ≈ 單次停頓成本 → 進入時代答生效）。
     比 v6 bench 表的數字還低，但那輪整機波動大、情境不同（隔離 proot vs 日常），不做數值結論。
   - 日常追蹤器 30 s 窗：**0.007 核**（v2 時同法 0.013、原版 0.360）；累計 38 s／4.3 min＝0.148 核平均，含桌面＋Claude 啟動，不可與 v2 的 153 min 平均比。
   - 仍需使用者日常使用中留意：若有程式異常 → 「F8 設定」切原版、回報。
2. **搖桿玩遊戲時自動熄屏工具**（未開始）：使用者要「只有觸控或按鍵才算活動、2 分鐘沒碰就關手機面板、遊戲／外接螢幕／搖桿照常」。
   構想：Termux 腳本監看 `/dev/input/event7`（focaltech_ts 觸控）＋event0–4（實體鍵）的 getevent，2 分鐘無事件就用 SurfaceControl 關內建面板（scrcpy 的 turn-screen-off 同技術，需 shell 權限的 app_process），有觸控／按鍵就開回。
   **要等使用者接外接螢幕＋搖桿實測**。系統設定（逾時 2 分鐘、關「充電時螢幕不休眠」`stay_on_while_plugged_in=15`）要使用者自己改。
3. **外接螢幕同步顯示（鏡像）**：原因是開發人員選項 `force_desktop_mode_on_external_displays=1`（外接＝獨立桌面）；玩遊戲要鏡像就關它（但「外接 Linux 桌面」需要它）。系統設定，使用者自己改；可陪同實測。
4. **證據壓縮（需使用者同意，證據規則）**：`evidence/` 內 raw-logcat／logcat-follow ~9 GB（zstd 無損可省 ~8 GB）、APK／libXlorie.so 副本 ~4 GB。
5. 可能的後續 PRoot 優化：openat／readlink 等仍兩次 stop 或需路徑翻譯的呼叫；getdents；把 v5/v6 回報上游 termux/proot（對外發文，需同意）。
6. Gate A：我建議為了 CPU 目標先凍結（X 只吃 0.03–0.14 核，GPU 2D 大多比 CPU 慢）；**使用者沒有明確決定**。
7. **DRI3＋AHB 零拷貝（GL/VK 上屏）**：未開始、未排程；使用者 09-25 問過，**未決定**。
   - X 端已有：upstream `loriePixmapFromFds`（`src/upstream/lorie/src/main/cpp/lorie/InitOutput.c:1170`）認 modifier 1255／1256（socket 傳 AHB）、1274／LINEAR（可 mmap 的 fd）；Gate A R2 的 fixture 就是用 1255。
   - Client 端缺：`/opt/mesa-kgsl`（26.0.6＋0017–0019）原始碼與 Termux 原生 `libvulkan_freedreno.so`／`libgallium-26.0.6.so` 都沒有「配 AHB→經 socket 交給 X」的程式碼 → Zink/Turnip 現在走 drisw。
   - 描述性證據（GL-BENCH）：Zink 上屏時 X3 吃 55–74 CPU 秒、畫面外只有 4–5 秒 → 上屏很貴（推測 CPU 複製，**未證實**）。
   - 只對 GL/VK 程式有益；日常 Electron 開 GPU 本身就 NO_BENEFIT（ELECTRON-BENCH-01）。未查證的風險：PRoot 內 glibc 的 Mesa 不能直接呼叫 bionic 的 `AHardwareBuffer_*`。

## 已知問題（都不影響日常）
- tar 解開含硬連結的目錄會報 `Cannot change mode ... No such file or directory`：**原版 proot 也一樣**（link2symlink 既有問題）。
- Node 在加速版只看得到有 IPv4 的介面（`lo`、`wlan0`）；原版另有 3 個只有 IPv6 link-local 的介面。
- Python `ifaddr`（zeroconf）在加速版仍失敗（ctypes 繞過 preload）→ **ADB 探測改用「UDP connect 取本機 IP＋TCP 掃 30000–50000」**。
- `bwrap --unshare-net` 在加速版不能用（日常沒有程式用到；需要時啟動器加 `PROOT_BWRAP_COMPAT=1`）。
- 拖曳中文路徑關窗：DND-PROBE-01 未重現，使用者說現在沒問題，不追。

## 會咬人的事（今天真的踩過）
- **ADB 會斷**：手機換 Wi-Fi（10.191.48.13 ↔ 192.168.1.100）時無線偵錯被自動關掉，需使用者重開；最後一次是 `192.168.1.100:35251`。
  PRoot 內重起 adb server 必須 `ADB_VENDOR_KEYS=/data/data/com.termux/files/home/.android/adbkey`（否則 CERTIFICATE_UNKNOWN）。
- **裝置端長測試要脫離 adb**：`run-as com.termux ... sh -c 'setsid nohup sh script > out 2>&1 < /dev/null &'`，再從主機端輪詢輸出檔；否則 adb 一斷整批被殺。
- runner 需要 MemAvailable ≥ 4500 MB、螢幕亮且未鎖；記憶體不足先用等待器（連續 20 s ≥ 4600）。
- 殘留掃描會「命中」自己的 shell（指令字串含關鍵字）——用前綴比對或看 cmdline 是否為 `bash -c source ... shell-snapshots`。
- PRoot 表中 arm64 的 syscall 79 叫 **PR_fstatat64**（不是 PR_newfstatat）。
- **Termux 的 procps-ng（pgrep／ps 4.0.7）把程序名截成 7 字**（`xfce4-session`→`xfce4-s`），`pgrep -x` 對長名稱永遠比不到；
  「F8 工作站」因此一度沒有關閉選項（09:5x 已改成直接比對 `/proc/*/comm`，舊版備份 `~/.shortcuts-backup-20260925/F8 工作站.v1`）。
- 在 run-as 下 Termux 的 `zstd` 被拒（權限／SELinux），在 PRoot 內執行正常。
- 真實登入設定檔開程式留下的 launch.out 推 PR 前要掃帳號識別資訊（目前只有請求 ID）。

## fork（`waydefu/termux-x11` worktree `src/f8-ahb-exa-async`，**全部本地、未 push**）
`22137ff`、`9f7bad4`（PROOT-BENCH 工具）→ `e4bf7d6`（PF_BIN）→ `9c190e7`（APP-IDLE）→ `0341c54`（DND）→ `a45558c`（f8ifaddrs）→ `98396ad`（proftrace）→ `be7fbc0`（sanity 模式）。
受判工具的原檔快照已放進 PR：`evidence/session/proot/tools-e4bf7d6/`、`tools-be7fbc0/`。proot 本身的修補在 `~/build/proot-fast/proot-5.1.107.92-v*/`，patch 檔在 `evidence/session/proot/`。
