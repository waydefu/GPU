# D-02 / R9-SUPPORT — IMPLEMENTATION RECORD

DATE 2026-09-22  TREE `src/f8-ahb-gatea-r7-p1-arm` (branch `feat/gatea-r8-lifecycle-support-20260918`, base `14caa7b`)
MODE host-only: source edits + host compile + host tests + offline judge replay.
     NO device, NO adb, NO CI dispatch, NO artifact build.
SEAM as selected in `SEAM-REVIEW.md` (seam C, ABI-layout-neutral reserved word).

## WHAT CHANGED — 9 files, +234 / -12

```
lorie/src/main/cpp/lorie/lorie.h            struct field + assert + 2 accessors
lorie/src/main/cpp/lorie/InitOutput.c       field rename at the single init site
lorie/src/main/cpp/lorie/lorie_r8_test.c    ProcLorieR8Terminate publishes finalize
lorie/src/main/cpp/lorie/renderer.cpp       finalize re-gated; R_EPOCH_END emitted
lorie/src/main/cpp/lorie/activity.cpp       R_EPOCH_BEGIN emitted; Q4-F1 fix
lorie/src/main/cpp/lorie/cmdentrypoint.cpp  Q6-F1 fix (defer tuple before obs)
lorie/src/main/cpp/lorie/lorie_r8_obs.c     tuple-explicit core + epoch API + epoch ids
lorie/src/main/cpp/lorie/lorie_r8_obs.h     API declarations
tests/r8/verify-r8-support.py               +15 static checks, +1 compiled test
tests/r8/test_r8_epoch_obs.c                NEW — 17 behavioural checks
```

## 1. FINALIZATION SEAM (D-02 item 4)

```
lorie.h          `uint32_t pad` at +20 -> `uint32_t runFinalize`, plus
                 lorieGateAPublishRunFinalize() / lorieGateAObserveRunFinalize()
                 (release/acquire). NEW assert: offsetof(runFinalize) == 20.
                 All five pre-existing asserts are literally unchanged.
lorie_r8_test.c  ProcLorieR8Terminate publishes it immediately BEFORE GiveUp(0).
renderer.cpp     lorieR8MaybeFinalizeRendererObs(st) now requires
                 lorieGateAObserveRunFinalize(st) in addition to the three
                 pre-existing quiescence preconditions. All three call sites pass a
                 valid state pointer (`st` at the control drain, member `state` in
                 refreshContext and threadLoop).
```
END authority is therefore **explicit whole-run finalization**, not first-generation
unbind / surface quiesce / first epoch end.

## 2. EPOCH RECORDS (D-02 items 2 and 3)

```
lorie_r8_obs.c   lorieR8ObsTuple()  — emit with an explicit tuple
                 lorieR8ObsEpoch()  — epoch boundary record
                 lorieR8EpochAllocId() / lorieR8EpochCurrentId()
activity.cpp     R_EPOCH_BEGIN at bind  (reason "bind")
renderer.cpp     R_EPOCH_END   at unbind (reason "generation_close")
```
Each record carries `epoch_id`, `epoch_nonce`, `epoch_generation`, `reason`.
`epoch_id` is a renderer-process-local counter, **independent of
`epoch_generation`** — Q2-F2 proved the generation alone cannot express an Activity
boundary.

Two correctness details fixed during implementation:
```
- emission moved OUTSIDE gateABindMutex, so the obs mutex is never nested under
  the bind mutex
- gated on a REAL tuple change, so a duplicate EVENT_SHARED_SERVER_STATE does not
  allocate a spurious epoch
```

### The regression this avoided (found and fixed mid-implementation)
The first draft stamped the epoch tuple into `original_nonce` /
`original_generation`. That would have been a **frozen-contract regression**:
```
judge-r8-v2.py:243-248  tuple_bind() collects (original_nonce, original_generation)
                        from every non-BEGIN/END row, discards rows whose
                        original_nonce is 0, and raises INVALID TUPLE_BINDING if
                        more than one distinct tuple survives.
lorie_r8_test.c:110,201,283   lorieR8BindTuple() is called ONLY on the X side, so the
                        renderer's r8Nonce/r8Generation stay 0.
evidence (runtime-b984ded)    r-stream origins are {(0,0)} in every cell — i.e. every
                        renderer row is discarded by that filter TODAY.
```
Stamping a real nonce would newly admit renderer rows into that assertion and change
the judge's input set for frozen cells. **Fixed:** the epoch tuple lives in the
`epoch_*` columns only; `original_*` keeps its existing provenance meaning. The
property is pinned by a host check (`epoch_original_columns_unchanged`).

## 3. CONTAINED DEFECT FIXES (bundled — one artifact, not three)

```
Q6-F1  cmdentrypoint.cpp  the DEFER_ENQUEUE observation is now emitted AFTER the
                          tuple snapshot is assigned. Previously it printed the
                          calloc'd zeros: 570 of 570 records in the corpus carried
                          nonce=0 generation=0.
Q4-F1  activity.cpp       gateAMappedState is cleared on BOTH unmap paths (peer-HUP
                          :440 and warm reconnect :556). It previously had no clear
                          site at all, and Q1-F2 proved the stale read reachable.
```

## 4. VERIFICATION PERFORMED (all host-only, zero device cost)

### Compilation
```
lorie_r8_obs.c standalone, -Wall -Wextra                       exit 0
test_r8_epoch_obs.c + lorie_r8_obs.c, -Wall -Werror -std=c11   exit 0
verify-r8-support.py header TUs (shared_c/cxx, x_only_c, ...)  pass
```
`renderer.cpp`, `activity.cpp`, `cmdentrypoint.cpp` and `InitOutput.c` need the full
Android/X toolchain and are **NOT** host-compilable. They are covered here only by
static checks; a build is required before any runtime claim.

### Host tests
```
test_r8_epoch_obs.c    NEW   17 checks, 0 failures
test_r8_obs_terminal.py      10 vectors, 0 failures  (the frozen terminal contract)
verify-r8-support.py         +15 new static checks, all passing
```
New static checks: `d02_run_finalize_field`, `d02_run_finalize_offset_assert`,
`d02_testfault_{size,magic,gen_off}_unchanged`, `d02_terminate_publishes_finalize`,
`d02_finalize_requires_publish`, `d02_finalize_still_emits_end`,
`d02_epoch_{begin,end}_emitted`, `d02_{epoch,tuple}_api_present`,
`d02_legacy_obs_unchanged`, `d02_epoch_id_independent`,
`q6f1_defer_tuple_before_obs`, `q4f1_mapped_state_cleared`.

### Offline judge regression — the strongest available evidence
Epoch records were injected into all ten frozen `runtime-b984ded` attempts (correctly
sequenced, `actual_count` adjusted exactly as the product would), then re-collected
and re-judged with the unmodified collector and judge:
```
cell                 baseline                  with epoch records        same?
r8-c1                R8_PASS R8-C1             R8_PASS R8-C1             YES
r8-c2                R8_PASS R8-C2             R8_PASS R8-C2             YES
r8-c3-disconnect     R8_PASS R8-C3-disconnect  R8_PASS R8-C3-disconnect  YES
r8-c3-window         R8_PASS R8-C3-window      R8_PASS R8-C3-window      YES
r8-c4                R8_PASS R8-C4             R8_PASS R8-C4             YES
r8-c5-full           R8_PASS R8-C5-full        R8_PASS R8-C5-full        YES
r8-c5-overflow       R8_PASS R8-C5-overflow    R8_PASS R8-C5-overflow    YES
r8-d                 R8_PASS R8-D              R8_PASS R8-D              YES
r8-p1                R8_PASS R8-P1             R8_PASS R8-P1             YES
r8-p2                R8_PASS R8-P2             R8_PASS R8-P2             YES
```
**10/10 identical.** The frozen evidence itself was never modified — every run was
made on a scratch copy.

## 5. PRE-EXISTING HOST FAILURES — NOT CAUSED BY THIS WORK

`verify-r8-support.py` is RED at HEAD, before any D-02 change, on three checks:
```
collector_unchanged   sha256(tests/r8/collect-r8.py) != FROZEN_COLLECTOR_SHA
                      actual: c2d4013bbf6fb2532047e97fd1ab6989e3c31a1ddcefcd81ef5a6b4f11f5640b
                      collect-r8.py is UNMODIFIED by this work (`git diff` empty)
judge_vectors_v2      tests/r8/test-judge-r8-v2.py reports failures=5
                      test-judge-r8-v2.py and judge-r8-v2.py are UNMODIFIED here
obs_ingestion         test_r8_obs_ingestion.py 1 failure (PENDING_NOT_OBSERVED);
                      reproduced identically on a pristine `git archive HEAD` tree
```
After this work the verifier still reports **exactly these three and no others**.
They must be resolved before the build/CI step, but they are a separate matter.

## 6. STOP-CONDITION SELF-CHECK — FINAL

```
Gate A production semantics changed?  NO. Every new site is inside
                                      LORIE_ENABLE_R8_TEST_SUPPORT except the two
                                      contained defect fixes, which change ORDERING
                                      and a NULL assignment only — no Gate A
                                      decision, admission or protocol behaviour.
Frozen R8 contract changed?           NO. Terminal contract untouched
                                      (test_r8_obs_terminal.py 10/10); judge verdicts
                                      identical 10/10; original_* columns unchanged.
New ABI required?                     NO. No size, offset or alignment change; all
                                      five pre-existing static asserts unchanged.
Design-freeze contradiction found?    NO.
```

## 7. WHAT IS EXPLICITLY NOT DONE

```
- NO artifact build, NO CI dispatch, NO install, NO device run.
- renderer.cpp / activity.cpp / cmdentrypoint.cpp / InitOutput.c are NOT compiled
  here; only static checks cover them. A build MUST precede any runtime claim.
- R8 requalification scope is NOT decided. The offline replay above is evidence FOR
  a narrow scope, not the touched-semantics audit itself (method: GAP-4).
- The three pre-existing host failures are NOT fixed.
- No commit, no push. The worktree carries the changes.
```

## 8. REMAINING CHAIN

```
[done] source implementation
[done] static/host tests
[next] P009
[next] build / CI
[next] artifact bind
[next] affected observation regression on the real artifact
       (the offline replay above is the host-side pre-check, not a substitute)
[then] R9 runtime design
```
