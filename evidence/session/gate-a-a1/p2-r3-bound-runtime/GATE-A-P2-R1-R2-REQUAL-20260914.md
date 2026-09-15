# Gate A P2 R1/R2 requalification on 98b0011 — 2026-09-14

Artifact `98b0011` / `1.03.01-98b0011-13.09.26` / SHA256
`e547eadbbd33f8f2fdeb6efa650094b9f0103177721068392dbd353b4a211760` /
Build ID `520533123eec488db553e2610b32e263968266cf` MATCH on-device.
CI run 34786907985. Production Gate A remains **BLOCKED**.
Stable `:1` PID **16085** untouched. HDMI observe-only. `--display 0` only.

```
R0 INSTALL PASS
R1 T2 6/6 PASS (unset + PROTO=0 ×3)
R1 OFF oracle/stress PASS (unset and PROTO=0)
R2 imported-AHB rejection PASS (modifier 1255 ×2, GATEA_EVENT=0)
R3 FAIL x-ready-timeout (see GATE-A-P2-R3-RUNTIME-20260914.md)
```

## R1

T2 alive 8 s, `NO_X3_RESIDUE`, Stable 16085: A1/A2/A3 unset PIDs 17957 /
19634 / 20969; B1/B2/B3 PROTO=0 PIDs 18914 / 20371 / 21541.

| cell | oracle | x100 | mixed100 | x1000 | GATEA_EVENT | X |
|---|---|---|---|---|---|---|
| unset | 1514 fail=0 maxΔ=0 Xnz=0 | 100/100 | 100/100 | 1000/1000 | 0 | 23718 ALIVE |
| PROTO=0 | same | 100/100 | 100/100 | 1000/1000 | 0 | 24966 ALIVE |

Historical `15caa00` PID 31807 SIGSEGV remains OBSERVED / NON-REPRODUCED.

## R2

PROTO=1 TELEMETRY=1 DEBUG=1. X PID **30247**. Both cells exact
`got0=00804000` maxΔ=0. Server `DRI3: imported AHardwareBuffer, modifier
1255, 8x8 stride 64` ×2. `GATEA_EVENT=0`. `NO_X3_RESIDUE`.

`ADMIT_REJECT` still does not exist on this ABI. Authorized proof is the
1255 import log + software exact pixels + zero Gate A events, same as
`dd81ac0`.
