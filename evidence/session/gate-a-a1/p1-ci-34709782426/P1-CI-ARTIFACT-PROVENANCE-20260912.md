# Gate A P1 CI artifact provenance — 2026-09-12/13

## BINDING (all exact)

```text
branch: qualification/gatea-a1-microprobe-20260912
local HEAD:  5e9eb2a6f2a05a0c8d50c49727519b61b2477302
remote fork: 5e9eb2a6f2a05a0c8d50c49727519b61b2477302 (ls-remote verified)
CI run: 34709782426, workflow_dispatch, completed/success
run headSha: 5e9eb2a6f2a05a0c8d50c49727519b61b2477302
```

No compile defect this round: first attempt succeeded on all ABIs (the LP32
align lesson from P0 CI remains encoded in member-alignment asserts).

## ARTIFACTS

```text
universal-debug artifact: 10303285573 (7,357,981 bytes zip)
unstripped artifact:      10303091005 (28,338,112 bytes zip)
APK: 14982622 bytes, SHA256 645127f88df05596f9f4ed9b17abee47882ed3637fc02a1693ed555aab7d1fd0
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-5e9eb2a-12.09.26
ARM64 member: present
ZIP: testzip PASS, 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed
ARM64 unstripped libXlorie.so SHA256: 0ca23d8fecf04add3fbdb7cefa68e8e25f37266adc56fd6719ca6356c2c3bc95
ARM64 embedded libXlorie.so SHA256:   eb110a4224c378a64726ab311ec4c89aa3a7de5b25e44d608f899ff657054abc
Build ID (both): 6f3e1933928fabb4c28b1a964a18e2e674b47792 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

## P0 CONTINUITY

`GATEA_A1` strings in both binaries; `gateaA1MicroprobeRun` in unstripped only
(hidden visibility preserved). Base behavior intact.

## P1 PRESENCE (better than minimum)

P1 flag literal (`TERMUX_X11_GATEA_PROTO`) and fatal-halt tag
(`GATEA_FATAL_HALT`) present in BOTH binaries. Unstripped text symbols include
the full P1 surface: `gateASendFrame`, `gateASendRegisterFailed`,
`gateAFatalFromInput`, `gateABroadcastGateAFailed`, `gateAXFindLocked`,
`lorieGateAActive/Shared/BoundTuple/EnqueueImport/ImportBusy/
RegistryCloseGeneration/RegistryMarkChecked`, plus statics (`gateAPending`,
`gateAReady`, `gateAXRegistry`, mutexes, bound tuple, overflow flag).
Uncalled globals were retained by the linker here; absence would still not have
been failure per the round rule — but presence is recorded.

## VERDICT

```text
P1 CI: PASS
ARTIFACT: QUALIFIED (identity/integrity/signer/BuildID; provenance only)
PROVENANCE: PASS
RUNTIME: NOT RUN (forbidden this round; no ADB/device/install)
Stable: UNTOUCHED (no device operation at all)
```

Full machine report: `p1-ci-34709782426/apk-elf-verification/p1-apk-elf-report.json`.
Verifier: `p1-ci-34709782426/verify-p1-apk.py`.
