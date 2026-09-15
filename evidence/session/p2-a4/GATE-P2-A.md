# GATE P2-A — CLOSED

> Gate close record. The verdict remains current, but the PID/APK details in this file belong to the P2-A run; current runtime and next gate are maintained in `HANDOFF.md`.

```
P2-A: CLOSED
Failure was histogram probe double-wrap lifecycle, not backing / pitch / fb / pixman.
Repair: 6182b94 per-screen install-once + drop post-DamageRegister install.
A.3 ROOT CAUSE CONFIRMED
A.4a topology PASS
A.4b probe return PASS
A.4c EXA/fb path reached and returned PASS
A.4d matrix + ×100 PASS
A.4e bounded XFCE compositor PASS
Stable :1 PID 26474 untouched throughout
Next at the time: P2-B.1 Composite dispatch + software-fallback census (completed).
Current next: P2-B.3 real-workload performance qualification.
```

P2-A asked why real Composite crashed. After A.3/A.4 the answer is sealed:

`lorieInstallXRenderProbe` ran twice. The second call, after `DamageRegister`, saved `damageComposite` as the probe’s next hop while Damage already pointed at `lorieCompositeProbe`. The cycle exhausted the stack (SIGILL). EXA / fb / pixman were **not reached** on the crashing build.

`6182b94` made install idempotent on per-screen state and removed the duplicate call site. 1×1, matrix, ×100, and a bounded XFCE session on `:3` all returned. At this P2-A close, `PrepareComposite` was still `FalseNoop`; P2-B.2 later added only the narrow Over slice and passed R3. This report does not reopen P2-A.

Do not reopen A.2 pointer/pitch as the P2 crash root cause. Do not treat this close as GPU Composite work.
