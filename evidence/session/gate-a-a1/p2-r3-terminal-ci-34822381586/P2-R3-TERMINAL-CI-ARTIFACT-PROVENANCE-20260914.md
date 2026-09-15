# Gate A P2 R3 terminal/observability CI artifact provenance — 2026-09-14

## BINDING (all exact)

```text
branch: qualification/gatea-a1-microprobe-20260912
local HEAD:  88e3f176d5be313b7dee058da9021cfe8d09e7de
remote fork: 88e3f176d5be313b7dee058da9021cfe8d09e7de
CI run: 34822381586, workflow_dispatch, completed/success, single Build job
run headSha: 88e3f176d5be313b7dee058da9021cfe8d09e7de
url: https://github.com/waydefu/termux-x11/actions/runs/34822381586
```

First attempt. No compile/portability defect. No skip/rerun.

Parent runtime artifact `8479997` remains the **installed** experimental
APK until a later install authorization. Do not retry R3 on `8479997`.
This `88e3f17` APK is QUALIFIED and **NOT INSTALLED**.

## ARTIFACTS

```text
APK: 15188658 bytes, SHA256 7e5540a247f0a0dd1c179fc818ba2f83abd2d970fb4961588ba6f071b19b8616
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-88e3f17-14.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64
ZIP: testzip PASS (null), 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): e91c7683b3dd0ac61739f274a5eaeffaace1be12 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

Verifier: `verify-p2-r3-terminal-apk.py`
Report: `apk-elf-verification/p2-r3-terminal-apk-elf-report.json`

## CONTINUITY + REPAIR

- P0/A1, P1 flag/halt, B1–B4, telemetry env literal, Uraw/Upid: PASS.
- Peek-diag + drain-wait literals: `GATEA_BIND` / `GATEA_PEEK` /
  `GATEA_HANDLE` / `r-unbound-frame` / `GATEA_DRAIN`: PASS.
- Terminal totality: `r-tuple-mismatch` / `r-failed-send` /
  `r-duplicate-ready` / `x-fatal-after-timeout`: PASS.
- VALIDATE stages + `GATEA_VALIDATE` tag: PASS both binaries.
- Shared telemetry enable: `TERMUX_X11_GATEA_TELEMETRY` still present;
  `lorieGateATelemetryEnabled` absent from unstripped nm.
- Finite Gate A fence: `r-gatea-fence-wait` present.
- No `direct-to-legacy` / CPU-fallback-as-PASS strings.
- `gateAHasPendingDrain` is `static` (nm-missing expected).
- `lorieGateAWaiterObserve` / `lorieGateATelemetryPublished` /
  `lorieGateATelemetryRequested` are `static inline __always_inline`
  (nm-missing expected).

## VERDICT

```text
P2 R3 TERMINAL/OBSERVABILITY CI: PASS
ARTIFACT: QUALIFIED
RUNTIME: NOT RUN
INSTALL: NOT DONE — STOP HERE
Production Gate A: BLOCKED
```
