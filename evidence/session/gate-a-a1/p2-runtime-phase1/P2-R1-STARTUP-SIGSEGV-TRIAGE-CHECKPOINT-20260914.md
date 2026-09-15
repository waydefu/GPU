# P2 R1 Startup SIGSEGV Triage — checkpoint 2026-09-14 (T1 diagnostic QUALIFIED)

T0 done. T1 diagnostic artifact QUALIFIED. T2 matrix NOT RUN (device
runtime requires screen ON / unlocked; not executed this offline close).

Historical Phase 1 on `15caa00` remains frozen:

```text
R0 PASS
R1 unset PASS
R1 PROTO=0 FAIL NEW SIGSEGV PID 31807
R2 NOT RUN
R3+ NOT RUN
```

## SOURCE DIFFERENTIAL (T0) — done, static only

`lorieGateAProtoEnabled()` is exact `"1"`. Unset and `"0"` are equivalent.
Presence-sensitive Gate A path: NO. Do not treat getenv presence as root cause.

## CRASH HANDLER (T1) — QUALIFIED

Commit `dd81ac056bd3fe84d757c63c5ee484a2037ebb4f` adds AS-safe `Upid` + `Uraw`
(512-byte little-endian qword dump) after the existing `Uctx` line.

CI 34781139248 PASS. APK SHA256
`cc0058d8b90d2bdc6829051b1e8c398da171611ab1712a207e2d4f508f2ad459`.
Build ID `0892201de126af9e9b5a06d44ea1c0fbd5cd33a4` MATCH.

**This diagnostic artifact is the only T2-authorized APK.**
Do not install `15caa00` / `d69aff2c…0e8d` / `33a3b67f…` for new cells.

PID 31807 `PC=0x48000ec4` on the old artifact is still not a proven
faulting instruction. Original PC capture valid: NOT PROVEN until a
T2 crash yields Uraw-derived PC on Build ID `0892201d…`.

## STARTUP MATRIX (T2)

NOT RUN. Required cells after screen-on device admission:

```text
A1 unset
B1 PROTO=0
A2 unset
B2 PROTO=0
A3 unset
B3 PROTO=0
```

Each cell: fresh Experimental process, `:3`, display 0, same startup
checkpoint, clean teardown, NO_X3_RESIDUE. Then remaining R1 oracle/stress
and R2–R10 per the full closure goal.

## STOP STATE

```
REPRODUCIBILITY: NOT ESTABLISHED
ROOT CAUSE: NOT PROVEN
CLASSIFICATION: OBSERVED / ROOT CAUSE NOT YET PROVEN
SOURCE FIX: diagnostic capture only (dd81ac0)
BUILD: PASS (incremental + full-clean, 0 new warnings)
CI: 34781139248 PASS
ARTIFACT: QUALIFIED dd81ac0 / cc0058d8… / 0892201d…
STABLE: UNTOUCHED
HDMI: UNTOUCHED
NEXT: READY FOR DEVICE RUNTIME (screen ON, unlocked, display 0)
```
