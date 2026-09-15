# Gate A P2 R5 deep investigation — 2026-09-15

Read-only. HEAD `d9b7f60f24e722205891f1ce941816393ae4c695` clean.
No C++ change. No second R5. No R6.
First cell `r5-ahb-cycles/` and rerun `r5-ahb-cycles-rerun1/` not overwritten.

The first investigation treated H1+H2 as one deadlock: renderer holds
`state->lock` across a blocking `conn_fd` write; X is the only reader and
then needs that lock for 24bpp repair. It incorrectly rejected socket fill by
comparing payload bytes (`N×24`) directly with `SO_SNDBUF`. Linux socket
accounting charges each `sk_buff` and bookkeeping overhead, not payload alone.
A bounded socketpair probe on this same POCO/PRoot kernel overturns that
rejection.

## ROOT CAUSE

Observed R5 hang: **PROVEN — unread `EVENT_GPU_COPY_DONE` records exhaust the
AF_UNIX send-buffer accounting; renderer blocks in the notification write
while holding `state->lock`; X reaches RELOCK_DST then waits for that lock in
24bpp repair and can no longer drain the socket.**

The `CLOCK_MONOTONIC`/`pthread_mutex_timedlock` `CLOCK_REALTIME` mismatch in
`lorie_mutex_lock` turns X's lock wait into a busy retry, but it is an
amplifier, not the primary trigger.

## PROVEN

1. After SUCCESS, `gateADoneDirect` always relocks then, for depth < 32,
   `lorieExaRepairDestXByteZero` → `lorieGpuCopyAck`. REPAIR is traced
   only after repair returns (`InitOutput.c` 3048–3077). R5 dest is 24bpp.
2. Repair `PrepareAccess` takes process-shared `state->lock` while
   `gpuCopyPending` is still set. Ack decrements pending after repair
   (`InitOutput.c` 3433–3447, 1862–1867, 3135–3153).
3. Renderer holds `state->lock` across `gateAFencePublishGateA` /
   `notifyGpuCopyDone` and unlocks only after the write
   (`renderer.cpp` 1805–1839, 879–928, 1976–2091).
4. `notifyGpuCopyDone` writes a raw `sizeof(lorieEvent)` record (ARM64
   **24 bytes**) with blocking `write()` via `lorieGateAWriteFull`. Activity
   `conn_fd` is **not** `O_NONBLOCK` (`renderer.cpp` 137–140,
   `activity.cpp` 29–61, 507–526; `lorie.h` 769–785).
5. `gateAWaitTerminal` observes shared `completedSerial` and `usleep(200)`.
   It does **not** pump `conn_fd` (`InitOutput.c` 2741–2764).
6. Lorie never calls `InputThreadPreInit`. `InputThreadRegisterDev` falls
   back to `SetNotifyFd` on the X `dix_main` pthread (`cmdentrypoint.cpp`
   536–538, 1431–1434; `inputthread.c` 194–201, 461–470).
7. PROTO=1 `handleLorieEventsProto` calls `lorieRecordDecoderNext` **once**.
   A fixed 24-byte legacy record needs one callback to consume the 4-byte
   PREFIX and a second callback to consume/emit the remaining 20-byte BASE
   (`lorie.h` 1137–1174, 1207–1229; `cmdentrypoint.cpp` 1232–1256).
8. Device AF_UNIX SOCK_STREAM `socketpair` `SO_SNDBUF=229376` (measured
   2026-09-15; equals `/proc/sys/net/core/wmem_default`). `socket(7)` states
   that Linux reserves socket-buffer space for bookkeeping/internal kernel
   structures; payload bytes are not the occupancy metric.
9. Same-machine bounded probe, with peer unread and sender nonblocking:
   `SO_SNDBUF=229376`; exactly **299 × 24-byte writes** complete; the next
   write reaches `EAGAIN`; payload/FIONREAD is only **7176 bytes**, while
   `TIOCOUTQ=229632`. A blocking variant stops after write 299 with writer
   `wchan=sock_alloc_send_pskb`. This directly falsifies the old
   `815×24 < 229376` reasoning.
10. A bounded decoder-cadence model on the same kernel stalls after 597
    completed writes when each cycle emits one 24-byte record but makes only
    one alternating 4-byte/20-byte decoder call. Two decoder calls per cycle
    drains 10,000 cycles without a stall. Variable normal-main-loop callback
    opportunities therefore explain why the real threshold moved from 815
    to 1279 published records without requiring a poison serial.
11. `pthread_mutex_timedlock` uses an absolute `CLOCK_REALTIME` timeout, but
    `lorie_mutex_lock` constructs it from `CLOCK_MONOTONIC` (`lorie.h`
    96–129). A bounded host probe returned `ETIMEDOUT` in 53 μs instead of
    33 ms. With `lorieConnectionAlive()` true, X retries immediately.
12. Logcat X Gate A lines are dix-main tids **15363** and **31469**, not
    leaders **14858** and **31265**. The old `/proc/$X3/wchan` samples are not
    thread-location proof, but rerun `State: R` is compatible with the proven
    immediate-timeout retry loop.

## CAUSAL CHAIN

```text
one direct cycle
→ renderer fences and release-publishes completedSerial (event 14)
→ renderer still holds state->lock
→ renderer sends one 24-byte EVENT_GPU_COPY_DONE under writer mutex
→ normal X callback advances only one decoder phase per invocation
→ unread sk_buff records accumulate until socket accounting is full
→ renderer blocks in writer mutex/write before state->lock unlock
→ X gateAWaitTerminal sees shared completedSerial (no socket read needed)
→ SUCCESS (17) → RELOCK_SRC (18) → RELOCK_DST (19)
→ 24bpp repair calls loriePrepareAccess while gpuCopyPending is still set
→ X retries state->lock; it cannot return to the only conn_fd reader
→ renderer waits for socket space; X waits for renderer's state->lock
```

This explains both exact terminal prefixes and the absence of REPAIR (20),
ACK (21), pending decrements (22), and lease release (23).

## FALSIFIED

| ID | Claim | Verdict |
|---|---|---|
| old H2 payload arithmetic | `815×24` and `1279×24` are below `SO_SNDBUF`, so the write cannot block | **FALSIFIED.** Same-kernel probe fills the socket accounting after only 299 tiny writes / 7176 payload bytes because each write carries `sk_buff` bookkeeping cost. |
| H3 primary | unfiltered logcat blocked REPAIR | rerun silent-default logcat still hung; logcat is not the primary trigger. |
| H4 | serial 819 unique poison | rerun hung at 1283; serials consecutive. |
| H1 via `/proc/pid/wchan` | old dump proves X idle in `epoll_wait` | sampled process leader, not dix-main tids 15363/31469. |

## RESIDUAL UNKNOWN

- The frozen R5 cells did not capture simultaneous per-thread kernel stacks or
  `TIOCOUTQ` at the hang instant. They are no longer required to identify the
  causal chain because the runtime event boundary leaves X immediately before
  the only contended-lock call, source leaves renderer immediately before the
  only blocking writer call while retaining that lock, and the same-kernel
  probe proves that this tiny-write stream fills far below 229376 payload
  bytes. A future hang dump would be corroboration, not permission to rerun R5.
- Whether renderer itself owned `lorieActivityWriterMutex` or waited behind a
  different Activity writer at the final instant is not known. Every writer
  critical section is a blocking `conn_fd` write, so either variant closes the
  same socket-backpressure/state-lock cycle.

## MINIMUM EVIDENCE

- Hang cells: `r5-ahb-cycles/` (X 14858 / dix-main tid 15363,
  serial 819), `r5-ahb-cycles-rerun1/` (X 31265 / dix-main tid 31469,
  serial 1283). Both end at event 19 after renderer event 14; neither reaches
  event 20/21/23.
- Device sndbuf: `unix_stream_sndbuf=229376` (static probe, removed from
  `/data/local/tmp` after run).
- Same-machine host probes executed from this POCO/PRoot session:
  - nonblocking 24-byte writes: 299 PASS; next `EAGAIN`; FIONREAD 7176;
    TIOCOUTQ 229632;
  - blocking 24-byte writes: writer blocked after 299, kernel
    `wchan=sock_alloc_send_pskb`;
  - one decoder phase/cycle: stall after 597 writes; two phases/cycle:
    10,000 cycles without stall;
  - monotonic absolute deadline passed to `pthread_mutex_timedlock`:
    `ETIMEDOUT` in 53 μs, not 33 ms.
- Independent Luna review confirmed the payload-only falsification is invalid
  and the source chain is complete; it conservatively rated target correlation
  MEDIUM because the frozen cells lack simultaneous thread stacks. Parent
  closes that gap with the exact event-boundary control flow and same-kernel
  socket probe; no device replay was used.

## WHAT NOT TO DO

Do not second-retry R5 on `d9b7f60`. R6–R8 are conditionally authorized by
the user only **after** a corrected artifact makes R5 PASS; that condition is
not met yet.

## IMPLEMENTATION STATUS / NEXT BOUNDARY

The user granted the bounded architecture correction. It is implemented but
uncommitted on `fix/gatea-r5-backpressure-20260915`:

1. Normal PROTO callback continues across `INCOMPLETE` phases and complete
   records until the nonblocking decoder returns `WOULD_BLOCK`.
2. `notifyGpuCopyDone()` is outside `state->lock` for Gate A in standalone and
   redraw paths; fence/completedSerial and legacy placement remain unchanged.
3. RED/GREEN host regression, decoder socketpair, X-pump verifier, ARM64
   incremental/full-clean, 41==41 warning fingerprint comparison, final review,
   and independent review PASS.
4. Generic `lorie_mutex_lock` clock/recovery remains unchanged and recorded as
   a separate hygiene blocker.

Authority:
`../../p2-r5-backpressure-fix/GATE-A-P2-R5-STATIC-IMPLEMENTATION-20260915.md`.

Commit/push/CI/artifact qualification are not done. Obtain explicit shared-
history authorization, then qualify the exact artifact and stop to notify the
user before ADB/install/device/runtime. After corrected-artifact R5 PASS, the
user's conditional authorization opens R6, R7, and R8. R7 still requires an
artifact containing its missing fault hook; no current R6–R8 cell may start on
`d9b7f60`.
