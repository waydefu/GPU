# Gate A P2 R7 — 2026-09-17 `a07d66c` R7-01 **BLOCKED** (no trusted R7-01 runner); R7-05 PASS remains; R7 **IN PROGRESS**

```
STATUS: R6 PASS on frozen 0f1e546 remains historical
        B-2 PASS on 7549e36 remains frozen
        fdfb1ce R7-04 PASS remains frozen
        historical fdfb1ce R7-05 VALID FAIL r-hup/6 remains frozen
        a07d66c R7-05 PASS remains frozen
        a07d66c R7-01 NOT RUN / BLOCKED (runner authority)
        R7 IN PROGRESS / NOT YET PASS
        next frozen cell is still R7-01 / src-ready-miss
        do not treat BLOCKED as FAIL
        do not start R7-01 until a reviewed a07d66c R7-01 runner exists
DEVICE HEAD: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82 INSTALLED
CI: 35171333149
APK: 1.03.01-a07d66c-17.09.26
Stable :1: PID 20146 UNTOUCHED
HDMI: UNTOUCHED observe-only
Production Gate A: BLOCKED
```

R7-01 BLOCKED packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-a07d66c/GATE-A-P2-R7-01-A07D66C-BLOCKED-20260917.md`

Preflight (not the legal cell dir):
`.../runtime-a07d66c/r7-01-blocked-preflight/`

Legal cell `.../runtime-a07d66c/r7-01/` is **ABSENT**. Keep it that way until a reviewed runner grant.

R7-05 PASS remains:
`.../runtime-a07d66c/GATE-A-P2-R7-05-A07D66C-REQUALIFICATION-01-20260917.md`

## Summary

1. Live pull of installed experimental APK MATCHES `a07d66c` SHA/signer/Build ID. No reinstall.
2. Stable 20146 unchanged. X3 absent. Frozen judge 16/16. Fixtures present.
3. Only a07d66c-aware runner is `run-r7-05-requal-a07d66c.sh` (SHA256 `46c24fc9…6473`), locked to `r7-05-requalification-01` / `post-draw-gl`. Dry-run REFUSE on R7-01.
4. fdfb1ce/7549e36 runners are wrong provenance. Copy+sed is forbidden.
5. Cell not started. BLOCKED ≠ FAIL.

## Next

Separately authorized **runner review + R7-01 implementation** (a07d66c-aware, `src-ready-miss`, destination `runtime-a07d66c/r7-01`), then a **new** single-cell grant.
Do **not** execute R7-01 from this packet.
Do **not** widen the R7-05 runner without that review.
Do **not** retry R7-05 / R7-04 / B-2.
Do **not** start R7-02+.
Production Gate A remains BLOCKED.
