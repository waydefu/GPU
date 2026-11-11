# Gate A P2 R7 — 2026-09-18 abb27a65 R7-P1 **INVALID / FROZEN**；R7 **IN PROGRESS 11/13**

```
STATUS: abb27a65 INSTALLED experimental only (CI 35253641841)
        R7-10 8545b26 PASS / FROZEN
        historical 8545b26 R7-P1 INVALID / FROZEN
        abb27a65 R7-P1 R7_P1_ABB27A65_QUALIFICATION_INVALID / FROZEN
        classifier PEER_DIED / runner_invalid=YES
        R7-P2 NOT RUN
        R7 IN PROGRESS / 11/13
        do not retry runtime-abb27a65/r7-p1
        do not retry runtime-8545b26/r7-p1
        do not run R7-P2
        do not silent-patch liveness and rerun
Stable :1: PID 20146 UNTOUCHED
Production Gate A: BLOCKED
```

Frozen abb27a65 cell: `runtime-abb27a65/r7-p1/` X **19686** classifier `PEER_DIED`.

Packet: `evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-abb27a65/GATE-A-P2-R7-P1-ABB27A65-20260918.md`

Historical INVALID remains: `runtime-8545b26/r7-p1/` X **14331** `NO_PRESENT_CALLBACK`.

## Next

Do **not** retry `runtime-abb27a65/r7-p1`.
Do **not** retry `runtime-8545b26/r7-p1`.
Do **not** execute R7-P2.
Do **not** silent-patch the host `/proc/$ACT_PID` liveness probe and rerun.
Do **not** start R8. Production Gate A remains BLOCKED.
Any later repair needs a new explicit grant and a fresh evidence path.
