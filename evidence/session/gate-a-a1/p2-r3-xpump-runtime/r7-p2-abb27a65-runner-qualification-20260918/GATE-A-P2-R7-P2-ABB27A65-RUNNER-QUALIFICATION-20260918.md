# Gate A P2 R7 — abb27a65 R7-P2 dedicated runner tooling qualification — 2026-09-18

```
PRIMARY_VERDICT: R7_P2_ABB27A65_RUNNER_QUALIFIED
abb27a65: ARTIFACT QUALIFIED / NOT INSTALLED at this packet
R7-P2 device: NOT RUN
R7 overall: IN PROGRESS (11/13)
Production Gate A: BLOCKED
Device execution this packet: NONE
```

This packet is **tooling only**. It is **not** `R7_PASS present-renderer-exit`
and **not** an R7-P2 device qualification.

## Frozen R7-P2 contract

Selector `present-renderer-exit` cell 13 renderer/2.
CALLBACK(30) src=4 matching serial/generation → event35 enum=13 once →
renderer intentional `_exit(127)`.
Expected X terminal `GATEA_FATAL_HALT what=x-hup reason=6`.
`x-present-copy-wait/4` is FAIL.
Startup CopyArea consume of enum13 is INVALID.
event34 / CompleteNotify / ACK / idle / semantic completion = 0.
`r-hup/6` is not an X-containment substitute.
Product wait remains 2000 ms. WAIT_S=12 observation only.

Uses the same Present-target arm as P1. Holder `p_b3a_hold` required exactly once
(`lorieRendererAvailable` / surfaceAvailable). Frozen Present ELF `p_r6_d2_present`
SHA256 `fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86`.

## Dedicated runner

Path: `run-r7-p2-abb27a65.sh`
SHA256: `d36a4ccca7b7b148d77433b376c994ae435cec92e5dc4ed09604ab653901d8cc`
Size: 24501

Only tuple: `CELL_ID=r7-p2 FAULT=present-renderer-exit FIXTURE=present WAIT_S=12 ROOT=.../runtime-abb27a65`

VALIDATE_ONLY=1: adb=0 mkdir=0 trigger=0. Does not create `runtime-abb27a65/r7-p2`.
Refuses historical `runtime-8545b26`. Never installs.
Does not fabricate waitpid / exit127.

Classifier `scripts/classify_r7_p2_abb27a65.py`
SHA256 `d4dd9f0b148e28077cb9a3411ef5ef28070cc46d78d702cb4a8291686302030e`

Positive class: `EXPECTED_PRESENT_RENDERER_EXIT`
Invalid: `EARLY_COPY_CONSUME`, `SERIAL_MISMATCH`
Fail: timeout/4 after construction, `RHUP_SUBSTITUTE`, `TARGET_COMPLETED`

## Host tests

`scripts/test_r7_p2_abb27a65_runner.sh` **pass=27 fail=0**

Includes classifier 8/8, frozen judge 16/16, C fault-class PASS,
wait-wake PASS, present-target-arm static PASS, historical 8545b26 P1 runner
unmodified, historical INVALID P1 cell intact.

## Device mutation audit

```
ADB install = 0
Activity = 0
X3 = 0
runtime-abb27a65/r7-p2 created = NO
Stable mutation = 0
HDMI mutation = 0
```

## Primary verdict

**R7_P2_ABB27A65_RUNNER_QUALIFIED**
