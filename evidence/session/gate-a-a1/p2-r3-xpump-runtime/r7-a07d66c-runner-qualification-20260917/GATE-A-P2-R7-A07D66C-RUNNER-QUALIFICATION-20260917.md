# Gate A P2 R7 — a07d66c reusable one-cell runner tooling qualification — 2026-09-17

```
PRIMARY_VERDICT: R7_A07D66C_RUNNER_QUALIFIED
CANDIDATE: a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82 INSTALLED
R7-05 on a07d66c: PASS / FROZEN (not rerun)
R7-01: NOT RUN
R7 overall: IN PROGRESS
Production Gate A: BLOCKED
Device execution this task: NONE
```

This packet is **tooling only**. It removes the previous R7-01 runner-authority blocker.
It does **not** execute R7-01.

## Runner authority

Path: `evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-a07d66c.sh`
SHA256: `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded`
Size: 20529 bytes
EXPECT_VERSION: `1.03.01-a07d66c-17.09.26`
EXPECT_VERSION_CODE: 15
ROOT: last component must be `runtime-a07d66c` (refuse `runtime-fdfb1ce` / `runtime-7549e36`)
WAIT_S: frozen 12
Judge: frozen `p2-r7-design/judge-r7.py` SHA256 `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17`

VersionName/versionCode/lastUpdateTime are live package checks only. APK SHA256 / signer / Build ID remain the outer qualification profile.

## Next grant (do not execute here)

```
SERIAL=<live>
ROOT=.../runtime-a07d66c
CELL_ID=r7-01
FAULT=src-ready-miss
FIXTURE=direct
WAIT_S=12
bash run-r7-one-cell-a07d66c.sh
```

One attempt. No VALIDATE_ONLY. Destination `runtime-a07d66c/r7-01/` must still be absent at start.
