# Gate A P2 R8-C1 attempt-08 INVALID — 2026-09-18

```
STATUS: R8_INVALID JUDGE_NOT_PERMITTED / MULTI_BEGIN_x
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        b984ded INSTALLED CI 35347497216
        C1 attempts 01–08 FROZEN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** retry C1 attempts 01–08. Do **not** create attempt-09.
Do **not** start R8-C2 or R9.
Do **not** rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455 /
35331185799 / 35338856846 / **35347497216**.
Do **not** amend b984ded / fb4f017 / 2a245b0 / 5a782f6 / 65938a4.
Do **not** silent-retry `runtime-b984ded/r0` or `runtime-b984ded/r8-c1`.

Install **PASS**: experimental `1.03.01-b984ded-18.09.26`
SHA256 `0d06de68…98d3` Build ID `3658dd1f…1aa7`.
Packet `GATE-A-P2-R8-INSTALL-BIND-PASS-B984DED-20260918.md`.

Attempt-08 path `runtime-b984ded/r8-c1/attempt-08-xcb-sender/`
X 29598 CLIENT_OK `TEST_CONTROL op=TERMINATE` PASS; `ddxGiveUp` then X END=1
renderer END=1; wait-finalized ok; permit-judge REFUSE `MULTI_BEGIN_x`
(raw scan + jsonl double-load); judge not invoked.
Packet `GATE-A-P2-R8-C1-ATTEMPT-08-INVALID-20260918.md`.

xcb sender host repair is committed `b984ded` (parent `fb4f017` unamended).
Attempt-07 hole (no server TERMINATE) is closed on this cell. Orchestration
double-count is the remaining INVALID.

Historical attempts 01–07 remain frozen with original classifiers.

**STOP.** New explicit grant required before any R8 source change or C1 retry.
Production Gate A remains BLOCKED.
