# B3a U4 execution checklist — 2026-09-11

此文件是本輪執行控制，不取代 runtime evidence。唯一實驗目標為
`com.waydefu.x11gpu` / `DISPLAY=:3`；Stable `com.termux.x11` / `:1` 不操作。

## U4-L1 lifecycle

- [x] 三個獨立 R3 server sessions；每個都 `create → use → release → teardown`，下一輪重建。
  - Evidence: `B3A-T2-U4-L1-LIFECYCLE-20260910.md`; PIDs `30844`, `2882`, `11183`; all final `NO_X3_RESIDUE`.
- [x] 每輪：Activity `displayId=0`、X PID/cmdline、holder、oracle、cold one-op cell、actual-server RSS/FD T0/T1/T2/T3。
  - External live FD is `NOT OBSERVABLE`; server telemetry gives `x_fd_start=79`, `x_fd_end=89` in all three sessions.
- [x] 每輪：telemetry exact-count `1520/1520`（oracle 1519 + cell 1）、oracle/cell exact PASS、R3 fallback=0、`NO_X3_RESIDUE`。
- [x] 記錄 buffer registration/release counters 與 renderer queue state。
  - Explicit release counter and queue state are `NOT OBSERVABLE`; `Gcomp FDCLONE=Gcomp Done=1516` per session is retained as operational evidence.

> Historic U4-L1 preflight block is resolved by fresh serial `10.56.180.219:39035`; full record remains in `B3A-U4-L1-PREFLIGHT-20260910.md`.

## cold-N5

- [x] 五個短窗 CPU↔R3 配對；64×64，cold=1、batch=1、immediate GetImage、warmup=100、count=500。
  - Sequence: CPU1→R31→R32→CPU2→CPU3→R33→R34→CPU4→CPU5→R35.
- [x] 每個 session：oracle/cell exact PASS、telemetry `2119/2119`、資源 endpoint、teardown residue=0。
  - Ten sessions passed; CPU fallback=1, R3 fallback=0; all `NO_X3_RESIDUE`.
- [x] 彙整 median/p95/min/max、pair ratios、aggregate ratio、R3 promotion/AHB alloc/clone/DoneComposite。
  - Aggregate measured-only R3/CPU median=3.188×; detail/evidence: `B3A-T2-U4-COLD-N5-20260910.md`, `t2-u4-cold-n5/`.

## C2 batch16 exact-sequence reproduction

前置：embedded `libXlorie.so` Build ID 與 matching unstripped symbol file 必須相符。

- [x] **C2 provenance PASS**：artifact `10160961032` ZIP digest、ARM64 unstripped
  extraction、Build ID、installed APK embedded library 全部已比對；詳見
  `B3A-U4-C2-ARTIFACT-PROVENANCE-20260911.md`。
- [x] 保存 APK/lib hash、embedded Build ID、matching unstripped Build ID、git HEAD、git status。
- [x] 若 provenance PASS，完整回放 `CPU-A → R3-A → CPU-B → R3-B` 三次，並保存 launcher logs 與 phase markers；本輪無 crash，未需另行 crash-buffer capture。
- [x] 任一 crash：STOP benchmark expansion，轉 crash forensic。
  - 本輪無新 crash；historical R3-B startup SIGSEGV 為 `3/3 non-reproduced`，root cause 仍 unknown。
- [x] 三次皆 clean：batch16 exact-protocol performance completion PASS。詳見
  `B3A-T2-U4-C2-20260911.md`、`t2-u4-c2-exact-sequence/C2-SUMMARY.json`。

## Completion evidence

- [x] Raw stdout/stderr, JSON/CSV, launcher log, phase logs, resource snapshots copied into durable evidence before next phase.
- [x] Update `GATE-P2-B.3a.md`; update `HANDOFF.md` only if stage verdict changes.
