# V2-R10-AGG — Gate A resource management, aggregate result

DATE 2026-09-22  PRODUCT `dc94485a7ef4f74cada36ea3c1d35d0aa0f48693`
APK `1bd8bef0…b8a3`  CI 35673085569
DESIGN `planning-v2/r10-design/V2-R10-DESIGN.md`  ·  `planning-v2/d06/D-06-DECISION.md`

---

## RESULT

```
R10-A  in-session balance, 5 iterations, one session      PASS
R10-B  5 sessions on ONE surviving Activity               PASS
R10-C  5 full cold cycles                                 PASS
R10-E  the F and H endings + a fresh session              PASS

NO LEAK in any series. Zero counter imbalance in 15 clean closes.
Stable com.termux.x11 :1 untouched in every series.
```

One finding is carried to **D-04** rather than waved through: an unexplained upward
drift in the Activity's mapping count. See §5.

## 1. WHAT EACH SERIES ANSWERED

### R10-A — does ONE workload leave anything behind?

Five iterations of the frozen workload inside a single session. At every iteration,
derived from the live telemetry:

```
x_registry_current 0 · renderer_registry_current 0 · lease_current 0
direct_success_events 8   (4 pairs x 2 passes, zero CPU fallback)
```

Five for five. The workload takes the GPU path and gives everything back before the
next iteration starts.

### R10-B — does a SESSION leave anything behind in a process the user never restarts?

This is the V1 question. Five consecutive X sessions against **one Activity process
(pid 25809 throughout)** — the warm reattach of D-06 §2.4, exercised four times.

```
session nonces   null, 512192…193, 12031539…577, 6587275…485, 2038408…570
generations      1, 1, 1, 1, 1
per session      AHB 8/8 · EGLImage 8/8 · texture 8/8
                 x_registry 0 · renderer_registry 0 · lease 0 · ring overflow 0
                 8 direct successes
trend            82 NOISE, 9 ONE_OFF, 0 LEAK
```

Round 1's nonce is `null` because its bind happens during `start_x`, before the
round's logcat window opens. Null is NOT OBSERVED and is left as such; the four that
were observed are all distinct.

**Every session is generation 1.** That is D-06 enforced at runtime, not assumed:
`judge-r10.py` fails the run if any session reports generation 2, because that would
mean a generation boundary became reachable and D-06 plus the R9 WARM/COLD-2
removals would have to be reopened.

### R10-C — does the SYSTEM leak across complete restarts?

Five cold cycles, fresh Activity and fresh X each time.

```
activity pids    10218, 27996, 1057, 6632, 7692     all distinct
session nonces   five distinct values
generations      1, 1, 1, 1, 1
per round        AHB 8/8 · EGLImage 8/8 · texture 8/8 · registries 0 · lease 0
residue          /tmp/.X11-unix contains only X1 (Stable) after every round
trend            76 NOISE, 15 ONE_OFF, 0 LEAK
```

### R10-E — after an unclean ending, does the next session inherit anything?

```
E1  F ending   armed renderer-fatal-pre-fence
               -> GATEA_FATAL_HALT what=r-test-fatal-pre-fence reason=6
               -> X dead AND Activity dead
               -> registries still held 2 and 2 when the processes died
E2  H ending   X SIGKILLed with nothing published
               -> GATEA_FATAL_HALT what=r-hup reason=6
               -> X dead AND Activity dead
E3  fresh      new nonce, generation 1, zero halts, clean close
               where=x-close-screen nonce=0 generation=0 generationFatal=0
```

Three distinct nonces. **Both unclean endings kill both processes**, which is D-06
§2.3 confirmed a third and fourth time, now deliberately rather than incidentally.

E1's registries holding 2 entries at death is **not a leak and is not scored as one**.
The F and H endings release nothing by design — the process dies holding, the OS
reclaims — so a leak metric taken after them measures the OS. The judge returns early
for mode E for exactly this reason, and vector E02 pins it.

The SIGKILL in E2 is **construction, not cleanup**. `r-hup` is the evidence the round
exists to capture; it is recorded, never suppressed, and the target pid and cmdline
are written to `h-construction.txt` before the signal.

## 2. THE CLEAN-CLOSE SIGNATURE, 15 TIMES

Across R10-B (5), R10-C (5), R10-E3 (1) and probe-01 (1), plus the four smoke closes,
every clean close produced the same shape:

```
where=x-close-screen · nonce=0 · generation=0 · generationFatal=0
AHB acquire == release · EGLImage create == destroy · texture create == delete
X_REGISTRY_CURRENT 0 · RENDERER_REGISTRY_CURRENT 0 · LEASE_CURRENT 0
GENERATION_CLOSE 1
```

These are **counts of protocol events, judged exactly, with no tolerance**. Class 1 of
the design. Not one of them was off by one.

> This is also where the counter-index defect would have landed. Read as c25/c26 —
> as the tooling did until `waydefu/termux-x11@b68770f` — every one of these clean
> closes reports **8 leaked entries on each side**. R10 would have opened with a
> fabricated leak in all 15 closes. It was found by reading the enum, before any R10
> round existed, and no R9 verdict had depended on it.

## 3. TOLERANCES WERE FROZEN BEFORE ANY JUDGED ROUND

`V2-R10-NOISE` ran first: five sessions, identical structure, **no workload at all**.
`r10-tolerance.json` was derived from it and frozen before R10-A started.

```
rule    2 x max|delta between consecutive same-tag samples|,
        floored at 1 for counts and 512 for *_kb
```

The floors matter: a noise run that happened to be perfectly still would otherwise
freeze a zero tolerance and make the first ordinary +1 a FAIL.

The judge refuses a tolerance file that is not `R10_TOLERANCE_FROZEN_V1` or whose
`apk_sha256` differs from the ledger's, and `r10_tolerance.py` refuses to derive from
anything that is not a 5-round, halt-free, Stable-unchanged noise ledger. Changing a
tolerance after seeing judged data voids R10; nothing was changed.

## 4. WHAT THE MEMORY METRICS CAN AND CANNOT DO

The frozen tolerances say this plainly:

```
x.fd_count            1          a real detector
activity.maps_count   2          a real detector
activity.fd_count     8
x.pss_kb          17114 KB       ~17 MB of idle noise
activity.pss_kb   21098 KB       ~21 MB
activity.rss_kb   24480 KB       ~24 MB
x.vm_size_kb     744960 KB       ~728 MB: this metric cannot detect anything
```

The workload allocates ~32 MB of AHB per iteration, which is barely above the PSS
noise band even after being raised from R8/R9's 64x64 pairs (~32 KB, which was two to
three orders of magnitude below it — measured in probe-01).

**So R10's correctness answer does not rest on the memory classes.** It rests on the
protocol counters, which are exact, and on the fd and mapping counts, whose bands are
tight. The memory metrics are recorded with their bands and can only refute a large
leak; that limit is stated here rather than left for a reader to infer from a green
result.

## 5. THE ONE FINDING CARRIED TO D-04

`activity.maps_count` drifts **upward** across sessions, outside the idle band:

```
R10-B  @B3   4050, 4058, 4057, 4058, 4060      +10 over 5 sessions   tol 2
R10-C  @B3   4024, 4037, 4020, 4042, 4046      +22 over 5 rounds     tol 2
R10-C  @B0   4021, 4042, 4020, 4034, 4034      +13                   tol 2
```

It is **not** classified LEAK: the rule requires strictly increasing across all
rounds and these dip (4058 -> 4057, 4042 -> 4020). But the direction is consistently
positive and the magnitude is five to ten times the idle band, so calling it noise
would be a stretch.

What it is not: a Gate A accounting failure. The counters are exact and balanced in
every one of those same rounds, and the same drift appears in R10-C, where **every
process is new each round** — so it cannot be accumulation inside a long-lived
Activity. That points at mapping churn in the Android/driver layer rather than at
Gate A's own bookkeeping, but R10 has not proven that and does not claim it.

```
DISPOSITION   open for D-04. Not a V1 blocker on this evidence: ~2-4 mappings per
              session, no counter imbalance, no fd growth, no PSS trend.
TO RESOLVE    a longer series (20+ sessions) would separate drift from churn, and
              /proc/<pid>/maps diffing would name what is accumulating. Neither is
              needed to close R10; both are cheap if D-04 wants them.
```

## 6. WHAT R10 DOES NOT ANSWER

```
fence fd ownership       the three ahb_*_fence_fd metrics have NO trace site in
                         dc94485 (R-30). Frozen null so the gap stays visible.
                         Instrumenting them is a product change R10 does not make.
generation 2             unreachable (D-06). R10 instead ENFORCES its absence.
XFCE-scale workloads     bounded XFCE is a separate packet (plan §11)
performance              B.3 telemetry, not R10
large-scale drift        see §5
```

## 7. SERIES LEDGER — every series, including the one that failed

```
noise-01     captured, not judged (a noise run is never judged: vector N23)
r10-a-01     PASS
r10-b-01     PASS
r10-c-01     PASS
r10-e-01     INVALID, frozen. `local r=$1 m=$2 sd="...$r..."` expands $r against the
             OUTER scope; A/B/C all happen to have a loop variable named r, so three
             green series never touched it. The E branch calls run_client from
             straight-line code and set -u aborted mid-series.
             SERIES-FROZEN-INVALID.md records it, including that its E1 round had
             already captured the F ending correctly.
r10-e-02     PASS
```

One blocked start (`R10_BLOCKED x3_already_running`) consumed nothing, which is what
a preflight gate is for.

## 8. HOST GATES AT THIS COMMIT

```
verify-r10-support.py   R10_SUPPORT_HOST_STATIC_OK
                        metrics=43 derived=3 observable=20
                        observable_at_dump_only=15 unavailable=5
test-judge-r10.py       39 vectors, 0 failures
test_r10_ledger.py      17 tests, OK
verify-r9-support.py    R9_SUPPORT_HOST_STATIC_OK   (unchanged)
```

Vector **E09** is worth naming: it caught that `d06_holds` sat inside the generic
per-round loop, which mode E returns before reaching. An E round could have reported
generation 2 and still passed. The guard now runs for every mode before any
mode-specific path returns.

## 9. WHAT THIS MEANS FOR V1

Within the lifecycle V1 actually has — one session per X process, fresh-process
recovery, and the clean-close warm reattach — **Gate A gives back what it takes.**

```
per workload   exact, 5/5 iterations
per session    exact, 15/15 clean closes
across sessions in a surviving Activity   no leak, 5 sessions
across full restarts                      no leak, 5 cycles
after an unclean ending                   nothing inherited, both processes gone
```

R10 is **ACCEPTED** subject to D-04's disposition of §5.

This is a resource-safety result. It says nothing about performance, nothing about
XFCE-scale workloads, and nothing about the fence-fd question that has no
instrumentation. P2 closure, B.3 telemetry and the Gate H/W chain remain ahead.
