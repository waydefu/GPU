# TOUCHED-SEMANTICS AUDIT — b984ded -> 7e3a05e

DATE 2026-09-22  MODE host-only, read-only. No device, no install, no runtime.
PURPOSE Decide the R8 requalification scope for the new PRODUCT_SHA (D-12).
METHOD  GAP-4's: enumerate touched symbols, classify production reach, then test
        each production-reaching change against what the ten R8 cells actually assert.

## 1. THE PRODUCT DELTA IS EXACTLY ONE COMMIT

```
git merge-base --is-ancestor b984ded 7e3a05e   -> YES, linear
commits in b984ded..7e3a05e, by product reach (files under lorie/, i.e. in the APK):
  7e3a05e  R9: multi-epoch renderer observation (D-02) + 2 fixes   lorie/ files = 8
  14caa7b  R8: composite with PictOpOver                           lorie/ files = 0
  2b6f9f0  R8: fix judge/fixture contract defects                  lorie/ files = 0
  2a14ab2  R8: count collector jsonl as the sole observation       lorie/ files = 0
```
The three intervening commits touched only `tests/`, which is why PRODUCT_SHA stayed
at b984ded. **The entire binary delta is 7e3a05e.**

## 2. GUARD CLASSIFICATION OF EVERY ADDED LINE

Each added line was tested for membership in a
`#ifdef LORIE_ENABLE_R8_TEST_SUPPORT` block by walking the preprocessor stack of the
post-image:

```
file                added   inside #ifdef   outside
lorie_r8_obs.c         63         63            0
lorie_r8_obs.h         11         11            0
lorie_r8_test.c         9          9            0
renderer.cpp           23         23            0
activity.cpp           29         17           12
cmdentrypoint.cpp      10          0           10
lorie.h                31          0           31
InitOutput.c            1          0            1
```

The "outside" lines resolve as follows — only TWO are production statements:

```
InitOutput.c:2586   st->gateATestFault.runFinalize = 0;
                    RENAME of the pre-existing `pad = 0`. Same statement, same
                    position, same value. NOT a new statement.

lorie.h  (31)       comments; the field RENAME `uint32_t pad` -> `uint32_t runFinalize`
                    (identical size/offset/alignment, all five pre-existing static
                    asserts unchanged); one NEW static assert (compile-time only, emits
                    no code); two `static inline` DEFINITIONS whose only callers are
                    inside #ifdef'd sites — an uncalled static inline emits no code.

activity.cpp (12)   four are the `#endif` directives closing the blocks added above
                    (a guard-walk artifact); six are comments;
                    TWO ARE PRODUCTION STATEMENTS -> change A below.

cmdentrypoint.cpp   five are comments;
             (10)   FIVE ARE PRODUCTION STATEMENTS -> change B below.
```

```
=> PRODUCTION DELTA = exactly two changes.
```

## 3. CHANGE A — `gateAMappedState = NULL` at two sites (activity.cpp)

```
reach      gateAMappedState is READ at exactly one site: activity.cpp:418-419,
           inside the peer-HUP handler, guarded by `bound && gateAMappedState != NULL`.
effect     a NULL makes `published` stay 0 instead of dereferencing a pointer whose
           target setSharedState(NULL) has already munmap'd.
ordering   in the HUP handler the READ (:419) precedes the CLEAR (:461) in the SAME
           invocation, so that HUP's own classification is unchanged. Only a LATER
           read — after a connect_ or a previous HUP — can differ.
R8 reach   every one of the ten cells logs exactly GATEA_BIND=1, i.e. a single bind
           per cell and no second connect_. HUP occurs in only two cells:
             r8-p1/attempt-03  HUP=1
             r8-p2/attempt-01  HUP=1
           and in both it is the single terminal HUP, whose read precedes the clear.
verdict    NO REACHABLE BEHAVIOUR CHANGE IN ANY R8 CELL.
```

## 4. CHANGE B — statement reorder in `gateAQueueDeferredRecord` (cmdentrypoint.cpp)

The tuple snapshot (`shared = lorieGateAShared(); queued->nonce/generation = ...`)
moved from AFTER the `#ifdef`'d observation block to BEFORE it.

```
production build   the #ifdef block does not exist, so the moved statements are
                   adjacent either way. The reorder is a NO-OP.
test build         the code the reorder steps over is:
                     lorieR8DeferAllocId()  - touches r8DeferIds under r8ObsMu only
                     snprintf               - local buffer only
                     lorieR8Obs()           - r8ObsMu + __android_log_print only
                     lorieR8WakeReceived()  - r8WakeRecv under r8ObsMu, then obs
                   NONE of them reads or writes `queued` or `shared`.
                   => semantically inert; only the LOGGED VALUES change (0/0 -> real).
judge reach        both judges do `enq = require_obs(xrows, "DEFER_ENQUEUE")`
                     judge-r8.py:353,  judge-r8-v2.py:421
                   They assert PRESENCE only. Neither reads nonce or generation from
                   that record. No verdict can depend on the changed values.
R8 reach           DEFER_ENQUEUE fires in ALL ten cells (6 to 15 records each), so the
                   change is present everywhere — but only in fields nothing asserts.
verdict            NO REACHABLE VERDICT CHANGE IN ANY R8 CELL.
```

## 5. NEW RECORDS IN THE r-STREAM

D-02 adds `R_EPOCH_BEGIN` / `R_EPOCH_END` to every run. Independently tested by
injecting them into all ten frozen attempts, re-collecting with the unmodified
collector and re-judging with the unmodified judge:
```
10 of 10 verdicts IDENTICAL to baseline (see d02-seam-review/IMPLEMENTATION-RECORD.md)
```
The finalization re-gate is also observationally equivalent: the renderer END now
requires the terminate-published flag, and the END appears today in exactly the eight
cells that send TERMINATE and in neither of the two fatal cells that do not.

## 6. WHAT THIS AUDIT DOES *NOT* ESTABLISH

```
- That the new binary is runtime-identical. It is not: BUILD_ID changed
  (3658dd1f -> ed3e15a9) because native source changed. Codegen and timing are not
  covered by source reading.
- That the frozen R8 corpus transfers. It does not, and it should not: the ten frozen
  attempts remain bound to b984ded. Any run on 7e3a05e is a NEW attempt against a NEW
  PRODUCT_SHA, whatever this audit concludes.
- Anything about R9 behaviour. This audit is scoped to R8 regression only.
```

## 7. CONCLUSION AND RECOMMENDED SCOPE

```
FINDING    No R8 cell's SEMANTICS are touched. Both production changes are either
           unreachable within an R8 cell's lifecycle (A) or confined to fields no
           judge asserts (B). A full 10/10 requalification is NOT justified by the
           source delta.

BUT        the binary is genuinely different, and every cell's r-stream gains new
           records. "Zero runs" would rest entirely on source reasoning, with no
           measurement on the new artifact at all.

RECOMMENDED  a 2-cell smoke scope, chosen for coverage rather than count:
  R8-D    the deferred-path cell and the heaviest DEFER_ENQUEUE producer (15 records),
          so it exercises change B directly, and it is the cell whose judge reads the
          DEFER_* phases at all.
  R8-P2   the only coverage of change A's reachable path (HUP=1), and it is also the
          fatal-terminal cell, where the new END gating must NOT produce a renderer
          END. If the re-gate were wrong, P2 is where it shows.

  Together they cover: both production changes, the epoch records, the finalize
  re-gate in both its firing and non-firing forms, and both terminal shapes
  (clean terminate vs fatal halt).

NOT RECOMMENDED
  full 10/10   unjustified by the delta; 8 extra attempts buy no new coverage.
  zero runs    leaves the new artifact entirely unmeasured.

DECISION OWNER  ASTRA/SOL under D-12. This document is the audit input, not the decision.
```
