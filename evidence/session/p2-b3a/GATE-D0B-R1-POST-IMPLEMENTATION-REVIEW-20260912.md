# Gate D0b-R1 Post-implementation Review — 2026-09-12

## CURRENT AUTHORITY

```text
D0b-R1 implementation: REJECTED
D0b: HOLD
runtime qualification: NOT AUTHORIZED
```

Source under review:

```text
worktree: /root/projects/GPU加速/src/f8-ahb-d0b-r1
branch: qualification/d0b-r1-narrow-20260912
base HEAD: a6cc7952861b8a63740d42bf78553573cfa0eec0
working diff: 6 allowed files, 724 additions / 14 deletions
git diff --check: PASS
main D0a worktree: clean
```

## Sol findings

### BLOCKER 1 — Renderer can draw stale texture after failed partial upload

Severity: HIGH
Confidence: HIGH

`renderer.cpp:947-954` stores `uploadFdRegion` failure in `upload_ok` and only
logs “skipping upload”. Control then continues through blend setup and draws every
entry rectangle at `renderer.cpp:974-1005`. Consequently an invalid/malformed
D0b upload can blend stale or uninitialized texture content while the queue entry
still advances and may later receive completedSerial.

This is not fail-closed and violates:

```text
accepted rect == copied rect == uploaded rect == sampled rect
```

The current queue has no renderer-to-X failure result that could trigger the CPU
fallback after publication. Skipping draw alone would still lose the Composite.
The design must prove upload cannot fail after publication or introduce an
architecture-reviewed failure contract; the current implementation does neither.

### BLOCKER 2 — D0b mode selection is not proven cross-process

Severity: HIGH
Confidence: HIGH

The X producer and renderer are explicitly separate processes
(`lorie.h:193-207`). The implementation selects D0b independently with
`getenv("TERMUX_X11_D0B")` in X (`InitOutput.c`) and renderer
(`renderer.cpp:771-776`). A shell environment used to launch the X server does not
mutate an already separate Android renderer process environment.

No queue field, registered-buffer marker, shared-state flag, socket message, or
other producer-to-renderer mode proof was added. Therefore the producer can run
partial CPU copy while the renderer remains on full upload, or mode selection can
otherwise disagree. The writer report's requirement that the flag exist “in both
X server and renderer” is an operational assumption, not a source-level contract.

Fixing this may require a cross-process mode indicator and therefore a renewed
queue/shared-state/config architecture decision. It is outside the R1 approval.

### BLOCKER 3 — Native compile failure

Severity: MUST FIX
Confidence: HIGH

The real ARM64 native build reached compilation and failed because three new sites
treat `RegionInit` as a boolean even though it returns void:

- `InitOutput.c:2299`
- `InitOutput.c:2423`
- `InitOutput.c:2425`

See `D0B-R1-NATIVE-BUILD-VERIFY-20260912.md`.

### RISK 4 — High-risk DoneComposite path was duplicated

Confidence: MEDIUM

The diff adds a separate `lorieExaDoneD0bComposite` containing scheduling,
completion wait, quarantine, destination repair, ref decrements/releases, and
transaction reset. Although no shared queue layout or fence function changed,
this duplicates high-risk completion/release sequencing rather than minimally
reusing the existing DoneComposite path. Native/runtime proof is absent.

## Checks that did pass

- Exact branch/base binding and isolated worktree.
- Main D0a worktree remained clean.
- Only six pre-approved files changed; no `lorie.h` diff.
- `git diff --check` passed.
- Picture predicate was not widened.
- Source-side bounds calculation is overflow-aware and precedes BoxRec casts.
- Source Region accumulation precedes the single D0b publication attempt.
- FD row-copy and per-row upload pointer arithmetic are bounded in source.
- Static telemetry smoke and standalone telemetry compile passed as reported.

These checks do not override the blockers.

## Architecture gate

```text
Sampling invariant:                  NOT ACCEPTED (implementation cannot ensure upload==sample)
Bounds gate:                         VALID IN SOURCE, NOT BUILT
Refreshed region definition:         SOURCE REGION PRESENT, NOT RUNTIME-PROVEN
Copy-before-publish:                 PRESENT IN SOURCE
Queue ABI change required:           INCONCLUSIVE — cross-process mode signal unresolved
Conservative completedSerial reuse:  PARTIAL SOURCE PROOF ONLY
Failure-path reuse safety:           NOT PROVEN
New ownership semantics required:    INCONCLUSIVE
New fence semantics required:        NO CURRENT CHANGE
Stride-safe partial upload:          SOURCE DESIGN PRESENT, COMPILE/RUNTIME NOT PROVEN
High-risk lifecycle semantics touched: YES — D0b DoneComposite release path duplicated

D0b: HOLD
```

## Forbidden next steps

- Do not commit or merge the rejected diff.
- Do not build CI/APK or install/run it.
- Do not perform device/runtime/failure-injection qualification.
- Do not touch Stable `com.termux.x11` / `DISPLAY=:1`.
- Do not silently add a queue/shared-state mode bit or renderer failure ack.

## NEXT ACTION — ONE ONLY

```text
D0b-R2 architecture design: prove a cross-process producer→renderer D0b mode
contract and a no-stale-draw upload-failure contract without changing ownership,
fence, or queue semantics; otherwise keep D0b blocked.
```

Gate A remains `BLOCKED FOR CURRENT BGRA DIRECT-SAMPLING CONTRACT`.
Gate H remains `HOLD`.
Historical SIGSEGV remains `OBSERVED / NON-REPRODUCED / ROOT CAUSE UNKNOWN`.
