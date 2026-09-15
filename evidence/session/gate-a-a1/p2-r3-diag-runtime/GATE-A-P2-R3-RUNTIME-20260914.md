# Gate A P2 R3 FAIL — 6c7ee6f peek-diag — 2026-09-14

Fresh COLD Activity after T2 rerun 6/6 + R1 oracle + R2 PASS on
`6c7ee6f`. PROTO=1 TELEMETRY=1. Stable PID **16085**. `NO_X3_RESIDUE`.

## Runtime

| | |
|---|---|
| Activity | PID **640** COLD |
| X `:3` | PID **8089** died after fixture |
| Fixture | `FAIL GetImage` |
| GATEA_EVENT | 0 |

```text
08:01:27.637 pid=640 GATEA_BIND version=1 nonce=…66948 generation=1 bound=1
08:01:33.892 pid=640 GATEA_PEEK magic=1 bound=1 nonce=…66948 generation=1
08:01:33.892 pid=640 GATEA_HANDLE type=1 id=6
08:01:35.892 pid=8089 GATEA_FATAL_HALT what=x-ready-timeout reason=4
08:01:35.916 pid=640 GATEA_FATAL_HALT what=r-hup reason=6
```

`type=1` is `LORIE_GATEA_MSG_REGISTER`. No `r-unbound-frame`, no
`r-bad-register`, no `r-import-enqueue`. Peek-true + unbound is **falsified**.

## Proven remaining cause

`gateAHandleRegister` enqueued and `lorieGateAWakeRenderer` →
`Renderer::wakeGateA` (`pthread_cond_signal`). `Renderer::shouldWait`
then classifies a wake with no draw/buffer/gpuCopy as **spurious** and
returns true, so `threadLoop` never reaches `gateADrainPendingImports`.
READY is never sent. X times out at 2s. `GATEA_EVENT=0` matches: the GL
thread never ran the READY/FAILED send path.

`lorieGateAImportBusy` cannot be the wait predicate: it is true while
READY entries remain, which would spin the GL thread after the first
success. Pending-import + pending-control + overflow only.

Do **not** retry R3 on `6c7ee6f`. Production stays BLOCKED.

Evidence: `r3-single-direct/`.
