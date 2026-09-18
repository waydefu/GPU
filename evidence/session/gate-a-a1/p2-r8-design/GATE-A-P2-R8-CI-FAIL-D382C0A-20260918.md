# GATE A P2 R8 CI FAIL — d382c0a / 35305368742 — 2026-09-18

```
STATUS: R8_CI_FAIL
        first NEW CI run 35305368742 FAILED
        no automatic rerun
        no source patch under this grant
        R8 device cells NOT RUN
        Production Gate A BLOCKED
```

This packet freezes the **new** CI attempt after the compile-only prototype
repair. It does **not** replace or rewrite historical
`GATE-A-P2-R8-CI-FAIL-20260918.md` (run **35304122983** / `bc25170`).

## Binding

| Field | Value |
| --- | --- |
| Verdict | **R8_CI_FAIL** |
| Prototype repair commit | `d382c0a96fb84330de939f415413f346fa4b5848` |
| Parent | `bc25170bfb9dcf40dee3ab64de9ca8962f4da4cc` (unamended) |
| R7 final | `a4c8177f4b059fddd111717255e9d23cf0e15e1e` (unamended) |
| Diff of repair | `InitOutput.c` +1 line: `void lorieExaDestroyPixmap(ScreenPtr pScreen, void *driverPriv);` |
| Branch | `feat/gatea-r8-lifecycle-support-20260918` |
| CI run | **35305368742** |
| Job | Build `105476359676` |
| Event | `workflow_dispatch` |
| headSha | `d382c0a96fb84330de939f415413f346fa4b5848` |
| Conclusion | `failure` |
| URL | https://github.com/waydefu/termux-x11/actions/runs/35305368742 |
| Artifact | **none** |
| Installed experimental | unchanged `a4c8177` CI **35295094951** |

## Evidence hashes

| File | SHA256 |
| --- | --- |
| `ci-35305368742/run.json` | `21f280bfd2492bdc2d6834c01158e3e0c5fe39d65d83bdfbe3aa4b1920c54691` |
| `ci-35305368742/run.log` | `b07b6c0ba9424155e77ead18ead56bd9d3c8b20275347d2b4ee53b9202a41d32` |
| `ci-35305368742/compile-errors.txt` | `a73ef7538270f8f6e48238aedfd06689a62435661c144e03effeb503b1dd7747` |

Historical 35304122983 log SHA remains `e814953f…b4a8` (verified present).

## What the prototype repair did prove

`CMakeFiles/Xlorie.dir/lorie/InitOutput.c.o` was built (`[537/540]`).
The original `lorieExaDestroyPixmap` implicit-declaration / conflicting-types
errors are **absent** from this log.

That is not artifact qualification. The Build job still FAILED.

## Fail site (this run)

`lorie/src/main/cpp/lorie/lorie_r8_test.c.o`

1. `lorie_r8_test.h:16/21` — `unknown type name 'PixmapPtr'`
2. `lorie_r8_test.c:89` — `unknown type name 'xLorieR8QueryVersionReply'`
3. follow-on REQUEST/member errors because protocol structs were not visible
   (`r8-test-protocol.h` gates the layouts on `__X11_XMD_H` / `CARD8`)

`:lorie:buildCMakeDebug[arm64-v8a] FAILED`. `BUILD FAILED in 1m 29s`.

## RCA class (report only; not repaired here)

This remaining NDK failure is **not** the frozen 35304122983 declaration-order
defect. It is include / XMD / PixmapPtr visibility in the R8 test extension TU.

Fixing it requires more than a same-file prototype. This grant forbids that
class of source change (`R8_COMPILE_REPAIR_SCOPE_ESCALATION` if continued).
No automatic source repair after this CI fail.

## What did not run

Phase C artifact qualification: **NOT RUN**  
Phase D tooling: **NOT RUN**  
Phase E install: **NOT RUN**  
R8-C1 … R8-P2: **NOT RUN**  
R9: **NOT RUN**

## Do not

- Silent-retry CI **35305368742**
- Silent-retry historical CI **35304122983**
- Amend `a4c8177`, `bc25170`, or `d382c0a`
- Install `bc25170` or `d382c0a`
- Start any R8 device cell
- Start R9
