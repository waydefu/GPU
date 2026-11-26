# GPU 加速專案（Gate A / V1-Core）— 每次接手先知道的事

> 2026-11-17 自 `~/.claude/CLAUDE.md` 搬來（只在這個專案載入；原本每個會話都載入）。
> 現行狀態、redlines、指令一律以 `AGENTS.md` 與入口 `HANDOFF.md` 為準。
> 本檔只記**不會隨進度改變**的結構，避免每次重新摸索。

## 相關倉庫與本地樹，分工不同，不要搞混

| repo | 內容 | 本機位置 |
|---|---|---|
| `waydefu/GPU` | docs / planning / evidence / handoff / CI。**文件與證據權威** | 專案資料在 `/root/projects/GPU加速`，Git 操作在獨立 clone 或 linked worktree |
| `waydefu/termux-x11` | Termux:X11 實驗 source + `tests/`（judge / verifier） | `/root/projects/GPU加速/src/f8-ahb-exa-async`（及 `upstream` 等 5 個 worktree） |
| `waydefu/proot` | PRoot 上游 fork（`stat-at-enter` 分支） | `/root/projects/GPU加速/src/termux-proot-upstream` |
| `f8-proot-fast`（僅本地） | 現役 `proot-fast8` + `auto-shard` | `/root/projects/GPU加速/src/f8-proot-fast`（`main`，暫無 GitHub 遠端） |

- `waydefu/GPU` 設有 `.github/workflows/governance-check.yml`（文件／衛生／凍結保護）；docs PR 綠燈仍 ≠ 裝置 qualification。
- 要推 evidence 時：clone 到 scratchpad → 複製檔案 → branch → PR。
- **evidence 只推判決依據那一份**：不含 `raw-logcat.txt`、`collect-input.txt`、
  `x3.maps`；`sha256sums.txt` 仍是完整本地清單，另附 `PUBLISHED-SUBSET.md` 說明。

## 證據紀律（這個專案的核心，違反就等於作廢）

```
frozen attempt      永久保留，不重判、不重跑、不改寫。工具改了也不回頭改判決。
null ≠ 0            量不到寫 null。把「沒量到」寫成 0 會把 leak 稀釋成沒有 leak。
INVALID ≠ FAIL      payload 沒走到那條路 = INVALID（無資訊），不是失敗。
expected fatal      某些 cell 的 PASS 條件就是「那個 halt 有出現」，不是「沒壞」。
先定 threshold      tolerance 必須在看到受判資料前凍結；事後調 = 整批作廢。
工具出錯要留痕      修正要寫進 commit / 報告，錯誤版本不抹除。
不會失敗的對照組    不是對照組——驗證工具時一定要有一個「應該要紅」的案例。
```

## 裝置操作

- 實驗只碰 `com.waydefu.x11gpu` / `DISPLAY :3`。
  **Stable `com.termux.x11` / `:1` 絕對不碰**（使用中的日常機器）。
- ADB endpoint **每次都會變**，一律用 `$PREFIX/bin/f8-adb-port` 重探，不要沿用舊值；lane 只用 5038。
  從 Termux 那側執行（PRoot 內沒有 Termux 的 adb 金鑰），測完 `adb -P 5038 kill-server`。
  探測機制、mDNS 失效、`-P` vs `-L` 等細節見 `mem:global/f8-workstation`（ADB endpoint / ADB lane 兩段）。
- 不用 broad `pkill` / `killall`。若測試需要 kill，那是 **construction**，
  要在證據裡記下目標 pid 與 cmdline，不可當成 cleanup 一筆帶過。
