# V1-Core execution entrypoint

**Planning only. No device, source, CI, install, merge, or production authorization is conveyed by this PR.**

Authority checked on 2026-09-17 (Asia/Taipei): `waydefu/GPU/main` **`c95b893ea161d5aacb7b633495b1751ac97182b7`**, including merged [PR #6](https://github.com/waydefu/GPU/pull/6). Its old in-file “not merged” wording is historical. Before future execution, fetch current main and reconcile newer handoffs without overwriting this snapshot.

| Current merged record | Status |
|---|---|
| Candidate | `fdfb1ce44b429897eda17c43bf33fbd37afe67f3`, experimental `com.waydefu.x11gpu`, recorded INSTALLED; live binding must be checked again |
| R6 | PASS / FROZEN on `0f1e54699d0b11a781f2c044fbc77505f8a53bd8` |
| RCA-1 / CASE_LOOP | FIXED / DEVICE-PROVEN; hardened `7549e36` DEVICE-VALIDATED |
| B-2 | PASS, `runtime-7549e36/b2-requalification-02` |
| R7-04 | `R7_04_REQUALIFICATION_PASS` on `fdfb1ce`; old `7549e36` valid FAIL remains FROZEN |
| R7 overall | IN PROGRESS, **not** GATE_PASS |
| R8 / R9 / R10 / Production Gate A | Not qualified / Production Gate A BLOCKED |

```text
CURRENT NEXT QUALIFICATION:
R7-05 / post-draw-gl
NEXT-001 — R7-05 post-draw-gl qualification
Execution requires a new explicit device grant.
```

Read [MASTER-PLAN.md](MASTER-PLAN.md) for architecture and hard rules; then only the applicable packet in [EXECUTION-PACKETS.md](EXECUTION-PACKETS.md). [AUTHORITY-INDEX.md](AUTHORITY-INDEX.md) resolves authority IDs and immutable source links. [CONTRACT-DETAILS.md](CONTRACT-DETAILS.md) supplies exact cell matrices, commands, counters, and design blockers. [P2-CLOSURE.json](P2-CLOSURE.json) is the machine-readable closure checklist, currently incomplete.

Do not rerun R7-04, B-2, repair-validation, historical failures, or any `stall-obs-01` by default. Old “R7 NOT STARTED”, “B-2 BLOCKED”, “7549e36 installed”, and “R7-04 pending” statements must not regress current state. The R7 frozen order after 04 is **05 → 01 → 02 → 03 → 06 → 07 → 08 → 09 → 11 → 10 → P1 → P2**. R7-12/13/14 belong to later R8/R9, not this R7 batch.

Hard rules: never touch `com.termux.x11` or `:1`; no HDMI changes; never overwrite evidence, silent-retry, weaken judges, extend the 2000 ms timeout, or confuse source/CI/install/cell/gate PASS. No permission carries across an unspecified action boundary. R8/R9/R10 require a reviewed lifecycle harness/judge; they are not ready-made commands. The first architecture escalation is **NEXT-014**, resolving R8 event ordering, capacity units, and missing observability before implementation.

Minimal path: remaining R7 → R8 → R9 → R10 → P2 runtime closure → bounded desktop/performance evidence → required production lifecycle corrections and affected requalification → conditional Gate H → Gate W → V1-Core freeze. Performance and desktop evidence must bind the final artifact or have an approved carry-forward proof.

**Deferred After V1-Core:** V1-UWQHD (including dedicated 3440×1440@60 and 90/120 Hz), Full Global GPU, general mask/transform/bilinear/repeat/componentAlpha/two-pass XRender expansion. Neither blocks V1-Core.
