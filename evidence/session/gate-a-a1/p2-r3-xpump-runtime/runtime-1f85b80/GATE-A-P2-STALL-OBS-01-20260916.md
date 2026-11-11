# Gate A P2 stall observation-01 — 2026-09-16 `1f85b80` **STALL_NOT_OBSERVED**

One authorized device observation. **Not B-2.** **Not R7.** Timeout stayed **2000 ms**. No retry.

| Field | Value |
|---|---|
| HEAD / APK | `1f85b803847e8522647c2bb7a4aba821428a606b` / `1.03.01-1f85b80-16.09.26` CI **35063553801** |
| SHA256 / Build ID | `bbe88f1b…9316` / `d0d9d924…f79a` MATCH install cell `runtime-1f85b80/r0/` |
| serial | `10.191.48.13:45645` live-fetched |
| X3 | PID **28893** cmdline `termux-x11gpu com.waydefu.x11gpu :3` mode=unset `NO_GATEA_ENV` |
| Renderer | LorieNative pid **19884** tid **28385** (`STALL_PHASE`) |
| Stress | `p_b2_stress` SHA256 `3e79b5cf…3c56` `1000` **ok=1000 fail=0 alive=1** RC=0 (trigger only) |
| Window | 2026-09-16T16:39:33 → 16:40:22 +08 |
| Gcomp Done | **999** in logcat (fixture ok=1000; one Done line **NOT OBSERVED** in logcat) |
| EXA wait timeout | **0** |
| Fatal / `x-exa-composite-wait` | **NONE** |
| `STALL_PHASE` | **3982** follow: SWAP 995/995, NEXT_FENCE 996/996 |
| NOTIFY_ENTER / EXIT | **0 / 0** follow **and** unfiltered — **NOT OBSERVED** |
| NOTIFY max | **NOT OBSERVED** (no pair) |
| SWAP max | **9.183 ms** (EGL_TRUE; gt2000ms=0) |
| NEXT_FENCE max | **2.102 ms** (EGL_CONDITION_SATISFIED 12534; gt2000ms=0) |
| fromDequeueTime | **NOT OBSERVED** |
| BufferQueue / SurfaceFlinger | 4 / 1 lines; activity disconnect at start, not a ≥2 s stall |
| HDMI | observe-only; `mDisplayId=0` |
| Stable | PID **14604** `1.03.01-11b82d9-06.09.26` lastUpdateTime **2026-09-07 22:55:03** UNTOUCHED |
| Teardown | killed 28893; **NO_X3_RESIDUE**; Stable PID unchanged |

Classifier: `stall-obs-01/stall-phase-classify.txt` `verdict=STALL_NOT_OBSERVED`.
Durations: `stall-obs-01/stall-phase-durations.txt`.

`NOTIFY_*` wrap only the `redrawLocked` pre-SWAP `notifyGpuCopyDone()` sites.
Unfiltered dump has **1002** `rendererApplyPendingGpuCopies` (`gles-renderer` Debug).
Those applies can complete on the standalone path, which this diagnostic **did not wrap**.
Do **not** infer a NOTIFY duration. Do **not** classify CASE_NOTIFY.

## Verdict

```
STALL_NOT_OBSERVED
CASE_NOTIFY / CASE_SWAP / CASE_NEXT_FENCE / CASE_LOOP NOT CLASSIFIED
not a B-2 PASS
B-2 remains BLOCKED (0d72332 serial 2370 + rerun1 serial 1810)
R7 NOT STARTED
timeout 2000 UNCHANGED
RCA impact: UNCHANGED
```

This cell **DID NOT REPRODUCE** a >2 s EXA Composite stall. SWAP and NEXT_FENCE
stayed well under 2 s. That does **not** falsify the earlier `0d72332` fail-stop
cells. Do **not** retry this cell (`stall-stress1000.out` exists). Do **not**
start B-2 matrix or R7.

Install evidence: `runtime-1f85b80/r0/INSTALL-1f85b80-20260916.md`.
Frozen `runtime-27d8d1b/` / `runtime-0d72332/` / `runtime-a7528bd/` unchanged.
