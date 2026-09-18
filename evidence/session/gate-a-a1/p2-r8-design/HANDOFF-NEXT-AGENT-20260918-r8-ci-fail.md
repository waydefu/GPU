# Gate A P2 R8 CI FAIL / bc25170 — 2026-09-18

```
STATUS: R8_CI_FAIL
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13 (unchanged)
        R8 design ACCEPT / DESIGN_FROZEN for this generation
        R8 host SUPPORT_HOST_VERIFIED
        first CI 35304122983 FAIL frozen
        R8 device NOT STARTED
        Production Gate A BLOCKED
Stable :1: PID 20146 UNTOUCHED
```

Installed experimental remains: `com.waydefu.x11gpu` `1.03.01-a4c8177-18.09.26`
CI **35295094951** APK SHA256 `91a4b74e…a55c` Build ID `dcd82974…ba60`.

Support commit (not installed): `bc25170bfb9dcf40dee3ab64de9ca8962f4da4cc`
parent `a4c8177f4b059fddd111717255e9d23cf0e15e1e`
branch `feat/gatea-r8-lifecycle-support-20260918`

## Do not retry

Frozen R7 cells unchanged (`runtime-a4c8177/r7-p1`, validity-02, r7-p2, abb27a65/8545b26 P1, a07d66c R7-10, …).

Do **not** silent-retry GitHub Actions run **35304122983**.
Do **not** install `bc25170`.
Do **not** start R8-C1 or any R8 device cell.
Do **not** start R9/R10.
Do **not** amend `a4c8177` or `bc25170`.

## Next

STOP until a new explicit grant to:

1. add a compile-only `lorieExaDestroyPixmap` prototype (same-file forward declaration or header), new commit on top of `bc25170`;
2. dispatch **one** new CI run;
3. continue artifact → install → 10 cells only if that new CI PASSes.

Authority packet: `GATE-A-P2-R8-CI-FAIL-20260918.md`
Design: `GATE-A-P2-R8-DESIGN-ACCEPTANCE-20260918.md`
Host: `GATE-A-P2-R8-SUPPORT-HOST-VERIFIED-20260918.md`
Historical R7 complete: `p2-r7-design/HANDOFF-NEXT-AGENT-20260918-r7-complete-a4c8177.md`
