# 專案治理與安全十項稽核處置紀錄（2026-11-26）

> **目的**：針對本專案（`.` 與 [`waydefu/GPU`](https://github.com/waydefu/GPU)）之 10 項治理與工程衛生告警，逐項查證實際根因，並在不違背「凍結證據不改寫、Stable `:1` 不觸碰」紅線下完成修補與 CI 防線。

| 嚴重度 | 稽核項目 | 本次實查根因 | 處置方式與狀態 |
|---|---|---|---|
| **高** | **歷史測試證據遭修改** | 若直接修改 `evidence/session/gate-a-a1/` 等凍結目錄下的 capture / judge / script 檔案，會破壞既有資格結論與 sha256 清單。 | **保留唯讀＋CI 鎖護**：本次未修改任何凍結目錄；在 `waydefu/GPU` 新增 `.github/workflows/governance-check.yml`，PR/push 一旦異動 `evidence/session/gate-a-a1/` 內凍結判決／`sha256`／腳本即直接擋下。 |
| **高** | **測試腳本寫死 ADB 端點** | 本機排除 `src/` 後，有 3 支凍結的 `evidence/session/gate-a-a1/p2-r3-drain-runtime/run-*.sh` 與現役旁側腳本 [`patches/run_tiny_pixmap.py`](../../../patches/run_tiny_pixmap.py) 含有硬編碼 `IP:PORT`（`192.168.1.101:35749`）。 | **已修現役、凍結保留**：改寫 `patches/run_tiny_pixmap.py` 為讀取 `ADB_SERIAL`/`ANDROID_SERIAL` 或即時呼叫 `f8-adb-port`；凍結的 `gate-a-a1/` 腳本不溯及修改；CI 禁止未來新增/異動腳本寫死 ADB `IP:PORT`。 |
| **高** | **工程權威狀態不一致** | `AGENTS.md` 仍殘留超長單行舊 R7/R8 歷史流水帳與 `gpt-5.6-luna-900k` 舊模型名；`.claude/rules/gpu-structure.md` 仍指向舊 `STATUS-HANDOFF-*.md`；且 `waydefu/GPU#40`（2026-11-10 PR）過期並與今日重整衝突。 | **已全面對齊**：精簡 [`AGENTS.md`](../../../AGENTS.md) Redlines 指向歸檔台帳並更新為 `gpt-6-luna-900k`；更新 [`.claude/rules/gpu-structure.md`](../../../.claude/rules/gpu-structure.md) 指向 [`HANDOFF.md`](../../../HANDOFF.md)；關閉過期 PR `#40` 並同步最新權威檔至 `waydefu/GPU` `main`。 |
| **高** | **壓縮工具存在證據遺失風險** | `evidence/COMPRESSED-LOGS-20260927.zlogs.sh` 使用 `set -u`（缺 `-eo pipefail`）、未檢查 `$h`/`$h2` 是否為合法 64 碼 SHA256（若管線異常導致兩者皆空字串會誤判 `[ "" = "" ]` 而 `rm` 原檔）、先寫入最終 `.zst` 再驗證、且含 `TEST_CORRUPT` 測試鉤子。 | **已新建安全版**：建立 [`scripts/zlogs-safe.sh`](../../../scripts/zlogs-safe.sh)（`set -euo pipefail`、雙端 `^[0-9a-f]{64}$` 校驗、`.tmp.$$` 原子寫入與更名、`--dry-run`、移除生產端破壞性測試鉤子），已通過失敗保原檔與正常壓縮 3 項 `/tmp` 測試。原歷史檔保留不改以維持歷史追溯。 |
| **中** | **腳本依賴本機絕對路徑** | 歷史累積共有 308 支（含歷史 `evidence/` 與 PRoot 快照）`.sh`/`.py` 含 `/root/projects/` 或 `/data/data/com.termux`。 | **漸進治理**：現役 [`patches/run_tiny_pixmap.py`](../../../patches/run_tiny_pixmap.py) 已改為 `Path(__file__).resolve().parent.parent` 相對定位；歷史 `evidence/` 腳本保留不改，新增 CI 警示新腳本勿硬編 `/root/projects/` 絕對路徑。 |
| **中** | **公開內網位址** | 歷史紀錄與證據（401 檔含歷史日誌、歸檔手冊、`AGENTS.md` 舊段落等）帶有 `10.191.*` / `192.168.*`。 | **新增寫入防護**：已自現役 [`AGENTS.md`](../../../AGENTS.md) 與 [`patches/run_tiny_pixmap.py`](../../../patches/run_tiny_pixmap.py) 移除舊內網 IP:Port，並由 CI 檢查現役設定與新增/異動腳本不再引入內網 IP:Port；已發布之歷史歸檔不重寫歷史。 |
| **中** | **Agent 自動授權範圍過廣** | 檢查工作區無 `.claude/settings*.json`，僅存說明規則 `.claude/rules/gpu-structure.md`；全域 `~/.claude/settings.json` 屬使用者個人工具設定，非本專案檔。 | **已確認與界定**：工作區層維持最小唯讀規則，不擴大專案層自動授權；全機 `~/.claude/settings.json` 保留由使用者依個人風險偏好收斂。 |
| **中** | **缺少自動化驗證 CI** | `waydefu/GPU` 原先完全沒有 `.github/workflows/`（`.claude/rules/gpu-structure.md:14` 曾記為無 CI）。 | **已補上 CI**：新增 `.github/workflows/governance-check.yml`，自動檢查 `HANDOFF.md` ≤150 行、無本機對話暫存路徑與憑證外洩、`scripts/zlogs-safe.sh` 語法、新增腳本禁用寫死 ADB/LAN 位址、以及凍結證據保護。 |
| **中** | **歷史 PR 狀態被錯誤回退 / 低：PR 描述與實際變更不符** | `waydefu/GPU#40`（2026-11-10）長期 `OPEN`，標題稱「393 files」但內容與今日 2026-11-26 歸檔／重整衝突；另外 `termux/proot#430` 曾送出後撤回。 | **已清理與對齊**：關閉過期衝突之 `waydefu/GPU#40`（保留原分支不破壞歷史）並以清晰單一 commit 同步今日權威狀態；`termux/proot#430` 狀態已確實記為 `CLOSED / WITHDRAWN`。 |

## 已驗證結果（2026-11-26）

- `scripts/zlogs-safe.sh`：
  - `bash -n` 通過；
  - `SHA256_BIN=/bin/false` 失敗測試確實拒絕刪除原檔並清理暫存（`FAILSAFE_OK`）；
  - `--dry-run` 與實際 2 MiB 壓縮校驗通過（`ZLOGS_SAFE ok=1 fail=0 ...`）。
- `patches/run_tiny_pixmap.py`：`python3 -m py_compile` 通過。
- `src/f8-proot-fast` 與 `src/termux-proot-upstream` 均維持 `dirty=0`。
