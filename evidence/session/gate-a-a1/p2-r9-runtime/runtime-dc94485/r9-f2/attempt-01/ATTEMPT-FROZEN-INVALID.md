# R9-F2 attempt-01 — FROZEN INVALID (two evidence-source defects; one was my own fix)

DATE 2026-09-22 14:48  PRODUCT dc94485  RUNNER run-r9-one-cell-dc94485.sh V2

## Verdict as recorded

```
judge.json   R9_INVALID  IDENTITY_FIELD_MISSING_shared_nonce
```

Consumed and frozen. Never rerun, never reclassified. attempt-02 takes the next
number.

## The session itself was clean

```
fixture.jsonl   RESULT outcome=CLIENT_OK composite_issued=true
raw-logcat      GATEA_EVENT ... event=5 ...            LEASE_GPU_OWNED, once
                seq=43/46 role=1 event=24/25 src=6     X unregister send + ack, id 6
                seq=45     role=2 event=25   src=6     renderer unregister ack, id 6
                seq=47/50 role=1 event=24/25 src=7     the same pair for id 7
                seq=49     role=2 event=25   src=7
LorieNative     xrender_ops=1 exa_comp_check=1/0 prepare=1/0 gpu_rects=1 cpu_rects=0 done=1
```

One GPU composite, zero CPU rects, both buffers registered and both fully
unregistered on both roles. New X pid, new Activity pid, new nonce. Stable untouched.

## Defect 1 — a dump-only source for a cell that never dumps

`shared_nonce` came only from `GATEA_SUMMARY`, and `lorieGateADumpSummary` runs on a
fatal, a clean close or a terminate — never on a healthy idle server. F2 is the one
cell defined to leave X healthy, so the field was structurally unobtainable and the
cell could not pass. The same held for the c25/c26 registry counters behind
`empty_registry_both_sides`.

Fixed by reading what the product logs unconditionally:

```
shared tuple    GATEA_BIND. gateABindFromState logs
                  lorieGateALoadU64Acquire(&state->gateA.sessionNonce) and .generation
                  (activity.cpp:202-203) BEFORE latching them (:219-220), so it is a
                  real read of the shared words, not the renderer's private copy.
                  The record now carries shared_tuple_source, and renderer_bound_*
                  stays separate: the two halves have different lifetimes.
registry        the telemetry events. REGISTER_READY (1) and UNREGISTER_ACK (25) are
                  traced per id per role, so what each side still holds is
                  (ready - acked) per role. Strictly better than a counter snapshot:
                  it is per-id and immune to ring overflow.
```

## Defect 2 — my own clean-close step made things worse, and is reverted

To obtain those counters this runner had been given a step that `kill -TERM`ed X after
the composite, expecting `CloseScreen -> gateACloseGeneration() -> dump`. It measured
false on both counts:

* **No clean close happened.** X's last log line is 14:48:14.928; there is no
  `X_CLOSE_ENTER`, no `Server stopped`, no `GATEA_SUMMARY`. SIGTERM does not reach
  `CloseScreen` in this build — the process was simply killed.
* **It fatalled the renderer.** `14:48:15.939 GATEA_FATAL_HALT what=r-hup reason=6`
  from the Activity pid, which `judge_f2` reads — correctly — as
  `UNEXPECTED_FATAL_IN_FRESH_SESSION`.

So the step could only ever have turned a clean F2 into a FAIL. Reverted, with the
measurement written into the runner where the step used to be, so it is not
reinvented.

## Offline replay — diagnostic, NOT a verdict

Re-deriving this attempt's own artifacts with the fixed code gives complete boundary
records (`shared_tuple_source: gatea_bind_shared_read` for the F2 half,
`summary_dump` for the F1 half) and `x_entries: 0, renderer_ready_entries: 0` from
`telemetry_events`. The judge then returns **`R9_FAIL UNEXPECTED_FATAL_IN_FRESH_SESSION`**
— because this capture still contains the `r-hup` that defect 2 caused. That is the
right answer for this capture and the reason it cannot be salvaged: the evidence is
contaminated by the runner step, not merely incomplete.

## Fixes landed before attempt-02

```
runner        the clean-close step is gone, replaced by the measurement that killed it
r9_evidence   boundary_record() falls back to GATEA_BIND and records the source;
              registry_state() reads the telemetry events, counters only as fallback
judge         registry counters of None are REGISTRY_COUNTERS_NOT_OBSERVED (INVALID),
              never silently "empty"; ring_events() unions gatea-ring.txt with the
              live gatea-telemetry stream
spec          R9-F2 require_note and evidence_note record both sources and why the
              SIGTERM route is rejected
tests         36 host evidence tests, 32 judge vectors
```
