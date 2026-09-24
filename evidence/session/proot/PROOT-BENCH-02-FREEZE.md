# PROOT-BENCH-02 — Cursor 在 proot-fast v2（PF2）對系統 proot（P0）：判準凍結

**狀態：FROZEN（2026-09-24 19:5x，使用者 19:32 起授權兩小時內自行決定測試）。凍結時沒有任何 PF2 的 Cursor 資料。**
已知的只有微基準 `proot-fast2-bench-01.txt`（futex／epoll_pwait／fcntl 約 30–60 µs → 0.2 µs；對照組 `PROOT_KOMPAT_FULL=1` 變慢回來）。

## 為什麼有 02
PROOT-BENCH-01（proot-fast v1，只拿掉 socket／clone 攔截）判 `PROOT_FAST_NO_BENEFIT`：PF 下追蹤器仍吃 0.28–0.30 核。
日常 PRoot 的 ptrace-stop 抽樣（`trapmix`）找到原因：`--kernel-release` 啟用 kompat 擴充，它無條件攔 futex、epoll_pwait、pselect6、
fcntl、pipe2、dup3…（並強迫 openat／execve 等離開時再停一次），但在實際核心 ≥ 2.6.29 時所有處理都是 no-op；它還在每次 execve 後拿掉 vDSO。
v2 = v1 ＋ kompat-lean：實際核心 ≥ 2.6.29 且未設 `PROOT_KOMPAT_FULL` 時，kompat 只攔 uname／sethostname／setdomainname，且不拿掉 vDSO。

## 組態（與 01 相同，只換 PF 的二進位）
| 代號 | 追蹤器 |
|---|---|
| P0 | `/data/data/com.termux/files/usr/bin/proot`（系統 5.1.107.92，sha256 前綴 `ea47e17da8e6ff48`） |
| PF2 | `~/build/proot-fast/out2/bin/proot-fast2`（5.1.107.92-fast2，sha256 前綴 `8a30e9d63aead905`，loader 在 `out2/libexec`） |
其餘（42 個日常參數、Cursor 旗標、driver、負載、順序 rep01 P0→PF→P0'／rep02 PF→P0→PF'、run-as 側計量與結束、記憶體等待）與 01 相同。
工具 = 01 受判版本，唯一差別是 cell 與 judge 以環境變數 `PF_BIN` 指定 PF 路徑（預設值仍是 v1）。

## 指標與判準（與 01 逐字相同）
- `S` = 捲動＋打字 CPU（Cursor session＋追蹤器＋X3）；`noise = max(|S(P0)−S(P0')|/S(P0), |S(PF)−S(PF')|/S(PF))`。
- **CPU_BETTER** 每次重複 `S(PF2) ≤ S(P0) × (1 − max(0.10, 2×noise))`；**IDLE_OK** 閒置 `PF2 ≤ P0 + 0.05 核`；
  **FRAMES_NOT_WORSE** `p95(PF2) ≤ p95(P0)×1.10` 且 `>50ms(PF2) ≤ >50ms(P0)+3`。
- 判決 `PROOT_FAST_BENEFIT`／`PROOT_FAST_NO_BENEFIT`／`PROOT_FAST_FAIL`（PF2 的 Cursor 功能失效）／`PROOT_INVALID`；有效性條件同 01。

## 流程（自動化，中途不看數字）
1. 乾跑 `proot-bench-02-dryrun`（P0、PF2 各一輪）：judge `analyse()` 兩輪都 VALID 才繼續；PF2 的 arg0 必須是 `…/out2/bin/proot-fast2`、
   cell 的 `PROOTS pf=` 必須是 `8a30e9d63aead905`。否則停止，不進正式。
2. 正式 `proot-bench-02-rep01`、`-rep02`；任一 rep 非 `CMD_CAPTURED` 就停止。
3. 以 `PF_BIN=…/out2/bin/proot-fast2 proot_bench_judge.py rep01 rep02` 判決；門檻不調、不重跑。

## 不在範圍內
換掉日常 proot（另依結果決定）、其他程式、bwrap 行為（v1 起 socket 攔截需 `PROOT_BWRAP_COMPAT=1`）。
