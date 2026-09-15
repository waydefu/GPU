# Gate A P2 R1/R2 requalification on 88e3f17 — 2026-09-14

Artifact `88e3f17` / `1.03.01-88e3f17-14.09.26` / SHA256
`7e5540a247f0a0dd1c179fc818ba2f83abd2d970fb4961588ba6f071b19b8616` /
Build ID `e91c7683b3dd0ac61739f274a5eaeffaace1be12` MATCH on-device.
CI run 34822381586. Production Gate A remains **BLOCKED**.
Stable `:1` PID **16085** untouched. HDMI observe-only. `--display 0` only.
T2 6/6 was **not** rerun. Historical `8479997` cells were not overwritten.

```
R0 DEVICE PASS
R0 ARTIFACT INSTALL BINDING PASS
R1 OFF oracle/stress PASS (unset and PROTO=0)
R2 imported-AHB rejection PASS WITH INDIRECT REJECTION EVIDENCE
R3 FAIL (see GATE-A-P2-R3-RUNTIME-20260914.md)
STOP HERE — R4–R10 NOT RUN
```

## R1

`NO_X3_RESIDUE`, collector NONE, logcat size idle, Stable 16085.
Unset X PID **12959**; PROTO=0 X PID **19530**.

| cell | oracle | x100 | mixed100 | x1000 | GATEA_EVENT | X |
|---|---|---|---|---|---|---|
| unset | 1514 fail=0 maxΔ=0 Xnz=0 | 100/100 | 100/100 | 1000/1000 | 0 | 12959 ALIVE then torn down |
| PROTO=0 | same | 100/100 | 100/100 | 1000/1000 | 0 | 19530 ALIVE then torn down |

No fatal/SIGSEGV/SIGILL. Historical `15caa00` PID 31807 and `6c7ee6f` PID 21977 remain OBSERVED / not reproduced here.

Evidence: `r1-unset-oracle/`, `r1-proto0-oracle/`.

## R2

PROTO=1 TELEMETRY=1 DEBUG=1. X PID **26140** alive through fixture.
Both cells `exact_px=64 maxΔ=0 got0=00804000`. Server
`DRI3: imported AHardwareBuffer, modifier 1255, 8x8 stride 64` ×2.
X-side / renderer `GATEA_EVENT=0`. `NO_X3_RESIDUE`.

Proof remains **PASS WITH INDIRECT REJECTION EVIDENCE** (1255 import log +
software exact pixels + zero Gate A events). `ADMIT_REJECT` still does
not exist on this ABI.

Evidence: `r2-imported-reject/`.
