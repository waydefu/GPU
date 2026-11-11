# Gate A P2 R7 — 2026-09-17 `8545b26` R7-10 **PASS / DEVICE-QUALIFIED**；歷史 a07d66c FAIL 凍結；R7 **IN PROGRESS 11/13**

```
STATUS: 8545b26 INSTALLED experimental only
        R7-10 8545b26 R7_10_8545B26_REQUALIFICATION_PASS
        historical a07d66c R7-10 VALID FAIL FROZEN
        R7 IN PROGRESS / 11/13
        next frozen cell is R7-P1 / present-hold-complete
        do not run R7-P1 from this packet
        do not retry runtime-a07d66c/r7-10
        do not retry runtime-8545b26/r7-10
Stable :1: PID 20146 UNTOUCHED
Production Gate A: BLOCKED
```

Device packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-8545b26/GATE-A-P2-R7-10-8545B26-20260917.md`

Cell: `runtime-8545b26/r7-10/` X **13115** last halt `x-hup/6`；reason4=0；classifier `EXPECTED_HUP`；judge `R7_PASS renderer-exit-after-consume`.

Install bind: `runtime-8545b26/r0/` APK SHA256 `92220845…377a` Build ID `50a4078b…7b0a`.

Historical BLOCKED preflight remains `runtime-8545b26/r7-10-preflight/`.

## Next

Separately authorized **one** R7-P1 / `present-hold-complete` cell.
Do **not** execute it from this packet.
Do **not** retry `runtime-8545b26/r7-10` or `runtime-a07d66c/r7-10`.
Do **not** start R7-P2 / R8. Production Gate A remains BLOCKED.
