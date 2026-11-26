# AGENTS.md — GPU加速 / 非 Root Android PRoot 工作站研究

Project root `.` is a plain folder holding source trees (see `WORKTREE-MAP.md`), research docs, and frozen evidence. It is itself NOT a Git repo — work per-repo/worktree.

## Entry order (every task)

1. Read [`HANDOFF.md`](HANDOFF.md) first — current status authority across all tracks (PRoot `proot-fast8`/`auto-shard`, Gate A `RESEARCH COMPLETE / PAUSED`, Track #3 `FEASIBILITY COMPLETE / PAUSED`, upstream status).
2. Read [`WORKTREE-MAP.md`](WORKTREE-MAP.md) for active source trees (`src/f8-proot-fast`, `src/termux-proot-upstream`, and the 5 preserved `termux-x11` worktrees).
3. Read [`TEST-MATRIX.md`](TEST-MATRIX.md) and historical ledgers in `docs/archive/handoffs/` only when touching historical Gate A / GL / PRoot artifacts.
4. F8 workstation redlines: `/root/.serena/memories/global/f8-workstation.md`.

## Current Track Boundary (2026-11-26)

- **PRoot Performance & Auto-Shard (ACTIVE)**: `src/f8-proot-fast` (`main` `ee603b8`) holds `proot-fast8` patches, `f8-shard` v2, `shard-daemon.sh` fix 4, and offline tests. Do not mutate live `$PREFIX/home/build/proot-fast/out8/`, `shard2/`, `$PREFIX/bin/f8desk*`, or `/usr/local/bin/f8-shard` without explicit authorization.
- **Gate A 2D GPU Acceleration (RESEARCH COMPLETE / PAUSED)**: R6 (`0f1e546`), R7 (13/13), R8–R10 technical qualification completed as research assets; `XFCE-NOTEL-01` proved daily 2D GPU yields no net gain over CPU once `GATEA_TELEMETRY` is disabled. Do not reopen closed gates (P0/P1/P2-A/P2-B.1/P2-B.2), do not overwrite or retry any frozen cells under `evidence/session/gate-a-a1/`, and do not enable Production Gate A.
- **Track #3 GL/VK Present (FEASIBILITY COMPLETE / PAUSED)**: `GL-PRESENT-03` + `X3-DIRECT-FEAS` completed; X3 Vulkan copy yields too little net gain for its complexity. "EGL black-screen / no-present" remains conditional TODO.
- **Historical Gate A ledger**: Archived verbatim at `docs/archive/handoffs/HANDOFF-LEDGER-20260919.md` (plus `STATUS-HANDOFF-20260921.md`, `HANDOFF-NEXT-SESSION-20260923..27.md`). All historical `do not retry` / `frozen` constraints on consumed device cells remain permanently in force.

## ART JIT 偶發當機分類與處置規則（0x4800xxxx / dalvik-jit 類）

高低階代理（Sol High / Luna Max / Codex）通用鐵則：

1. **特徵簽名**：
   - Faulting PC 落入 `0x4800xxxx`，核對 `/proc/$PID/maps` 確實在 `[anon_shmem:dalvik-jit-code-cache]`。
   - `signo=11` (SIGSEGV), `si_code=1` (SEGV_MAPERR), `si_addr=0x0`（Null dereference）。
   - 暫存器特徵（ARM64）：`x0=0x61`, `x1=0x0680f338` (Dalvik heap), `x8=0x3`。
   - `Uraw 60` 含有 ASCII 碎片 `undleMonitorStub` (ART monitor/locking stub)。
   - Backtrace 在 `libXlorie.so` 內唯一看到的只有訊號處理函式本身（`p2a3CrashHandler`），不是原始觸發指令。
2. **本質與定性**：
   - 這是 Termux:X11 以 `app_process64` 啟動 Java/ART 運行時並以 `sun.misc.Unsafe` 偽造 Context 啟動階段，Android 16 / HyperOS 的 ART JIT 編譯與物件鎖調度產生的極偶發系統級競態。
   - **不是 `libXlorie.so` 的 C/C++ 原始碼邏輯問題**，更不是 Gate A DDX / renderer / socket pump 造成的。
3. **處置紀律（嚴禁瞎修）**：
   - **嚴禁改動 C/C++ 核心邏輯**：禁止為了這個無法定位到 C 原始碼行數的 JIT 空指針去修改 socket pump、waiter 或 DDX。
   - **低階代理（Luna Scout / Worker）**：只負責提取 `maps` 對齊、PC/Uraw 字串判定、驗證 Build ID 與抓取 logcat，回傳最小特徵包，**不得自行判定「軟體 bug」或提出 C 程式碼修改建議**。
   - **高階代理（Sol High）**：標記為 `OBSERVED`，依歷史慣例申請單次有界重跑（one bounded rerun）。若重跑 PASS，定性為 `NON-REPRODUCED / ROOT CAUSE NOT PROVEN`。
   - **Fail-Closed 停機防線**：任何未經授權的啟動當機，即使懷疑是 JIT 類，也必須先停閉後續 R3/R4 測試，不得自動 silent-retry，經顯式授權後方可重跑或推進。

## Redlines

- Stable display `:1` (daily driver, `com.termux.x11`) is NEVER touched. Experimental APKs only in `com.waydefu.x11gpu`.
- Closed gates stay closed: P0 / P1 / P2-A / P2-B.1 / P2-B.2 (R3 PASS) / R6 / R7 (13/13) / R8–R10 (`RESEARCH COMPLETE / PAUSED`). Do not reopen closed gates or retry frozen device cells/CIs listed in [`docs/archive/handoffs/HANDOFF-LEDGER-20260919.md`](docs/archive/handoffs/HANDOFF-LEDGER-20260919.md) and [`TEST-MATRIX.md`](TEST-MATRIX.md); Production Gate A stays BLOCKED.
- Predicate stays narrow: mask / two-pass / transform / bilinear / repeat / componentAlpha remain software.
- No `termux/termux-x11` origin PR. Docs-only `waydefu/GPU` PRs are records, not qualification. No `±1 UNORM counts as PASS`. Kill/install safety exactly as HANDOFF.md "Runtime" says.

## Done means

Gate doc updated under `evidence/session/` + stress per TEST-MATRIX.md + HANDOFF "Next" still holds + Stable verified untouched.

## 子代理分工與 Hermes 使用規則

為節省 Sol High 額度，**凡是可安全拆分的工作，優先指派給 `GPT-5.6 Luna Max` 子代理執行**，例如：

```text
Serena symbol navigation
call/reference tracing
局部 source reading
git provenance
build/log evidence整理
benchmark資料彙整
文件比對
低風險 static audit
候選方案初步整理
```

Sol High 自己只保留：

```text
Gate A / Gate D 架構裁決
AHB / EGLImage byte contract
ownership / fence semantics
跨 thread lifecycle
高風險 root-cause
最終 prototype 邊界與 decision
```

原則：

> **能委派給 Luna Max 的，不要由 Sol High 親自消耗上下文；Luna Max 回傳結論＋最小證據即可，Sol High 再做最終驗證。**

但子代理同樣受本提示詞全部限制：**不得碰 Stable、不得擴 scope、不得自行修改高風險 renderer / ownership / fence semantics。**

### 併發上限

- **同一時間最多執行 2 個子代理。** 這是本專案上限；即使 Hermes 全域設定允許更多，也不得啟動第 3 個。
- 任務超過 2 個時，固定以最多 2 個為一批；等其中一個退出、確認結果後，才可補下一個。
- ARM64／PRoot 資源緊張時可降為逐一執行；不得為追求平行度壓垮 workstation。

### 模型與思考程度必須由 Hermes 直接設定

在 prompt 內寫「請深度思考」**不等於**設定 reasoning。啟動每個 Luna Max 子代理時，必須在 Hermes CLI 明確指定：

```text
-m gpt-6-luna-900k
--provider openai-codex
--reasoning max
```

`--reasoning max` 是實際 runtime 設定；prompt 只負責角色、scope、authority 與回報格式。除非任務明確要求較低 reasoning，專案的 Luna Max scout／writer 預設一律用 `max`。

一次性環境設置／確認：

```bash
# 尚未登入 openai-codex 時才執行；不得複製或外洩 token
hermes auth add openai-codex

# 確認 CLI 支援 model/provider/reasoning 參數
hermes chat --help
```

若要調整全域預設，可用：

```bash
hermes config set agent.reasoning_effort max
```

但本專案仍須在每次子代理 invocation 顯式傳 `--reasoning max`，不可依賴可能漂移的全域預設。

### Read-only scout 使用方法

每個 scout 使用獨立 one-shot session、唯一 `--source` tag 與獨立 `/tmp` query/report 檔；禁止 `--resume`／`--continue`：

```bash
hermes chat \
  --query-file /tmp/<task>.prompt \
  -Q \
  -m gpt-6-luna-900k \
  --provider openai-codex \
  --reasoning max \
  -s serena-projects,spec-grounded-review \
  --max-turns <bounded-turns> \
  --run-budget <bounded-seconds> \
  --source <unique-task-tag> \
  --in ./src/f8-ahb
```

Scout prompt 必須明列：

```text
READ ONLY
exact branch + HEAD
先讀 authority
Serena project 使用既有名稱 gpu-f8-ahb
禁止 adb/device/install/build（除非該 scout 明確負責執行）
禁止 source/doc mutation、commit、push
只回 conclusion + minimum evidence + symbols + unknown/risk
```

Serena source research 優先使用 `find_symbol`、`find_referencing_symbols`、`get_symbols_overview` 與 bounded symbol body；不可先全文讀大型 source 或全 repo grep。Scout 結束後，parent 必須檢查 `git status --short`／`git diff --check`；若 Serena/clangd 留下已確認為本輪生成的 `.cache/` 或 `.serena/`，只清理該精確 generated path，再次確認 tracked source clean。

### Writer 使用方法

一旦進入 source write，必須同時滿足：

```text
ONE WRITER
=
ONE INDEPENDENT SESSION
=
ONE LINKED WORKTREE
```

Writer invocation 使用同一組 model/provider/reasoning 明確參數。若 parent 尚未建立 worktree，使用 `--worktree`（`-w`）讓 Hermes 建立；若 parent 已建立並驗證命名 linked worktree，則直接以 `--in <linked-worktree>` 啟動，**不得再加 `-w` 建立第二層 worktree**。禁止兩個 agent 同時寫同一 worktree。Writer 開始前必須核對 exact HEAD、clean status、批准 scope；若需要越過 Sol 核准邊界，立即停止並回報。

### Session 與回報紀律

子代理一律使用新建的獨立 session，禁止 resume 同一 session、共用父代理 session，或兩個 writer 共用 session（2026-09-11 已證實單 session 互斥會拒絕第二個寫入者）。父子上下文只透過 prompt／evidence／summary 顯式搬運，不共享 mutable tool state。

每個 Luna 結果只搬回：

```text
CONCLUSION
MINIMUM EVIDENCE（含 path:line / symbol）
RELEVANT SYMBOLS
UNKNOWN
ARCHITECTURE RISK FLAG
```

Luna 不做最終 architecture authorization；Sol 只讀上述最小 packet，再親自複核真正影響 invariant、ownership、fence 或 lifecycle 的 decisive source。
