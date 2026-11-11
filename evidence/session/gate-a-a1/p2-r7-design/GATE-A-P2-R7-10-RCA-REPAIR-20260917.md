# Gate A P2 R7-10 RCA + HUP-containment repair — 2026-09-17

Frozen `a07d66c` R7-10 **VALID FAIL**. This packet is RCA + repair + artifact
authority. **No device retry. No install. Judge and 2000 ms unchanged.**

## Primary verdict

**`R7_10_RCA_PROVEN_REPAIR_ARTIFACT_QUALIFIED`**

- Historical `a07d66c` R7-10 remains **VALID FAIL / FROZEN**.
- Repair SHA `8545b26b308aa60b05685f48560285350e22ee8d` is **HOST/STATIC/ABI/CI/ARTIFACT QUALIFIED**.
- CI **35225593518** PASS. APK **NOT INSTALLED**.
- Device: still **`a07d66c` INSTALLED**.
- R7 overall: **IN PROGRESS** (10/13). R7-P1 **BLOCKED**. Production Gate A **BLOCKED**.

## Frozen failure authority

| Item | Value |
|---|---|
| Candidate | `a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82` |
| Package | `com.waydefu.x11gpu` `1.03.01-a07d66c-17.09.26` / 15 |
| APK SHA256 | `a25861b41fe9088a7163e5d882909ca0a292780e418e1278665a436b27bface5` |
| Signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` |
| Build ID | `ad3509c0e64d4de3c7846117978881995b2543f2` |
| CI | **35171333149** |
| Cell | `evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-a07d66c/r7-10/` |
| X | 12568 TID 12860 |
| Activity | 28497 renderer TID 12463 |
| Construction | PUBLISH(6) seq=28 → CONSUME_DIRECT(7) seq=29 → event35 seq=30 enum=10 side=2 |
| Target | generation=1 serial=5 src=6 dst=7 |
| Expected last halt | `x-hup` reason=6 |
| Actual last halt | `x-direct-not-success` reason=4 |
| Judge | `R7_FAIL halt_mismatch` exit 1 |
| Class | **VALID FAIL** (not INVALID) |
| `judge-r7.py` | unmodified SHA256 `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17` |

Do **not** overwrite `runtime-a07d66c/r7-10/`. Do **not** retry that cell.

## Device evidence timeline

Clock is logcat milliseconds on 2026-09-17. Labels are exclusive.

| T | Instant | Label | Evidence |
|---|---|---|---|
| T0 | 20:38:03.924 | **DEVICE OBSERVED** + **SOURCE PROVEN** | X TID 12860 `GATEA_EVENT seq=28 event=6` PUBLISH serial=5 src=6 dst=7. Source: `gateADirectPublishRect` publishes then `pthread_cond_signal`. |
| T1 | 20:38:03.925 | **DEVICE OBSERVED** + **SOURCE PROVEN** | Renderer TID 12463 `seq=29 event=7` CONSUME_DIRECT same tuple. Source: consume then fault site. |
| T2 | 20:38:03.925 | **DEVICE OBSERVED** + **SOURCE PROVEN** | `seq=30 event=35 src=10 dst=2` enum=10 side=renderer. One-shot CAS then event 35. |
| T3 | 20:38:03.925 | **SOURCE PROVEN** dump; **DEVICE OBSERVED** SUMMARY; `_exit` **INFERRED** | `GATEA_SUMMARY where=r-exit-after-consume generationFatal=0 fatalReason=0`. Source immediately `_exit(127)` with no `gateARendererFatal` / no completed / no ACK. Device has no `_exit` log line. |
| T4 | 20:38:03.949 | **DEVICE OBSERVED** Activity death; AF_UNIX close **INFERRED** | InputDispatcher `events=0x9`, `WINDOW DIED` MainActivity. Renderer process death closes `socketpair` peer `client[0]`. Exact kernel HUP timestamp on X `conn_fd` is not traced. |
| T5 | from T0 | **SOURCE PROVEN** wait on X TID 12860; start vs PUBLISH **INFERRED** | `lorieExaDoneComposite` → `gateADoneDirect` → `gateAWaitTerminal`. Same dix-main TID later emits seq=31. Single-rect fixture: wait begins as soon as Composite returns into Done. |
| T6 | ≤20:38:03.949 | **SOURCE PROVEN** wait can observe HUP; dispatch **UNKNOWN** unused | `lorieConnectionAlive()` `poll(conn_fd, 0)` watches `POLLHUP\|POLLRDHUP\|POLLERR\|POLLNVAL`. ospoll `handleLorieEvents` was not invoked (x-hup=0, x-eof=0). |
| T7 | n/a | **FALSIFIED** | Halt is **24 ms** after event35, not `elapsed > 2000`. 2000 ms budget did not expire. |
| T8 | 20:38:03.949–.953 | **DEVICE OBSERVED** + **SOURCE PROVEN** | seq=31 event=16 GENERATION_FATAL; SUMMARY `where=x-direct-not-success generationFatal=4`; `GATEA_FATAL_HALT what=x-direct-not-success reason=4` TID 12860. |
| T9 | after T8 | **DEVICE OBSERVED** | X 12568 dead, Activity 28497 absent. `x-hup=0 r-hup=0 GATEA_HUP_PRESERVE=0`. |

**FAULT CONSTRUCTION CORRECT.** Renderer alive before fault. Intentional `_exit` after CONSUME_DIRECT. No LOOKUP/DRAW/FENCE/COMPLETED/SUCCESS/ACK/release/fallback/replay after event35. Renderer own `GATEA_FATAL_HALT` absent. Old fatal-preserve repair **NOT APPLICABLE** (`generationFatal=0` at exit).

## Source control flow (`a07d66c`)

```text
lorieExaDoneComposite (direct)
  → gateADoneDirect
      → r = gateAWaitTerminal(lastSerial)
          loop:
            derive(completed, firstFailed, fatal, serial)
            if result != NONE: return it
            if !lorieConnectionAlive() || !lorieRendererAvailable():
                return FATAL          // peer death lands here
            if elapsed > 2000: return FATAL
            usleep(200)               // 200 µs
      → cls = lorieGateAClassifyDirectDone(r, publishedFatal, firstFailureCode)
      → if cls != SUCCESS:
            gateAXFatal("x-direct-not-success", reason, serial)
```

`lorieGateAClassifyDirectDone` on `RESULT_FATAL` with `publishedFatal==0` sets
`reason = FAIL_TIMEOUT (4)` and `DONE_TIMEOUT`. That is why reason=4 is the
halt identity even when the wait returned in 24 ms.

`handleLorieEventsProto` emits `x-hup/6` only on `ready & X_NOTIFY_ERROR`.
That callback is registered by `InputThreadRegisterDev` → because lorie never
calls `InputThreadPreInit()`, `inputThreadInfo` stays NULL and registration
falls back to `SetNotifyFd(conn_fd, handleLorieEvents, X_NOTIFY_READ)` on the
X dix-main pthread (`xserver/os/inputthread.c` gitlink `65d790bd`, same as
`a07d66c`). `gateAWaitTerminal` never calls `WaitForSomething` /
`lorieGateAPumpConnection` / `handleLorieEvents`. The only conn_fd reader that
can emit `x-hup` is starved. The wait **does** poll the same fd via
`lorieConnectionAlive()`, so HUP is observed, then misclassified.

This is **not** the R7-04/R7-05 published-fatal overwrite. Renderer left
`generationFatal=0`. cmdentrypoint `x-hup` never ran.

## Thread / socket ownership

| Endpoint | Owner | Observer during R7-10 wait |
|---|---|---|
| `socketpair` `client[0]` | Activity / renderer process 28497 | closed by `_exit` |
| `socketpair` `client[1]` = X `conn_fd` | X dix-main | `lorieConnectionAlive` poll; also `SetNotifyFd` (not pumped) |
| Shared `lorie_shared_server_state` | both; X mapping survives renderer `_exit` | `surfaceAvailable` **not** cleared on the dump/`_exit` path |

Same AF_UNIX connection. HUP is level-triggered `poll(..., 0)` in the wait
and would be `EPOLLHUP` → `X_NOTIFY_ERROR` if dix-main returned to ospoll.

`lorieExaDoneComposite` / `gateAWaitTerminal` / `gateAXFatal`: **X TID 12860**.
`handleLorieEvents` / `x-hup`: **same dix-main thread**, only when ospoll runs.
Renderer drain / `_exit`: Activity TID 12463. No shared mutex is held across
the wait (`gateAWaitTerminal` only acquire-loads + `usleep`). The failure is
**event-loop starvation plus misclassification**, not a lock inversion.

## Direct terminal wait analysis

| Item | `a07d66c` fact |
|---|---|
| Primitive | `clock_gettime(CLOCK_MONOTONIC)` + `usleep(200)` loop |
| Success wake | `completedSerial >= serial` with fatal=0, firstFailed not poisoning |
| Fatal wake | `generationFatal != 0` (derive FATAL) |
| Peer-death wake | `!lorieConnectionAlive()` → **FATAL**, not x-hup |
| Surface wake | `!lorieRendererAvailable()` → FATAL (not used on this `_exit` path) |
| Timeout | `elapsed > 2000` → FATAL |
| Can renderer death wake the wait? | **YES**, via `poll(conn_fd)`. It cannot invoke `x-hup`. |

## HUP dispatch analysis

`x-hup` emit sites on X (unchanged, still required for idle-generation HUP):

- proto: `handleLorieEventsProto` `X_NOTIFY_ERROR` → `gateAFatalFromInput(..., "x-hup")`
- legacy: `handleLorieEventsLegacy` same flag → `lorieGateAFatalHalt("x-hup", 6)`

Condition: notify callback runs with error/HUP ready bits. Depends on dix-main
ospoll. Direct Done wait does not pump that source. Generation/serial for
cmdentrypoint HUP is the bound tuple (serial 0 in that path); R7-10 expected
reason is still 6.

## Root cause

**PROVEN.**

Renderer `_exit(127)` after CONSUME_DIRECT closes the Activity end of `conn_fd`.
X dix-main is inside `gateAWaitTerminal`. That loop observes POLLHUP through
`lorieConnectionAlive()` within one 200 µs slice after the kernel HUP (~24 ms
wall, **not** 2000 ms), returns `LORIE_GATEA_RESULT_FATAL` with
`generationFatal==0`, and `lorieGateAClassifyDirectDone` maps that to
`x-direct-not-success` / `FAIL_TIMEOUT=4`. `handleLorieEventsProto` never runs,
so `x-hup/6` is never emitted.

## Why reason4 won

Classifier contract: `RESULT_FATAL` + `publishedFatal==0` **is** timeout.
Peer death reused that bucket. Device elapsed falsifies a real 2000 ms expiry.

## Why x-hup did not win

x-hup is only produced by the conn_fd notify callback on dix-main. Dix-main
was blocked in the wait. The wait consumed the HUP observation itself and
halted with the timeout identity before ospoll could deliver `X_NOTIFY_ERROR`.

## Repair design

Class **A** (wait integrates peer-death observation). No new shared field.

New host-testable helper `lorieGateAClassifyWaitWake`:

| connectionAlive | rendererAvailable | timeoutExpired | publishedFatal | class | halt |
|---|---|---|---|---|---|
| 0 | * | * | 0 | `X_HUP` | `x-hup` / 6 |
| 0 | * | * | ≠0 | `PRESERVE_FATAL` | `gateAXFatal` preserve (no second identity) |
| 1 | 0 | * | * | `SURFACE_LOSS` | existing FATAL → Done timeout path |
| 1 | 1 | 1 | 0 | `TIMEOUT` | existing `x-direct-not-success` / 4 |
| 1 | 1 | 0 | * | `CONTINUE` | `usleep(200)` |

Caller order frozen: **derive first**. SUCCESS / QUIESCED / published FATAL
return before wake classification. Normal completed-before-peer-close stays
SUCCESS.

`gateAWaitTerminal` and `lorieGpuCopyWait` both use the helper. Present 2000 ms
timeout path `x-present-copy-wait/4` remains for a **live** peer (R7-P1).

Not used: renderer `generationFatal` before `_exit`; timeout inflation; judge
change; ABI word; event-loop pumping inside Done.

## Fatal precedence / race semantics

1. Derived SUCCESS (completed ≥ serial, no fatal, not poisoned) **wins** over a
   later HUP. Wait returns before wake classify.
2. Derived / published `generationFatal != 0` **wins** over HUP.
   `gateAXFatal` still dumps `x-observe-fatal` and `_exit(127)` without a
   second `GATEA_FATAL_HALT`.
3. Peer HUP with published==0 and no SUCCESS **fail-closes as `x-hup/6`**.
   Must not wait for 2000 ms.
4. Live peer, no completion, `elapsed > 2000` remains **timeout / 4**.
   Not relabeled HUP.
5. Surface loss without socket HUP is **not** x-hup.

## Compatibility matrix

| Cell | Why unbroken |
|---|---|
| R7-01 src-ready-miss | Renderer publishes DRAW fatal then halt. Derive sees fatal first. Later HUP preserve. |
| R7-02 dst-ready-miss | Same as R7-01. |
| R7-03 tuple-mismatch | Renderer PROTOCOL fatal. Preserve. |
| R7-05 post-draw-gl | QUIESCED firstFailed DRAW; X `x-direct-not-success/2`; Activity HUP preserve already on `a07d66c`. Wait returns QUIESCED, never X_HUP. |
| R7-06 fence-create-fail | Renderer FENCE fatal. Preserve. |
| R7-07 fence-timeout | Renderer fence-wait fatal. Preserve. |
| R7-08 renderer-fatal-pre-fence | Renderer GENERATION fatal then (eventually) process death. Preserve, no x-hup overwrite. |
| R7-09 wrong-generation-frame | X cmdentrypoint fatal on inbound frame; no Done wait. Untouched. |
| R7-11 serial-wrap | X publish-path fatal; no renderer `_exit`. Untouched. |

## R7-P2 impact assessment

R7-P2 `present-renderer-exit` expected `x-hup/6` was going to hit
`lorieGpuCopyWait` → FALSE on `!lorieConnectionAlive()` →
`x-present-copy-wait/4`. The same helper is now in `lorieGpuCopyWait`, so
present peer death **shares** this repair. **Do not execute R7-P2.**

R7-P1 `present-hold-complete` keeps a live renderer and withholds
`completedSerial`; still 2000 ms → `x-present-copy-wait/4`.

## Files changed (repair worktree)

Worktree: `src/f8-ahb-gatea-r7-10-hup`
Branch: `fix/gatea-r7-10-hup-containment-20260917`
HEAD: `8545b26b308aa60b05685f48560285350e22ee8d`
Parent: `a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82` (historical commit **not** rewritten)

| File | Role |
|---|---|
| `lorie/src/main/cpp/lorie/lorie_gatea_wait_wake_class.h` | wait-wake classifier |
| `lorie/src/main/cpp/lorie/lorie.h` | include helper |
| `lorie/src/main/cpp/lorie/InitOutput.c` | `gateAWaitTerminal` + `lorieGpuCopyWait` |
| `scripts/test_gatea_wait_wake_class.c` | host tests |
| `scripts/verify_r7_10_hup_containment.py` | static gate |

`cmdentrypoint.cpp` x-hup kept. Renderer `_exit` hook unchanged. Judge/runner
untouched (outside this tree).

## Host tests

`scripts/test_gatea_wait_wake_class.c` → `GATEA_WAIT_WAKE_CLASS=PASS`

| Case | Expect |
|---|---|
| connection dead, published=0, even if timeoutExpired | `X_HUP` reason=6, not 4 |
| connection dead, published=DRAW/FENCE | `PRESERVE_FATAL`, not x-hup |
| live + not expired | `CONTINUE` |
| live + expired + published=0 | `TIMEOUT` reason=4; Done classifier still timeout |
| live + surface 0 | `SURFACE_LOSS`, not x-hup |
| Derive SUCCESS still SUCCESS | production returns before wake |

Existing `test_gatea_direct_done_class` PASS. `test_gatea_hup_class` PASS.

## Static verifier

`python3 scripts/verify_r7_10_hup_containment.py $WT` → `R7_10_HUP_CONTAINMENT=PASS`

Also PASS: `verify_r7_fatal_propagation.py`, `verify_r7_hup_preserve.py`,
`verify_exa_composite_wait.py`, `verify_case_loop_wakeup.py`.

Checks: no timeout widen, no judge in tree, no ABI drift, no auto retry,
derive-before-wake, HUP reachable before timeout class, published-fatal
precedence, cmdentrypoint x-hup retained, fault hook still dump+`_exit`
without renderer fatal.

## ABI freeze

Unchanged: `sizeof(LorieGateAProtocol)==40`, `generationFatal` offset 4,
protocol version 1, `EVENT_MAX==37`, `COUNTER_MAX==28`, fault enum 10/11 tail,
fence 2000 ms, CASE_LOOP 8 ms, `usleep(200)` cadence.

## CI / artifact

CI **35225593518** `workflow_dispatch` **success**.
headSha = local HEAD = fork HEAD = `8545b26b308aa60b05685f48560285350e22ee8d`.

| Item | Value |
|---|---|
| Package | `com.waydefu.x11gpu` |
| versionName | `1.03.01-8545b26-17.09.26` |
| versionCode | 15 |
| APK SHA256 | `92220845a4cfff24eb47edef95664070d7bf60b159c01258e03b91d6a332377a` |
| signer | `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1` |
| Build ID | `50a4078b940d982e1ca1484cac6dd2bf2abe7b0a` |
| Installed | **NO** |

Provenance:
`evidence/session/gate-a-a1/p2-r7-10-hup-ci-35225593518/P2-R7-10-HUP-CONTAINMENT-CI-ARTIFACT-PROVENANCE-20260917.md`

## State transition

```text
a07d66c:
  R7-10 VALID FAIL / FROZEN
  INSTALLED

8545b26:
  R7-10 candidate for requalification
  ARTIFACT QUALIFIED
  NOT INSTALLED

R7 overall: IN PROGRESS
progress: 10/13
R7-P1: BLOCKED
Production Gate A: BLOCKED
R8/R9/R10: NOT STARTED
```

## Recommended next action

**Separate** one-shot R7-10 device requalification on **`8545b26` only**, after an
explicit install+cell grant. Do not retry `runtime-a07d66c/r7-10`. Do not
rerun R7-01/02/03/05/06/07/08/09/11 unless a later impact review authorizes
it. Do not start R7-P1 / R7-P2. Do not auto-install.
