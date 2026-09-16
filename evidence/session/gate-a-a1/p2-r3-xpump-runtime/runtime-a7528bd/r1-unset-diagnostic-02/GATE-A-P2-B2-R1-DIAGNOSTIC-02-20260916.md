# Gate A P2 B-2 R1-unset diagnostic-02 — 2026-09-16

```
STATUS: RCA IDENTIFIED
CANDIDATE: a7528bd25b89d0408bc15002e10bccefaeef3028
APK: 1.03.01-a7528bd-15.09.26  CI 35007764673
X PID: 10903  DISPLAY :3  thread 11167
MODE: TEST/PROTO/TELEMETRY/R6-OOM unset (proven /proc/environ)
STRESS: ok=997 fail=3 n=1000 alive=1  exit=1
B2_DIAG_FAIL: 3 × PIXEL_RGB_MISMATCH
EXA GPU composite wait timeout: 3
Gcomp Prepare/Done: 1000/1000
CORRELATION: PROVEN SAME OPERATION
HYPOTHESIS: SUPPORTED
AUTHORITATIVE B-2 FAIL UNCHANGED: runtime-a7528bd/r1-unset-oracle/
```

This is **not** B-2 requalification and **not** R7. Do not start R7.

## Preflight

- R7 HEAD `a7528bd25b89d0408bc15002e10bccefaeef3028`
- Frozen R6 HEAD `0f1e54699d0b11a781f2c044fbc77505f8a53bd8` (untouched)
- Diagnostic ELF SHA256 `3e79b5cf875f5d7d05a25634983a44d9acfe67dfb885bf11f19b2cdb70e43c56`
- Opaque preserved `d020d453…3504f9`
- Cell was **absent** before this run
- `r1-unset-oracle/` still `ok=999 fail=1`
- `r1-unset-diagnostic-01/` still `ok=1000 fail=0`
- Installed `1.03.01-a7528bd-15.09.26` lastUpdateTime `2026-09-16 02:40:28`
- Screen Awake, keyguard false
- No APK rebuild/install; harness not modified

## Stable

| | PID | cmdline | package |
|---|---|---|---|
| before | **17922** | `termux-x11 com.termux.x11 :1 -legacy-drawing` | `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03 |
| after | **17922** | same | same |

Contamination: **none**. HDMI untouched.

## Experimental / env

- Pre: no `:3`
- X PID **10903** `termux-x11gpu com.waydefu.x11gpu :3`
- `/proc/10903/environ`: **NO_GATEA_ENV**
- Holder `p_b3a_hold` session keep-alive only
- Post: `NO_X3_RESIDUE`

## Exact command

```
.../p2-r1-diag-runtime/fixtures/p_b2_stress 1000
```

- DISPLAY=:3
- start `2026-09-16T10:04:56+08:00` end `2026-09-16T10:05:19+08:00`
- stdout: three `B2_DIAG_FAIL` lines + `STRESS mixed=0 ok=997 fail=3 n=1000 alive=1`
- stderr: empty
- exit code: **1**
- One-run rule honored; do not overwrite this cell

## Failure detail (all three)

Client iteration is 0-based (`for i = 0; i < n`). Probe `enter` is 1-based Composite index on this X thread (`enter = i+1`). First stress Composite is `Probe ENTER enter=1` + `Gcomp RECT 1x1` at `10:04:56.824`.

| field | fail A | fail B | fail C |
|---|---|---|---|
| iteration | 201 | 483 | 936 |
| Probe ENTER/RETURN | 202 | 484 | 937 |
| GPU serial (timeout) | 206 | 488 | 941 |
| stage | PIXEL_RGB_MISMATCH | PIXEL_RGB_MISMATCH | PIXEL_RGB_MISMATCH |
| w×h | 17×17 | 17×17 | 1×1 |
| alpha | 127 | 254 | 127 |
| mixed | 0 | 0 | 0 |
| sc / dc | `0x00ff00` / `0xffffff` | `0xffffff` / `0x123456` | `0x00ff00` / `0xffffff` |
| src_px / dst_px | `0x7f007f00` / `0x00ffffff` | `0xfefefefe` / `0x00123456` | `0x7f007f00` / `0x00ffffff` |
| PutImage/Composite X error | NA / NA / NA | NA / NA / NA | NA / NA / NA |
| getimage_reply / err | 1 / NA | 1 / NA | 1 / NA |
| expected | `0x0080ff80` | `0x00fefefe` | `0x0080ff80` |
| got | `0x00ffffff` | `0x00123456` | `0x00ffffff` |
| rgb expected/got | `0x80ff80` / `0xffffff` | `0xfefefe` / `0x123456` | `0x80ff80` / `0xffffff` |
| x_expected / x_got | `0x00` / `0x00` | `0x00` / `0x00` | `0x00` / `0x00` |
| conn_err | 0 | 0 | 0 |
| sequence | 4036 | 9676 | 18736 |
| start_mono_ns | 39654300949664 | 39660973536536 | 39670539505022 |
| fail_mono_ns | 39656318271642 | 39662989499869 | 39672552266115 |
| fail−start | **2017.322 ms** | **2015.963 ms** | **2012.761 ms** |

In all three cases `got == dst_px` (uncomposited destination). RGB mismatch only; X-byte already 0. Not an X protocol error, not connection loss, not allocation failure.

## Server / renderer correlation

Same X thread `10903/11167` for Probe, RECT, timeout, Done, then dest PrepareAccess / GetImage.

| | RECT (schedule) | timeout + Gcomp Done | RECT→timeout | SF after |
|---|---|---|---|---|
| A | `10:05:00.124` 17×17 | `10:05:02.126` serial=206 scheduled=1 | **2002 ms** | `10:05:02.263` frame 176 **2167 ms** |
| B | `10:05:06.796` 17×17 | `10:05:08.797` serial=488 scheduled=1 | **2001 ms** | `10:05:08.937` frame 417 **2151 ms** |
| C | `10:05:16.362` 1×1 | `10:05:18.363` serial=941 scheduled=1 | **2001 ms** | `10:05:18.490` frame 778 **2138 ms** |

Session-start SF `10:04:56.839` frame 2 **1758 ms** did **not** produce a fail (same class as diagnostic-01).

Immediately after each timeout Done: `Probe RETURN enter=i+1`, then `Sprep` dest at the failing size (17×17 / 17×17 / 1×1), then next Composite of the next size in the recipe (32×32 / 32×32 / 2×2).

`Gcomp Prepare`/`Done` totals remain 1000/1000 because `lorieExaDoneComposite` logs `Gcomp Done` **even when wait returns FALSE** (`InitOutput.c` ~3550–3582).

Renderer process still received the **next** shared buffers after each timeout (alive). No `GATEA_EVENT`, no fatal, no SIGSEGV/SIGILL. SUMMARY `where=x-close-screen` all counters 0.

GPU blit serial is not equal to iteration (`serial = i+5` on these three); the **operation** bind is Probe `enter=i+1` plus matching RECT size plus dest GetImage, not a shared client-printed GPU serial.

## Correlation verdict

**PROVEN SAME OPERATION**

Unambiguous one-operation sequence, three times:

1. Client `one(i)` starts CLOCK_MONOTONIC.
2. Server `Probe ENTER enter=i+1` then `Gcomp RECT` of `sizes[i%6]`.
3. `lorieGpuCopyWait(lastSerial, 2000)` expires (~2001–2002 ms after RECT).
4. Log timeout; **still** `Gcomp Done` (source continues).
5. `Probe RETURN enter=i+1`; PrepareAccess dest; GetImage.
6. Client `PIXEL_RGB_MISMATCH` with `got == dst_px`, fail−start ≈ 2013–2017 ms.

## RCA verdict

**RCA IDENTIFIED**

Defect chain (source + this device cell):

`lorieExaDoneComposite` calls `lorieGpuCopyWait(serial, 2000)`. On timeout it logs `EXA GPU composite wait timeout` then still runs `lorieExaRepairDestXByteZero`, ack/release, and `Gcomp Done`. Composite is treated as finished. GetImage then reads the destination that still contains the PutImage dest color (Over never became visible). Client reports exact RGB mismatch with X-byte 0.

SurfaceFlinger `fromDequeueTime` ≈ 2138–2167 ms in the same second as each timeout is a **contributing stall** that can make the 2000 ms wait expire; it is not a separate pixel-formula bug. diagnostic-01 showed a start-of-session ~1709 ms SF stall **without** timeout and **without** fail.

## Existing hypothesis impact

**SUPPORTED**

The diagnostic-01 1000/1000 non-reproduction does not contradict this: that lifetime had timeout count 0.

## Cleanup

- killed X 10903 (cmdline matched)
- `am force-stop com.waydefu.x11gpu`
- `NO_X3_RESIDUE`
- Stable 17922 unchanged
- `r1-unset-oracle/` and `r1-unset-diagnostic-01/` not modified

## Project status after this run

- R6 = PASS frozen `0f1e546`
- B-2 = **BLOCKED** (authoritative FAIL still `r1-unset-oracle/`; this cell explains the class)
- R7 = **NOT STARTED**
- R8+ unauthorized
- Production Gate A = **BLOCKED**

## Recommended next action (do not execute here)

Authorize a bounded source correction on a **new** worktree from `a7528bd`: `lorieExaDoneComposite` must not treat `lorieGpuCopyWait` timeout as success (must not repair / ack / `Gcomp Done` and then allow GetImage of an unproven dest). Do not mutate frozen R6. Do not start R7 cells until a new B-2 requalification is separately authorized after that fix.
