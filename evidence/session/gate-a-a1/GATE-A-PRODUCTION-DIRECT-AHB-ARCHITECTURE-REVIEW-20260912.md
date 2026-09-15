# Gate A production direct-live-AHB ownership architecture review — 2026-09-12

## Conclusion

```text
A1 BGRA byte/import/shader-sampling capability on this exact F8 stack: PASS
Production direct live-AHB on current a6cc795 ownership contract: NOT SAFE / BLOCKED
Feasible in principle for server-owned, non-imported AHB: YES, with a new
  import-ready + per-serial result/replay + generation/lifecycle protocol
Feasible as a staging-removal-only patch: NO
Imported/client-owned AHB direct sampling: BLOCKED pending an external acquire-fence contract
Production Gate A: BLOCKED
D0a: CLOSED / UNCHANGED
D0b: BLOCKED / UNCHANGED
Gate H: HOLD
```

A1 removed the byte-format uncertainty: project-defined BGRA value 5 sampled
exactly through AHardwareBuffer → EGLImage → sampler2D on the POCO F8 Ultra.
It did **not** establish repeated live-buffer ownership, registration readiness,
post-publication failure recovery, teardown, or imported-client synchronization.
The current production path cannot add direct sampling safely by only bypassing
FD staging.

## Authority and scope

- Source reviewed: `/root/projects/GPU加速/src/f8-ahb`, branch
  `qualification/d0a-narrow-20260912`, HEAD
  `a6cc7952861b8a63740d42bf78553573cfa0eec0`, clean; `git diff --check` PASS.
- Runtime capability evidence: A1 marker commit `4196798`, CI run
  `34694695463`, exact 9/9 (`CONTROL/BGRA/RGBA` each 3/3
  `SHADER_SAMPLE_EXACT`), `state_restore_error=0`, no fatal signal.
  See `marker/GATE-A-A1-MARKER-EXECUTION-20260912.md`.
- API authority: local NDK `29.0.14206865` (`source.properties`) and its
  `android/hardware_buffer.h`; Android NDK r29 official release history checked.
- Read-only review: no source edit, build, ADB/device/package/process operation,
  Stable operation, HDMI operation, or production prototype.

## What A1 proves—and does not prove

### Proven on this device/build

- Exact bytes for BGRA value 5 survive CPU write → synchronous unlock →
  EGLClientBuffer/EGLImage → texture sampling → RGBA FBO/readback.
- RGBX control and RGBA diagnostic are valid; BGRA is neither black nor
  channel-swapped in the isolated pipeline.
- Format value 5 remains a project/HAL alias, not an NDK public enum
  (`buffer.h:12`); qualification is target/build specific, not portable.

### Not proven by A1

- Reusing one live AHB across repeated X CPU and renderer GPU ownership cycles.
- Renderer import readiness before queue consumption.
- Correct behavior on allocation, lock/unlock, socket transfer, EGLImage,
  texture, FBO, draw, or fence failure.
- Imported DRI3 producer fences, resize, CloseScreen, disconnect, context loss,
  or generation reuse.

## Current production transaction

```text
X REGULAR pixmap
  → lorieEnsureGpuSampleable converts to BGRA AHB
  → X leaves AHB CPU-locked in priv->locked
  → PrepareComposite clones live bytes to FD staging
  → lorieTryScheduleGpuBlit registers/acquires/pending++ and publishes ID+rect
  → renderer receives/registers buffer asynchronously
  → findBufferWithRetry attaches texture
  → renderer uploads FD staging, blends into destination AHB FBO
  → EGL fence create → glFlush → EGL_FOREVER wait
  → completedSerial publication
  → X DoneComposite wait → pending--/release
  → later CPU access locks destination/source as needed
```

Evidence: `InitOutput.c:200-235,1523-1578,1581-1701,2145-2207,2270-2388`;
`renderer.cpp:745-967`; `buffer.c:635-673`.

A staging-removal-only Gate A change would replace the FD source at
`InitOutput.c:1618-1621` with the live AHB, but all ownership and failure gaps
below would remain.

## Required safe ownership state machine

A safe design has one legal owner/access domain at a time. Reference lifetime
and memory-access ownership are separate facts.

| State | X / producer | Renderer / GPU | Required transition proof |
|---|---|---|---|
| `X_CPU_OWNED` | AHB lock succeeded; CPU pointer usable | no sample/write | no GPU pending for this generation |
| `CPU_RELEASE` | finish all writes; call `AHardwareBuffer_unlock(buf, NULL)` | no access | return **0**; with NULL fence this is a synchronous cache/content handoff |
| `IMPORT_READY` | no CPU pointer use | renderer owns received AHB ref; EGLClientBuffer, EGLImage and texture validated on GL thread | explicit `READY(id,generation)` result, not a timing delay |
| `QUEUED` | local pixmap ref + per-entry ref + pending count held | no consumption before full publication | release-store `writeIndex`; acquire-load before copying entry |
| `GPU_IN_FLIGHT` | may not relock, write, unregister, or free | validated source texture/destination FBO; draw submitted | entry remains owned until terminal result |
| `GPU_SUCCESS` | still blocked | fence created, flushed, wait satisfied; GL/FBO/draw status successful | release-publish `SUCCESS(serial,generation)` |
| `GPU_FAILED_QUIESCED` | still blocked | failure recorded and all possibly submitted GPU work proven quiescent | release-publish failure status; CPU replay is now safe |
| `X_REACQUIRE` | acquire-load terminal status; then pending--/release; lock with fence `-1` only after success/quiescence | no use | status distinguishes success from failure |
| `RETIRING` | reject new work; retain owner refs | drain/terminalize entries; destroy GL texture then EGLImage on GL thread | renderer unregister acknowledgment |
| `DEAD` | release AHB/pixmap/state | no old-generation callback/queue access | generation/epoch invalidates stale IDs and shared state |

The local NDK contract is decisive here:

- `AHardwareBuffer_unlock(..., NULL)` blocks until work/content update completes
  (`hardware_buffer.h:508-518`), so a successful synchronous unlock is a valid
  CPU→GPU handoff; a native fence FD is optional, not mandatory.
- `AHardwareBuffer_lock(..., fence=-1)` makes the caller responsible for proving
  prior writes complete (`hardware_buffer.h:462-466`). Therefore X may not
  relock from timeout or connection-loss alone.
- AHardwareBuffer reference ownership only prevents deletion
  (`hardware_buffer.h:425-440`); it does not authorize simultaneous CPU/GPU
  access.

## Ownership ledger

| Resource | Creation / owner | Transfer / consumer | Correct release | Current status |
|---|---|---|---|---|
| X pixmap + `LoriePixmapPriv` | X `lorieCreatePixmap`; pixmap owns wrapper | per-entry X wrapper ref at scheduling | after terminal result/pending=0 | happy path mostly present; timeout clears early |
| AHardwareBuffer (X side) | allocate/promote; wrapper owns allocation ref | handle sent over AF_UNIX | after no CPU/GPU use and unregister completion | no import-ready acknowledgment; unlock errors not stateful |
| AHardwareBuffer (renderer side) | receive creates process-local ref | EGLClientBuffer/EGLImage/texture | after texture delete + image destroy on GL thread | normal removed-buffer path is ordered; failure/teardown quiescence incomplete |
| CPU mapping | `LorieBuffer_lock`; `priv->locked` | never transferable | successful AHB unlock before publish | Composite currently leaves it locked; direct path has no transition |
| EGLClientBuffer/EGLImage | renderer GL thread | texture binding | image destroyed before receiver AHB release | happy-path ordering exists in `__LorieBuffer_free`; creation success not reported |
| GL texture / destination FBO | renderer GL thread | draw | delete on current GL thread after last fence | add/remove lists support happy path; attach/FBO/draw failures unclassified |
| Queue entry | X producer | renderer consumer | only after terminal result | renderer advances `readIndex` even when source/destination missing |
| EGL fence | renderer after commands | renderer CPU wait | destroy after satisfied/failed wait | happy success path correct; failure loses drained entries |
| `completedSerial` | renderer | X wait loop | monotonic generation-bound terminal success | no failure status; volatile only, no formal release/acquire edge |
| Shared state / mutex | X mmap | renderer mmap | quiesce consumer, then unmap/reset generation | CloseScreen has no queue drain/generation barrier |

## Current invariant assessment

| Invariant | Classification | Evidence |
|---|---|---|
| Exact BGRA direct sampling on target | **PROVEN** | A1 3/3 exact; aggregate 9/9 |
| CPU mapping ended before direct Composite sampling | **CONTRADICTED** | promotion locks `priv->locked` (`InitOutput.c:225-230`); PrepareComposite clones while lock remains (`2167-2169`); no Composite unlock |
| Successful CPU→GPU cache handoff checked | **MISSING** | `LorieBuffer_unlock` returns status but clears lock state regardless (`buffer.c:459-483`); existing BGRA unlock helper ignores it |
| Renderer import is ready before queue entry | **MISSING** | socket write/send results ignored (`cmdentrypoint.cpp:468-479`); renderer uses bounded 100 ms retry (`renderer.cpp:745-767`) |
| EGLImage/texture/FBO/draw success reaches X | **MISSING** | `LorieBuffer_attachToGL` and bind are void/no terminal status (`buffer.c:635-673`); missing buffers are skipped (`renderer.cpp:794-799`) |
| Queue consumption means operation succeeded | **CONTRADICTED** | `readIndex++` and `lastSerial` occur even after skipped/no-draw entry (`renderer.cpp:794-799,917-918`) |
| GPU→X completion on happy path | **PROVEN** | fence create, flush, FOREVER wait, then completed serial (`renderer.cpp:943-965`) |
| Failure/timeout keeps ownership | **CONTRADICTED** | DoneComposite logs false wait then repairs/acks/releases (`InitOutput.c:2353-2375`); CPU fallback paths also ignore failed waits (`2306-2310,2341-2343`) |
| CPU access cannot begin before AHB unlock completes | **CONTRADICTED** | FinishAccess releases shared mutex before `LorieBuffer_unlock` (`InitOutput.c:2519-2527`) |
| Cross-process queue publication has formal acquire/release | **MISSING** | producer barrier + volatile index (`InitOutput.c:1687-1693`); consumer copies entry after volatile reads without acquire (`renderer.cpp:776-782`); completion is also volatile-only (`lorie.h:203-213`, `InitOutput.c:1704-1705`) |
| Imported AHB has producer acquire fence | **MISSING** | imported AHB is marked `imported` (`InitOutput.c:2567`), but Composite admission does not exclude it (`2101-2121`) and queue has no acquire-fence field |
| Destroy/recreate waits for terminal entries | **MISSING** | DestroyPixmap unregisters immediately (`InitOutput.c:2470-2477`); CloseScreen destroys root without renderer drain (`1080-1096`) |
| Disconnect cannot split mutex ownership | **CONTRADICTED** | shared mutex may be reinitialized from connection state rather than proven owner death (`lorie.h:52-85`) |

## Decisive findings

### F1 — Post-publication failure has no correct terminal result

- **Severity:** HIGH; **Confidence:** HIGH.
- **Evidence:** asynchronous registration has no acknowledgment; attach/draw calls
  do not return a transaction result; missing buffers are skipped; `readIndex`
  still advances; a later fence can publish `completedSerial` for an operation
  that never drew (`renderer.cpp:745-767,781-799,917-965`).
- **Failure mode:** X sees completion, releases ownership and reports a Composite
  that may have left destination unchanged/stale.
- **Required proof/fix:** renderer→X `READY` plus per-serial
  `SUCCESS / FAILED_NOT_SUBMITTED / FAILED_QUIESCED / FATAL` status and
  same-transaction CPU replay after quiescence.

### F2 — Current CPU/GPU handoff permits overlap or false release

- **Severity:** HIGH; **Confidence:** HIGH.
- **Evidence:** Composite source remains CPU-locked; unlock status is not tied to
  ownership state; FinishAccess exposes the shared mutex before ending AHB CPU
  access; timeout clears pending refs (`InitOutput.c:225-230,2353-2375,2519-2527`;
  `buffer.c:459-483`).
- **Failure mode:** renderer samples while CPU access remains active, or X relocks
  and writes while GPU may still read. On AHB lock with `fence=-1`, that violates
  the caller's synchronization responsibility.
- **Required proof/fix:** checked synchronous unlock before publish; pending stays
  set until an acquire-observed terminal result; AHB unlock occurs before shared
  mutex release.

### F3 — Imported/client-owned AHB would be silently admitted without an acquire fence

- **Severity:** HIGH; **Confidence:** HIGH.
- **Evidence:** AHardwareBuffer DRI3 imports set `priv->imported=true`; current
  narrow Composite admission does not reject imported buffers. Staging currently
  fails closed because imported AHB has no `priv->locked`; removing staging would
  remove that accidental exclusion (`InitOutput.c:1532-1537,2101-2121,2567`).
- **Failure mode:** GPU samples while an external producer still writes, with no
  fence carried in `LorieGpuCopyEntry`.
- **Required proof/fix:** first production prototype must explicitly reject
  `priv->imported`, or separately add and qualify DRI3/Present acquire/idle-fence
  ownership. The latter is a separate architecture phase.

### F4 — Completion publication is not a full lifecycle protocol

- **Severity:** HIGH; **Confidence:** HIGH for the gap.
- **Evidence:** a satisfied EGL fence correctly proves commands completed, but
  `completedSerial` has no result or generation; timeout still releases; pixmap
  destroy and CloseScreen do not wait for a renderer unregister/drain acknowledgment
  (`renderer.cpp:943-965`; `InitOutput.c:2353-2375,2470-2477,1080-1096`).
- **Failure mode:** old IDs/AHB/EGLImage/texture/shared state may be retired while
  an entry is unresolved or later consumed.
- **Required proof/fix:** generation-bound drain, terminal result, unregister ack,
  GL-thread destruction, then AHB/state release.

### F5 — Shared-memory queue ordering is operationally tested but not formally synchronized

- **Severity:** HIGH; **Confidence:** HIGH that the formal edge is absent; MEDIUM
  for manifestation on this ARM64 build.
- **Evidence:** one producer-side full barrier precedes a volatile `writeIndex`;
  consumer and X completion waiter use volatile loads/stores without matching
  acquire/release atomics (`InitOutput.c:1687-1693,1704-1705`;
  `renderer.cpp:776-782,963`; `lorie.h:203-213`).
- **Failure mode:** stale/partially observed entry or completion state under the C
  memory model; successful stress does not prove the missing happens-before edge.
- **Required proof/fix:** explicit release-store/acquire-load for publish,
  consume, and terminal result; retain ABI only if alignment/type constraints are
  demonstrated.

## Why existing successes are insufficient

- A1 proves capability and exact channels, not a long-lived owner transition.
- P2-B.2/D0a exact oracles prove tested happy paths, not import failure, fence
  failure, timeout, disconnect, context loss, or CloseScreen overlap.
- Existing EXA Copy is not an ownership proof: its BGRA helper ignores unlock
  status, and DoneCopy also acknowledges after a false wait.
- Reference counts prove object lifetime only; they do not prove cache visibility
  or exclusive CPU/GPU access.

## Architecture decision

A correct direct-live-AHB production model is technically possible on this F8
for **server-owned, non-imported BGRA AHBs**, because A1 proved exact sampling
and the NDK permits a successful blocking `AHardwareBuffer_unlock(..., NULL)`
as the CPU→GPU handoff. But current source lacks the protocol needed to prove
that every admitted transaction reaches a safe terminal state.

Therefore:

```text
Production Gate A direct live-AHB on current contract:
BLOCKED

Reopen condition:
explicit authorization for a generation-bound renderer↔X protocol providing
(1) import-ready acknowledgment,
(2) checked CPU-release ownership transition,
(3) acquire/release queue and completion semantics,
(4) per-serial success/failure + quiesced replay contract,
(5) deferred unregister and teardown drain,
with imported AHB excluded from the first prototype.
```

This is not a byte-format blocker anymore. It is an ownership, result, and
lifecycle blocker. It cannot be resolved by changing only
`LorieBuffer_attachToGL`, `LorieBuffer_bindTexture`, or the Composite staging
selection.

## Sources

- Local NDK 29: `/root/android-sdk/ndk/29.0.14206865/source.properties`.
- Local AHardwareBuffer contract:
  `/root/android-sdk/ndk/29.0.14206865/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include/android/hardware_buffer.h:409-440,451-525`.
- Android NDK AHardwareBuffer reference:
  <https://developer.android.com/ndk/reference/group/a-hardware-buffer>.
- Khronos EGL Android native client buffer:
  <https://registry.khronos.org/EGL/extensions/ANDROID/EGL_ANDROID_get_native_client_buffer.txt>.
- Khronos EGL Android native fence sync:
  <https://registry.khronos.org/EGL/extensions/ANDROID/EGL_ANDROID_native_fence_sync.txt>.
- Source symbols and lines cited above under
  `lorie/src/main/cpp/lorie/{InitOutput.c,buffer.c,buffer.h,lorie.h,renderer.cpp,activity.cpp,cmdentrypoint.cpp}`.

## Safety and next action

```text
Source mutation: NO
Build/CI: NO
ADB/device/package/process: NO
Stable :1: UNTOUCHED
HDMI: UNTOUCHED
D0a/D0b/Gate H: UNCHANGED
```

**NEXT (one action):** architecture decision—either authorize a protocol-design
phase for the five reopen conditions above, or keep Production Gate A blocked
and continue using qualified D0a staging. No prototype or runtime is authorized
by this review.
