# R8-C1 attempt-09 — NON-PASS REPORT + RCA

```
PACKET_ID          V2-R8-C1-09
GRANT_REFERENCE    user grant 2026-09-21, conditional on F1 remediation (satisfied: runner v3)
CLASSIFIER         INVALID
DECISION TREE      Q4 HIT — "evidence 不足以形成可信判斷（缺 stable 記錄）"
                   Q1 no (fix is mechanical, no architecture decision)
                   Q2 no (ADB / screen / device all healthy throughout)
                   Q3 no (all preflight dependencies held; artifact verified by v3)
ATTEMPT_CONSUMED   TRUE — runner was invoked and the cell dir was created (§2.9).
                   attempt-09 is frozen as INVALID. Not reclassifiable.
EVIDENCE_PATH      evidence/session/gate-a-a1/p2-r8-runtime/runtime-b984ded/r8-c1/attempt-09
FROZEN             yes — evidence written, judge.rc=2 recorded, nothing modified after the run
NEXT               FREEZE_AND_STOP
NEEDS NEW GRANT    yes
```

## Exact failing predicate
`judge-r8-v2.py` `check_stable()` L180-L183:
```python
after = load_json(ev / "stable-after.json")
if after is None:
    raise Verdict(INVALID, "STABLE_EVIDENCE_MISSING")
```

## Root cause — harness ordering regression, NOT a product defect

```
run-r8-one-cell-b984ded-v3.sh
  L536   python3 "$JUDGE" ...          <-- judge runs, needs stable-after.json
  L557   stable_json ".../stable-after.json"   <-- written 21 lines LATER, in CLEANUP
```
The judge structurally cannot see a file the runner has not written yet. With this
ordering, R8-C1 **cannot return anything except `R8_INVALID STABLE_EVIDENCE_MISSING`**.
It is deterministic, not intermittent.

### The regression is six runner generations old
```
run-r8-one-cell-65938a4.sh       stable-after L297 -> judge L298    CORRECT
run-r8-one-cell-5a782f6.sh       judge L513 -> stable-after L534    REGRESSION INTRODUCED HERE
run-r8-one-cell-2a245b0.sh       judge L514 -> stable-after L535    inherited
run-r8-one-cell-fb4f017.sh       judge L475 -> stable-after L496    inherited
run-r8-one-cell-b984ded.sh       judge L501 -> stable-after L522    inherited
run-r8-one-cell-b984ded-v2.sh    judge L502 -> stable-after L523    inherited
run-r8-one-cell-b984ded-v3.sh    judge L536 -> stable-after L557    inherited (v3 did not introduce it)
```
Since `5a782f6`, **no R8 cell could pass with any of these runners.** attempt-09 is
simply the first run whose lifecycle was clean enough to reach the judge at all;
attempts 02-08 produced no `judge.stdout`, i.e. they died before the judge.
This was missed by `V2-P008`: that packet bound the runner's CLI surface but did not
trace internal step ordering against the judge's required inputs. P008's
`INTERFACE_BOUND` verdict was therefore incomplete.

## What DID succeed — recorded so it is not re-litigated

The lifecycle itself was clean end to end, and the terminal path matched
`V2-P007` RULING-4 exactly:
```
SERVER_TEST_CONTROL_TERMINATE=PASS
  source=LORIE_R8_TERMINATE  opcode=3
  handler=ProcLorieR8Terminate  giveup=GiveUp(0)
x_begin=1  x_end=1  r_begin=1  r_end=1
x_close_enter=true  x_close_result=true  r_unbound_final=true
x_count=47  r_count=9
FIXTURE_EXIT=0   PRODUCERS_FINALIZED   FINALIZED ok
```
This is the first observed end-to-end clean C1 lifecycle on b984ded. It is NOT a PASS
(the judge never got to rule on the product predicates) but it does establish that the
entry point, close sequence and producer finalisation behave as P007 predicted.

## STOP-THE-LINE (§6.6) — none triggered
```
S1 append-only violated .............. NO  (only new files added)
S2 Stable identity before != after ... NO  (pid 8430, cmdline, versionName,
                                            versionCode, lastUpdateTime all identical)
S3 :3 residue after cleanup .......... NO  (x3-residue.txt = NO_X3_RESIDUE)
S4 two runtime evidence sets ......... NO  (attempt-09 is the only runtime dir;
                                            -preflight / -adb-restore are records)
```
The line is not frozen. Stable `:1` was untouched for the entire run.

## Repair (§19.2) — requires a new grant, not performed here
Move `stable_json "$EVIDENCE/stable-after.json"` to immediately before the judge
invocation, restoring the `65938a4` ordering. This is a runner change (v4) and a new
manifest, and it makes the next run attempt-10 — which §26 STOP BOUNDARY forbids
without explicit instruction. Not done.
