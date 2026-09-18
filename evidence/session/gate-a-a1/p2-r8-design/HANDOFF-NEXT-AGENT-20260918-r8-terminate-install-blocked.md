# Gate A P2 R8 fb4f017 install BLOCKED — 2026-09-18

```
STATUS: R8_INSTALL_BIND_BLOCKED SCREEN_DOZING
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        source fb4f017 CI 35338856846 PASS / ARTIFACT QUALIFIED
        experimental remains 2a245b0 INSTALLED
        C1 attempts 01–06 FROZEN
        C1 attempt-07 NOT RUN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** silent-retry install. Do **not** wake the screen from the agent.
Do **not** create attempt-07 until install bind PASS.
Do **not** retry C1 attempts 01–06. Do **not** start R8-C2 or R9.
Do **not** rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455 /
35331185799 / **35338856846**.
Do **not** amend fb4f017 / 2a245b0.

## What landed

- RCA: C1 last-client `xcb_disconnect` → `SetDispatchExceptionTimer` →
  `DE_RESET` (`dispatchExceptionAtReset` default). `Dispatch` clears
  `DE_RESET`. `dix_main` calls `ddxGiveUp` only on `DE_TERMINATE`.
  SIGTERM `GiveUp` is the official terminate handler, but this runtime
  already entered gen-2 before END. Product `-terminate` was **not** enabled.
- Repair (test-only, `LORIE_ENABLE_R8_TEST_SUPPORT`): opcode 3
  `X_LorieR8Terminate` → `ProcLorieR8Terminate` / inlined dispatch path
  writes reply then `GiveUp(0)` while the client is still connected.
  X END still only in `ddxGiveUp`. Renderer / judge / collector / 2000ms
  timeout unchanged.
- Host: `R8_SUPPORT_HOST_STATIC_OK`. Judge SHA `f021048d…0e31`. Collector
  SHA `e6df519a…666c8`.
- Commit `fb4f017c73e942e13dc2423744acb912c055b74e` parent `2a245b0`.
- CI **35338856846** workflow_dispatch success on that SHA.
- Artifact QUALIFIED: `1.03.01-fb4f017-18.09.26`
  SHA256 `71e83276…4c80` Build ID `3658dd1f…1aa7`
  signer `b6da0148…e5e1`. Unstripped: opcode 3 → `GiveUp@plt`;
  `GiveUp` ORs `#0x2`; `ddxGiveUp` still `lorieR8ObsEnd` then `exit`.

## What blocked

Install `runtime-fb4f017/r0/`: `PRE_INSTALL_ARTIFACT_BIND=PASS` then
`mWakefulness=Dozing` / `isKeyguardShowing=true`. No `pm install`.
Device experimental remains `1.03.01-2a245b0-18.09.26`.

Packet: `GATE-A-P2-R8-INSTALL-BIND-BLOCKED-FB4F017-20260918.md`

## Next (new explicit grant)

1. Screen Awake, keyguard false (human).
2. `RUN_INSTALL=YES` `install-fb4f017.sh` CELL `.../runtime-fb4f017/r0`
   (no `pm-install-commit.raw.txt` yet).
3. Fresh C1 `runtime-fb4f017/r8-c1/attempt-07-*` with terminate runner.
4. PASS auto-continue C2→P2 fail-fast. First FAIL/INVALID/BLOCKED freeze+STOP.
