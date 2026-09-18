# Gate A P2 R8 CI FAIL / d382c0a — 2026-09-18

```
STATUS: R8_CI_FAIL
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13 (unchanged)
        R8 design ACCEPT / DESIGN_FROZEN
        R8 host SUPPORT_HOST_VERIFIED
        historical CI 35304122983 FAIL frozen (bc25170 implicit dtor)
        prototype repair d382c0a committed (InitOutput.c +1)
        new CI 35305368742 FAIL frozen (lorie_r8_test.c include/XMD)
        R8 device NOT STARTED
        Production Gate A BLOCKED
Stable :1: PID 20146 UNTOUCHED
```

Installed experimental remains: `com.waydefu.x11gpu` `1.03.01-a4c8177-18.09.26`
CI **35295094951**.

Repair commit (not installed): `d382c0a96fb84330de939f415413f346fa4b5848`
parent `bc25170bfb9dcf40dee3ab64de9ca8962f4da4cc`

## Do not retry

Frozen R7 cells unchanged.

Do **not** silent-retry GitHub Actions **35304122983** or **35305368742**.
Do **not** install `bc25170` or `d382c0a`.
Do **not** start R8 device cells or R9.
Do **not** amend `a4c8177` / `bc25170` / `d382c0a`.

## Next

STOP until a new explicit grant whose scope is **beyond** a same-file
prototype: NDK include order / `PixmapPtr` completeness / `r8-test-protocol.h`
XMD visibility for `lorie_r8_test.c`. Then one new commit and one new CI run.

Authority packet: `GATE-A-P2-R8-CI-FAIL-D382C0A-20260918.md`
Historical prototype-era fail: `GATE-A-P2-R8-CI-FAIL-20260918.md`
Design: `GATE-A-P2-R8-DESIGN-ACCEPTANCE-20260918.md`
Host: `GATE-A-P2-R8-SUPPORT-HOST-VERIFIED-20260918.md`
Historical R7 complete: `p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-complete-a4c8177.md`
