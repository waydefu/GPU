# S3 B3a State (instrumentation ready, zero runtime cells)

## Goal (unchanged)

Measure, for the narrow R3 Over slice only: CPU pixman vs current R3 GPU for
timing, clone bytes, upload bytes, queue latency, GPU execution (via fence,
never `total − CPU` inference), fence wait, DoneComposite, X-byte repair
bytes/time, RSS/FD lifecycle, and exact correctness.

## Current state

```text
instrumentation prepared (4 files, see below)
performance matrix NOT RUN
qualification binary unavailable (link-19, S3 round pending)
B3a = BLOCKED / INCONCLUSIVE (never write FAIL)
```

## Instrumented files (exact)

| File | Content |
|---|---|
| `lorie/.../lorie/b3a_telemetry.h` (new) | record schema (46 fields; unavailable = `null`/`NA`, never 0), ring buffer (16384×352 B ≈ 5.8 MB shared, one-time), monotonic clock helpers, runtime switch |
| `lorie/.../lorie/b3a_telemetry.c` (new) | serialization (JSON/CSV), dump on close |
| `lorie/.../lorie/InitOutput.c` | Prepare/promotion/clone/rect/queue/fence-wait/repair/wall boundaries; CPU-path timing |
| `lorie/.../lorie/buffer.c` | promotion + upload byte accounting (logical vs stride-physical) |
| `lorie/.../lorie/lorie.h` | queue-entry timestamp fields (publish/dequeue/upload/draw) |
| `lorie/.../lorie/renderer.cpp` | renderer-side dequeue/upload/draw-submit stamps |
| `lorie/.../recipes/xserver.cmake` | build line for `b3a_telemetry.c` only |

Runtime switches (env, default off): `TERMUX_X11_B3A_TELEMETRY`,
`TERMUX_X11_B3A_CANDIDATE=cpu|r3`, `TERMUX_X11_B3A_OUTPUT=/path/base`.
CPU baseline uses the existing `TERMUX_X11_DISABLE_EXA_GPU` path with the
identical oracle binary/geometry/order — never an R3-fallback masquerading as
baseline. `gpu_exec_ns` stays `null` by design (fence completion ≠ execution
timestamp).

## Forbidden in B3a (unchanged)

Production routing, Composite predicate, synchronization model, Direct AHB
architecture, dirty texture, hybrid router, any threshold (`w>64 → GPU` style),
mask/A8/two-pass/transform/bilinear/repeat/componentAlpha/Glamor/ANGLE.
