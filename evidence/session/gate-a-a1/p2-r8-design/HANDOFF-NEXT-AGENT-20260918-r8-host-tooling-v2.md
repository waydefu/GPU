# Gate A P2 R8 host tooling v2 published — 2026-09-18

```
STATUS: R8_HOST_TOOLING_V2_PUBLISHED
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        b984ded INSTALLED CI 35347497216
        C1 attempts 01–08 FROZEN
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Product remains `b984dedcac731b77ca4cf8899f8a78b7848ad083`
CI **35347497216**. Tooling commit
`2a14ab2f7a5d81e7cd72d5308f5865b81b22881f` is host-only.

Do **not** retry C1 attempts 01–08.
Do **not** start C1 attempt-09 without a new explicit grant.
Do **not** start R8-C2 or R9.
Do **not** rerun CI 35304122983 / 35305368742 / 35311343984 / 35321447455 /
35331185799 / 35338856846 / **35347497216**.
Do **not** amend b984ded product / APK / EXPECT_HEAD.
Do **not** overwrite `run-r8-one-cell-b984ded.sh`.

Live runner for any future C1 grant:
`p2-r8-runtime/run-r8-one-cell-b984ded-v2.sh`
(`JUDGE=judge-r8-v2.py`, product `EXPECT_HEAD=b984ded…`).

Frozen historical runner:
`p2-r8-runtime/run-r8-one-cell-b984ded.sh` SHA256 `f22546b7…ab7b0`.

Attempt-08 remains `R8_INVALID JUDGE_NOT_PERMITTED / MULTI_BEGIN_x`.
Packet `GATE-A-P2-R8-C1-ATTEMPT-08-INVALID-20260918.md`.
Host tooling packet `GATE-A-P2-R8-HOST-TOOLING-V2-PUBLISHED-20260918.md`.

**STOP.** Request explicit authorization for fresh C1 attempt-09.
Do not start it automatically.
Production Gate A remains BLOCKED.
