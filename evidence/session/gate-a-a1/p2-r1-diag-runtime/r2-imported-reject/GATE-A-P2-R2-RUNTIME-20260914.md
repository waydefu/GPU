# Gate A P2 R2 — imported AHB rejection (dd81ac0) 2026-09-14

Artifact `dd81ac0` / `1.03.01-dd81ac0-13.09.26` / CI 34781139248.
Production Gate A remains **BLOCKED**. Stable `:1` PID **16085** untouched. HDMI observe-only.

```
R2 PASS
PROTO=1 TELEMETRY=1 TERMUX_X11_DEBUG=1
X PID 6378
both imported cells exact RGB maxΔ=0
DRI3 imported AHardwareBuffer modifier 1255 ×2
GATEA_EVENT=0 (no REGISTER/READY/lease/publish)
NO_X3_RESIDUE
```

## Why this is R2 without `ADMIT_REJECT`

`LORIE_GATEA_EVENT` on `dd81ac0` has no `ADMIT_REJECT` (see `lorie.h` enum). Adding it would be a new commit and would invalidate this APK. Proof on this artifact:

1. Real DRI3 `PixmapFromBuffers` modifier **1255** (`AHARDWAREBUFFER_SOCKET_FD`), not raw-FD 1274/LINEAR and not `dst-argb`.
2. Server log `DRI3: imported AHardwareBuffer, modifier 1255, 8x8 stride 64` twice, PID **6378**.
3. Direct admission would otherwise be live: process environ `TERMUX_X11_GATEA_PROTO=1` and `TERMUX_X11_GATEA_TELEMETRY=1`.
4. `gateADirectTryPrepare` refuses `sp->imported || dp->imported` before `gateAEnsureReady` / REGISTER.
5. `GATEA_EVENT` count **0** for the whole session until teardown snapshot.
6. Software Over pixels exact (fail=0, maxΔ=0, Xnz n/a on solid 8×8).

## Cells

| cell | source | dest | import | pixels |
|---|---|---|---|---|
| 1 | BGRA AHB format=5 | server-owned RGBX depth 24 | modifier 1255 depth 32 | PASS 64/64 maxΔ=0 got0=`00804000` |
| 2 | server-owned BGRA depth 32 | RGBX AHB format=2 | modifier 1255 depth 24 | PASS 64/64 maxΔ=0 got0=`00804000` |

Premul src `80800000` Over dest `00008000` → ref `00804000`.

Fixture output: `r2-fixture-appprocess.out`.

## How the client had to run

Termux/PRoot `AHardwareBuffer_allocate` is a trampoline; `run-as` is `runas_app` and aborts `gralloc-mapper is missing`. The X server is Termux uid **10365** + `untrusted_app_27` via `app_process`, which has gralloc.

R2 client is therefore the same class of process:

- dex `R2AhbHelp` + `libr2ahb.so` (`-DR2_JNI`)
- `LD_LIBRARY_PATH` = xcb-only helper `libs/` (never Termux `libandroid.so`)
- `/system/bin/app_process -Xnoimage-dex2oat … R2AhbHelp`

Helper path: `/data/data/com.termux/files/home/r2-ahb-helper/`
Source: `patches/p_r2_imported_ahb.c`

## Session

- serial `10.193.235.219:35301` myron / 25102PCBEG
- screen Awake, `isKeyguardShowing=false`, built-in display ON; HDMI ON observed, `--display 0` only
- Experimental activity COLD start display 0; X cmdline `termux-x11gpu com.waydefu.x11gpu :3` PID **6378** 8s alive then workload
- holder `p_b3a_hold` PID 7457
- tester SIGABRT during env discovery (`python3` 8398, `p_r2_imported_a` 17227) is **not** X; X has `NONE_FOR_X3`
- teardown: holder SIGTERM, X SIGTERM, `am force-stop com.waydefu.x11gpu`, `NO_X3_RESIDUE`, Stable **16085**

## Not claimed

- Production Gate A PASS
- `ADMIT_REJECT` telemetry event
- R3 direct admit / publish
- historical `15caa00` PID 31807 root-cause
