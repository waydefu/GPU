# Gate A P2 R8 OBS terminal repair — install blocked — 2026-09-18

```
STATUS: R8_INSTALL_BIND_BLOCKED
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        5a782f6 HOST/CI/ARTIFACT QUALIFIED
        experimental still 65938a4
        C1 attempts 01–04 FROZEN
        attempt-05 NOT STARTED
        Production Gate A BLOCKED
```

Do **not** retry C1 attempts 01–04. Do **not** start R9.
Do **not** rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455.
Do **not** amend 65938a4 or 5a782f6.

Repair SHA `5a782f6f47ffa1a3374bac04aef5616a81d59089` parent `65938a4`.
CI **35321447455** PASS. APK `1.03.01-5a782f6-18.09.26`
SHA256 `43590412…a78e` Build ID `d032a818…b02a`.

X END is after saved CloseScreen return. Renderer END is
unbind + surface_quiesced + loop drain. Post-END emits `R8_OBS_POST_END`.

Next: live mDNS on ADB 5038 → install-5a782f6.sh →
`runtime-5a782f6/r8-c1/attempt-05-obs-terminal/` one attempt.

Packets:
`GATE-A-P2-R8-OBS-TERMINAL-REPAIR-HOST-QUALIFIED-20260918.md`
`GATE-A-P2-R8-CI-PASS-5A782F6-20260918.md`
`GATE-A-P2-R8-OBS-TERMINAL-ARTIFACT-QUALIFIED-20260918.md`
`GATE-A-P2-R8-INSTALL-BIND-BLOCKED-5A782F6-20260918.md`
