# R8-C1 SECOND BLOCKER — judge_c1 requires vectors cell_c1 cannot produce

DATE    2026-09-21
MODE    HOST-ONLY diagnostic on a COPY of attempt-09 evidence. The frozen
        attempt-09 directory was NOT read-write, NOT modified, NOT reclassified.
        Its classification remains INVALID / STABLE_EVIDENCE_MISSING.
CLASS   DESIGN_REQUIRED  (§19.1 Q1 — an architecture decision is needed to continue)

## How this was found without spending an attempt
Runner v4 fixes the STABLE_AFTER ordering. To check whether that fix alone unblocks
C1, attempt-09's evidence was copied to scratch and `judge-r8-v2.py` was re-run
offline against the copy (output written to scratch). Result:

```
v3 ordering (what actually ran)  ->  R8_INVALID STABLE_EVIDENCE_MISSING
v4 ordering (simulated offline)  ->  R8_INVALID DESTRUCTOR_NOT_OBSERVED
```
**The ordering fix alone does not unblock C1.** attempt-10 would have died here.

## The mismatch

`judge_c1()` requires three observation phases:
```
destroy_before_x_release(xrows, rrows)
    needs renderer R_DESTROY_STAGE   -> absent
    needs renderer R_ACK_SETTLED     -> absent
require_obs(xrows, "X_CHECKPOINT")   -> absent
```

What attempt-09 actually produced:
```
x  (47 rows)  X_DESTRUCTOR_ENTER 10 · X_DESTRUCTOR_EXIT 10 · DEFER_ENQUEUE 6
              DEFER_DISPATCH 6 · X_WAKE_RECEIVED 4 · RECHECK 4 · TEST_CONTROL 2
              BEGIN · X_CLOSE_ENTER · X_TERMINAL_WAIT_ENTER · X_CLOSE_RESULT · END
r  (9 rows)   BEGIN · R_WAKE_SENT 5 · R_UNBOUND_FINAL · R_SURFACE_QUIESCED · END
```
The x stream is rich and complete. The renderer stream is complete and finalised
(`r_begin=1 r_end=1 r_unbound_final=true`, END digest present) — it simply contains
no destroy staging.

## Root cause — the fixture and the judge disagree about what C1 IS

All three phases exist in product `b984ded`:
```
R_DESTROY_STAGE  lorie/src/main/cpp/lorie/renderer.cpp      (emitted when a REGISTERED
                                                             renderer resource is destroyed)
R_ACK_SETTLED    lorie/src/main/cpp/lorie/renderer.cpp
X_CHECKPOINT     lorie/src/main/cpp/lorie/lorie_r8_test.c   (emitted only in response to
                                                             an X_LorieR8Checkpoint request)
```
They are not emitted spontaneously. They require the client to send
`X_LorieR8RegisterBuffer` and `X_LorieR8Checkpoint`.

In `p_r8_lifecycle.c`:
```
cell_c1  pair_create -> pair_composite -> pair_free   (x2)     <-- XRender only.
         No r8_query. No r8_register. No r8_checkpoint.
cell_c4  pair_create -> r8_query -> r8_checkpoint(BEGIN)
                     -> r8_register(src) -> r8_register(dst)
                     -> r8_checkpoint(PRE_FREE) -> pair_free
                     -> r8_checkpoint(POST_FREE)                <-- produces all three
```
**`judge_c1` requires exactly the vectors `cell_c4` produces and `cell_c1` does not.**

## Consequence
R8-C1 is **structurally unachievable as currently specified**. This is not a product
defect, not an infra failure, and not a re-runnable condition: no number of attempts
can make `cell_c1` emit a checkpoint it never requests. §7.1 defines C1 as
"clean pair lifecycle + clean test-control terminate"; `judge_c1` additionally demands
registered-resource destruction evidence, which belongs to C4 ("REGISTER_BUFFER only",
§7.5).

## Decision required (Astra / Sol) — two mutually exclusive directions
```
A. Widen the fixture: give cell_c1 r8_query + r8_register + r8_checkpoint.
   Cost: C1 stops being a pure pair lifecycle and overlaps C4; §7.1 must be rewritten;
         the C1/C4 boundary in §2.10 MANDATORY CELL ORDER needs re-derivation.

B. Narrow the judge: drop destroy_before_x_release() and the X_CHECKPOINT requirement
   from judge_c1, keeping them in judge_c4.
   Cost: judge/tooling change (v5 + new hashes); must first establish what DOES prove
         clean resource release for a pure pair lifecycle, or C1 proves less than §7.1
         claims it proves.
```
Neither is an executor decision. Both change frozen contracts.
Do not pick one by running another attempt.

## Also worth noting
`judge_c1` reaches `destroy_before_x_release()` and `X_CHECKPOINT` only AFTER
`check_stable()` passes. Every runner since 5a782f6 failed at `check_stable()`, so
this second mismatch has been hidden behind the first for six runner generations and
eight attempts. It was never a product problem.
