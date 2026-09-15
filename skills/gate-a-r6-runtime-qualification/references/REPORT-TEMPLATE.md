# R6 final report template

Write the user-facing verdict in Traditional Chinese. Use this structure.

```text
最終裁決
R6 PASS | R6 BLOCKED | R6 NOT YET VERIFIED
blocking reason immediately

Exact Authority
worktree / branch / HEAD / candidate SHA / APK SHA256 / Build ID / runtime package

Pre-Edit Review
inspected / ownership / ACK sites / scrap-destroy / timeout-loss / CloseScreen /
judge / xserver.patch

Changes
exact files / semantic change / why necessary

Host Verification
tests / judge adversarial / patch / PASS or FAIL

CI / Artifact
workflow / exact-head / identity

Runtime
D1 / D2-INFLIGHT / D2-OOM
each: artifact, first attempt, branch, telemetry, pixels, PASS/FAIL/BLOCKED

Fail-Stop / Teardown Matrix
timeout / renderer loss / scrap / destroy / CloseScreen
DEVICE-PROVEN | HOST-PROVEN | SOURCE-PROVEN | NOT VERIFIED

Stable Safety
explicitly whether com.termux.x11 / :1 was touched

Findings
P0 / P1 / P2 / P3
each: file/symbol, invariant, failure mode, evidence, minimal correction,
acceptance test

Remaining Unknowns

Next Authorized Action
R6-only. If R6 PASS: STOP BEFORE R7 — authorization required.
```
