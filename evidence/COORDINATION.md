# 協作記錄

## 2026-09-14（Cursor / Codex Gate A project sync）

- Cursor與Codex專案根皆以 `/root/projects/GPU加速` 為共同研究入口；兩者依官方支援讀取根目錄 `AGENTS.md`。
- `AGENTS.md` 已改為單一導覽鏈：`HANDOFF.md` → `TEST-MATRIX.md` → `p2-r3-terminal-runtime/HANDOFF-NEXT-AGENT-20260914.md` → `p2-r3-xpump-design/GATE-A-P2-R3-XPUMP-DESIGN-20260914.md`。
- Current Gate A：`88e3f17` R0–R2 PASS、R3 FAIL；第一個 blocker 已由source證明為X主執行緒自我等待。short-peek/demux是次要缺陷，不是本次首先發生的原因。
- 修復方向為bounded record-aware main-thread pump；設計已完成但source實作仍在使用者決策邊界。禁止把附件中的copy-paste pump直接套入source。
- 本輪同步只改研究文件與agent入口；C/C++ worktree仍是exact `88e3f17` clean。未build、push、CI、ADB、install或runtime。
- Cursor全域context／memory稽核：[`evidence/session/cursor-global-memory-audit-20260914.md`](session/cursor-global-memory-audit-20260914.md)。結論是移植精簡User Rule＋可攜式Skills，不整包複製Hermes記憶；MCP調整另立授權，避免影響Clinic。

## 2026-09-08（Codex 專案綁定）

- 詳細紀錄：[`evidence/session/codex-project-binding-2026-09-08.md`](session/codex-project-binding-2026-09-08.md)。
- 最新本機核對：`GPU加速` 的資料庫與桌面端快取都指向 `/root/projects/GPU加速`；檔案選擇器曾回傳空路徑 `stat ''`，原因未歸因於 Markdown 或權限。

**以下為2026-09-08歷史快照；現況一律以目前的`HANDOFF.md`與上方2026-09-14同步鏈為準。** 當時文件曾於2026-09-08 15:33 CST重新查驗；未重新探測裝置。

## 2026-09-08 ~07:40 CST（P2-B.2 PASS R3）

- Stable `:1` PID **26474** `com.termux.x11` `1.03.01-11b82d9`：不可碰。
- Experimental `:3` PID **29225** ppid=1，`com.waydefu.x11gpu` `1.03.01-9822435-07.09.26` commit `9822435` CI `34168546084`。
- P2-B.2 PASS：校正後 oracle `fail=0` `maxΔ=0`；×100 / mixed100 / ×1000 PASS；bounded XFCE 45s 無 fatal，隨後已停。
- 歷史 1094-fail 是 tester 用 root depth-24 GC 對 depth-32 source PutImage（`BadMatch` 8），不是 GPU slice。閘門 `evidence/session/p2-b2/GATE-P2-B.2.md`。
- 勿開 PR；勿加寬 mask/two-pass/transform；實驗 APK 只准進 waydefu。

## 2026-09-08 ~06:35 CST（P2-B.2 FAIL，已由 R3 取代）

- Stable `:1` PID **26474** `com.termux.x11` `1.03.01-11b82d9`：不可碰。
- Experimental `:3` PID **13655** ppid=1，`com.waydefu.x11gpu` `1.03.01-d7de868-07.09.26`。閘門 `evidence/session/p2-b2/GATE-P2-B.2.md`。
- P2-A CLOSED、P2-B.1 CLOSED/PASS、P2-B.2 FAIL（oracle got==dst；FDCLONE px0 全 0）。勿開 `:3` XFCE，勿 PR。
- 實驗 APK 只准進 waydefu；裝包前先停 `:3` 並 `am force-stop com.waydefu.x11gpu`，否則 `pm install-commit` 會掛。

## 2026-09-07 ~19:39

- Stable `:1` PID **10718** / XFCE **18844** / xfwm **18871**：雙方皆不可碰。
- Experimental 只用 `:3` + `com.waydefu.x11gpu`。`:2` 不再使用。
- 禁止：raw CI `com.termux.x11` 安裝、`pkill -f f8-x11gpu`、`logcat -c`、babysit 重啟、未隔離就開 xfwm。
- P2：1×1 RENDER Composite 會殺 X；xfwm compositor-off 同一 last request。crash instance 不重啟。

## 2026-09-07 ~22:55 CST（事故＋回退，已結案）

- 事故：21:32 有人把 P2STAGE CI 包（`1.03.01-6721db9`，sha `9b038a5d…`）裝進 `com.termux.x11` 蓋掉 Stable → `:1` 在 xfce/xfwm 啟動後堆疊溢位（stack overflow，tombstone 512 同幀 `blr x8` 自我呼叫，BuildId `30091699…` 已在實際出事庫反組譯確認）。
- 回退：同簽名（`b6da0148…`）`adb install -r` 覆蓋回 control（`1.03.01-11b82d9`，sha `aad3d433…` 已驗），firstInstallTime 未動、資料無損。禁刪掉重裝（沒必要）。
- 鐵律（再犯即停工）：CI／實驗 APK 只准進 `com.waydefu.x11gpu`；`com.termux.x11` 非凍結包永不覆寫；adb 連法見本機（f8-adb-port＋kill-server 後連）。

## 2026-09-07 ~02:30 CST（歷史）

- 本工作階段（Phase 1B-1/1B-2 runtime＋code hunt）原用 `:2`，02:17–02:28 間 `:2` server
  已退場（非本工作階段所殺，log 無 crash 行；應為另一工作階段收尾或系統回收）。
- 為避免互相干擾：**`:2` 留給另一工作階段，本工作階段後續 runtime 測試改用 `:3`**。
- 共用檔（TEST-MATRIX.md、evidence/）只做最小追加，不改對方段落。
- `src/upstream` 工作樹不動；新分支一律用獨立 worktree（`src/f8-*`）。
- Stable `:1`（PID 10718）雙方皆不可碰；APK 不安裝、不覆蓋。
