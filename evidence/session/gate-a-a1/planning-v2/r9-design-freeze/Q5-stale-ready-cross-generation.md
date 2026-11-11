# R9 DESIGN FREEZE — Q5 RESOLVED (stale READY visible to a new generation)

DATE 2026-09-21  MODE host-only source trace, read-only, no device, no attempt consumed
TREE `src/f8-ahb-gatea-r7-p1-arm` @ `14caa7b` (branch `feat/gatea-r8-lifecycle-support-20260918`)
SCOPE Answers Q5 only. Q1/Q2/Q4/Q6/Q9/Q10/Q11 remain OPEN.
DEPTH `V2-R8-D-SRC-TRACE` — every claim cites a line.
BUILDS ON `Q3-generation-nonce-lifecycle.md` (two independent tuple authorities).

§8.2 calls this "the most dangerous UAF surface". **It is not one.** A stale READY
cannot be reached by a new generation: three independent filters block it, and the
rebind that would create the exposure fail-stops. The real residual is different and
smaller, and is stated at the end.

---

## The object in question

```
renderer.cpp:205-213   struct GateAReadyImport { occupied; id, nonce, generation,
                       fingerprint; AHardwareBuffer *ahb; EGLClientBuffer;
                       EGLImage; GLuint texture; }
renderer.cpp:219       static struct GateAReadyImport gateAReady[LORIE_GATEA_MAX_READY]
renderer.cpp:221       guarded by gateAImportMutex
```
Every entry **carries its own (nonce, generation)**. That is what makes the filters
below possible: staleness is a property of the entry, not of ambient state.

---

## Filter 1 — draw-time lookup skips foreign generations

`gateALookupDirect()` (`renderer.cpp:843`) resolves the src/dst textures for a
COMPOSITE. It takes the renderer's **bound** tuple first (`renderer.cpp:852`), then:
```
renderer.cpp:857   if (!e->occupied || e->nonce != bn || e->generation != bg
renderer.cpp:858       || e->ahb == NULL || e->texture == 0)
renderer.cpp:859       continue;
```
A READY entry from an older generation is therefore **invisible**, not misused. Both
endpoints must be found or the function returns 3 (`renderer.cpp:879`) and the caller
fail-stops. There is no fallback that reaches into an unmatched entry.

## Filter 2 — retirement requires an exact triple

`gateATakeReadyImport()` (`renderer.cpp:713`):
```
renderer.cpp:718-720   gateAReady[i].occupied && .id == id && .nonce == nonce
                       && .generation == generation
renderer.cpp:722       memset(&gateAReady[i], 0, ...)     <- removed under the mutex
```
A miss returns -1, and the sole caller turns that into
`r-unregister-missing` / `FAIL_UNREGISTER` fatal (`renderer.cpp:779-782`). An
UNREGISTER for one generation can never retire another generation's entry.

## Filter 3 — rebinding over a live READY is fatal

This is the filter my Q3 note got wrong, and it is the decisive one.
`lorieGateAImportBusy()` (`renderer.cpp:282`) counts **four** things, and the READY
table is one of them:
```
renderer.cpp:286-287   sticky gateAImportOverflow
renderer.cpp:288-289   gateAPending[]           (REGISTER outcomes in flight)
renderer.cpp:290-291   gateAPendingControl[]    (UNREGISTER / GENERATION_CLOSE)
renderer.cpp:292       gateAReady[i].occupied   <-- a stale READY IS "busy"
```
and the rebind guard consumes it:
```
activity.cpp:204-207   if (gateABound && (nonce != gateABoundNonce
                               || generation != gateABoundGeneration)
                           && lorieGateAImportBusy())
                           lorieGateAFatalHalt("r-rebind-busy", FAIL_GENERATION)
```
So the exact scenario Q5 names — a new generation arriving while a previous
generation's READY entry still exists — **halts the renderer**. It does not rebind
and then race.

## Filter 4 (X side, independent) — `gateAReadyStill()`

X does not trust its own earlier admission either. Before each use
(`InitOutput.c:2829`, `:3373`) it re-derives everything:
```
InitOutput.c:2680   static int gateAReadyStill(LorieBuffer *buf)
InitOutput.c:2695-2699  meta.nonce == shared->sessionNonce
                     && meta.generation == shared->generation
                     && both nonzero
                     && meta.state == LORIE_GATEA_REG_READY
                     && meta.fingerprint == lorieGateAFingerprint(w,h,stride,format)
```
The fingerprint term means even a same-id, same-generation entry whose geometry
changed is rejected.

---

## Ruling

```
Q5  A stale READY is NOT reachable by a new generation.
    Draw-time lookup filters it (renderer.cpp:857); retirement cannot match it
    (renderer.cpp:718-720); the rebind that would expose it fail-stops
    (activity.cpp:204-207 via renderer.cpp:292); and X independently re-validates
    tuple + state + fingerprint per use (InitOutput.c:2695-2699).
    §8.2's "most dangerous UAF surface" framing is NOT supported by the source.
    R9 must not be designed around defending it; R9 must instead PROVE the halt.
```

## The actual residual — smaller, and a lifetime hole, not a UAF

**`gateADestroyReadyImport()` (`renderer.cpp:444`) has exactly one caller**
(`renderer.cpp:783`), inside the UNREGISTER control handler. It is the only code that
releases a READY entry's `AHardwareBuffer`, `EGLImage` and GL texture. Consequences:

1. Every non-UNREGISTER exit leaves those GL objects owned by a table that only
   **process death** reclaims. Today every such path does die —
   `r-rebind-busy` (`activity.cpp:206`), `gateAHupPreserve` → `_exit(127)`
   (`activity.cpp:153`, reached at `:424`), `r-hup` fatal (`activity.cpp:427`) — so
   the leak is contained by termination, not by cleanup.
2. **That containment is exactly what an R9-RESET would have to replace.** This is a
   hard input to Q10: a same-process reset needs a READY-table teardown that does not
   exist yet, in addition to the nonce problem Q3 already recorded.

**One narrow unguarded transition.** The busy check at `activity.cpp:204` is gated on
`gateABound` being true. The else-branch takes no busy check at all:
```
activity.cpp:210-212   } else { gateABound = 0; }     /* version mismatch, or
                                                         nonce == 0, or generation == 0 */
```
Reachability is tight: `gateABindFromState` is called only from
`activity.cpp:504` (`EVENT_SHARED_SERVER_STATE`), and `lorieSendSharedServerState`
has exactly one caller, `InitOutput.c:592` in `lorieActivityConnected()`. A zero
tuple can reach the renderer only via `InitOutput.c:582` (`sessionNonce = 0` on
generation exhaustion at `UINT64_MAX`) or a getrandom failure at startup
(`InitOutput.c:527`, where Gate A was never active and no READY entry can exist).
So this is reachable **only at 2^64 shares** — theoretical, not live. Recorded so R9
does not have to re-derive it, and so any future code that zeroes the tuple for some
other reason knows it is walking into an unguarded unbind.

---

## Correction to `Q3-generation-nonce-lifecycle.md`

That document's forward note said a stale READY with no live import "rebinds
silently". **That is wrong** — `lorieGateAImportBusy()` counts READY occupancy
(`renderer.cpp:292`), so such a rebind is `r-rebind-busy` fatal. The Q3 document has
been corrected in place; this paragraph records why.

## Still OPEN
```
Q1 Q2 Q4 Q6 Q9 Q10 Q11 — §8.1 still forbids running R9 off PR #7's design.
Q6 next: the bump/latch window from Q3 (InitOutput.c:586 -> activity.cpp:209-211),
   now known NOT to be exploitable via READY. Q6 must ask the same of in-flight
   FRAMES rather than imports.
```
