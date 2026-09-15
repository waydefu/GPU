# Gate A P2 R6 CI artifact provenance — 2026-09-15

## BINDING (all exact)

```text
branch: qualification/gatea-r6-20260915
local HEAD:  936955397619091b48c8e717f28b2cd187d79065
remote fork: 936955397619091b48c8e717f28b2cd187d79065
CI run: 34926730189, workflow_dispatch, completed/success, single Build job
run headSha: 936955397619091b48c8e717f28b2cd187d79065
run_attempt: 1
run_number: 43
job: Build 104246256398 completed/success in 5m9s
url: https://github.com/waydefu/termux-x11/actions/runs/34926730189
```

First attempt. No compile/portability defect. No skip/rerun.
Local HEAD = fork HEAD = CI headSha.

Nightly Release step skipped (expected: `github.repository != termux/termux-x11`
or ref not `master`).

No PR. No origin push. No force.

The installed experimental APK remains `37d8393` CI **34918397208**.
This `9369553` APK is QUALIFIED and **NOT INSTALLED**.
Do not install, ADB, or run R6-D1/D2 without explicit authorization.
Do not start R7.
Do not open a PR or push origin.

Rollback: keep device + `src/f8-ahb-gatea-r5-fix` on `37d8393`; drop only
`fork/qualification/gatea-r6-20260915`. Never force-push
`fix/gatea-r5-backpressure-20260915`.

## ARTIFACTS (downloaded from this run only)

Artifact records (all `workflow_run.id=34926730189`,
`head_sha=936955397619091b48c8e717f28b2cd187d79065`):

```text
id 10380485570  termux-x11-universal-debug                         (qualified)
id 10380435836  termux-x11-sharedUid-debug                         (not used)
id 10380430829  termux-x11-unstripped-libraries-for-ndk-stack      (Build ID bind)
id 10380004361  termux-companion packages                          (not used)
```

```text
APK: 15237854 bytes, SHA256 02baccbfd745dffcaa62699452c386710d5a7cf1b63217ea293141e06d98af7f
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-9369553-15.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64
ZIP: testzip PASS (null), 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): 82136dd9ebd230b8bf6d655f334ac40e4be998a8 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

Verifier: `verify-r6-apk.py`
Report: `apk-elf-verification/p2-r6-apk-elf-report.json`

## CONTINUITY + R6 OBSERVABILITY

- P0/A1, P1 flag/halt, B1–B4, telemetry env literal, Uraw/Upid: PASS.
- Peek-diag + drain-wait + terminal VALIDATE literals: PASS.
- X-pump literals both binaries: `x-pump-hup` / `x-pump-io` /
  `x-pump-protocol` / `x-deferred-record-queue` /
  `x-legacy-record-dispatch` / `x-wait-clock`.
- R6 getenv literal both binaries:
  `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL`.
- Unstripped nm contains `lorieGateAPumpConnection`,
  `lorieActivitySendGateFrame` / `lorieActivitySendLegacyRecord` /
  `lorieActivitySendLegacyFd`, plus R6 C ABI
  `lorieGateATraceXRequest` / `lorieGateATraceXCallback` /
  `lorieGateAPresentRequeueShouldFail` / `lorieGateATracePresentEarlyAck`.
- `lorieActivitySendLegacyPayload` remains nm-missing (informational; same
  class as R5).
- Shared telemetry enable: `TERMUX_X11_GATEA_TELEMETRY` still present;
  `lorieGateATelemetryEnabled` absent from unstripped nm.
- Forbidden absent: `direct-to-legacy`, `CPU fallback as PASS`,
  `TERMUX_X11_GATEA_TEST_FAULT` (R7 still source-blocked).

## VERDICT

```text
P2 R6 CI: PASS
ARTIFACT: QUALIFIED
RUNTIME: NOT RUN
INSTALL: NOT DONE — STOP HERE
Production Gate A: BLOCKED
```
