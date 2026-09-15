# Gate A P2 R3 peek-diag CI artifact provenance — 2026-09-14

## BINDING (all exact)

```text
branch: qualification/gatea-a1-microprobe-20260912
local HEAD:  6c7ee6fa9f5b15b408270ea11ee7f53afc854037
remote fork: 6c7ee6fa9f5b15b408270ea11ee7f53afc854037 (ls-remote verified)
CI run: 34789717269, workflow_dispatch, completed/success, single Build job
run headSha: 6c7ee6fa9f5b15b408270ea11ee7f53afc854037
url: https://github.com/waydefu/termux-x11/actions/runs/34789717269
```

First attempt. No compile/portability defect.

Parent runtime artifact `98b0011` / `e547eadb…1760` / Build ID `52053312…`
is SUPERSEDED for future device cells. Its R1+R2 PASS remains valid for that
old APK only. R3 on `98b0011` remains FAIL (`x-ready-timeout`, bind live via
`r-hup`, `GATEA_EVENT=0`). Do not retry R3 on `98b0011`.

## ARTIFACTS

```text
universal-debug artifact: 10327750973 (7,434,669 bytes zip)
unstripped artifact:      10327681248 (28,589,851 bytes zip)
APK: 15132590 bytes, SHA256 d20e6091817db1ba7eb449f34a0a967ff61d498b42ab0ae1b38f9591d11a4e8a
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-6c7ee6f-13.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64
ZIP: testzip PASS, 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): 49be84eaf4ded3e876f530b132ab25f6099aae00 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

## CONTINUITY + DIAGNOSTIC

- P0/A1, P1 flag/halt, B1–B4, telemetry, Uraw/Upid: PASS.
- Repair: `r-rebind-busy`, `GATEA_BIND`, `GATEA_PEEK`, `GATEA_HANDLE`,
  `r-unbound-frame` in both binaries. PASS.

## VERDICT

```text
P2 R3 PEEK-DIAG CI: PASS
ARTIFACT: QUALIFIED
RUNTIME (later, same day): R1 T2 rerun 6/6 + oracle/stress PASS;
  R2 PASS; R3 FAIL (HANDLE live, GL drain never ran). SUPERSEDED by 8479997.
Do not retry R3 on this APK.
Production Gate A: BLOCKED
```

Later runtime: `../p2-r3-diag-runtime/`. Current authority: `HANDOFF.md`.

Verifier: `verify-p2-r3-diag-apk.py`.
