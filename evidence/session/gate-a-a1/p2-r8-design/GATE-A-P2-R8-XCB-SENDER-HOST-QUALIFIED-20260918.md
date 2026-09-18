# GATE A P2 R8 XCB SENDER HOST QUALIFIED — 2026-09-18

```
STATUS: R8_XCB_SENDER_HOST_QUALIFIED
        parent fb4f017c73e942e13dc2423744acb912c055b74e unamended
        commit b984dedcac731b77ca4cf8899f8a78b7848ad083
        Production Gate A BLOCKED
        no device cell in this packet
        attempts 01–07 remain frozen
```

## RCA (source-backed)

Attempt-07 fixture logged `TERMINATE_SENT` then blocked in `xcb_wait_for_reply`
until `timeout 20` exit 124. Server never logged `TEST_CONTROL op=TERMINATE`.
X then took last-client `DE_RESET` → `CloseScreen` → generation-2. No
`ddxGiveUp`, no X END.

Cause was not Terminate-only. Every homemade LORIE-R8-TEST sender in
`tests/r8/p_r8_lifecycle.c` used:

```c
xcb_send_request64(..., &(xcb_protocol_request_t){
  .count = 1, .ext = NULL, .opcode = 0, .isvoid = 0
});
```

while also stuffing `ext->major_opcode` into the request buffer and passing an
`iovec` without the two reserved prefix slots.

libxcb 1.17.0 `xcb_send_request_with_fds64` (`src/xcb_out.c`):

- unless `XCB_REQUEST_RAW`, writes major/minor itself:
  - `req->ext` set → `vector[0][0] = extension->major_opcode`,
    `vector[0][1] = req->opcode` (minor)
  - else → `vector[0][0] = req->opcode` (core)
- BIGREQUESTS may `--vector`, so `vector[-1]` and `vector[-2]` must be valid
  (`/usr/include/xcb/xcbext.h` on `xcb_send_request64`)
- generated senders (`src/c_client.py`) allocate `struct iovec xcb_parts[count+2]`,
  put data at `xcb_parts[2]`, call `xcb_send_request(..., xcb_parts + 2, &xcb_req)`
  with `.ext = &xcb_xxx_id` and `.opcode = REQUEST_NAME`

`.ext = NULL` plus `.opcode = 0` made the wire request a core opcode 0, not
LORIE-R8-TEST minor 3. That is why fixture SENT ≠ server TERMINATE.

## Repair (host fixture / runner only)

Shared helper `tests/r8/r8_xcb_request.c` `r8_send_checked`:

- `.ext = &r8_ext`, `.opcode = minor`
- zeros header bytes 0–3; libxcb fills major/minor/length
- `struct iovec parts[4]`; payload at `parts[2]`; `xcb_send_request64(..., parts + 2, &req)`
- `xcb_wait_for_reply64` (no 32-bit sequence truncation)
- protocol error prints `error_code` / `sequence` / `minor_code` immediately
- no timeout-as-eaten-request path

Callers: QueryVersion (minor 0), RegisterBuffer (1), Checkpoint (2), Terminate (3).

Runner: `TERMINATE_SENT` is not enough. Before `CLEAN_SHUTDOWN_REQUESTED` it
requires server-side `"phase":"TEST_CONTROL"` and `"op":"TERMINATE"`, else
`R8_INVALID MISSING_TEST_CONTROL_TERMINATE`. Class-B hangup is
`X_HANGUP_AFTER_TERMINATE` only. C2/C5-full `permit_judge` now refuses
hold-without-terminate.

Unchanged: renderer terminal, judge, collector, 2000ms timeout, X END still
only in `ddxGiveUp`, GiveUp(0) still `DE_TERMINATE`, reset path still no END,
post-END still fail-closed, shared ABI / protocol layouts unchanged.

## Host proof

`python3 tests/r8/verify-r8-support.py` → `R8_SUPPORT_HOST_STATIC_OK`

- wrap-test minors 0/1/2/3 dispatch with hdr major=140 and hdr minor=opcode
- malformed core `.ext=NULL .opcode=0` yields hdr[0]==0, not 140
- reply path observed for 0–3
- Terminate still `GiveUp(0)` then no `lorieR8ObsEnd` in the handler
- reset stream without END → not PASS
- terminate-then-giveup stream → X END exactly once
- post-END producer call → `POST_END` / `R8_OBS_POST_END`
- renderer / judge / collector unchanged
- judge SHA `f021048da3c1b729c6f9bf560eba52609b2f980336dd4fab77ad1700438c0e31`
- collector SHA `e6df519a75c872c8a56fac00146585853eec7f17a3f424e70e5d4736340666c8`

## Frozen C1 history (immutable)

| Attempt | Path | Verdict |
| --- | --- | --- |
| 01–05 | historical | frozen original classifiers |
| 06 | `runtime-2a245b0/r8-c1/attempt-06-giveup-end/` | `R8_INVALID MISSING_END_x` |
| 07 | `runtime-fb4f017/r8-c1/attempt-07-terminate/` | `R8_INVALID MISSING_END_x` / `PRODUCERS_NOT_FINALIZED` |

Do not retry 01–07. Do not start C2 until attempt-08 PASS.
Do not start R9. Production Gate A BLOCKED.
