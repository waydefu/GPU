# Gate A P2 R6 CI artifact provenance — 2026-09-16 retirement `0f1e546`

## BINDING (all exact)

```text
branch: fix/gatea-r6-present-retirement-20260915
local HEAD:  0f1e54699d0b11a781f2c044fbc77505f8a53bd8
remote fork: 0f1e54699d0b11a781f2c044fbc77505f8a53bd8
CI run: 34999213228, workflow_dispatch, completed/success, single Build job
run headSha: 0f1e54699d0b11a781f2c044fbc77505f8a53bd8
run_number: 46
job: Build 104483116121 completed/success 17:07:31Z–17:12:29Z
url: https://github.com/waydefu/termux-x11/actions/runs/34999213228
origin branch: ABSENT (no origin push)
```

Local HEAD = fork HEAD = CI headSha.

Nightly Release step skipped (expected: `github.repository != termux/termux-x11`
or ref not `master`).

Historical cells stay frozen. Do not silent-retry them.

This packet qualifies the artifact. Runtime of the same SHA is recorded in
`../p2-r3-xpump-runtime/runtime-0f1e546/GATE-A-P2-R6-RUNTIME-20260916.md`.

## ARTIFACTS (downloaded from this run only)

Artifact records (all `workflow_run.id=34999213228`,
`head_sha=0f1e54699d0b11a781f2c044fbc77505f8a53bd8`):

```text
id 10409167288  termux-x11-universal-debug                         (qualified)
id 10409177303  termux-x11-unstripped-libraries-for-ndk-stack      (Build ID bind)
id 10409610758  termux-x11-sharedUid-debug                         (not used)
id 10408669539  termux-companion packages                          (not used)
```

GitHub artifact ZIP digest (universal-debug wrapper, not APK bytes):
`d3a3631b097420ad10623a96ce482b6886678a4cd55a35e7338582d07c97aac3`.

```text
APK: 15239218 bytes, SHA256 2bc4c8ba2b6a11928a3a6b76e04fcd9acf0bacfe11f88afd0a698c8c81b10851
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-0f1e546-15.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64
ZIP: testzip PASS (null), 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): 263bee5f7d41087b0bd7fa180d47fdafd12b2ecf — MATCH
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
  `lorieGpuCopyWaitForPresentOrFatal` /
  `present_gpu_copy_retire_or_fatal`.
- `lorieGateATracePresentEarlyAck` is nm-missing (informational): source still
  defines the forbidden event-32 tracer, but nothing calls it after retirement;
  `--gc-sections` dropped the unused function. Event 32 remains forbidden in the
  judge.
- Other nm-missing names (`gateACloseGeneration`, `gateADirectTryPrepare`,
  `lorieActivitySendLegacyPayload`, …) remain informational; same class as
  `95e6f96` (static / `--gc-sections`). Totality is not claimed from nm alone.
- Forbidden absent: `direct-to-legacy`, `CPU fallback as PASS`,
  `TERMUX_X11_GATEA_TEST_FAULT` (R7 still source-blocked).

## VERDICT

```text
P2 R6 retirement CI: PASS
ARTIFACT: QUALIFIED
INSTALL: DONE experimental only — SHA/Build ID MATCH; Stable PID 17922 UNTOUCHED
RUNTIME: D1 PASS / D2-INFLIGHT PASS (QUIESCENT-ADMIT) / D2-OOM PASS
R6: PASS (design-complete three cells on this artifact)
Production Gate A: BLOCKED
STOP BEFORE R7
```
