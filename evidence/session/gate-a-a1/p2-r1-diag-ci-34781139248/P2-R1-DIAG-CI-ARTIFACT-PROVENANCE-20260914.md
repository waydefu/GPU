# Gate A P2 R1 diagnostic CI artifact provenance — 2026-09-14

## BINDING (all exact)

```text
branch: qualification/gatea-a1-microprobe-20260912
local HEAD:  dd81ac056bd3fe84d757c63c5ee484a2037ebb4f
remote fork: dd81ac056bd3fe84d757c63c5ee484a2037ebb4f (ls-remote verified)
CI run: 34781139248, workflow_dispatch, completed/success, single Build job
run headSha: dd81ac056bd3fe84d757c63c5ee484a2037ebb4f
```

First attempt. No compile/portability defect. Narrow-fix clause not exercised.

Parent runtime artifact `15caa00` / `d69aff2c…0e8d` / Build ID `33a3b67f…`
is SUPERSEDED for future device cells. Historical Phase 1 R1 PROTO=0
SIGSEGV remains OBSERVED on that old artifact.

## ARTIFACTS

```text
universal-debug artifact: 10324878206 (7,434,317 bytes zip)
unstripped artifact:      10325327584 (28,590,564 bytes zip)
APK: 15132670 bytes, SHA256 cc0058d8b90d2bdc6829051b1e8c398da171611ab1712a207e2d4f508f2ad459
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-dd81ac0-13.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64 (all four libXlorie.so present)
ZIP: testzip PASS, 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): 0892201de126af9e9b5a06d44ea1c0fbd5cd33a4 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

CI `assembleDebug` linked `libXlorie.so` on all four ABIs
(`[538/538]`, `[540/540]`, `[535/535]`, `[535/535]`); no `: error:` in
the four `build_stdout_Xlorie.txt` logs.

## CONTINUITY

- P0/A1: `GATEA_A1` in both binaries; `gateaA1MicroprobeRun` unstripped-only.
  PASS.
- P1: `TERMUX_X11_GATEA_PROTO` + `GATEA_FATAL_HALT` in both binaries. PASS.
- B1–B4 fail-stop literals: all present in both binaries. PASS.
- Telemetry flag `TERMUX_X11_GATEA_TELEMETRY` in both binaries. PASS.

## DIAGNOSTIC PROVENANCE

```text
p2a3CrashHandler unstripped: 0xed65c (was 0xed63c on 15caa00)
handler span: 0xed65c .. 0xef00c (~1396 B larger than 15caa00)
Uraw marker in both ELFs (stored as "Uraw"; trailing space is an immediate)
Upid pid marker in both ELFs (stored as "Upid pid"; '=' is an immediate)
p2a3DumpUraw / p2a3PutHex64: inlined into handler at -O2 (nm absent except
p2a3PutHex64.H); not a failure.
```

Original-fault authority remains **siginfo + Uraw**, not `xorg_backtrace()`.

## VERDICT

```text
P2 R1 DIAGNOSTIC CI: PASS
ARTIFACT: QUALIFIED (identity/integrity/signer/BuildID)
PROVENANCE: PASS
RUNTIME: NOT RUN
this HEAD is the only T2-authorized artifact
SIGSEGV: OBSERVED / ROOT CAUSE NOT YET PROVEN
Stable: UNTOUCHED
HDMI: UNTOUCHED
Production Gate A: BLOCKED
```

Full machine report: `apk-elf-verification/p2-r1-diag-apk-elf-report.json`.
Verifier: `verify-p2-r1-diag-apk.py`.
