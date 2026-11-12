# Gate A P2 R7-P2 a4c8177-v2 runner QUALIFIED — 2026-09-18

```
R7_P2_A4C8177_V2_RUNNER_QUALIFIED
product source: a4c8177f4b059fddd111717255e9d23cf0e15e1e UNCHANGED
APK rebuild: NO
install: NO
device: NOT RUN at this packet
judge SHA: fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17 UNCHANGED
```

## Tooling

| Item | SHA256 | size |
|---|---|---|
| `run-r7-p2-a4c8177-v2.sh` | `3fca2553ac2835aabb0bff36ae570faba305d743d22db874d393acef9d2db622` | 27681 |
| `classify_r7_p2_a4c8177_v2.py` | `3c6bb8a2fd235484792a1ab5bc46792cdff3951ff14b7ba09adc2408f746d43c` | — |

Classifier later target-serial-scoped (unrelated serial-6 event17 is not TARGET_COMPLETED). Host tests 12/12.
Device later **R7_P2_A4C8177_QUALIFICATION_PASS** (X 12663); this packet remains the tooling QUALIFIED record.

Frozen v1 `run-r7-p2-a4c8177.sh` SHA256 `6b0a9bdb…d55e` unmodified.
Fresh live path: `runtime-a4c8177/r7-p2/` (absent at qualification).

## Oracle v2

Pre-fault Activity/renderer liveness required.
Post-fault Activity ABSENT is expected after enum13 renderer exit; not INVALID.
`DEAD_BEFORE_FAULT` if renderer/Activity missing before target event35.

## Host tests

`scripts/test_r7_p2_a4c8177_v2_runner.sh` **pass=36 fail=0**
Classifier unit **10/10** including post-fault ABSENT PASS and renderer missing before event35 INVALID.
Judge **16/16**. C class + wait-wake + present-target-arm static PASS.
