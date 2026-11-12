# R9 DESIGN FREEZE — Q4 (renderer state retained across generations)

## QUESTION
Which renderer/Activity-process state survives a generation boundary, who resets it,
and at which line? Anything with no reset site is a lifetime constraint on R9.

## SOURCE AUTHORITY
```
TREE   src/f8-ahb-gatea-r7-p1-arm @ 14caa7b (branch feat/gatea-r8-lifecycle-support-20260918)
DATE   2026-09-22
MODE   host-only, read-only, no device, no adb, no build, no CI, no source mutation,
       no runtime attempt
DEPTH  Q3/Q5/Q6 standard. Every claim cites file:line. Unsettled -> NOT PROVEN.
BUILDS ON Q3 (two tuple authorities), Q5 (READY table), Q6 (frame/defer/completion).
```

## THE STRUCTURAL FACT

`g_renderer` is a file-scope static (`activity.cpp:128`), and every Gate A table is a
file-scope static in `renderer.cpp:218-222`. **Their lifetime is the APK process, not
the generation.** Therefore the default for every item below is "retained", and the
question is only which ones have an explicit reset site.

## INVENTORY

| # | state | decl | reset site | retained across a generation? |
|---|---|---|---|---|
| 1 | `gateABoundNonce` / `gateABoundGeneration` / `gateABound` | `activity.cpp:137-139` | `lorieGateAUnbindTuple` `:168-179`; `gateABindFromState` else-branch `:211` | only on GENERATION_CLOSE or a zero/mismatched tuple; **NOT on disconnect** |
| 2 | `gateAMappedState` | `activity.cpp:143` | **NONE** | **YES — and it dangles. See F1.** |
| 3 | `gateAPending[]` | `renderer.cpp:218` | drained in `gateADrainPendingImports` `:667-689` | drained only when the GL thread runs |
| 4 | `gateAReady[]` | `renderer.cpp:219` | `gateATakeReadyImport` `:713-729` (UNREGISTER only) | **YES** — confirms Q5 |
| 5 | `gateAPendingControl[]` | `renderer.cpp:220` | consumed in the control drain `:764-820` | drained only when the GL thread runs |
| 6 | `gateAImportOverflow` | `renderer.cpp:222` | read-and-clear `:668-669` | per-drain; overflow poisons the generation `:696` |
| 7 | EGL context `ctx` | `lorie.h:1792` | **NONE** | **YES — process lifetime. See F2.** |
| 8 | `gpuCopyFbo`, `g_texture_program*`, `g_solid_program` | `lorie.h:1828-1832` | **NONE** | **YES — process lifetime. See F2.** |
| 9 | `r8RendererGenerationUnbound` / `SurfaceQuiesced` / `EndEmitted` | `renderer.cpp:144-147` | **NONE** | **YES — one-shot latches. See F3.** |
| 10 | `r8RendererLoopDrained` | `renderer.cpp:146` | `:2398` each loop iteration | no |
| 11 | `b3aBatchRecords[]` / `b3aBatchRecordCount` | `renderer.cpp:181-182` | `:190`, `:1715` | no — per batch |
| 12 | `addedBuffers` / `buffers` / `removedBuffers` | `lorie.h:1796` | `Renderer::removeAllBuffers` `:1526-1540` | no — drained on disconnect |
| 13 | `Renderer::state` | `lorie.h:1822` | swapped at `renderer.cpp:2407`, old mapping munmap'd `:2427` | replaced, and the old one is unmapped |

## FINDING Q4-F1 — `gateAMappedState` has no invalidation site (NEW)

**Provable by enumeration — the identifier occurs on exactly four lines in the whole
tree: one declaration, one write, and one read spanning two lines:**
```
activity.cpp:143   static struct lorie_shared_server_state *gateAMappedState = NULL;   DECL
activity.cpp:503                       gateAMappedState = state;                        ONLY WRITE
activity.cpp:418-419  if (bound && gateAMappedState != NULL)
                          published = lorieGateAObserveFatal(&gateAMappedState->gateA); ONLY READ
```
There is **no site that writes NULL back.**

Meanwhile the mapping it points at is unmapped by the GL thread:
```
renderer.cpp:2404-2405   if (state && pendingState != state) oldState = state;
renderer.cpp:2427-2428   if (oldState) munmap(oldState, sizeof(*oldState));
```
and two paths drive `setSharedState(NULL)`, which makes `pendingState == NULL != state`
and therefore munmaps the current mapping:
```
activity.cpp:436   g_renderer.setSharedState(NULL);   (peer-HUP handler)
activity.cpp:549   g_renderer.setSharedState(NULL);   (connect_, when oldFd != -1)
```
Neither path clears `gateABound` (`activity.cpp:137-139` is touched only at `:173`,
`:209-211`). So after either path, the read guard at `:418` —
`bound && gateAMappedState != NULL` — **can still be true while the pointee is
unmapped.**

**The re-share path is safe** and shows the intended ordering: `gateAMappedState` is
reassigned at `:503` *before* `setSharedState(state)` at `:506`, so by the time the GL
thread munmaps the old mapping at `renderer.cpp:2427`, the pointer already refers to
the new one. Only the transitions to NULL leave the dangler.

**Exposure chain** (each step cited; final reachability marked):
```
1  Gate A bound: gateABound = 1, gateAMappedState = P1        activity.cpp:209-213, :503
2  Activity reconnects -> connect_ with oldFd != -1
     -> setSharedState(NULL)                                   activity.cpp:549
     -> GL thread munmaps P1                                   renderer.cpp:2404, :2427
   gateABound is STILL 1; gateAMappedState is STILL P1 (now unmapped)
3  A new fd is registered and HUPs BEFORE X sends
   EVENT_SHARED_SERVER_STATE (which is the only thing that
   reassigns gateAMappedState)                                 activity.cpp:486, :503
4  HUP handler: bound == 1 && gateAMappedState != NULL -> TRUE
     -> lorieGateAObserveFatal(&gateAMappedState->gateA)        activity.cpp:418-419
     -> reads unmapped memory
```
```
CLASS         read-after-munmap of a MAP_SHARED region (not a heap UAF)
CONSEQUENCE   SIGSEGV, or a garbage `published` value if the address was reused,
              which then mis-steers lorieGateAClassifyPeerHup at activity.cpp:420
              between HUP_PRESERVE (gateAHupPreserve, _exit 127) and HUP_R_HUP
              (lorieGateAFatalHalt "r-hup")
PROVEN        the absence of any clear site; the munmap; that gateABound is not
              cleared by either NULL path; that the guard can therefore be true
              with an unmapped pointee
NOT PROVEN    that step 3 occurs. It depends on Java-side connect/HUP sequencing
              that is not in this tree. Reachability NOT PROVEN either way.
```
Both outcomes are process-fatal by design, so this does **not** widen the blast
radius beyond an already-terminal path — but it converts a *classified* halt into an
*unclassified* crash, which destroys the very identity `gateAHupPreserve` exists to
preserve (`activity.cpp:146-155`, and the comment at `:408-412` explaining that a
preserved identity must not emit a second `r-hup`).

## FINDING Q4-F2 — GL objects and the EGL context are process-lifetime

`Renderer::refreshContext()` (`renderer.cpp:1620-1660`) replaces only the **surface**:
`releaseWinAndSurface(&win, &sfc)` `:1625`, then `eglCreateWindowSurface` `:1650`. It
never touches `ctx`. The only `eglDestroyContext` in the tree is `:1472`, on a
throwaway `testctx` inside the capability probe.

`gpuCopyFbo` is created lazily (`:922-923`, `:1834-1835`) and **never deleted**. The
three programs are created in `:1202` and never deleted — the single `glDeleteProgram`
at `:2527` is the link-failure arm of `createProgram`, not teardown.

Consequence: every `GateAReadyImport.texture` / `.image` (`renderer.cpp:205-213`)
lives in a context that outlives any number of generations. Combined with Q5's
result that `gateADestroyReadyImport` (`renderer.cpp:444`) has exactly one caller
(`:783`, the UNREGISTER handler), **the only reclamation for those GL objects is
process death.** Q5 recorded this as a lifetime hole; Q4 establishes that the
containing context never turns over either, so the hole cannot self-heal.

`Renderer::removeAllBuffers()` (`:1526-1540`) does **not** help: it drains
`addedBuffers` and `buffers` into `removedBuffers` and touches no Gate A table.

## FINDING Q4-F3 — the R8 renderer observation terminal is one-shot per process

```
renderer.cpp:147        static int r8RendererEndEmitted;      (never cleared)
renderer.cpp:149-159    lorieR8MaybeFinalizeRendererObs():
                          :150-151  if (r8RendererEndEmitted) return;
                          :152-153  require r8RendererGenerationUnbound && r8RendererSurfaceQuiesced
                          :156-157  require r8RendererLoopDrained
                          :158      r8RendererEndEmitted = 1; lorieR8ObsEnd("r")
renderer.cpp:820        r8RendererGenerationUnbound = 1      (never cleared)
renderer.cpp:1644       r8RendererSurfaceQuiesced   = 1      (never cleared)
renderer.cpp:2398       r8RendererLoopDrained = 0            (cleared per loop)
```
`lorieR8ObsEnd("r")` can fire **at most once per APK process**. R9 spans generations
inside one process by definition, so:
```
- the renderer observation stream cannot be terminated per generation as it stands;
- generation 2 onward starts with GenerationUnbound and SurfaceQuiesced ALREADY 1,
  so the terminal condition is satisfiable by generation 1's history alone.
```
This is an R9 **tooling** constraint, not a product defect — the latches are all under
`#ifdef LORIE_ENABLE_R8_TEST_SUPPORT` (`renderer.cpp:143`, `:819`, `:1643`).

## WHAT IS PROVEN

```
P1  g_renderer and every Gate A table are file-scope statics: process lifetime by
    construction.                          activity.cpp:128; renderer.cpp:218-222
P2  gateAMappedState has ONE write site, ONE read site, and NO clear site.
    Enumerated: 4 lines tree-wide (decl :143, write :503, read :418-419).
                                                    activity.cpp:143, :503, :418-419
P3  setSharedState(NULL) causes the GL thread to munmap the current mapping.
                          activity.cpp:436, :549; renderer.cpp:2404-2405, :2427-2428
P4  Neither NULL path clears gateABound, so the :418 guard can be true with an
    unmapped pointee.                     activity.cpp:137-139, :173, :209-211, :418
P5  The re-share path reassigns gateAMappedState (:503) BEFORE setSharedState (:506),
    so it is ordered correctly and is not exposed.
P6  The EGL context is never destroyed; refreshContext swaps only the surface.
                                                 renderer.cpp:1620-1660, :1472
P7  gpuCopyFbo and the three GL programs are never deleted.
                                    renderer.cpp:922-923, :1202, :1834-1835, :2527
P8  removeAllBuffers touches only the legacy buffer lists, never a Gate A table.
                                                             renderer.cpp:1526-1540
P9  lorieR8ObsEnd("r") is one-shot per process; two of its three preconditions are
    never-cleared latches.                    renderer.cpp:147, :149-159, :820, :1644
P10 gateAImportOverflow is NOT permanently sticky: read-and-clear at :668-669, and
    an overflow poisons the generation at :696.
```

## WHAT IS NOT PROVEN

```
N1  RESOLVED 2026-09-22 by Q1 — see Q1-Q2-activity-restart-boundaries.md, Q1-F2.
    The WARM-RECONNECT flow produces exactly this ordering: connect_ munmaps the old
    mapping at activity.cpp:549 while gateABound stays 1, then installs and registers
    the new fd (:556-560) BEFORE any EVENT_SHARED_SERVER_STATE (:503, the only writer
    of gateAMappedState). MainActivity.java:604-606 retries every 250 ms, so a
    flapping or slow-starting X routinely yields a registered-but-not-yet-stateful
    connection. REACHABILITY IS ESTABLISHED. Whether it has OCCURRED remains a
    runtime question.
N2  Whether the munmap'd address can be reused by a later mmap before the dangling
    read, which decides SIGSEGV vs. garbage-value. NOT PROVEN.
N3  Whether any generation-2 renderer path depends on GL objects created under
    generation 1 (F2). The objects survive; whether that is ever OBSERVED is not
    established here and belongs to an R9 packet, not to source reading.
N4  Whether gateAPending[] / gateAPendingControl[] can still hold generation-1
    entries at the moment generation 2 binds. Q5 proved that a rebind over a live
    entry is r-rebind-busy fatal (activity.cpp:204-207 via renderer.cpp:288-291),
    but whether the drain always precedes the rebind is NOT PROVEN.
```

## R9 TEST IMPLICATION

```
1  F3 is a HARD BLOCKER for multi-generation renderer observation. Any R9 packet
   that needs a per-generation renderer obs terminal cannot get one from the
   current test-support code. Decide this BEFORE writing an R9 fixture.
2  F1 gives R9 a concrete, cheap assertion: at every generation boundary, record
   whether gateAMappedState still equals the live mapping. The product offers no
   such observation today.
3  F2 means an R9-RESET (Q10) must destroy GL objects itself. Q5 established there
   is no teardown outside UNREGISTER; Q4 adds that the context never turns over, so
   nothing reclaims them implicitly.
4  Items 1, 3, 5 in the inventory are drained only when the GL thread runs. Every
   R9 packet crossing a boundary must therefore record whether a GL-thread drain
   occurred between the bump and the assertion, or its result is unfalsifiable.
```

## Q3 / Q5 / Q6 CROSS-CHECK

```
CONTRADICTION_FOUND: none.
```
```
Q3  Confirmed and extended. Q3 recorded the renderer's latch as authority 2; Q4 adds
    that NOTHING clears that latch on disconnect (activity.cpp:137-139 vs :436, :549),
    which is what makes F1's guard survivable.
Q5  Confirmed and strengthened. Q5 found gateADestroyReadyImport has one caller and
    that containment rests on process death. Q4 proves the EGL context never turns
    over either (P6/P7), so the hole cannot self-heal, and that removeAllBuffers is
    not a second reclamation path (P8).
Q6  Consistent. Q6's QUEUE_LIFETIME_GAP concerned X-side queues; Q4 is the
    renderer-side counterpart. Neither revises the other.
```
No claim in Q3, Q5 or Q6 is withdrawn.

## FINAL VERDICT

```
RENDERER_STATE_RETAINED_BY_CONSTRUCTION   all Gate A tables and g_renderer are
                                          file-scope statics; retention is the
                                          default, not an oversight.
                                          activity.cpp:128; renderer.cpp:218-222
MAPPING_POINTER_LIFETIME_DEFECT           gateAMappedState has no clear site and can
                                          outlive its mapping. Reachability NOT
                                          PROVEN (N1). New in Q4.
                                          activity.cpp:143, :418-419, :503
GL_OBJECT_PROCESS_LIFETIME                EGL context and all GL objects survive every
                                          generation; only process death reclaims the
                                          READY textures/images.
                                          renderer.cpp:1620-1660, :1472, :1202
OBS_TERMINAL_ONE_SHOT                     lorieR8ObsEnd("r") can fire once per process;
                                          blocks per-generation renderer observation.
                                          renderer.cpp:147, :149-159
```
`DESIGN_REQUIRED` is **not** raised. F1's two outcomes are both already-terminal
paths; F2 and F3 are constraints on R9's design, not defects that block the freeze.

## STILL OPEN
```
Q1 Q2 Q9 Q10 Q11 — §8.1 still forbids running R9 off PR #7's design.
Q10 now has THREE independent pre-answers: no nonce re-roll (Q3), no READY teardown
    outside UNREGISTER (Q5), and no context turnover (Q4/F2).
```
