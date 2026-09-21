# GATE A P2 R8 fb4f017 INSTALL BIND BLOCKED — 2026-09-18

```
STATUS: R8_INSTALL_BIND_BLOCKED
        classifier SCREEN_DOZING
        mWakefulness=Dozing
        isKeyguardShowing=true
        experimental remains 2a245b0 INSTALLED
        C1 attempt-07 NOT RUN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

| Field | Value |
| --- | --- |
| SERIAL | `192.168.1.100:46715` live mDNS `_adb-tls-connect._tcp` |
| ADB | isolated 5038 PID **3065** `device` |
| source | `fb4f017c73e942e13dc2423744acb912c055b74e` |
| parent | `2a245b0bc5d38394df29546e0af0de798f9d260c` |
| CI | **35338856846** PASS / QUALIFIED |
| APK SHA256 | `71e832768106c9208b2bb3361b2faacbb591c649346ce013f02cbcd0204b4c80` |
| Build ID | `3658dd1f8047bfbb9d4671b269305313adaf1aa7` |
| versionName | `1.03.01-fb4f017-18.09.26` (artifact, not installed) |
| device | `myron` |
| screen | `mWakefulness=Dozing` `isKeyguardShowing=true` |
| cell | `p2-r8-runtime/runtime-fb4f017/r0/` |
| `pm install-commit` | **NOT RUN** |

`PRE_INSTALL_ARTIFACT_BIND=PASS` then the install script stopped at the
Awake/keyguard gate. No `pm install-*`. No experimental process kill beyond
the script abort (X `:3` was not force-installed). Stable `:1` not touched.

Do **not** silent-retry this install. Do **not** `input keyevent` to wake.
Do **not** create `runtime-fb4f017/r8-c1/attempt-07-*` until install bind PASS.
Do **not** retry C1 attempts 01–06. Do **not** start C2 or R9.
Do **not** rerun CI **35338856846** or frozen CIs.

`r0` has no `pm-install-commit.raw.txt`, so a later explicit grant may reuse
it after the screen is Awake and keyguard is false.
