# Gate A P2 R7 — 2026-09-17 `8545b26` R7-10 dedicated runner **QUALIFIED**; repair **NOT INSTALLED**; historical FAIL frozen; R7 **IN PROGRESS**

```
STATUS: a07d66c INSTALLED (historical R7-10 FAIL frozen)
        R7-10 RCA PROVEN
        repair 8545b26 ARTIFACT QUALIFIED
        repair APK NOT INSTALLED
        8545b26 R7-10 runner R7_10_8545B26_RUNNER_QUALIFIED
        8545b26 R7-10 device NOT RUN
        R7-05 PASS frozen
        R7-01 PASS frozen
        R7-02 PASS frozen
        R7-03 PASS frozen
        R7-06 PASS frozen
        R7-07 PASS frozen
        R7-08 PASS frozen
        R7-09 PASS frozen
        R7-11 PASS frozen
        R7 IN PROGRESS / still 10/13
        next is separate install+one R7-10 device cell on 8545b26
        do not retry runtime-a07d66c/r7-10
        do not start R7-P1 / R7-P2
        do not install from this packet
Stable :1: PID 20146 UNTOUCHED
Production Gate A: BLOCKED
```

Tooling packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/r7-10-8545b26-runner-qualification-20260917/`

Dedicated runner `run-r7-10-8545b26.sh` SHA256 `690a865d…54cd` size 22480.
Classifier `classify_r7_10_hup_containment.py` SHA256 `ed73a314…05d7`.
Generic one-cell runner unmodified SHA `36d66f17…8ded` (still a07d66c-bound).
Frozen judge unmodified SHA `fba3c10f…cc17` 16/16.
`runtime-8545b26/r7-10/` still ABSENT.
Historical `runtime-a07d66c/r7-10/` intact.

RCA packet remains:
`evidence/session/gate-a-a1/p2-r7-design/GATE-A-P2-R7-10-RCA-REPAIR-20260917.md`

Historical FAIL brief remains:
`HANDOFF-NEXT-AGENT-20260917-r7-10-a07d66c.md`

Historical RCA brief remains:
`HANDOFF-NEXT-AGENT-20260917-r7-10-rca.md`

## Next

**Separate** grant: install `8545b26` on experimental only, verify full
artifact binding, then **one** R7-10 `renderer-exit-after-consume` cell:

```
SERIAL=<live>
ROOT=.../runtime-8545b26
CELL_ID=r7-10
FAULT=renderer-exit-after-consume
FIXTURE=direct
WAIT_S=12
bash evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-10-8545b26.sh
```

Do **not** execute it from this packet.
Do **not** use `run-r7-one-cell-a07d66c.sh` for 8545b26.
Do **not** retry `runtime-a07d66c/r7-10`.
Do **not** start R7-P1 or R7-P2.
Do **not** retry R7-11 / R7-09 / R7-08 / R7-07 / R7-06 / R7-03 / R7-02 / R7-01 / R7-05 / R7-04 / B-2.
Production Gate A remains BLOCKED.
