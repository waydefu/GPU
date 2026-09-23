# PGA-GAP-3 DESIGN — unregister the per-transaction staging upload when its transaction ends

DATE 2026-09-23 · base `bfb5769` · RCA: PGA-GAP-3-RCA.md · plan §13.2 step 2 (minimal design)

## The change (one rule, one function)

In `lorieExaDoneComposite` (InitOutput.c), before the upload's last X-side reference is dropped:

```c
/* PGA-GAP-3: a non-cached staging upload is registered with the renderer by
 * lorieTryScheduleGpuBlit (InitOutput.c:1855) for THIS transaction only. Done has
 * waited for completedSerial >= lastSerial, so the renderer is finished with it:
 * tell it to drop its copy. The D0a cache buffer keeps its registration by design
 * (it is unregistered when replaced, InitOutput.c:1678). */
if (upload && upload != d0aStagingCache)
    lorieUnregisterBuffer(upload);
```

placed once, after the completion wait and before the `LorieBuffer_release(upload)` calls, on the
non-direct path. On the direct path (`exaGpuComp.direct`) the upload is not scheduled (direct transactions
never stage); it is released there without having been registered — `lorieUnregisterBuffer` on an
unregistered buffer is a no-op (it returns when the id is not in `registeredBuffers`), so the same
line is harmless there and is added for symmetry only if the review wants it; minimal = non-direct path.

## Why this is safe (ordering / ownership)

```
completion   Done calls lorieGpuCopyWaitForCompositeOrFatal(lastSerial) first: every entry of the
             transaction has completed on the renderer (completedSerial is published after the
             renderer's fence wait). No entry of another transaction references this upload id
             (a fresh LorieBuffer_allocate per Prepare -> unique id).
message      EVENT_REMOVE_BUFFER goes over the same conn_fd, in order after the ADD; the renderer's
             removeBuffer path is the same one pixmap destruction already uses (InitOutput.c:3917).
X side       lorieUnregisterBuffer only removes the id from registeredBuffers and writes the event;
             the X-side memory is still released by the existing LorieBuffer_release calls.
cache        d0aStagingCache is excluded: it is reused across transactions and keeps its registration.
failure      conn_fd == -1 (renderer gone): lorieUnregisterBuffer does nothing, as today.
```

Not changed: the per-op full-size clone itself (a cost, PGA-GAP-2 territory), the synchronous wait,
Gate A direct, the D0a cache, any protocol / ABI (EVENT_REMOVE_BUFFER already exists).

## Verification (frozen before the patched artifact runs)

Host: source-level test that `lorieExaDoneComposite` unregisters a non-cache upload after the wait
and before the release, and never unregisters d0aStagingCache (negative vector: removing the line or
dropping the cache exclusion must make it red).

Device (requal, mem-guard on every run):
```
workload   B.3 mode S subset that registered ~7 GB in 45 s on bfb5769 (cells N0000, A0114, A0118, C0237,
           plus the first 20 cells of the S order), NOT the whole matrix
predicate  X "Sent shared buffer ... type 2" bytes >= 3 GB during the run (the workload really stages)
           AND mem-guard never trips
           AND swap used grows < 512 MB and MemAvailable drops < 1024 MB from start to end
           AND the Activity maps_count after the run is within +16 of before
control    b3-s-02 on bfb5769 (frozen): 7382 MB registered, memory exhausted - the same workload that must
           now stay flat. No new run on the unpatched build (it would only trip the guard).
XFCE       the G-configuration soft check activity.maps_count K4-K0 (D-04) is re-read on the next XFCE run;
           tolerance unchanged.
```

---

## Appendix A — requal-01 result and requal-02 (frozen before requal-02 runs)

```
gap3-requal-01 (83d45a9, mode S, 22 cells)   GAP3_REQUAL_FAIL  (frozen; not re-judged)
  staged 15.8 GB (2784 FD registrations)  ✓   mem-guard not tripped   ✓
  swap growth 0 MB                        ✓   MemAvailable drop 169 MB ✓
  Activity maps_count 4035 -> 4054 = +19  ✗ (threshold <= 16)
  pixels 22/22 ok, 0 X errors; screen awake; Stable unchanged; X3 untraced
```

What it shows: the memory leak is gone (bfb5769 exhausted the phone after 7.4 GB; 83d45a9 staged 15.8 GB with
flat memory). The mapping residue per registration fell from 0.166 (xfce3-c1-01: +555 / 3348) to 0.0068
(+19 / 2784). The failing criterion is the maps threshold, which this design set WITHOUT a baseline: the Activity
drifts by itself (R10 D-04 +2..4 per session; XFCE C configuration +6 with zero staging).

requal-02 (new attempt, two fresh runs on 83d45a9, same cells, same runner, S first then C):
```
S run     mode S as requal-01                        -> every requal-01 criterion except maps, unchanged
C run     TERMUX_X11_DISABLE_EXA_GPU=1 (no staging)  -> must register 0 FD buffers (else INVALID: not a control)
maps      (S after - S before) - (C after - C before) <= 16      (the original 16, applied to the residue
                                                                  attributable to staging)
verdict   PASS iff every S criterion holds and the maps residue <= 16; a missing value -> INVALID
```
requal-01 keeps FAIL. If requal-02 fails too, the residue is attributed to staging and PGA-GAP-3 is incomplete.

### requal-02 result (2026-09-23 18:16)

```
gap3-requal-02-s  maps 4034 -> 4056 = +22 · staged 15.8 GB · swap +0 · MemAvailable -238 MB · no trip · 22/22 px
gap3-requal-02-c  maps 4027 -> 4020 = -7  · staged 0 (valid control) · 22/22 px
residue 29 > 16  -> GAP3_REQUAL_FAIL (frozen)
```
Per this appendix: the residue is attributed to staging; **PGA-GAP-3 is incomplete**. What is fixed and proven
(two runs): the multi-GB renderer memory leak (7.4 GB exhausted the phone on bfb5769; 15.8 GB staged with flat
memory on 83d45a9). What remains: ~20-30 Activity mappings per 2784 staged transactions (~0.01 each; bfb5769: 0.166).
Open question for the next step (not answered here): does the residue grow linearly with transactions (a second,
smaller leak) or plateau (driver-side pooling after texture churn)? Discriminator to freeze before running: the same
cells at 2x rounds; linear -> residue ~2x; plateau -> residue ~equal.
