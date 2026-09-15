# Gate A P2 R3 drain-wait CI artifact provenance — 2026-09-14

## BINDING (all exact)

```text
branch: qualification/gatea-a1-microprobe-20260912
local HEAD:  84799977fdf2923c352cf1a86c00cb7e153189bf
remote fork: 84799977fdf2923c352cf1a86c00cb7e153189bf
CI run: 34791993198, workflow_dispatch, completed/success, single Build job
run headSha: 84799977fdf2923c352cf1a86c00cb7e153189bf
url: https://github.com/waydefu/termux-x11/actions/runs/34791993198
```

First attempt. No compile/portability defect.

Parent runtime artifact `6c7ee6f` is SUPERSEDED for future device cells.
Its T2 rerun 6/6, R1 oracle, R2 PASS remain valid for that old APK only.
R3 on `6c7ee6f` remains FAIL (`x-ready-timeout` after HANDLE; GL drain
never ran). Do not retry R3 on `6c7ee6f`.

## ARTIFACTS

```text
APK: 15132962 bytes, SHA256 0a9d91f6fb26ee445935d5243f0b80b3f7e0c76574fdbebcc02f0d92f20323a2
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-8479997-14.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64
ZIP: testzip PASS, 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): b072c9d2ff12f0a92258086a609b22744359654a — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

## CONTINUITY + REPAIR

- P0/A1, P1 flag/halt, B1–B4, telemetry, Uraw/Upid: PASS.
- Peek-diag: `GATEA_BIND` / `GATEA_PEEK` / `GATEA_HANDLE` / `r-unbound-frame`: PASS.
- Drain-wait: `GATEA_DRAIN` in both binaries. PASS.
- `gateAHasPendingDrain` is `static` (nm-missing expected, same class as inlined helpers).

## VERDICT

```text
P2 R3 DRAIN-WAIT CI: PASS
ARTIFACT: QUALIFIED
RUNTIME 2026-09-14: R1 oracle/stress PASS; R2 PASS;
  R3 FAIL (GATEA_DRAIN ran, no READY); PAUSED
this HEAD is the only T2-authorized artifact
Do not retry R3 on this APK until a new repair is installed
Production Gate A: BLOCKED
```

Runtime evidence: `../p2-r3-drain-runtime/`.

Verifier: `verify-p2-r3-drain-apk.py`.
