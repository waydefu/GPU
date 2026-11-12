# Gate A P2 R7 — 2026-09-17 `8545b26` R7-P1 **RUNNER QUALIFIED**；裝置 cell **NOT RUN / UNBLOCKED**；R7 **IN PROGRESS 11/13**

```
STATUS: 8545b26 INSTALLED experimental only
        R7-10 8545b26 PASS / FROZEN
        R7-P1 R7_P1_8545B26_RUNNER_QUALIFIED
        R7-P1 device NOT RUN / UNBLOCKED
        R7 IN PROGRESS / 11/13
        next frozen cell is one runtime-8545b26/r7-p1 present-hold-complete
        do not run R7-P1 from this packet
        do not run R7-P2
        do not retry runtime-a07d66c/r7-10
        do not retry runtime-8545b26/r7-10
Stable :1: PID 20146 UNTOUCHED
Production Gate A: BLOCKED
```

Tooling packet:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/r7-p1-8545b26-runner-qualification-20260917/`

Dedicated runner: `run-r7-p1-8545b26.sh`
SHA256 `46c2289dcdddd518c2e4ecb99095e3991c640fa11e92149b83d8d79f20a16ba7`

Classifier: `scripts/classify_r7_p1_present_hold.py`
SHA256 `07de408bc0b316ce0ed7d0e60fd719b897319cf64b2b38c41d2ca1de7be33908`

Generic a07d66c runner still **REVIEW_REQUIRED** for r7-p1 (not lifted).
Frozen judge 16/16 SHA `fba3c10f…cc17` unmodified.
Present fixture ELF SHA `fec8f46d…ba86` size 72536.

R7-10 device packet remains:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-8545b26/GATE-A-P2-R7-10-8545B26-20260917.md`

## Next

Separately authorized **one** `runtime-8545b26/r7-p1` / `present-hold-complete`
using `run-r7-p1-8545b26.sh`.
Do **not** execute it from this packet.
Do **not** execute R7-P2.
Do **not** retry `runtime-8545b26/r7-10` or `runtime-a07d66c/r7-10`.
Do **not** use `run-r7-one-cell-a07d66c.sh` for 8545b26.
Do **not** start R8. Production Gate A remains BLOCKED.
