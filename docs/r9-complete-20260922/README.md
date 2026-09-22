# R9 COMPLETE — 2/2 PASS — docs + evidence snapshot 2026-09-22

```
STATUS: R9 DEVICE PACKET COMPLETE — 2 of 2 PASS
        R9-F1 PASS  r9-f1/attempt-03   expected fatal x-wrong-generation reason=6
        R9-F2 PASS  r9-f2/attempt-02   new nonce · empty registry · event=5 · no fatal
        R9-COLD-2 REMOVED — SOURCE-PROVEN / RUNTIME-NOT-CONSTRUCTIBLE
        6 removed cells total: WARM-1/2/3 · COLD-1/3 · COLD-2
        Production Gate A BLOCKED · V1-Core NOT QUALIFIED
```

- Artifact `dc94485a7ef4f74cada36ea3c1d35d0aa0f48693`, CI **35673085569**,
  APK SHA256 `1bd8bef0…b8a3`, package `com.waydefu.x11gpu` `1.03.01-dc94485-22.09.26`
- Runner `run-r9-one-cell-dc94485.sh` **V2**; fixture
  `tests/r9/p_r9_boundary.c` SHA256 `b2103b23…2531`, binary `c5ca4786…4694`
- Tooling commit `waydefu/termux-x11@3a12e73` on
  `feat/gatea-r8-lifecycle-support-20260918`
- Stable `com.termux.x11` `:1` pid 20881 untouched throughout; ADB lane 5038 only

## Start here

| what | where |
|---|---|
| aggregate result + full attempt ledger | `evidence/session/gate-a-a1/planning-v2/r9-agg/V2-R9-AGG.md` |
| why COLD-2 is gone (line-by-line proof) | `evidence/session/gate-a-a1/planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md` |
| the handoff | `STATUS-HANDOFF-20260921.md` §6.5 |
| frozen INVALID attempts | each `attempt-*/ATTEMPT-FROZEN-INVALID.md` |

## The three findings

**1. Gate A has no reachable generation boundary at all.** The bump path runs exactly
once per X process; a second `lorieActivityConnected()` with `generation != 0` cannot
be reached. X outlives its Activity only when `lorieGateAActive()` is already false
(`InitOutput.c:620-624`); a clean close zeroes `sessionNonce` as well as `generation`
(`:3334-3335`) and the bump is gated on a non-zero nonce (`:567`); and every fatal
publisher that would clear the gate exits the X process in the same breath — X-side
through `lorieGateAFatalHalt`'s `_exit(127)` (`lorie.h:1414-1416`), renderer-side
because all 14 publish sites fire while X is inside `gateAWaitTerminal` for that
serial. So `lorieGateARegistryCloseGeneration` (`cmdentrypoint.cpp:380`) has no
runtime caller and `x-bump-unterminal` (`:391`) and `x-share-in-lease`
(`InitOutput.c:570`) are defensive-only. Corroboration, not proof: across every Gate A
run in this repo's evidence — 201 989 `GATEA_EVENT` lines — `generation` has never
been observed above 1. **Recorded for D-06, not decided.**

This also retracts a sentence in `COLD1-ROUTE-SEARCH.md`: its condition 3 asked only
that `x-eof` not fire, not that X still be running. Corrected in place.

**2. R9 cannot use the R8 fixture.** `parseArm()` allows only
`R8-P1`/`destroy-while-gpu-owned` and `R8-P2`/`close-while-lease`; any other case with
any fault halts X at startup with `x-r8-env`. Disarming R8 instead makes
`LorieR8TestExtensionInit` return early so the extension is never registered. Both
measured, one attempt each. Hence `p_r9_boundary.c`: no extension, one ordinary XCB
`PictOpOver` composite is the whole Gate A direct trigger.

**3. None of the five INVALID attempts was a product defect.** Four were tooling
reading the wrong source — the fd table, the validate stages, the registry counters —
and the fifth was a fix of mine that made the evidence worse and is written up as
such. Every one is pinned by an offline test; no attempt was reclassified.

## What is NOT claimed

- Nothing about warm reconnect. Three cells were designed for it and the product has
  no entry point.
- Nothing about a generation bump. It is unreachable, so R9 observed exactly one
  generation, and `renderer_bound_*` is kept separate from `shared_*` throughout.
- Nothing about resource reclamation across a generation (D-06 / Q4-F2 / Q5). F2 shows
  the next process starts clean; it does not show the previous one released anything.

## Reopen conditions

The six removed cells are **not "done"** — they are unreachable in *this* product.
`judge-r9.py` returns `R9_BLOCKED` for all six and cannot yield PASS, FAIL or INVALID
even when handed evidence that would previously have passed. `verify-r9-support.py`
pins the source facts each removal rests on, so the host gate turns red if either
reopen condition becomes true:

- a **warm reconnect / rebind entry point** → reopen WARM-1/2/3 and COLD-2
- a **renderer fatal publisher reachable outside an X terminal wait** → reopen
  COLD-1/3 and COLD-2
