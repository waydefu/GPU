# Gate A P2 R7 — a07d66c R7-09 dedicated early-fault runner tooling qualification — 2026-09-17

```
PRIMARY_VERDICT: R7_09_A07D66C_RUNNER_QUALIFIED
CANDIDATE: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82 INSTALLED
R7-08: PASS / FROZEN (not rerun)
R7-09 device cell: NOT RUN / UNBLOCKED
R7 overall: IN PROGRESS
Production Gate A: BLOCKED
Device execution this task: NONE
```

This packet is **tooling only**. It removes the R7-09 generic-runner
`REVIEW_REQUIRED` **tooling** blocker by adding a dedicated expected-fatal-aware
runner. It does **not** execute R7-09. It is **not** `R7_PASS wrong-generation-frame`.

Generic `run-r7-one-cell-a07d66c.sh` remains frozen
`R7_A07D66C_RUNNER_QUALIFIED` and still maps
`r7-09|wrong-generation-frame|direct` as `REVIEW_REQUIRED` / live REFUSE.
Do **not** lift that mapping. Do **not** modify that file.

## Starting authority

- Candidate `a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82` INSTALLED experimental only
- R6 PASS / FROZEN
- B-2 PASS / FROZEN
- R7-04 / R7-05 / R7-01 / R7-02 / R7-03 / R7-06 / R7-07 / R7-08 PASS / FROZEN
- R7 **IN PROGRESS** (8/13 cells closed; not full R7 PASS)
- Next frozen cell was R7-09 / `wrong-generation-frame` **NOT RUN**
- Production Gate A BLOCKED
- Frozen generic runner SHA256 `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded`
- Frozen judge SHA256 `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17`

## Frozen R7-09 contract

| Field | Frozen value |
|---|---|
| CELL_ID | `r7-09` |
| FAULT | `wrong-generation-frame` |
| side | X / 1 |
| enum | 9 |
| fixture argument | `direct` |
| WAIT_S | 12 |
| construction | first inbound Gate A frame; **no PUBLISH prerequisite** |
| expected fatal | `GATEA_FATAL_HALT what=x-wrong-generation reason=6` |
| judge selector | `wrong-generation-frame` `need=()` |
| expected judge | `R7_PASS wrong-generation-frame` |

PUBLISH event6 / CONSUME_DIRECT event7 / DRAW event10 are **not** required.
If they appear, preserve them; do not raise the PASS bar.

## Why generic runner was REVIEW_REQUIRED

`run-r7-one-cell-a07d66c.sh` after X PID + ENV_EXACT:

1. wait socket
2. `sleep 8`
3. if `/proc/$X3` gone → write `DIED_DURING_8S` + `INVALID` exit 9
4. only then holder `p_b3a_hold` until `HOLD READY`
5. then fixture once

R7-09 may fail-stop during READY setup / first inbound Gate A frame, inside that
8-second window, before holder/fixture. The generic path would classify the
**expected** fail-stop as qualification-not-yet-started INVALID. That is a
tooling false-red. REVIEW_REQUIRED stays on the generic runner.

## Injection reachability finding

**YES — event35 can fire before holder/fixture.** Source-proven, not guessed.
No device trial was used.

- `handleGateARecord` (`cmdentrypoint.cpp`) consumes
  `LORIE_GATEA_TEST_WRONG_GENERATION_FRAME=9` on the **first inbound Gate A
  frame**, then `gateAFatalFromInput(FAIL_GENERATION, "x-wrong-generation")`.
- That handler is pumped from `lorieGateAPumpConnection` during
  `gateAWaitForReply` after `lorieGateASendRegister` (`InitOutput.c`
  `gateAEnsureReady` READY setup).
- Frozen design: “FATAL `x-wrong-generation` reason=6 on first inbound Gate A
  frame”. 計畫書: “REGISTER 階段 35”.
- Frozen judge `need=()`.

Therefore fixture/holder `NOT_REACHED` is legal when expected event35 enum=9
side=1 and last halt `x-wrong-generation/6` are observed.

Generation identity is the injected first-inbound-frame branch: event35 carries
incoming `fr->generation`; last halt must remain `x-wrong-generation/6`. The
runner does not re-derive a numeric generation±1 comparison (source injects on
first inbound frame even if the tuple would otherwise match).

## Dedicated runner

Path: `evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-09-a07d66c.sh`

SHA256: `d6ec76c17b42403e426170ab4bbe7fe6800eb92b7a37a966a530255d6873f60d`
Size: 22582 bytes

Classifier:
`scripts/classify_r7_09_early_fail.py`
SHA256: `5b135dbed0adbb9716801caaf27f47860f685b8543a357f332d4fd795609f085`

Only tuple accepted:

```
CELL_ID=r7-09 FAULT=wrong-generation-frame FIXTURE=direct WAIT_S=12
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

## Early-fail state machine

1. Capture `/proc/X/environ` immediately on PID discovery, **before** maps.
   Unread environ → INVALID. Never fabricate `ENV_EXACT`.
2. Observe `WAIT_S=12`. Do **not** `sleep 8` then INVALID.
3. If X dies before the generic 8s startup deadline, freeze evidence and run
   `classify_r7_09_early_fail.py`.
4. `EXPECTED_EARLY_FAIL` (event35 count=1 enum=9 side=1 role=X **and** last halt
   `x-wrong-generation/6`, no forbidden-after-35 / event32 / later publish,
   env exact) → **not** `DIED_DURING_8S INVALID`; continue frozen judge.
   fixture/holder may be `NOT_REACHED`.
5. `UNRELATED_EARLY_DEATH` (missing/wrong event35, wrong halt, covering
   `x-hup`/`r-hup`/other HALT, unexpected signal without expected halt) →
   INVALID fail-closed.
6. `INVALID_ENV` if environ unread or not exact.
7. If X survives the 8s window, continue observation/judge; fixture still not
   required. Best-effort holder/fixture only while X is alive and expected fatal
   is not yet seen.
8. `x-alive` / exit-signal heuristic are pre-cleanup. EXIT_SIGNAL is a logcat
   Fatal-signal heuristic, not waitpid; not fabricated as exit127.

This is expected-fatal-aware, not early-death-tolerant.

## Input validation (host)

`scripts/test_r7_09_a07d66c_runner.sh` SHA256
`56762b0811f62f3a68ed4336eb874fa827f3301e5e57bd834c0a695b3df0590e`

22/22 PASS including:

| Case | Result |
|---|---|
| r7-09 / wrong-generation-frame / direct / WAIT=12 | ACCEPT |
| r7-09 / serial-wrap | REFUSE |
| r7-09 / present | REFUSE |
| r7-11 / wrong-generation-frame | REFUSE |
| r7-08 / r7-10 / r7-p1 / r7-p2 | REFUSE |
| runtime-fdfb1ce / runtime-7549e36 | REFUSE |
| WAIT=30 | REFUSE |
| existing destination | REFUSE, no write |
| VALIDATE_ONLY no mkdir | PASS |
| generic r7-09 still REVIEW_REQUIRED | PASS |
| early expected fatal mock | NOT `DIED_DURING_8S` INVALID; continue_judge |
| early unrelated death mock | INVALID fail-closed |
| `runtime-a07d66c/r7-09` absent | PASS |

## Static verification

`scripts/verify_r7_09_a07d66c_runner.py` SHA256
`0ec8a0e3ba5f3d6f2373693691a1ad53244bdc9e16654d9c49f2491338cd0ca9`

`VERIFIER_PASS`:

- product C/C++ worktree `src/f8-ahb-gatea-r7-hup-preserve` HEAD `a07d66c` clean
- judge unmodified
- generic runner unmodified SHA `36d66f17…8ded` and still REVIEW_REQUIRED
- WAIT_S frozen 12; no timeout relaxation
- no auto retry / auto next / evidence erase
- arbitrary early death is not PASS
- destination-exists check before mkdir
- VALIDATE_ONLY before harness/ADB/mkdir

## Mock tests

`scripts/test_classify_r7_09_early_fail.py` SHA256
`cce16f09e9c5a96e12068d3f05dd221d9230caaaa35f4f1f91f3c9effaa9c904`

11/11 PASS, including frozen judge `need=()` accepts no-publish
`wrong-generation-frame`, rejects `fault_missing` and `fault_cell_or_side`,
dump-only event35 still expected, covering later `x-hup` is NOT expected early
fail.

## Judge regression

`test-judge-r7.py` 16/16 PASS.
Judge SHA unchanged `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17`.

## Tool hashes

| Artifact | SHA256 | Size |
|---|---|---|
| dedicated `run-r7-09-a07d66c.sh` | `d6ec76c17b42403e426170ab4bbe7fe6800eb92b7a37a966a530255d6873f60d` | 22582 |
| generic `run-r7-one-cell-a07d66c.sh` | `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded` | 20529 |
| `classify_r7_09_early_fail.py` | `5b135dbed0adbb9716801caaf27f47860f685b8543a357f332d4fd795609f085` | 9121 |
| `verify_r7_09_a07d66c_runner.py` | `0ec8a0e3ba5f3d6f2373693691a1ad53244bdc9e16654d9c49f2491338cd0ca9` | 10223 |
| `test_r7_09_a07d66c_runner.sh` | `56762b0811f62f3a68ed4336eb874fa827f3301e5e57bd834c0a695b3df0590e` | 8258 |
| `test_classify_r7_09_early_fail.py` | `cce16f09e9c5a96e12068d3f05dd221d9230caaaa35f4f1f91f3c9effaa9c904` | 6524 |
| `judge-r7.py` | `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17` | 9965 |
| `p_r3_single_direct` | `b424a6340aac9140114ef70b4eb80cdbaa17cf8762b730963b865cd947cd8c13` | 71704 |
| `p_b3a_hold` | `3417abbf0855c10bfd2328e87f33518c2f7f59c42529ba157a847d3019f5b5ca` | 70960 |

## Device mutation audit

```
ADB install = 0
Activity launch = 0
X3 launch = 0
fixture execution = 0
R7-09 fault injection = 0
runtime-a07d66c/r7-09 created = NO
Stable mutation = 0
HDMI mutation = 0
```

## Primary verdict

`R7_09_A07D66C_RUNNER_QUALIFIED`

Meaning: R7-09 remains **NOT RUN**, but the tooling blocker is removed.

Not: R7-09 PASS.

## State after tooling PASS

- R7-08: PASS / frozen
- R7-09: NOT RUN / UNBLOCKED
- R7 overall: IN PROGRESS
- Production Gate A: BLOCKED

## Next grant (do not execute here)

```
SERIAL=<live>
ROOT=.../runtime-a07d66c
CELL_ID=r7-09
FAULT=wrong-generation-frame
FIXTURE=direct
WAIT_S=12
bash evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-09-a07d66c.sh
```

One attempt. No VALIDATE_ONLY. Destination `runtime-a07d66c/r7-09/` must still
be absent at start. Use the dedicated runner. Do **not** use
`run-r7-one-cell-a07d66c.sh` for this cell. Do **not** retry R7-08 or earlier
frozen cells.
