# Gate A P2 EXA Composite timeout-repair CI artifact provenance — 2026-09-16 `0d72332`

## BINDING (all exact)

```text
branch: fix/gatea-exa-composite-timeout-20260916
local HEAD:  0d72332c0e591b2137262d06d7dcab704be49383
remote fork: 0d72332c0e591b2137262d06d7dcab704be49383
CI run: 35049545631, workflow_dispatch, completed/success, single Build job
run headSha: 0d72332c0e591b2137262d06d7dcab704be49383
url: https://github.com/waydefu/termux-x11/actions/runs/35049545631
origin branch: ABSENT (no origin push, no PR)
frozen R6 worktree: 0f1e546 UNCHANGED
installed device APK: still a7528bd (this task did not install)
```

Local HEAD = fork HEAD = CI headSha.

Nightly Release step skipped (expected: not `termux/termux-x11` master).

No local `assembleDebug` APK was produced. Qualification uses this
`workflow_dispatch` run only.

This packet qualifies the **build artifact**. It is **not** B-2
requalification, **not** R7, and **not** an install binding.

## ARTIFACTS (downloaded from this run only)

```text
APK: 15298846 bytes
filename: termux-x11-universal-debug.apk
SHA256: 13d7f42f6bcd15379ecd353ee613c5c668fe2d7d06160ecabb34abf08d3a749e
package: com.waydefu.x11gpu
versionName: 1.03.01-0d72332-16.09.26
versionCode: 15
Build ID (embedded == unstripped): b46d1bd59c8f66327370df9fae154dbf4c53f11e
signer: b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1 CONTINUITY PASS
ZIP testzip: PASS
STORED local-header mod4 failures: 0
ABIs: arm64-v8a armeabi-v7a x86 x86_64
```

Report: `apk-elf-verification/p2-exa-timeout-apk-elf-report.json`

GitHub artifact `digest` is the ZIP wrapper, not APK bytes:
`ci-artifacts.json`.

## REPAIR / R7 / R6 OBSERVABILITY

Present in both embedded and unstripped `libXlorie.so`:

- `x-exa-composite-wait`
- `EXA GPU composite wait timeout`
- `TERMUX_X11_GATEA_TEST_FAULT` / `TERMUX_X11_GATEA_TEST_ARM` / `x-test-fault-env`
- `GATEA_SUMMARY` / `r-test-fatal-pre-fence`
- R6 literals still present: `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL`,
  `x-present-copy-wait`

Unstripped strings contain `lorieGpuCopyWaitForCompositeOrFatal`
(static helper; inlined so absent from `nm`). Unstripped `nm` still
contains:

- `present_gpu_copy_retire_or_fatal`
- `lorieGateADumpSummary`
- `lorieGateATracePresentRetire`
- `lorieGateACopyBufferId`
- `lorieGpuCopyWaitForPresentOrFatal`
- `lorieGateATraceXRequest`

Forbidden absent: `direct-to-legacy`, `CPU fallback as PASS`.

TEST env remains getenv-only; default off (`test_env_default_off`).

Shared-state ABI / R7 hooks / Present wait helper were not in the
repair diff (`InitOutput.c` + `scripts/verify_exa_composite_wait.py`
only vs `a7528bd`).

## Next

Experimental-only install of this APK, then B-2 requal (TEST env unset),
requires **new explicit authorization**. Do not start R7. Stop before R8.
Device remains `a7528bd` until that authorization.
