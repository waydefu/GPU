# Stage 7.6 — 桌面客戶端接入紀錄（2026-11-28）

使用者 2026-11-28 指示「接入 claude codex agy hermes」，並說明「都是桌面版」。接在 [試點升級](STAGE7-6-PILOT-UPGRADE-20261128.md) 之後；relay／daemon 程式不變（受治理腳本彙總 `6ebf7354`，`c583002`）。

## 統一啟動方式

四家設定都只寫同一個指令：[`scripts/f8_hybrid2_launch.py`](../../../scripts/f8_hybrid2_launch.py)（部署於 `$HOME/build/proot-fast/tools/hybrid2/f8_hybrid2_launch.py`，納入 `DEPLOYED.sha256`）。它的行為：

- 治理變數固定由包裝程式提供，客戶端設定裡不重複：預算目錄 `~/.f8hyb2-budget`、信任根（同目錄的 `trusted-git-roots.json`），以及 `PYTHONDONTWRITEBYTECODE`。
- 桌面程式啟動 MCP 子程序時常剝除 `am` 需要的 7 個 Android 執行期變數，所以缺少的那幾個會從 Termux app 程序（同 uid）的環境補上。只補缺少的，不覆蓋已有值，也不帶入任何其他變數。
- 最後以 `--auto-start` 執行 relay。

單元測試 `ClientLauncherTests` 驗證：治理變數固定、既有 Android 變數不被覆蓋、不帶入其他變數。實機在 daemon 已停止、`env -i` 完全剝除環境的情況下執行這個指令：經 TermuxService 拉起受治理的原生 daemon（`TracerPid 0`），`git_ro` 原生 `ok`。

## 各客戶端

| 客戶端（桌面版） | 設定檔 | 變更 | 驗證 | 狀態 |
|---|---|---|---|---|
| Claude（Code 分頁） | `~/.claude.json` 使用者範圍 | `hybrid2` 改為包裝程式（取代先前帶 `-e` 的寫法） | `claude mcp get hybrid2`：`✔ Connected` | 生效（新會話） |
| Claude（一般對話） | `~/.config/Claude/claude_desktop_config.json` | 新增 `mcpServers.hybrid2` | JSON 正確；同一指令在剝除環境下可用 | **待下次重開 Claude Desktop**（本會話在 Desktop 內，未重開） |
| Codex（ChatGPT 桌面版） | `~/.codex/config.toml` | 附加 `[mcp_servers.hybrid2]`（`startup_timeout_sec = 30`） | `codex mcp get/list` 啟用；`codex app-server`：`mcpServerStatus/list` 看到 4 個工具，`mcpServer/tool/call git_ro` 0.24 s 成功、daemon 稽核原生 `ok` | 生效（下次 Codex 啟動 MCP 時） |
| Antigravity（AGY 桌面版） | `~/.gemini/config/mcp_config.json`（路徑取自 `/opt/antigravity-hub/resources/bin/language_server` 內字串） | 新增 `mcpServers.hybrid2` | JSON 正確；同一指令在剝除環境下可用 | **待下次開啟 AGY**（目前未執行；language server 單獨啟動需互動式登入） |
| Hermes（桌面版） | `~/.hermes/config.yaml` | `mcp_servers` 下新增 `hybrid2`（`enabled: true`） | `hermes mcp test hybrid2`：`✓ Connected (2150ms)`、4 個工具 | 生效 |

每個檔案修改前都有備份，後綴 `.pre-hybrid2-20261128-130514`。與備份比對：TOML／YAML 只多了 `hybrid2` 那幾行，三個 JSON 只有 `mcpServers.hybrid2` 改變，其他 MCP 伺服器不變。

## 併發注意

4 路模式只有 4 個 relay 租約，由所有客戶端共用：每個 Claude Code 會話、Claude Desktop 一般對話、Codex、AGY、每次 Hermes 對話（含 Hermes 子代理）各佔一個。第 5 個會在該客戶端顯示 `hybrid2` 連線失敗（relay `rc=3 admission refused`），其他工具不受影響；釋放後即可再取得。

## 回退

- 單一客戶端：還原該檔案的 `.pre-hybrid2-20261128-130514` 備份，或刪除 `hybrid2` 項目（Claude Code：`claude mcp remove hybrid2 -s user`；Codex：`codex mcp remove hybrid2`）。
- 全部只走 PRoot：`f8_hybrid2_ctl.py disable`。

紅線：Stable `X1` inode 2300674、Fast9+09c 3/3；驗證結束後換回常駐 daemon（pid 13023，`idle_timeout 0`），無殘留 relay／app-server。
