# Gate A P2 CASE_LOOP repair-validation — 2026-09-16 `7549e36` **CASE_LOOP_REPAIR_VALIDATED**

One authorized device repair-validation cell. **Not B-2.** **Not R7.** Timeout stayed **2000 ms**. No retry.

This cell answers only:

> Does hardened `7549e36` prevent the previously observed CASE_LOOP renderer-consume stall under one bounded device validation workload, while preserving exact Composite behavior and the existing 2000 ms EXA fail-stop invariant?

Prompt and contract were **consistent**: the design file is not itself an install grant; this execution used the separate explicit install grant in the 2026-09-16 repair-validation authorization.

| Field | Value |
|---|---|
| HEAD / APK | `7549e3667ec03b8b5e50d2e5befe03065840bbd9` / `1.03.01-7549e36-16.09.26` CI **35084701124** |
| SHA256 / Build ID | `45500894…4bc3` / `4c5b7b86…8f81` MATCH install cell `runtime-7549e36/r0/` |
| lastUpdateTime | 2026-09-16 19:03:48 (unchanged by this observation) |
| serial | `10.191.48.13:36483` live-fetched |
| Screen | Awake, `isKeyguardShowing=false` |
| X3 | PID **19887** cmdline `termux-x11gpu com.waydefu.x11gpu :3` mode=unset `NO_GATEA_ENV` |
| Activity | pid **29087** `com.waydefu.x11gpu` displayId=0 |
| Renderer | GLES tid **20323** (`gles-renderer` on X 19887) |
| Stress | `p_b2_stress` SHA256 `3e79b5cf…3c56` `1000` **ok=1000 fail=0 n=1000 alive=1** RC=0 **role=repair-validation, NOT B-2** |
| executions | **1** |
| Window | 2026-09-16T19:04:07 → 19:04:43 +08 |
| Gcomp Prepare TRUE / RECT / Done | **1000 / 1000 / 1000** |
| apply | **1002** follow = unfiltered (`gles-renderer`) |
| RECT→Done | n=1000 max **22 ms** gt2000=0 |
| RECT→apply (proxy; apply has no serial) | n=999 max **181 ms** gt2000=0 |
| EXA wait timeout | **0** |
| Fatal | **0** (`x-exa-composite-wait` absent; teardown `GATEA_SUMMARY where=x-close-screen` fatalReason=0) |
| timeout→Done | **0** |
| pixel_mismatch | **0** (`PIXEL_RGB_MISMATCH=0` `PIXEL_XBYTE_MISMATCH=0` `B2_DIAG_FAIL=0`) |
| STALL_PHASE / NOTIFY_* | **absent as expected** (production `0d72332` lineage, not `feeaa56`) |
| HDMI | observe-only; activity `display=0` |
| Stable | PID **14604** `1.03.01-11b82d9-06.09.26` lastUpdateTime **2026-09-07 22:55:03** UNTOUCHED |
| Teardown | killed experimental X 19887 after workload; **NO_X3_RESIDUE**; Stable PID unchanged |
| APK left installed | **yes** (`7549e36`; contract did not require restoration) |

Classifier: `repair-validation-01/repair-validation-classify.txt` `verdict=CASE_LOOP_REPAIR_VALIDATED`.

## Historical comparison (frozen; not retried)

`runtime-feeaa56/stall-obs-01` CASE_LOOP: X 23034; serial 86 published; renderer silent ~2002 ms; `x-exa-composite-wait` reason=4; stress `ok=81 fail=919 alive=0`.

This cell used the **same harness family** (`p_b2_stress 1000`, SHA256 `3e79b5cf…`) on `7549e36` and did **not** reproduce that stall.

## Consume limitation

`7549e36` has no per-serial `STALL_PHASE` / `NOTIFY_*` markers. Strongest defensible metrics:

- identity-bound Composite completion: every observed `Gcomp RECT` has a later `Gcomp Done` (1000/1000), max 22 ms
- wall-clock RECT→next `rendererApplyPendingGpuCopies` proxy (no serial on apply): 999 paired samples, max 181 ms
- 8 ms is the idle recheck interval, **not** an end-to-end SLA; 181 ms is not a CASE_LOOP failure

## Verdict

```
CASE_LOOP_REPAIR_VALIDATED
7549e36 passed the dedicated CASE_LOOP repair-validation cell; this is NOT B-2 PASS.
historical CASE_LOOP remain DEVICE-PROVEN on feeaa56 stall-obs-01
mechanism remains SOURCE-SUPPORTED
RCA-1 timeout→Done still ABSENT (repair held)
B-2 remains BLOCKED (0d72332 serial 2370 + rerun1 serial 1810; not requalified)
R7 NOT STARTED
timeout 2000 UNCHANGED
Production Gate A BLOCKED
```

Do **not** retry this cell (`stall-stress1000.out` exists).
Do **not** start B-2 from this packet.
Do **not** merge waydefu/GPU PR #4 as qualification.

Install evidence: `runtime-7549e36/r0/INSTALL-7549e36-20260916.md`.
Frozen historical cells unchanged.
