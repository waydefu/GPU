# GATE A P2 R8-C1 attempt-06 INVALID — 2026-09-18

```
STATUS: R8_INVALID PRODUCERS_NOT_FINALIZED / MISSING_END_x
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        2a245b0 INSTALLED CI 35331185799
        C1 attempts 01–06 FROZEN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** retry this cell. Do **not** create attempt-07. Do **not** start R8-C2 or R9.
Do **not** rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455 / 35331185799.
Do **not** amend 2a245b0 / 5a782f6 / 65938a4.

## Bind

| Field | Value |
| --- | --- |
| source | `2a245b0bc5d38394df29546e0af0de798f9d260c` |
| parent | `5a782f6f47ffa1a3374bac04aef5616a81d59089` |
| CI | **35331185799** |
| package | `com.waydefu.x11gpu` |
| versionName | `1.03.01-2a245b0-18.09.26` |
| APK SHA256 | `008a1ece18c0b766abb8389a512fe81d3c2dd8527e7175531964a4cf43683af4` |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` |
| Build ID | `5ea80da0915ba382c53345efd28099b66d101828` |
| SERIAL | `192.168.1.100:46715` (live mDNS `_adb-tls-connect._tcp`) |
| ADB | isolated 5038 PID **3065** |
| device | Xiaomi / 25102PCBEG / myron / Android 16 SDK 36 |
| screen | Awake; keyguard false |
| runner | `p2-r8-runtime/run-r8-one-cell-2a245b0.sh` SHA256 `5c7d07e0…e279fe` |
| judge | `f021048d…0e31` **not invoked** |
| collector | `e6df519a…666c8` unchanged |
| FINALIZE_S | 8 |
| evidence | `p2-r8-runtime/runtime-2a245b0/r8-c1/attempt-06-giveup-end/` |

CmdEntryPoint log: `commit 2a245b0bc5d38394df29546e0af0de798f9d260c`.

## Cell

| Field | Value |
| --- | --- |
| X PID | **30003** (owned `termux-x11gpu com.waydefu.x11gpu :3`) |
| fixture | `CLIENT_OK` FIXTURE_EXIT=0 |
| shutdown | SIGTERM to exact owned PID 30003 |
| X BEGIN | 1 (`18:03:11.429`) |
| X END | **0** |
| X `R8_OBS_POST_END` | **0** (no END, detector correctly idle) |
| X_CLOSE_ENTER | true `18:03:18.976` path=`lorieCloseScreen` |
| X_CLOSE_RESULT | true `18:03:18.986` generation_close=`invoked` |
| last X JSON | `RECHECK` site=`handleLegacyRecord` seq=52 `18:03:19.156` |
| renderer BEGIN | 1 |
| renderer END | 1 (`actual_count=8`, digest `eb9d3739fdcb6321`) |
| renderer `R8_OBS_POST_END` | 0 |
| completeness | x_count=53 r_count=10 fabricated=false |
| judge | **not invoked** (`PRODUCERS_NOT_FINALIZED`) |
| runner rc | **2** |
| verdict | `R8_INVALID PRODUCERS_NOT_FINALIZED` / `MISSING_END_x` |

## Timeline (device logcat)

1. `18:03:11.429` X `BEGIN` pid 30003 tid 30779
2. `18:03:18.976` `X_CLOSE_ENTER` then `X_TERMINAL_WAIT_ENTER` serial=4
3. `18:03:18.986` `X_CLOSE_RESULT` / `GATEA_SUMMARY where=x-close-screen`
4. `18:03:18.998` generation-2 EGL init (`Xlorie: Initialized EGL version 1.5`)
5. `18:03:19.028` `lorieInstallXRenderProbe` / histogram probe installed
6. `18:03:19.043` shared buffer id **10** 1200×2191
7. `18:03:19.075–19.156` post-CloseScreen DDX: destructor buffers 12/13, `DEFER_ENQUEUE` type=17, `X_WAKE_RECEIVED`, `DEFER_DISPATCH`, `RECHECK`
8. `18:03:19.404` renderer `R_SURFACE_QUIESCED` then renderer `END`
9. Collect window through `18:03:28`: **no** `role=x` `END`, **no** `R8_OBS_POST_END`, **no** `ddxGiveUp` log

SIGTERM request is timestamped `18:03:19` (after CloseScreen enter). CloseScreen is the last-client / `DE_RESET` path. `ddxGiveUp` (the only remaining X `lorieR8ObsEnd("x")` site under `LORIE_ENABLE_R8_TEST_SUPPORT`) was not reached inside `FINALIZE_S=8`.

## Classification

Detector behaved as specified: missing X END is `R8_INVALID`, not PASS, and post-END was not weakened.

`2a245b0` moved X END to `ddxGiveUp` so generation-2 DDX work after saved CloseScreen return is no longer post-END. This cell shows that same generation-2 work still happens, and the X producer then stays without END for the whole finalize window.

C2–P2 were **not** started (fail-fast). Attempts 01–05 remain frozen with their original classifiers.

## Stable / HDMI

Stable `:1` X PID **20146** `com.termux.x11` `1.03.01-11b82d9-06.09.26`
lastUpdateTime `2026-09-07 22:55:03` UNCHANGED. HDMI observe-only
(internal display only). Experimental leftover activity was force-stopped
after the cell; Stable was not.
