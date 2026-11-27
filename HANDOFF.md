# GPU加速 / 非 Root Android PRoot 工作站總覽 — 2026-11-27

> **入口權威（≤150 行）**。本專案原為 POCO F8 Ultra Termux:X11 GPU 加速研究，現已收斂為 **非 Root Android / PRoot Linux 工作站效能與穩定性工程**。本檔與 GitHub `waydefu/GPU` `main` 的 `HANDOFF.md` 內容一致（2026-11-27 起以 PR 同步，改一邊就要同步另一邊）。歷史交接見文末「重要文件索引」。

## 各戰線現況總表

| 戰線 | 狀態 | 權威成果與位置 |
|---|---|---|
| **PRoot 效能＋自動分流** | **LIVE (`fast9+09c`)** | 正式來源為 [waydefu/GPU PR #42](https://github.com/waydefu/GPU/pull/42) 合併提交 `d5ddc73`。現役 SHA256 `4a6bc677…`，Stable `:1` 已換新版 tracer，30 分鐘壓測 514/514 批、Vulkan 7/7。見 [實機驗收](evidence/session/proot/FAST9-09C-LIVE-QUALIFICATION-20261127.md)。 |
| **Gate A 2D GPU 加速 (EXA/AHB)** | **RESEARCH COMPLETE / PAUSED** | R6–R10 技術驗證完成；`XFCE-NOTEL-01` 證實關掉 `GATEA_TELEMETRY` 後日常 2D GPU 與 CPU 打平（89% pixmap ≤64×64 留 CPU），留作技術資產、不再擴充。 |
| **主線 #3 (GL/VK 上屏)** | **FEASIBILITY COMPLETE / PAUSED** | `GL-PRESENT-03` + `X3-DIRECT-FEAS` 完成：Android EGL/GLES 不收 dma-buf 無法零複製；系統 Vulkan GPU copy 每幀僅省 0.03–0.11 核卻倒貼 ~1.2 ms GPU，不開原型。「EGL 不上屏」列為條件式待辦。 |
| **上游查驗與回饋** | **PR #430 CLOSED / WITHDRAWN** | ① `termux/termux-x11` `loriePresentFlip` 尺寸 bug（`InitOutput.c:947`）上游已修，無需提 PR；② `termux/proot` `stat`/`fstat`/`statx` enter-time（`STAT_SYSCALL` 分層重構）曾送出 [PR #430](https://github.com/termux/proot/pull/430) 後依指示撤回（`CLOSED / WITHDRAWN`），`waydefu/proot` `stat-at-enter`（`edc3319`，對 `0e42875` 實測微基準 **-36.4%～-45.4%**、總牆鐘 **-27.2%**、回歸 0 差異）與匯出 patch 保留於本地待後續再送，紀錄見 [`PROOT-STAT-AT-ENTER-UPSTREAM-PR-DRAFT-20261126.md`](evidence/session/proot/PROOT-STAT-AT-ENTER-UPSTREAM-PR-DRAFT-20261126.md)。 |
| **F6 複製與空間整理** | **CLOSED** | POCO F6 Pro 複製驗收通過並已結案；F8 `evidence/` raw log 經 zstd 無損壓縮釋放 ~9.8G（現 6.9G，`/data` 可用 67G）；14 個凍結 worktree 已清理（`src/` 1.6G → 612M）。 |

## 現役 `fast9+09c` 關鍵事實

- **正式部署**：沿用 `out8/bin/proot-fast8` 路徑，版本 `5.1.107.92-fast9`，補丁 `01..09 + 09b + 09c`，SHA256 `4a6bc67723d9517771ea602e61caa98a4ac7cb7cf75f932d85fa1a5038ae7660`。正式 dry-run、`DEPLOY_PASS`、部署雜湊 3/3 通過。
- **隔離驗證與桌面**：socket FD、部署失敗復原、fast8 回退指標和 Claude 啟動判定均驗證。Stable `:1` 保持原 X11 伺服器與 socket，XFCE tracer 已載入新版。壓測 1,805.76 秒、514/514 批，daemon 單一實例、7 FD。
- **回退**：上一版 fast9+09b 備份 `/data/data/com.termux/files/home/build/proot-fast/backups/out8-previous-20261127-004529.KNBzD8mu`，雜湊 5/5。已驗證 fast8 備份與指標仍可用，相關方法詳見 [前版部署紀錄](evidence/session/proot/STAGE5-FAST9-LIVE-DEPLOYMENT-AND-SOAK30M-20261126.md)。
- **同機效能對照**：各版 10 批，09b → 09c 批次中位數 2,490.57 → 2,495.91 ms（+0.21%），tracer CPU 中位數 860 ms、rAF p95 中位數 16.7 ms 均持平。
- **效能基準凍結（2026-11-27）**：fast9+09c 為新的穩定效能基準，凍結副本 `/data/data/com.termux/files/home/build/proot-fast/baselines/fast9-09c-20261127/`（`out8/` 5 檔，`sha256sums.txt` 與現役 5/5 一致；權限無法設唯讀，只靠雜湊比對）。數值與比較規則見 [基準凍結](evidence/session/proot/FAST9-09C-BASELINE-FREEZE-20261127.md)。
- **`termux-bg-run` 無回報（根因已證實並驗收）**：11-27 00:48 `restart-desktop.py` 以手寫 5 個變數重啟 Stable 桌面，遺失 `ANDROID_ART_ROOT`／`BOOTCLASSPATH` 等 7 個變數，桌面內 Termux `am` 靜默 exit 0、intent 不送出；TermuxService 本身正常，與 09b／09c 無關。修正已合併 [waydefu/GPU PR #43](https://github.com/waydefu/GPU/pull/43)（`9530c13`）：`termux-bg-run` 缺變數即 exit 4。後續已完成 [事後驗收](evidence/session/proot/STABLE-RESTART-E2E-20261127.md)（調查見 [調查報告](evidence/session/proot/TERMUX-BG-RUN-REPORT-INVESTIGATION-20261127.md)），並於 11-27 10:06 由原生 Termux 實跑 `restart-stable-desktop.py --apply` 通過：`xserver=28218`／`x1_inode=812663` 不變、`new_xfce=20772`／`20766`、`survivors_gone=none`、`android_env_missing=none`，新桌面不借變數 `termux-bg-run` `rc=0`，見 [實戰驗收](evidence/session/proot/STABLE-RESTART-APPLY-20261127.md)。
- **操作降級**：單次略過分流可設 `F8_NO_SHARD=1`，停用 enter-time stat 可設 `PROOT_STAT_AT_ENTER=0`。切換原版的操作紀錄見前版部署報告。
- **Stage 6（Android 宿主最佳化）CLOSED / COMPLETE**：6.1–6.4 全案結案（無 Root、零 Android 系統寫入）：
  - **6.1 基線**（[快照](evidence/session/proot/stage6-audit-20261127/README.md)）：`PSI` 與 `zram0/mm_stat` 不可讀（`null`）；`vmstat` 唯經 `adb shell` 為真。
  - **6.2 電源模式（候選 3 → `PAUSE`）**：第一輪 `B1 P1 P2 B2` ＋ `S1`（5 塊皆 `BLOCK_VALID`、`370/370` 批、`S1` `+8.78%` 過 V8）。均衡極穩（`0.026%` 離散）；效能前 30s 快 `+6.39%`／`+6.45%`，但 90–180s 兩次皆破 `85.0 °C`（`87.2`／`85.7 °C`）且 `P2` 遭 `cpu6` 砍半至 `2.23 GHz` 歸零（`-0.00%`），日常維持 `balanced`。見 [6.2 報告](evidence/session/proot/STAGE6-2-POWER-MODE-RESULT-20261127.md)（凍結門檻 [FREEZE](evidence/session/proot/STAGE6-2-POWER-MODE-FREEZE-20261127.md) 未改動）。
  - **6.3–6.4（候選 1 `GO` 操作紀律、候選 2 `PAUSE`、候選 4 `PAUSE`）**：Antigravity 佔 UID PSS `76.9%`（`547.6`/`711.9 MB`）；`--max-old-space-size=512` 無淨收益且 `650 MB` OOM 閃退（退回）；`4→2` 降併發以 `+43.4%` 耗時換 `-39.5%` 峰值 PSS（作操作紀律、不硬編碼）；全程 `com.termux` 零誤殺不改 Phantom 設定；§5.2 驗收 4 項通過、6.1 因非 Root 權限無法讀 `PSI`/`zram0/mm_stat` 標記為 `UNAVAILABLE_DUE_TO_PERMISSION`（不視為完整量測通過）。見 [6.3/6.4 結案報告](evidence/session/proot/STAGE6-3-4-CLOSURE-20261127.md)（`5.55×` 誤植已獨立勘誤為 `1.89×`，見 [勘誤](evidence/session/proot/ERRATUM-STAGE6-HYBRID-SPEEDUP-20261127.md)）。
- **Stage 7.1–7.4（Native Hybrid 2.0 原型、基準與隔離試點）`7.2/7.3 MERGED` / `7.4 ISOLATED_PASS`**：已合併 [PR #50](https://github.com/waydefu/GPU/pull/50)（`91d2b52`）、[PR #51](https://github.com/waydefu/GPU/pull/51)（`d1d5dcc`）與 [PR #52](https://github.com/waydefu/GPU/pull/52)（`40edf91`，`n=10` ABBA 驗證 `tree_scan` `5.74×`／`git_ro` `1.16×–3.81×`／`text_search` `2.52×`／混合輪 `2.74×`，`python_json_summary` `0.67×` 與 4 路單 GIL `0.61×`）。Stage 7.4 已落地**選擇性分流、JSON-RPC 2.0 嚴格驗證、有界 `--max-local-inflight` 與 Daemon 非阻塞 `POLLOUT` 背壓**（`f8_hybrid2_relay.py`／`daemon.py`／`ctl.py`；初版雙軌 **13/13 PASS** 為歷史測試），並以隔離試點完成 Hermes／Claude Code／Codex `app-server` **`PARTIAL_PASS`**（MCP 工具／生命週期通過、無金鑰 LLM 對話分別 `UNKNOWN`/`BLOCKED_NO_AUTH`；Desktop/AGY `UNVERIFIED_LIVE_GUI`），對照 `rg`/`git`/`Serena`/`RTK` 劃定邊界、未動現役設定。另有尚未推送的安全複審候選版，修補 inflight 清理、慢速輸出與 Git metadata 邊界，PRoot／Termux Native 各 **15/15 PASS**，待 Neon 與遠端 CI。見 [7.3 基準](evidence/session/proot/STAGE7-3-ABBA-BENCHMARK-20261127.md) 與 [7.4 試點驗收](evidence/session/proot/STAGE7-4-ISOLATED-PILOT-20261127.md)。

## 三條不可逾越的紅線

1. **Stable `:1` 永不觸碰**：`com.termux.x11`（`-legacy-drawing`）為日常使用環境，禁止替換或修改；實驗 APK 僅准安裝於 `com.waydefu.x11gpu`（`:3`）。
2. **ADB 通道隔離**：只使用獨立 `-P 5038`（端點依 `f8-adb-port` 重探，見 [`ADB-CONNECT.md`](ADB-CONNECT.md)），不殺不重用 `5037`。
3. **凍結證據與既有判決不可改寫**：`evidence/` 下所有已凍結 capture、verdict 與 SHA256 清單維持原樣；歷史 `±1 UNORM` 仍不作 PASS；無授權不對 `termux/termux-x11` 送 origin PR。

## 重要文件索引

- 專案規則與子代理紀律：[`AGENTS.md`](AGENTS.md)（全域環境紅線見 `/root/.serena/memories/global/f8-workstation.md`）
- Worktree 與遠端地圖：[`WORKTREE-MAP.md`](WORKTREE-MAP.md)
- Stage 5 Phase 3 最終收斂與隔離驗收：[`STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md`](evidence/session/proot/STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md)
- **fast9+09c 本機部署與驗收**：[FAST9-09C-LIVE-QUALIFICATION-20261127.md](evidence/session/proot/FAST9-09C-LIVE-QUALIFICATION-20261127.md)
- **Stage 5 `proot-fast9` 部署、回退與 `fast9+09b` 現役重部署驗收**：[`STAGE5-FAST9-LIVE-DEPLOYMENT-AND-SOAK30M-20261126.md`](evidence/session/proot/STAGE5-FAST9-LIVE-DEPLOYMENT-AND-SOAK30M-20261126.md)
- **Stage 6 Android 宿主效能與電源最佳化計畫**：[`STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md`](evidence/session/proot/STAGE6-ANDROID-HOST-OPTIMIZATION-PLAN-20261126.md)
- **Stage 6.2–6.4 電源與宿主最佳化結案**：凍結門檻 [`STAGE6-2-POWER-MODE-FREEZE-20261127.md`](evidence/session/proot/STAGE6-2-POWER-MODE-FREEZE-20261127.md)；6.2 實測 [`STAGE6-2-POWER-MODE-RESULT-20261127.md`](evidence/session/proot/STAGE6-2-POWER-MODE-RESULT-20261127.md)（[原始資料](evidence/session/proot/stage6-2-runs-20261127/README.md)）；6.3/6.4 結案 [`STAGE6-3-4-CLOSURE-20261127.md`](evidence/session/proot/STAGE6-3-4-CLOSURE-20261127.md)（[原始資料](evidence/session/proot/stage6-3-candidate2-20261127/README.md)）；6.1 基線 [`stage6-audit-20261127/`](evidence/session/proot/stage6-audit-20261127/README.md)；勘誤 [`ERRATUM-STAGE6-HYBRID-SPEEDUP-20261127.md`](evidence/session/proot/ERRATUM-STAGE6-HYBRID-SPEEDUP-20261127.md)
- **Stage 7 Native Hybrid 2.0**：[初版計畫書](evidence/session/proot/STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md)；[多客戶端修訂計畫](evidence/session/proot/STAGE7-2-MULTI-CLIENT-REVISION-20261127.md)；[7.2 隔離原型驗收](evidence/session/proot/STAGE7-2-PROTOTYPE-ACCEPTANCE-20261127.md)；[7.3 ABBA 基準報告](evidence/session/proot/STAGE7-3-ABBA-BENCHMARK-20261127.md)（[原始資料](evidence/session/proot/stage7-3-runs-20261127/README.md)）；[7.4 隔離試點報告](evidence/session/proot/STAGE7-4-ISOLATED-PILOT-20261127.md)
- Stage 5 隔離驗證與 Phase 2 紀錄：[`STAGE5-ISOLATED-20261126.md`](evidence/session/proot/STAGE5-ISOLATED-20261126.md)、[`STAGE5-PHASE2-ACCEPTANCE-20261126.md`](evidence/session/proot/STAGE5-PHASE2-ACCEPTANCE-20261126.md)
- 歷史測試矩陣：[`TEST-MATRIX.md`](TEST-MATRIX.md)
- Stable 桌面驗收（2026-11-27）：事後查驗 [`STABLE-RESTART-E2E-20261127.md`](evidence/session/proot/STABLE-RESTART-E2E-20261127.md)；`--apply` 實戰 [`STABLE-RESTART-APPLY-20261127.md`](evidence/session/proot/STABLE-RESTART-APPLY-20261127.md)
- GPU 管線剩餘槓桿唯讀盤點（2026-11-27）：[`GPU-PIPELINE-LEVER-INVENTORY-20261127.md`](docs/GPU-PIPELINE-LEVER-INVENTORY-20261127.md)
- 主線 #3 可行性結論：[`evidence/session/gl/X3-DIRECT-FEAS-RESULT.md`](evidence/session/gl/X3-DIRECT-FEAS-RESULT.md)
- `shard-daemon` fix 3/4 紀錄：手機本機 `evidence/session/proot/SHARD-DAEMON-FIX3-20260927.md`（含私有 ADB 端點，治理掃描會擋，不推送 GitHub）
- 歷史交接歸檔：手機本機 `docs/archive/handoffs/`（含原 104K 台帳 `HANDOFF-LEDGER-20260919.md` 與 09-23～09-27 交接）。該路徑是治理凍結路徑，CI 拒絕新增檔案，因此不推送；GitHub 上同期交接仍在根目錄 `HANDOFF-NEXT-SESSION-*.md` 與 `STATUS-HANDOFF-*.md`，台帳僅存本機。
