# GATE A P2 R8-C1 attempt-05 INVALID — 2026-09-18

```
STATUS: R8_INVALID POST_END_OBSERVATION
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        5a782f6 INSTALLED
        C1 attempts 01–05 FROZEN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** retry this cell. Do **not** create attempt-06. Do **not** start R8-C2 or R9.
Do **not** rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455.
Do **not** amend 5a782f6.

## Bind

| Field | Value |
| --- | --- |
| source | `5a782f6f47ffa1a3374bac04aef5616a81d59089` |
| parent | `65938a447639fce2adae61a15a2d8348e7c6455f` |
| CI | **35321447455** |
| package | `com.waydefu.x11gpu` |
| versionName | `1.03.01-5a782f6-18.09.26` |
| APK SHA256 | `43590412d5537339bb6822d0157e135b5fc00a7cca80570d987adc87c15ba78e` |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` |
| Build ID | `d032a8188b4f768a523b4c06cfe62a813950b02a` |
| SERIAL | `10.191.48.13:38361` (live mDNS `_adb-tls-connect._tcp.local.`) |
| ADB | isolated 5038 PID **3065** |
| device | Xiaomi / 25102PCBEG / myron / Android 16 SDK 36 |
| evidence | `p2-r8-runtime/runtime-5a782f6/r8-c1/attempt-05-obs-terminal/` |

## Cell

| Field | Value |
| --- | --- |
| X PID | **14186** (owned `termux-x11gpu com.waydefu.x11gpu :3`) |
| fixture | `CLIENT_OK` FIXTURE_EXIT=0 |
| shutdown | SIGTERM to exact owned PID 14186 |
| X BEGIN | 1 |
| X END | 1 (`actual_count=44`, JSON last phase END) |
| X post-END JSON | 0 (collector does not ingest `R8_OBS_POST_END`) |
| X `R8_OBS_POST_END` | **8** |
| renderer BEGIN | 1 |
| renderer END | 1 (`actual_count=8`) |
| renderer `R8_OBS_POST_END` | 0 |
| judge | **not invoked** (terminal-stream validation failed first) |
| verdict | `R8_INVALID POST_END_OBSERVATION` |

## Timeline (device logcat)

1. `16:22:27.744` `X_CLOSE_ENTER` path=lorieCloseScreen
2. `16:22:27.758` `X_CLOSE_RESULT` generation_close=invoked
3. `16:22:27.760` X `END` actual_count=44 (after saved CloseScreen return)
4. `16:22:27.805–27.858` eight `R8_OBS_POST_END role=x`:
   `X_DESTRUCTOR_ENTER`×2, `X_DESTRUCTOR_EXIT`×2, `DEFER_ENQUEUE`,
   `X_WAKE_RECEIVED`, `DEFER_DISPATCH`, `RECHECK`
5. `16:22:28.085` renderer `R_SURFACE_QUIESCED` then renderer `END`

JSON completeness for collected `R8_OBS` rows is internally consistent
(BEGIN=1 END=1, x_count=46, r_count=10). That does **not** make the cell
PASS: post-END producer calls were observed and not truncated.

## Classification

`5a782f6` moved X END to after saved CloseScreen returns. Remaining
destructor / defer work still runs on the same X thread **after**
`lorieCloseScreen` returns. Detector behaved as specified.

C2–P2 were **not** started (fail-fast). Attempts 01–04 remain frozen
with their original classifiers.

## Stable / HDMI

Stable `:1` PID **20146** `com.termux.x11` `1.03.01-11b82d9-06.09.26`
lastUpdateTime `2026-09-07 22:55:03` UNCHANGED. HDMI observe-only
(internal display only).
