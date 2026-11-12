# Gate A P2 R7 — 2026-09-17 R7-10 RCA **PROVEN**; repair **ARTIFACT QUALIFIED**; historical FAIL frozen; **NOT INSTALLED**

```
STATUS: a07d66c INSTALLED (historical R7-10 FAIL frozen)
        R7-10 RCA PROVEN
        repair 8545b26 HOST/STATIC/ABI/CI/ARTIFACT QUALIFIED
        repair APK NOT INSTALLED
        R7-05 PASS frozen
        R7-01 PASS frozen
        R7-02 PASS frozen
        R7-03 PASS frozen
        R7-06 PASS frozen
        R7-07 PASS frozen
        R7-08 PASS frozen
        R7-09 PASS frozen
        R7-11 PASS frozen
        R7 IN PROGRESS / still 10/13
        next is separate device install+R7-10 requal grant on 8545b26
        do not retry runtime-a07d66c/r7-10
        do not start R7-P1 / R7-P2
        do not install without a new grant
Stable :1: PID 20146 UNTOUCHED
Production Gate A: BLOCKED
```

RCA + repair:
`evidence/session/gate-a-a1/p2-r7-design/GATE-A-P2-R7-10-RCA-REPAIR-20260917.md`

Artifact:
`evidence/session/gate-a-a1/p2-r7-10-hup-ci-35225593518/P2-R7-10-HUP-CONTAINMENT-CI-ARTIFACT-PROVENANCE-20260917.md`

Historical FAIL cell (do not overwrite):
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-a07d66c/r7-10/`

Repair worktree: `src/f8-ahb-gatea-r7-10-hup`
Branch: `fix/gatea-r7-10-hup-containment-20260917`
HEAD: `8545b26b308aa60b05685f48560285350e22ee8d`
CI: **35225593518**
APK: `1.03.01-8545b26-17.09.26` SHA256 `92220845…377a` Build ID `50a4078b…7b0a`

## Summary

R7-10 construction was valid. X classified peer death as timeout reason=4
because `gateAWaitTerminal` returned FATAL on `!lorieConnectionAlive()` and
Done mapped publishedFatal==0 to `x-direct-not-success/4`. cmdentrypoint
`x-hup` never ran (dix-main blocked in the wait; no `InputThreadPreInit`).
2000 ms did **not** expire (24 ms halt). Repair observes existing `conn_fd`
HUP in the wait and fail-stops `x-hup/6` while preserving published fatals
and genuine live-peer timeout.

## Next

**Separate** grant: install `8545b26` on experimental only, then **one**
R7-10 `renderer-exit-after-consume` cell. Do **not** retry
`runtime-a07d66c/r7-10`. Do **not** start R7-P1 or R7-P2. Do **not** retry
R7-11 / R7-09 / R7-08 / R7-07 / R7-06 / R7-03 / R7-02 / R7-01 / R7-05 /
R7-04 / B-2. Do **not** install automatically. Production Gate A remains BLOCKED.
