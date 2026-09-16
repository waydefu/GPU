# Gate A P2 EXA Composite timeout repair — 2026-09-16

```
STATUS: B-2 BLOCKED — R1-unset FAIL (timeout fail-stop serial 2370); no timeout→Done
BASE: a7528bd25b89d0408bc15002e10bccefaeef3028
WORKTREE: src/f8-ahb-gatea-exa-timeout
BRANCH: fix/gatea-exa-composite-timeout-20260916
HEAD: 0d72332c0e591b2137262d06d7dcab704be49383
CI: 35049545631 workflow_dispatch success
APK: 1.03.01-0d72332-16.09.26 SHA256 13d7f42f…749e Build ID b46d1bd5…f11e
INSTALLED: YES experimental only (device 0d72332)
FROZEN R6: 0f1e546 UNTOUCHED
```

This is **not** B-2 requalification. **Not** R7. **Not** an install.

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
2. `scripts/verify_exa_composite_wait.py` (committed copy of the evidence verifier)

Commit: `0d72332c0e591b2137262d06d7dcab704be49383`
`fix(gatea): fail-stop EXA Composite wait timeout`

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
- APK **QUALIFIED** CI **35049545631** (`1.03.01-0d72332-16.09.26`,
  SHA256 `13d7f42f6bcd15379ecd353ee613c5c668fe2d7d06160ecabb34abf08d3a749e`,
  Build ID `b46d1bd59c8f66327370df9fae154dbf4c53f11e` MATCH)
  Provenance: `evidence/session/gate-a-a1/p2-exa-timeout-ci-35049545631/`
- device **INSTALLED** `0d72332`; B-2 R1 unset **FAIL** (timeout fail-stop serial 2370; no timeout→Done). Cell `runtime-0d72332/r1-unset-oracle/`.

## Next (not this task)

Do not silent-retry R1-unset. Do not start R2–R6-D1 or R7.
