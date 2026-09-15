# B3a U4-C2 exact-sequence execution — 2026-09-11

## Gate

Artifact `10160961032` provenance and matching unstripped Build ID are PASS;
see `B3A-U4-C2-ARTIFACT-PROVENANCE-20260911.md`.

Target is only `com.waydefu.x11gpu` / `DISPLAY=:3`, pinned ADB
`10.56.180.219:39035`. Stable `com.termux.x11` / `:1` is out of scope and
untouched.

## Exact contract

Three complete sequences, each:

```text
CPU-A → R3-A → CPU-B → R3-B
```

Every candidate session uses:

```text
64×64
warmup=100
count=500
mode=1
reuse=1
batch=16
cold=0
expected telemetry records=1519 + (100 + 500) × 16 = 11119
expected cell output=00ff0000
```

Each session must independently pass:

- Activity explicit `displayId=0`, `state=RESUMED`, `reportedDrawn=true`;
- actual `termux-x11gpu com.waydefu.x11gpu :3` PID discovery;
- holder and X readiness;
- oracle `1514/1514`, `fail=0`, `maxΔ=0`;
- cell exact driver check, no `MISMATCH`;
- telemetry `11119/11119`, `dropped=0`;
- CPU fallback=1 or R3 fallback=0 as applicable;
- teardown telemetry artifact and `NO_X3_RESIDUE`.

`gpu_exec_ns`, queue, and renderer external resource endpoints remain
`NOT OBSERVABLE` unless the candidate emits a valid value. Null is not zero.

## Stop rule

Any SIGSEGV/SIGILL/SIGABRT, missing server, invalid display target, oracle/cell
mismatch, telemetry drop/count mismatch, or teardown residue stops the full
sequence immediately. On a fresh SIGSEGV, retain the exact matching unstripped
library and enter crash forensic/symbolization; do not expand the benchmark.

## Session slots

- [x] sequence 1: `c2-s1-cpu-a`, `c2-s1-r3-a`, `c2-s1-cpu-b`, `c2-s1-r3-b`
- [x] sequence 2: `c2-s2-cpu-a`, `c2-s2-r3-a`, `c2-s2-cpu-b`, `c2-s2-r3-b`
- [ ] sequence 3: `c2-s3-cpu-a`, `c2-s3-r3-a`, `c2-s3-cpu-b`, `c2-s3-r3-b`

Raw output directory: `t2-u4-c2-exact-sequence/`.
