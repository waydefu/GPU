# Gate A P2 R3 PASS — d9b7f60 xpump — 2026-09-15

Exactly one fresh `p_r3_single_direct` after R0/R1 on `d9b7f60`.
PROTO=1 TELEMETRY=1. COLD Activity displayId=0. Fresh X `:3`.
Stable PID **16085**. Teardown `NO_X3_RESIDUE`.
Do **not** silent-retry this cell. Historical stop at this report was
before R4; **2026-09-15 R2+R4 PASS** superseded that stop. Current stop
is before R5. Production Gate A remains **BLOCKED**.

## Runtime

| | |
|---|---|
| Activity / renderer | PID **20945** (GL drain tid **7885**) |
| X `:3` | PID **8034** alive after fixture, then torn down |
| Fixture | `PASS pixels exact_px=64 maxΔ=0 got0=00804000` `FIXTURE_EXIT=0` |
| GATEA_EVENT | 30 unique (file lists 60: follow+blob duplicate) |
| GATEA_BIND | version=1 bound=1 generation=1 |

```text
01:48:02.580 pid=20945 GATEA_BIND bound=1
01:48:10.345 pid=20945 GATEA_PEEK magic=1 bound=1
01:48:10.346 pid=20945 GATEA_HANDLE type=1 id=6
01:48:10.346 tid=7885 GATEA_DRAIN imports=1
01:48:10.346 tid=7885 VALIDATE READY_SEND_* + VALIDATE_TERMINAL_READY result=1
01:48:10.346 pid=20945 role=2 event=1 REGISTER_READY src=6
01:48:10.346 pid=8034  role=1 event=1 REGISTER_READY src=6   ← X consumed
… id=7 same pattern …
lease/publish/consume/lookup/draw/fence/completed/success/relock/repair/ack
UNREGISTER type=4 id=6 and id=7
no x-ready-timeout, no GATEA_FATAL_HALT
```

## What this proves / does not prove

Versus frozen `88e3f17` R3 FAIL: X main-thread self-wait is **falsified on this APK**.
The X waiter consumed READY (`role=1 event=1`) instead of sleeping into
`x-ready-timeout`. Pixel oracle matched expect `00804000`.

Does **not** prove Production ownership/lifecycle completeness. Does **not**
clear PID **21639**. Does **not** authorize R5–R10, timeout changes, or a PR.

Harness leftover: logcat pid 8008 still alive after TERM then gone. Not a
product result.

Evidence: `r3-single-direct/`.
