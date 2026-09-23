# INCIDENT 2026-09-23 17:08 (second) — the B.3 S-mode device run exhausted phone memory; lmkd killed com.termux.x11 (Stable) and com.termux

Not caused by host analysis this time: the only host analysis attempted during the run
(missing-seq scan) was REFUSED by safe-run.sh (MemAvailable 1040 MB < floor 3072 MB).

## Timeline (device event log, adb lane 5038, read after the fact)

```
17:07:30  run-device-queue-3.sh -> run-b3.sh MODE=S (b3-s-02), X3 pid 18189, Activity pid 14427
17:07:43  first cell N0000 (1024x1024) begins; lmkd pressure reports start the same second
17:08:09  killinfo com.termux.widget (adj 401) · com.termux.x11 pid 31118 = STABLE :1 app (adj 400,
          not foreground because the experimental Activity was on top)
17:08:12+ com.termux.x11 restarts are killed repeatedly (critical_mem_pressure)
17:08:28  killinfo com.termux pid 7224 (adj 200) -> PRoot, Claude Desktop, adb server, X3 all gone
17:16:03  user swipes the experimental app away (SwipeUpClean); 17:16:06 Termux restarted by the user
```

## What the capture shows (b3-s-02, partial: 9 cells, died in C0237)

```
cell    rect         batch  S (staging, PROTO unset)  G (direct)   C (CPU)     per-op p50
N0000   1024x1024     1     19.1 ms                   2.2 ms       0.43 ms
A0114   1200x2608     8     57.6 ms                   5.5 ms       1.39 ms
A0118   1200x2608    16     68.8 ms                   6.5 ms       3.07 ms
```
G (b3-g-01) and C (b3-c-01) ran the whole 263-cell matrix (+center) without incident.
Pressure started with the FIRST S cell. No allocation-failure line from X3 or the Activity in logcat.

## Cause — what is and is not known

Known: the device workload itself (X3 is a child of the com.termux app process; its memory and
its AHB allocations count against the phone) exhausted memory within ~40 s of S mode.
safe-run.sh guards host analysis only; nothing watched memory DURING a device run.
NOT known: why S does it. Candidate (unproven): the D0a staging path allocates a per-op AHB clone
(a 1200x2608 source = 12.5 MB) faster than they are released. To be settled from source + a
bounded, watchdog-protected measurement - never by rerunning the matrix.

## Required before ANY further device run

1. A memory watchdog inside every device runner: poll MemAvailable every 0.5 s; below a floor,
   SIGTERM X3 by exact pid and force-stop com.waydefu.x11gpu at once (the run becomes
   ABORTED_MEM_GUARD - construction, recorded), so the phone never reaches lmkd.
2. No S-mode (staging) run until the staging memory behaviour is understood.
3. User's explicit go-ahead for device runs (their daily environment died twice today).

b3-s-02 stays as captured (partial); it is not retried.
