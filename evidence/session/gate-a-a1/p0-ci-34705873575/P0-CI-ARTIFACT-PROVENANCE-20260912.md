# Gate A P0 CI artifact provenance — 2026-09-12

## BINDING (all exact)

```text
branch: qualification/gatea-a1-microprobe-20260912
local HEAD:  97401bce514fa7d43be80df271e163669f849746
remote fork: 97401bce514fa7d43be80df271e163669f849746 (ls-remote verified)
CI run: 34705873575, workflow_dispatch, completed/success
run headSha: 97401bce514fa7d43be80df271e163669f849746
```

First dispatched run 34705593764 (HEAD 2844a18) FAILED on x86 with two real
defects: `_Alignof(struct LorieGateAProtocol)==8` and `_Alignof(struct
LorieGateAFrame)==8` are false on LP32 (uint64_t aligns to 4 on i386).
Fixed in 97401bc by asserting 8-alignment of the 64-bit members instead
(offsets identical on LP32/LP64); no layout/semantic change. Local ARM64
recompile passed before re-push.

## ARTIFACTS

```text
universal-debug artifact: 10301384852 (7,337,671 bytes zip)
unstripped artifact:      10301609478 (28,252,855 bytes zip)
APK: 14957330 bytes, SHA256 75068288604802724abb960314d94f8085d15eacc02d2df80e163155e7f3f703
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-97401bc-12.09.26
ARM64 member: present
ZIP: testzip PASS, 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed
ARM64 unstripped libXlorie.so SHA256: f4ff6e87ab43cc2d06b27640eacbfbade65e291e25ef224a5de933b72eaf069a
ARM64 embedded libXlorie.so SHA256:   49ca64b79b9a271dd8744f255d5bd89582fea4f0ccc53621cab67f955a486d9d
Build ID (both): cb87eb7f4057fe838fb6edff009de15b66395662 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

## P0 PRESENCE (informational)

`TERMUX_X11_GATEA_PROTO` literal and `lorieGateA*` text symbols are absent from
both binaries — consistent-with-design: P0 is unused static-inline foundation
(discarded at link), and CI compiled the assert-guarded header on all four ABIs
(x86 failure then fix proves the asserts actually execute). A1 markers intact
(`GATEA_A1` strings in both, `gateaA1MicroprobeRun` in unstripped).

## VERDICT

```text
P0 CI: PASS
ARTIFACT: QUALIFIED (identity/integrity/signer/BuildID; provenance only)
PROVENANCE: PASS
RUNTIME: NOT RUN (forbidden this round; no ADB/device/install)
Stable: UNTOUCHED (no device operation at all)
```

Full machine report: `p0-ci-34705873575/apk-elf-verification/p0-apk-elf-report.json`.
Verifier: `p0-ci-34705873575/verify-p0-apk.py`.
