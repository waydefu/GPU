# Gate A P2 R3 — X main-thread reply-pump design review

Date: 2026-09-14

## Status

```text
DESIGN REVIEW: PASS — IMPLEMENTATION AUTHORIZED BY USER
SOURCE IMPLEMENTATION: AUTHORIZED / NOT YET STARTED
BUILD / CI / APK / RUNTIME: NOT RUN
R3 88e3f17: FROZEN FAIL / DO NOT RETRY
Production Gate A: BLOCKED
Stable / HDMI: UNTOUCHED
```

This is a source-only architecture correction. It does not rewrite the frozen `88e3f17` runtime result. The runtime report correctly records the then-known classification `NARROWED`; the combined source and runtime evidence below now proves the first causal blocker.

## 1. Authority and inspected state

| Item | Authority |
|---|---|
| Gate A worktree | `/root/projects/GPU加速/src/f8-ahb-gatea-a1` |
| Branch | `qualification/gatea-a1-microprobe-20260912` |
| Source HEAD | `88e3f176d5be313b7dee058da9021cfe8d09e7de` |
| Source state | clean; `git diff --check` PASS |
| xserver submodule | `65d790bd208ec380b196eb98f144abb0b32e334d` |
| Runtime authority | `../p2-r3-terminal-runtime/runtime-88e3f17/GATE-A-P2-R3-RUNTIME-20260914.md` |
| Current handoff | `../p2-r3-terminal-runtime/HANDOFF-NEXT-AGENT-20260914.md` |
| ABI review needing erratum | `../GATE-A-PROTOCOL-ABI-REVIEW-R3-20260912.md` |
| Ownership review needing thread-model note | `../GATE-A-P2-OWNERSHIP-ARCHITECTURE-REVIEW-20260913.md` |

Frozen invariants remain:

- Stable `com.termux.x11` / `:1` is never touched.
- Experimental work remains default OFF and isolated to `com.waydefu.x11gpu` / `:3`.
- Queue entry ABI remains 168 bytes.
- Gate A frame header remains 40 bytes.
- P0 result sideband remains 40 bytes.
- Direct side metadata remains 48 bytes.
- READY / UNREGISTER_ACK / GENERATION_CLOSED budgets remain 2000 ms.
- Ownership, completion, fence, replay, predicate, D0a, D0b, and Gate H semantics are not reopened here.

## 2. Proven root cause: the waiter and the only socket reader are the same X thread

### 2.1 There is no lorie input thread

The lorie build compiles `xserver/dix/main.c` and `xserver/os/inputthread.c`, but its source lists do not include xfree86 or kdrive:

- `lorie/src/main/cpp/recipes/xserver.cmake:85-90`
- `lorie/src/main/cpp/recipes/xserver.cmake:137-142`

The only real call sites of `InputThreadPreInit()` in this xserver tree are:

- `xserver/hw/xfree86/common/xf86Init.c:730`
- `xserver/hw/kdrive/src/kinput.c:1124`

No lorie source, recipe, or patch calls it.

`InputThreadPreInit()` is what allocates `inputThreadInfo` (`xserver/os/inputthread.c:397-419`). Although `dix/main.c:273` calls `InputThreadInit()`, that function explicitly returns when pre-init was never requested (`xserver/os/inputthread.c:462-470`). Therefore lorie does not create `InputThreadDoWork`.

### 2.2 `InputThreadRegisterDev` degrades to a main-loop notifier

The X connection is registered in `cmdentrypoint.cpp:1061-1065` using `InputThreadRegisterDev(fd, handleLorieEvents, ...)`.

With `inputThreadInfo == NULL`, that function executes:

```text
return SetNotifyFd(fd, readInputProc, X_NOTIFY_READ, readInputArgs)
```

at `xserver/os/inputthread.c:193-201`.

`SetNotifyFd` callbacks execute from the server's normal `WaitForSomething()` → `ospoll_wait()` path:

- `xserver/os/WaitFor.c:201-208`
- `xserver/os/ospoll.c:643-658`

That is the X server dispatch/main thread, not a dedicated input thread.

### 2.3 The same thread sends REGISTER and sleeps

A direct Composite reaches `gateAEnsureReady()` through `gateADirectTryPrepare()` (`InitOutput.c:2663-2665`). It arms the waiter, sends REGISTER, then calls `lorieGateAWaiterWaitUntil()`:

- arm: `InitOutput.c:2371`
- send: `InitOutput.c:2372-2375`
- condvar wait: `InitOutput.c:2376-2383`
- timeout: `InitOutput.c:2394-2409`

The only success transition is the socket receive path:

```text
handleLorieEvents
→ handleGateAFrame
→ lorieGateARegistryMarkChecked
→ lorieGateAWaiterSignal(DONE)
```

at `cmdentrypoint.cpp:177-190`, `607-652`, and `705-739`.

The X main thread cannot return to `WaitForSomething()` to invoke `handleLorieEvents` while it is sleeping in `gateAEnsureReady()`. This is a self-cycle:

```text
X main thread
  → send REGISTER
  → wait for local waiter DONE
  → DONE requires handleLorieEvents
  → handleLorieEvents requires this same X main thread to return to ospoll
```

The cycle is deterministic; it does not depend on GPU timing, tuple matching, or socket short reads.

### 2.4 The same defect applies to clean retirement

`gateAWaitCleanAck()` repeats the same condvar wait at `InitOutput.c:2737-2758`. It is used for renderer replies that also arrive only through `handleLorieEvents`:

- UNREGISTER_ACK
- GENERATION_CLOSED

Therefore the same-thread wait also blocks normal buffer retirement and generation close. These are RC-1b and RC-1c, not separate transport failures.

### 2.5 Runtime correlation

Frozen `88e3f17` evidence shows:

```text
17:24:02.849 Activity receives REGISTER and renderer drains it
17:24:02.850 READY_SEND_RETURN result=1
17:24:02.850 renderer GATEA_EVENT role=2 event=1 REGISTER_READY
17:24:04.849 X x-ready-timeout reason=4
17:24:04.879 Activity r-hup after X exits
```

The 1 ms renderer completion followed by an exact 2.000 s X timeout is the expected manifestation of the proven self-cycle. No X-side `role=1 event=1` can occur before timeout because the callback is not scheduled while the X thread is waiting.

## Root-cause verdict

```text
RC-X-SELF-WAIT: PROVEN BY SOURCE
RUNTIME CORRELATION: PASS
8479997 SILENT VALIDATE DROP: FALSIFIED ON 88e3f17
EGL / TUPLE / IMAGE / TEXTURE: NOT THE 88e3f17 R3 BLOCKER
SHORT PEEK: REAL SECONDARY DEFECT, NOT THE FIRST 88e3f17 BLOCKER
```

The earlier ABI review's `WAITER DEADLOCK — PASS` depended on an input-thread wake source (`GATE-A-PROTOCOL-ABI-REVIEW-R3-20260912.md:136-153`). That premise is false for the lorie DDX. The review requires an additive erratum; its frozen historical text should not be rewritten.

## 3. Secondary defects exposed by fixing the self-cycle

These defects are reachable once the X thread starts pumping the connection.

### 3.1 Demux loop skips the magic check

In `cmdentrypoint.cpp:732-739`, `again:` is below the Gate A peek. After a legacy event, `goto again` jumps directly to the legacy `read()`. A Gate A frame queued behind that event can be consumed as a 24-byte `lorieEvent` and desynchronize the stream.

### 3.2 Both sides can block after consuming one Gate frame

- X: Gate frame → unconditional `goto again` → blocking legacy read (`cmdentrypoint.cpp:733-739`).
- Activity: Gate frame → unconditional `goto again` → blocking peek (`activity.cpp:342-357`).

A bounded pump cannot delegate to code that may block waiting for the next record.

### 3.3 Gate header/body and legacy multipart records can interleave

Renderer Gate replies are currently two writes under a renderer-only mutex (`renderer.cpp:309-335`). Activity UI-thread records use separate unlocked writes, including:

- clipboard header + payload (`activity.cpp:540-545`)
- screen-size header + name (`activity.cpp:549-554`)
- wakeup event + SCM_RIGHTS byte (`activity.cpp:444-450`)
- ordinary single-record events via `sendEvent` (`activity.cpp:24`)
- GPU-copy completion from the renderer thread (`renderer.cpp:138-142`)

Locking only multipart writers is insufficient: an unlocked ordinary writer can still run between a multipart record's pieces. `writev` reduces a header/body pair to one syscall, but SOCK_STREAM does not expose record boundaries and the full-delivery helper can require more than one syscall. Correctness must come from one logical-record writer serialization contract, not an assumed atomicity property.

### 3.4 A naive pump re-enters X semantics mid-request

`handleLorieEvents()` does more than parse bytes. Some cases queue work, but others immediately call input or X helpers. Calling the entire handler from inside `PrepareComposite` can therefore perform legacy semantics in the middle of an active request. Deferring only `EVENT_STYLUS_ENABLE` is not a complete reentrancy proof.

### 3.5 A 24-byte availability check does not bound a 48-byte READY read

A proposed `FIONREAD >= sizeof(lorieEvent)` gate only proves 24 bytes are buffered. A Gate A READY is 40-byte header + 8-byte body. Entering `handleGateAFrame()` with 24–47 bytes allows its blocking `lorieGateAReadFull()` to exceed the pump quantum and potentially the end-to-end deadline.

### 3.6 Error and HUP handling must remain actionable

Treating every `poll() <= 0` or `ioctl()` failure as an empty quantum can turn `EBADF`, `EINVAL`, or other permanent errors into a misleading `x-ready-timeout`. HUP handling must not close the fd in one path and then invoke a second fatal path against already-cleared state.

## 4. Options

### Option A0 — call the existing full handler from each waiter

**Reject.** It removes the immediate self-cycle but retains blocking reads, parser label errors, incomplete-record reads, and request reentrancy. It can convert a deterministic timeout into a hang or stream corruption.

### Option A1 — bounded record-aware main-thread pump

**Recommended for the default-OFF prototype.** Keep the X main thread as the sole X-side reader, but replace sleeping X-side Gate waiters with a strict deadline loop that invokes a nonblocking, record-aware decoder.

Advantages:

- no wire/shared/queue ABI change;
- no new thread ownership model;
- PROTO OFF can remain on the current path;
- fixes READY, UNREGISTER_ACK, and GENERATION_CLOSED as one defect class;
- retains a finite 2000 ms end-to-end budget.

Cost:

- the Activity→X byte stream must gain explicit record-completeness and writer-serialization rules;
- legacy records encountered ahead of a Gate reply must be consumed without executing unsafe semantics in the active request.

### Option B — enable the xserver input thread

**Not recommended.** Calling `InputThreadPreInit()` moves all registered legacy input handling to another thread. That changes the established PROTO-OFF thread model and expands races around `conn_fd`, `registeredBuffers`, device hotplug, clipboard state, and X helpers. It requires a broader thread-safety qualification, not a narrow Gate A repair.

### Option C — asynchronous REGISTER admission

**Defer to Production design.** Returning to D0a while REGISTER remains pending avoids blocking the X thread, but changes admission and timeout semantics, requires asynchronous retirement/tombstones, and means a one-shot R3 fixture may never take the direct path.

### Option D — put READY state in shared memory

**Not recommended for this repair.** It avoids socket pumping but changes the frozen shared ABI and duplicates the control-frame state machine.

## 5. Recommended A1 contract

### 5.1 One end-to-end deadline

Each of the three X-side reply waits uses `CLOCK_MONOTONIC` and an absolute 2000 ms deadline:

1. observe sticky fatal;
2. observe waiter terminal state;
3. compute remaining budget;
4. if exhausted, re-observe fatal and waiter once, then fail with the original timeout reason;
5. invoke one bounded connection-pump quantum no longer than the remaining budget;
6. repeat.

No sleep-based retry and no timeout extension are allowed. Time spent decoding, dispatching, or waiting for bytes is part of the same 2000 ms budget.

### 5.2 Decoder result contract

The decoder returns one explicit result:

```text
PROGRESSED          one complete record consumed
INCOMPLETE          bytes exist, but not a complete record yet
WOULD_BLOCK         no bytes currently available
PEER_CLOSED         EOF / HUP
IO_ERROR(errno)     permanent read/poll/ioctl failure
PROTOCOL_FATAL      malformed active Gate frame
```

`INCOMPLETE` and `WOULD_BLOCK` return to the deadline loop. `PEER_CLOSED`, `IO_ERROR`, and `PROTOCOL_FATAL` take the existing fail-stop path immediately with distinct diagnostics; they must not age into `x-ready-timeout`.

### 5.3 Never enter a blocking read

For PROTO ON, the decoder uses nonblocking peek/receive semantics and consumes only after one complete logical record is available.

Gate A frame:

1. fewer than 4 prefix bytes → `INCOMPLETE`;
2. magic matches but fewer than 40 header bytes → `INCOMPLETE`;
3. peek and validate the entire 40-byte header;
4. reject unknown version, reserved bits, type, or invalid length using existing active-generation fatal policy;
5. calculate `40 + body_length` with overflow checking;
6. consume only when that entire byte count is present;
7. dispatch READY/FAILED/ACK/CLOSED exactly once.

Legacy record:

1. fewer than `sizeof(lorieEvent)` bytes → `INCOMPLETE`;
2. inspect the complete base event without consuming it;
3. fixed-size event requires only the base record;
4. screen-name and clipboard events require base + declared payload;
5. SCM_RIGHTS records require the base record plus the ancillary-data byte and successful fd receipt;
6. any payload limit must be derived from an existing accepted bound or separately reviewed—do not invent a silent truncation limit.

`FIONREAD` may be diagnostic input, but it is not by itself a framing API. The consumer remains nonblocking and rechecks actual receive results.

### 5.4 Gate replies execute inline; legacy semantics are deferred

While a Gate waiter is active:

- READY, REGISTER_FAILED, UNREGISTER_ACK, GENERATION_CLOSED, and valid fatal control frames update the Gate registry/waiter immediately.
- A complete legacy record located ahead of the reply is consumed into owned storage so the stream can advance.
- The record's semantic action is queued for normal X-main-loop processing after the current request returns.
- The queue item owns every copied payload and received fd until dispatch or cleanup.
- No legacy record is dropped, replayed, or semantically executed twice.
- Queue insertion failure during an active generation is fail-stop; it must not silently discard input or control state.

The implementation review must enumerate every Activity→X event type and classify it as fixed payload, variable payload, or ancillary-fd payload. A generic claim that only stylus hotplug is unsafe is insufficient.

### 5.5 Logical-record writer serialization

Within the Activity process, one mutex guards:

- `conn_fd` replacement/close identity relevant to writes;
- every Activity→X logical record, including ordinary single events;
- renderer READY/FAILED/ACK/CLOSED frames;
- renderer GPU-copy notifications;
- multipart clipboard/window records;
- event + ancillary-fd sequences.

A writer acquires the mutex once per logical record and releases it only after the full record succeeds or fails. Multipart records may use `writev`; the ancillary-fd sequence may remain multiple syscalls only while the same mutex excludes every other writer. All helper return values are checked. A partial or failed Gate control write is fatal for the active generation.

Do not hold the writer mutex while waiting for a renderer state transition, fence, Java callback, or X reply.

The implementation must explicitly resolve `conn_fd` close/replacement versus renderer-write races; checking a volatile fd before taking the mutex is not sufficient.

### 5.6 Normal callback drain

For PROTO ON, the normal notifier and the waiter pump use the same one-record decoder. The normal notifier may drain multiple already-complete records but stops on `INCOMPLETE`/`WOULD_BLOCK`; it never performs an unconditional blocking `goto again`.

For PROTO OFF, retain the current legacy path unless a separately proven shared-parser change is required. The acceptance claim is behavioral equivalence, verified by R1/T2—not merely that an `if` statement looks unchanged.

### 5.7 Fatal and lifecycle behavior

- HUP/error while generation ACTIVE: publish fatal, wake all waiters, terminate Experimental X; no normal unregister/release.
- HUP/error while inactive: preserve current legacy disconnect behavior.
- READY timeout remains reason 4.
- UNREGISTER/CLOSE errors retain their existing reason classes.
- A pump reentrancy attempt is a protocol fatal.
- Fatal teardown remains distinct from clean UNREGISTER/CLOSE.

## 6. Required RED/GREEN verification before runtime

### 6.1 Thread-model verifier

Static verifier must fail on `88e3f17` and pass after repair:

- no lorie `InputThreadPreInit()` call;
- `InputThreadRegisterDev` fallback to `SetNotifyFd` documented;
- no X-side Gate reply path uses `lorieGateAWaiterWaitUntil()`;
- all three reply waits call the bounded pump;
- timeout constants and frozen struct assertions unchanged.

### 6.2 Record decoder tests

Use host/native socketpair tests against the actual decoder/helper where possible, not a disconnected look-alike. Required cases:

- Gate prefix split after byte 1, 2, and 3;
- Gate header split at every boundary from 4 through 39;
- Gate body split from 40 through 47;
- complete READY, REGISTER_FAILED, UNREGISTER_ACK, GENERATION_CLOSED;
- legacy fixed event before Gate frame;
- Gate frame before legacy fixed event;
- two Gate frames in one wake;
- variable screen-name and clipboard records before Gate frame;
- ancillary-fd record before Gate frame;
- malformed magic/version/type/length/reserved;
- EOF after partial header and after partial body;
- POLLERR/HUP/NVAL and permanent syscall error;
- exact one registry mark and waiter signal per accepted reply;
- zero Gate-to-legacy consumption;
- no blocking beyond the supplied quantum/deadline.

### 6.3 Writer tests

At least two concurrent Activity-process writers must exercise:

- ordinary single events versus Gate frame;
- clipboard/window multipart record versus Gate frame;
- ancillary-fd record versus Gate frame;
- forced EINTR and partial-write helper behavior;
- close/rebind versus renderer reply write.

The reader must validate complete ordered records and received fds. A test that uses one `writev()` per record but does not exercise the real mutex, helper, or partial-write path is insufficient.

### 6.4 Source/build gates

After implementation authorization:

1. regression tests RED on exact `88e3f17` where applicable;
2. implementation GREEN;
3. `git diff --check`;
4. ARM64 incremental native build;
5. ARM64 full-clean native build;
6. new warnings = 0 versus a fresh `88e3f17` baseline;
7. final diff review;
8. Conventional Commits split by behavior, not telemetry convenience;
9. fork push and exact remote binding;
10. multi-ABI CI and exact workflow `headSha`;
11. APK/signer/ZIP/embedded-vs-unstripped Build ID qualification;
12. STOP before install/runtime and request a new runtime authorization.

Required command-local build environment remains:

```text
LANG=C.UTF-8
LC_ALL=C.UTF-8
LANGUAGE=C.UTF-8
ANDROID_HOME=/root/android-sdk
```

No `local.properties` is created.

## 7. Blast radius

Likely source files if A1 is authorized:

- `lorie.h`: decoder/writer contracts and declarations; frozen ABI assertions untouched.
- `cmdentrypoint.cpp`: X-side record decoder, deferred legacy queue, normal callback, bounded pump.
- `InitOutput.c`: READY and clean-ACK wait loops.
- `activity.cpp`: Activity-side logical-record writer and fd lifecycle synchronization.
- `renderer.cpp`: renderer replies and GPU-copy notifications use the same writer contract.
- `buffer.c` only if ancillary-fd send/receive helpers require checked logical-record variants; touching it needs an explicit scope update before editing.

Affected behaviors requiring requalification:

- PROTO unset and PROTO=0 startup/input/clipboard/window-change paths;
- R1 oracle/stress and the full affected T2 set;
- R2 imported rejection and clean close;
- exactly one fresh R3 on a newly qualified artifact, only under separate runtime authorization.

Not affected and not reopened:

- Stable;
- D0a closed result;
- P2-B.2 closed result;
- direct ownership order;
- GPU fence semantics;
- R4–R10;
- Production enablement.

## 8. Decisions and implementation authorization

User decisions after the design review:

1. **Deadline scope:** each individual READY / UNREGISTER_ACK / GENERATION_CLOSED waiter retains its own 2000 ms monotonic deadline. This preserves the existing per-wait contract; it does not introduce a transaction-wide shared deadline.
2. **Deferred legacy lifecycle:** during READY and UNREGISTER waits, a complete legacy record is decoded into owned storage and its semantic action is deferred until the active X request returns. During GENERATION_CLOSE, complete legacy records encountered ahead of the reply are consumed but their semantics are cancelled; payload memory is released and received FDs are closed so nothing crosses into another generation.
3. **Decoder consequence:** use an incremental nonblocking state machine for partial prefixes, headers, bodies, variable payloads, and the expected ancillary-FD byte. Activity-side callback drain must also stop instead of entering an unconditional blocking next read. No arbitrary silent payload truncation is allowed; overflow/allocation/protocol failures remain explicit and fail closed while Gate A is active.

Authorization granted:

```text
A1 RECORD-AWARE MAIN-THREAD PUMP IMPLEMENTATION: AUTHORIZED
REGRESSION TESTS: AUTHORIZED
ARM64 INCREMENTAL + FULL-CLEAN BUILD: AUTHORIZED
FORK PUSH + MULTI-ABI CI + ARTIFACT QUALIFICATION: AUTHORIZED
INSTALL / ADB / DEVICE / RUNTIME: NOT AUTHORIZED
```

Implementation remains constrained by the frozen invariants and verification matrix above. Any need to change wire/shared/queue ABI, timeout duration, ownership/fence semantics, predicate, fallback, or the lifecycle decisions in this section is a new architecture boundary and must stop for approval.

## 9. Additive erratum — normal callback drain after R5

R5 on `d9b7f60` proved that §5.6's phrase “stops on
`INCOMPLETE`/`WOULD_BLOCK`” is too broad for the incremental decoder that was
actually implemented. In that state machine, `INCOMPLETE` can mean “the
4-byte PREFIX was consumed and the decoder advanced to LEGACY_BASE while the
remaining 20 bytes are already queued”; it does not necessarily mean the
socket currently lacks bytes.

For the normal PROTO notifier, the corrected rule is:

```text
INCOMPLETE  → immediately call the nonblocking decoder again
PROGRESSED  → dispatch/release exactly once, then continue draining
WOULD_BLOCK → return to the X main loop
fatal/error → preserve the existing active fail-stop / inactive close behavior
```

Every `INCOMPLETE` return in the implemented decoder either consumed bytes or
advanced phase; the following call either progresses again or reaches
nonblocking `WOULD_BLOCK`, so this rule does not add a blocking read. Waiter
pump deadlines, deferred legacy semantics, wire/shared/queue ABI, and PROTO-OFF
behavior are unchanged. R5 correction authority:
`../p2-r5-backpressure-fix/GATE-A-P2-R5-STATIC-IMPLEMENTATION-20260915.md`.
