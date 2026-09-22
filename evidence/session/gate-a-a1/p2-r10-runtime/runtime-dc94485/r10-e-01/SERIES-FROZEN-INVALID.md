# R10-E series 01 — FROZEN INVALID (runner defect mid-series)

DATE 2026-09-22  PRODUCT dc94485

## Verdict

**R10_INVALID — RUNNER_ABORTED_MID_SERIES.** The series id is consumed. It is never
rerun and never reclassified; `r10-e-02` takes the next id. Per V2-R10-DESIGN §9 a
round that fails to capture invalidates the SERIES, not just the round, because the
rounds are only comparable to each other.

## E1 — the F ending — worked, and is worth reading even though the series is void

```
identity-before   x_pid 13010 · activity_pid 8984
raw-logcat        GATEA_FATAL_HALT what=r-test-fatal-pre-fence reason=6
ending            x_alive_after=false · activity_pid_after=   (empty)
```

The armed fault fired in the renderer, the renderer PUBLISHED the fatal, and **both
processes are gone**. That is exactly D-06 §2.3: a published fatal reaches X inside
its own terminal wait and X exits, and the Activity's peer-HUP classifies PRESERVE
and exits 127 too. Nothing here is claimed as a verdict — the series is INVALID —
but it is the third independent runtime confirmation of the F arm.

## Why the series is INVALID

E2 aborted at `run-r10.sh:192`:

```
./run-r10.sh: line 192: r: unbound variable
```

```bash
run_client() {
  local r=$1 m=$2 sd="$EVIDENCE/r$r/state"   # <- here
```

In a single `local` statement the `$r` inside `sd` is expanded against the OUTER
scope. The A, B and C branches all happen to have a loop variable also called `r`, so
the bug was invisible in three green series. The E branch calls `run_client` from
straight-line code with no such variable, and `set -u` turned it into an abort.

E2 therefore never reached its SIGKILL, and E3 never ran at all.

## Fix applied before r10-e-02

The declaration is split into three, with the reason recorded at the site. Nothing
else changed; A, B and C are unaffected and are not re-run.
