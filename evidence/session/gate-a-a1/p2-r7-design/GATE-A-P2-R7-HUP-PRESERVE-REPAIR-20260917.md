# Gate A P2 R7-05 HUP duplicate-fatal repair — 2026-09-17

Source RCA + narrow repair for frozen R7-05 FAIL on `fdfb1ce`.
**No device install. No R7-05 rerun. Judge and contract unchanged.**

## Verdict (source/host/CI/artifact)

Repair SHA **`a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82`** is SOURCE/HOST/CI/ARTIFACT
QUALIFIED. Device remains **`fdfb1ce` INSTALLED**. New candidate is
**NOT INSTALLED**. Historical R7-05 remains **VALID FAIL / FROZEN**.
R7 overall remains **BLOCKED at R7-05**. Production Gate A stays **BLOCKED**.

Primary verdict: **`R7_05_HUP_PROPAGATION_ARTIFACT_QUALIFIED`**.

## Frozen authority (unchanged)

| Item | Status |
|---|---|
| R6 `0f1e546` | PASS / frozen |
| RCA-1 `0d72332` | FIXED / DEVICE-PROVEN |
| CASE_LOOP `7549e36` | DEVICE-VALIDATED |
| B-2 `runtime-7549e36/b2-requalification-02/` | PASS |
| Historical R7-04 on `7549e36` | valid FAIL `halt_mismatch` (not INVALID) |
| `fdfb1ce` R7-04 | PASS / DEVICE-QUALIFIED |
| `fdfb1ce` R7-05 | VALID FAIL `halt_mismatch what=r-hup reason=6` / frozen |
| R7-05 expected last halt | `x-direct-not-success` reason=2 |
| `judge-r7.py` | unmodified SHA256 `fba3c10f…cc17`; old evidence still FAILs |
| EXA wait | 2000 ms |
| CASE_LOOP idle recheck | 8 ms CLOCK_MONOTONIC |
| ABI | no size/layout/enum/event/version change |

## Historical R7-05 observation (`fdfb1ce`, not rewritten)

- Selector `post-draw-gl`, arm 1, `p_r3_single_direct` ×1, X **22704**, Activity **30140**
- Env exactly `PROTO=1 TELEMETRY=1 TEST_FAULT=post-draw-gl TEST_ARM=1`
- Serial **5**; PUBLISH seq=28 → DRAW seq=31 → event 35 seq=32 src=5 dst=2
- FENCE_SATISFIED seq=33, FIRST_FAILED seq=34, COMPLETED seq=35, GENERATION_FATAL seq=36
- SUMMARY `firstFailedSerial=5 generationFatal=2 fatalReason=2`; no reason=4
- First halt `GATEA_FATAL_HALT what=x-direct-not-success reason=2` process=X
- Last halt `GATEA_FATAL_HALT what=r-hup reason=6` process=Activity
- Frozen judge last-halt → `R7_FAIL halt_mismatch what=r-hup reason=6`
- Forbidden success zeros; no unexpected signal; `NO_X3_RESIDUE`; Stable unchanged

Re-ran frozen `judge-r7.py` against `runtime-fdfb1ce/r7-05/logcat-follow.txt`
after this repair: still **`R7_FAIL halt_mismatch what=r-hup reason=6`**.

## RCA answers (A–I)

### Hypothesis

R7-05 correctly publishes/establishes authoritative failure reason=2 and X
intentionally fail-stops. X process death closes the Activity socket. The
Activity looper then observes HUP while its Gate A tuple remains bound and
unconditionally emits a new generic `r-hup reason=6`. That second fatal is
redundant for containment and destroys the frozen terminal identity.

**PROVEN** by source ordering + shared mmap visibility + device sequence.
Not merely inferred.

### A — `generationFatal` already 2 before X halt?

**SOURCE-PROVEN: YES.**

R7-05 is `FAILED_QUIESCED`, not renderer `RESULT_FATAL`:

1. Renderer `lorieGateATestFaultConsume(..., POST_DRAW_GL)` forces
   `GL_INVALID_OPERATION` (`renderer.cpp` after DRAW_SUBMIT).
2. `gateAFencePublishGateA` does **not** `PublishFatal`. It
   `lorieGateAFirstFailedCAS(..., lastSerial, FAIL_DRAW=2)` then publishes
   `completedSerial`.
3. X `gateAWaitTerminal` derives `FAILED_QUIESCED` (firstFailed set,
   `generationFatal==0` until X publishes).
4. `lorieGateAClassifyDirectDone` returns QUIESCED with `firstFailureCode=2`.
5. `gateADoneDirect` calls `gateAXFatal("x-direct-not-success", 2, serial)`.
6. `gateAXFatal` (`InitOutput.c`): acquire-load `ObserveFatal`; if 0,
   **`lorieGateAPublishFatal(&st->gateA, reason)`** sticky CAS
   `__ATOMIC_RELEASE` on `generationFatal`; then EVENT_GENERATION_FATAL;
   DumpSummary; **then** `lorieGateAFatalHalt` → log halt → `_exit(127)`.

Writer: X `gateAXFatal` via `lorieGateAPublishFatal`. Ordering: RELEASE store
is sequenced-before `_exit` on the same thread.

**DEVICE-PROVEN:** SUMMARY `generationFatal=2 fatalReason=2` and first halt
`x-direct-not-success/2` precede Activity `r-hup/6`.

### B — Does Activity still see the same protocol state at HUP?

**SOURCE-PROVEN: YES, via MAP_SHARED, not via `Renderer::setSharedState`.**

- Activity `EVENT_SHARED_SERVER_STATE` `mmap(..., MAP_SHARED)` then hands the
  pointer to `g_renderer.setSharedState(state)`. Closing the memfd does not
  unmap (`activity.cpp` comment).
- `setSharedState` waits on the GL thread (`stateChangeFinishCond`). HUP must
  not call it to *read* fatal (could hang if GL is in fence wait).
- Repair keeps `gateAMappedState` on the Activity looper thread and
  `lorieGateAObserveFatal(&gateAMappedState->gateA)` ACQUIRE-load.
- X `_exit` unmaps X's view; Activity's mapping remains until process death.

**INFERRED (kernel):** AF_UNIX HUP is delivered after the peer closes the
socket; it does not unmap the memfd object.

### C — Can Activity acquire-load `generationFatal` before classifying HUP?

**SOURCE-PROVEN: YES**, using existing `lorieGateAObserveFatal` on the
retained mmap pointer. No new ABI field.

Fail-closed: bound && `gateAMappedState==NULL` treats published as 0 →
existing `r-hup/6` (cannot observe). R7-05 bind path maps successfully
before the cell runs.

### D — Does socket HUP guarantee X already published?

**SOURCE-PROVEN for this halt path:** `PublishFatal` is sequenced-before
`lorieGateAFatalHalt` → `_exit(127)` → fd close → peer HUP. Cross-process
happens-before is the protocol RELEASE/ACQUIRE on MAP_SHARED
`generationFatal`.

**DEVICE-PROVEN for R7-05:** GENERATION_FATAL / SUMMARY / X halt then
Activity `r-hup`.

**Not a general guarantee** that every HUP means a published fatal
(that's Case B / genuine unexpected HUP).

### E — If Activity observes `generationFatal != 0`?

Preserve authoritative fatal. Log `GATEA_HUP_PRESERVE` (must not contain
`GATEA_FATAL_HALT`). `_exit(127)` fail-stop. Do **not** emit second halt.
Do **not** enter `ALooper_removeFd` / `setSharedState(NULL)` /
`removeAllBuffers`.

### F — If `generationFatal == 0` and bound?

**YES, keep `r-hup reason=6`.** Frozen contracts: an active generation
cannot survive unexpected peer HUP. R7-10/P2 are the opposite direction
(X observes renderer death → `x-hup`). Weakening bound zero-fatal HUP
would drop genuine containment.

### G — Skip halt and fall through into normal cleanup?

**UNSAFE. Not implemented.** `setSharedState(NULL)` waits on the GL thread;
`removeAllBuffers` can run GL teardown on a poisoned generation. Fail-stop
must remain noreturn.

### H — Do frozen R7-10 / R7-P2 depend on `r-hup` as last halt?

**NO.** CONTRACT-DETAILS / support design:

- R7-10 `renderer-exit-after-consume`: renderer `_exit(127)` then X
  `x-hup` / 6.
- R7-P2 `present-renderer-exit`: same, X `x-hup`; event 34=0.

Those are **X-side** `handleLorieEventsProto` / legacy
`gateAFatalFromInput(..., "x-hup")`. This repair does not touch
`cmdentrypoint.cpp`. R8/R9 HUP cells are NOT STARTED.

**SOURCE-PROVEN non-regression:** `verify_r7_hup_preserve.py` asserts
X `x-hup` halt and proto `gateAFatalFromInput(..., "x-hup")` unchanged
and that the renderer classifier is absent from cmdentrypoint.

### I — Same family as R7-04 duplicate fatal?

Same **class**: second `GATEA_FATAL_HALT` after an already-authoritative
`generationFatal` destroys last-halt identity.

Different **direction and call site**:

| | R7-04 (`fbo-incomplete`) | R7-05 (`post-draw-gl`) |
|---|---|---|
| Authoritative publisher | renderer `gateARendererFatal` | X `gateAXFatal` after QUIESCED |
| First halt | `r-gatea-DIRECT_LOOKUP_FAIL` / 2 | `x-direct-not-success` / 2 |
| Duplicate halt | X `x-direct-not-success` / 4 | Activity `r-hup` / 6 |
| Repair site | X Done / `gateAXFatal` preserve | Activity HUP classifier |

Do **not** copy the R7-04 helper. Do **not** convert R7-05 to
renderer-authoritative last-halt semantics.

## HUP state table (desired = implemented)

| bound | publishedFatal | class | halt emitted? | process exits? | normal cleanup? |
|---|---|---|---|---|---|
| 0 | any | `UNBOUND` | no | no | yes (legacy disconnect) |
| 1 | 0 | `R_HUP` | `r-hup` reason=6 | yes `_exit(127)` | no |
| 1 | 2 | `PRESERVE` | no `GATEA_FATAL_HALT` | yes `_exit(127)` | no |
| 1 | 6 | `PRESERVE` | no `GATEA_FATAL_HALT` | yes `_exit(127)` | no |
| 1 | !=0 | `PRESERVE` | no `GATEA_FATAL_HALT` | yes `_exit(127)` | no |

## Cross-path audit (unchanged unless noted)

| Path | existing fatal? | publish? | HALT? | exit? | normal cleanup? |
|---|---|---|---|---|---|
| Activity xcallback HUP bound+published | yes | no | no (PRESERVE) | yes | no |
| Activity xcallback HUP bound+0 | no | via halt helper no extra CAS | `r-hup`/6 | yes | no |
| Activity xcallback HUP unbound | n/a | no | no | no | yes |
| X `handleLorieEventsProto` HUP active | publish GENERATION then `x-hup`/6 | yes if 0 | `x-hup` | yes | close then halt |
| X legacy `handleLorieEventsLegacy` HUP | same | yes if 0 | `x-hup` | yes | close then halt |
| renderer `gateARendererFatal` | publish then halt | yes | renderer what | yes | no |
| X `gateAXFatal` published!=0 | preserve | no | no (`x-observe-fatal`) | yes | no |
| clean generation close | n/a | no | no | no | yes |
| Activity `connect_` force-stop old fd | n/a | no | no | no | yes (unbound/rebind) |

Only the Activity bound-HUP classification changed.

## Repair

| | |
|---|---|
| Parent | `fdfb1ce44b429897eda17c43bf33fbd37afe67f3` |
| Branch | `fix/gatea-r7-hup-fatal-preserve-20260917` |
| SHA | `a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82` |
| Worktree | `src/f8-ahb-gatea-r7-hup-preserve` |
| Files | `lorie_gatea_hup_class.h` (new), `activity.cpp`, `scripts/test_gatea_hup_class.c`, `scripts/verify_r7_hup_preserve.py` |
| Symbols | `lorieGateAClassifyPeerHup`, `gateAHupPreserve`, `gateAMappedState` |
| Why narrow | reuse `generationFatal` / `ObserveFatal`; no ABI; no judge; no timeout; no X `x-hup` change |

## ABI (NO ABI CHANGE)

Source asserts unchanged: `sizeof(LorieGateAProtocol)==40`,
`generationFatal` offset 4, protocol version 1, EVENT_MAX 37, COUNTER_MAX 28,
fault tail 40, fence 2000 ms, CASE_LOOP 8 ms. No new shared field.

## Baseline requalification decision

MASTER-PLAN row: **Fault-only classification, no normal-path change** →
specific failed cell only + host classifier/judge regression; do not rerun
B-2 automatically.

Proposed minimum future device scope: **R7-05 only** on SHA `a07d66c`.
Not B-2. Not R7-01+ until that cell PASSes under a new grant.

## Device

**NEW CANDIDATE NOT INSTALLED.** No ADB install. No R7-05 requalification
executed. Historical `runtime-fdfb1ce/r7-05/` not overwritten.
