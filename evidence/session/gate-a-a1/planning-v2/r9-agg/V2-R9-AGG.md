# V2-R9-AGG — R9 LIFECYCLE PACKET, AGGREGATE RESULT

DATE 2026-09-22  PRODUCT `dc94485a7ef4f74cada36ea3c1d35d0aa0f48693`
APK `1bd8bef0909249737ea43acf0a35f3c995d941e1badbfcf370e5cd854f4bb8a3`
CI 35673085569  SPEC `tests/r9/r9-lifecycle-cell-spec.json` (`R9_CELL_SPEC_FROZEN_V2`)

## RESULT

```
R9 DEVICE PACKET: 2 of 2 PASS
REMOVED AS SOURCE-PROVEN / RUNTIME-NOT-CONSTRUCTIBLE: 6
NO FAIL. NO BLOCKED. NO UNRESOLVED CELL.
```

| cell | verdict | attempt | expected outcome | observed |
|---|---|---|---|---|
| R9-F1 | **R9_PASS** | `r9-f1/attempt-03` | `x-wrong-generation` reason 6 | `GATEA_FATAL_HALT what=x-wrong-generation reason=6` |
| R9-F2 | **R9_PASS** | `r9-f2/attempt-02` | new nonce, empty registry, `event=5`, no fatal | all four |

The Stable lane was untouched by every attempt: `com.termux.x11` pid 20881 on `:1`,
byte-identical `stable-before.json` / `stable-after.json` in all six runs that reached
the after-capture. ADB lane 5038 only; 5037 never killed or reused.

## WHAT R9-F1 PROVES

Fault 16 (`stale-ready-replay`) makes the renderer send a second READY with
`(nonce-1, generation-1)` after the legitimate one (`renderer.cpp:674-679`). X
receives it, `gateAFrameTupleMatch` fails, and X halts:

```
GATEA_VALIDATE ... bufferId=6 stage=READY_SEND_RETURN result=1     the legitimate READY
GATEA_EVENT ... role=2 event=35 ... src=16 dst=2                   the fault firing, cell 16
GATEA_VALIDATE ... bufferId=6 stage=VALIDATE_TERMINAL_READY result=1
GATEA_FATAL_HALT what=x-wrong-generation reason=6                  cmdentrypoint.cpp:640-641
```

The halt IS the pass. §8.8 forbids concluding PASS from the absence of harm, and the
silent-drop trap is checked separately: `handleGateARecord` returns before the tuple
check when Gate A is inactive (`cmdentrypoint.cpp:631-632`), so a dropped frame is
`INVALID_CONSTRUCTION`. It was not dropped — `x-wrong-generation` is only reachable
past that gate.

## WHAT R9-F2 PROVES

A genuinely fresh session recovers completely from F1's fatal:

```
x_pid            24295 -> 30656          new X process
activity_pid     15036 -> 27379          new Activity process
shared_nonce     14133237869424124691 -> 15990518995061823726
registry         x_entries 0, renderer_ready_entries 0   (from REGISTER_READY/UNREGISTER_ACK)
ring             event=5 LEASE_GPU_OWNED present, once
halts            none
```

`f1-precondition.json` was resolved from F1's own `judge.json` verdict, not from a
logcat, and points at `r9-f1/attempt-03`. §8.8: without F1's expected fatal, F2 is
BLOCKED and manufacturing another fatal is forbidden. It was not manufactured.

## THE SIX REMOVED CELLS

Each is **SOURCE-PROVEN / RUNTIME-NOT-CONSTRUCTIBLE** — not PASS, not FAIL, not
INVALID, not runtime-qualified — and each names the condition that reopens it.

```
R9-WARM-1/2/3   no product entry point for a warm reconnect/rebind
R9-COLD-1/3     no drivable published renderer fatal with a TERMINAL registry
                planning-v2/r9-fixture/COLD1-ROUTE-SEARCH.md
R9-COLD-2       x-bump-unterminal needs a SECOND lorieActivityConnected() with
                generation != 0, and no X process can reach one
                planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md
```

`judge-r9.py` refuses all six with `R9_BLOCKED` and cannot return PASS, FAIL or
INVALID for them even when handed evidence that would previously have passed (test
vectors R01-R08). `verify-r9-support.py` carries a reopen guard pinning the source
facts each removal rests on; a failure there means the removal is no longer justified,
not that the tooling regressed.

**No attempt was burned on any of the six**, except the two already spent on COLD-2
before the proof existed, which stay frozen INVALID.

## THE PRODUCT-LEVEL FINDING — D-06

> **Gate A has no reachable generation boundary at all.**

The bump path (`InitOutput.c:565-589`) is correctly built and runs exactly once per X
process: the first `lorieActivityConnected()` takes the `generation == 0` branch and
sets generation 1. A second is unreachable, because

* X outlives its Activity only when `lorieGateAActive()` is already false
  (`InitOutput.c:620-624`);
* a clean close zeroes `sessionNonce` as well as `generation`
  (`InitOutput.c:3334-3335`), and the bump is gated on a non-zero nonce (`:567`), so
  that route is terminal; and
* every fatal publisher that would clear the gate exits the X process in the same
  breath — X-side through `lorieGateAFatalHalt`'s `_exit(127)` (`lorie.h:1414-1416`),
  renderer-side because all 14 publish sites fire while X is inside
  `gateAWaitTerminal` for that serial.

Consequently `lorieGateARegistryCloseGeneration` (`cmdentrypoint.cpp:380`) has no
runtime caller, and `x-bump-unterminal` (`:391`) and `x-share-in-lease`
(`InitOutput.c:570`) are defensive-only. Corroboration, not proof: across every Gate A
run recorded under `evidence/` — 201 989 `GATEA_EVENT` lines — `generation` has never
been observed above 1.

**Recorded, not decided.** This belongs to D-06 (production lifecycle redesign scope)
and is a statement about the current product, not a defect claim: a boundary that
cannot be reached also cannot be got wrong.

## D-01 AND D-02 IN PRODUCTION USE

* **D-01 (`-noreset`)** carried both passing cells. Every run asserts it is present in
  `/proc/<x_pid>/cmdline` before the cell starts. Without it, F2's fixture
  disconnecting would raise DE_RESET, run the clean close, zero `sessionNonce` and
  disable Gate A silently (Q10) — and F2's own later reads would have been
  unattributable.
* **D-02 (epoch observation)** produced `R_EPOCH_BEGIN` with `epoch_id 1` in every
  session, including the ones with R8 observation disarmed, confirming the armed guard
  in `lorieR8ObsTuple` really is `role[0] == 'x'` only. The R8 process-level
  `BEGIN`/`END` contract was not touched, and the touched-semantics audit's offline
  judge replay stayed 10/10 identical.

## ATTEMPT LEDGER — every attempt, including the ones that failed

```
r9-cold-2/attempt-01  INVALID  x-r8-env halt: parseArm rejects (R8-C1, any fault)
r9-cold-2/attempt-02  INVALID  LORIE-R8-TEST missing: disarming R8 unregisters it
                               -> produced tests/r9/p_r9_boundary.c
                               -> also corroborates the COLD-2 removal
r9-f1/attempt-01      INVALID  cell CORRECT (x-wrong-generation fired); capture aborted
                               in snap() - pidof exits 1 when the process is gone and
                               pipefail turned that into a failed run
r9-f1/attempt-02      INVALID  cell CORRECT; two derivation defects: the identity
                               contract demanded an fd-table field nothing captured,
                               and stale_replay() read R8_OBS rows for stages the
                               product logs as GATEA_VALIDATE lines - and inferred
                               "stale frame sent" from the very fatal the judge
                               requires, which was circular
r9-f1/attempt-03      PASS
r9-f2/attempt-01      INVALID  session CLEAN; shared_nonce and the registry counters
                               were read only from a dump that a healthy cell never
                               produces. My own clean-close step, added to force one,
                               did not reach CloseScreen and fatalled the renderer
                               with r-hup - reverted, with the measurement recorded in
                               the runner where the step used to be
r9-f2/attempt-02      PASS
```

Seven attempts, five INVALID, two PASS. **Not one INVALID was a product defect**, and
not one was reclassified after the fact. Four were tooling defects that an offline
test now pins; the fifth (`r9-f2/attempt-01`) was a fix of mine that made the evidence
worse, and it is written up as such.

## HOST GATES AT THIS COMMIT

```
verify-r9-support.py   R9_SUPPORT_HOST_STATIC_OK   r9_cells=2 removed=7
test-judge-r9.py       32 vectors, 0 failures      device_cells=2
test_r9_evidence.py    36 tests, OK
```

## WHAT R9 DOES NOT CLAIM

* Nothing about warm reconnect. Three cells were designed for it and the product has
  no entry point; the packet says so rather than approximating it.
* Nothing about a generation bump. It is unreachable, so R9 observed exactly one
  generation, and `renderer_bound_*` is kept as a separate field from `shared_*`
  throughout precisely because the two halves have different lifetimes and a future
  bump would separate them.
* Nothing about resource reclamation across a generation (D-06 / Q4-F2 / Q5): the
  READY GL objects have no teardown outside UNREGISTER and the EGL context never turns
  over, so only process death reclaims them. F2 shows the next process starts clean;
  it does not show the previous one released anything.
