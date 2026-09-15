# Gate A P2 R1/R2 requalification on 8479997 — 2026-09-14

Artifact `8479997` / `1.03.01-8479997-14.09.26` / SHA256
`0a9d91f6fb26ee445935d5243f0b80b3f7e0c76574fdbebcc02f0d92f20323a2` /
Build ID `b072c9d2ff12f0a92258086a609b22744359654a` MATCH on-device.
CI run 34791993198. Production Gate A remains **BLOCKED**.
Stable `:1` PID **16085** untouched. HDMI observe-only. `--display 0` only.
T2 6/6 was **not** rerun on this APK (user: no new crash → do not repeat).

```
R0 INSTALL PASS
R1 OFF oracle/stress PASS (unset and PROTO=0)
R2 imported-AHB rejection PASS (modifier 1255 ×2, GATEA_EVENT=0)
R3 FAIL x-ready-timeout after GATEA_DRAIN (see GATE-A-P2-R3-RUNTIME-20260914.md)
PAUSED 2026-09-14 12:17 CST
```

## R1

`NO_X3_RESIDUE`, Stable 16085. Unset X PID **26155**; PROTO=0 X PID **27458**.

| cell | oracle | x100 | mixed100 | x1000 | GATEA_EVENT | X |
|---|---|---|---|---|---|---|
| unset | 1514 fail=0 maxΔ=0 Xnz=0 | 100/100 | 100/100 | 1000/1000 | 0 | 26155 ALIVE then torn down |
| PROTO=0 | same | 100/100 | 100/100 | 1000/1000 | 0 | 27458 ALIVE then torn down |

Historical `15caa00` PID 31807 SIGSEGV remains OBSERVED / NON-REPRODUCED.
Historical `6c7ee6f` PID 21977 JIT SIGSEGV remains OBSERVED / NON-REPRODUCED
on the later T2 rerun of that older APK.

Evidence: `r1-unset-oracle/`, `r1-proto0-oracle/`.

## R2

PROTO=1 TELEMETRY=1 DEBUG=1. X PID **28794** ALIVE_8S. Both cells exact
`got0=00804000` maxΔ=0. Server `DRI3: imported AHardwareBuffer, modifier
1255, 8x8 stride 64` ×2 (logcat duplicated → 4 lines; assert `n>=2`).
`GATEA_EVENT=0`. `NO_X3_RESIDUE`. Also observed `GATEA_DRAIN controls=1`
on HANDLE type=6 (control drain, not REGISTER).

`ADMIT_REJECT` still does not exist on this ABI. Authorized proof is the
1255 import log + software exact pixels + zero Gate A events, same as
`dd81ac0` / `98b0011` / `6c7ee6f`.

Evidence: `r2-imported-reject/`.
