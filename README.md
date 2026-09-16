# 這份手機副本是什麼

完整專案在 workstation `/root/projects/GPU加速`。
這裡只放 **Markdown + 核心 C／judge／技能**，方便請人規劃後續。

**先讀狀態交接：** `STATUS-HANDOFF-20260916.md`

然後：`HANDOFF.md` →
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md` →
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-27d8d1b/GATE-A-P2-STALL-OBS-01-20260916.md` →
`core-src/stallPhaseLog.c`。

歷史：
- [PR #1](https://github.com/waydefu/GPU/pull/1) R6 PASS `0f1e546`
- [PR #2](https://github.com/waydefu/GPU/pull/2) B-2 RCA + EXA timeout 修復摘錄

不含：完整 git worktree、xserver submodule、APK、ELF、logcat dump、`.gradle`／build。

不是授權開 R7。不是 B-2 PASS。不是授權 retry stall-obs-01。
