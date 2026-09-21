# GATE A P2 R8 DESIGN ACCEPTANCE — 2026-09-18

Authority: `R8_DESIGN_ACCEPTED_ON_A4C8177`

This is a **new** acceptance record. Historical GPU PR #8 planning docs remain
**PROPOSED** as written. They are not rewritten as if they were always accepted.

| Field | Value |
| --- | --- |
| Historical design source | `fdfb1ce44b429897eda17c43bf33fbd37afe67f3` |
| Historical design docs | `planning/r8-lifecycle-20260917/` (GPU PR #8 merged; status in those files remains PROPOSED) |
| Final R7 runtime authority | `a4c8177f4b059fddd111717255e9d23cf0e15e1e` |
| R7 verdict | GATE A P2 R7 PASS / COMPLETE 13/13 |
| Installed experimental at acceptance | `com.waydefu.x11gpu` `1.03.01-a4c8177-18.09.26` CI **35295094951** |
| R8 implementation parent | `a4c8177f4b059fddd111717255e9d23cf0e15e1e` (do not amend) |
| R8 implementation branch | `feat/gatea-r8-lifecycle-support-20260918` |
| Design status for this generation | **DESIGN_FROZEN** after A01–A11 below |
| Production Gate A | BLOCKED |
| R9 | not authorized by this record |

Frozen wait precedence (carried from R7, unchanged):

SUCCESS already derived > published generationFatal > peer HUP > live-peer genuine timeout

Frozen R7 source carried into R8: `8545b26` peer-HUP containment; `abb27a65` Present fault12/13 exact target arming; `a4c8177` cell12 held-incomplete protection against later completedSerial high-watermark.

## A01 — Destroy / ACK ownership order — ACCEPT

Renderer, same import identity:

1. remove READY
2. delete GL texture
3. destroy EGLImage
4. release imported AHB
5. event26
6. send ACK

X, after receiving ACK:

1. remove X slot
2. release owning pixmap/buffer

Oracle is **partial order only**. Do not restore older inaccurate prose that treated log timestamps as a total order across the AF_UNIX boundary.

Source: `gateADestroyReadyImport` (`texture → EGLImage → AHB`) then `EVENT_RESOURCE_DESTROY` then `gateASendUnregisterAck`; X `lorieGateARegistryHandleUnregisterAck` then `lorieGateARegistryRemoveAcked` then owner release in `lorieExaDestroyPixmap`.

## A02 — Partial order / connection semantics — ACCEPT

Freeze source-proven causality, not raw textual timestamp order.

For the **same buffer**: renderer actual destroy/release must precede X ownership release.

Do **not** demand a total order among:

- X request log
- renderer diagnostic
- X receive log

unless a single-thread source edge requires it. V02/V03 (renderer26 vs X24/X25 post-send logging) are legal PASS constructions.

## A03 — Capacity units — ACCEPT

| Capacity | Unit | Count |
| --- | --- | --- |
| X registry | buffer | 16 (`LORIE_GATEA_XREGISTRY_SIZE`) |
| renderer READY | buffer | 16 (`LORIE_GATEA_MAX_READY`) |
| pending import queue | buffer | 8 (`LORIE_GATEA_MAX_PENDING`) |

Pending import 8 is **not** registry capacity. Do **not** interpret 16 as 16 pairs.

C5 must first measure the live unrelated registered baseline. If a necessary root/screen slot exists, record it and fill only remaining slots. Do not blindly allocate 16 additional slots.

## A04 — register-only control — ACCEPT

Test-build only (`LORIE_ENABLE_R8_TEST_SUPPORT`, default OFF): `LORIE-R8-TEST` `REGISTER_BUFFER(xid)` for C4/C5 setup.

Must call real `lorieEnsureGpuSampleable(...AHARDWAREBUFFER)` and a wrapper around real `gateAEnsureReady`.

Must **not** call PrepareComposite, pair reserve, unlock, submit, fallback, or Done.

No normal product semantic change.

## A05 — P1/P2 real guard invocation — ACCEPT

P1 (`destroy-while-gpu-owned` enum14): the consumed branch on the R8 support candidate invokes actual `lorieExaDestroyPixmap` while the pair is GPU_OWNED. Expected fatal: `x-destroy-in-lease` reason=7 (existing destructor overlap guard). Unconditional synthetic `gateAXFatal` at the consume site is not proof.

P2 (`close-while-lease` enum15): invoke actual `gateACloseGeneration` (already the product function; keep that, do not replace with a stub). Expected fatal: `x-close-in-lease` reason=8.

If the real guard returns, emit observation `R8_HOOK_UNEXPECTED_RETURN` and fail-stop with that sentinel. That path is FAIL (`GUARD_RETURNED`), not PASS.

OFF builds retain the historical P1 consume-site fatal stub.

## A06 — observation completeness — ACCEPT

Compile-gated `R8_OBS` sideband. Observation only. Never feeds admission, completion, ownership, or product result.

Required live observations as listed in the implementation grant (registry, pending, lease/pair, queue indices, completedSerial, fatal, final renderer/X resource state, destructor/close/present/defer/wake/hook kinds).

Missing required snapshot → INVALID. Never coerce null mandatory fields to false/zero.

Producer completeness: BEGIN (expected count/digest) / records / END (actual count/digest). Collector cannot fabricate missing producer records.

## A07 — deferred completion test — ACCEPT

R8-D uses **real** Present GPU COPY completion. Required:

real `GPU_COPY_DONE` / wake arrives while X UNREGISTER wait is active → actual DEFER enqueue → later workproc dispatch → **same record exactly once**.

Forbidden: sleep, renderer delay, fake `GPU_COPY_DONE` on device, device completion injection, retry-until-overlap.

No required overlap → `INVALID_CONSTRUCTION`. Freeze once-run evidence and STOP. No attempt 2.

Synthetic completion is host-only (`HOST-DEFER` H01–H03) and must be absent from the Android artifact.

## A08 — ownership claim scope — ACCEPT

Do not generalize `ownerRef == root lifecycle` unless source proves it. This generation does not.

R8 qualifies **bounded destroy/close lifecycle** claims only.

Root resize and `REGISTER_FAILED` cleanup remain Production blockers. Not in this 10-cell matrix.

## A09 — Present retirement proof — ACCEPT

event36 is Present helper **entry / waited sample**, not completion proof.

Present retirement requires:

- pre-ACK completed watermark covering target serial S in the same session (`T >= S`)
- post-ACK pending clear for that helper invocation

`waited` 0 or 1 can both be legal depending on timing (V05 waited0, V06 waited1).

## A10 — clean shutdown — ACCEPT

Clean shutdown is a **requested** shutdown that reaches `CloseScreen` → `gateACloseGeneration` → renderer unbind.

A cleanup kill cannot be relabeled clean.

Harness TERM is acceptable **only** because source proves `dix/main.c` after `Dispatch()` returns: `FreeAllResources` → `CloseScreen` → `ddxGiveUp(EXIT_NO_ERROR)`. `DE_TERMINATE` / TERM that enters that path is requested normal shutdown, not a cleanup kill.

## A11 — C2 CloseScreen construction — RESOLVED (SPLIT)

Question: can real normal server shutdown enter `CloseScreen` while relevant Gate A **client** registrations are still live?

Source (lineage `a4c8177`, `dix/main.c` + `lorieCloseScreen`):

After `Dispatch()` returns, DIX runs `FreeAllResources()` (client pixmap destroy → `lorieExaDestroyPixmap` → `gateARetireBuffer`) **before** `CloseScreen`. Root is set `NullWindow` after `FreeAllResources`. `lorieCloseScreen` then calls `gateACloseGeneration()` and destroys `pScreen->devPrivate` (root pixmap).

**Verdict: NO.** Real normal shutdown **cannot** enter `CloseScreen` with live **client** Gate A registrations. Root/screen pixmap may still be registered at CloseScreen and is retired by generation close / DestroyPixmap of `devPrivate`.

Do **not** modify product teardown to manufacture live-client-at-CloseScreen.

Frozen C2 split:

1. **Device cell R8-C2 (this matrix):** real requested TERM → actual `CloseScreen` entry. Client IDs are retired by real destructors during `FreeAllResources` **before** CloseScreen (accepted source-bound shutdown disposition). No active pair at close. Generation closed. Renderer unbound. Spec already allows `actual_CloseScreen_entry_with_recorded_live_registry_or_accepted_source_bound_shutdown_disposition` and forbids `unproven_live_at_close`.
2. **Synthetic clean-generation-close** with live client registry is a **separate** reviewed test-only claim. It is **not** a device cell in this 10-cell order. It is **not** equivalent to real normal CloseScreen. Not implemented as a disguised C2.

C5-full uses the same real TERM disposition: fill 16, retain client pixmaps until TERM; `FreeAllResources` runs real destructors; then CloseScreen.

## Frozen runtime order (unchanged)

R8-C1 → R8-C2 → R8-C3-window → R8-C3-disconnect → R8-C4 → R8-C5-full → R8-C5-overflow → R8-D → R8-P1 → R8-P2

Device cells: **10**. Judge-negative vectors: **53 host/judge vectors** (not 53 device executions). `judge_vectors=53`, `device_cells=10`.

## Escalation stop conditions (unchanged)

If implementation would change normal direct admission, READY semantics, normal result path, Present ACK/retirement, normal completedSerial, surface behavior, shared ABI, or generation ownership model: **STOP** with `R8_SCOPE_ESCALATION_REQUIRED`.

## Verdict

A01 ACCEPT  
A02 ACCEPT  
A03 ACCEPT  
A04 ACCEPT  
A05 ACCEPT  
A06 ACCEPT  
A07 ACCEPT  
A08 ACCEPT  
A09 ACCEPT  
A10 ACCEPT  
A11 RESOLVED SPLIT  

**R8_DESIGN_ACCEPTED_ON_A4C8177**

This R8 implementation generation may proceed as **DESIGN_FROZEN**.
