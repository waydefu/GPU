# R8 fixture, observation and oracle interfaces

All paths/commands below are **PROPOSED deliverables**, not tools present in this docs PR. The accepted implementation must create them with these interfaces, bind their hashes in an artifact manifest and pass host verification before any device use.

## Build and activation boundary

Proposed CMake option `LORIE_ENABLE_R8_TEST_SUPPORT` defaults OFF. OFF builds register no test extension, install no test hooks or observers, and retain the original ABI. An enabled experimental build still requires X:
- exact `TERMUX_X11_GATEA_PROTO=1` and `TERMUX_X11_GATEA_TELEMETRY=1`;
- `TERMUX_X11_R8_CASE=<one exact cell ID>` and `TERMUX_X11_R8_ARM=1`;
- display `:3`, experimental launcher/package binding verified by harness, current nonzero tuple;
- no R6 requeue fault or unrelated Gate A fault environment.
- P1/P2 additionally require existing fault selector14/15 and TEST_ARM=1; all other cells require existing fault/arm absent.

The case/arm is validated once in X startup. A mismatched/unknown/partial setup fails before opening the test interface; it must never silently act as normal test mode. X-local state owns a phase-limited invocation budget derived from the cell JSON. TEST_CASE must not be read by renderer getenv (different process). Renderer observation is compile-gated plus existing shared telemetry-enabled, with no new shared flag. The full candidate build is test support, never a Stable installation.

## Test-only X control extension

Name proposal: `LORIE-R8-TEST`, protocol version1. This is an explicit new **test-only local X extension**, NOT a modification of Gate A wire/shared ABI. Register it only after validated activation; reject remote transport clients and clients without normal X authorization. No arbitrary address/path/FD/GL command/opcode forwarding.

Dispatch on the X main thread only, never from a terminal waiter. Use the pinned xserver's actual own-client resource lookup/access checks; verify supplied pixmaps belong to this connection, are live offscreen pixmaps, supported depths/formats, non-imported and not root/screen/window backing. Reject foreign/stale XIDs, swapped-invalid lengths, unrecognized opcodes, repeated forbidden phases and overflow without touching ownership.

Proposed requests/replies:
- `QUERY_VERSION`: exact version and active case, no mutation.
- `REGISTER_BUFFER(xid)`: C4/C5 only. Ensure actual buffer via `lorieEnsureGpuSampleable(...AHARDWAREBUFFER)`, call a wrapper around real static `gateAEnsureReady`, return accepted/refused and copied tuple/buffer/fingerprint/state/lastSerial/pending/occupancy. Do not call PrepareComposite, pair reserve, unlock, publish, Done, staging or CPU fallback. Same-buffer repeat may return existing READY according to real helper; it must not create a second slot. A refused descriptor/full pool is an explicit result, not fake READY.
- `CHECKPOINT(phase)`: copy safe X-owned registry/buffer/pair/root/queue state only; does not pump, dispatch, retire, clear counters or alter pending.
- No raw RETIRE or FREE command: fixtures use actual XFreePicture/FreePixmap/client teardown so real resource ownership is exercised.
- No completion injection command on device. D's synthetic injection seam is host-link-only and absent from Android artifact.

Protocol parsing is checked against request size and native/swapped client byte order. Version/case/ownership failures return a specific test-protocol error and are recorded; they cannot look like successful registration. A reply can carry at most16 registry rows; counts are explicit and truncation is an error. Existing active nonce/generation/serial are encoded as two32-bit words in specified network-order fields, never host-pointer serialization. The implementation freezes exact C structs, reply byte lengths and X extension request numbers in `r8-test-protocol.h` and parser tests before it is HOST_VERIFIED; any proposal to grow production shared structs is out of scope.

The test control is justified only by C4/C5's otherwise unreachable setup. Normal cells C1/C2/C3/D use the production X requests; observation checkpoints must not reconfigure their scheduling.

## Fixture CLI

Proposed outputs in the source/harness worktree:
- `tests/r8/p_r8_lifecycle.c` → `p_r8_lifecycle` (links xcb/render/present and test-protocol client helpers).
- `tests/r8/run-r8-one-cell.sh` (orchestration only).
- `tests/r8/judge-r8.py` and `tests/r8/test-judge-r8.py`.
- `tests/r8/verify-r8-support.py` and actual-source host tests.
- `tests/r8/collect-r8.py` binds raw records, no caller-provided verdict booleans.

Exact proposed commands, for **later authorized F8 shell**:

```bash
# No device action in this planning task.
python3 tests/r8/verify-r8-support.py --source "$SRC" --spec "$SPEC"
python3 tests/r8/test-judge-r8.py --vectors "$NEGATIVE_CASES"
p_r8_lifecycle --display :3 --cell R8-C1 --spec "$SPEC" --client-log "$NEW/client.jsonl"
bash tests/r8/run-r8-one-cell.sh --manifest "$MANIFEST" --spec "$SPEC" --cell R8-C1 --evidence "$NEW"
python3 tests/r8/judge-r8.py --manifest "$NEW/manifest.json" --spec "$SPEC" --evidence "$NEW" --output "$NEW/judge.json"
```

The runner invokes the fixture; never invoke both fixture and runner as separate device attempts. The explicit fixture command documents its interface, not an additional run. `MANIFEST` binds full source SHA, successful fork CI/head, APK SHA256/signature/package/version, both Build IDs, installed read-back, fixture/judge/collector/spec hashes, grant/cell/counts, live device/display and process identities. `SPEC` is this cell spec copied with accepted design revision; newly built tool hashes come from implementation manifest, never fabricated in this design.

A fixture clean cell uses 64×64 offscreen BGRA source/RGBX destination, no mask/transform/repeat/componentAlpha, nearest, one rectangle per direct operation. Present cells use1024×1024 ASYNC|COPY on the current display geometry; record clipping/visible geometry and reject a window setup that cannot exercise the required copy. Pixel reference uses existing exact premultiplied Over arithmetic; explicit expected X-byte rule stays unchanged. Direct counts and stream counts are in JSON. No xterm/XFCE compositor or unrelated client may consume registry slots in these isolated cells.

For C1/C4 frees: release Picture objects referencing the pixmaps before FreePixmap, flush/check errors and obtain an X round-trip barrier; free source then destination as specified. A FreePixmap request alone does not prove the last server reference was dropped.

For C3: source copy scheduled is mandatory. Immediate DestroyWindow/client disconnect is issued without waiting for CompleteNotify; collector may observe early completed work legitimately. A destroyed client/window need not receive notifications. Readiness of a survivor connection and subsequent exact direct operation prove continued usable server state.

For D: one Present connection, one gate-pair connection, a live observer. Submit8 unique accepted ASYNC|COPY requests in two bursts of4; flush the first burst, issue source FreePicture/FreePixmap on the gate pair, flush remaining4, free destination, then drain all8 Present notifications. No wait-for-completion barrier before the frees, no sleeps. Existing copy scheduling may coalesce wakeups; event count is not notification count. One entire session only; absent required overlap => INVALID_CONSTRUCTION. The schedule is bounded and auditable, not claimed deterministic.

## Observation schema and producer map

Text prefix `R8_OBS ` followed by one bounded JSON object/line. Required envelope:
`v=1, role, pid, tid, producer_seq, case, phase, original_nonce, original_generation`.
Each role's BEGIN and END contain expected record count/digest; every required line must be present and internally consistent. Split oversized snapshots into numbered rows with declared total/digest; no truncated JSON is accepted. Renderer may use case=null and be bound externally by exact mapped artifact and tuple; it must not invent an X env value.

For P1/P2, require the X fault-prefix and final fatal diagnostic snapshot; do not require a graceful renderer END, unbind or zero resources. X fatal diagnostics must close only their observation stream before exit, never run resource cleanup. Clean cells require both roles' final streams. Unexpected crash/incomplete fatal capture cannot acquire a PASS by substituting collector-generated END metadata.

Phase payloads:
- `X_REG_ROW`: bufferId/fingerprint/state/lastSubmittedSerial/pendingCount/cpuLocked; actual buffer pending is separately read, not c11.
- `X_CHECKPOINT`: registry_count, total actual buffer pending for enumerated owned buffers, root_pending, pair_state/src/dst, readIndex/writeIndex/completedSerial, firstFailed/generationFatal, tuple. For nonzero serial terminal proof use same mapping.
- `X_DESTRUCTOR_ENTER/EXIT`: copied bufferId, overlap predicate and before/after slot existence. EXIT output uses copied scalar IDs only.
- `X_TERMINAL_WAIT_ENTER`: bufferId and requested serial; C4 forbids this for target IDs.
- `R_DESTROY_STAGE`: texture_deleted, image_destroyed, ahb_released for same import; actual GL-thread identity, not merely function entry.
- `R_ACK_SETTLED`: original tuple, bufferId, current READY/import/control count and resource balances after existing ACK diagnostic decrement. No global zero demanded while other imports remain.
- `X_CLOSE_ENTER`, `X_CLOSE_RESULT`, `R_UNBOUND_FINAL`: original tuple, before/after registry/pending/lease state and result. R_UNBOUND_FINAL only after successful real unbind and final resource state copy. No live-resource dereference after final release.
- `PRESENT_SUBMIT`: client/window/Present request serial ↔ actual GPU copy serial/dst ID. `PRESENT_PRE_ACK`: same identity, completed watermark T, firstFailed/fatal, pending flags/counts. `PRESENT_POST_ACK`: flags cleared and pending decrements for that actual helper invocation. `PRESENT_IDLE/DESTROY` requires preceding retirement when pending.
- `R_WAKE_SENT`: successful notify send ordinal on that exact connection, cause=fence_completed or surface_loss, completed watermark, original tuple. A failed send is not a sent ordinal.
- `X_WAKE_RECEIVED`: ordered receive ordinal on same connection and new X-local record ID; legacy payload has no serial. Join nth successful type-specific send/receive only with complete connection-bound records and no reconnect.
- `DEFER_ENQUEUE/DEFER_DISPATCH/DEFER_CANCEL/RECHECK`: local record ID/type/original tuple, active wait kind and queue occupancy; actual successful ownership transfer and dispatch, not attempted call. X-local metadata may be added to the deferred-record struct under test compile guard; never legacy wire fields.
- `TEST_CONTROL`: operation sequence/client/XID and true helper result; `P1_DESTRUCTOR_CALL` at actual call site and `R8_HOOK_UNEXPECTED_RETURN` sentinel.

Existing Gate A events retain their exact meaning. event26 proves aggregate renderer release only with actual producer ordering; event36 is before terminal wait. Sideband fields are observation only; none feed product admission/result decisions.

Capture policy: exact owned launcher output and PID-filtered logcat plus existing ring/summary. Do not clear logcat. Hash raw files before normalization. Missing required diagnostics yields INVALID even if existing ring repairs its own event stream; the frozen ring cannot repair newly invented sideband records. All BEGIN/END/hash/counts must derive from the actual producer; collector-generated expected counts are not proof of no lost tail.

## Preflight / stop / cleanup

1. Read accepted design/grant; fetch current handoff; bind exact installed artifact. Do not install automatically.
2. Require entire output directory absent, no existing experimental X3, source/tools/spec hashes match, Stable before snapshot and live ADB5038/display0 identity valid.
3. Validate all exact env reaches X; instrumentation compiled and activated; gate-control extension absent when disallowed. Allocate new manifest first in fresh directory, no copy of an old verdict.
4. One fresh X, one fixture case, frozen case count. Record actual runner/fixture/judge rc; no loops until overlap or PASS.
5. C1/C3/C4/C5-overflow/D require usable X before requested clean shutdown. C2/C5-full request normal verified TERM per their construction. P cases observe fatal/process state **before** cleanup.
6. Copy final X and renderer records after their actual last phases; observation timeout proposed12s, product wait remains2000ms. If required phase absent, INVALID/FAIL as appropriate; no extension to get green.
7. Stop owned fixture/holder/logcat, experimental Activity and any remaining verified own X3 after verdict capture. Record actual socket/lock and process absence, Stable unchanged. Never kill an unrelated session, Stable or ADB5037.
8. A crash/fatal in a clean cell is FAIL if correctly bound; absent identity/construction/trace is INVALID. A preflight mismatch is BLOCKED without starting the cell.

## Oracle CLI outputs

Exit0: `R8_PASS <cell>`; JSON layer flags all true and evidence references bound.
Exit1: `R8_FAIL <predicate>`; complete bound evidence proves forbidden product behavior.
Exit2: `R8_INVALID <reason>`; required construction/identity/trace/observation is unusable.
Exit3: `R8_BLOCKED <dependency>`; no device attempt should have started.

Process liveness is an input captured before teardown, not inferred from runner exit. Use three-valued fields: true/false/null; null fails required claims closed. An expected P fatal may have an unobservable raw exit code, but requires exact fatal marker, PID-bound no-crash audit and disappearance under the adopted frozen policy; never invent a waitpid status.

For P1/P2 run immutable R7 judge with selectors `destroy-while-gpu-owned` / `close-while-lease` plus R8 supplemental oracle for event5, actual guard entry, no unexpected-return marker, no resource release/CLOSED and matched pair. A07's stronger GPU_OWNED requirement is not replaced by the frozen judge's event2 check.

## Required evidence files

`manifest.json`, `grant-reference.txt`, `preflight.json`, `commands.jsonl`, `env.txt`, `artifact-binding.json`, `process-identities.json`, `fixture.jsonl`, raw launcher/logcat, ring/summary, `x-observations.jsonl`, `renderer-observations.jsonl`, `capture-completeness.json`, `pre-cleanup-process-state.json`, `judge.json`, original judge stdout/stderr/rc, `cleanup.json`, `stable-before.json`, `stable-after.json`, `sha256-manifest.json`. No APK/ELF, credential or private pairing material enters the docs repository.
