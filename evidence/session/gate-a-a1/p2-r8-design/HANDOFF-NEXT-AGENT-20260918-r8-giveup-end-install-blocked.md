# Gate A P2 R8 giveup-end — install BLOCKED — 2026-09-18

```
STATUS: R8_GIVEUP_END_HOST_QUALIFIED
        R8_CI_PASS 35331185799 headSha 2a245b0
        R8_GIVEUP_END_ARTIFACT_QUALIFIED
        R8_INSTALL_BIND_BLOCKED
        device still 5a782f6 INSTALLED
        C1 attempts 01–05 FROZEN
        attempt-06 NOT RUN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

## Do

1. Restore isolated ADB 5038 to a **live** mDNS `_adb-tls-connect._tcp` endpoint. Identity: `ro.product.device=myron`, screen Awake, keyguard false. Do not invent IPs. Do not touch 5037. Do not retry CERT_UNKNOWN.
2. `RUN_INSTALL=YES SERIAL=<live> CELL=.../runtime-2a245b0/r0 bash p2-r8-runtime/install-2a245b0.sh`
3. Bind experimental `1.03.01-2a245b0-18.09.26` SHA256 `008a1ece…3af4` Build ID `5ea80da0…1828`.
4. Fresh C1 `runtime-2a245b0/r8-c1/attempt-06-*` with `run-r8-one-cell-2a245b0.sh`. If PASS, auto-continue C2→P2 fail-fast.

## Do not

- Retry C1 attempts 01–05.
- Rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455 / 35331185799.
- Amend 5a782f6 or 2a245b0.
- Start R9.
- Touch Stable `com.termux.x11` `:1` or HDMI.
- Move X END back into `lorieCloseScreen`.
- Weaken `R8_OBS_POST_END` / judge / 2000 ms timeout.

## RCA in one line

CloseScreen is generation reset (`InitOutput` / `CreateRootCursor` still emit role=x R8_OBS). X END belongs on `ddxGiveUp` immediately before `exit`.

Packets:

- `GATE-A-P2-R8-GIVEUP-END-HOST-QUALIFIED-20260918.md`
- `GATE-A-P2-R8-CI-PASS-2A245B0-20260918.md`
- `GATE-A-P2-R8-ARTIFACT-QUALIFIED-2A245B0-20260918.md`
- `GATE-A-P2-R8-INSTALL-BIND-BLOCKED-2A245B0-20260918.md`
