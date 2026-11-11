# Gate A P2 R7 — 8545b26 R7-P1 dedicated runner tooling qualification — 2026-09-17

```
PRIMARY_VERDICT: R7_P1_8545B26_RUNNER_QUALIFIED
8545b26: INSTALLED / R7-10 PASS FROZEN / R7-P1 NOT RUN / RUNNER QUALIFIED
R7-P1 device: NOT RUN / UNBLOCKED
R7 overall: IN PROGRESS (11/13)
Production Gate A: BLOCKED
Device execution this task: NONE
```

This packet is **tooling only**. It is **not** `R7_PASS present-hold-complete`
and **not** an R7-P1 device qualification.

## Starting authority

- Candidate `8545b26b308aa60b05685f48560285350e22ee8d` INSTALLED experimental only
- Artifact: `com.waydefu.x11gpu` `1.03.01-8545b26-17.09.26` versionCode 15
  APK SHA256 `92220845a4cfff24eb47edef95664070d7bf60b159c01258e03b91d6a332377a`
  signer `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1`
  Build ID `50a4078b940d982e1ca1484cac6dd2bf2abe7b0a`
  CI **35225593518**
- R7-10 RCA PROVEN; repair ARTIFACT QUALIFIED; R7-10 runner QUALIFIED;
  8545b26 R7-10 **PASS** (`runtime-8545b26/r7-10/`, X 13115, last halt `x-hup/6`)
- a07d66c R7-10 VALID FAIL FROZEN (`runtime-a07d66c/r7-10/`, `x-direct-not-success/4`)
- R7-04 / R7-05 / R7-01 / R7-02 / R7-03 / R7-06 / R7-07 / R7-08 / R7-09 / R7-11 PASS frozen
- R7 IN PROGRESS 11/13
- Frozen generic runner SHA256 `36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded`
  still marks `r7-p1` **REVIEW_REQUIRED** / live REFUSE (not lifted)
- Frozen judge SHA256 `fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17`
- Production Gate A BLOCKED; R8/R9/R10 NOT STARTED

## Frozen R7-P1 contract

Selector: `present-hold-complete`
Cell: 12
Fault side: renderer / 2
Fixture: present
Expected construction: CALLBACK(30) src=4
Expected terminal: `GATEA_FATAL_HALT what=x-present-copy-wait reason=4`
Frozen judge expected: `R7_PASS present-hold-complete`
Judge metadata: cell=12 side=2 what=x-present-copy-wait reason=4 need=(present_cb,) present=true

This is **not** renderer-exit / peer HUP (R7-10, expected `x-hup/6`).
This is **not** direct composite timeout (`x-direct-not-success/4` or `x-exa-composite-wait/4`).

## 8545b26 wait-repair interaction

Shared classifier `lorieGateAClassifyWaitWake` precedence:

1. SUCCESS (completedSerial) wins in the wait loop (`lorieGpuCopyIsDone`)
2. published `generationFatal != 0` + peer dead → PRESERVE_FATAL
3. peer dead + publishedFatal=0 → `x-hup` / FAIL_GENERATION=6
4. live peer + elapsed timeout → FAIL_TIMEOUT=4

R7-10 exercises (3): renderer `_exit(127)` → conn_fd HUP → `x-hup/6`.

R7-P1 exercises (4): renderer stays alive, COPY `completedSerial` withheld,
no authoritative fatal, Present wait 2000 ms expires → `x-present-copy-wait/4`.

Host binary `test_gatea_wait_wake_class` **PASS**: peer-dead+timeoutExpired still
HUP (not timeout/4); live-peer+timeoutExpired still TIMEOUT/4.

If 8545b26 caused P1 to emit `x-hup/6` with a live renderer: **PRODUCT FAIL**.
If P1 still emits genuine `x-present-copy-wait/4` with peer alive: **correct**.

## Present fixture provenance

| Field | Frozen identity |
|---|---|
| path | `evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_r6_d2_present` |
| SHA256 | `fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86` |
| size | 72536 |
| ELF | aarch64 PIE, BuildID `81bf1d980025f2b11d8afcd89c7fe3fa13d485d2` |
| invocation | `p_r6_d2_present inflight` |
| source | `patches/p_r6_d2_present.c` SHA256 `c647b39157a216819dc52cbf603ea06bfa3b87769e911ac26cf60c4717f1a740` |

Source mtime is later than the shipped ELF. R7 identity is the **SHIPPED ELF**,
not a rebuild. The client is xcb-present `PresentPixmap` with
`ASYNC|COPY` on DISPLAY `:3`; it is not linked to `libXlorie.so`. That protocol
is the 8545b26 Present GPU-copy path. Compatible. Not BLOCKED.

Holder `p_b3a_hold` SHA256 `3417abbf0855c10bfd2328e87f33518c2f7f59c42529ba157a847d3019f5b5ca`
is required **exactly once**: `lorieRendererAvailable()` is `surfaceAvailable`.
A 2000 ms live-peer Present wait must keep the experimental `:3` surface mapped.
This is not a direct-cell buffer-owner assumption.

## Fault12 source reachability (8545b26)

`LORIE_GATEA_TEST_PRESENT_HOLD_COMPLETE = 12`. Name `present-hold-complete`.

`lorieGateATestFaultConsume` one-shot CAS then traces event 35
(`EVENT_TEST_FAULT_FIRED`) with src=cell dst=role.

Consume sites after GPU fence, **legacy `!gateASeen` path only**:

- `Renderer::applyPendingGpuCopies` (`renderer.cpp` ~1937)
- `Renderer::redrawLocked` (`renderer.cpp` ~2209)

Present COPY is `LORIE_GPU_OP_COPY` and never sets `gateASeen`, so fault12
reaches the withheld-completion hook.

Withheld action: skip `lorieGateAPublishCompleted` and skip `notifyGpuCopyDone`,
then `return`. Renderer stays in its loop. No `_exit`.

P2 `LORIE_GATEA_TEST_PRESENT_RENDERER_EXIT = 13` remains a **separate** COPY-slot
`_exit(127)` at ~1875. Not used by this runner.

CALLBACK(30) src=4: `lorieGateATraceXCallback(4u, gpuCopySerial, …)` in
`present_execute.c` immediately after `lorieTryScheduleGpuCopy` succeeds
(`LORIE_GATEA_XOP_PRESENT = 4`).

Typical observed order (not a stricter invented schedule):

1. PresentPixmap ASYNC|COPY
2. COPY scheduled → CALLBACK 30 src=4
3. queue_vblank often Success (first request returns; wait is not here)
4. renderer fence then fault12 → event35 enum=12 side=2; completedSerial withheld
5. later `present_gpu_copy_retire_or_fatal` (requeue-fail or `present_vblank_destroy`)
6. event36 waited=1 (helper-entry / waited-sample, **not** completion)
7. `lorieGpuCopyWaitForPresentOrFatal(serial, 2000)`
8. live peer, no fatal → genuine timeout → `x-present-copy-wait/4` (noreturn)

event36 is **not** standalone terminal proof. Classifier uses waited=1 only as
wait-entry for elapsed measurement.

event34 / CompleteNotify / `present_pixmap_idle`: `gateAXFatal` is noreturn, so
ack/idle after a real timeout cannot run. Target event34 or CLIENT_OK after
fault is `TARGET_COMPLETED` / product FAIL.

## Renderer liveness model

`lorieConnectionAlive()` polls **`conn_fd`** for `POLLERR|POLLNVAL|POLLRDHUP|POLLHUP`.
That fd is the Activity↔X shared-server socket, not the Present X11 client.

Fault12 does not kill the renderer, so `conn_fd` stays up → peer-alive stays true
→ wait-wake cannot take the HUP class.

Runner samples Activity+X3 during WAIT_S and requires Activity ALIVE at
pre-cleanup. Renderer death before timeout is `PEER_DIED` /
`INVALID_CONSTRUCTION`, never a valid P1 timeout.

Expected clean HUP audit before the Present timeout terminal: `x-hup=0` `r-hup=0`
`GATEA_HUP_PRESERVE=0`.

## Genuine timeout model

Product wait remains **2000 ms** (`lorieGpuCopyWait(serial, 2000)` then
`gateAXFatal("x-present-copy-wait", LORIE_GATEA_FAIL_TIMEOUT, serial)`).
`usleep(200)` poll. No timeout inflation. WAIT_S=12 is observation only.

Classifier elapsed: event36 waited=1 timestamp → `x-present-copy-wait/4` halt,
bounded 1500–4500 ms. Not wall-clock 2000.000.

reason=4 alone is insufficient. Identity must be exactly
`what=x-present-copy-wait reason=4`.

## Dedicated runner

Path: `evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-p1-8545b26.sh`

SHA256: `46c2289dcdddd518c2e4ecb99095e3991c640fa11e92149b83d8d79f20a16ba7`
Size: 24458 bytes

Does **not** modify `run-r7-one-cell-a07d66c.sh` or `run-r7-10-8545b26.sh`.

Only tuple accepted:

```
CELL_ID=r7-p1
FAULT=present-hold-complete
FIXTURE=present
WAIT_S=12
ROOT=.../runtime-8545b26
```

VALIDATE_ONLY=1 prints the immutable plan (adb=0 mkdir=0 activity=0 x3=0
holder_exec=0 fixture_exec=0 r7_p1_trigger=0 r7_p2=0 fault12_trigger=0) and
exits. No ADB, no mkdir of `runtime-8545b26/r7-p1`.

Live destination-exists REFUSE before mkdir / harness source.

Env (future live only):

```
TERMUX_X11_GATEA_PROTO=1
TERMUX_X11_GATEA_TELEMETRY=1
TERMUX_X11_GATEA_TEST_FAULT=present-hold-complete
TERMUX_X11_GATEA_TEST_ARM=1
```

No unrelated Gate A env. Exact `/proc/X3/environ` set equality.

Hard-bound candidate SHA / version / versionCode / package / Build ID as above.
Live dumpsys still checks package/versionName/versionCode only; APK SHA / signer
/ Build ID / CI / source SHA remain the outer device-grant profile.

This runner never installs.

## Classifier

Path: `scripts/classify_r7_p1_present_hold.py`

SHA256: `07de408bc0b316ce0ed7d0e60fd719b897319cf64b2b38c41d2ca1de7be33908`

Positive class: `EXPECTED_PRESENT_TIMEOUT`

Mandatory: event35 count=1 enum=12 side=2; CALLBACK 30 src=4 before 35;
renderer/Activity alive; last halt `x-present-copy-wait/4`; no peer HUP;
no target event34 / waited=0 / SUCCESS / CLIENT_OK; genuine elapsed window.

Negative classes: `PEER_DIED`, `WRONG_REASON4_IDENTITY`, `TARGET_COMPLETED`,
`NO_PRESENT_CALLBACK`, `NO_EVENT35`, `REPEATED_FAULT`, `WRONG_TERMINAL`,
`TRACE_INCOMPLETE`.

Wait-architecture mode: peer-dead HUP vs live-peer timeout remain distinct.
R7-10 construction (event35 src=10) labeled as Present timeout is product FAIL.

`reason4_globally_forbidden=NO`.

## Input tests / mock regressions / judge / wait-wake

`scripts/test_r7_p1_8545b26_runner.sh` **pass=30 fail=0**

Includes: correct tuple VALIDATE_ONLY; no mkdir; candidate bind; present ELF
identity; refuse a07d66c/fdfb1ce/7549e36 roots; refuse r7-10/r7-p2/r7-01;
refuse wrong fault/fixture/WAIT; dest-exists live refuse; extra args; missing
SERIAL; generic still REVIEW_REQUIRED; generic + r7-10 runners unmodified;
classifier 14/14; judge 16/16; wait-wake host binary PASS; legal r7-p1 absent.

Mandatory mocks (`test_classify_r7_p1_present_hold.py` 14/14):

| Mock | Class |
|---|---|
| CALLBACK30 + event35 + alive + ~2000 ms + `x-present-copy-wait/4` | EXPECTED_PRESENT_TIMEOUT / judge R7_PASS |
| CALLBACK30 + event35 + renderer dies + `x-hup/6` | PEER_DIED (not valid P1) |
| CALLBACK30 + event35 + alive + `x-direct-not-success/4` | WRONG_REASON4_IDENTITY FAIL |
| CALLBACK30 + event35 + event34 then timeout | TARGET_COMPLETED FAIL |
| CALLBACK30 + event35 + published fatal then later timeout | WRONG_TERMINAL (fatal wins) |
| wait-architecture peer dead + `x-hup/6` | WAIT_ARCHITECTURE_HUP |
| wait-architecture live + `x-present-copy-wait/4` | WAIT_ARCHITECTURE_TIMEOUT |

Frozen `judge-r7.py` unmodified. Host `test-judge-r7.py` **16/16 PASS**.

## ABI / timeout freeze

Unchanged on `8545b26` source (worktree clean):

| Item | Frozen |
|---|---|
| `sizeof(LorieGateAProtocol)` | 40 |
| `generationFatal` offset | 4 |
| protocolVersion | 1 |
| EVENT_MAX | 37 |
| COUNTER_MAX | 28 |
| fault enum 12 | `PRESENT_HOLD_COMPLETE` |
| Present wait | 2000 ms |
| CASE_LOOP / frame wait | 8 ms (`8000000L`) |

InitOutput.c SHA `97a7a704…3205`. lorie.h SHA `4863175f…a031`.
wait-wake header SHA `50b6a19a…b397`. renderer.cpp SHA `d7f0489d…aa63`.

## Tool hashes

See `hashes.txt` in this directory.

Dedicated runner `46c2289d…16ba7`. Classifier `07de408b…3908`.
Verifier `645af1d2…6726`. Generic `36d66f17…8ded` unmodified.
R7-10 runner `690a865d…54cd` unmodified. Judge `fba3c10f…cc17` unmodified.

## Historical evidence isolation

Not modified:

- `runtime-a07d66c/*` (r7-10 judge SHA `c816d6c1…eef5` frozen FAIL)
- `runtime-8545b26/r7-10/*` (judge SHA `bdd9cf8f…eb77` frozen PASS)

`runtime-8545b26/r7-p1` was **not created**.

## Device mutation audit

```
ADB install = 0
Activity = 0
X3 = 0
present fixture execution = 0
fault12 trigger = 0
runtime-8545b26/r7-p1 created = NO
Stable mutation = 0
HDMI mutation = 0
```

8545b26 remains INSTALLED. No new install this grant.

## Primary verdict

**R7_P1_8545B26_RUNNER_QUALIFIED**

Meaning: R7-P1 device cell remains **NOT RUN**; tooling is ready.
Not: R7-P1 PASS.

## State transition

```
8545b26 R7-10: PASS / FROZEN
R7-P1: NOT RUN / UNBLOCKED
R7 overall: IN PROGRESS 11/13
Production Gate A: BLOCKED
R8/R9/R10: NOT STARTED
```

## Recommended next action

Separate device grant: run exactly one fresh `runtime-8545b26/r7-p1`
`present-hold-complete` with `run-r7-p1-8545b26.sh`.
Do **not** execute P2. Do **not** retry r7-10.
Do **not** use the generic a07d66c runner.
