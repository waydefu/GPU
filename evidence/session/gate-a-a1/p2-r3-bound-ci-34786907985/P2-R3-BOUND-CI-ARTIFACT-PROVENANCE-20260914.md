# Gate A P2 R3 bound-tuple repair CI artifact provenance — 2026-09-14

## BINDING (all exact)

```text
branch: qualification/gatea-a1-microprobe-20260912
local HEAD:  98b001129682a50eb43180e29bc57ac03556dae3
remote fork: 98b001129682a50eb43180e29bc57ac03556dae3 (ls-remote verified)
CI run: 34786907985, workflow_dispatch, completed/success, single Build job
run headSha: 98b001129682a50eb43180e29bc57ac03556dae3
url: https://github.com/waydefu/termux-x11/actions/runs/34786907985
```

First attempt. No compile/portability defect. Narrow-fix clause not exercised.

Parent runtime artifact `dd81ac0` / `cc0058d8…d459` / Build ID `0892201d…`
is SUPERSEDED for future device cells. Historical Phase 1 R1 PROTO=0
SIGSEGV on `15caa00` remains OBSERVED. `dd81ac0` R1/R2 PASS remains valid
for that old artifact only; do not install `dd81ac0` or `15caa00` for new cells.

## ARTIFACTS

```text
universal-debug artifact: 10327226347 (7,433,999 bytes zip)
unstripped artifact:      10326518038 (28,589,364 bytes zip)
APK: 15132398 bytes, SHA256 e547eadbbd33f8f2fdeb6efa650094b9f0103177721068392dbd353b4a211760
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-98b0011-13.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64 (all four libXlorie.so present)
ZIP: testzip PASS, 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
Build ID (both): 520533123eec488db553e2610b32e263968266cf — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

CI `assembleDebug` linked `libXlorie.so` on all four ABIs
(`[538/538]`, `[540/540]`, `[535/535]`, `[535/535]`); no `: error:` in
the four `build_stdout_Xlorie.txt` logs. `activity.cpp` and `renderer.cpp`
were compiled on every ABI.

## CONTINUITY

- P0/A1: `GATEA_A1` in both binaries; `gateaA1MicroprobeRun` unstripped-only.
  PASS.
- P1: `TERMUX_X11_GATEA_PROTO` + `GATEA_FATAL_HALT` in both binaries. PASS.
- B1–B4 fail-stop literals: all present in both binaries. PASS.
- Telemetry flag `TERMUX_X11_GATEA_TELEMETRY` in both binaries. PASS.
- Diagnostic `Uraw` / `Upid pid` in both binaries. PASS.
- Repair: `r-rebind-busy` in both binaries; `lorieGateABoundTuple` present in
  unstripped nm. `gateABindFromState` is `static` (nm absent is expected).

## DIAGNOSTIC PROVENANCE

```text
p2a3CrashHandler unstripped: 0xed65c (unchanged vs dd81ac0)
Uraw / Upid pid markers retained
```

Original-fault authority remains **siginfo + Uraw**, not `xorg_backtrace()`.

## VERDICT

```text
P2 R3 REPAIR CI: PASS
ARTIFACT: QUALIFIED (identity/integrity/signer/BuildID)
PROVENANCE: PASS
RUNTIME (later, same day): R1 T2 6/6 + oracle/stress PASS; R2 PASS;
  R3 FAIL (bind live, no READY). SUPERSEDED by 6c7ee6f then 8479997.
Do not retry R3 on this APK.
Production Gate A: BLOCKED
Stable: UNTOUCHED
HDMI: UNTOUCHED
```

Full machine report: `apk-elf-verification/p2-r3-bound-apk-elf-report.json`.
Verifier: `verify-p2-r3-bound-apk.py`.
