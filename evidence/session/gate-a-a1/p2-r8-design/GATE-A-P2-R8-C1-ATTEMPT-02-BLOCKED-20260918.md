# GATE A P2 R8-C1 attempt-02 BLOCKED — 2026-09-18

```
STATUS: R8_BLOCKED SCREEN_NOT_AWAKE
        keyguard showing
        X never started
        fixture never run
        judge never invoked
        historical attempt-01 INVALID preserved
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

v2 runner preflight recorded `mWakefulness=Dozing` and
`isKeyguardShowing=true`. Script stopped before `am start` / X :3.

Path: `runtime-65938a4/r8-c1/attempt-02-orchestration-v2/`

Live binding at stop still `1.03.01-65938a4-18.09.26` SHA256
`b88f12ec…1a6c`. Stable PID **20146** UNCHANGED. No HDMI mutation.

Do **not** retry this path. Do **not** start attempt-03. Do **not** start C2.
Do **not** overwrite attempt-01.
