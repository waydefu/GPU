# Gate A P2 EXA Composite timeout repair — 2026-09-16

```
STATUS: REPAIR READY FOR B-2 REQUALIFICATION — DEVICE RUN NOT AUTHORIZED
BASE: a7528bd25b89d0408bc15002e10bccefaeef3028
WORKTREE: src/f8-ahb-gatea-exa-timeout
BRANCH: fix/gatea-exa-composite-timeout-20260916
HEAD: a7528bd (uncommitted dirty InitOutput.c + untracked scripts/verifier)
FROZEN R6: 0f1e546 UNTOUCHED
R7 WORKTREE a7528bd: UNCHANGED (still installed device candidate)
```

This is **not** B-2 requalification. **Not** R7. **Not** an APK.

## Root cause (already IDENTIFIED)

Diagnostic-02 bound 3× `PIXEL_RGB_MISMATCH` (`got == dst_px`) to 3×
`lorieGpuCopyWait` timeout then same-ms `Gcomp Done`.
`lorieExaDoneComposite` treated wait-false as successful completion.

## Repair design

Frozen invariant: **no completion proof → no successful Composite Done
visible to the client.**

When `lorieGpuCopyWait(serial, 2000)` returns false in the legacy
scheduled Done path:

1. Keep the existing `EXA GPU composite wait timeout` log (identity).
2. `gateAXFatal("x-exa-composite-wait", LORIE_GATEA_FAIL_TIMEOUT, serial)`.
3. Do **not** repair X-byte, ack, pending-dec, release, `exaCompDone++`,
   or `Gcomp Done`.
4. Timeout duration stays **2000**. No retry, no sleep, no CPU fake Over.

`serial == 0` with `scheduled > 0` is `LORIE_GATEA_FAIL_PROTOCOL`.

Direct Gate A Composite (`exaGpuComp.direct`) is unchanged
(`gateADoneDirect` already fail-stops).

Present remains `lorieGpuCopyWaitForPresentOrFatal` /
`"x-present-copy-wait"`.

## RED → GREEN

Verifier: `evidence/session/gate-a-a1/p2-r7-design/verify_exa_composite_wait.py`

- `a7528bd` / `src/f8-ahb-gatea-r7`: **FAIL**
  `done:wait-false-must-fatal` / `what` / `timeout-reason`
- repair worktree after patch: **PASS**

The test extracts `lorieExaDoneComposite`, skips the direct transaction,
and brace-matches the wait-false then-body. It is not a whole-file grep
for `Gcomp Done`.

## Code change

Two paths in the repair worktree:

1. `lorie/src/main/cpp/lorie/InitOutput.c` (+13/−3)
   - Add `lorieGpuCopyWaitForCompositeOrFatal(serial, scheduled)`
   - `what` frozen: `"x-exa-composite-wait"`
   - wait-false: keep timeout log, then `gateAXFatal(..., LORIE_GATEA_FAIL_TIMEOUT, serial)`
   - `lorieExaDoneComposite` scheduled path calls the helper **before** repair/ack/Done
2. `scripts/verify_exa_composite_wait.py` (untracked copy of the evidence verifier)

## Wait-caller audit (not patched)

| Caller | Semantics | Safe? | Action |
|---|---|---|---|
| `lorieGpuCopyWaitForPresentOrFatal` | Present wait-or-fatal | already safe | none |
| `lorieGpuCopyWaitForCompositeOrFatal` | Composite Done wait-or-fatal | **this repair** | patched |
| `lorieExaSolid` retry/fallback waits | ignore return, then reschedule or CPU solid | different semantics / unproven | FINDING, not patched |
| `lorieExaDoneSolid` | timeout then still repair X-byte + ack | **same defect pattern** | FINDING, not patched |
| `lorieExaCopy` retry/fallback waits | ignore return, then reschedule or CPU copy | different semantics / unproven | FINDING, not patched |
| `lorieExaDoneCopy` | timeout then still ack | **same defect pattern** | FINDING, not patched |
| `lorieExaComposite` retry wait | ignore return, then try another GPU blit | different semantics / unproven | FINDING, not patched |
| `lorieExaComposite` CPU-fallback wait | ignore return, then CPU Over on dest | different semantics / unproven | FINDING, not patched |

DoneSolid / DoneCopy were **not** bound by diagnostic-02. Scope stays Composite Done only.

## Verification

- targeted RED→GREEN PASS (`verify_exa_composite_wait.py`)
- `verify_r7_support.py` PASS on frozen `a7528bd`; also PASS on repair tree after applying committed `xserver.patch` onto gitlink `65d790bd` (then reset; not part of the repair)
- `test-judge-r7.py` 16/16 OK
- `git diff --check` clean
- timeout→Done on wait-false: unreachable (noreturn `gateAXFatal`)
- ACK/release on wait-false: unreachable
- `lorie.h` / `renderer.cpp` / `cmdentrypoint.cpp` / `xserver.patch`
  identical to `a7528bd`
- TEST env / R7 hooks / ABI unchanged
- frozen R6 `0f1e546` untouched
- APK build **not run** (not authorized)
- device **not run**

## Next (not this task)

Authorize B-2 requalification on a built/installed APK from this lineage.
Do not start R7. Do not silent-retry `r1-unset-oracle`.
