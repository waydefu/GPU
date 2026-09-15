# Gate A P2 runtime qualification design review — 2026-09-13

## Scope and authority

This is a DESIGN / SOURCE REVIEW ONLY against:

```text
D0a  a6cc7952861b8a63740d42bf78553573cfa0eec0  CLOSED PASS
P0   97401bce514fa7d43be80df271e163669f849746  QUALIFIED
P1   5e9eb2a6f2a05a0c8d50c49727519b61b2477302  QUALIFIED
P2   82a87f4a99ae4b1d4e09d6c74a735cd40b6e73e2  STATIC/CI/ARTIFACT PASS
CI   34716168485
APK  f9fce1b35bc9b7760061f6b225c916118efb2441b69609ab8146aecb8028adba
ELF  6a69205c9211ad115ed58f5ac7193ac08e628023
```

No install, ADB, device connection, runtime, APK execution, Stable/`:1`, HDMI,
source mutation, build, or CI was performed. Both source worktrees were clean and
`git diff --check` passed before and after read-only review.

## Executive verdict

```text
OBSERVABILITY: BLOCKED
RUNTIME PLAN ON CURRENT 82a87f4 ARTIFACT: BLOCKED
P2 RUNTIME EXECUTION: NOT AUTHORIZED
Production Gate A: BLOCKED
```

The current artifact cannot safely reach R3. This is not only an
instrumentation deficit: source review found three P2 execution defects plus the
already-known missing normal lifecycle.

### B1 — direct queue entry never becomes consumed (CRITICAL)

`Renderer::applyPendingGpuCopiesLocked()` enters the Gate A branch at
`renderer.cpp:1267-1277`, but `out.lastSerial = entry.serial` and the release
store to `readIndex` are inside the legacy `else` at `renderer.cpp:1413-1417`.
There is no other assignment/publication for a direct entry. The drain loop will
therefore re-read and re-draw the same slot without advancing; no finite fence or
`completedSerial` terminal can be reached.

Required correction before any runtime: make slot-consumption bookkeeping common
to a successfully submitted direct entry and a legacy entry, while preserving
"readIndex = slot copied/consumed only" and never advancing it after a fatal.
This is a narrow functional fix, not instrumentation.

### B2 — source READY miss/tuple loss routes to legacy CPU upload (CRITICAL)

Gate A identity is inferred from a successful source lookup:

```text
renderer.cpp:1267-1268
flag && op==COMPOSITE && gateAIsReady(srcId) → direct
else                                           → legacy
```

If the source READY entry is missing, stale, or tuple-mismatched after X has
published a direct transaction, execution enters the legacy branch, including
`findBufferWithRetry()` and `LorieBuffer_bindTexture()` at
`renderer.cpp:1284-1288,1353-1357`. It may consume and publish the serial as
legacy success. That violates the required READY-miss failure cell and the
frozen rule "no legacy CPU-upload fallback from a published Gate A entry."

Required correction before runtime: carry an unambiguous direct-entry identity
without relying on lookup success. The queue entry byte size may remain 168
bytes, but any field/tag or out-of-band serial table chosen to identify Gate A
is an architecture decision and must be reviewed before implementation. A
missing source or destination READY lookup for an identified direct entry must
be FATAL, never legacy.

### B3 — reverse cross-operation admission is not closed after first use (HIGH)

The implementation blocks COPY/SOLID/Present scheduling only while a Gate A
pair lease is currently active (`InitOutput.c:1709-1712,1877-1879`). The first
Gate A submit requires global queue quiescence, but only under `!gateAUsed`
(`InitOutput.c:2542-2550`). Later direct admissions do not reject an older
legacy Present/COPY/SOLID operation on the same endpoints. X registry
`pendingCount` and `lastSubmittedSerial` are initialized/checked but never
updated (`cmdentrypoint.cpp:107-116,194-205`). A Present OOM/scrap path can drop
its pending reference before `completedSerial` proves quiescence
(`present_execute.c:100-108,133-135`; `present_vblank.c:191-215`).

Required correction before runtime: either conservatively require global queue
quiescence before every direct pair reserve, or fully wire per-buffer
`lastSubmittedSerial`/pending terminal admission. For this prototype, the
always-global check is the smaller, safer boundary; it may reduce admission but
does not expand semantics.

### B4 — normal unregister/generation cleanup is absent (known HIGH)

Renderer READY imports retain AHB/EGLImage/texture until future UNREGISTER
(`renderer.cpp:350-393`). `DestroyPixmap` sends only the legacy remove event
(`InitOutput.c:3065-3077`), and `CloseScreen` poisons a used generation instead
of draining it (`InitOutput.c:1149-1164`). Reusing an ID in the same generation
can encounter stale READY state; renderer registry count cannot return to
baseline during a clean in-process lifecycle. Therefore R8 clean Destroy/Close,
R9 clean stale-rejection, and R10 registry/ref balance cannot pass on 82a87f4.

Required correction is a separately reviewed lifecycle phase: terminal wait,
UNREGISTER/ACK, GL-thread texture→EGLImage→AHB cleanup, and generation
CLOSE/CLOSED drain. Instrumentation cannot turn the current fail-stop placeholder
into a clean lifecycle.

## Current observability audit

| Required invariant | Current direct evidence | Verdict |
|---|---|---|
| generation/session bind | shared values exist; no successful bind event | BLOCKED |
| REGISTER sent/received tuple | no success event | BLOCKED |
| READY inserted/received tuple | only send failure/duplicate logs | BLOCKED |
| imported rejection reason | plain `return FALSE`; no reason/counter | BLOCKED |
| lease NONE→RESERVED→GPU_OWNED→NONE | assignments only; no event/counter | BLOCKED |
| source/destination checked unlock success | only fatal-on-error; no success result | BLOCKED |
| direct serial publish | no direct trace; direct telemetryIndex is INVALID | BLOCKED |
| renderer consumes same serial | no direct trace; B1 prevents consumption | BLOCKED |
| direct lookup success/failure | return code only; source miss misclassifies via B2 | BLOCKED |
| no legacy upload from direct | no direct identity/counter; B2 makes fallback reachable | BLOCKED |
| finite fence create/wait/satisfied/elapsed | source has 2 s bound; only failure fatal logged | BLOCKED |
| completedSerial/firstFailed/fatal tuple | shared atomics exist; no terminal snapshot output | BLOCKED |
| semantic SUCCESS | derived internally; no correlated event | BLOCKED |
| repair ordering/count | existing B3a record not attached to direct entry | BLOCKED |
| ACK/pending decrement | no correlated event/counter | BLOCKED |
| relock source/destination success | only fatal-on-error; no success event | BLOCKED |
| fatal halt | `GATEA_FATAL_HALT what/reason` is logged | PARTIAL PASS |
| renderer/X registry cleanup | no counts; normal cleanup absent | BLOCKED |
| AHB acquire/release balance | no logical ref counters | BLOCKED |

The existing 1514 oracle proves pixels, not these ownership events. Existing
B3a telemetry is staging/reference-path telemetry; P2 direct entries set
`telemetryIndex = LORIE_B3A_INVALID_INDEX` (`InitOutput.c:2689`). Timing and
absence of a crash cannot fill these gaps.

## Required instrumentation-only patch (after B1–B3 are fixed)

Use a second exact-default-off flag, e.g. `TERMUX_X11_GATEA_TRACE=1`. When not
exactly `1`, it must add no I/O, allocation, wait, or branch affecting Gate A
semantics.

Append a versioned diagnostic area to the end of the shared server state; do not
move or change P0 protocol/result fields or the 168-byte queue entry. The area
must contain:

1. atomic sequence and bounded event ring for one-transaction order proof;
2. non-wrapping counters and first-violation bitmask for long runs;
3. last tuple/source/destination/serial and the latest atomic result snapshot;
4. X and renderer registry current/high-water counts;
5. renderer AHB acquired/released, EGLImage created/destroyed, texture
   created/deleted counters;
6. per-endpoint pending increment/decrement and CPU lock/unlock counters;
7. direct-admit rejects by exact reason, including imported source/destination;
8. direct publish/consume/lookup/draw/fence/completed/SUCCESS counts;
9. `direct_to_legacy` and `legacy_cpu_upload_for_direct` violation counters;
10. repair, ACK, relock, lease-transition, conflict-reject, fatal and cleanup
    counters.

Every event must carry role, sequence, event code, nonce, generation, source ID,
destination ID, serial, lease state, write/read/completed, firstFailed/code,
fatal, and endpoint pending/CPU-lock state. It must not log pixel contents or
secrets.

Required events:

```text
GENERATION_INIT / RENDERER_BIND
REGISTER_SEND / REGISTER_RECV
READY_INSERT / READY_SEND / READY_MARK
ADMIT_REJECT(reason) / LEASE_RESERVED
UNLOCK_SRC(rc) / UNLOCK_DST(rc) / LEASE_GPU_OWNED
PUBLISH / CONSUME_DIRECT / LOOKUP_DIRECT
DRAW_SUBMIT / FENCE_CREATE / FENCE_RESULT(elapsed,bound)
COMPLETED_PUBLISH / TERMINAL_RESULT
RELOCK_SRC / RELOCK_DST / LEASE_NONE
REPAIR / ACK / PENDING_DEC
CONFLICT_REJECT / UNREGISTER / UNREGISTER_ACK
GENERATION_CLOSE / GENERATION_CLOSED
FATAL_SNAPSHOT / SUMMARY
```

The trace writer must release-publish complete records. A verifier, not a human
reading logcat, must reject missing/duplicate/out-of-order records, counter
mismatch, ring overflow in R3, direct-to-legacy count nonzero, or a terminal
summary missing after clean exit. Long R4/R5 runs use counters plus an online
violation bitmask; the event ring may wrap but counters may not.

Before every `_exit(127)`, emit a best-effort shared `FATAL_SNAPSHOT`; on HUP the
X side dumps the shared snapshot before halting. Clean CloseScreen writes a
machine-readable JSON summary to a fresh path. Logcat is corroboration, not the
sole authority.

Instrumentation alone is insufficient until B1–B4 are resolved.

## Deterministic test controls and fixtures

Current source has no Gate A fault-injection controls. Add a separately reviewed,
exact-default-off, one-shot Experimental-only control, for example:

```text
TERMUX_X11_GATEA_TEST_FAULT=<one exact cell>
TERMUX_X11_GATEA_TEST_ARM=1
```

A cell may fire once; a second arm or unknown value must refuse startup. Every
fault session is fresh and no poisoned generation is retried. Controls are not
enabled in ordinary/off-equivalence runs.

Required deterministic cells:

```text
source READY miss after publish
destination READY miss after publish
tuple mismatch
FBO incomplete before draw
post-submit GL failure (FAILED_QUIESCED path)
fence creation failure
fence timeout result
renderer fatal before completion
wrong generation frame
renderer loss after PUBLISH marker
serial seed near UINT64_MAX (wrap containment)
mid-pending Destroy / Close
```

Required reproducible clients and reusable sources:

- corrected 1514 oracle: `patches/p_b2_oracle.c` (includes exact RGB/X-byte
  checks and five software negative controls; compile recipe at lines 1-6);
- one direct transaction: reuse `patches/p_b3a_cost.c` with
  `warmup=0,count=1,batch=1,cold=1,mode=1`; P2 instrumentation supplies the
  ownership/serial evidence that this client currently lacks;
- same-AHB cycles: reuse `patches/p_b3a_cost.c` with `reuse=1`, but qualify via
  new P2 direct counters rather than historical staging evidence;
- Present baseline: `patches/p_present.c` supplies CompleteNotify, pixels and
  window-destroy behavior; it needs an added cross-operation/OOM driver cell;
- holder/recreate: `patches/p_b3a_hold.c` and
  `evidence/session/p2-b3a/t2-u4-l1-lifecycle/p2b3a_session.sh`;
- FD/mmap process-level resource baseline: `patches/p_tiny_pixmap.c`;
- `imported-ahb`: new DRI3 PixmapFromBuffers fixture through the existing AHB
  socket modifier 1255, with separate imported-source/destination cells;
- `cross-op`: added Present/COPY/SOLID/PrepareAccess/CPU fallback ordering
  cells, including deterministic Present requeue OOM/scrap;
- `lifecycle`: added direct clean destroy/close and injected pending
  destroy/close cells.

The reusable sources still need their exact compiled executable SHA pinned per
runtime session. Historical `p_b3a_cost`/lifecycle results exercised the
staging/reference path and are fixtures only, never P2 direct evidence.

## Strict runtime gates

No gate starts unless every earlier gate passed. Each command is issued one at a
time and checked before the next. Every session targets only
`com.waydefu.x11gpu`, `:3`, Android display 0. Stable is read-only observed and
never signaled/configured; HDMI is not queried or touched beyond confirming the
activity is on display 0.

### R0 — artifact/environment admission

Before install/launch under a future explicit execution authorization:

1. verify host artifact SHA256, package, versionCode 15, versionName
   `1.03.01-82a87f4`, arm64 member and embedded Build ID;
2. verify the only connected target is the authorized F8 Ultra serial/model;
3. verify Stable `com.termux.x11 :1 -legacy-drawing` has one live PID and record
   it without modifying it;
4. require no `com.waydefu.x11gpu :3` process/socket residue;
5. install only the experimental package when separately authorized, then read
   back package/version and installed APK/ELF identity;
6. start only with `--display 0`; read back `display=0`, RESUMED and drawn.

Any mismatch, multiple devices, existing `:3`, display mismatch, or inability to
prove artifact identity is STOP. Because B1–B4 require a new commit/artifact,
82a87f4 cannot be the eventual runtime artifact; repeat full source/CI/artifact
binding on the corrected instrumented commit.

### R1 — flag-off equivalence

Fresh session with Gate A flag absent, then a second fresh session with exact
`0`; trace may be enabled but must report Gate A inactive and every direct
counter zero. Run the corrected 1514 oracle and existing R3 negative controls,
then the frozen x100/mixed100/x1000 stress from `TEST-MATRIX.md`. Require exact
pixels, fail=0, maxDelta=0, Xnz=0, no fatal signal, clean teardown and
`NO_X3_RESIDUE`. Any Gate A REGISTER/lease/publish event or baseline regression
stops all ON work.

### R2 — imported rejection

Use real AHB imports, not the raw-FD export test and not the `dst-argb` format
negative control. Run two pre-publish cells in a fresh session:

1. imported BGRA source + server-owned RGBX destination;
2. server-owned BGRA source + imported RGBX destination.

Each must emit `ADMIT_REJECT(imported-source|imported-destination)`, zero
REGISTER/READY/direct lease/publish, and exact pixels through the existing safe
path. Any Gate A registration or publish is STOP.

### R3 — single direct transaction

Fresh minimal session, no XFCE/compositor, holder plus `single-direct` client.
Require exactly one admitted pair and one serial S. The machine verifier requires:

```text
READY(src tuple) + READY(dst tuple)
NONE → RESERVED
unlock src rc=0; unlock dst rc=0; both CPU pointers invalidated
RESERVED → GPU_OWNED
PUBLISH(S) → CONSUME_DIRECT(S) → LOOKUP_DIRECT(src,dst)
no direct_to_legacy; no legacy CPU upload
DRAW_SUBMIT(S)
finite fence create + CONDITION_SATISFIED within 2,000 ms
completedSerial >= S; firstFailedSerial=0; generationFatal=0
TERMINAL_RESULT(SUCCESS)
then and only then relock src/dst → lease NONE → repair → ACK/pending--
```

Pixel output must be exact with fail=0, maxDelta=0 and Xnz=0. Missing evidence,
extra direct serial, trace overflow or any wrong order means R3 NOT QUALIFIED and
blocks R4+.

### R4 — corrected 1514 production oracle

One fresh session after R3. Run the pinned corrected 1514-case production-path
oracle. Require 1514/1514 exact, fail=0, maxDelta=0, Xnz=0; negative predicates
remain software. Let N be the observed direct-admitted entry count. Require:

```text
publish=N=consume=lookup=draw=fence-satisfied=completed=SUCCESS=ACK
all admitted serials terminal; monotonic serial/completed
firstFailed=0; fatal=0; direct_to_legacy=0; legacy-upload-for-direct=0
pending and lease return to baseline; violation mask=0
```

A correct screen with any counter/terminal mismatch is FAIL, not PASS.

### R5 — same-AHB ownership cycles

Fresh session. Reuse exactly one source/destination pair. Run gated checkpoints
1, 16, 64, 256, 1024 and 4096 cycles; stop at the first failed checkpoint. Each
cycle writes a deterministic changing CPU pattern, direct-composites, reads exact
pixels, then writes the next pattern through the relocked mapping. Require per
cycle lease NONE at boundaries, pending baseline, completedSerial monotonic,
unique serial, no CPU/GPU overlap, no stale mapping/texture and exact pixels.

4096 cycles exercise queue-ring wrap and leak accumulation; natural u64 serial
rollover is infeasible. Exercise wrap only in the separate near-UINT64_MAX
one-shot fault cell, which must halt before publishing serial zero and must not
release ambiguous ownership.

### R6 — cross-operation ownership

This gate is source-blocked by B3 until symmetric prior-work admission exists.
After correction, use two directions:

1. while renderer completion is delayed below the 2 s bound, submit conflicting
   Present/COPY/SOLID/PrepareAccess/CPU work from a second client; X's single
   server thread must leave those requests queued until the direct terminal and
   their callbacks must have no timestamp/event before SUCCESS;
2. schedule legacy Present/COPY/SOLID first, including forced Present requeue
   OOM and scrap/early-ACK, then request direct work on the same endpoints;
   direct admission must reject as prior work nonterminal and may admit only in a
   later transaction after completedSerial proves quiescence.

Require no early ACK, destination access, source relock, ownership steal or
false completion. Test fixture events must distinguish "request arrived" from
"X callback executed"; timing alone is not proof.

### R7 — failure injection

One fresh Experimental session, one armed fault, one attempt, no retry. Required
cells: source READY miss, destination READY miss/tuple mismatch, FBO incomplete,
post-submit GL error, fence create failure, finite fence timeout, renderer fatal
before completion, generation mismatch, renderer loss after publish, and serial
wrap containment.

For every post-publish cell, require the final snapshot to show sticky first
failure and/or fatal, waiter wake/connection termination, and zero repair, ACK,
pending decrement, relock, normal lease release, D0a fallback and replay after
the injected boundary. The generation/session must terminate and final process
scan must reach `NO_X3_RESIDUE`. Any cell that continues normally is P2 FAIL.

### R8 — destroy/close lifecycle

This gate is source-blocked by B4. After UNREGISTER and generation-close
lifecycle is implemented and separately qualified, run four fresh cells:

1. successful direct work, then DestroyPixmap source/destination;
2. successful direct work, then clean CloseScreen;
3. injected DestroyPixmap while work is pending;
4. injected CloseScreen while work is pending.

Clean cells require terminal wait, UNREGISTER/ACK or GENERATION_CLOSE/CLOSED,
GL-thread reverse destruction and registry/ref counts returning to baseline.
Pending cells require fatal poisoned termination with no normal release. All
cells require no UAF, premature AHB release, stuck waiter, stale lease,
cross-generation READY or renderer registry leak.

### R9 — recreate

After clean lifecycle exists, run three clean create/use/destroy rounds with
fresh X PID and nonce each round. Generation may restart at 1 in a fresh process,
so nonce+generation is the identity; all nonce values must differ. In separate
one-fault sessions, replay an old READY/tuple against the new session and require
deterministic rejection/fatal, then start another fresh session and prove normal
registration succeeds. Old registry count must be zero before fresh admission.

### R10 — resource residue

For every clean lifecycle round snapshot X and renderer FD counts, logical AHB
acquire/release balance, X/renderer registry current counts, EGLImage/texture
create/destroy balance, pending counts, lease count, process/socket/`:3` residue.
Run at least five clean recreate rounds after R9. Require all logical live counts
zero at teardown, no monotonic FD growth at equivalent checkpoints and
`NO_X3_RESIDUE` after every round. RSS may be recorded but is not a substitute
for ownership/ref accounting and no performance claim is made.

## Global stop conditions

Stop the current session and do not start a later gate on any:

```text
artifact/device/display/provenance mismatch
missing/overflowed correctness trace
pixel mismatch or nonzero maxDelta/Xnz
false SUCCESS or semantic/result counter mismatch
completedSerial advance without a satisfied finite fence
lookup miss or tuple loss entering legacy
finite-fence timeout followed by ownership release
repair/ACK/pending--/relock before SUCCESS
CPU mapping live while GPU owns the pair
pair lease stuck or pending/resource count not at expected baseline
generationFatal with continued same-generation work
renderer loss with continued same-generation X work
unexpected SIGSEGV/SIGILL/SIGABRT or exit code
Stable PID/cmdline/display change
activity not on Android display 0 or any HDMI interaction
```

If the historical batch16 SIGSEGV signature occurs in any new session, record it
as a NEW OBSERVATION with current PID/time/artifact/log evidence and stop. Do not
merge it into the historical observation or retry the poisoned generation.

## Decision

The staged R0–R10 shape is suitable only after the source blockers and
observability prerequisites above are resolved. Current exact artifact 82a87f4
must not be installed or Gate A-enabled for runtime: its first direct entry has a
source-proven queue non-progress defect, and lookup-miss containment is not
representable reliably. A future corrected commit requires ARM64 compile,
full multi-ABI CI, artifact/provenance qualification, and a new explicit runtime
authorization before R0.
