# Serena 專案環境（2026-09-08）

這份文件記錄本工作區目前的 Serena 設定與已驗證的限制。`sersna` 依官方專案名稱校正為 **Serena**；它是透過 MCP 連接 coding agent、以 LSP 做符號級程式碼理解的工具。

## 已完成

- 本機 Serena：`1.7.0`，執行檔為 `/root/.local/bin/serena`。
- Codex MCP 已登錄於 `/root/.codex/config.toml`，目前固定啟動這個實驗 worktree：

  ```text
  serena start-mcp-server --context=codex --project /root/projects/GPU加速/src/f8-ahb
  ```

- Serena 專案目標：`/root/projects/GPU加速/src/f8-ahb`。
- 目前 worktree：`f8-p2-b2-over`，HEAD `98224356e409`。
- Serena 專案設定：`/root/.serena/projects/f8-ahb/project.yml`。
  - 語言後端：LSP。
  - 語言伺服器：`cpp`（C/C++ 使用 clangd）。
  - 工作區：`lorie/src/main/cpp`。
  - `read_only: true`，尚未授權改碼前，Serena 不提供編輯工具。
- `/root/projects/GPU加速/src/f8-ahb/compile_commands.json` 已由 Gradle/AGP 的 CMake metadata 產生，不是手寫資料：498 筆、`arm64-v8a`、Android API 24、Termux NDK `29.0.14206865`、Clang `21.1.8`；檔案路徑目前全部存在，且沒有 `/tmp/` 暫存路徑。
- 產生流程已驗證：`./gradlew --no-daemon :lorie:tasks --all` 成功，`./gradlew --no-daemon :lorie:configureCMakeDebug[arm64-v8a]` 成功。AGP 的原始資料位於 `lorie/.cxx/tools/debug/arm64-v8a/compile_commands.json`，根目錄檔案是同一份可供 clangd/Serena 使用的副本。
- `serena project health-check /root/projects/GPU加速/src/f8-ahb` 已通過；實際啟動並使用 clangd `21.1.8`，可取得 C 符號。健康檢查產生的 repo-local `.serena/` 與 `.cache/clangd/` 已清除，權威設定與快取仍在 `/root/.serena/`。
- Hermes 的 Serena MCP 已改為 `--project-from-cwd`，因此在各個已註冊 F8 worktree 以目前目錄選擇專案；Cursor 保留內建索引，沒有接 Serena MCP。
- Stable `:1`、裝置狀態、APK 與 source code 都沒有被這次環境整理觸碰。

## 其他專案與 Codex 的實際邊界

- Serena 全域註冊表目前包含 F8 三個 worktree、`/root/projects/clinic`、`clinic-ui-ux-redesign`、`clinic-web-p0-01`、`clinic-web-p0-02-03`、`wt-wb02-semantics`、`20260906md`、`f8-hermes-spec` 與文件協調根目錄。註冊只代表有專案 metadata，不代表每個專案都在目前對話中啟動或已完成 onboarding/index。
- Hermes 的 `--project-from-cwd` 已實測可在 `/root/projects/clinic` 和三個 F8 Git worktree 選到正確專案；`/root/projects/20260906md` 與 `/root/projects/f8-hermes-spec` 沒有 `.git` 或 repo-local `.serena/project.yml`，所以只連上 MCP、沒有自動啟用專案。對這類 docs-only 目錄要明確呼叫 `activate_project` 或先完成一次 Serena registration。
- Codex 的 `/root/.codex/config.toml` 目前是固定設定：`--project /root/projects/GPU加速/src/f8-ahb`。因此 Codex 已配置 Serena，且會吃到 F8 的 compilation database；它不會因為你把 Codex 切到 clinic 或新 repo 就自動換 Serena project。`codex mcp get serena` 已確認此設定存在。
- 已在八個現有 coding repo 建立被 Git exclude 的 `.codex/config.toml`（F8 三個 worktree、clinic 四個 worktree、`wt-wb02-semantics`），並在 `/root/.codex/config.toml` 將它們列為 trusted；從這些 repo 執行 `codex mcp get serena` 會顯示 `--project-from-cwd`。文件型目錄沒有硬塞這個設定。
- Codex/桌面/IDE 共用 `~/.codex/config.toml`；官方也支援 trusted project 下的 `.codex/config.toml`。若要每個 repo 自動切換，可在該 repo 使用 `--project-from-cwd` 的 project-scoped MCP 設定，然後重啟 Codex。這比把所有 repo 共用一個固定 F8 project 安全。

## 新專案的可重現啟用流程

Serena 不應被當成新資料夾出現就一定會自動完成註冊、onboarding 和 index。新 coding repo 可使用已安裝的 `/root/.local/bin/serena-project-init`，它要求明確的專案名稱與語言：

```bash
serena-project-init --name <唯一專案名> --language <cpp|typescript|...> --trust-codex /絕對/路徑
```

這會註冊 Serena、建立 project-scoped Codex MCP 設定、加入 Git exclude，並選擇性加入 Codex trusted project。接著在 Serena MCP 內對該絕對路徑呼叫 `activate_project`，再做一次 `onboarding`。Hermes 從該 repo 根目錄啟動時會依 cwd 選擇已註冊專案；Codex 的設定內容是：

```toml
[mcp_servers.serena]
command = "/root/.local/bin/serena"
args = ["start-mcp-server", "--context=codex", "--project-from-cwd"]
```

完成後重啟 Codex/MCP，並用 `/mcp` 或 `codex mcp get serena` 檢查。新專案的 Serena memory、language server 和 index 仍要各自建立；不會從 `GPU加速` 複製過去。

## 目前限制

- 目前只為 `f8-ahb` 產生並驗證 C/C++ compilation database；`f8-ahb-debug` 與 `upstream` 已各有獨立 Serena 專案設定，但沒有把不同 worktree 的資料庫混在一起。
- 本機沒有 `jdtls` 或 `kotlin-language-server`，因此這份 Serena 設定只宣稱 C/C++ 語意分析；Gradle wrapper 實際存在，並已完成 tasks/configureCMake 驗證，但沒有宣稱 APK build 或裝置 runtime 驗證。
- `/root/android-sdk` 是 ARM64 本機相容組裝：平台/Build Tools 使用已核對的官方 archive，NDK toolchain/sysroot 使用 Termux `ndk-sysroot`；它不是可在 ARM64 原生執行的標準 x86_64 Android command-line-tools 安裝。CMake `3.22.1` SDK 入口實際指向系統 `cmake 3.28.3`，只為符合 AGP 的套件入口要求。

## 使用順序

1. 重新啟動 Codex App/工作階段，讓新的 MCP 設定載入。
2. 開始工作前先讀 `/root/projects/GPU加速/HANDOFF.md` 與 `TEST-MATRIX.md`；前者是目前 runtime authority。
3. 讓 Serena 先執行 `initial_instructions`，再做符號查詢；不要用 Serena 的讀取結果取代 evidence 文件或實機 gate。
4. 任何 source edit 仍須由使用者明確授權；目前設定會阻擋 Serena 編輯工具。

## 可重現的 compilation database

在 `/root/projects/GPU加速/src/f8-ahb` 執行：

```bash
./gradlew --no-daemon :lorie:configureCMakeDebug[arm64-v8a]
```

成功後，使用 `lorie/.cxx/tools/debug/arm64-v8a/compile_commands.json` 更新根目錄的 `compile_commands.json`。這個檔案已加入該 worktree 的 Git exclude，屬於本機分析產物，不應提交到 source repository。它只影響 clangd/Serena 的分析與索引，不改變 APK 或 runtime 效能；索引期間會使用 CPU、RAM 與磁碟空間。

F8/Termux/Ubuntu PRoot 的本機目錄、套件版本與本輪未重探手機 runtime 的界線，見 [`F8-LOCAL-ENV.md`](F8-LOCAL-ENV.md)。

官方安裝、Codex 連接、專案工作流與 C/C++ compilation database 要求：

- <https://github.com/oraios/serena>
- <https://oraios.github.io/serena/02-usage/030_clients.html>
- <https://oraios.github.io/serena/02-usage/040_workflow.html>
- <https://oraios.github.io/serena/03-special-guides/cpp_setup.html>
