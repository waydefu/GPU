# Gate A P2 B1–B4 CI artifact provenance — 2026-09-14

## BINDING (all exact)

```text
branch: qualification/gatea-a1-microprobe-20260912
local HEAD:  15caa00908aa9d1f1c4a78bb630aa24a93e7e4cd
remote fork: 15caa00908aa9d1f1c4a78bb630aa24a93e7e4cd (ls-remote verified)
CI run: 34772571553, workflow_dispatch, completed/success, single Build job
run headSha: 15caa00908aa9d1f1c4a78bb630aa24a93e7e4cd
```

First attempt. No compile/portability defect. Narrow-fix clause not exercised.

## ARTIFACTS

```text
universal-debug artifact: 10322199758 (7,430,870 bytes zip)
unstripped artifact:      10322980586 (28,580,322 bytes zip)
APK: 15131390 bytes, SHA256 d69aff2c98d6a3442ff11151ba5858ef6b9537663a94b2f62302766da94f0e8d
package: com.waydefu.x11gpu / versionCode 15 / versionName 1.03.01-15caa00-13.09.26
contained ABI: arm64-v8a, armeabi-v7a, x86, x86_64 (all four libXlorie.so present)
ZIP: testzip PASS, 493 members, 0 duplicates, STORED 259/259 4-byte aligned
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed PASS
ARM64 unstripped libXlorie.so SHA256: recorded in p2-b1b4-apk-elf-report.json
Build ID (both): 33a3b67f3c4213a1611f1fcb18232f2acb2f9d79 — MATCH
signer: expected experimental cert b6da0148…ee5e1 present — CONTINUITY PASS
```

CI `assembleDebug` linked `libXlorie.so` on all four ABIs
(`[538/538]`, `[540/540]`, `[535/535]`, `[535/535]`); no `: error:` in
the four `build_stdout_Xlorie.txt` logs.

## CONTINUITY

- P0/A1: `GATEA_A1` in both binaries; `gateaA1MicroprobeRun` unstripped-only.
  PASS.
- P1: `TERMUX_X11_GATEA_PROTO` + `GATEA_FATAL_HALT` in both binaries. PASS.

## B1–B4 / TELEMETRY PROVENANCE

Fail-stop / identity / lifecycle literals present in BOTH binaries:

```text
r-gatea-DIRECT_LOOKUP_FAIL, r-gatea-stale-direct-meta,
r-gatea-direct-identity, x-direct-slot-not-consumed,
x-direct-not-success, x-post-unlock-revalidate, r-gatea-fence-wait,
x-publish-no-lease, x-unregister-send, x-generation-close-send,
r-unregister-missing, r-close-not-empty — all true/true
```

Telemetry flag `TERMUX_X11_GATEA_TELEMETRY` present in both binaries.
Exact-opt-in (`"1"` only) remains source-proven; default OFF.

Unstripped text symbols found (7/17): `consumeGateAComposite`,
`gateAEnsureReady`, `gateAPairOverlapsBuffer`,
`gateAQueueSemanticallyQuiescent`, `gateAReadyStill`, `gateARetireBuffer`,
`gateAWaitTerminal`.

Missing from symbol table (informational): static/single-call-site or
header-inline helpers including `gateADirectTryPrepare`,
`gateALookupDirect`, `gateACloseGeneration`,
`lorieGateAPublishDirectMeta`, `lorieGateAConsumeDirectMeta`. Inlining
at -O2 is not failure. Authority is exact source `15caa009` → CI head
binding → all-ABI compile → ELF/APK literals.

Source review on the same HEAD: B1 consume/`readIndex` in the direct
branch; B2 identity from `LORIE_GATEA_DIRECT_PUBLISHED` with lookup-miss
FATAL and no `findBufferWithRetry`/`LorieBuffer_bindTexture` on that
path; B3 every reserve uses `gateAQueueSemanticallyQuiescent()` and
`!gateAUsed` is write-only residue; B4 UNREGISTER↔ACK and
GENERATION_CLOSE↔CLOSED with texture→EGLImage→AHB destroy; fatal is
`_exit(127)`. Frozen asserts still compile: queue 168 B, P0 sideband
40 B, direct meta 48 B.

## VERDICT

```text
P2 B1-B4 CI: PASS
ARTIFACT: QUALIFIED (identity/integrity/signer/BuildID; provenance only)
PROVENANCE: PASS
RUNTIME: NOT RUN (forbidden this round; no ADB/device/install)
Stable: UNTOUCHED
HDMI: UNTOUCHED
Production Gate A: BLOCKED
```

This qualifies only that exact source `15caa009` reproducibly built a
trusted Experimental artifact. It does not prove B1–B4 runtime
correctness.

Full machine report: `apk-elf-verification/p2-b1b4-apk-elf-report.json`.
Verifier: `verify-p2-b1b4-apk.py`.
