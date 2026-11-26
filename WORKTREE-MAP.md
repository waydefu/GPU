# Worktree / 倉庫地圖 — 2026-11-27

專案根目錄 `.` 本身**不是 Git 倉庫**，而是文件、證據與獨立原始碼工作樹的集合。

## 遠端對照

| 角色 | URL | 備註 |
|---|---|---|
| 工作站工程、文件與證據 | https://github.com/waydefu/GPU | 正式 fast9 原始碼在 `core-src/f8-proot-fast/`，另保留治理文件、judge 與凍結證據 |
| Termux:X11 實驗 fork | https://github.com/waydefu/termux-x11 | CI artifact 建置與歷史研究分支 |
| Termux:X11 上游（只讀） | https://github.com/termux/termux-x11 | **禁止 origin PR / merge / push / force** |
| PRoot fork | https://github.com/waydefu/proot | `stat-at-enter` 移植分支 |
| PRoot 上游 | https://github.com/termux/proot | 上游參照與回饋目標 |

## 保留之工作站原始碼樹（2026-11-27）

| 路徑 | 倉庫 / 分支 | HEAD | 狀態與角色 |
|---|---|---|---|
| 遠端 `core-src/f8-proot-fast/` | [`waydefu/GPU/main`](https://github.com/waydefu/GPU/tree/main/core-src/f8-proot-fast) | `d5ddc73` | 現役 fast9+09c 正式建置來源，來源樹與本機 `23f9bdc` 一致 |
| `src/f8-proot-fast` | 本機獨立倉庫（`main`） | `ab18e49` | fast9+09b 歷史主線與本機基線 |
| `src/f8-proot-fast-fast9-fixes` | 本機同庫工作樹（`fix/fast9-fd-deploy`） | `23f9bdc` | PR #42 匯入的原始快照 |
| `src/f8-proot-fast-stage5` | 同庫隔離 worktree（`stage5/isolated-fast8-20261126`） | `d2ec249` | Stage 5 測試修正與原生隔離基線，詳見 [Stage 5 交接](evidence/session/proot/STAGE5-ISOLATED-20261126.md) |
| `src/termux-proot-upstream` | `termux/proot` + `waydefu/proot`（`stat-at-enter`） | `edc3319` | 上游 [PR #430](https://github.com/termux/proot/pull/430)（`CLOSED / WITHDRAWN`；保留 `stat-at-enter` `STAT_SYSCALL` enter-time 移植與對比實測分支） |
| `src/upstream` | `waydefu/termux-x11`（`f8-control`） | `11b82d9` | 對照基準主庫（凍結不改） |
| `src/f8-ahb` | `waydefu/termux-x11`（`qualification/d0a-narrow-20260912`） | `a6cc795` | Serena `gpu-f8-ahb` 專案綁定路徑（保留不刪） |
| `src/f8-ahb-exa-async` | `waydefu/termux-x11`（`feat/exa-async-proto-20260923`） | `8423f0a` | 最新實驗 APK 來源與 GL/XFCE 測試工具（`dirty=0`） |
| `src/f8-ahb-gatea-r7-p1-arm` | `waydefu/termux-x11`（`feat/gatea-r8-lifecycle-support-20260918`） | `5d9c433` | 最新 Gate A R8/R9/R10 生命週期樹 |
| `src/f8-ahb-d0b-r1` | `waydefu/termux-x11`（`qualification/d0b-r1-narrow-20260912`） | `a6cc795` | 保留（含 6 個未提交修改檔；遠端已有 `backup/snapshot-f8-ahb-d0b-r1-20261111` 備份，為免 `--force` 暫留） |

## 已清理之歷史凍結 Worktree（2026-11-26）

以下 14 個已凍結、超專案 `dirty=0` 且已備份至遠端 `fork` / `fork-backup` 之 worktree 已自 `src/` 移除（`src/` 磁碟由 1.6G 降至 612M），同時保留所有遠端分支供隨時重建：

- `f8-ahb-debug` (`c698164`), `f8-ahb-gatea-a1` (`88e3f17`), `f8-ahb-gatea-xpump` (`d9b7f60`), `f8-ahb-gatea-r5-fix` (`37d8393`)
- `f8-ahb-gatea-r6` (`95e6f96`), `f8-ahb-gatea-r6-retire` (`0f1e546`), `f8-ahb-gatea-r7` (`a7528bd`)
- `f8-ahb-gatea-exa-timeout` (`0d72332`), `f8-ahb-gatea-stall-diag` (`27d8d1b`), `f8-ahb-gatea-notify-diag` (`1f85b80`), `f8-ahb-gatea-notify-fn` (`feeaa56`)
- `f8-ahb-gatea-case-loop` (`fdfb1ce`), `f8-ahb-gatea-r7-hup-preserve` (`a07d66c`), `f8-ahb-gatea-r7-10-hup` (`8545b26`)

任一歷史樹若需查閱原始碼，可自 `src/upstream` 重建（例）：
```bash
git -C ./src/upstream worktree add ./src/f8-ahb-gatea-r6-retire 0f1e546
```

## Serena

既有專案名：`gpu-f8-ahb`（綁定 `./src/f8-ahb`）。不要為交接新建專案，不要殺別人的 clangd/Serena。
