# 這份手機副本是什麼

完整專案在 workstation `/root/projects/GPU加速`。
這裡只放 **Markdown + 核心 C／judge／技能**，方便請人規劃後續。

**先讀狀態交接：** `STATUS-HANDOFF-20260916.md`

然後：`HANDOFF.md` →
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md` →
`evidence/session/gate-a-a1/p2-r7-design/WAYDEFU-GPU-PR-MAP-20260916.md`。

Docs PR（本倉庫 **沒有 status checks**）：
- [PR #1](https://github.com/waydefu/GPU/pull/1) 歷史 R6 PASS `0f1e546` — **已 merge**
- [PR #2](https://github.com/waydefu/GPU/pull/2) 歷史 B-2 RCA（已被 #3 包含）— **不 merge 關閉**
- [PR #3](https://github.com/waydefu/GPU/pull/3) 目前 stall-obs 快照（含 #2 + #1 獨有 R6 證據）— **已 merge**

`termux-x11` fork artifact CI PASS ≠ 本倉庫 PR 綠燈 ≠ R7 qualification。

不含：完整 git worktree、xserver submodule、APK、ELF、logcat dump、`.gradle`／build。

不是 B-2 PASS。不是授權 retry stall-obs-01。R7 support artifact 存在；R7 qualification **未開始**。
