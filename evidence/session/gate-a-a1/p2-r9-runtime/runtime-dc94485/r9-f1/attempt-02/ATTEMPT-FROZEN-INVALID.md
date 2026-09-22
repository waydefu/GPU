# R9-F1 attempt-02 — FROZEN INVALID (two derivation defects, not a cell failure)

DATE 2026-09-22 14:39  PRODUCT dc94485  RUNNER run-r9-one-cell-dc94485.sh V2

## Verdict as recorded

```
judge.json   R9_INVALID  IDENTITY_FIELD_MISSING_x_fd_table_had_previous_conn_fd
```

Consumed and frozen. Never rerun, never reclassified. attempt-03 takes the next
number.

## The cell itself worked, again

```
raw-logcat.txt:13076  GATEA_VALIDATE ... bufferId=6 stage=READY_SEND_ENTER  result=1
raw-logcat.txt:13077  GATEA_VALIDATE ... bufferId=6 stage=READY_SEND_RETURN result=1
raw-logcat.txt:13078  GATEA_EVENT seq=20 role=2 event=35 generation=1 serial=0 src=16 dst=2
raw-logcat.txt:13080  GATEA_VALIDATE ... bufferId=6 stage=VALIDATE_TERMINAL_READY result=1
raw-logcat.txt:13098-13101  the same four for bufferId=7
raw-logcat.txt:13105  GATEA_FATAL_HALT what=x-wrong-generation reason=6
```

Event 35 is `LORIE_GATEA_EVENT_TEST_FAULT_FIRED` and `lorieGateATrace` puts the CELL
number in `src`, so `src=16` is cell 16, `stale-ready-replay`, firing exactly once.
`stable-before.json` and `stable-after.json` are byte-identical: the Stable lane was
untouched.

## Defect 1 — the identity contract demanded a field nothing captured

`x_fd_table_had_previous_conn_fd` is mandatory in `r9-identity-contract.json`, whose
own rationale says it "must come from `/proc/<x_pid>/fd` at the boundary" — and the
runner never read `/proc/<x_pid>/fd`, it only counted entries. It passed
`--fd-had-prev unknown`, which becomes `None`, and `load_boundaries` correctly refuses
`None` as NOT OBSERVED. The cell could never have passed, and COLD-2 would have hit
the same wall had it ever got this far.

Fixed by capturing the table (`x-fdlist-<tag>`, `ls -l /proc/$X3/fd`) and deriving the
answer in `r9_evidence.fd_previous_conn()`, which answers only what the capture
supports: no listing -> None; listing plus at most one bind -> False, because with a
single bind there was never a previous connection to retain; listing plus a rebind ->
None, because that needs per-fd peer identity and nothing captures it. F1 and F2 do
not cross a rebind; the WARM cells that did are removed.

## Defect 2 — stale_replay() read the wrong source, and read it circularly

`legitimate_ready_sent` came out **false** on a run where two buffers each logged
`READY_SEND_RETURN result=1`. The derivation only looked at `R8_OBS` rows, but the
validate stages are `LorieNative` `GATEA_VALIDATE ... stage=X result=N` lines
(`renderer.cpp:369`) — and R9 runs with R8 observation DISARMED, so the obs stream is
thin by design. Had defect 1 not fired first, this would have produced
`INVALID VALIDATE_IMPORT_NOT_REACHED` on a correct run.

`stale_frame_sent` was worse than wrong. It matched the literal string
`TEST_FAULT_FIRED`, which never appears in any log line, and then fell back to *the
expected fatal itself*. Taking the fatal as proof the frame was sent, while the judge
requires that same fatal for the verdict, is one check wearing two hats. It now reads
the independent `event=35 src=16` telemetry, and a fault fired for a different cell
does not count.

## Offline replay — diagnostic, NOT a verdict

Re-deriving this attempt's own `raw-logcat.txt` with the fixed code yields
`legitimate_ready_sent=true, stale_frame_sent=true, gate_a_active_on_arrival=true` and
`judge-r9.py` returns `R9_PASS`. **That replay substituted a synthetic fd listing**,
because this run never captured one — that is the whole of defect 1. A substituted
input is not evidence. attempt-03 has to produce the fatal and the fd table itself.

## Fixes landed before attempt-03

```
runner        snap() also writes x-fdlist-<tag> (ls -l /proc/$X3/fd)
              derive is passed --x-fdlist-before/--x-fdlist-after/--prev-x-fdlist
r9_evidence   fd_previous_conn(), binds_observed(), validate_stages(),
              test_fault_fired(); stale_replay() rewritten on both real sources
tests         33 host tests (was 23): the two real log shapes verbatim from this
              attempt, a circularity guard, a wrong-cell guard, and the four
              fd-table answers
```
