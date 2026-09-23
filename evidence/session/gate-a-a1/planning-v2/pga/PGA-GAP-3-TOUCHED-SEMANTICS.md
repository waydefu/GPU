# PGA-GAP-3 touched semantics — 83d45a9 vs bfb5769 (carry-forward review, plan §13.4)

Product diff: `lorie/src/main/cpp/lorie/InitOutput.c` +7, inside `lorieExaDoneComposite`, non-direct branch, after
`lorieGpuCopyWaitForCompositeOrFatal`:
`if (upload && upload != d0aStagingCache) lorieUnregisterBuffer(upload);`

## What the line can reach

```
runs only    EXA composite transactions that took the D0a staging path (not Gate A direct) AND scheduled >= 1
             GPU entry (exaGpuComp.scheduled); upload = the per-transaction FD clone
sends        one EVENT_REMOVE_BUFFER for that clone id over conn_fd (existing event, existing renderer
             handler Renderer::removeBuffer, already used by pixmap destruction)
X side       removes the id from registeredBuffers; memory release is the pre-existing LorieBuffer_release
never        Gate A direct (returns earlier: exaGpuComp.direct), Gate A REGISTER/UNREGISTER frames, leases,
             generations, fences, the gpuCopyQueue, the D0a cache buffer, solid/copy/present paths
```

## Gate-by-gate

| Gate / cell family | Touches? | Decision |
|---|---|---|
| R0–R2 (setup, telemetry, bind) | no | CARRY_FORWARD |
| R3–R6 (direct path, oracle, stress, retirement) | direct path untouched; staging fallback in stress cells now also removes its clone after completion | CARRY_FORWARD; staging pixel correctness re-shown by gap3-requal (22/22 cells pixel_ok, S mode) |
| R7 (fatal / halt classes) | no (halting paths precede the new line or never reach it) | CARRY_FORWARD |
| R8–R10 (lifecycle, generation, resources) | no Gate A lifecycle change; R10 activity.maps_count (D-04) is expected to IMPROVE | CARRY_FORWARD; D-04 re-read on the next XFCE / R10-type run |
| B-2 (staging oracle, historical) | yes: the staging transaction now ends with a REMOVE | covered by gap3-requal pixel checks (exact, every cell); no separate rerun |
| oracle V3 (direct, oracle-03 PASS on bfb5769) | no (direct) | CARRY_FORWARD |
| B.3 captures on bfb5769 (G, C, G2, ATTR-02) | G/G2 staging cells (25) had leak-driven memory pressure only above bfb5769 | stay bfb5769 evidence; not pooled with 83d45a9 |

Not poolable: 83d45a9 runs with any bfb5769 run.
