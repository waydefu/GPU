# Gate A P2 R7 Artifact B handoff — 2026-09-16 `a7528bd` INSTALLED; B-2 R1 FAIL; R7 **BLOCKED**

```
STATUS: R6 PASS on frozen 0f1e546 remains historical
        Artifact B COMMITTED+CI+INSTALLED a7528bd
        B-2 R1 unset FAIL (stress 999/1000) AUTHORITATIVE
        diagnostic-01 DID NOT REPRODUCE
        diagnostic-02 RCA IDENTIFIED (997/1000, timeout→Done→stale GetImage)
        EXA Composite timeout repair READY (local dirty, no device)
        R7 cells NOT STARTED
        R8–R10 NOT AUTHORIZED
DEVICE HEAD: a7528bd25b89d0408bc15002e10bccefaeef3028
R7 CI (installed): 35007764673
APK INSTALLED experimental only: 1.03.01-a7528bd-15.09.26
APK SHA256: c29b1c68df613d40d8bfd93b44887ffd389419d8ca5f36661d1a48b3f03f4c2c
Build ID: aa1d23e7fc88048f40c450ca5bacf0506cb93b9c
R7 WORKTREE: src/f8-ahb-gatea-r7
R7 BRANCH: qualification/gatea-r7-20260916
R7 HEAD: a7528bd25b89d0408bc15002e10bccefaeef3028
R6 WORKTREE: src/f8-ahb-gatea-r6-retire HEAD 0f1e546 (UNCHANGED)
Stable :1: PID 17922 UNTOUCHED
HDMI: UNTOUCHED
Production Gate A: BLOCKED
```

R6 runtime brief remains:
`evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260916.md`.
Do not rewrite it. Do not silent-retry its cells.

B-0 freeze:
`GATE-A-P2-R7-R10-SUPPORT-DESIGN-20260916.md`.

## Summary

1. Artifact B is implemented on a new lineage from frozen R6 `0f1e546`.
2. Host + fork CI **35007764673** PASS; experimental install PASS
   (`1.03.01-a7528bd-15.09.26`, SHA256 `c29b1c68…4c2c`, Build ID `aa1d23e7…3b9c`).
4. Device experimental is `a7528bd`. Frozen R6 worktree is unchanged.
5. Renderer does not getenv `TERMUX_X11_GATEA_TEST_FAULT`. Event 32 stays unused.
6. B-2 R1 unset first attempt **FAIL**: oracle 1514/1514; stress 1000 `fail=1`.
   Event 35=0. SUMMARY on close with all counters 0. Root cause NOT PROVEN.
   Cell `runtime-a7528bd/r1-unset-oracle/` remains authoritative.
7. Authorized diagnostic-01 on X PID **29184**: `ok=1000 fail=0`; no
   `B2_DIAG_FAIL`; EXA timeout count 0; Gcomp Done 1000. Verdict:
   **DIAGNOSTIC REPRODUCTION DID NOT REPRODUCE**. Not a B-2 PASS.
   Cell `runtime-a7528bd/r1-unset-diagnostic-01/`.
8. Authorized diagnostic-02 on X PID **10903**: `ok=997 fail=3`; 3×
   `B2_DIAG_FAIL PIXEL_RGB_MISMATCH` (`got==dst`); 3× EXA wait-timeout
   then same-ms `Gcomp Done`. Verdict: **RCA IDENTIFIED**.
   Cell `runtime-a7528bd/r1-unset-diagnostic-02/`. Not a B-2 PASS. Not R7.
9. EXA Composite timeout repair on `src/f8-ahb-gatea-exa-timeout`
   branch `fix/gatea-exa-composite-timeout-20260916`: wait-false now
   `gateAXFatal("x-exa-composite-wait", LORIE_GATEA_FAIL_TIMEOUT)`.
   Host verifier RED on `a7528bd`, GREEN on the repair. Uncommitted.
   Device run **not authorized**. Frozen R6 untouched. Installed APK
   remains `a7528bd`.

## Next

Do **not** start R7 cells. Do **not** silent-retry `runtime-a7528bd/r1-unset-oracle`.
Do **not** overwrite `r1-unset-diagnostic-01/` or `r1-unset-diagnostic-02/`.
Do **not** start R8. B-2 remains BLOCKED; R7 = NOT STARTED.
B-2 requalification of the EXA timeout repair requires **new explicit
authorization** (build/install APK). Do not mutate frozen R6.
