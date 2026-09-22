# R9 DECISION LOG

§8.6 requires this deliverable to carry the Astra/Sol decisions on **Q10 scope** and
**Q4 ownership**. Both are now taken, plus a third that the implementation forced.
The authoritative records live in plan §23.1-§23.3; this file is the R9-local index
and states what each decision changed for R9 specifically.

## D-01 — Q10 scope / R9 reset policy — **ACCEPTED 2026-09-22**

```
DECISION   V1-Core / R9 launch X with `-noreset`.
           Same-process DE_RESET is OUT OF SCOPE for V1-Core -> DEFERRED.
```
Q10 found that a same-process reset **already exists and is the default**: with no
`-terminate`, the last X client disconnecting raises DE_RESET, which runs
`lorieCloseScreen` -> `gateACloseGeneration()` -> `sessionNonce = 0`, and the nonce
allocator in `OsVendorInit` is then guarded off by `stateFd != -1`. Gate A is
permanently dead while X keeps running, with no fatal and no log line.

`-noreset` sets `dispatchExceptionAtReset = 0`, so the last-client disconnect raises
nothing at all, the dispatch loop never exits, and the clean close never runs.
`GiveUp()` sets DE_TERMINATE directly, so R8's explicit fixture terminate is
unaffected.

**What it changed for R9**
```
- Every R9 packet MUST launch with -noreset. Without it, any "Gate A inactive"
  observation is unattributable, and R9's long-lived X makes that likely.
- V2-R9-RESET is removed from the packet set (see r9-cell-spec.json).
- R8's frozen corpus was run WITHOUT -noreset, so R8 and R9 evidence are
  configuration-distinct on this axis and must not be pooled.
```

## D-02 — Q4 ownership / multi-epoch renderer observation — **ACCEPTED, IMPLEMENTED, SMOKED**

```
DECISION   R8 process-level BEGIN/END unchanged.
           R9 epochs are ORDINARY semantic phase records (R_EPOCH_BEGIN / R_EPOCH_END),
           not a second terminal stream.
           Each epoch carries epoch_id / epoch_nonce / epoch_generation / reason.
           Renderer END authority moves to explicit whole-run finalization.
           Exact control transport deliberately NOT frozen at decision time.
```
Q4-F3 found the renderer observation terminal was **one-shot per process**: two of its
three preconditions are never-cleared latches, and `lorie_r8_obs.c` drops every record
after the terminal, classifying it `R8_INVALID POST_END_OBSERVATION`. R9 spans
generations inside one process, so epoch 2 onward could never have been observed.

**What it changed for R9**
```
- Multi-epoch observation is now POSSIBLE. It is not yet DEMONSTRATED: each R8 cell
  contains exactly one epoch, so the smoke proved the records exist and are correctly
  shaped, nothing more.
- epoch_id is independent of epoch_generation, because Q2-F2 proved (nonce, generation)
  cannot express an Activity boundary. The identity contract depends on this.
- The seam chosen was a previously-unused reserved word in struct LorieGateATestFault
  (+20). ABI-layout-neutral; all five pre-existing static asserts unchanged.
```

**Implementation note worth carrying forward.** The first artifact (7e3a05e) gated the
END on a flag read AT the terminal and failed R8-D with
`R8_INVALID PRODUCERS_NOT_FINALIZED`. `R_SURFACE_QUIESCED` is the last renderer
record; by then X has died, the Activity has called `setSharedState(NULL)` and the GL
thread has munmap'd the region. The seam review had proven the publish/observe
**ordering** rigorously but never asked whether the **mapping was still mapped** when
the terminal conditions complete. dc94485 latches the flag when first visible.
`runtime-7e3a05e/r8-d/attempt-01` stays INVALID and frozen — it is the evidence for
the fix.

## D-12 — new PRODUCT_SHA for R9 product support — **ACCEPTED 2026-09-22**

```
DECISION   Accept the new PRODUCT_SHA. R8 historical evidence is neither re-judged nor
           revoked. Any R8 requalification scope is decided by a touched-semantics
           audit, NOT assumed.
```
The audit found the product delta is exactly one commit and that the production delta
is exactly two changes, neither reachable in a way that alters any R8 verdict. Scope
was set to 2 cells (R8-D, R8-P2); both PASS on dc94485.

**What it changed for R9**
```
- §8.7 #5/#6/#7 (PRODUCT-SUPPORT / CI / INSTALL) are no longer conditional. Done.
- INSTALLED product is dc94485; b984ded remains the authority for all R7 and
  pre-2026-09-22 R8 evidence. The two are not poolable.
```

## Decisions still OPEN that R9 will hit

```
D-04  resource leak disposition            triggered at V2-R10-AGG, not R9
D-05  carry-forward approval (R0-R7)       needed for P2 closure, not R9
D-06  production lifecycle redesign scope  Gate A workload; Q4/F2 and Q5 feed it
      (the READY GL objects have no teardown outside UNREGISTER and the EGL context
       never turns over, so only process death reclaims them)
```
None of these blocks a WARM or COLD packet.

---

## 2026-09-22 — R9-COLD-2 REMOVED (CONTRADICTION_FOUND)

**Decision.** R9-COLD-2 is reclassified **SOURCE-PROVEN / RUNTIME-NOT-CONSTRUCTIBLE**
and removed from the R9 device packet, on the same terms the user set for
R9-WARM-1/2/3: not PASS, not FAIL, not INVALID, not runtime-qualified. The runtime
packet is `[R9-F1, R9-F2]`.

**Why.** Its expected fatal `x-bump-unterminal` (`cmdentrypoint.cpp:391`) needs a
second `lorieActivityConnected()` with `generation != 0`, and no X process can reach
one. Full proof with `file:line` throughout:
`planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md`. In one line: X outlives its Activity
only when `lorieGateAActive()` is already false, a clean close zeroes `sessionNonce`
as well as `generation`, and every fatal publisher that would clear the gate exits the
X process in the same breath — X-side through `lorieGateAFatalHalt`'s `_exit(127)`,
renderer-side because all 14 publish sites fire while X is inside `gateAWaitTerminal`
for that same serial.

**What it retracts.** `COLD1-ROUTE-SEARCH.md`'s preamble claimed conditions 1-4 and 6
were satisfied by any published renderer fatal. Condition 3 was written as "X does NOT
take the x-eof fatal", which is true and beside the point: X takes
`x-direct-not-success` instead and exits 127. Corrected in place, with the correction
banner naming this document.

**What it strengthens.** The product-level finding moves from *"every generation
boundary in a surviving X requires a prior fatal"* to *"**there is no reachable
generation boundary at all**"*. `generation` is set to 1 by the first Activity connect
and can never advance. Corroboration, not proof: across every Gate A run in
`evidence/` — 201 989 `GATEA_EVENT` lines — `generation` has never been observed above
1. `lorieGateARegistryCloseGeneration` has no runtime caller; `x-bump-unterminal` and
`x-share-in-lease` are defensive-only. This belongs to **D-06** and is recorded, not
decided.

**Frozen attempts are untouched.** `runtime-dc94485/r9-cold-2/attempt-01` and
`attempt-02` stay frozen INVALID. A removal does not reclassify a consumed attempt.
attempt-02 is in fact corroborating evidence for the removal: with no composite ever
issued, `am force-stop` alone produced `GATEA_FATAL_HALT what=x-hup reason=6` on the X
process.

**Enforcement.** `judge-r9.py` keeps a `judge_removed()` refusal for all six removed
cells: they return `R9_BLOCKED` and can never yield PASS, FAIL or INVALID, even when
handed evidence that would previously have passed (vectors R01-R08).
`verify-r9-support.py` gained a **COLD-2 reopen guard** pinning the six source facts
the removal rests on — a failure there means the removal is no longer justified and
the cell must be reopened, not that the tooling regressed.

**Reopen condition.** A renderer fatal publisher reachable outside an X terminal wait,
**or** a warm reconnect/rebind entry point. Either restores a second
`lorieActivityConnected()`, and with it both `x-bump-unterminal` and
`x-share-in-lease`.
