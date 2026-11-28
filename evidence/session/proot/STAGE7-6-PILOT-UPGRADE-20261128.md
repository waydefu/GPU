# Stage 7.6 — 4 路日用試點升級紀錄（2026-11-28）

使用者 2026-11-28 指示「替換試點」，在 [Stage 7.6 驗收](STAGE7-6-L2S-AUTOSTART-20261128.md)通過（F13 GO、2／4／6 路 GO）之後執行。PR #55 仍未合併。

## 變更

| 項目 | 之前（7.5 試點） | 之後 |
|---|---|---|
| 受治理腳本 | 彙總 `11513936`（`125eef8`） | 彙總 `6ebf7354`（`c583002`），`tools/hybrid2/DEPLOYED.{sha256,candidate}` |
| 原生分流 | `repo_tree_scan`、`repo_text_search` | 預設三項：再加 `git_ro`（F13）；`python_json_summary` 仍在 PRoot |
| PRoot 路由 | 含 F14／F15 越界 | 已修補（`readlink`＋目錄項類型，`hidden-link` 拒絕） |
| relay 參數 | `--native-tools repo_tree_scan,repo_text_search` | `--auto-start`（daemon 不在時經 TermuxService 拉起，帶預算目錄） |
| 日誌 | route log／`daemon.out` 無上限 | `append_rotating`（5 MiB／1 MiB，一代 `.1`） |
| 預算目錄、信任根、socket | 不變（`~/.f8hyb2-budget` mode 4、20 個本機 repo、`~/.f8hyb2/m.sock`） | 不變 |

備份：`tools/hybrid2.pre-s76-20261128-125611`（7.5 版，雜湊驗證通過）、`~/.claude.json.pre-s76-20261128-125611`。`~/.claude.json` 只有 `mcpServers.hybrid2` 改變，其他 MCP 伺服器不變。

## 部署驗證（實機）

| 檢查 | 結果 |
|---|---|
| 舊 daemon | `ctl stop`（pid 15369，pidfile＋cmdline 驗證），替換時無任何 relay 連線 |
| 新 daemon | 啟動腳本起，pid 31657：`TracerPid 0`、1 thread、7 FD、PSS 26.3 MiB、`governed=true`、`max_clients=4`、`max_inflight=2`、`idle_timeout 0` |
| `claude mcp get hybrid2` | `✔ Connected` |
| 對照（與 Claude Code 相同的 relay 指令） | f8-proot-fast、upstream、termux-proot-upstream 三個 PRoot 真 repo 的 tree／search／`git_ro log --stat`／`git_ro show --stat` 加 JSON 摘要：原生與 `F8_NO_HYBRID=1` **13/13 一致**，無拒絕 |
| 路由 | daemon 稽核：`repo_tree_scan` 3、`repo_text_search` 3、`git_ro` 6，全部 `ok` |
| 租約上限 | 4 個 relay 佔滿時第 5 個 `rc=3 admission refused: budget exhausted` |
| 自動恢復 | `ctl stop` 後以同一 relay 指令呼叫：1.3 s 內經 TermuxService 拉起新 daemon（`TracerPid 0`、環境含預算目錄、`governed=true`），結果與停止前相同。之後換回常駐 daemon |
| 紅線 | Stable `X1` inode 2300674、Fast9+09c `deployed.sha256` 3/3、無殘留實驗程序 |

單次延遲（非基準，毫秒）：f8-proot-fast `git_ro show --stat` 原生 48 vs PRoot 251；upstream `show --stat` 321 vs 1,553；upstream 第一次 `log -n 10 --stat` 1,587 vs 1,604（原生的物件檢查約 450 ms 佔大宗）。

## 已知限制

沿用 [7.6 報告](STAGE7-6-L2S-AUTOSTART-20261128.md)的殘餘限制：檢查到使用之間的時間窗；PRoot 路由的物件檔無法驗證來源；`.bitmap`／`.mtimes`／`clone --local` 形狀安全失敗；daemon 中途消失時 relay 照 7.4 設計退出，下次啟動才恢復；同時最多 4 個 Claude Code 會話拿到 `hybrid2`。自動拉起的 daemon 閒置 300 秒退出，之後由下一個 relay 再拉起（約 1.3 s）。

## 回退

1. 回到 7.5 試點：停 daemon（`f8_hybrid2_ctl.py --dir ~/.f8hyb2 stop`），把 `tools/hybrid2.pre-s76-20261128-125611` 換回 `tools/hybrid2`，`~/.claude.json` 還原備份（或 `claude mcp remove hybrid2 -s user` 後依 [7.5 試點紀錄](STAGE7-5-PILOT-DEPLOY-20261128.md)重新註冊），重跑 `f8-hybrid2-pilot.sh`。注意：7.5 版含 F14／F15。
2. 只停原生：`f8_hybrid2_ctl.py disable`（relay 全走 PRoot，7.6 的 PRoot 修補仍有效）。
3. 完全移除：`claude mcp remove hybrid2 -s user`，再 `ctl stop`。
