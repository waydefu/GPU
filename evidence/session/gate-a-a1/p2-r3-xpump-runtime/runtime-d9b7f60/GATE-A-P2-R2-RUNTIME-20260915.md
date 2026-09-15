# Gate A P2 R2 PASS — d9b7f60 imported-AHB rejection — 2026-09-15

Exactly one fresh `p_r2_imported_ahb` on installed `d9b7f60` after R3 PASS.
PROTO=1 TELEMETRY=1 **TERMUX_X11_DEBUG=1**. COLD Activity. Fresh X `:3`.
Stable PID **16085**. Teardown `NO_X3_RESIDUE`.
Do **not** silent-retry this cell. Do **not** start R5–R10 without a new decision.
Production Gate A remains **BLOCKED**.

This is the same deny-gate contract as historical `dd81ac0` / `88e3f17` R2:
no `ADMIT_REJECT` enum on this ABI. Proof is GATEA_EVENT=0 + real DRI3
modifier **1255** ×2 unique + exact pixels.

## Runtime

| | |
|---|---|
| Command | `SERIAL=10.193.235.219:38663 CELL=…/runtime-d9b7f60/r2-imported-reject bash run-r2.sh` |
| Exit | **0** `R2_IMPORTED_REJECT_PASS` |
| Activity | PID **8115** COLD `--display 0` |
| X `:3` | PID **28042** alive after fixture, then torn down |
| Fixture | `RESULT p_r2_imported_ahb PASS both-cells exact maxΔ=0` `FIXTURE_EXIT=0` |
| GATEA_EVENT | **0** (follow + blob; `NONE`) |
| DRI3 import | unique **2** on pid 28042 (`modifier 1255, 8x8 stride 64`); file lists 4 = follow+blob duplicate |
| Fatal | NONE |

```text
CELL1 imported-BGRA-src + server-RGBX-dst
  AHB format=5  IMPORT pixmap=0x400000 depth=32 modifier=1255
  PASS exact_px=64 maxΔ=0 got0=00804000
CELL2 server-BGRA-src + imported-RGBX-dst
  AHB format=2  IMPORT pixmap=0x400006 depth=24 modifier=1255
  PASS exact_px=64 maxΔ=0 got0=00804000
```

Premul src `80800000` Over dest `00008000` → ref `00804000`.

Client: `/system/bin/app_process` `R2AhbHelp` + helper
`/data/data/com.termux/files/home/r2-ahb-helper/` (not PRoot
`AHardwareBuffer_allocate`).

## What this proves / does not prove

Imported AHB pixmaps take the existing software Over path. Direct
REGISTER/READY/lease/publish did not fire (`GATEA_EVENT=0`) while PROTO=1
was live. Modifier 1255 is `AHARDWAREBUFFER_SOCKET_FD`, not raw-FD 1274.

Does **not** emit `ADMIT_REJECT`. Does **not** prove Production Gate A.
Does **not** authorize R5.

Evidence: `r2-imported-reject/`.
