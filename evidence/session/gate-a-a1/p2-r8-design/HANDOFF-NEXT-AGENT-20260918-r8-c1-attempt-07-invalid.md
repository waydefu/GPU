# Gate A P2 R8-C1 attempt-07 INVALID — 2026-09-18

```
STATUS: R8_INVALID PRODUCERS_NOT_FINALIZED / MISSING_END_x
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        fb4f017 INSTALLED CI 35338856846
        C1 attempts 01–07 FROZEN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** retry C1 attempts 01–07. Do **not** create attempt-08.
Do **not** start R8-C2 or R9.
Do **not** rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455 / 35331185799 / 35338856846.
Do **not** amend fb4f017 / 2a245b0 / 5a782f6 / 65938a4.
Do **not** silent-retry `runtime-fb4f017/r0` or `runtime-fb4f017/r8-c1`.

Install **PASS**: experimental `1.03.01-fb4f017-18.09.26`
SHA256 `71e83276…4c80` Build ID `3658dd1f…1aa7`.
Packet `GATE-A-P2-R8-INSTALL-BIND-PASS-FB4F017-20260918.md`.

Attempt-07 path `runtime-fb4f017/r8-c1/attempt-07-terminate/`
X 725 CLIENT_OK `TERMINATE_SENT` no `TEST_CONTROL TERMINATE`;
fixture exit 124; CloseScreen then gen-2 InitOutput; X END=0 renderer END=0;
judge not invoked. Packet `GATE-A-P2-R8-C1-ATTEMPT-07-INVALID-20260918.md`.

Historical attempts 01–06 remain frozen with original classifiers.

**STOP.** New explicit grant required before any R8 source change or C1 retry.
Production Gate A remains BLOCKED.
