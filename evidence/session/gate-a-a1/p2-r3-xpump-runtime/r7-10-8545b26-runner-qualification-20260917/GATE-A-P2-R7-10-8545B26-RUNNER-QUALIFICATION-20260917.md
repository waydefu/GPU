# Gate A P2 R7 — 8545b26 R7-10 dedicated runner tooling qualification — 2026-09-17

```
PRIMARY_VERDICT: R7_10_8545B26_RUNNER_QUALIFIED
a07d66c: R7-10 VALID FAIL / FROZEN / INSTALLED
8545b26: ARTIFACT QUALIFIED / R7-10 NOT RUN / RUNNER QUALIFIED / NOT INSTALLED
R7 overall: IN PROGRESS (10/13)
R7-P1: BLOCKED
Production Gate A: BLOCKED
Device execution this task: NONE
```

This packet is **tooling only**. It is **not** `R7_PASS renderer-exit-after-consume`
and **not** an 8545b26 device requalification.

## Starting authority

- Historical candidate `a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82` INSTALLED experimental only
- Historical R7-10 `R7_10_A07D66C_QUALIFICATION_FAIL` VALID FAIL FROZEN
  (`runtime-a07d66c/r7-10/`; last halt `x-direct-not-success/4`; expected `x-hup/6`)
- Repair candidate `8545b26b308aa60b05685f48560285350e22ee8d` parent `a07d66c`
  branch `fix/gatea-r7-10-hup-containment-20260917`
- RCA PROVEN; HOST QUALIFIED; CI **35225593518** PASS; ARTIFACT QUALIFIED; **NOT INSTALLED**
- APK `com.waydefu.x11gpu` `1.03.01-8545b26-17.09.26` versionCode 15
  SHA256 `92220845a4cfff24eb47edef95664070d7bf60b159c01258e03b91d6a332377a`
  signer `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1`
  Build ID `50a4078b940d982e1ca1484cac6dd2bf2abe7b0a`
- R7-04 / R7-05 / R7-01 / R7-02 / R7-03 / R7-06 / R7-07 / R7-08 / R7-09 / R7-11 PASS frozen
- Frozen generic runner SHA256 `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded`
- Frozen judge SHA256 `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17`
- Production Gate A BLOCKED

## Why the a07d66c runner cannot be reused

`run-r7-one-cell-a07d66c.sh` is historical tooling authority for
R7-01/02/03/06/07/08/10 on `a07d66c`. Candidate / versionName / ROOT binding
is part of that qualification identity.

Editing it to bind `8545b26` would pollute those cells' tool identity.
Copying its live skeleton into a **new** file is the isolation required.

Generic r7-10 mapping remains ENABLED for the frozen a07d66c candidate only.
Future 8545b26 R7-10 device requal **must** use the dedicated runner.

## New runner

Path: `evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-10-8545b26.sh`

SHA256: `690a865d1bce410cabe10dd7d1da27be89a1f53302ac932f64cc50980afc54cd`
Size: 22480 bytes

Classifier:
`scripts/classify_r7_10_hup_containment.py`
SHA256: `ed73a314104c5eae5aaa5f8964e583ccd8b3d06f5ff387d75fb42cc146ca05d7`

Only tuple accepted:

```
CELL_ID=r7-10
FAULT=renderer-exit-after-consume
FIXTURE=direct
WAIT_S=12
ROOT=.../runtime-8545b26
```

VALIDATE_ONLY=1 validates CELL/FAULT/FIXTURE/WAIT_S/ROOT, prints candidate
constants and the immutable plan, then exits. No ADB, no mkdir, no Activity,
no X3, no holder, no fixture, no install.

Live destination-exists REFUSE happens before mkdir / harness source.

## Candidate binding

Hard-bound in the runner:

| Constant | Value |
|---|---|
| EXPECT_SHA / CANDIDATE_HEAD | `8545b26b308aa60b05685f48560285350e22ee8d` |
| EXPECT_VERSION | `1.03.01-8545b26-17.09.26` |
| EXPECT_VERSION_CODE | 15 |
| EXPECT_PACKAGE | `com.waydefu.x11gpu` |
| EXPECT_BUILD_ID | `50a4078b940d982e1ca1484cac6dd2bf2abe7b0a` |
| EXPECT_APK_SHA256 | `92220845…377a` (plan/preflight; outer grant must re-verify) |
| EXPECT_SIGNER | `b6da0148…e5e1` (plan/preflight; outer grant must re-verify) |
| CANDIDATE_PARENT | `a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82` |
| CANDIDATE_CI | 35225593518 |

Live dumpsys checks package / versionName / versionCode only.
APK SHA256 / signer / Build ID / CI / source SHA remain the outer device-grant
profile. versionName alone is not provenance.

This runner never installs.

## Input policy

ACCEPT only the tuple above.

REFUSE (exit 9): r7-01, r7-02, r7-03, r7-05, r7-06, r7-07, r7-08, r7-09,
r7-11, r7-p1, r7-p2, wrong FAULT, `present` fixture, WAIT_S != 12,
`runtime-a07d66c`, `runtime-fdfb1ce`, `runtime-7549e36`, extra args,
missing SERIAL in live mode, existing live destination.

## Frozen R7-10 oracle

Unchanged by the repair:

PUBLISH(6) → CONSUME_DIRECT(7) → event35 enum=10 side=2 → renderer
intentional exit → X detects peer HUP → `GATEA_FATAL_HALT x-hup reason=6`

Judge selector `renderer-exit-after-consume`.
Expected judge: `R7_PASS renderer-exit-after-consume`.

Frozen judge row (unmodified):

```
cell=10 side=2 what=x-hup reason=6 need=(publish, consume) hup=true
```

2000 ms timeout, `usleep(200)`, ABI, protocol, fault enum, CASE_LOOP 8 ms
recovery are unmodified.

## Repair-specific oracle

Independent classifier + `r7-10-oracle.txt` on the constructed R7-10 cell:

- `x-hup reason=6` present
- `x-direct-not-success reason=4` = 0

This is the requalification delta versus the frozen a07d66c FAIL.

Timeout/4 is **not** globally forbidden. Genuine live-peer timeout remains
valid architecture. Only this constructed peer-exit cell requires reason4=0.

## HUP precedence semantics

Qualification tooling preserves:

1. SUCCESS already derived → success wins
2. published generationFatal != 0 → published authoritative fatal wins
3. peer HUP + no success + no published fatal → `x-hup/6`
4. live peer + real timeout → timeout/4

A later HUP must not overwrite a published renderer fatal.

## Validation tests

`scripts/test_r7_10_8545b26_runner.sh` SHA256
`1396f0ed1da323f8dc6b28013667568f740ccf797b79def1b7e992c596c6c4ce`

27/27 PASS including:

| Case | Result |
|---|---|
| r7-10 / renderer-exit-after-consume / direct / WAIT=12 / runtime-8545b26 | ACCEPT |
| VALIDATE_ONLY no mkdir | PASS |
| runtime-a07d66c | REFUSE |
| runtime-fdfb1ce | REFUSE |
| r7-11 | REFUSE |
| r7-p1 | REFUSE |
| post-draw-gl | REFUSE |
| present fixture | REFUSE |
| WAIT=30 | REFUSE |
| live destination exists | REFUSE before write |
| VALIDATE_ONLY=1 | no ADB / no mkdir / no launch |

## Mock regressions

| Mock | Classifier | Frozen judge |
|---|---|---|
| PUBLISH+CONSUME+event35+x-hup/6, reason4=0 | EXPECTED_HUP continue_judge | `R7_PASS renderer-exit-after-consume` |
| same construction + x-direct-not-success/4 | HISTORICAL_REASON4 product FAIL | `R7_FAIL halt_mismatch` |
| published `r-test-fatal-pre-fence/6` + HUP_PRESERVE | HUP_PRECEDENCE_PRESERVE | n/a (not this cell) |
| published fatal then later `x-hup/6` halt | HUP_PRECEDENCE_OVERWRITE product FAIL | n/a |
| live-peer timeout/4, no R7-10 construction | GENUINE_TIMEOUT_NOT_R7_10; reason4_globally_forbidden=NO | n/a |

## Static verifier

`scripts/verify_r7_10_8545b26_runner.py` SHA256
`1ebb137359dde42b6d111ca62bb3976722b1718a5a1a42977b88270e86ded184`

`VERIFIER_PASS`: candidate SHA/version/ROOT hard-bound; only r7-10 enabled;
WAIT_S=12; no retry/auto-next/overwrite; judge/timeout/source untouched;
Stable cleanup read-only; experimental cleanup scoped; historical FAIL
cell SHA frozen; `runtime-8545b26/r7-10` absent.

## Judge regression

`test-judge-r7.py` 16/16 PASS.
Judge SHA unchanged `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17`.

## Historical evidence isolation

`runtime-a07d66c/r7-10/` was not modified, copied into, or deleted.
`judge.txt` SHA256 `c816d6c1…eef5` unchanged (`R7_FAIL halt_mismatch what=x-direct-not-success reason=4`).
New candidate writes, when later authorized, go only to `runtime-8545b26/r7-10`.
That cell was **not** created this grant.

## Tool hashes

| Artifact | SHA256 | Size |
|---|---|---|
| dedicated `run-r7-10-8545b26.sh` | `690a865d1bce410cabe10dd7d1da27be89a1f53302ac932f64cc50980afc54cd` | 22480 |
| `classify_r7_10_hup_containment.py` | `ed73a314104c5eae5aaa5f8964e583ccd8b3d06f5ff387d75fb42cc146ca05d7` | 13324 |
| `verify_r7_10_8545b26_runner.py` | `1ebb137359dde42b6d111ca62bb3976722b1718a5a1a42977b88270e86ded184` | 16020 |
| `test_r7_10_8545b26_runner.sh` | `1396f0ed1da323f8dc6b28013667568f740ccf797b79def1b7e992c596c6c4ce` | 13224 |
| generic `run-r7-one-cell-a07d66c.sh` | `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded` | 20529 |
| `judge-r7.py` | `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17` | 9965 |
| `p_r3_single_direct` | `b424a6340aac9140114ef70b4eb80cdbaa17cf8762b730963b865cd947cd8c13` | 71704 |
| `p_b3a_hold` | `3417abbf0855c10bfd2328e87f33518c2f7f59c42529ba157a847d3019f5b5ca` | 70960 |

Repair product HEAD still `8545b26b308aa60b05685f48560285350e22ee8d` clean.
`lorie.h` / `InitOutput.c` / wait classifier / repair tests were not edited.

## Device mutation audit

```
ADB install = 0
Activity launch = 0
X3 launch = 0
holder execution = 0
fixture execution = 0
R7-10 trigger = 0
runtime-8545b26/r7-10 created = NO
Stable mutation = 0
HDMI mutation = 0
```

8545b26 installed = NO
a07d66c remains installed = YES

## Primary verdict

`R7_10_8545B26_RUNNER_QUALIFIED`

Meaning: 8545b26 R7-10 **device requalification tooling is ready**.
Not R7-10 PASS. Not installed.

## State transition

| Axis | Before | After |
|---|---|---|
| a07d66c R7-10 | VALID FAIL / FROZEN / INSTALLED | unchanged |
| 8545b26 artifact | QUALIFIED / NOT INSTALLED | unchanged |
| 8545b26 R7-10 device | NOT RUN | NOT RUN |
| 8545b26 R7-10 runner | absent | QUALIFIED |
| R7 overall | IN PROGRESS 10/13 | IN PROGRESS 10/13 |
| R7-P1 | BLOCKED | BLOCKED |
| Production Gate A | BLOCKED | BLOCKED |

## Recommended next action

Separate grant only:

1. install 8545b26 experimental package only
2. verify APK SHA256 / signer / Build ID / CI / source SHA (not versionName alone)
3. do not touch Stable
4. create fresh `runtime-8545b26/r7-10`
5. run exactly one R7-10 with this dedicated runner

That grant is the first allowed device mutation for this candidate.
