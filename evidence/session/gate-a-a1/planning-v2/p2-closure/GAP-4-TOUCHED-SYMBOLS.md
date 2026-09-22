# GAP-4 — touched-symbol / touched-semantics diff, and the CF-PENDING rulings

DATE 2026-09-23  CURRENT ARTIFACT `dc94485a7ef4f74cada36ea3c1d35d0aa0f48693`
TOOLS `tests/p2/touched_symbols.py`, `tests/p2/verify_r7_predicates.py`, `tests/p2/p2_scan.py`
STATUS **GAP-4 CLOSED · CF-PENDING-001 CLOSED · CF-PENDING-002 CLOSED**

---

## 0. THE FIRST THING THE SCAN FOUND WAS THAT THE QUESTION WAS WRONG

`CF-PENDING-001` is written as:

> R7 PASS 13/13 取得於 `a4c8177f…`

**That is not what the evidence says.** `p2_scan.py` over the whole tree puts R7's
thirteen PASSes on **four different artifacts**:

```
a07d66c   9   r7-01 02 03 05-requalification-01 06 07 08 09 11
8545b26   1   r7-10
a4c8177   2   r7-p1-validity-02, r7-p2
fdfb1ce   1   r7-04-requalification-01
```

In commit order: `fdfb1ce`(09-16) → `8545b26`(09-17) → `a07d66c`(09-17) →
`a4c8177`(09-18) → `b984ded`(09-18) → `dc94485`(09-22). Three of those four are
themselves Gate A fatal-semantics fixes — "preserve authoritative fatal",
"contain renderer peer death as x-hup", "preserve fatal identity across renderer
HUP" — so R7 was qualified **along a repair chain**, not at one point on it.

The three `R7_FAIL` records in the tree are the superseded halves of that chain
(r7-04 FAIL on `7549e36` → PASS on `fdfb1ce`; r7-10 FAIL on `a07d66c` → PASS on
`8545b26`; r7-05 FAIL on `fdfb1ce` → PASS on `a07d66c`). They stay frozen and are
not re-judged.

So GAP-4 is not one diff. It is four, and asking only about `a4c8177 → b984ded`
would have carried eleven cells on a premise that never covered them.

## 1. THE DIFFS

`touched_symbols.py` separates production source from test tooling and, for every
added line, records whether it sits under `#ifdef LORIE_ENABLE_R8_TEST_SUPPORT`.

```
a4c8177 → b984ded   product files 11   added outside guard 102   under guard 1024   removed/modified 12
b984ded → dc94485   product files  8   added outside guard  54   under guard  142   removed/modified 12
```

Every line outside the guard, and every removed or modified line, was read
individually. The tool reports where they are; it does not decide whether they are
safe, and this section is the deciding.

### 1.1 `a4c8177 → b984ded` — production semantic change: **NONE**

All twelve removals and all 102 non-guard additions fall into three kinds:

```
pure refactor, return value unchanged
  InitOutput.c:1230,1262-63   `return pScreen->CloseScreen(p)` -> `ret = ...; return ret`
  InitOutput.c:1605-06,1617   same shape in lorieTryScheduleGpuPresentCopy
  InitOutput.c:3424,3436      single-statement `if` becomes a block, and the #else
  InitOutput.c:3440,3451      branch keeps gateAXFatal("x-destroy-in-lease") and
                              gateACloseGeneration() unchanged
  cmdentrypoint.cpp:781,794   loop body gains braces
forward declarations         InitOutput.c:1587, 2017
read-only observation        buffer.c:61-63 / buffer.h:132
                              LorieBuffer_gpuCopyPendingCount, a getter with no caller
                              that changes behaviour
rename with identical body   renderer.cpp:163-175
                              notifyGpuCopyDoneCause(cause) outside the guard is
                              byte-for-byte the old notifyGpuCopyDone: same
                              lorieEvent, same lorieActivitySendLegacyRecord. The old
                              name is kept as a wrapper. The four call sites
                              (1641, 1657, 2025, 2301) pass a cause string that only
                              the guarded lorieR8WakeSent reads.
struct field addition        lorie.h:1333 area — r8LocalId / r8Type, under the guard,
                              in struct LorieDeferredLegacyRecord. That is an X-side
                              heap record, NOT the cross-process
                              lorie_shared_server_state, so it carries no ABI risk.
```

### 1.2 `b984ded → dc94485` — production semantic change: **ONE**

```
Q4-F1   activity.cpp:461 and :577    gateAMappedState = NULL on both unmap paths
        This IS a behaviour change, and it is a FIX: without it the pointer outlived
        its mapping and the peer-HUP read could dereference unmapped memory.
Q6-F1   cmdentrypoint.cpp:747-751    the tuple snapshot MOVED ahead of the obs block.
        The diff shows the same five lines removed and re-added earlier. The values
        queued->nonce / ->generation end up identical; only the moment they become
        observable changed. gateADeferredTupleStillValid reads the same values.
        NOT a semantic change.
        (570 of 570 records in the runtime-b984ded corpus had printed the calloc'd
        zeros, which is what made it worth moving.)
runFinalize
        lorie.h  a renamed `pad` at offset 20, pinned by a static assert, plus two
        accessors used only by test support. InitOutput.c:2586 initialises it inside
        lorieGateATestFaultPublishFromEnv, past `if (!faultSet && !armSet) return;`,
        so it is unreachable unless a test fault is armed. NOT a semantic change.
```

> An earlier write-up (`p2-r9-artifact/touched-semantics-audit/`) called this "exactly
> 2 changes". That counted the two assignment sites. Counting distinct semantic
> changes it is one fix appearing on two paths. Same finding, different unit; the
> earlier document is not wrong, and is not superseded.

## 2. THE TOOL WAS WRONG FIRST, AND THAT MATTERS

`verify_r7_predicates.py` initially reported every R7 cell INTACT — and also reported
cell 14 `x-destroy-in-lease` INTACT on `dc94485`, which is the one case where the
token demonstrably moved into an `#else` branch. A control that cannot fail is not a
control.

The defect was the guard model. `guard_map` answers "was this written under the
guard", and correctly calls an `#else` **not** guarded. But the experimental APK is
built with `-DLORIE_ENABLE_R8_TEST_SUPPORT=ON` (`lorie/build.gradle:41`), so under
that build the `#else` branch is **not compiled at all**. The question a predicate
check needs is "does this line exist in the shipped binary", which is the opposite
answer for an `#else`.

`compiled_map(guard_on=True)` was added for that question. With it, cell 14 reports
`sites=2 (live 1)`: `InitOutput.c:3434` is present in source but absent from the
build, and `:3911` is the one that survives. The control now discriminates.

**Every conclusion in §3 was re-derived after this fix.** The audit trail of the
wrong version is kept here deliberately.

## 3. RULINGS

### CF-PENDING-001 — R7 → `dc94485`: **CARRY_FORWARD**

A PASS is only as portable as the predicate it was judged against. `judge-r7.py`'s
`CELLS` table pins, per cell, a (fault index, expected halt token, expected reason).
Checked against `dc94485` for cells 1-13, reading the fault table out of the
product's own `gateATestCellNames`:

```
13 of 13  PREDICATE_INTACT
          every expected halt token still exists, every one has at least one site
          that survives the -DLORIE_ENABLE_R8_TEST_SUPPORT=ON build, and every fault
          index still maps to the same fault name
```

Stronger than source-proof, four of those predicates have been **reproduced on
`dc94485` on the device**, by packets run for other reasons:

```
cell 8   r-test-fatal-pre-fence r6   R10-E1 (r10-e-02), same fault name armed
cell 9   x-wrong-generation r6       R9-F1 (r9-f1/attempt-03)
cell 10  x-hup r6                    observed in the R9/R10 corpus
cell 13  x-hup r6                    same token
```

Combined with §1 — zero production semantic change from `a4c8177` to `b984ded`, and
one fix from `b984ded` to `dc94485` that removes a use-after-unmap on the Activity's
HUP path — nothing R7 measured has moved. **CARRY_FORWARD, all 13 cells, no
REVERIFY required.**

Claim scope carried with it, unchanged: R7 cells 1-13 only. Cells 14-16 were never
R7's and are not covered by this ruling.

### CF-PENDING-002 — R0–R6 → `dc94485`: **CARRY_FORWARD, with one REVERIFY**

R0–R6 predate this repair chain entirely. Their exposure is the §1 delta, and the
only production semantic change in it is Q4-F1, on the Activity's unmap paths.

```
R0  installed artifact binding       NOT_APPLICABLE as a carry-forward: it is
                                     re-established per artifact and dc94485's
                                     binding is recorded in every R9/R10 attempt
R1  off-mode regressions             CARRY_FORWARD. Gate A off; Q4-F1 is inside
                                     gateA unmap paths that off-mode never enters
R2  imported AHB rejection           CARRY_FORWARD. Admission-side; untouched
R3  x-pump / drain / terminal        CARRY_FORWARD. The four p2-r3-* packets are
                                     X-side pump behaviour; Q4-F1 is Activity-side
R4  R5  R6                           CARRY_FORWARD on the same ground
REVERIFY                             the peer-HUP path itself, because that is where
                                     Q4-F1 lands
```

That REVERIFY is **already satisfied on `dc94485`** and needs no new run: R10-E2
drove an abrupt X death with nothing published and observed `r-hup reason=6` with the
Activity terminating, and R9-F1 drove the published-fatal arm and observed
`GATEA_HUP_PRESERVE` with the Activity terminating. Both HUP arms exercised, both on
the current artifact.

### R8 `b984ded` → `dc94485`: **CARRY_FORWARD**

R8's 10/10 is bound to `b984ded`. The delta to `dc94485` is §1.2: one fix on the
Activity unmap path, plus a moved snapshot and a test-only field.

```
source          no R8 predicate depends on gateAMappedState. R8 judges X-side
                lifecycle: registry, lease, pending, terminal contract.
smoke           R8-D and R8-P2 re-run on dc94485, both PASS
offline replay  the frozen R8 corpus re-judged with the dc94485 tooling: 10/10
                identical
independent     R9 (2/2) and R10 (4/4, 15 clean closes) on dc94485 exercise the same
                registry, lease and close machinery R8 covers, with zero counter
                imbalance
```

**CARRY_FORWARD.** Claim scope unchanged and carried with it: R8's 10/10 ran on the
historical launch configuration **without `-noreset`**, so it makes no claim about
same-process DE_RESET continuity, and R8 evidence must never be pooled with R9/R10
on that axis.

## 4. WHAT THIS DOES NOT DECIDE

```
p2_runtime_closed      still false. §3 closes three carry-forward items; the 17-item
                       ledger has the rest.
D-04                   open. R10 carried activity.maps_count drift to it.
R-30                   open. No fence-fd instrumentation exists.
performance            B.3 telemetry, untouched here.
```
