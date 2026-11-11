# Gate A P2 R7 — 2026-09-17 `a07d66c` R7-11 dedicated serial-wrap runner **QUALIFIED**; R7-11 device **NOT RUN**; R7 **IN PROGRESS**

```
STATUS: a07d66c INSTALLED
        R7-05 PASS frozen
        R7-01 PASS frozen
        R7-02 PASS frozen
        R7-03 PASS frozen
        R7-06 PASS frozen
        R7-07 PASS frozen
        R7-08 PASS frozen
        R7-09 PASS / DEVICE-QUALIFIED / frozen
        R7-11 NOT RUN / UNBLOCKED
        R7-11 dedicated runner R7_11_A07D66C_RUNNER_QUALIFIED
        R7 IN PROGRESS / NOT YET PASS
        next frozen cell is R7-11 / serial-wrap device qualification
        do not execute R7-11 from this packet
Stable :1: PID 20146 UNTOUCHED
Production Gate A: BLOCKED
```

Tooling packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/r7-11-a07d66c-runner-qualification-20260917/`

Dedicated runner `run-r7-11-a07d66c.sh` SHA256 `74385947…c453` size 25716.
Classifier `classify_r7_11_serial_wrap.py` SHA256 `3a0af4ff…b107`.
Generic one-cell runner unmodified SHA `36d66f17…8ded` and still
`REVIEW_REQUIRED` / live REFUSE for r7-11.
Frozen judge unmodified SHA `fba3c10f…cc17` 16/16.
`runtime-a07d66c/r7-11/` still ABSENT.

## Next

Separately authorized **one** `a07d66c` R7-11 `serial-wrap` **device** cell
using the dedicated runner only:

```
SERIAL=<live>
ROOT=.../runtime-a07d66c
CELL_ID=r7-11
FAULT=serial-wrap
FIXTURE=direct
WAIT_S=12
bash evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-11-a07d66c.sh
```

Do **not** execute it from this packet.
Do **not** use `run-r7-one-cell-a07d66c.sh` for r7-11.
Do **not** retry R7-09 / R7-08 / R7-07 / R7-06 / R7-03 / R7-02 / R7-01 / R7-05 / R7-04 / B-2.
Production Gate A remains BLOCKED.
