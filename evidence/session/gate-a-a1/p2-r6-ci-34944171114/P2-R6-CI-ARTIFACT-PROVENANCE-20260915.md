# Gate A P2 R6 CI artifact provenance — 2026-09-15 wait-or-fatal `95e6f96`

## BINDING (all exact)

```text
branch: qualification/gatea-r6-20260915
local HEAD:  95e6f9602b0146ee190870f84a34aad822ef666f
remote fork: 95e6f9602b0146ee190870f84a34aad822ef666f
CI run: 34944171114, workflow_dispatch, completed/success, single Build job
run headSha: 95e6f9602b0146ee190870f84a34aad822ef666f
run_number: 45
job: Build 104299542358 completed/success 07:55:15Z–07:58:39Z
url: https://github.com/waydefu/termux-x11/actions/runs/34944171114
```

First PASS after KEEP FAIL run **34943831800** (`7092d0c`, malformed
`xserver.patch` hunk counts). No skip of that red. No origin/PR/force.

Local HEAD = fork HEAD = CI headSha.

Nightly Release step skipped (expected: `github.repository != termux/termux-x11`
or ref not `master`).

Rollback source remains `src/f8-ahb-gatea-r5-fix` `37d8393`. Historical
`runtime-9369553/` cells stay frozen. Do not silent-retry `9369553` D2.

## ARTIFACTS (downloaded from this run only)

Artifact records (all `workflow_run.id=34944171114`,
`head_sha=95e6f9602b0146ee190870f84a34aad822ef666f`):

```text
id 10386706158  termux-x11-universal-debug                         (qualified)
id 10386790786  termux-x11-unstripped-libraries-for-ndk-stack      (Build ID bind)
id 10386483372  termux-x11-sharedUid-debug                         (not used)
id 10386960299  termux-companion packages                          (not used)
```

```text
APK: 15238882 bytes, SHA256 60c36b4f59c38d13db6fe6c366e6f115a720ec1d6946d057b3ec41551b12f628
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-95e6f96-15.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64
ZIP: testzip PASS (null), 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): 1188e1cabf3b78285e7e5fbedcf64f0b5e7d44f9 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

Verifier: `verify-r6-apk.py`
Report: `apk-elf-verification/p2-r6-apk-elf-report.json`

## CONTINUITY + R6 OBSERVABILITY

- P0/A1, P1 flag/halt, B1–B4, telemetry env literal, Uraw/Upid: PASS.
- Peek-diag + drain-wait + terminal VALIDATE literals: PASS.
- X-pump literals both binaries.
- R6 getenv literal both binaries:
  `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL`.
- Wait-or-fatal halt tag both binaries: `x-present-copy-wait`.
- Unstripped nm contains `lorieGateAPumpConnection`,
  `lorieActivitySendGateFrame` / `lorieActivitySendLegacyRecord` /
  `lorieActivitySendLegacyFd`, plus R6 C ABI
  `lorieGateATraceXRequest` / `lorieGateATraceXCallback` /
  `lorieGateAPresentRequeueShouldFail` /
  `lorieGateATracePresentRequeueFailed` /
  `lorieGateATracePresentAckAfterCompleted` /
  `lorieGpuCopyWaitForPresentOrFatal`.
- `lorieGateATracePresentEarlyAck` is nm-missing (informational): source still
  defines the forbidden event-32 tracer, but nothing calls it after wait-or-fatal;
  `--gc-sections` dropped the unused function. Event 32 remains forbidden in the
  judge.
- `lorieActivitySendLegacyPayload` remains nm-missing (informational; same
  class as R5).
- Forbidden absent: `direct-to-legacy`, `CPU fallback as PASS`,
  `TERMUX_X11_GATEA_TEST_FAULT` (R7 still source-blocked).

## VERDICT

```text
P2 R6 wait-or-fatal CI: PASS
ARTIFACT: QUALIFIED
RUNTIME: D2-INFLIGHT FAIL kept (X 21317); D2-OOM NOT RUN
INSTALL: DONE experimental only — SHA/Build ID MATCH; Stable PID 1004 UNTOUCHED
Production Gate A: BLOCKED
```
