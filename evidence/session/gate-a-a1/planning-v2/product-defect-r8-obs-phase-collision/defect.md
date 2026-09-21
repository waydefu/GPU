# PRODUCT DEFECT — R8_OBS `phase` key collision destroys the observation kind

DATE      2026-09-21
SEVERITY  blocks R8-C1, R8-C5-full, R8-C5-overflow (every cell whose judge calls
          require_obs(x,"X_CHECKPOINT"))
PRODUCT   b984dedcac731b77ca4cf8899f8a78b7848ad083
FILE      lorie/src/main/cpp/lorie/lorie_r8_test.c  (ProcLorieR8Checkpoint, ~L288-L300)
STATUS    EVIDENCE ESTABLISHED — §2.2's "product defect evidence" condition is now met.
          Rebuild/reinstall NOT performed and NOT recommended here; see "Containment".

## The defect
`lorieR8Obs(role, kind, fields)` emits `{... ,"phase":"<kind>", ... ,<fields>}`.
`ProcLorieR8Checkpoint` builds `fields` ending in `"phase":%u` (the checkpoint phase
1..7). The emitted object therefore contains the key `phase` TWICE:

```
R8_OBS {"v":1,...,"phase":"X_CHECKPOINT",...,"registry_count":0,...,"phase":4}
                  ^^^^^^^^^^^^^^^^^^^^^ observation kind      ^^^^^^^^^ checkpoint phase
```
Per JSON semantics every standard parser keeps the LAST duplicate key, so the
observation kind is destroyed at parse time:

```
attempt-10 x-observations.jsonl phase values:
  'X_DESTRUCTOR_ENTER' (str) x10   'X_DESTRUCTOR_EXIT' (str) x10
  'DEFER_ENQUEUE' (str) x6         'DEFER_DISPATCH' (str) x6
  'TEST_CONTROL' (str) x5          ...
  1 (int) x1                       4 (int) x1     <-- the two checkpoints
```
`judge-r8-v2.py obs_kinds()` matches `r.get("phase") == "X_CHECKPOINT"`, which can
never be true. Result: `R8_INVALID MISSING_OBS_X_CHECKPOINT`, deterministically.

The rows are NOT lost — they are present and complete, only mislabelled:
```
seq=31  phase=1  registry_count=0  root_pending=0   (BEGIN)
seq=41  phase=4  registry_count=0  root_pending=0   (POST_FREE)
```

## Second, independent product gap in the same emitter
```c
"\"registry_count\":%u,\"total_actual_buffer_pending\":null,"
```
`total_actual_buffer_pending` is a hardcoded literal `null` — the field is declared but
never populated. `judge_c1` L274-L278 requires it to be non-None and 0:
```python
pending = ck[-1].get("total_actual_buffer_pending")
if pending is None: raise Verdict(INVALID, "PENDING_NOT_OBSERVED")
```
So even with the collision fixed, C1 would next fail `PENDING_NOT_OBSERVED`. This was
found by reading attempt-10's evidence, not by spending attempt-11.

## What the checkpoint DOES provide (real, populated data)
```
registry_count 0      root_pending 0       pair_state 0   pair_src 0   pair_dst 0
readIndex 4           writeIndex 4         completedSerial 4
firstFailed 0         generationFatal 0
```
`readIndex == writeIndex == completedSerial` is a drained GPU copy queue.
`pair_state/src/dst == 0` is no retained pair. Both are meaningful for a pure pair
lifecycle. `registry_count == 0` is NOT meaningful for C1 specifically: C1 never
registers, so it is 0 at BEGIN too — asserting it would be a tautology.

## Containment (why no rebuild is proposed here)
A product change means new PRODUCT_SHA -> CI -> install -> re-proof, and per §13.4
invalidates the b984ded binding that R7 and all frozen R8 evidence rest on. Both
symptoms are recoverable tooling-side without touching the product:

```
collision      collector parses with object_pairs_hook, keeping the FIRST "phase"
               as the observation kind and exposing the duplicate as
               "checkpoint_phase". This RECOVERS information that is present in the
               raw stream and lost only by a naive parse. It is a parser fix, not a
               relaxation of any criterion.
pending:null   judge_c1 must assert residue from fields the product actually
               populates. Choosing which ones is a DESIGN decision (see below) and
               is NOT made here.
```

## Open design question (requires Astra/Sol, do not resolve by running an attempt)
What proves "clean resource balance" for a pure pair lifecycle, given
`total_actual_buffer_pending` is never populated?

Candidate predicate from the data above:
```
root_pending == 0
readIndex == writeIndex == completedSerial      (copy queue drained)
pair_state == 0 and pair_src == 0 and pair_dst == 0   (no retained pair)
generationFatal == 0 and firstFailed == 0
```
This is stronger than asserting a placeholder field and stronger than the
tautological registry_count check. It is still a change to what §7.1 claims C1 proves,
so it needs sign-off before it goes into the judge.
