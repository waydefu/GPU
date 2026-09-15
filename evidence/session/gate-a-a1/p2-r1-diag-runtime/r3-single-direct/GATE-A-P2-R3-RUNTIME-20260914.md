# Gate A P2 R3 — FAIL x-ready-timeout (dd81ac0) 2026-09-14

```
R3 FAIL
what=x-ready-timeout reason=4 (LORIE_GATEA_FAIL_TIMEOUT)
X PID 23684  thread 23868
GATEA_EVENT=0
Production Gate A BLOCKED
```

Fresh PROTO=1 TELEMETRY=1 session. Startup 8s ALIVE. Holder READY. One 8×8 Over ARGB→XRGB (server-owned, not imported). Composite entered EXA; both pixmaps converted REGULAR→AHB (src format 5, dst format 2). ~2 s later X fail-stopped. Client GetImage saw a dead server. Stable `:1` PID **16085** unchanged. HDMI untouched. `NO_X3_RESIDUE`.

## Observation

```
09-14 06:15:23.438  … R3 S2_AHB … dest format=2
09-14 06:15:25.439  23684 23868 F gatea-a1: GATEA_FATAL_HALT what=x-ready-timeout reason=4
```

No `Uctx`/`Uraw` (not SIGSEGV). No `GATEA_EVENT`. No renderer `REGISTER_READY`.

`gateAEnsureReady` sent REGISTER (else `x-register-send`) then waited 2 s for the renderer waiter (`InitOutput.c:2370-2395`).

## Root cause (proven, static + this run)

X is `f8-x11gpu` `app_process` and **has** `TERMUX_X11_GATEA_PROTO=1`.

The Activity (`com.waydefu.x11gpu`, `am start --display 0`) **does not inherit that environ**. `lorieGateAProtoEnabled()` in `activity.cpp` / `renderer.cpp` is therefore false.

Those getenv gates skip:

1. `gateABindFromState` on `EVENT_SHARED_SERVER_STATE`
2. magic-peek `gateAHandleFrame` for X→Activity REGISTER
3. GL-thread `gateADrainPendingImports`

REGISTER is ignored (or consumed as a bogus `lorieEvent`). The renderer never ACKs READY. X halts. R2 did not hit this path: imported rejection returns before `gateAEnsureReady`.

## Repair (authorized, next commit)

Activity/renderer must demux/bind/drain from the **shared bound tuple** (nonce+generation in the mapped state), not from Activity getenv. X keeps exact `"1"` getenv. That is a new commit → CI → requalify R1+R2+R3 on a new artifact. Do not keep running R3 on `dd81ac0`.

## Evidence

- `r3-fixture.out` — `FAIL GetImage`
- `x3-launcher.raw.log` — S0/S1/S2 then silence
- `logcat-dump-from-composite.txt` — `GATEA_FATAL_HALT what=x-ready-timeout`
- Stable 16085
