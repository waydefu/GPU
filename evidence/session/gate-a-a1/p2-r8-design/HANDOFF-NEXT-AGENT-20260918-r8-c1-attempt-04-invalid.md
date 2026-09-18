# Gate A P2 R8-C1 attempt-04 INVALID — 2026-09-18

```
STATUS: R8_INVALID END_COUNT_MISMATCH_x
        GATE A P2 R7 PASS / a4c8177 COMPLETE 13/13
        65938a4 INSTALLED
        v2 obtained CloseScreen + both ENDs
        post-END destructor/wake records vs END.actual_count
        product ObsEnd-before-remainder; source change NOT authorized
        C2–P2 NOT RUN
        Production Gate A BLOCKED
```

Do **not** retry attempt-01/02/03/04. Do **not** start C2 or R9.
Do **not** drop post-END records to force green. Do **not** patch
`lorieCloseScreen` / `lorieR8ObsEnd` without a new product grant.

Packet: `GATE-A-P2-R8-C1-ATTEMPT-04-INVALID-20260918.md`
