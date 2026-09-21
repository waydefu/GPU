# V2-R8-AGG — R8 AGGREGATE **PASS**, 10/10

DATE 2026-09-21   PRODUCT `b984ded` (unchanged, never rebuilt)   TOOLING `2a14ab2` + v11 amendments

## Cells (all under one tooling generation, v11)
| cell | attempt | verdict | stable | residue |
|---|---|---|---|---|
| R8-C1 | attempt-13 | PASS | before==after | NO_X3_RESIDUE |
| R8-C2 | attempt-03 | PASS | before==after | NO_X3_RESIDUE |
| R8-C3-window | attempt-04 | PASS | before==after | NO_X3_RESIDUE |
| R8-C3-disconnect | attempt-03 | PASS | before==after | NO_X3_RESIDUE |
| R8-C4 | attempt-03 | PASS | before==after | NO_X3_RESIDUE |
| R8-C5-full | attempt-04 | PASS | before==after | NO_X3_RESIDUE |
| R8-C5-overflow | attempt-03 | PASS | before==after | NO_X3_RESIDUE |
| R8-D | attempt-04 | PASS | before==after | NO_X3_RESIDUE |
| R8-P1 | attempt-03 | PASS | before==after | NO_X3_RESIDUE |
| R8-P2 | attempt-01 | PASS | before==after | NO_X3_RESIDUE |

## The 12 aggregate checks (§7.11) — re-verified, not collected
```
 1 product binding        PASS  10/10 bound to b984ded…
 2 tooling binding        PASS  10/10 bound to 2a14ab2…
 3 attempt id unique      PASS  10 distinct
 4 no duplicate attempts  PASS
 5 stable before/after    PASS  10/10 identical
 6 unexpected signal      PASS  0 fatal signals across all evidence
 7 fatal expected-only    PASS  only P1 (src=14) and P2 (src=15), exactly one each
 8 no X3 residue          PASS  10/10
 9 evidence hashes        PASS  554 files recomputed and matched
10 judge authority        PASS  one judge-r8-v2.py across all ten
11 collector authority    PASS  one collect-r8.py across all ten
12 tooling amendments     PASS  ledger below; all ten re-run after the last amendment
```

**Production Gate A remains BLOCKED. V1-Core remains NOT QUALIFIED.** R8 is one input
to P2 runtime closure, not a substitute for Gate A (§7.11).

## The finding that matters most

Until v10, `pair_composite()` in the fixture issued `PictOpSrc`. Gate A accelerates
**only** `PictOpOver`:
```c
lorieCanAccelCompositePictures():  if (op != PictOpOver) return FALSE;
```
That check runs before any trace is emitted, so a `PictOpSrc` composite silently took
the CPU fallback. **Every cell that passed before v10 was exercising the software
path, not Gate A.** The evidence is unambiguous:
```
before (PictOpSrc)   ring events: 14, 27, 28, 29, 30 only
after  (PictOpOver)  ring events: 1 REGISTER_READY, 2 LEASE_RESERVED,
                     3/4 UNLOCK_SRC/DST, 5 LEASE_GPU_OWNED, 6 PUBLISH,
                     7 CONSUME_DIRECT, 8 DIRECT_LOOKUP_OK, 10 DRAW_SUBMIT,
                     11 FENCE_SATISFIED, 14 COMPLETED_SERIAL,
                     17 SEMANTIC_SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK,
                     22 PENDING_DEC, 23 LEASE_RELEASE, 24/25 UNREGISTER,
                     26 RESOURCE_DESTROY, 27/28 GENERATION_CLOSE/CLOSED
```
This also resolved GAP-9: `EVENT_LEASE_GPU_OWNED` had zero occurrences because the
lease path was never entered, which is why P1/P2 reported GPU_OWNED_NOT_CONSTRUCTED.
It was never an environment limitation.

**Any R8 result predating runner v10 must be read as a CPU-fallback result.** The
ten cells above were all re-run after the change; earlier attempts stay frozen as
historical and are not part of this aggregate.

## Tooling amendment ledger (check 12)
```
v3   F1: verify the installed APK instead of only recording it
v4   STABLE_AFTER captured before the judge (six-generation ordering regression)
v5   D-17: judge_c1 narrowed, cell_c1/cell_c5_overflow gain read-only checkpoints
v6   GAP-8: duplicate-key-safe R8_OBS parse; judge_c1 residue predicate rebound
v7   judge_c3 implements both legal C3 traces (§7.3 / presentproto)
v8   cell_c5_full / cell_c5_overflow put_image backing buffers
v9   cell_d drain replaced with deterministic round-trip syncs
v10  pair_composite PictOpSrc -> PictOpOver   <-- the path correction above
v11  parse_events collapses byte-identical duplicate producer records
```
Each amendment invalidated the cells run before it; that is why all ten were re-run
under v11. No amendment relaxed a predicate: v5/v6/v7 replaced unsatisfiable or
single-branch assertions with ones the product can actually satisfy, and v11 collapses
two copies of one record rather than tolerating two records.
