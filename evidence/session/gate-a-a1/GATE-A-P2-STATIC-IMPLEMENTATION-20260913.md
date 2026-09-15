# Gate A P2 static implementation — 2026-09-13

## SOURCE

```text
branch: qualification/gatea-a1-microprobe-20260912
base:   5e9eb2a (preserved, not amended)
D0a:    qualification/d0a-narrow-20260912 / a6cc795, untouched
```

## DIFF

```text
lorie/src/main/cpp/lorie/InitOutput.c | 568 ++++-
lorie/src/main/cpp/lorie/activity.cpp  |   8 +-
lorie/src/main/cpp/lorie/lorie.h       |  41 +-
lorie/src/main/cpp/lorie/renderer.cpp  | 290 ++-
4 files changed, 868 insertions(+), 39 deletions(-)
```

All 39 removed lines are the intended replacements (plain queue access →
accessors, drain signature, BGRA-only filters → exact BGRA+RGBX pair,
comment updates). No production call-site change when the flag is OFF:
every new runtime branch is `lorieGateAProtoEnabled()`-gated, and the
accessor rewiring keeps (and strictly strengthens) the legacy barriers.

## WHAT EACH FILE CARRIES

- `lorie.h`: firstFailed/firstFailureCode acquire observers (P0 gap closure),
  `LORIE_GATEA_FENCE_TIMEOUT_NS` (2000 ms finite budget), `LorieGateABatchOut`
  drain outcome, `consumeGateAComposite` decl, drain signature change,
  queue-index de-volatiling (layout unchanged; accessors only).
- `renderer.cpp`: Gate A entry detection (COMPOSITE + live READY source),
  READY-registry direct lookup (tuple-matched both endpoints),
  persistent-texture direct draw (FBO + `.bgra` swizzle + completeness check),
  sticky-failure stop, finite Gate A fence + terminal publication
  (fatal-skip / FAILED_QUIESCED CAS / SUCCESS), legacy paths preserved
  bit-for-bit when no Gate A entry is drained.
- `InitOutput.c`: pair lease (NONE/RESERVED/GPU_OWNED), bounded READY ensure
  (REGISTER_FAILED → D0a-legal FALSE; timeout/fatal → halt), direct admission
  (predicate + imported rejection + BGRA→RGBX + first-submit barrier + slot),
  checked pair unlock at first publish with post-unlock revalidation,
  per-rect release-publish, terminal derivation wait, SUCCESS-only
  relock/repair/ack, cross-op guards (schedule refuse, PrepareAccess refuse,
  destroy/resize/share/close fail-stop, CloseScreen poison after use).
- `activity.cpp` + `renderer.cpp` import gates: exact BGRA-or-RGBX pair
  (framing/fingerprint unchanged). Without this, RGBX-destination REGISTER
  would fail and the direct path could never admit — found in self-review.

## STATIC CHECKLIST (8 authorized blockers)

- Lookup miss never completes as success: PASS. Detection is per-entry
  (COMPOSITE + READY source); miss/tuple-mismatch/FBO-incomplete halts the
  renderer before any publication. Legacy-skip paths are unreachable for
  Gate A entries. Stale-generation replay is closed by X-side ordering
  (every Gate A serial is terminal before any re-share; new publishes use
  the new tuple + new READY).
- Finite fence: PASS. `LORIE_GATEA_FENCE_TIMEOUT_NS` on standalone and
  redraw-shared completion fences whenever a Gate A entry was drained.
  The post-swap next-buffer readiness wait stays `EGL_FOREVER` by design:
  it publishes nothing, so a hang there stalls (X Done bounds it) rather
  than lying.
- Wait/fence failure never releases: PASS. Done-direct halts on anything
  but SUCCESS before repair/ack/dec/release/relock. Renderer halt paths
  publish nothing; fatal-observed-after-fence returns silently on both
  sides by the same observation order.
- Present early-ACK: SAFE. COPY/SOLID schedule paths refuse on lease
  overlap (→ CPU fallback pre-publish); scrap/destroy ack only entries
  Present scheduled (never Gate A); first-submit global quiescence
  (`completed == counter` + drained queue) closes the legacy OOM/early-ACK
  cell before any direct submit.
- Queue atomics: PASS. Zero plain accesses remain (grep-verified):
  X release-publish / renderer acquire-consume, renderer release readIndex
  (slot-consumed only) / X acquire, renderer release completed / X acquire,
  plus firstFailed/fatal observers. Legacy `__sync_synchronize` retained.
- READY direct lookup: PASS. Tuple-matched both-endpoint lookup under one
  mutex hold; no legacy list/attach/bind; no CPU lock/clone/upload;
  `.bgra` program for direct BGRA source (D0a's `composite ? 0` not reused);
  ACTIVE now gates on actual-address lock-free atomics.
- Pair lease: PASS. RESERVED (refs held, CPU owns) → GPU_OWNED (first
  publish after checked unlock + revalidation) → NONE (SUCCESS-only relock,
  then repair, then ack). `gateAPreFail` makes post-scheduled refusal
  impossible: any later loss halts.
- Post-publish fail-stop: PASS. No D0a fallback, no replay, no normal
  cleanup after publish; sticky failure/fatal + waiter wake via existing
  P1 primitives + HUP chain; generation/session terminates.

## SELF-FOUND AND FIXED DURING REVIEW (3)

1. RGBX destination REGISTER rejected by both P1 import gates → direct path
   could never admit. Widened to the exact BGRA+RGBX pair, framing unchanged.
2. `gateADirectPublishRect` returned FALSE on paths reachable after
   scheduled > 0 → later rect would run CPU while GPU owns the pair.
   All refusals now route via `gateAPreFail` (halts once scheduled > 0).
3. Admit-time fresh locks did not restore `devPrivate.ptr`/`wasLocked`.
   Now restored, matching the locked-at-rest invariant.

## DELIBERATE MECHANISM NOTE (invariant unchanged)

The P2 review prescribed a bounded `state->lock` acquire around unlock.
Implemented instead without the shared lock: monotonic `completedSerial`
plus sticky firstFailed/fatal make the terminal checks stable once true,
and the renderer cannot touch an unpublished buffer, so the lock adds
deadlock surface (the only locker, `lorie_mutex_lock`, is unbounded)
with no safety benefit. Same invariant, less mechanism.

## NATIVE COMPILE

`:lorie:buildCMakeDebug[arm64-v8a]`, `--no-daemon --no-build-cache`:

1. Incremental: BUILD SUCCESSFUL after fixing real defects in order —
   missing forward declarations (C use-before-define), `egl_display`
   member used from a file-static (now a parameter), drain signature at
   both call sites, `const`-discard warnings (2, fixed by matching the
   existing non-const API), one self-removed bad `RegionUninit`, one
   self-fixed duplicated prologue.
2. Warnings: zero new. Remaining C/C++ warnings are pre-existing lines
   and classes (verified line-by-line: legacy `%llu` formats, keycode
   designators, reorder-init, GLX typedef).
3. Full clean rebuild: log `GATE-A-P2-NATIVE-BUILD-FULL-20260913.log`.

## SCOPE

No CI/APK/ADB/runtime/device/Stable/HDMI operation. No queue-entry or wire
ABI change (frozen asserts still compile). No UNREGISTER/CloseScreen drain
lifecycle (CloseScreen only poison-guards). No imported/external-fence/
replay/D0b/Gate H work. Known narrow limitation (by predicate, fail-closed
to D0a): destinations whose format is not RGBX never admit direct.

## ADDENDUM 2026-09-14

`82a87f4` remains the P2 ownership implementation. B1–B4 source correction
plus default-OFF telemetry closed as `15caa00`. UNREGISTER/generation
lifecycle now exists on that later commit. Compile/static evidence:
`GATE-A-P2-B1-B4-IMPLEMENTATION-20260914.md`. P2 runtime still NOT
AUTHORIZED; Production Gate A still BLOCKED.
