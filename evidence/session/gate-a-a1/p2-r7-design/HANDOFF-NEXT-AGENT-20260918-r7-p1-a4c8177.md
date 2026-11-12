# Gate A P2 R7 — 2026-09-18 a4c8177 R7-P1 **INVALID / FROZEN**；R7 **IN PROGRESS 11/13**

```
STATUS: a4c8177 INSTALLED experimental only (CI 35295094951)
        parent abb27a65
        dual RCA PROVEN
        hold+liveness support HOST_QUALIFIED
        a4c8177 R7-P1 R7_P1_A4C8177_QUALIFICATION_INVALID / FROZEN
        classifier PEER_DIED / runner_invalid=YES
        activity_pre_cleanup=ABSENT after X fatal
        R7-P2 NOT RUN
        R7 IN PROGRESS / 11/13
        do not retry runtime-a4c8177/r7-p1
        do not retry runtime-abb27a65/r7-p1
        do not retry runtime-8545b26/r7-p1
        do not run R7-P2
        do not silent-patch pre-cleanup liveness and rerun
Stable :1: PID 20146 UNTOUCHED
Production Gate A: BLOCKED
```

Frozen a4c8177 cell: `runtime-a4c8177/r7-p1/` X **24284** classifier `PEER_DIED`.
classify SHA256 `246832f2733d0c27bcdcf716615fdaf4431680b6320542893a69c19e8bcc84f6`.
primary-verdict SHA256 `d528a6a9da6ea5e2e17f195afb563d107899a8a092b3c22681e0c2fc894a1b8f`.

Packet: `evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-a4c8177/GATE-A-P2-R7-P1-A4C8177-20260918.md`

RCA: `evidence/session/gate-a-a1/p2-r7-design/GATE-A-P2-R7-P1-DUAL-RCA-20260918.md`

Historical frozen cells remain immutable:
- `runtime-abb27a65/r7-p1/` classify SHA256 `a135c79c5599d00424dbbdf46c0e2edb703987f54653898dc226ee523c58f19b`
- `runtime-8545b26/r7-p1/`
- `run-r7-p1-abb27a65.sh` SHA256 `95900a2d…7098`

## Next

Do **not** retry `runtime-a4c8177/r7-p1`.
Do **not** retry `runtime-abb27a65/r7-p1`.
Do **not** retry `runtime-8545b26/r7-p1`.
Do **not** execute R7-P2.
Do **not** silent-patch Activity pre-cleanup vs during-wait and rerun.
Do **not** start R8. Production Gate A remains BLOCKED.
Any later repair needs a new explicit grant and a fresh evidence path.
