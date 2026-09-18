# Gate A P2 R8 HEADER SCOPE ESCALATION — 2026-09-18

```
STATUS: R8_HEADER_REPAIR_SCOPE_ESCALATION
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        R8 design ACCEPT / DESIGN_FROZEN
        R8 host SUPPORT_HOST_VERIFIED (historical; 53/53)
        CI 35304122983 FAIL frozen (bc25170)
        prototype d382c0a kept
        CI 35305368742 FAIL frozen (d382c0a lorie_r8_test.c)
        header visibility grant STOPPED (pixmap.h unsafe in shared header;
          checkpoint sizeof 72 != frozen sz 64)
        R8 device NOT STARTED
        Production Gate A BLOCKED
Stable :1: PID 20146 UNTOUCHED
```

HEAD remains `d382c0a96fb84330de939f415413f346fa4b5848`.
Do **not** amend `a4c8177` / `bc25170` / `d382c0a`.

## Do not retry

Frozen R7 cells unchanged.
Do **not** silent-retry CI **35304122983** or **35305368742**.
Do **not** install `bc25170` or `d382c0a`.
Do **not** start R8 device cells or R9.

## Next

New explicit grant that names:

- Xmd self-containment
- PixmapPtr split-or-guarded-typedef (not `void *`)
- QV/checkpoint `sizeof == sz_*` field freeze

Then one commit on top of `d382c0a` and one new CI.

Packet: `GATE-A-P2-R8-HEADER-REPAIR-SCOPE-ESCALATION-20260918.md`
