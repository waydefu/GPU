# Stage 7.5 — 4 路日用試點部署紀錄（2026-11-28）

使用者 2026-11-28 指示「部署 4 路試點」。本紀錄是**試點部署**，不是新的驗收判決；判決依據仍是 [7.5 分級驗收](STAGE7-5-TIERED-GOVERNANCE-20261128.md)。PR #55 未合併。

## 部署內容

| 項目 | 值 |
|---|---|
| 受治理腳本 | `f8_hybrid2_{budget,ctl,daemon,policy,relay,tools}.py`，取自分支 HEAD `2050b19`；雜湊彙總 `11513936…`，與驗收候選 `125eef8` 相同 |
| 安裝位置 | `$HOME/build/proot-fast/tools/hybrid2/`（`DEPLOYED.sha256`、`DEPLOYED.candidate`）；舊 7.3/7.4 暫存副本備份為同層 `hybrid2.pre-s75-20261128-103127` |
| 預算目錄 | `$HOME/.f8hyb2-budget`，`init --mode 4` → `{"mode": 4, "exec_slots": 2, "session_queue": 4}` |
| 原生 daemon | [`scripts/stage75_pilot.sh`](../../../scripts/stage75_pilot.sh) 經 `termux-bg-run` 啟動：驗雜湊、拒絕被追蹤、`--max-clients 4 --idle-timeout 0`，socket `$HOME/.f8hyb2/m.sock` |
| 客戶端 | 僅 Claude Code 使用者範圍 `hybrid2`（`claude mcp add -s user`），帶 `F8_HYBRID2_BUDGET_DIR` 與 20 個本機 repo 的 `F8_HYBRID2_TRUSTED_GIT_ROOTS`；`~/.claude.json` 只新增 `mcpServers.hybrid2`（已備份）。Hermes／Codex／Desktop 設定未動 |
| 原生分流 | `--native-tools repo_tree_scan,repo_text_search`；`git_ro` 與 `python_json_summary` 在 PRoot relay 本地執行（見下） |

## 部署時發現：原生 `git_ro` 拒絕 PRoot 寫過的 repo（F13）

PRoot 以 link2symlink 模擬硬連結：git 在 PRoot 內寫入的 loose object 在宿主側是指向 `rootfs/.l2s/.l2s.*` 的符號連結。原生 daemon 的 Git 信任檢查把它解析到允許根目錄外，正確地回 `-32602 Policy refused: symlink-escape`。實測本機 8 個獨立 `.git` 物件庫全部含此類連結（30–1,439 個）。7.5 矩陣的 fixture repo 由原生 git 建立、沒有這類連結，所以沒抓到。PRoot 本地路徑結果正確。

試點處置：`git_ro` 不分流（設定層，程式不變）。放寬信任邊界以接受 `.l2s` 目標屬程式變更，需另行審核與驗收。

## 部署驗證（同一 daemon，實機）

| 檢查 | 結果 |
|---|---|
| daemon | `TracerPid 0`、1 thread、7 FD、PSS 27.0 MiB（啟動時）／8.2 MiB（閒置後） |
| 4 工具 native 與 `F8_NO_HYBRID=1` 對照（`src/f8-proot-fast`） | 4/4 輸出一致（去除計時欄位）；daemon 稽核只見 `repo_tree_scan`、`repo_text_search` 各 1 次 `ok` |
| 延遲（單次，非基準） | tree 22.6 ms vs 50.2；text 10.3 vs 50.4；`git_ro` 與 JSON 兩邊都在 PRoot |
| 租約上限 | 4 個 relay 佔滿後第 5 個 `rc=3 admission refused: budget exhausted`；釋放 1 個後新 relay 可取得 |
| `claude mcp get hybrid2` | `✔ Connected`（1.1 s） |
| 紅線 | Stable `X1` inode 2300674 前後一致；Fast9+09c `out8/deployed.sha256` 3/3；無殘留 relay |

## 試點限制

- 同時最多 4 個 Claude Code 會話能拿到 `hybrid2`；第 5 個在該會話顯示 MCP 連線失敗，其他工具不受影響。
- daemon 不隨 Termux／手機重啟自動啟動；不在時 relay 自動走 PRoot（較慢、結果相同），重跑 `stage75_pilot.sh` 即恢復。
- `audit.jsonl` 不輪替，試點期間需留意大小。
  - **勘誤（2026-11-28，Stage 7.6 稽核）**：上句錯誤。daemon 的 `audit.jsonl` 原本就在 5 MiB 時輪替為 `.1`（`AUDIT_ROTATE_BYTES`）；真正沒有輪替的是 relay 的 `--route-log` 與直接啟動時的 `daemon.out`，已在 7.6 修補（試點版本尚未替換）。

## 回退

1. 只停原生：`python3 $HOME/build/proot-fast/tools/hybrid2/f8_hybrid2_ctl.py disable`（建 `disabled.flag` 並停 daemon，relay 走 PRoot）；恢復用 `enable` 後重跑啟動腳本。
2. 完全移除：`claude mcp remove hybrid2 -s user`（或還原 `~/.claude.json.pre-hybrid2-20261128-103422`），再 `ctl stop`。
