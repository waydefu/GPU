# GATE A P2 R8 HOST TOOLING V2 PUBLISHED — 2026-09-18

```
STATUS: R8_HOST_TOOLING_V2_PUBLISHED
        PRODUCT b984ded / CI 35347497216 UNCHANGED
        VALIDATE_ONLY device mutation = 0
        attempt-08 NOT reclassified
```

Product/artifact authority remains `b984dedcac731b77ca4cf8899f8a78b7848ad083`
CI **35347497216**, experimental `1.03.01-b984ded-18.09.26`.
No APK rebuild. No reinstall.

Tooling commit (host only, not the installed APK):
`2a14ab2f7a5d81e7cd72d5308f5865b81b22881f`

Frozen historical live runner (unchanged):
`p2-r8-runtime/run-r8-one-cell-b984ded.sh`
SHA256 `f22546b7f42aa9f45c4bdee5e7ce675efe6b1fae4e9709e15696e59262dab7b0`
still binds `tests/r8/judge-r8.py`.

New live runner:
`p2-r8-runtime/run-r8-one-cell-b984ded-v2.sh`
SHA256 `53e0c6b8ac613eab7dcce970438e7adc071bddcde4d7e1e202763bfe62de44e5`
binds `tests/r8/judge-r8-v2.py` and amended `r8_orchestration_v2.py`.
`EXPECT_HEAD` remains `b984dedcac731b77ca4cf8899f8a78b7848ad083`.

Manifest:
`p2-r8-runtime/runtime-b984ded/r8-runtime-tooling-manifest-v2.json`
(`source_sha` = product `b984ded`, not the tooling commit).
Historical `r8-runtime-tooling-manifest.json` is not overwritten.

| Item | SHA256 / SHA |
| --- | --- |
| tooling commit | `2a14ab2f7a5d81e7cd72d5308f5865b81b22881f` |
| product SHA | `b984dedcac731b77ca4cf8899f8a78b7848ad083` |
| live runner v2 | `53e0c6b8ac613eab7dcce970438e7adc071bddcde4d7e1e202763bfe62de44e5` |
| historical live runner | `f22546b7f42aa9f45c4bdee5e7ce675efe6b1fae4e9709e15696e59262dab7b0` |
| r8_orchestration_v2.py | `27af4a6253bcc021f3da2494b99045c754fb27f2b815b23cbbe1e0744760a536` |
| judge-r8-v2.py | `baceae096fda8ffdb373267bc9c1e80c3e3e2985df278de3295a1bd8b73380a2` |
| judge-r8.py (frozen) | `f021048da3c1b729c6f9bf560eba52609b2f980336dd4fab77ad1700438c0e31` |
| collect-r8.py | `e6df519a75c872c8a56fac00146585853eec7f17a3f424e70e5d4736340666c8` |
| lifecycle-cell-spec.json | `ff22a1521d23a8954b0b4f3a603dbb19af98b3e8b3727342caf5e107b639b3ba` |
| fixture ELF `/tmp/p_r8_lifecycle` | `ad93f2ba6adcaae53dbb750b9bdc928d32b1932c3e86ea1b4d2121a5c96f12de` |
| CI | **35347497216** |

Attempt-08 cell `runtime-b984ded/r8-c1/attempt-08-xcb-sender/` remains
`R8_INVALID JUDGE_NOT_PERMITTED / MULTI_BEGIN_x`. Replay is non-authority.

Do **not** start C1 attempt-09 without a new explicit grant.
Do **not** start C2 or R9.
