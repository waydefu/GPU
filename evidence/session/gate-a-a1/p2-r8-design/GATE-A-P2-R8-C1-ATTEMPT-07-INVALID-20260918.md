# GATE A P2 R8-C1 attempt-07 INVALID — 2026-09-18

```
STATUS: R8_INVALID PRODUCERS_NOT_FINALIZED / MISSING_END_x
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        fb4f017 INSTALLED CI 35338856846
        C1 attempts 01–07 FROZEN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** retry C1 attempts 01–07. Do **not** start R8-C2 or R9.
Do **not** rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455 / 35331185799 / 35338856846.
Do **not** amend fb4f017 / 2a245b0 / 5a782f6 / 65938a4.

## Bind

| Field | Value |
| --- | --- |
| SERIAL | `192.168.1.100:46715` |
| source | `fb4f017c73e942e13dc2423744acb912c055b74e` |
| CI | **35338856846** |
| versionName | `1.03.01-fb4f017-18.09.26` |
| APK SHA256 | `71e832768106c9208b2bb3361b2faacbb591c649346ce013f02cbcd0204b4c80` |
| Build ID | `3658dd1f8047bfbb9d4671b269305313adaf1aa7` |
| X | PID **725** `termux-x11gpu com.waydefu.x11gpu :3` |
| renderer | PID **26047** |
| Stable | PID **20146** `1.03.01-11b82d9-06.09.26` lastUpdateTime 2026-09-07 22:55:03 UNCHANGED |
| cell | `p2-r8-runtime/runtime-fb4f017/r8-c1/attempt-07-terminate/` |
| runner | `p2-r8-runtime/run-r8-one-cell-fb4f017.sh` SHA256 `ee756f5a…4101` |
| fixture | `/tmp/p_r8_lifecycle` SHA256 `0156d296…045bf` |

Install **PASS** (`runtime-fb4f017/r0/`, `pm-install-commit.raw.txt` Success). Historical `SCREEN_DOZING` freeze remains as `screen-dozing-blocked.txt`.

## Observed

- `CLIENT_OK`; `TERMINATE_SENT`; `TERMINATE_NO_REPLY_WAIT_HANGUP`; no `TERMINATE_ACK`; no `X_HANGUP_AFTER_TERMINATE`.
- Fixture `timeout 20` exit **124**. CLASS A runner treated `TERMINATE_SENT` as shutdown request (`source=LORIE_R8_TERMINATE`, `x_alive=1` at 20:11:52).
- Logcat has **no** `TEST_CONTROL` `op=TERMINATE`. `ProcLorieR8Terminate` / `GiveUp(0)` were **not observed**.
- 20:11:52.294 `X_CLOSE_ENTER` `lorieCloseScreen` then `X_CLOSE_RESULT` `generation_close=invoked` then **Initialized EGL 1.5** / probe install / shared buffer **id 10** (generation-2 `InitOutput`). `ddxGiveUp` / X `END` not reached.
- Completeness: X BEGIN=1 END=0 count=53; renderer BEGIN=1 END=0 count=7; `R_UNBOUND_FINAL` present; wait-finalized `NOT_FINALIZED MISSING_END_x`.
- Judge **not invoked** (`permit-judge` never reached).
- Runner `invalid` EXIT left X 725 alive; post-cell experimental `am force-stop` then `NO_X725`. Stable 20146 still `:1 -legacy-drawing`.

## Classifier

`R8_INVALID PRODUCERS_NOT_FINALIZED` / `MISSING_END_x`. Same CloseScreen-without-`ddxGiveUp` family as attempt-06, but attempt-07 did **not** SIGTERM X as C1 shutdown. Client death after `timeout 20` is the observed last-client `DE_RESET` edge.

Hypothesis (not proven; do not silent-repair): fixture `xcb_send_request64` uses `iov` without the two reserved leading iovecs xcb documents; `wait_for_reply` blocked the full 20 s; runner `timeout` then closed the socket.

Do **not** move X END. Do **not** enable product `-terminate`. Do **not** SIGKILL.
