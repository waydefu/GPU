# AGENTS.md — GPU加速 (POCO F8 Ultra Termux:X11 GPU research)

Project root `/root/projects/GPU加速` is a plain folder holding Git worktrees
(`src/f8-ahb` experimental, `src/f8-ahb-debug` instrumented, `src/upstream` control,
Gate A frozen control `src/f8-ahb-gatea-a1`, active A1 implementation
`src/f8-ahb-gatea-xpump`, R5 installed `src/f8-ahb-gatea-r5-fix`, R6 source
`src/f8-ahb-gatea-r6-retire`, R7 source `src/f8-ahb-gatea-r7`, EXA Composite
timeout repair `src/f8-ahb-gatea-exa-timeout`, stall-phase diagnostic
`src/f8-ahb-gatea-stall-diag`, notify-phase diagnostic
`src/f8-ahb-gatea-notify-diag`, notify function-coverage diagnostic
`src/f8-ahb-gatea-notify-fn`, CASE_LOOP wakeup fix
`src/f8-ahb-gatea-case-loop`, R7-05 HUP preserve
`src/f8-ahb-gatea-r7-hup-preserve`, R7-10 HUP containment
`src/f8-ahb-gatea-r7-10-hup`, R7-P1 present-target arm
`src/f8-ahb-gatea-r7-p1-arm`) plus research docs. It is itself NOT a Git repo — work
per-worktree.

## Entry order (every task)

1. Read `HANDOFF.md` first — runtime authority (PIDs, SHAs, gate status). Never trust memory for status.
2. Then read `TEST-MATRIX.md`.
3. Current A1 implementation handoff:
   `evidence/session/gate-a-a1/p2-r3-xpump-implementation/HANDOFF-NEXT-AGENT-20260914.md`.
4. Current Gate A runtime authority:
 `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260919-r8-c1-attempt-09-adb-restored.md`
 (`b984ded` INSTALLED CI **35347497216**; ADB **RESTORED** SERIAL `10.191.48.13:46847`; R8-C1 attempt-09 cell **NOT RUN**; historical preflight **R8_BLOCKED ADB_CONNECT_FAILED** frozen; host tooling v2 **PUBLISHED**; attempt-08 **R8_INVALID** frozen; C2–P2 NOT RUN; do not silent-start C1; do not silent-retry `10.191.48.13:45165` or CI **35347497216**; do not create attempt-10; do not start C2 or R9; Production BLOCKED) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260919-r8-c1-attempt-09-blocked.md`
 (historical attempt-09 ADB connect failed) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-host-tooling-v2.md`
 (historical host tooling v2 published) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-08-invalid.md`
 (historical attempt-08 INVALID) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-07-invalid.md`
 (historical attempt-07 INVALID) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-terminate-install-blocked.md`
 (historical SCREEN_DOZING install-blocked; later install PASS) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-06-invalid.md`
 (`5a782f6` C1 attempt-05 INVALID frozen) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-giveup-end-install-blocked.md`
 (historical ADB-empty 2a245b0 install-blocked) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-obs-terminal-install-blocked.md`
 (historical ADB-empty install-blocked) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-c1-attempt-04-invalid.md`
 (`65938a4` attempt-04 INVALID; frozen) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-install-blocked.md`
 (historical install-blocked) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-header-escalation.md`
 (historical header-escalation) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-ci-fail-d382c0a.md`
 (historical `d382c0a` CI fail) and
 historical `evidence/session/gate-a-a1/p2-r8-design/HANDOFF-NEXT-AGENT-20260918-r8-ci-fail.md`
 (historical `bc25170` CI fail) and
 historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-complete-a4c8177.md`
 (historical R7 COMPLETE 13/13) and
 historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-p1-a4c8177.md`
 (historical a4c8177 first P1 INVALID) and
 historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-p1-abb27a65.md`
 (historical abb27a65 R7-P1 INVALID) and
 historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-p1-validity.md`
 (historical validity HOST_QUALIFIED / then committed) and
 historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-p1-8545b26.md`
 (historical R7-P1 INVALID device packet) and
 historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-p1-8545b26-runner.md`
 (historical R7-P1 runner QUALIFIED; device was NOT RUN) and
 historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-10-8545b26.md`
 (historical 8545b26 R7-10 PASS) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-10-8545b26-blocked.md`
   (historical 8545b26 R7-10 ADB BLOCKED) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-10-8545b26-runner.md`
   (historical runner QUALIFIED) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-10-rca.md`
   (historical RCA / artifact QUALIFIED) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-10-a07d66c.md`
   (historical R7-10 FAIL) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-11-a07d66c.md`
   (historical R7-11 PASS) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-11-a07d66c-blocked.md`
   (historical R7-11 ADB BLOCKED) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-11-a07d66c-runner.md`
   (historical R7-11 runner QUALIFIED) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-09-a07d66c.md`
   (historical R7-09 PASS) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-09-a07d66c-runner.md`
   (historical R7-09 runner QUALIFIED) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-08-a07d66c.md`
   (historical R7-08 PASS) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-07-a07d66c.md`
   (historical R7-07 PASS) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-06-a07d66c.md`
   (historical R7-06 PASS) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-03-a07d66c.md`
   (historical R7-03 PASS) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-02-a07d66c.md`
   (historical R7-02 PASS) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-01-a07d66c.md`
   (historical R7-01 PASS) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-a07d66c-runner.md`
   (historical runner QUALIFIED) and
   historical `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-01-blocked.md`
   (historical runner-authority BLOCKED) and
   `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-r7-05-a07d66c.md`
   (historical R7-05 PASS) and
   `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917-hup-preserve.md`
   (historical artifact QUALIFIED / then installed) and
   `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260917.md`
   (frozen historical R7-05 FAIL) and historical
   `evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md`
   (R7-04 PASS) and
   `evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260916.md`
   (frozen R6 device packet — do not rewrite).
5. Current post-R3 root-cause and implementation-decision document:
   `evidence/session/gate-a-a1/p2-r3-xpump-design/GATE-A-P2-R3-XPUMP-DESIGN-20260914.md`.
6. Current R6 design-complete + D2 COMPLETED root-cause + **D2 HOLD**:
   `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-DESIGN-20260915.md`,
   `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-D2-COMPLETED-ROOT-CAUSE-20260915.md`,
   and `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-D2-HOLD-20260915.md`.
7. R6 skills (parent folder, not inside a worktree). Worktree workspaces
   do not auto-discover them; read before R6 judge / C / CI / runtime:
   `/root/projects/GPU加速/.cursor/skills/gate-a-r6-design-review/SKILL.md`
   (review),
   `/root/projects/GPU加速/.cursor/skills/gate-a-r6-runtime-qualification/SKILL.md`
   (CI / install / D1–D2 / verdict),
   `/root/projects/GPU加速/.cursor/skills/gate-a-r6-present-retirement-implementation/SKILL.md`
   (frozen helper contract; implementation complete),
   and `gate-a-r6-runtime-qualification/references/RELATED-SKILLS.md`.
   Portable gate-design skill: `~/.agents/skills/evidence-first-gate-test-design/SKILL.md`
   (do not copy to `~/.cursor/skills/`).
8. Then read the relevant historical `evidence/session/<area>/GATE-*.md` only as needed.
9. F8 workstation redlines: `/root/.serena/memories/global/f8-workstation.md`.

## Current Gate A boundary (Cursor / Codex / Hermes)

- Frozen control worktree: `src/f8-ahb-gatea-a1`, exact HEAD `88e3f176d5be313b7dee058da9021cfe8d09e7de`, clean.
- Active implementation worktree: `src/f8-ahb-gatea-xpump`, branch `qualification/gatea-xpump-20260914`, HEAD `d9b7f60f24e722205891f1ce941816393ae4c695` clean.
- Historical `88e3f17`: R0–R2 PASS, R3 FAIL after `VALIDATE_TERMINAL_READY` then X `x-ready-timeout`. That APK is no longer installed.
- Root cause is proven by source: lorie never calls `InputThreadPreInit()`, so the REGISTER waiter and the only `conn_fd` callback reader are the same X main thread. The thread sleeps on its own waiter and cannot consume READY.
- Short-peek/demux defects are secondary; do not treat them as the first `88e3f17` blocker.
- Record-aware main-thread pump is committed (`d9b7f60`). Fork CI **34872266646** PASS; APK INSTALLED on experimental only.
- R1 unset PASS. R1 PROTO=0 first cell FAIL SIGSEGV PID 21639 (OBSERVED, dalvik-jit class / same family as 21977). Authorized one-shot PROTO=0 rerun PASS (X 27435); 21639 NON-REPRODUCED, root cause NOT PROVEN.
- R3 PASS (X 8034 consumed READY, pixels exact 64 `00804000`; historical `88e3f17` waiter deadlock falsified on `d9b7f60`).
- R2 PASS (X 28042, GATEA_EVENT=0, unique DRI3 modifier 1255 ×2, both cells exact `00804000`).
- R4 PASS (X 29807, 1514/1514 fail=0 maxΔ=0 Xnz=0, N=8 publish=consume=lookup=draw=fence=completed=success=ack).
- R5 FAIL (X 14858 hang after serial 819 RELOCK_DST; checkpoints 1/16/64/256 pixel PASS; 1024/4096 not reached). Authorized bounded rerun FAIL REPRODUCED (X 31265 hang after serial 1283 RELOCK_DST; 1/16/64/256/1024 pixel PASS; 4096 not reached). R5 root cause is PROVEN (AF_UNIX tiny-record backpressure + lock-across-write cycle).
- Bounded correction is COMMITTED `37d8393` on `fix/gatea-r5-backpressure-20260915` (worktree `src/f8-ahb-gatea-r5-fix`) and pushed to fork; GitHub CI run **34918397208** PASS; artifact QUALIFIED (APK SHA256 `31ec7037...`, Build ID `cc8cee05...`).
- APK INSTALLED on experimental only (`1.03.01-a4c8177-18.09.26` CI **35295094951**, SHA256 `91a4b74e…a55c`, Build ID `dcd82974…ba60`). Historical `abb27a65` CI **35253641841** superseded on device. Historical `8545b26` CI **35225593518** superseded on device. Historical `a07d66c` CI **35171333149** superseded on device. Historical `fdfb1ce` CI **35103216566** superseded on device. CASE_LOOP repair-validation **CASE_LOOP_REPAIR_VALIDATED** (X 19887; **not B-2**). B-2 requalification-01 **INVALID** frozen. B-2 requalification-02 **B2_REQUALIFICATION_PASS** (X 32228; oracle 1514/1514; stress 100/100/1000; timeout=0). Historical R7 qualification-01 **BLOCKED** (r7-04 X 31122 halt_mismatch; remaining cells NOT RUN; frozen). R7-04 requalification-01 **R7_04_REQUALIFICATION_PASS** (X 9891). Historical R7-05 **R7_05_QUALIFICATION_FAIL** (X 22704; last halt `r-hup reason=6`; frozen). `a07d66c` R7-05 **R7_05_A07D66C_REQUALIFICATION_PASS** (X 8418; last halt `x-direct-not-success/2`; r-hup/6=0). `a07d66c` R7-01 **R7_01_A07D66C_QUALIFICATION_PASS** (X 15029; last halt `r-gatea-DIRECT_LOOKUP_FAIL/2`). `a07d66c` R7-02 **R7_02_A07D66C_QUALIFICATION_PASS** (X 28625; event35 enum=2; last halt `r-gatea-DIRECT_LOOKUP_FAIL/2`). `a07d66c` R7-03 **R7_03_A07D66C_QUALIFICATION_PASS** (X 28326; event35 enum=3; last halt `r-gatea-direct-identity/5`). `a07d66c` R7-06 **R7_06_A07D66C_QUALIFICATION_PASS** (X 21795; last halt `r-gatea-fence-create/3`). `a07d66c` R7-07 **R7_07_A07D66C_QUALIFICATION_PASS** (X 31938; last halt `r-gatea-fence-wait/3`). `a07d66c` R7-08 **R7_08_A07D66C_QUALIFICATION_PASS** (X 14424; last halt `r-test-fatal-pre-fence/6`). `a07d66c` R7-09 **R7_09_A07D66C_QUALIFICATION_PASS** (X 22076; last halt `x-wrong-generation/6`). `a07d66c` R7-11 **R7_11_A07D66C_QUALIFICATION_PASS** (X 31764; last halt `x-serial-wrap/6`). `a07d66c` R7-10 **R7_10_A07D66C_QUALIFICATION_FAIL** (X 12568; last halt `x-direct-not-success/4`; frozen). `8545b26` R7-10 **R7_10_8545B26_REQUALIFICATION_PASS** (X 13115; last halt `x-hup/6`). `8545b26` R7-P1 **R7_P1_8545B26_QUALIFICATION_INVALID** (X 14331; last halt none; classifier `NO_PRESENT_CALLBACK`; frozen). Validity RCA **PROVEN**; abb27a65 target-arm **COMMITTED**; a4c8177 hold support **COMMITTED / INSTALLED**; a4c8177 R7-P1 **R7_P1_A4C8177_QUALIFICATION_INVALID** (X 24284; classifier `PEER_DIED`; frozen). R7 **COMPLETE 13/13**. Historical `feeaa56` stall-obs-01 **CASE_LOOP** frozen. Initial `327b028` is **SUPERSEDED**. Do **not** retry `runtime-a07d66c/r7-09`, `runtime-a07d66c/r7-08`, `runtime-a07d66c/r7-07`, `runtime-a07d66c/r7-06`, `runtime-a07d66c/r7-03`, `runtime-a07d66c/r7-02`, `runtime-a07d66c/r7-01`, `runtime-a07d66c/r7-05-requalification-01`, `runtime-fdfb1ce/r7-05`, `runtime-fdfb1ce/r7-04-requalification-01`, `runtime-7549e36/r7-qualification-01`, `runtime-7549e36/repair-validation-01`, `runtime-7549e36/b2-requalification-01`, `runtime-7549e36/b2-requalification-02`, `runtime-feeaa56/stall-obs-01`, `runtime-1f85b80/stall-obs-01`, or `runtime-27d8d1b/stall-obs-01`. Historical **R6 PASS** APK `1.03.01-0f1e546-15.09.26` CI **34999213228** is no longer installed. Frozen R6 worktree remains `0f1e546`. Historical B-2 FAIL on `0d72332` remains frozen. Historical `a7528bd` FAIL frozen. Production Gate A BLOCKED. Do not silent-retry `runtime-0d72332/r1-unset-oracle`, `runtime-a7528bd/r1-unset-oracle`, `runtime-95e6f96` inflight cells, or `9369553` D2.
- Do not silent-retry PROTO=0. Do not second-retry R5 on `d9b7f60`. Experimental device is `a4c8177` INSTALLED; B-2 **PASS**; historical R7-04 FAIL frozen; current R7-04 **PASS**; historical R7-05 **FAIL** frozen; current R7-05 **PASS**; a07d66c one-cell R7 runner **R7_A07D66C_RUNNER_QUALIFIED** (`run-r7-one-cell-a07d66c.sh` SHA256 `36d66f17…8ded`; r7-09 and r7-11 remain REVIEW_REQUIRED); a07d66c R7-09 dedicated runner **R7_09_A07D66C_RUNNER_QUALIFIED** (`run-r7-09-a07d66c.sh` SHA256 `d6ec76c1…f60d`); a07d66c R7-11 dedicated runner **R7_11_A07D66C_RUNNER_QUALIFIED** (`run-r7-11-a07d66c.sh` SHA256 `74385947…c453`); R7-01 **PASS**; R7-02 **PASS**; R7-03 **PASS**; R7-06 **PASS**; R7-07 **PASS**; R7-08 **PASS**; R7-09 **PASS**; R7-11 device **PASS / DEVICE-QUALIFIED**; historical a07d66c R7-10 **FAIL** frozen; RCA **PROVEN**; repair `8545b26` INSTALLED / R7-10 runner **R7_10_8545B26_RUNNER_QUALIFIED** (`run-r7-10-8545b26.sh` SHA256 `690a865d…54cd`); 8545b26 R7-10 device **PASS**; R7-P1 runner **R7_P1_8545B26_RUNNER_QUALIFIED** (`run-r7-p1-8545b26.sh` SHA256 `46c2289d…16ba7`); R7-P1 device **INVALID / FROZEN**; abb27a65 R7-P1 **INVALID / FROZEN**; a4c8177 R7-P1 **INVALID / FROZEN**; R7 **COMPLETE 13/13**. Do not overwrite B-2 or historical R7-01 cells. Do not retry historical r7-04, `r7-04-requalification-01`, either R7-05 cell, `runtime-a07d66c/r7-01`, `runtime-a07d66c/r7-02`, `runtime-a07d66c/r7-03`, `runtime-a07d66c/r7-06`, `runtime-a07d66c/r7-07`, `runtime-a07d66c/r7-08`, `runtime-a07d66c/r7-09`, `runtime-a07d66c/r7-11`, or `runtime-a07d66c/r7-10`. Do not silent-retry `runtime-a07d66c/r7-11-preflight`. Do not silent-retry `runtime-8545b26/r7-10-preflight`. Do not retry `runtime-8545b26/r7-10`. Do not retry `runtime-8545b26/r7-p1`. Do not retry `runtime-abb27a65/r7-p1`. Do not retry `runtime-a4c8177/r7-p1`. Do not retry `runtime-a4c8177/r7-p1-validity-02`. Do not retry `runtime-a4c8177/r7-p2`. Do not use the generic one-cell runner for r7-11. Do not use the generic one-cell runner for 8545b26. Generic r7-11 remains REVIEW_REQUIRED; do not sed fdfb1ce runners or widen `run-r7-05-requal-a07d66c.sh`. Historical `feeaa56` stall-obs-01 **CASE_LOOP** frozen. `327b028` SUPERSEDED. Do not silent-retry R8 CI **35304122983**, **35305368742**, **35311343984**, **35321447455**, **35331185799**, **35338856846**, or **35347497216**. Do not install `bc25170` or `d382c0a`. Device is `b984ded` INSTALLED. ADB **RESTORED** SERIAL `10.191.48.13:46847`. R8-C1 attempt-09 cell is **NOT RUN** (dir absent). Do not silent-start C1. Do not silent-retry `10.191.48.13:45165`. Do not create attempt-10. R8-C1 attempt-08 is **R8_INVALID** `MULTI_BEGIN_x` frozen. Do not retry C1 attempts 01–08. Do not retry `runtime-b984ded/r8-c1`. Do not retry `runtime-fb4f017/r8-c1`. Do not start R8-C2. Do not start R9–R10, Stable, HDMI, Production enable, origin PR/merge, origin push, or force without a new explicit authorization. Do not silent-retry R6-D1 historical cells. Do not silent-retry `runtime-0d72332/r1-unset-oracle` or `runtime-a7528bd/r1-unset-oracle`.
- Never rerun R3 on `88e3f17`, `8479997`, `6c7ee6f`, or `98b0011`.

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
- Closed gates stay closed: P0 / P1 / P2-A / P2-B.1 / P2-B.2 (R3 PASS). Do not reopen them as P2-B.3. Current work is Gate A P2: device `a4c8177` INSTALLED / CASE_LOOP repair-validation **CASE_LOOP_REPAIR_VALIDATED** / B-2 **PASS** (`b2-requalification-02`, X 32228) / historical R7 **BLOCKED** (`r7-qualification-01` r7-04 halt_mismatch) / R7-04 requal **PASS** (`r7-04-requalification-01`, X 9891) / historical R7-05 **FAIL** (`runtime-fdfb1ce/r7-05`, X 22704 last halt `r-hup/6`) / current R7-05 **PASS** (`r7-05-requalification-01`, X 8418) / a07d66c one-cell R7 runner **QUALIFIED** / R7-09 dedicated runner **QUALIFIED** / R7-11 dedicated runner **QUALIFIED** / R7-01 **PASS** (`runtime-a07d66c/r7-01`, X 15029) / R7-02 **PASS** (`runtime-a07d66c/r7-02`, X 28625) / R7-03 **PASS** (`runtime-a07d66c/r7-03`, X 28326) / R7-06 **PASS** (`runtime-a07d66c/r7-06`, X 21795) / R7-07 **PASS** (`runtime-a07d66c/r7-07`, X 31938) / R7-08 **PASS** (`runtime-a07d66c/r7-08`, X 14424) / R7-09 **PASS** (`runtime-a07d66c/r7-09`, X 22076) / R7-11 **PASS** (`runtime-a07d66c/r7-11`, X 31764) / historical R7-10 **FAIL** (`runtime-a07d66c/r7-10`, X 12568) / 8545b26 R7-10 runner **QUALIFIED** / 8545b26 R7-10 device **PASS** (`runtime-8545b26/r7-10`, X 13115 last halt `x-hup/6`) / R7-P1 runner **QUALIFIED** / 8545b26 R7-P1 **INVALID** (`runtime-8545b26/r7-p1`, X 14331, `NO_PRESENT_CALLBACK`) / abb27a65 R7-P1 **INVALID** (`runtime-abb27a65/r7-p1`, X 19686, `PEER_DIED`) / a4c8177 R7-P1 **INVALID** (`runtime-a4c8177/r7-p1`, X 24284, `PEER_DIED`) / a4c8177 P1 validity-02 **PASS** (X 1892) / a4c8177 P2 **PASS** (X 12663) / R7 **COMPLETE 13/13**; Production Gate A stays BLOCKED. R8 support `b984ded` INSTALLED CI **35347497216**; ADB **RESTORED** SERIAL `10.191.48.13:46847`; R8-C1 attempt-09 cell **NOT RUN**; historical preflight **R8_BLOCKED ADB_CONNECT_FAILED**; attempt-08 **R8_INVALID** `MULTI_BEGIN_x` frozen; attempts 01–07 frozen; C2–P2 NOT RUN; historical CI **35304122983** / **35305368742** **R8_CI_FAIL** frozen; prototype `d382c0a` kept; do not silent-start C1; do not silent-retry those CIs, `10.191.48.13:45165`, or C1 attempts 01–08; do not create attempt-10; do not retry `runtime-b984ded/r8-c1` or `runtime-fb4f017/r8-c1`; do not start R8-C2.
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
-m gpt-5.6-luna-900k
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
  -m gpt-5.6-luna-900k \
  --provider openai-codex \
  --reasoning max \
  -s serena-projects,spec-grounded-review \
  --max-turns <bounded-turns> \
  --run-budget <bounded-seconds> \
  --source <unique-task-tag> \
  --in /root/projects/GPU加速/src/f8-ahb
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
