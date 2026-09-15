# Gate A P2 R6 retirement runtime — `0f1e546` — 2026-09-16

```text
STATUS: R6 PASS (design-complete D1 / D2-INFLIGHT / D2-OOM)
        Production Gate A BLOCKED
        STOP BEFORE R7
ARTIFACT: 0f1e546 / CI 34999213228 QUALIFIED and INSTALLED experimental only
HISTORICAL CELLS: IMMUTABLE (9369553, 95e6f96, 37d8393, d9b7f60)
```

Install of `0f1e546` **DONE** experimental only. Three first-attempt cells:

| Cell | X PID | First result | Branch | Pixels | Judge |
|---|---|---|---|---|---|
| `r6-d1` | 29152 | PASS | queued Composite then later ops | 64 exact `got0=00804000` | `R6_D1_PASS` |
| `r6-d2-inflight` | 31369 | PASS | **QUIESCENT-ADMIT** (no event 31) | 1048576 exact `got0=00804000` | `R6_D2_PASS d2-inflight` |
| `r6-d2-oom` | 2638 | PASS | requeue-fail **executed** (event 33) then ACK (event 34) | 1048576 exact `got0=00804000` | `R6_D2_PASS d2-oom` |

No silent retries. Historical FAIL files not overwritten. Event 32 absent on all three cells. Stable `:1` PID **17922** UNTOUCHED. HDMI observe-only `mDisplayId=0`. `NO_X3_RESIDUE` after each cell.

## Binding

| | |
|---|---|
| serial | `10.191.48.13:43399` live-fetched `_adb-tls-connect._tcp.local.` |
| Installed | `com.waydefu.x11gpu` `1.03.01-0f1e546-15.09.26` CI **34999213228** |
| APK SHA256 | `2bc4c8ba2b6a11928a3a6b76e04fcd9acf0bacfe11f88afd0a698c8c81b10851` MATCH local=staged=installed |
| Build ID | `263bee5f7d41087b0bd7fa180d47fdafd12b2ecf` MATCH embedded=unstripped=installed |
| HEAD | `0f1e54699d0b11a781f2c044fbc77505f8a53bd8` |
| Worktree | `src/f8-ahb-gatea-r6-retire` `fix/gatea-r6-present-retirement-20260915` clean vs fork |
| Stable | `com.termux.x11` `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03; PID **17922** UNTOUCHED |
| HDMI | observe-only, `mDisplayId=0` |

Install cell: `r0/INSTALL-0f1e546-20260916.md`.
CI QUALIFY: `../../p2-r6-ci-34999213228/P2-R6-CI-ARTIFACT-PROVENANCE-20260916.md`.

## D1 (`r6-d1`) — first attempt PASS

- Fixture SHA256 `e74776f3c85c8595e068d705f7f29a4555a407abd76054ffa4db4cac5afe1197`.
- Env: `TERMUX_X11_GATEA_PROTO=1` `TERMUX_X11_GATEA_TELEMETRY=1`; OOM env **unset**.
- Composite REQUEST seq=26 / CALLBACK seq=27 then SUCCESS serial 6 seq=42 **before** Copy/Solid/GetImage/Present requests.
- Present CALLBACK seq=67 xop=4 serial 9. Event 32 = 0.
- No fatal. X still alive after fixture. Teardown `NO_X3_RESIDUE`. Stable PID 17922.

## D2-INFLIGHT (`r6-d2-inflight`) — first attempt PASS, QUIESCENT-ADMIT

- Fixture SHA256 `fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86`.
- Env: PROTO=1 TELEMETRY=1; OOM env **unset**.
- Present REQUEST seq=53 / CALLBACK seq=54 generation=1 serial **S=7** xop=4.
- Immediate Composite REQUEST seq=55 then CALLBACK seq=57.
- Completion cover: renderer COMPLETED seq=56 serial **T=7 >= S**. GPU raced: cover sits between Composite REQUEST and CALLBACK.
- No LEASE/PUBLISH/SUCCESS between Present CALLBACK and cover.
- Immediate lifecycle: LEASE seq=60 serial=0 src=7 dst=5; PUBLISH serial=8; COMPLETED T=8; SUCCESS serial=8. Finishes before later Composite.
- Later Composite REQUEST seq=80 / CALLBACK seq=81 then second lifecycle LEASE serial=0 / PUBLISH serial=9 / SUCCESS serial=9 (same dest dst=5).
- Event 31 = 0. Event 32 = 0. This is the legal quiescent-admit branch, not a busy-reject.
- Order authority is telemetry `seq`, not logcat line order.

## D2-OOM (`r6-d2-oom`) — first attempt PASS

- Same D2 fixture SHA256. Env **includes** `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1` (X environ captured).
- Fault **executed**: event 33 seq=55 serial=7 dst=5. Environment alone is not the evidence.
- Present CALLBACK seq=54 S=7.
- REQUEUE_FAILED seq=55 serial=7 **then** COMPLETED seq=56 T=7 **then** ACK_AFTER_COMPLETED seq=57 serial=7.
- ACK after **both** requeue-failure and completion cover (`57 > 55` and `57 > 56`).
- Event 32 = 0.
- Later Composite REQUEST seq=58 / CALLBACK seq=59 then LEASE serial=0 / PUBLISH serial=8 / SUCCESS serial=8, then a second later Composite seq=82/83 + lifecycle serial=9.
- No fatal. Exact pixels. `NO_X3_RESIDUE`.

## Fail-stop / teardown classification

| Path | Status |
|---|---|
| D1 / D2-INFLIGHT / D2-OOM happy paths | DEVICE-PROVEN |
| Requeue-fail + wait-then-ACK (events 33 then 34) | DEVICE-PROVEN |
| Timeout (`x-present-copy-wait`) | SOURCE-PROVEN; DEVICE **NOT VERIFIED** (no timeout occurred) |
| Renderer loss | SOURCE-PROVEN; DEVICE **NOT VERIFIED** |
| Scrap | SOURCE-PROVEN (`present_vblank_scrap` → helper); DEVICE **NOT VERIFIED** as a dedicated cell |
| Destroy | SOURCE-PROVEN (`present_vblank_destroy` → helper); DEVICE **NOT VERIFIED** as a dedicated cell |
| CloseScreen with in-flight Present copy | SOURCE-PROVEN; device teardowns had no pending-copy construction. **NOT VERIFIED** as DEVICE-PROVEN |

Do not convert SOURCE-PROVEN into DEVICE-PROVEN.

## Not started

- R7 (`TERMUX_X11_GATEA_TEST_FAULT` still absent from both binaries).
- Production enable / HDMI qualification / PR / merge / origin push.

## Next

STOP BEFORE R7 — authorization required.
Production Gate A remains BLOCKED.
