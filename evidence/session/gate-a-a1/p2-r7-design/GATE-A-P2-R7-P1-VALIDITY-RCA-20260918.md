# Gate A P2 R7-P1 qualification-validity RCA — 2026-09-18

Frozen device verdict remains **`R7_P1_8545B26_QUALIFICATION_INVALID`**.
This packet is source/harness RCA only. It is **not** NEXT-037 product RCA.
It does **not** retry `runtime-8545b26/r7-p1/`. It does **not** execute R7-P2.

Source bind: worktree `src/f8-ahb-gatea-r7-10-hup` HEAD **`8545b26b308aa60b05685f48560285350e22ee8d`** clean.
xserver submodule pin **`65d790bd208ec380b196eb98f144abb0b32e334d`** (Present call site read from the checked-out copy in `src/f8-ahb-gatea-r7`, same pin).

## Frozen INVALID authority

Cell `runtime-8545b26/r7-p1/` X **14331**. Classifier `NO_PRESENT_CALLBACK`. Frozen judge NOT INVOKED. Do not overwrite, delete, append a new verdict, retry in that directory, or reinterpret as FAIL/PASS.

Observed:

| Identity | seq | time | meaning |
|---|---|---|---|
| CALLBACK event30 src=1 serial=1 | 0/1 | 00:00:38.654 | CopyArea GPU copy |
| event35 enum=12 side=2 serial=1 | 2 | 00:00:38.755 | fault12 consumed |
| CALLBACK event30 src=4 serial=7 | 54 | 00:00:47.211 | target Present COPY |
| event14 serial=7 | 56 | 00:00:47.212 | GPU COMPLETED of Present |
| event36 serial=7 waited=0 | 79 | 00:00:47.218 | helper entered after done |
| fixture CompleteNotify + CLIENT_OK | — | — | Present retired normally |

## Mandatory questions

### 1. fault12 consume paths

Exactly **two** renderer sites, both on the **legacy** (`gateASeen == 0`) completion path after the EGL fence:

- `Renderer::applyPendingGpuCopies` — `renderer.cpp` after fence, `!out.gateASeen`
- `Renderer::redrawLocked` — `renderer.cpp` after fence, `!gpuCopyOut.gateASeen`

Both call `lorieGateATestFaultConsume(state, LORIE_GATEA_TEST_PRESENT_HOLD_COMPLETE, ROLE_RENDERER, lastSerial, generation)` then skip `lorieGateAPublishCompleted` and `notifyGpuCopyDone` if consumed.

Comment at `renderer.cpp` ~971 is source-proof that Present/COPY/SOLID leave `gateASeen == 0`. Present COPY is therefore on this same legacy completion path as CopyArea.

### 2. Consume predicate

`lorieGateATestFaultConsume` (`lorie.h`):

1. `lorieGateATestFaultArmed(st, cell)` — magic/version/cell match and `armed != 0`
2. if `targetGeneration != 0` and != current generation → reject
3. if `targetOrdinal != 0` and != serial → reject
4. CAS `consumed` 0→1
5. event 35

Selector + one-shot + optional target fields. **No** Present origin, **no** CALLBACK src=4, **no** `entry.op` Present vs CopyArea check.

`OsVendorInit` → `lorieGateATestFaultPublishFromEnv` sets `armed=1`, `targetGeneration=0`, `targetOrdinal=0`. Zero targets are **wildcards**. Fault12 is eligible for the first matching consume site from X start.

### 3. CopyArea vs Present queue identity

Both call `lorieTryScheduleGpuCopy` → `lorieTryScheduleGpuBlit(..., LORIE_GPU_OP_COPY)`.

`LorieGpuCopyEntry` (168 bytes frozen): `serial`, buffer ids, rects, `op` ∈ {COPY=0, SOLID=1, COMPOSITE=2}. **No xop / origin / Present bit.**

X-side telemetry distinguishes them only in CALLBACK event30 `src`:

- CopyArea: `LORIE_GATEA_XOP_COPYAREA = 1` (`lorieExaPrepareCopy` / `lorieExaCopy`)
- Present: `lorieGateATraceXCallback(4u, gpuCopySerial, ...)` in `present_execute.c` after a successful schedule

That CALLBACK lives in the **X** process. It is not written into the queue entry.

### 4. Is `entry.op` enough?

**NO.** CopyArea and Present COPY both use `LORIE_GPU_OP_COPY == 0`. Treating `op == COPY` as Present identity is a false green.

### 5. Can renderer see CALLBACK src=4?

**NO.** Renderer never getenv and never reads X CALLBACK records. It only sees queue entries + `gateATestFault` shared tail.

### 6. Fault state ownership

`struct LorieGateATestFault gateATestFault` is the Artifact B tail of `lorie_shared_server_state` (mmap, process-shared). Size 40. Independent of frozen `LorieGateAProtocol` (also 40, `generationFatal` offset 4).

X publishes from getenv in `OsVendorInit`. Renderer CAS-consumes. No other writer on 8545b26.

### 7. ARM=1 startup-only?

**YES on 8545b26.** `TERMUX_X11_GATEA_TEST_ARM=1` is read once in `lorieGateATestFaultPublishFromEnv`. There is **no** runtime re-arm API. Renderer cannot getenv.

Existing `targetGeneration` / `targetOrdinal` are already in the tail but are always stored as 0 at publish.

### 8. Safe existing target/phase fields?

**YES, in the test-fault tail (not protocol ABI):**

- `cell`, `armed`, `consumed`
- `targetGeneration`, `targetOrdinal`

Consume already honors nonzero targets. The defect is that publish never fills them and arms immediately.

### 9. Post-Present arming without shared ABI?

**YES.** Do not add protocol fields, events, counters, or queue-entry bytes.

Use existing tail: for cells 12/13 leave `armed=0` at getenv publish; at the Present schedule site, after serial assignment and **before** `writeIndex` publish, store `targetOrdinal=serial`, `targetGeneration=generation`, then `armed=1` (release after targets). One-shot CAS unchanged.

Arming only from CALLBACK after `writeIndex` is **not** fail-closed: the renderer can dequeue as soon as writeIndex is published, which is **before** `present_execute.c` traces CALLBACK.

### 10. P2 enum13 impact (assessment only; do not execute P2)

`P2_EARLY_CONSUME_RISK = YES`

`PRESENT_RENDERER_EXIT` (enum 13) consumes in `applyPendingGpuCopiesLocked` when `entry.op == LORIE_GPU_OP_COPY` at readIndex advance — **any** COPY, including bring-up CopyArea, **before** fence. Same global arming. The same Present-target arming can cover enum 13. Do **not** run P2.

## Why timing-only cannot work

Holder `p_b3a_hold` keeps `:3` `surfaceAvailable`. EXA CopyArea during map/redraw is a normal product path (`lorieExaCopy` → `lorieTryScheduleGpuCopy`). Present fixture `p_r6_d2_present` is invoked **after** X is up. There is no source invariant that zero COPY completions occur between `OsVendorInit` and the first Present CALLBACK. Device serial=1 CopyArea at 00:00:38 vs Present serial=7 at 00:00:47 is that path, not a flake.

Sleeps, WAIT_S, or “retry until Present wins” are forbidden and cannot prove emptiness of the COPY window.

## RCA verdict

**`R7_P1_VALIDITY_RCA_PROVEN`**

Root cause: fault12 is getenv-armed at X start with wildcard targets, and the only consume sites are legacy COPY completion — the same path CopyArea and Present share. The first bring-up CopyArea one-shot-consumes fault12. The later Present COPY is unprotected and completes.

Selected minimum repair (next packet / branch): **Class A+B** using existing tail fields, Present-schedule-site arm **before** writeIndex publish, CopyArea remains unarmed. No protocol ABI, timeout, judge, or R7-10 wait-wake change.

Host-qualified continuation: `GATE-A-P2-R7-P1-VALIDITY-SUPPORT-20260918.md`
(`R7_P1_VALIDITY_SUPPORT_HOST_QUALIFIED`; uncommitted; NOT BUILT).

## Device mutation

This RCA: ADB install=0, X3=0, Activity=0, Present fixture=0, fault12 device=0, R7-P2=0, Stable=0, HDMI=0.
