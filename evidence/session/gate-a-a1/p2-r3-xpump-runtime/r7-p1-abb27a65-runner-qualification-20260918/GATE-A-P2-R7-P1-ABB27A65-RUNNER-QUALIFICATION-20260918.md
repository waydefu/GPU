# Gate A P2 R7 — abb27a65 R7-P1 dedicated runner tooling qualification — 2026-09-18

```
PRIMARY_VERDICT: R7_P1_ABB27A65_RUNNER_QUALIFIED
abb27a65: ARTIFACT QUALIFIED / NOT INSTALLED at this packet
R7-P1 device: NOT RUN
R7-P2 device: NOT RUN
R7 overall: IN PROGRESS (11/13)
Production Gate A: BLOCKED
Device execution this packet: NONE
```

This packet is **tooling only**. It is **not** `R7_PASS present-hold-complete`
and **not** an R7-P1 device qualification.

## Starting authority

- Source `abb27a65b029b16837fe178624a85ac18a4ba005` parent `8545b26b308aa60b05685f48560285350e22ee8d`
- CI **35253641841** artifact QUALIFIED
- APK `com.waydefu.x11gpu` `1.03.01-abb27a6-17.09.26` versionCode 15
  SHA256 `b7baa1df5d7541efb993bf38f728846996b9c1601ad34b7f8eadd8128aa99d99`
  size 15300558
  signer `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1`
  Build ID `7362d978c058ee2dac4cc8e60812dc3b3785f452`
- Historical 8545b26 R7-P1 `runtime-8545b26/r7-p1/` INVALID / FROZEN (`NO_PRESENT_CALLBACK`)
- Historical `run-r7-p1-8545b26.sh` SHA256 `46c2289dcdddd518c2e4ecb99095e3991c640fa11e92149b83d8d79f20a16ba7` unmodified
- Frozen judge SHA256 `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17`

## Frozen R7-P1 contract

Selector `present-hold-complete` cell 12 renderer/2.
CALLBACK(30) src=4 matching serial/generation → event35 enum=12 once.
Expected terminal `x-present-copy-wait/4`.
`x-hup/6` is forbidden for valid P1.
event34 / CompleteNotify / semantic retirement = 0.
Product wait 2000 ms. WAIT_S=12 observation only.

Present-target arm: early CopyArea cannot consume enum12; matching Present consumes once.

## Dedicated runner

Path: `run-r7-p1-abb27a65.sh`
SHA256: `95900a2d22a37877c065b007feefe07895d8dcb37661e0d3b52b27e9d4ba7098`
Size: 24482

Only tuple: `CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present WAIT_S=12 ROOT=.../runtime-abb27a65`

VALIDATE_ONLY=1: adb=0 mkdir=0 trigger=0. Does not create `runtime-abb27a65/r7-p1`.
Refuses historical `runtime-8545b26`. Never installs.

Classifier `scripts/classify_r7_p1_abb27a65.py`
SHA256 `e741867f0238ae85b41c79bdfb20ade00132ca88d74038eb28b4f926e2c2efe7`

Positive class: `EXPECTED_PRESENT_TIMEOUT`
New invalid classes: `EARLY_COPY_CONSUME`, `SERIAL_MISMATCH`

## Host tests

`scripts/test_r7_p1_abb27a65_runner.sh` **pass=30 fail=0**

Includes classifier 12/12, frozen judge 16/16, `GATEA_TEST_FAULT_CLASS=PASS`,
`GATEA_WAIT_WAKE_CLASS=PASS`, `R7_P1_PRESENT_TARGET_ARM=PASS`,
present fixture SHA `fec8f46d…ba86` size 72536, holder SHA `3417abbf…b5ca`,
historical INVALID cell intact, judge unmodified.

## Device mutation audit

```
ADB install = 0
Activity = 0
X3 = 0
runtime-abb27a65/r7-p1 created = NO
Stable mutation = 0
HDMI mutation = 0
```

## Primary verdict

**R7_P1_ABB27A65_RUNNER_QUALIFIED**
