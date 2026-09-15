# Gate A P2 CI artifact provenance — 2026-09-13

## BINDING (all exact)

```text
branch: qualification/gatea-a1-microprobe-20260912
local HEAD:  82a87f4a99ae4b1d4e09d6c74a735cd40b6e73e2
remote fork: 82a87f4a99ae4b1d4e09d6c74a735cd40b6e73e2 (ls-remote verified)
CI run: 34716168485, workflow_dispatch, completed/success, single Build job
run headSha: 82a87f4a99ae4b1d4e09d6c74a735cd40b6e73e2
```

No compile defect: first attempt succeeded (P2 authorized narrow-fix clause
not exercised).

## ARTIFACTS

```text
universal-debug artifact: 10303834673 (7,383,999 bytes zip)
unstripped artifact:      10304198663 (28,423,198 bytes zip)
APK: 15044354 bytes, SHA256 f9fce1b35bc9b7760061f6b225c916118efb2441b69609ab8146aecb8028adba
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-82a87f4-12.09.26
ARM64 member: present
ZIP: testzip PASS, 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed
ARM64 unstripped libXlorie.so SHA256: 4579de8755098411cd132e951c9d0412abb7a9985df93b0765e61ecf734ae264
ARM64 embedded libXlorie.so SHA256:   e8743b4dfa91bcfaa20771076f94d0b408bc64551ab9e03a00f84c4b3b20e20e
Build ID (both): 6a69205c9211ad115ed58f5ac7193ac08e628023 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

## CONTINUITY

- P0/A1: `GATEA_A1` in both binaries; `gateaA1MicroprobeRun` unstripped-only
  (hidden visibility preserved). PASS.
- P1: `TERMUX_X11_GATEA_PROTO` + `GATEA_FATAL_HALT` in both binaries. PASS.

## P2 PROVENANCE

Fail-stop literals present in BOTH binaries (embedded + unstripped):

```text
x-direct-not-success, x-post-unlock-revalidate, r-gatea-fence-wait,
r-gatea-consume, x-publish-no-lease — all true/true
```

Unstripped text symbols found (6/14): `consumeGateAComposite`,
`gateAEnsureReady`, `gateAPairOverlapsBuffer`, `gateAPreFail`,
`gateAReadyStill`, `gateAWaitTerminal`.

Missing from symbol table (8/14, informational): `gateADirectPublishRect`,
`gateADirectTryPrepare`, `gateADoneDirect`, `gateAFencePublishGateA`,
`gateAIsReady`, `gateALookupDirect`, `gateAPairRelockCpu`,
`gateAPairUndoReserve`. All are single-call-site `static` functions —
inlined at -O2, which removes the symbol while retaining the code (proven
by the fail-stop literals above, which live inside those very functions).
Per the round rule this is NOT a failure: authority is exact source commit
→ CI head binding → all-ABI compilation → ELF/APK provenance.

Finite-fence / no-`EGL_FOREVER`-on-Gate-A / accessor wiring / lease state /
fail-stop retention are source-proven (static review) and compiled on every
CI ABI (Build success); the binary literals above confirm the P2 paths
survived into the shipped objects. Legacy CPU-upload fallback remains
unreachable from the direct branch by construction (separate code path,
no shared call edge).

## VERDICT

```text
P2 CI: PASS
ARTIFACT: QUALIFIED (identity/integrity/signer/BuildID; provenance only)
PROVENANCE: PASS
RUNTIME: NOT RUN (forbidden this round; no ADB/device/install)
Stable: UNTOUCHED (no device operation at all)
```

Full machine report: `p2-ci-34716168485/apk-elf-verification/p2-apk-elf-report.json`.
Verifier: `p2-ci-34716168485/verify-p2-apk.py`.
