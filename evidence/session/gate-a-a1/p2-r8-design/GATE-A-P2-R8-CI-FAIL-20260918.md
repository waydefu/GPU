# GATE A P2 R8 CI FAIL — 2026-09-18

```
STATUS: R8_CI_FAIL
        first CI run 35304122983 FAILED
        no automatic rerun
        no source patch under this grant
        R8 device cells NOT RUN
        Production Gate A BLOCKED
```

This packet freezes the first (only) CI attempt for R8 support SHA
`bc25170bfb9dcf40dee3ab64de9ca8962f4da4cc`. Do **not** rewrite this record
as a later PASS. Do **not** silent-retry this run.

## Binding

| Field | Value |
| --- | --- |
| Verdict | **R8_CI_FAIL** |
| Parent (R7 final, unamended) | `a4c8177f4b059fddd111717255e9d23cf0e15e1e` |
| Support commit | `bc25170bfb9dcf40dee3ab64de9ca8962f4da4cc` |
| Branch | `feat/gatea-r8-lifecycle-support-20260918` |
| Fork | `waydefu/termux-x11` |
| CI run | **35304122983** |
| Job | Build `105472699316` |
| Event | `workflow_dispatch` |
| headSha | `bc25170bfb9dcf40dee3ab64de9ca8962f4da4cc` |
| Conclusion | `failure` |
| URL | https://github.com/waydefu/termux-x11/actions/runs/35304122983 |
| Created | 2026-09-18T03:41:04Z |
| Completed | 2026-09-18T03:43:31Z |
| Artifact | **none** (Store APK steps skipped) |
| Installed experimental | unchanged `a4c8177` `1.03.01-a4c8177-18.09.26` CI **35295094951** |
| Design acceptance | `R8_DESIGN_ACCEPTED_ON_A4C8177` (historical; not rewritten) |
| Host verification | `R8_SUPPORT_HOST_VERIFIED` (historical; host gcc/python, not NDK) |

## Evidence hashes

| File | SHA256 |
| --- | --- |
| `ci-35304122983/run.json` | `11494b7dc8fe025c74299ea241fc6a268d2fe4206fabcfd6d3a2f0e5e5e22d1e` |
| `ci-35304122983/run.log` | `e814953fb2d88ec81a9d0fbdeb6a191ebfbb1f5873baae92b7c789cfcbc6b4a8` |
| `ci-35304122983/compile-errors.txt` | `501fc0ba4dde1fe701f310681bb3d3aa086a5ba853cbde1976667806c86d0ada` |

## Fail site (NDK, arm64-v8a)

`lorie/src/main/cpp/lorie/InitOutput.c`

1. Line **3414** (R8 P1 ON path): `lorieExaDestroyPixmap(pScreenPtr, hookPriv);`
   - `error: call to undeclared function 'lorieExaDestroyPixmap'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration]`
2. Line **3877** (existing EXA destructor definition):
   - `error: conflicting types for 'lorieExaDestroyPixmap'`

Task `:lorie:buildCMakeDebug[arm64-v8a] FAILED`. `ninja: build stopped`. `BUILD FAILED in 1m 33s`.

`lorieExaDestroyPixmap` has **no header prototype**. It is defined later in the same translation unit. Host verification compiled the fixture/`tests/r8` parsers, not this Android C file, so host PASS did not cover this NDK error.

## RCA scope (report only; not repaired here)

- Class: compile-only test-support missing prototype.
- Product path: P1 R8 ON candidate must call the **real** destructor (A05). That call was inserted **above** the existing definition.
- Not: shared Gate A ABI, timeout, judge-r7, READY/result/Present ACK, completedSerial, surface, generation ownership.
- Minimal next-grant repair (not executed): a same-file forward declaration of `lorieExaDestroyPixmap` before line 3414, or a header prototype. Do **not** amend `bc25170`. Do **not** re-dispatch run **35304122983**.
- Requalification if repaired: one new commit, one new CI run, then artifact/install/10-cell batch under a **new** grant. This grant forbids automatic CI rerun and silent post-CI source patch.

## What did not run

Phase D runtime tooling/manifest qualification: **NOT RUN**  
Phase E install: **NOT RUN**  
R8-C1 … R8-P2: **NOT RUN**  
R8 aggregate: **NOT RUN**  
R9: **NOT RUN**

## Do not

- Silent-retry CI **35304122983**
- Amend `a4c8177` or `bc25170`
- Install `bc25170`
- Start any R8 device cell
- Start R9/R10
- Touch Stable `:1` / HDMI
- Weaken judge / timeout / shared ABI
