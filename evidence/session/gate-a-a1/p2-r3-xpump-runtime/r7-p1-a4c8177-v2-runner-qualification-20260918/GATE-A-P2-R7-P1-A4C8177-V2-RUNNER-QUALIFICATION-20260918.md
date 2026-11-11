# Gate A P2 R7-P1 a4c8177-v2 runner QUALIFIED — 2026-09-18

```
R7_P1_A4C8177_V2_RUNNER_QUALIFIED
product source: a4c8177f4b059fddd111717255e9d23cf0e15e1e UNCHANGED
APK rebuild: NO
install: NO
judge SHA: fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17 UNCHANGED
timeout_ms: 2000 UNCHANGED
```

## Tooling

| Item | SHA256 | size |
|---|---|---|
| `run-r7-p1-a4c8177-v2.sh` | `63e3d8a2d50398e243c96185e676d349acf0338b538e0938fc156395d85ed20c` | 28570 |
Classifier SHA after target-serial scope repair: `d287d361cd54753870639c548e544934ab121c30ed42ac663aacc4d2e52dbd14`.
Host classifier tests 20/20. Live validity-02 rescored `EXPECTED_PRESENT_TIMEOUT` without a second device run.


Frozen v1 runner `run-r7-p1-a4c8177.sh` SHA256 `4cbb1394…1b47` unmodified.
Frozen cell `runtime-a4c8177/r7-p1/` classify SHA256 `246832f2…84f6` unmodified.

Fresh live path: `runtime-a4c8177/r7-p1-validity-02/` (absent at qualification).
CELL_ID=`r7-p1-validity-02`. CELL_ID=`r7-p1` refused.

## Oracle v2

Phase-scoped liveness: before_fault / after_event35 / during_wait / near_terminal / post_terminal.
Device authority: `adb shell test -d /proc/$ACT_PID` + `ps`.
Host `/proc/$ACT_PID` is not death/life authority.
Post-terminal Activity ABSENT after `x-present-copy-wait/4` is observational, not `PEER_DIED`.
`GATEA_HUP_PRESERVE` after that terminal is observational.

## Host tests

`scripts/test_r7_p1_a4c8177_v2_runner.sh` **pass=45 fail=0**
Classifier unit **18/18** including:
- during-wait ALIVE + timeout/4 + post-terminal ABSENT → `EXPECTED_PRESENT_TIMEOUT`
- during-wait DEAD + timeout/4 later → `PEER_DIED`
- during-wait ALIVE + x-hup/6 → `WRONG_TERMINAL` product_fail
Judge regression **16/16**. C class + wait-wake + present-target-arm static PASS.

Static: `scripts/verify_r7_p1_a4c8177_v2_tooling.py` PASS.
