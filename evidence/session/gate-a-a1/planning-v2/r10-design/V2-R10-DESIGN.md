# V2-R10-DESIGN — Gate A resource management under the lifecycle V1 actually has

DATE 2026-09-22  PRODUCT `dc94485`  PRECONDITION `V2-R9-AGG` accepted (2/2 PASS),
`D-06` DECIDED.
INPUTS `planning-v2/d06/D-06-DECISION.md`, `p2-r10-probe/probe-01/`.

---

## 1. WHY THIS IS NOT V2.3 §9

Master plan §9.7 sequences `V2-R10-WARM-R1..R5` then `V2-R10-COLD-R1..R5`. That split
was written before R9, and R9 changed the premise underneath it:

```
V2.3 §8.4  WARM : Activity 未重啟，X server 為新
           COLD : Activity 重啟
```

Both are still real configurations. What is NOT real, and what §9 implicitly leaned
on, is a **second generation**. D-06 §2.1: the bump runs exactly once per X process
and a second is unreachable. So a "warm round" cannot mean "the same X moving to
generation 2" — it can only mean **a new X session in a surviving Activity process**,
which D-06 §2.4 proves is reachable, and only through a clean close.

Two further things §9 could not have known:

* **§9.1's K3 "generation close / process exit 後" is not always in-process.** On the
  two unclean endings the process is gone, so there is nothing left to sample. The
  sampling plan has to split in-process from post-mortem (§5).
* **§9.3's metric list is mostly unobservable at intermediate points.** Every Gate A
  counter comes from `lorieGateADumpSummary`, which runs only on a fatal, a clean
  close or a terminate. Measured in probe-01. See §7.

R10's question, restated for the lifecycle that exists:

> **Under the only session lifecycle V1 has, does Gate A give back everything it
> takes — within a session, across sessions in a surviving Activity, and across
> complete restarts?**

## 2. THE LIFECYCLE R10 IS MEASURING

```
one X process = one Gate A session = one sessionNonce, generation 1, one epoch

ends three ways                                    Activity afterwards
  T  clean close (test-control terminate)          SURVIVES  (renderer unbinds)
  F  X publishes a fatal                           dies 127  (HUP_PRESERVE)
  H  X dies with no published fatal                dies 127  (r-hup)
```

T is the only ending that releases anything: `gateACloseGeneration` UNREGISTERs every
buffer, the renderer frees texture -> EGLImage -> AHB and ACKs, `GENERATION_CLOSE` is
exchanged, the renderer unbinds. F and H release nothing — the process dies holding
it, and the OS reclaims.

**So "does Gate A leak?" has two different answers and R10 must not blur them:**

```
per-session, clean ending  -> a correctness question with an exact answer (counters)
across sessions            -> a trend question about the SURVIVING Activity process
across full restarts       -> a system-residue question
```

## 3. THE CELL SET — three modes, replacing WARM-R1..R5 / COLD-R1..R5

```
R10-A  IN-SESSION BALANCE
       one X session, one Activity. The frozen workload N times, sampled between
       iterations. Does ONE workload leave anything behind?

R10-B  SESSION CYCLING ON A SURVIVING ACTIVITY                 <- the V1 question
       one Activity process, >= 5 consecutive X sessions, each ending T.
       Does a SESSION leave anything behind in a process the user never restarts?
       This is §8.4's WARM, correctly scoped: new X, new nonce, generation 1,
       fresh registry. NOT generation 2, and it needs no product change.

R10-C  FULL COLD CYCLING
       >= 5 x (fresh X + fresh Activity), each ending T. Baseline and system
       residue: fds, sockets, /tmp, leftover processes, Stable untouched.
```

`R10-A` is one series. `R10-B` and `R10-C` are >= 5 rounds each, per §9.2's rule,
which survives intact: fewer than 5 and a trend cannot be told from noise.

**Removed from the plan, with reasons, not silently:**

```
generation-2 rounds        unreachable (D-06 §2.1). Not re-scoped, removed.
"warm = same X, next gen"  the same thing under its old name.
F / H endings as ROUNDS    they release nothing by design, so a leak metric taken
                           after them measures the OS, not Gate A. They appear in
                           R10-C as ONE round each (§3.1), to prove the fresh
                           session after them inherits nothing — which is the
                           actual question the user asked — not as a leak series.
```

### 3.1 R10-C round composition

```
C1..C5   ending T   the leak baseline
C6       ending F   one round, then a fresh session: inherits nothing?
C7       ending H   one round, then a fresh session: inherits nothing?
```
C6/C7 are judged on **inheritance and residue only**, never on memory deltas.
Their expected fatal is part of the construction, not a failure (§8.8 of the plan).

## 4. THE FROZEN WORKLOAD

Identical in every round of every mode. Any change invalidates the whole series, not
just the round (§9.7).

```
pairs        4 independent (src, dst) pairs
size         1024 x 1024
formats      src a8r8g8b8 (depth 32), dst x8r8g8b8 (depth 24)   <- the ONLY pair
             lorieCanAccelCompositePictures accepts
op           PictOpOver, full-surface, one composite per pair per iteration
iterations   8 composites per workload unit (2 passes over the 4 pairs)
teardown     the client destroys pictures, pixmaps and GCs explicitly, then
             disconnects. It does NOT terminate X; the runner decides the ending.
```

**Why not the 64x64 pair R8/R9 used.** probe-01 measured it: a 64x64 pair is ~32 KB,
while the Activity's `egl_mtrack` swings ~35 MB between samples and its PSS ~1.4 MB.
The signal was two to three orders of magnitude under the noise floor. Four
1024x1024 pairs is ~32 MB of AHB per iteration, which is measurable; it is also small
enough not to risk an allocation failure that would turn a leak test into an OOM test.

**The correctness answer does not depend on this sizing at all** (§8 class 1). The
sizing exists only so the memory classes have any power.

## 5. SAMPLING POINTS

```
R10-A, per iteration i        A0_i  before the composites
                              A1_i  after the composites, before client teardown
                              A2_i  after client teardown (X has unregistered)
R10-B, per session s          B0_s  after bind, before workload
                              B1_s  after workload + teardown
                              B2_s  at the clean close, from the DUMP          <- counters
                              B3_s  after X is gone, on the SURVIVING Activity
R10-C, per session            C0    system, before the session exists
                              C3    system, after both processes are gone
```

`B2_s` is the only point where Gate A counters exist. `B3_s` has no X process, so
every X metric is `null` — that is a fact, not a gap.

For endings F and H there is no `B2`/`B3` equivalent: the dump may exist (a fatal
dumps too) but the Activity is gone. Those rounds record a **post-mortem block**
instead: process absence, socket absence, `/tmp` residue, and the next session's
`B0`.

## 6. NOISE CHARACTERISATION — RUN BEFORE ANY JUDGED ROUND

`V2-R10-NOISE` runs first, as its own packet, and its output is **frozen before the
first judged round is started**. It is the plan's "雜訊範圍必須事先定義" made
executable rather than asserted.

```
structure    identical to R10-B: >= 5 sessions, same sampling cadence,
             same clean ending
workload     NONE. The client connects, holds for the same wall time the real
             workload takes, and disconnects without creating a single pixmap.
output       per metric: min, max, max |delta| between consecutive samples,
             and max |B3_s - B0_1| across the whole run
```

Tolerance for a metric = **2 x its max |delta| observed in the noise run**, floored
at 1 for counts and at 512 KB for KB-valued metrics. Frozen in
`r10-tolerance.json` with the noise run's hash. Changing a tolerance after a judged
round has been seen is forbidden and is the one thing that would void R10 entirely.

## 7. METRIC FREEZE — observable / derived / unavailable

Measured in probe-01. `unavailable` means **null**, always; writing 0 is permanently
forbidden (§9.5).

```
X PROCESS (local /proc)                                              OBSERVABLE
  fd_count fd_table_size maps_count threads rss_kb vm_size_kb
  pss_kb pss_anon_kb pss_shmem_kb

ACTIVITY PROCESS                                                     OBSERVABLE
  stat/status/statm       plain adb shell
  fd_count maps_count smaps_rollup(pss)   ONLY via `run-as <pkg>`; plain adb
                                          shell gets Permission denied / empty
  native_heap gfx_dev egl_mtrack gl_mtrack  ONLY via `dumpsys meminfo`

GATE A COUNTERS, at a DUMP point only                                OBSERVABLE
  all 28, by index, via tests/common/gatea_counters.py
  AHB_ACQUIRE/RELEASE  EGLIMAGE_CREATE/DESTROY  TEXTURE_CREATE/DELETE
  X_REGISTRY_CURRENT  RENDERER_REGISTRY_CURRENT  LEASE_CURRENT
  GENERATION_FATAL  UNREGISTER  RESOURCE_DESTROY  GENERATION_CLOSE

GATE A STATE, at a NON-dump point                                    DERIVED
  x_registry_current          REGISTER_READY(1,role=1) - UNREGISTER_ACK(25,role=1)
  renderer_registry_current   the same with role=2
  lease_current               LEASE_RESERVED(2) - LEASE_RELEASE(23), role=1
  from the live gatea-telemetry stream, which is unconditional and windowed to
  the round by `logcat -T`

UNAVAILABLE -> null, every round                                     NULL
  ahb_lock_in_fence_fd_count      no trace site exists
  ahb_unlock_out_fence_fd_count   no trace site exists
  ahb_fence_fd_leaked             derived from the two above; cannot be computed
  AHB/EGLImage/texture at a NON-dump point   counter-only, no event is traced
  any X metric at B3 (X is gone)  structurally absent, not unmeasured
```

> The three `ahb_*_fence_fd` metrics V2.3 §9.4 added from V-5 have **no
> instrumentation in this product**. They are frozen `null` rather than dropped, so
> the gap stays visible. Adding the trace sites is a product change and therefore a
> D-12-class decision; R10 does not make it, and R10 cannot answer the fence-fd
> ownership question without it. Recorded as an R10 limitation in §10.

## 8. PASS CRITERIA — four classes, all defined before any judged data

### Class 1 — protocol counters. Exact. Zero tolerance.
At every `B2` (clean close):
```
c18 X_REGISTRY_CURRENT        == 0
c19 RENDERER_REGISTRY_CURRENT == 0
c20 LEASE_CURRENT             == 0
c24 GENERATION_FATAL          == 0          (T rounds only)
c12 == c13   AHB acquire == release
c14 == c15   EGLImage create == destroy
c16 == c17   texture create == delete
c27 GENERATION_CLOSE          == 1
session_nonce == 0 and generation == 0      the close zeroed them
```
Any inequality is **FAIL**, not "within tolerance". These are counts of protocol
events, not measurements of a noisy system. probe-01 shows the healthy shape:
16/16, 16/16, 16/16, 0, 0, 0, 0, 1.

### Class 2 — in-session balance (R10-A). Exact where derived, tolerance elsewhere.
```
derived x_registry_current and renderer_registry_current at every A2_i  == 0
derived lease_current at every A2_i                                     == 0
X fd_count            A2_i - A2_1 within tolerance, and not strictly increasing
X maps_count          same
```

### Class 3 — cross-session trend (R10-B/C). Judged as a trend, never on one delta.
For each metric, over the >= 5 same-named sampling points:
```
LEAK        strictly increasing across ALL rounds AND total delta > tolerance
ONE-OFF     rises then flat; must be explained in the aggregate, not ignored
NOISE       |total delta| <= tolerance                        -> pass
```
`egl_mtrack` and `gfx_dev` additionally require the noise run's band, because
probe-01 measured them moving by tens of MB with the workload unchanged.

### Class 4 — residue and redlines. Binary.
```
X3 socket absent after every session
no leftover x11gpu process
Stable com.termux.x11 :1 before == after, byte-identical, every round
the next session's B0 shows a NEW sessionNonce and empty registries
```

## 9. SERIES AND ATTEMPT POLICY

```
a ROUND that fails to capture            INVALID, frozen, and the SERIES restarts
                                         under a new series id
a round whose workload differed          the whole series is void (§9.7)
tolerances                               frozen before the first judged round;
                                         changing one afterwards voids R10
noise run                                re-run required if the artifact changes
```

The R9 lesson applies unchanged: a consumed round is never reclassified, and a
tooling defect found by a round is written up in that round's directory.

## 10. WHAT R10 DOES NOT ANSWER

```
fence fd ownership            no instrumentation exists (§7). Needs a product change.
anything about generation 2   unreachable (D-06)
anything about F/H endings
  as leak data                they release nothing by design; they are inheritance
                              tests only
XFCE-scale workloads          bounded XFCE is a separate packet (plan §11)
performance                   B.3 telemetry, not R10
```

## 11. PACKET SEQUENCE

| # | packet | type | precondition |
|---|---|---|---|
| 1 | `V2-R10-DESIGN` | design | this document |
| 2 | `V2-R10-PROBE-INVENTORY` | host | probe-01 (done) |
| 3 | `V2-R10-HOST-VERIFY` | host | 2 |
| 4 | `V2-R10-NOISE` | device, >= 5 sessions | 3 |
| 5 | `V2-R10-A` | device, one series | 4, tolerances frozen |
| 6 | `V2-R10-B-R1..R5` | device | 5 |
| 7 | `V2-R10-C-R1..R7` | device | 6 |
| 8 | `V2-R10-AGG` / `D-04` | aggregate | 7 |

`V2-R10-HOST-VERIFY` must additionally pin the D-06 reopen condition that R9's
verifier does not cover: that `lorieGateAClassifyPeerHup` still terminates on BOTH
bound arms. If that ever changes, a bound Activity could survive a HUP, warm
reconnect becomes reachable, and D-06 and the R9 WARM removals must be reopened.
