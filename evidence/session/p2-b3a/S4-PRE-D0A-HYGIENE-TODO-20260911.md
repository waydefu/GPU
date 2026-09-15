# S4 PRE-D0a HYGIENE TODO — 2026-09-11

Scope: four confirmed narrow error-path fixes before D0a. No persistent
staging/texture, queue ABI, mutex ownership strategy, CloseScreen drain,
DoneComposite semantics, predicate, shader, blend, X-byte repair, Gate A, or
Gate H changes.

## Acceptance criteria

- [x] S4-1: `OsVendorInit` checks `mmap()` against `MAP_FAILED` and cannot call
  `memset()` on `(void *)-1`.
- [x] S4-2: `LorieBuffer_recvHandleFromUnixSocket` rejects short reads and
  receive/map failures fail-closed; `xcallback(EVENT_ADD_BUFFER)` cannot
  dereference or enqueue a stale output pointer.
- [x] S4-3: Composite/Solid GPU consumers are capability-gated by
  `lorieEglHasFence()`; all fence calls check non-NULL typed procedures through
  that gate and `EGL_NO_SYNC` before wait/destroy.
- [x] S4-4: `LorieBuffer_lock` leaves lock state/pointer invalid on AHB lock
  failure; `loriePrepareAccess` releases the existing shared mutex on that
  failure. Successful paths remain unchanged.
- [x] No D0a or architecture semantics changed; no new synchronization
  primitive, generation model, queue ABI, or teardown strategy.
- [x] Existing dirty worktree changes remain intact and separable.
- [x] Minimal native target build passes.
- [x] x64 CI produces the exact-source APK and unstripped artifact with
  verified artifact digest, package identity, APK/native hashes, and matching
  ARM64 Build ID.
- [x] Runtime gate: PASS — oracle 3/3, batch16 smoke 3/3, lifecycle x3,
  `NO_X3_RESIDUE` 3/3, no new device fatal signal; ADB Gate A passed on the
  Termux-home key lane.

## Stop conditions

Stop and return for architecture review if any fix requires a mutex
reinitialize/timeout redesign, CloseScreen drain change, DoneComposite
wait/release change, new generation/epoch, new synchronization primitive,
queue ABI change, or D0a persistent resource.

## Evidence

- Base HEAD and dirty status recorded at task entry.
- Target diffs inspected before edits.
- Serena definitions/callers: `OsVendorInit`,
  `LorieBuffer_recvHandleFromUnixSocket`, `xcallback`, `LorieBuffer_lock`,
  `loriePrepareAccess`, and renderer fence call sites.
- Runtime evidence to be appended after build and Experimental `:3` gate.
