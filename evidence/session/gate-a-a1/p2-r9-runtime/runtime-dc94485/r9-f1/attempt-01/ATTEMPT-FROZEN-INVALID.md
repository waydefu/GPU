# R9-F1 attempt-01 — FROZEN INVALID (capture aborted, not a cell failure)

DATE 2026-09-22 14:37  PRODUCT dc94485  RUNNER run-r9-one-cell-dc94485.sh V2

## Verdict

**R9_INVALID — EVIDENCE_CAPTURE_ABORTED.** The attempt number is consumed. It is
never rerun and never reclassified; attempt-02 takes the next number.

## What the cell actually did — it worked

```
raw-logcat.txt:3335  GATEA_SUMMARY where=x-wrong-generation nonce=844202797156858239
                     generation=1 generationFatal=6 fatalReason=6 ... c24=1
raw-logcat.txt:3336  GATEA_FATAL_HALT what=x-wrong-generation reason=6
```

That is R9-F1's EXACT expected fatal (`cmdentrypoint.cpp:640-641`,
`LORIE_GATEA_FAIL_GENERATION = 6`), and the fixture's own log shows the construction
reached it under its own steam:

```
fixture.jsonl  CONNECTED display=:3
               FORMATS fmt32=37 fmt24=41
               PAIR_CREATED
               COMPOSITE_SENT op=PictOpOver w=64 h=64
               RESULT outcome=SERVER_CONNECTION_BROKE composite_issued=true
x-survival.txt x_alive_after_cell=false
```

So the new extension-free fixture `p_r9_boundary` does drive the Gate A direct path
with R8 observation disarmed — which is exactly what r9-cold-2/attempt-01 and
attempt-02 failed to do. **This is not why the attempt is INVALID.**

## Why it is INVALID anyway

The runner aborted in `snap after`, after the cell had already run:

```
snap() { ...
  local ap; ap=$(ADB shell pidof "$EXPECT_PACKAGE" ... )   # <- here
```

`pidof` exits 1 when the process is gone. Under `set -o pipefail` the pipeline
inherits that, the assignment fails, and `set -e` ends the run. R9-F1 halts X and the
Activity goes with it, so "gone" is the EXPECTED state at snap-after time. The
previous cell shape (COLD-2) always restarted the Activity before `snap after`, so
the path had never been exercised with the Activity absent.

Consequently these never got captured:

```
stable-after.json      the Stable-unchanged redline proof  <- the disqualifying one
act-stat-after, x-fdcount-after
gatea-ring.txt, gatea-summary.txt
x-observations.jsonl, renderer-observations.jsonl, identity-boundaries.jsonl
stale-replay.json, judge.json
```

`judge-r9.py` runs `check_stable()` before dispatch, so without `stable-after.json`
there is no verdict to give. Backfilling it minutes later from a different device
state would be manufacturing evidence for a frozen attempt, which is forbidden.

## Fix applied before attempt-02

`snap()` now tolerates the absent process: `... ) || ap=""`. The absence is recorded
(`act-stat-after` empty) instead of ending the run. Nothing else changed.

## What is NOT claimed here

No PASS. The expected fatal is present in this directory's `raw-logcat.txt` and can be
read, but a verdict requires the full evidence set and this attempt does not have it.
attempt-02 must reproduce the fatal on its own; this file is not a precondition for
anything and `f1-precondition.json` for R9-F2 is derived from a `judge.json` verdict,
which this attempt has none of.
