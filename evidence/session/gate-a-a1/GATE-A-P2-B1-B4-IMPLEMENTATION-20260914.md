# Gate A P2 B1–B4 correction + telemetry — 2026-09-14

## SOURCE

```text
branch: qualification/gatea-a1-microprobe-20260912
base:   82a87f4a99ae4b1d4e09d6c74a735cd40b6e73e2 (preserved, not amended)
head:   15caa00908aa9d1f1c4a78bb630aa24a93e7e4cd
worktree: /root/projects/GPU加速/src/f8-ahb-gatea-a1
D0a:    qualification/d0a-narrow-20260912 / a6cc795, untouched
```

Source written 2026-09-13; native compile, commit, and this evidence closed 2026-09-14.

## DIFF

```text
lorie/src/main/cpp/lorie/InitOutput.c      | 327 ++++++++++++++++++---
lorie/src/main/cpp/lorie/activity.cpp      | 104 ++++---
lorie/src/main/cpp/lorie/cmdentrypoint.cpp | 230 ++++++++++++++-
lorie/src/main/cpp/lorie/lorie.h           | 298 ++++++++++++++++++-
lorie/src/main/cpp/lorie/renderer.cpp      | 445 ++++++++++++++++++++++++-----
5 files changed, 1248 insertions(+), 156 deletions(-)
```

`git diff --check`: PASS (before and after commit). No unrelated files.

## WHAT EACH FILE CARRIES

- `lorie.h`: 48-byte per-slot `LorieGateADirectMeta` (EMPTY/PUBLISHED/CONSUMED),
  publish/observe/consume/legacy-prepare accessors, default-OFF telemetry
  (`TERMUX_X11_GATEA_TELEMETRY` exact `"1"` only), UNREGISTER/GENERATION_CLOSE
  frame types, X/renderer control and registry APIs. Frozen asserts remain:
  `LorieGpuCopyEntry == 168`, `LorieGateAProtocol == 40`,
  `LorieGateADirectMeta == 48`.
- `renderer.cpp`: B1 direct branch consume (`out.lastSerial` + `readIndex`)
  exactly once after slot copy, distinct from fence/`completedSerial`;
  B2 identity only from side metadata; READY miss / tuple mismatch /
  stale CONSUMED meta → FATAL, never `findBufferWithRetry` /
  `LorieBuffer_bindTexture`; UNREGISTER GL-thread reverse destroy
  (texture → EGLImage → AHB) then ACK; GENERATION_CLOSE empty-registry
  check + CLOSED + unbind; fatal `_exit(127)` with no normal cleanup.
- `cmdentrypoint.cpp`: pair reserved/submitted/released/retire/ack/snapshot,
  UNREGISTER_ACK and GENERATION_CLOSED input dispatch, generation waiter.
- `activity.cpp`: unified frame parse, UNREGISTER/GENERATION_CLOSE enqueue
  onto the GL-thread control queue, `wakeGateA`, `lorieGateAUnbindTuple`.
- `InitOutput.c`: B3 `gateAQueueSemanticallyQuiescent()` on every direct
  reserve (ACTIVE/no fatal, `wi==ri`, `completed==gpuCopySerialCounter`,
  semantic SUCCESS); B4 UNREGISTER/GENERATION_CLOSE lifecycle;
  `gateAClosing` blocks new admission; `gateAXFatal` on fatal paths;
  SUCCESS-only repair bypass via `gateAInternalRepair`.

## STATIC CHECKLIST

- B1 direct slot exactly-once consume: PASS.
  `applyPendingGpuCopiesLocked` direct branch
  (`renderer.cpp:1497-1505`) sets `out.lastSerial`, consume-meta,
  `publishReadIndex(ri+1)` before lookup/draw. Comment and code keep
  `readIndex` as slot-copied/consumed only. Legacy `else` still has its
  own consume (`:1681-1682`). A published direct entry cannot remain at
  the same `ri`.
- B2 explicit 48B identity, no legacy fallback: PASS.
  Classification is `directState == LORIE_GATEA_DIRECT_PUBLISHED`
  (`:1497`), not READY lookup. X publishes metadata before `writeIndex`
  (`InitOutput.c:2888-2899`). Lookup miss traces
  `DIRECT_LOOKUP_FAIL` then `gateARendererFatal`. `gateAIsReady` is
  absent. Stale non-EMPTY meta fatals before legacy upload.
- B3 every-reserve quiescence: PASS.
  `gateADirectTryPrepare` always calls `gateAQueueSemanticallyQuiescent()`
  (`InitOutput.c:2593-2596`). The `!gateAUsed` first-use special case is
  gone. Checks: ACTIVE/no fatal/no firstFailed, `wi==ri`,
  `completed == gpuCopySerialCounter`, last serial SUCCESS or last==0.
- B4 clean lifecycle: PASS.
  DestroyPixmap → `gateARetireBuffer` (READY→RETIRING, terminal wait,
  UNREGISTER, ACK, slot release). CloseScreen → `gateACloseGeneration`
  (`gateAClosing`, drain, retire snapshot, GENERATION_CLOSE, wait CLOSED,
  zero nonce/generation). Renderer GL loop drains controls
  (`renderer.cpp:2101-2103`). Resource order texture→EGLImage→AHB.
  `gateAXFatal` / `gateARendererFatal` publish fatal then `_exit(127)`;
  they do not run UNREGISTER/ACK/release.
- Telemetry default OFF / no OFF behavior change: PASS.
  `lorieGateATelemetryEnabled()` requires exact `"1"`. `lorieGateATrace`
  and `lorieGateACounterAdd` return immediately when OFF. Admission,
  identity, consume, and fail-stop do not consult the flag.
  `lorieGateASharedAtomicsLockFree` skips telemetry-atomics when OFF.
- Queue ABI unchanged: PASS. `sizeof(LorieGpuCopyEntry)==168` compiled.
- P0 sideband unchanged: PASS. `sizeof(LorieGateAProtocol)==40` compiled.

## NATIVE COMPILE

`:lorie:buildCMakeDebug[arm64-v8a]`, `--no-daemon --no-build-cache`,
`LANG=C.UTF-8`.

1. Incremental: BUILD SUCCESSFUL in 16s, exit 0.
   Log: `GATE-A-P2-B1-B4-NATIVE-BUILD-20260914.log`.
2. Full clean (`:lorie:clean` then the same native task): BUILD SUCCESSFUL
   in 1m 52s, exit 0.
   Log: `GATE-A-P2-B1-B4-NATIVE-BUILD-FULL-20260914.log`.
3. Warnings: 41 C/C++ warnings, identical `(file, -Wtype, message)`
   fingerprint set to the frozen P2 full-clean baseline
   (`GATE-A-P2-NATIVE-BUILD-FULL-20260913.log`). NEW unique: 0.
   Line numbers for keycode-designator / `%llu` / reorder-init shifted
   because `lorie.h` grew; same warning classes, not new warnings.
   Incremental rebuild of the five dirty TUs showed 9 of those same
   classes only.

## SCOPE

No push / CI / APK / ADB / install / runtime / device / Stable `:1` /
HDMI. No frozen ABI change. No P3. No D0b. No Gate H. No imported-AHB
policy change. Fail-stop and SUCCESS-only release were not weakened.
`gateAUsed` remains a write-only leftover (not read); left untouched
because compile did not reject it.

## NEXT (NOT THIS ROUND)

P2 runtime execution remains NOT AUTHORIZED. Production Gate A remains
BLOCKED. Any later runtime cell needs a separate authorization after
CI+artifact requalification of `15caa00`.
