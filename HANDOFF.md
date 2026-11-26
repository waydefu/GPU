# GPU加速 / 非 Root Android PRoot 工作站總覽 — 2026-11-26

> **入口權威（≤150 行）**。本專案原為 POCO F8 Ultra Termux:X11 GPU 加速研究，現已收斂為 **非 Root Android / PRoot Linux 工作站效能與穩定性工程**。所有歷史交接與逐格流水帳已無損歸檔於 [`docs/archive/handoffs/`](docs/archive/handoffs/)。

## 各戰線現況總表

| 戰線 | 狀態 | 權威成果與位置 |
|---|---|---|
| **PRoot 效能＋自動分流** | **ACTIVE / 現役主力** | `proot-fast8` + `f8-shard` v2 + `shard-daemon.sh` fix 4 已獨立收斂至 [`src/f8-proot-fast/`](src/f8-proot-fast/)（`main` `ee603b8`），F8 與 F6 均部署現役；2026-11-26 實機核對僅單一 `shard-daemon.sh`（PID `17875`，PPid `1`，0 fd 洩漏）。 |
| **Gate A 2D GPU 加速 (EXA/AHB)** | **RESEARCH COMPLETE / PAUSED** | R6–R10 技術驗證完成；`XFCE-NOTEL-01` 證實關掉 `GATEA_TELEMETRY` 後日常 2D GPU 與 CPU 打平（89% pixmap ≤64×64 留 CPU），留作技術資產、不再擴充。 |
| **主線 #3 (GL/VK 上屏)** | **FEASIBILITY COMPLETE / PAUSED** | `GL-PRESENT-03` + `X3-DIRECT-FEAS` 完成：Android EGL/GLES 不收 dma-buf 無法零複製；系統 Vulkan GPU copy 每幀僅省 0.03–0.11 核卻倒貼 ~1.2 ms GPU，不開原型。「EGL 不上屏」列為條件式待辦。 |
| **上游查驗與回饋** | **PR #430 CLOSED / WITHDRAWN** | ① `termux/termux-x11` `loriePresentFlip` 尺寸 bug（`InitOutput.c:947`）上游已修，無需提 PR；② `termux/proot` `stat`/`fstat`/`statx` enter-time（`STAT_SYSCALL` 分層重構）曾送出 [PR #430](https://github.com/termux/proot/pull/430) 後依指示撤回（`CLOSED / WITHDRAWN`），`waydefu/proot` `stat-at-enter`（`edc3319`，對 `0e42875` 實測微基準 **-36.4%～-45.4%**、總牆鐘 **-27.2%**、回歸 0 差異）與匯出 patch 保留於本地待後續再送，紀錄見 [`PROOT-STAT-AT-ENTER-UPSTREAM-PR-DRAFT-20261126.md`](evidence/session/proot/PROOT-STAT-AT-ENTER-UPSTREAM-PR-DRAFT-20261126.md)。 |
| **F6 複製與空間整理** | **CLOSED** | POCO F6 Pro 複製驗收通過並已結案；F8 `evidence/` raw log 經 zstd 無損壓縮釋放 ~9.8G（現 6.9G，`/data` 可用 67G）；14 個凍結 worktree 已清理（`src/` 1.6G → 612M）。 |

## 現役 `proot-fast8` + `auto-shard` 關鍵事實

- **部署與 SHA256**：見 [`src/f8-proot-fast/README.md`](src/f8-proot-fast/README.md)（`f8-shard` `7158e011…`、`shard-daemon.sh` `8becae04…`、`shard-run.sh` `03a24987…`、`proot-fast8` wrapper `f1c211fd…`）。
- **日常回退開關**：單次略過分流設 `F8_NO_SHARD=1`；停用 enter-time stat 設 `PROOT_STAT_AT_ENTER=0`；全桌面切回原版在 Termux 建立 `~/.f8-proot-stock` 後重開桌面。
- **重開 Termux 後的最後一項實機驗收**（使用者手動重開一次 Termux 後執行此單行指令，確認只剩 1 個 `shard-daemon.sh` 且只有它握有 lock/fifo）：
  ```bash
  python3 -c "import glob,os; ds=[p for p in glob.glob('/proc/[0-9]*/cmdline') if 'shard-daemon.sh' in open(p,'rb').read().decode('utf-8','ignore') and open(p,'rb').read().startswith(b'/data/data/com.termux/files/usr/bin/bash')]; hs=[(os.path.basename(os.path.dirname(os.path.dirname(f))),os.readlink(f)) for f in glob.glob('/proc/[0-9]*/fd/*') if os.path.islink(f) and ('f8-shard/daemon.lock' in os.readlink(f) or 'f8-shard/ctl.fifo' in os.readlink(f))]; print('daemons=',len(ds),[os.path.basename(os.path.dirname(d)) for d in ds],'holders=',hs)"
  ```

## 三條不可逾越的紅線

1. **Stable `:1` 永不觸碰**：`com.termux.x11`（`-legacy-drawing`）為日常使用環境，禁止替換或修改；實驗 APK 僅准安裝於 `com.waydefu.x11gpu`（`:3`）。
2. **ADB 通道隔離**：只使用獨立 `-P 5038`（端點依 `f8-adb-port` 重探，見 [`ADB-CONNECT.md`](ADB-CONNECT.md)），不殺不重用 `5037`。
3. **凍結證據與既有判決不可改寫**：`evidence/` 下所有已凍結 capture、verdict 與 SHA256 清單維持原樣；歷史 `±1 UNORM` 仍不作 PASS；無授權不對 `termux/termux-x11` 送 origin PR。

## 重要文件索引

- 專案規則與子代理紀律：[`AGENTS.md`](AGENTS.md)（全域環境紅線見 `/root/.serena/memories/global/f8-workstation.md`）
- Worktree 與遠端地圖：[`WORKTREE-MAP.md`](WORKTREE-MAP.md)
- 歷史測試矩陣：[`TEST-MATRIX.md`](TEST-MATRIX.md)
- 主線 #3 可行性結論：[`evidence/session/gl/X3-DIRECT-FEAS-RESULT.md`](evidence/session/gl/X3-DIRECT-FEAS-RESULT.md)
- `shard-daemon` fix 3/4 紀錄：[`evidence/session/proot/SHARD-DAEMON-FIX3-20260927.md`](evidence/session/proot/SHARD-DAEMON-FIX3-20260927.md)
- 歷史交接歸檔：[`docs/archive/handoffs/`](docs/archive/handoffs/)（含原 104K 台帳 [`HANDOFF-LEDGER-20260919.md`](docs/archive/handoffs/HANDOFF-LEDGER-20260919.md) 與 09-23～09-27 交接）
