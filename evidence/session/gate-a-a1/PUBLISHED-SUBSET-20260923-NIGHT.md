# Published subset — 2026-09-23 night batch

Local evidence is complete; this repository carries the verdict basis only. Every run directory keeps its
full local `sha256sums.txt`; files listed there but absent here were deliberately not published:

```
raw-logcat.txt          full device logcat (0.2-1.3 GB for TELEMETRY=1 runs); verdicts are reproducible from it locally
x3-launcher.log         X3 stdout/stderr; not read by any judge
*.apk, *.so             artifact binaries (sha256 / build-id / signer recorded in artifact-binding.json and install/)
x_rtt.bin, fixtures     built binaries; their sources are in the fork
```

Batch contents: INCIDENT-20260923 (two lmkd incidents) · RCA-XFCE-3 + OPLAT (PGA-GAP-2) · PGA-GAP-3 RCA /
design / touched semantics / artifact 83d45a9 / requal-01 and -02 (both GAP3_REQUAL_FAIL: memory leak fixed,
mapping residue open) · oracle-01 (V1 FAIL_CORRECTNESS, construction) / -02 (V2 INVALID) / -03 (V3 ORACLE_PASS)
· B.3 G / C / G2 / ATTR-01 / ATTR-02 / S-01 (BLOCKED) / S-02 (partial, incident) + b3-analysis.json
(UNJUDGED_NOISE) · runners with mem-guard and safe-run.
Fork tooling: waydefu/termux-x11 feat/gatea-r8-lifecycle-support-20260918 up to a462b40.
