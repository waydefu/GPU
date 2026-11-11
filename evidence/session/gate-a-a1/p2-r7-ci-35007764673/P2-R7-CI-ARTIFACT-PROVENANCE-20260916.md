# Gate A P2 R7 CI artifact provenance — 2026-09-16 Artifact B `a7528bd`

## BINDING (all exact)

```text
branch: qualification/gatea-r7-20260916
local HEAD:  a7528bd25b89d0408bc15002e10bccefaeef3028
remote fork: a7528bd25b89d0408bc15002e10bccefaeef3028
CI run: 35007764673, workflow_dispatch, completed/success, single Build job
run headSha: a7528bd25b89d0408bc15002e10bccefaeef3028
url: https://github.com/waydefu/termux-x11/actions/runs/35007764673
origin branch: ABSENT (no origin push)
frozen R6 worktree: 0f1e546 UNCHANGED
```

Local HEAD = fork HEAD = CI headSha.

Nightly Release step skipped (expected: not `termux/termux-x11` master).

This packet qualifies the **build artifact**. Device still runs R6 `0f1e546`
until experimental install of this APK. Do not treat the installed R6 APK as
R7-qualified.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15298770 bytes
SHA256: c29b1c68df613d40d8bfd93b44887ffd389419d8ca5f36661d1a48b3f03f4c2c
package: com.waydefu.x11gpu
versionName: 1.03.01-a7528bd-15.09.26
Build ID (embedded == unstripped): aa1d23e7fc88048f40c450ca5bacf0506cb93b9c
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
ZIP testzip: PASS
STORED local-header mod4 failures: 0
```

Report: `apk-elf-verification/p2-r7-apk-elf-report.json`

## R7 / R6 OBSERVABILITY

Present in both embedded and unstripped `libXlorie.so`:

- `TERMUX_X11_GATEA_TEST_FAULT` / `TERMUX_X11_GATEA_TEST_ARM` / `x-test-fault-env`
- `GATEA_SUMMARY` / `r-test-fatal-pre-fence`
- R6 literals still present: `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL`,
  `x-present-copy-wait`

Unstripped nm contains:

- `present_gpu_copy_retire_or_fatal`
- `lorieGateADumpSummary`
- `lorieGateATracePresentRetire`
- `lorieGateACopyBufferId`
- `lorieGpuCopyWaitForPresentOrFatal`
- `lorieGateATraceXRequest`

Forbidden absent: `direct-to-legacy`, `CPU fallback as PASS`.

## Next

Experimental-only install of this APK, then B-2 requal (TEST env unset),
then mandatory R7 cells. Stop before R8.
