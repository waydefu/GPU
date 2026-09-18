# GATE A P2 R8-C1 attempt-04 INVALID — END_COUNT_MISMATCH_x — 2026-09-18

```
STATUS: R8_INVALID END_COUNT_MISMATCH_x
        also renderer records after END (END_COUNT_MISMATCH_r latent)
        orchestration v2 did obtain CloseScreen / both ENDs
        frozen; do not retry
        C2–P2 NOT RUN
        Production Gate A BLOCKED
        no product source change authorized
```

Path: `runtime-65938a4/r8-c1/attempt-04-orchestration-v2/`
X PID **21246**. Fixture `CLIENT_OK` FIXTURE_EXIT=0.
TERM to exact owned PID. `X_CLOSE_ENTER` path=`lorieCloseScreen`.
`X_CLOSE_RESULT` generation_close=invoked. X END and renderer END present.
`R_UNBOUND_FINAL` present.

## Count

X END `producer_seq=42` `actual_count=42`, then **10 more** X records
(seq 43–52): CloseScreen `DestroyPixmap` destructor enter/exit, then
DEFER_ENQUEUE/WAKE/DISPATCH/RECHECK.

Renderer END `actual_count=5`, then R_WAKE_SENT ordinal 5 and
`surface_loss`.

Producer END is emitted inside `lorieCloseScreen` **before** remaining
destructor / post-unbind wakes. Frozen completeness
`actual_count == recs excluding BEGIN/END` therefore cannot PASS on this
product SHA without moving `lorieR8ObsEnd` (product source change —
**not authorized**). Collector was not used to drop post-END records.

Judge was not invoked (`PRODUCERS_NOT_FINALIZED` / `R8_INVALID`).
Stable PID **20146** UNCHANGED. `NO_X3` after trap cleanup.

Do **not** retry this path. Do **not** start C2. Do **not** weaken judge.
Historical attempt-01 `MISSING_END_x` and attempt-02/03 BLOCKED remain.
