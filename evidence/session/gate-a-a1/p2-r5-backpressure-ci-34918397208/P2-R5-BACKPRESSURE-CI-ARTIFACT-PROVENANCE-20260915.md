# Gate A P2 R5 backpressure CI artifact provenance — 2026-09-15

## BINDING (all exact)

```text
branch: fix/gatea-r5-backpressure-20260915
local HEAD:  37d839323255b4830d657da3bcbf7f616bc78ad3
remote fork: 37d839323255b4830d657da3bcbf7f616bc78ad3
CI run: 34918397208, workflow_dispatch, completed/success, single Build job
run headSha: 37d839323255b4830d657da3bcbf7f616bc78ad3
url: https://github.com/waydefu/termux-x11/actions/runs/34918397208
```

First attempt. No compile/portability defect. No skip/rerun.
Local HEAD = fork HEAD = CI headSha.

The installed experimental APK remains `d9b7f60` CI **34872266646**.
This `37d8393` APK is QUALIFIED and **NOT INSTALLED**.
Do not install, ADB, or run R5 without explicit authorization.
Do not retry R5 on `d9b7f60`.
Do not open a PR or push origin.

## ARTIFACTS

```text
APK: 15233774 bytes, SHA256 31ec7037d3f1dc27836b8719ab21527e2943a21bc2763d08a2dbc51f702c1638
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-37d8393-15.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64
ZIP: testzip PASS (null), 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): cc8cee05dd7e4ae35085e33dec25bbb2229cee12 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

Verifier: `verify-r5-backpressure-apk.py`
Report: `apk-elf-verification/p2-r5-backpressure-apk-elf-report.json`

## CONTINUITY + R5 BACKPRESSURE CORRECTION

- P0/A1, P1 flag/halt, B1–B4, telemetry env literal, Uraw/Upid: PASS.
- Peek-diag + drain-wait + terminal VALIDATE literals: PASS.
- X-pump literals both binaries: `x-pump-hup` / `x-pump-io` /
  `x-pump-protocol` / `x-deferred-record-queue` /
  `x-legacy-record-dispatch` / `x-wait-clock`.
- Unstripped nm contains `lorieGateAPumpConnection` and
  `lorieActivitySendGateFrame` / `lorieActivitySendLegacyRecord` /
  `lorieActivitySendLegacyFd`.
- `lorieActivitySendLegacyPayload` is nm-missing (informational; static/inlined
  into legacy send helpers).
- Shared telemetry enable: `TERMUX_X11_GATEA_TELEMETRY` still present;
  `lorieGateATelemetryEnabled` absent from unstripped nm.
- No `direct-to-legacy` / CPU-fallback-as-PASS strings.

## VERDICT

```text
P2 R5 BACKPRESSURE CI: PASS
ARTIFACT: QUALIFIED
RUNTIME: NOT RUN
INSTALL: NOT DONE — STOP HERE
Production Gate A: BLOCKED
```
