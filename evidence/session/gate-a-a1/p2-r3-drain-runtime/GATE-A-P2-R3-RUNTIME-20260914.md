# Gate A P2 R3 FAIL — 8479997 drain-wait — 2026-09-14

Fresh Activity after R1 oracle/stress + R2 PASS on `8479997`.
PROTO=1 TELEMETRY=1. Stable PID **16085**. `NO_X3_RESIDUE`.
Do **not** silent-retry this cell on `8479997`.

## Runtime

| | |
|---|---|
| Activity | PID **27805** |
| X `:3` | PID **31408** died after fixture |
| Fixture | `FAIL GetImage` |
| GATEA_EVENT | 0 |

```text
12:11:38.037 pid=27805 GATEA_BIND version=1 nonce=…23937 generation=1 bound=1
12:11:45.063 pid=27805 GATEA_PEEK magic=1 bound=1 nonce=…23937 generation=1
12:11:45.063 pid=27805 GATEA_HANDLE type=1 id=6
12:11:45.063 pid=27805 tid=31188 GATEA_DRAIN imports=1 overflow=0
12:11:47.063 pid=31408 GATEA_FATAL_HALT what=x-ready-timeout reason=4
12:11:47.082 pid=27805 GATEA_FATAL_HALT what=r-hup reason=6
```

`type=1` is `LORIE_GATEA_MSG_REGISTER`. No `r-unbound-frame`, no
`r-import-enqueue`, no `r-ready-send`. Drain ran on a **different tid**
(31188) than the looper (27805).

## What this proves / does not prove

The 6c7ee6f cause (`shouldWait` dropped `wakeGateA` as spurious, so
`gateADrainPendingImports` never ran) is **falsified on this APK**.
Drain-wait works: REGISTER was queued and the GL thread logged
`GATEA_DRAIN imports=1`.

READY was still never published. X's 2s waiter saw neither READY nor
FAILED (`GATEA_EVENT=0`). Remaining unproven paths are inside
`gateAValidateImport` / send after drain (bound-tuple silent return,
EGL not current, EGL stall, or a failed send that did not take the
`r-ready-send` fatal). See
`HANDOFF-NEXT-AGENT-20260914.md` §6.

Do **not** retry R3 on `8479997`, `6c7ee6f`, or `98b0011`.
Production stays BLOCKED. Session paused 2026-09-14 12:17 CST.

Evidence: `r3-single-direct/`.
