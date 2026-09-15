# Gate A P2 R5 hang investigation — 2026-09-15 (rerun FAIL REPRODUCED)

First cell `runtime-d9b7f60/r5-ahb-cycles/` is **historical FAIL**. Do not overwrite.
This note is source+log alignment only. No C++ change. No R6.

## Bound facts (PROVEN)

1. Pixel path was exact through CYCLE 768 / checkpoint 256.
2. Last GATEA line is `event=19` RELOCK_DST serial **819** at 02:35:32.590.
   Renderer had already logged COMPLETED (`event=14`) for 819.
3. No REPAIR(20) / ACK(21) / LEASE_RELEASE(23) for 819. Client stayed in
   `poll`. X later `epoll_wait`. No fatal.
4. `gateADoneDirect` after SUCCESS is `gateAPairRelockCpu` → 24bpp
   `lorieExaRepairDestXByteZero` → `lorieGpuCopyAck`
   (`InitOutput.c` 3054–3071). REPAIR is traced **after** the repair call.
5. Repair `PrepareAccess` takes `state->lock` when `gpuCopyPending` is still
   set (`InitOutput.c` 3434–3447, 1862–1867). Ack is **after** repair.
6. Renderer `applyPendingGpuCopies` holds `state->lock` across
   `gateAFencePublishGateA` including COMPLETED trace and
   `notifyGpuCopyDone` → blocking `write()` on `conn_fd`
   (`renderer.cpp` 1805–1839, 879–928, 138–140; `lorieGateAWriteFull`).
7. `lorie_mutex_lock` on ETIMEDOUT **retries forever** while
   `lorieConnectionAlive()` (`lorie.h` 114–116).

## Hypotheses

| ID | Claim | Status |
|---|---|---|
| H1 | X livelocks in repair `PrepareAccess` on `state->lock` while renderer still holds it (fence/COMPLETED/`GPU_COPY_DONE` write) | **INFERRED** — source order + last log; dix_main tid not sampled (`/proc/$X/wchan` is ART leader) |
| H2 | `conn_fd` fills with unread `EVENT_GPU_COPY_DONE` so renderer `write` blocks while holding `state->lock` | **FALSIFIED at observed N** — device unix `SO_SNDBUF=229376`; 815×24 and 1279×24 ≪ sndbuf. Lock-across-write remains a latent invariant. |
| H3 | logcat `DEBUG:I` + 23 MB follow blocked `android_log_print` on REPAIR | **FALSIFIED as primary** — bounded rerun used silent-default logcat (6.2 MB) and hung at the same RELOCK_DST/missing-ACK boundary |
| H4 | Unique serial-819 protocol poison / ring wrap | **FALSIFIED** — first cell serials 5–819 consecutive; rerun hung at serial **1283** (5–1283 consecutive); TRACE wrap is 512 |

## Bounded rerun (authorized)

One cell `r5-ahb-cycles-rerun1/`. Same APK, same `p_r5_ahb_cycles` ELF.
Harness-only: logcat `gatea-telemetry:V gatea-a1:V LorieNative:I *:S`; 45 s
fixture-output stall watchdog. Keep PROTO=1 TELEMETRY=1.

**RESULT:** hang **REPRODUCED** (X 31265, last `event=19` serial **1283**,
ack=success−1, checkpoint 1024 PASS, 4096 not reached). Stop. No C++ patch.
No second retry. See `GATE-A-P2-R5-RUNTIME-RERUN-20260915.md`.

Deep follow-up (source + device sndbuf, no rerun): observed hang root cause
**NOT PROVEN**. H2 fill-at-815 **FALSIFIED**. See
`GATE-A-P2-R5-DEADLOCK-20260915.md`.
