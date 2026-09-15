# Gate A P2 R3 X-pump CI artifact provenance — 2026-09-15

## BINDING (all exact)

```text
branch: qualification/gatea-xpump-20260914
local HEAD:  d9b7f60f24e722205891f1ce941816393ae4c695
remote fork: d9b7f60f24e722205891f1ce941816393ae4c695
CI run: 34872266646, workflow_dispatch, completed/success, single Build job
run headSha: d9b7f60f24e722205891f1ce941816393ae4c695
url: https://github.com/waydefu/termux-x11/actions/runs/34872266646
```

First attempt. No compile/portability defect. No skip/rerun.
Local HEAD = fork HEAD = CI headSha.

The installed experimental APK remains `88e3f17` CI **34822381586**.
This `d9b7f60` APK is QUALIFIED and **NOT INSTALLED**.
Do not install, ADB, or run R3 without a new explicit authorization.
Do not retry R3 on `88e3f17`, `8479997`, `6c7ee6f`, or `98b0011`.
Do not open a PR or push origin.

## ARTIFACTS

```text
APK: 15233758 bytes, SHA256 255cc37d12dd052c32d2b8ba89af3029034f59f7e01b65bd61cffd50d86737a2
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-d9b7f60-14.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64
ZIP: testzip PASS (null), 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): 2b02bf139236d45aaa24a95fa8609cca0d956e7d — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

Verifier: `verify-p2-r3-xpump-apk.py`
Report: `apk-elf-verification/p2-r3-xpump-apk-elf-report.json`

## CONTINUITY + X-PUMP

- P0/A1, P1 flag/halt, B1–B4, telemetry env literal, Uraw/Upid: PASS.
- Peek-diag + drain-wait + terminal VALIDATE literals: PASS.
- X-pump literals both binaries: `x-pump-hup` / `x-pump-io` /
  `x-pump-protocol` / `x-deferred-record-queue` /
  `x-legacy-record-dispatch` / `x-wait-clock`.
- Unstripped nm contains `lorieGateAPumpConnection` and
  `lorieActivitySendGateFrame` / `lorieActivitySendLegacyRecord` /
  `lorieActivitySendLegacyFd`.
- `lorieActivitySendLegacyPayload` is nm-missing (informational; likely
  inlined into the record helper). Same class as other static/inlined
  helpers (`gateAHasPendingDrain`, header inlines).
- Shared telemetry enable: `TERMUX_X11_GATEA_TELEMETRY` still present;
  `lorieGateATelemetryEnabled` absent from unstripped nm.
- No `direct-to-legacy` / CPU-fallback-as-PASS strings.

## VERDICT

```text
P2 R3 XPUMP CI: PASS
ARTIFACT: QUALIFIED
RUNTIME: NOT RUN
INSTALL: NOT DONE — STOP HERE
Production Gate A: BLOCKED
```
