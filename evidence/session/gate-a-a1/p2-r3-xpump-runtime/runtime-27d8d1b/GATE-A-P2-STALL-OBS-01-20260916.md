# Gate A P2 stall observation-01 — 2026-09-16 `27d8d1b` **STALL_NOT_OBSERVED**

One authorized device observation. **Not B-2.** **Not R7.** Timeout stayed **2000 ms**. No retry.

| Field | Value |
|---|---|
| HEAD / APK | `27d8d1b4fcfc5456bac8720d36110eeeb7cbc9d3` / `1.03.01-27d8d1b-16.09.26` CI **35056388284** |
| SHA256 / Build ID | `142b6e1f…45b0` / `e8d859dd…5e2c` MATCH install cell `runtime-27d8d1b/r0/` |
| serial | `10.191.48.13:43399` live-fetched |
| X3 | PID **16420** cmdline `termux-x11gpu com.waydefu.x11gpu :3` mode=unset `NO_GATEA_ENV` |
| Renderer | LorieNative pid **20203** tid **16188** (`STALL_PHASE`) |
| Stress | `p_b2_stress` SHA256 `3e79b5cf…3c56` `1000` **ok=1000 fail=0 alive=1** RC=0 (trigger only) |
| Window | 2026-09-16T13:14:45 → 13:15:07 +08 |
| Gcomp Done | **1000** (13:14:45.750 … 13:15:07.342) |
| EXA wait timeout | **0** |
| Fatal / `x-exa-composite-wait` | **NONE** |
| `STALL_PHASE` | **3712** = 928× {SWAP_ENTER, SWAP_EXIT, NEXT_FENCE_ENTER, NEXT_FENCE_EXIT} |
| SWAP max | **1.468 ms** (EGL_TRUE ×928; 0 × >10 ms) |
| NEXT_FENCE max | **4.806 ms** (EGL_CONDITION_SATISFIED 12534 ×928; 0 × >10 ms) |
| Loop gap max | **1103 ms** (cs 4→5, before first Gcomp; 0 × ≥2000 ms) |
| Queue lag at markers | completedSerial==readIndex==writeIndex, max lag **0**, max serial **1004** |
| HDMI | observe-only; `mDisplayId=0` |
| Stable | PID **17922** `1.03.01-11b82d9-06.09.26` lastUpdateTime **2026-09-07 22:55:03** UNTOUCHED |
| Teardown | killed 16420; **NO_X3_RESIDUE**; live re-scan same |

Classifier: `stall-obs-01/stall-phase-classify.txt` `verdict=STALL_NOT_OBSERVED`.
Durations: `stall-obs-01/stall-phase-durations.txt`.

## Verdict

```
STALL_NOT_OBSERVED
CASE_A / CASE_B / CASE_C NOT CLASSIFIED
not a B-2 PASS
B-2 remains BLOCKED (0d72332 serial 2370 + rerun1 serial 1810)
R7 NOT STARTED
timeout 2000 UNCHANGED
```

This cell **DID NOT REPRODUCE** the >2 s consume-delay stall. Markers **did fire** and both wrapped EGL calls stayed fast. That does **not** falsify the earlier `0d72332` fail-stop cells. Do **not** retry this cell (`stall-stress1000.out` exists). Do **not** start B-2 matrix or R7.

Install evidence: `runtime-27d8d1b/r0/INSTALL-27d8d1b-20260916.md`.
Frozen `runtime-0d72332/` and `runtime-a7528bd/` unchanged.
