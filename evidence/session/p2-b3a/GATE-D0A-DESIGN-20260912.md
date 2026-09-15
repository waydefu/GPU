# Gate D0a Narrow Prototype — 2026-09-12

## STATUS

```text
SOURCE: IMPLEMENTED + NATIVE BUILD PASS
CI: PASS (34630012370)
RUNTIME A/B: PASS — see below
VERDICT: PASS / PERFORMANCE-POSITIVE (uniform steady-state workload)
```

## Objective

Verify only persistent staging allocation/registration + persistent GL
texture reuse. Full source clone and full texture upload are unchanged.

## Design (one core function)

`lorieCloneBgraAhbToFd` gains a default-off branch (`TERMUX_X11_D0A=1`):
one-slot FD cache keyed by `(width, height, stride==width, BGRA)`.

- Hit: `acquire` cached buffer for the caller, full memcpy into it.
- Miss: allocate first; only on success unregister + release the old entry,
  then store (cache ref) + acquire (caller ref). Allocate failure keeps the
  old entry and falls back exactly like before.
- `lorieExaPrepareComposite` / `lorieExaComposite` /
  `lorieExaDoneComposite`: unchanged. Queue ABI, predicate, blend, shader,
  X-byte repair, fence, completedSerial, mutex, CloseScreen: unchanged.
- Renderer: unchanged. The same buffer id stays registered, so
  `findBufferWithRetry` keeps finding it in `buffers` with its GL texture;
  `attachToGL` cannot run again for it. Texture reuse is proven offline by
  constant `staging_buffer_id` + absent `FD_ALLOC`/`FD_MMAP` phases.

## Refcount proof

- allocate returns 1 (cache) + acquire returns 2 (caller). Done releases the
  caller ref and every per-entry ref after waiting lastSerial → back to 1.
- Replace happens only in Prepare, after Done balanced all other refs, so the
  old entry is at exactly 1 and frees cleanly.
- Flag off: the old code path runs byte-identical (early branch only).

## Telemetry (schema 1 → 2, appended fields only)

Per record: `staging_cache_hit`, `staging_cache_miss` (0/1),
`staging_buffer_id` (0 when D0a off), gated by `LORIE_B3A_VALID_STAGING`.
Alloc/reuse totals derive offline (misses == allocs). Texture
create/reuse derives offline (new id ⇒ one attach; same id ⇒ reuse).
Unobservable GPU fields stay null, never 0.

## Reconnect semantics

The cache is one more registered buffer with identical lifetime rules to
every existing registered buffer; no new reconnect path was added. The
qualification matrix excludes app-backgrounding lifecycle actions.

## Qualification plan

OFF vs ON on Experimental `:3` only: oracle 1514/1514, batch16, cold 64×64,
lifecycle x3, NO_X3_RESIDUE, fatal-signal scan, FD/RSS sanity. Performance
classed POSITIVE/NEUTRAL/NEGATIVE/INCONCLUSIVE; allocation-count reduction
alone is not a performance claim.

## Source identity

```text
branch: qualification/d0a-narrow-20260912
commit: a6cc7952861b8a63740d42bf78553573cfa0eec0
parent: fd988c45e51692c6cae4420f84466872bedf9bf6
files: InitOutput.c (+99), b3a_telemetry.c (+23/-), b3a_telemetry.h (+11/-)
```

## Rollback

Unset `TERMUX_X11_D0A`. No persistent format, API, or ABI change outside
telemetry dumps.

## Runtime A/B — 2026-09-12 (Experimental `:3` only)

APK `1.03.01-a6cc795-11.09.26` (SHA256 `3f1298...`, Build ID `e9cb1d2e`
matched). DisplayId=0 verified, external display non-target untouched.

```text
OFF (flag unset, new binary): oracle 1514/1514 exact, cell exact,
  staging marks 0, NO_X3_RESIDUE — flag-off equivalence proven
ON s1/s2/s3 (TERMUX_X11_D0A=1): oracle 1514/1514 exact x3, cell exact x3,
  R3 fallback=0, NO_X3_RESIDUE x3, fresh X PIDs each round
ON cache: hits 1985 / miss 10 per 1999-record session, identical buffer-id
  sequences across sessions, 0 continuity violations, 0 alloc/mmap on hits,
  10/10 misses carry FD_ALLOC
ON invariant: upload_logical == clone_logical per record (full upload kept)
FD baseline: 81 → 81 → 81 → 81 start across recreates (no growth)
New device fatal signals: 0 (only 09-08 historical entries)
Stable: UNTOUCHED
```

Steady-state uniform 64×64 cell medians (ms):

```text
            prepare   clone     done      FD allocs / 480 ops
OFF         0.533     0.249     0.930     480
ON s1       0.387     0.003     0.500     1
ON s2       0.338     0.003     0.635     1
ON s3(cold) 0.329     0.003     0.655     1
```

Classification: PERFORMANCE-POSITIVE for the measured uniform steady-state
path (allocation/mmap/registration/texture-recreation avoided). This validates
the cost model: the waste was repeated staging allocation/registration/clone
path, not the shader — no shader/queue/fence/renderer/DoneComposite/fallback
change was needed for the win. Scope is conservative: uniform 64×64
steady-state only, not all XFCE workloads. Varied-size
oracle rows reuse only within equal descriptors (10 misses = 10 sizes), as
designed. Allocation-count reduction is reported alongside medians, not as a
standalone claim.
