# R8 SMOKE ON THE NEW ARTIFACT — RESULT

DATE 2026-09-22
SCOPE 2 cells (R8-D, R8-P2), as recommended by `touched-semantics-audit/AUDIT.md`
      and accepted by ASTRA under D-12.

## OUTCOME

```
R8-D   R8_PASS   runtime-dc94485/r8-d/attempt-01    manifest 55 files
R8-P2  R8_PASS   runtime-dc94485/r8-p2/attempt-01   manifest 53 files
```

## THE SMOKE FOUND A REAL REGRESSION — WHICH IS WHY IT WAS RUN

The first artifact (7e3a05e) FAILED the first cell:
```
runtime-7e3a05e/r8-d/attempt-01
  R8_INVALID PRODUCERS_NOT_FINALIZED
  {"x_begin":1,"x_end":1,"r_begin":1,"r_end":0,...,"r_unbound_final":true}
```
Cause: the renderer END was gated on `lorieGateAObserveRunFinalize(st)` evaluated AT
the terminal. But `R_SURFACE_QUIESCED` is the LAST renderer record (seq 25 of 26,
after `R_UNBOUND_FINAL` at 22 and `R_EPOCH_END` at 23). By then X has terminated, the
Activity has called `setSharedState(NULL)`, and the GL thread has munmap'd the region
and set `state = nullptr`. The read saw NULL and the END never fired.

The seam review had proven the publish/observe ORDERING rigorously (X blocks in
`gateAWaitCleanAck` until the renderer acks, so the renderer must run). It did not
ask the second question: **is the mapping still mapped when the terminal conditions
complete?** It is not.

Fixed in dc94485 by latching: `lorieR8NoteRunFinalize(st)` records the flag the first
time it is visible with a live mapping, and the terminal gates on the latch. Authority
semantics unchanged.

Had the scope been "zero runs", this would have shipped broken.

## MEASURED PROPERTIES ON dc94485

```
                          R8-D              R8-P2
renderer BEGIN / END      1 / 1             1 / 0     <- P2 correct: fatal cell sends
                                                         no TERMINATE, so runFinalize
                                                         is never published and the END
                                                         is correctly SUPPRESSED
R_EPOCH_BEGIN / END       1 / 1             1 / 0
epoch tuple carried       id=1 gen=1        id=1 gen=1     with a real nonce
epoch original_nonce      0                 0         <- MUST stay 0: judge-r8-v2.py
                                                         tuple_bind() discards rows
                                                         whose original_nonce is 0, and
                                                         admitting renderer rows there
                                                         would change the judge's input
                                                         set for frozen cells
DEFER_ENQUEUE records     16                6
DEFER_ENQUEUE tuple       real nonce, gen=1 real nonce, gen=1   <- Q6-F1 FIXED; every
                                                         one of the 570 records in the
                                                         b984ded corpus carried 0/0
judge                     R8_PASS ACCEPT    R8_PASS ACCEPT
```

R8-P2 earned its place in the scope: it is the only cell that proves the new gate does
**not** fire on the fatal path. A gate that fired unconditionally would have passed
R8-D and failed only here.

## WHAT THIS DOES AND DOES NOT ESTABLISH

```
ESTABLISHED  D-02's three goals all work on device: epoch records with their own
             tuple, the Q6-F1 tuple ordering fix, and the finalize re-gate in both
             its firing (R8-D) and non-firing (R8-P2) forms.
             The two production changes audited as unreachable/inert did not alter
             either verdict.
NOT ESTABLISHED
             The other eight cells on dc94485. They were deliberately not run: the
             audit found no cell whose semantics are touched, and the two chosen
             cells cover both production changes plus both terminal shapes.
             If a later finding contradicts the audit, the scope decision is
             revisitable - the audit is recorded, so its reasoning can be checked.
             R9 itself. Nothing here exercises multi-epoch behaviour; only ONE epoch
             occurs per R8 cell. D-02 makes multi-epoch observation POSSIBLE; it has
             not been demonstrated.
```

## PROVENANCE OF THE ATTEMPTS

```
runtime-7e3a05e/r8-d/attempt-01   INVALID, frozen, NOT reclassified (§5.1). It is the
                                  evidence that motivated dc94485 and must be kept.
runtime-dc94485/r8-d/attempt-01   PASS
runtime-dc94485/r8-p2/attempt-01  PASS
```
One additional dc94485 R8-D run exited 3 (`R8_BLOCKED ARTIFACT_MISMATCH_PRESTART`)
before these: the runner was copied with the new APK pins but still pointed at the
b984ded tooling manifest, so the judge compared `artifact-binding.json` against a
b984ded `manifest.json`. Exit 3 means the attempt was NOT consumed, so no frozen
evidence was produced; a manifest pinned to dc94485 was created and the cell re-run.
