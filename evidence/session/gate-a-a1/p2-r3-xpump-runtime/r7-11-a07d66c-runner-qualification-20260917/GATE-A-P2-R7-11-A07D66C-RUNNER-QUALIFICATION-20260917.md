# Gate A P2 R7 — a07d66c R7-11 dedicated serial-wrap runner tooling qualification — 2026-09-17

```
PRIMARY_VERDICT: R7_11_A07D66C_RUNNER_QUALIFIED
CANDIDATE: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82 INSTALLED
R7-09: PASS / DEVICE-QUALIFIED / FROZEN (not rerun)
R7-11 device cell: NOT RUN / UNBLOCKED
R7 overall: IN PROGRESS (9/13)
Production Gate A: BLOCKED
Device execution this task: NONE
```

This packet is **tooling only**. It removes the R7-11 generic-runner
`REVIEW_REQUIRED` **tooling** blocker by adding a dedicated serial-wrap /
no-serial0 runner. It does **not** execute R7-11. It is **not**
`R7_PASS serial-wrap`.

Generic `run-r7-one-cell-a07d66c.sh` remains frozen
`R7_A07D66C_RUNNER_QUALIFIED` and still maps
`r7-11|serial-wrap|direct` as `REVIEW_REQUIRED` / live REFUSE.
Do **not** lift that mapping. Do **not** modify that file.

## Starting authority

- Candidate `a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82` INSTALLED experimental only
- R6 PASS / FROZEN
- B-2 PASS / FROZEN
- R7-04 / R7-05 / R7-01 / R7-02 / R7-03 / R7-06 / R7-07 / R7-08 / R7-09 PASS / FROZEN
- R7 **IN PROGRESS** (9/13 cells closed; not full R7 PASS)
- Next frozen cell was R7-11 / `serial-wrap` **NOT RUN**
- Production Gate A BLOCKED
- Frozen generic runner SHA256 `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded`
- Frozen judge SHA256 `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17`

## Frozen R7-11 contract

| Field | Frozen value |
|---|---|
| CELL_ID | `r7-11` |
| FAULT | `serial-wrap` |
| side | X / 1 |
| enum | 11 |
| fixture | `direct` |
| WAIT_S | 12 (observation only; production 2000 ms unmodified) |
| construction | first `gateADirectPublishRect` serial allocation after event35 seed |
| PUBLISH prerequisite | **NO** (`need=()`) |
| expected fatal | `GATEA_FATAL_HALT what=x-serial-wrap reason=6` |
| judge selector | `serial-wrap` `need=()` `no_serial0=true` |
| expected judge | `R7_PASS serial-wrap` |

Prior PUBLISH count > 0 is **not** a PASS requirement.
`PUBLISH serial=0` is a **product FAIL** even if the halt string is correct.

## Why generic runner is REVIEW_REQUIRED

`run-r7-one-cell-a07d66c.sh` ENABLED direct cells assume:

startup → 8s alive → holder → fixture → renderer-path fault

R7-11 frozen oracle is different:

event35 → seed `gpuCopySerialCounter=UINT64_MAX` → next `++` wraps →
X-side `x-serial-wrap/6` **before** PUBLISH

Also `need=()`. Flipping `r7-11|serial-wrap|direct` to ENABLED would skip:

- source proof that seed is after event35, not a startup permanent seed
- source proof that the wrapping `++` is the `gateADirectPublishRect` increment
- a first-class `event=6 serial=0` product-FAIL oracle
- serial-state audit that distinguishes source-proven vs device-observed
- fixture identity binding (exactly one `p_r3_single_direct` publish attempt)

Generic remains `REVIEW_REQUIRED` / live REFUSE for r7-11.

## Source reachability

**YES — injection site and ordering are source-proven.** No device trial.

See `injection-reachability.txt` and `serial-seed-ordering.txt`.

`lorieExaComposite` (`exaGpuComp.direct`) → `gateADirectPublishRect`:

1. `lorieGateATestFaultConsume(SERIAL_WRAP)` CAS then event35 (serial_arg=0; does not allocate)
2. `gpuCopySerialCounter = UINT64_MAX` only if consume returned 1
3. `if (++gpuCopySerialCounter == 0) gateAXFatal("x-serial-wrap", FAIL_GENERATION=6)`
4. `gateAXFatal` is noreturn, so `entry->serial` assignment and `EVENT_PUBLISH` are unreachable on wrap

Holder READY then exactly one `p_r3_single_direct` is required to reach that path.
Early X death before that publish attempt is INVALID, unlike R7-09.

## Serial seed ordering

| Step | Class | Content |
|---|---|---|
| counter before hook | source-proven | X-local; default 0; legacy COPY/SOLID may ++ without this fault |
| event35 | source-proven ordering | consume then EVENT 35 enum=11 side=1 |
| seed | source-proven | `UINT64_MAX` after event35; test-only |
| next ++ | source-proven | wraps to 0 |
| detect / fatal | source-proven identity | `x-serial-wrap` reason=6 |
| observed C counter | **NOT_AVAILABLE** | do not invent `observed = UINT64_MAX` |

## Dedicated runner

Path: `evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-11-a07d66c.sh`

SHA256: `74385947cbcef8dbeeb1deea9722b424828d9bf3780a4dd0279290df5310c453`
Size: 25716 bytes

Classifier:
`scripts/classify_r7_11_serial_wrap.py`
SHA256: `3a0af4ff367bf18da2edd0888bda898b10c079c6e0bc93b95e3a111e5dd6b107`

Only tuple accepted:

```
CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct WAIT_S=12
ROOT=.../runtime-a07d66c
```

Any other cell/fault/fixture/wait/root REFUSE exit 9.

Reuses generic ADB isolation (5038), artifact/version readback, Stable snapshot,
X3 precheck, fresh destination, logcat, Activity/X3 launch, exact environ set,
identity, ring/summary, frozen judge, experimental-only cleanup, Stable after-check.

Does **not** `adb install`. Does **not** force-stop `com.termux.x11`. Does **not**
overwrite/append/suffix evidence. Does **not** retry or auto-next.

`VALIDATE_ONLY=1` prints the plan and exits 0 **before** harness source, ADB,
or `mkdir`.

## Input policy

See `input-matrix.txt`. 25/25 host mapping tests PASS.

## Serial-wrap state machine / no-serial0 oracle

Classifier classes:

| Class | Meaning |
|---|---|
| `EXPECTED_WRAP` | event35×1 enum=11 side=1 + `x-serial-wrap/6` + serial0=0 + fixture bound → continue judge |
| `SERIAL0_LEAKED` | event=6 serial=0 → product FAIL even if halt is correct |
| `WRONG_TERMINAL` | expected event35 but last halt is not `x-serial-wrap/6` → FAIL |
| `NO_EVENT35` | halt without expected hook → INVALID |
| `REPEATED_SEED` | event35 count>1 → INVALID |
| `UNRELATED_EARLY_DEATH` | 8s death without event35 → INVALID |
| `FIXTURE_NOT_BOUND` | event35 without the one-shot fixture → INVALID |
| `INVALID_ENV` | unread / inexact `/proc/X/environ` → INVALID |

Live evidence also writes `no-serial0-oracle.txt` and `serial-state-audit.txt`.

## Static verification

`scripts/verify_r7_11_a07d66c_runner.py` SHA256
`7a7d4f109802f29c6a4c3da52596199c21106687b66cb835d53b8f4a1392999e`

`VERIFIER_PASS`:

- product C/C++ worktree `src/f8-ahb-gatea-r7-hup-preserve` HEAD `a07d66c` clean
- judge unmodified, serial-wrap spec frozen
- generic runner unmodified SHA `36d66f17…8ded` and still REVIEW_REQUIRED
- WAIT_S frozen 12; no timeout relaxation
- no auto retry / auto next / evidence erase
- destination-exists check before mkdir
- VALIDATE_ONLY before harness/ADB/mkdir
- source consume < seed < wrap fatal < EVENT_PUBLISH
- does not invent observed UINT64_MAX
- does not invent prior PUBLISH requirement
- legal `runtime-a07d66c/r7-11` still absent

## Mock tests

`scripts/test_classify_r7_11_serial_wrap.py` SHA256
`9d69aa4fbf2014f2fcd92aaa4d79e572286e30279088b88cec30a14163c47cf9`

12/12 PASS, including frozen judge `need=()` accepts no-prior-publish
`serial-wrap`, rejects `publish_serial_zero` even with correct halt,
rejects `fault_missing`, treats repeated event35 as INVALID.

## Judge regression

`test-judge-r7.py` 16/16 PASS.
Judge SHA unchanged `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17`.

## Tool hashes

| Artifact | SHA256 | Size |
|---|---|---|
| dedicated `run-r7-11-a07d66c.sh` | `74385947cbcef8dbeeb1deea9722b424828d9bf3780a4dd0279290df5310c453` | 25716 |
| generic `run-r7-one-cell-a07d66c.sh` | `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded` | 20529 |
| dedicated `run-r7-09-a07d66c.sh` | `d6ec76c17b42403e426170ab4bbe7fe6800eb92b7a37a966a530255d6873f60d` | 22582 |
| `classify_r7_11_serial_wrap.py` | `3a0af4ff367bf18da2edd0888bda898b10c079c6e0bc93b95e3a111e5dd6b107` | 12825 |
| `verify_r7_11_a07d66c_runner.py` | `7a7d4f109802f29c6a4c3da52596199c21106687b66cb835d53b8f4a1392999e` | |
| `test_r7_11_a07d66c_runner.sh` | `eacc5362d3920977fb02cff1160a4a63b64b708ba43609300b101d3e2a84c3fa` | |
| `test_classify_r7_11_serial_wrap.py` | `9d69aa4fbf2014f2fcd92aaa4d79e572286e30279088b88cec30a14163c47cf9` | |
| `judge-r7.py` | `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17` | 9965 |
| `p_r3_single_direct` | `b424a6340aac9140114ef70b4eb80cdbaa17cf8762b730963b865cd947cd8c13` | 71704 |
| `p_b3a_hold` | `3417abbf0855c10bfd2328e87f33518c2f7f59c42529ba157a847d3019f5b5ca` | 70960 |

## Device mutation audit

```
ADB install = 0
Activity launch = 0
X3 launch = 0
fixture execution = 0
R7-11 fault injection = 0
runtime-a07d66c/r7-11 created = NO
Stable mutation = 0
HDMI mutation = 0
```

## Primary verdict

`R7_11_A07D66C_RUNNER_QUALIFIED`

Meaning: R7-11 remains **NOT RUN**, but the tooling blocker is removed.

Not: R7-11 PASS.

## State after tooling PASS

- R7-09: PASS / frozen
- R7-11: NOT RUN / UNBLOCKED
- R7 overall: IN PROGRESS
- Production Gate A: BLOCKED
- R8/R9/R10: NOT STARTED

## Next grant (do not execute here)

```
SERIAL=<live>
ROOT=.../runtime-a07d66c
CELL_ID=r7-11
FAULT=serial-wrap
FIXTURE=direct
WAIT_S=12
bash evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-11-a07d66c.sh
```

One attempt. No VALIDATE_ONLY. Destination `runtime-a07d66c/r7-11/` must still
be absent at start. Use the dedicated runner. Do **not** use
`run-r7-one-cell-a07d66c.sh` for this cell. Do **not** retry R7-09 or earlier
frozen cells.
