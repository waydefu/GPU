# Gate A P2 R6 bounded client cell — 37d8393 — 2026-09-15

Exactly one authorized R6. No R7/R8. R5 cells not overwritten.
Stable PID **16085** untouched. Production Gate A remains **BLOCKED**.

## Binding

Installed `1.03.01-37d8393-15.09.26` CI **34918397208**.
serial `10.12.7.144:34863` live-fetched.
Fixture `p_r6_cross_op` SHA256
`ca02bc27f2d7b6ae87823e774e08fa6c13925d7685087d6c4af7c378264f55ab`
source `patches/p_r6_cross_op.c` SHA256
`c06f414e92b599ad27fc37024ee45a470faade1d32eaad8fdb5fb458b276a46f`.

## Runtime

| | |
|---|---|
| Command | `SERIAL=10.12.7.144:34863 CELL=…/runtime-37d8393/r6-cross-op bash run-r6.sh` |
| Script exit | **0** `R6_BOUNDED_CLIENT_PASS` |
| Activity | COLD Display0 PID **24679** `GATEA_BIND` nonce=`13262347556379483958` |
| X `:3` | PID **11495** ALIVE then torn down |
| Watchdog | NONE |
| A | CopyArea then Over Composite: exact 64 px `got0=00804000` |
| B | Composite flushed, CopyArea on second connection: exact 64 px `got0=00804000` |
| Fixture | `RESULT p_r6_cross_op CLIENT_OK pixels exact; X request-arrived events NOT produced` |
| Fatal | none |
| Teardown | `STABLE 16085` `NO_X3_RESIDUE` |

GATEA follow (48 lines): publish=consume=lookup=draw=fence=completed=success=ack=lease=repair=relock_dst=**2**. firstFailed=0.

Client B timing (not X proof): copy_send−comp_send=8437 ns;
copy_reply−comp_reply=521094 ns.

## Classification

| Claim | Label |
|---|---|
| Sequential COPY then direct Over, exact pixels | **PROVEN** |
| Two-connection overlap, exact pixels, X alive | **PROVEN** |
| Direct N=2 counters match, no fatal | **PROVEN** |
| Request-arrived vs callback timestamps | **NOT PRODUCED** (no such GATEA event; fixture states this) |
| Present OOM/scrap/early-ACK then direct reject | **NOT RUN** (fixture does not implement) |
| Design-complete R6 (`GATE-A-P2-RUNTIME-QUALIFICATION-DESIGN-20260913.md`) | **NOT CLAIMED** in this cell. Architecture written 2026-09-15: `../../p2-r6-design/GATE-A-P2-R6-DESIGN-20260915.md` (implementation not authorized) |
| R7 / Production Gate A | **NOT STARTED** / **BLOCKED** |

Evidence: `r6-cross-op/`.
