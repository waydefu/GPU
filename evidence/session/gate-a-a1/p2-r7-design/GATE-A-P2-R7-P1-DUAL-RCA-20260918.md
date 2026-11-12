# Gate A P2 R7-P1 dual RCA — 2026-09-18

Frozen abb27a65 device verdict remains
**`R7_P1_ABB27A65_QUALIFICATION_INVALID`**.
This packet does **not** rewrite it.

Evidence directory `runtime-abb27a65/r7-p1/` is immutable.
Historical `runtime-8545b26/r7-p1/` remains INVALID `NO_PRESENT_CALLBACK`.

```
RCA-A: P1_LIVENESS_PROBE_RCA_PROVEN
RCA-B: P1_COMPLETION_RCA_PROVEN_HIGH_WATERMARK
```

The two questions are independent. Do not merge them.

Worktree bind at RCA time:

| Field | Value |
|---|---|
| worktree | `src/f8-ahb-gatea-r7-p1-arm` |
| HEAD | `abb27a65b029b16837fe178624a85ac18a4ba005` |
| parent | `8545b26b308aa60b05685f48560285350e22ee8d` |
| frozen cell | `runtime-abb27a65/r7-p1/` X **19686** Activity **19659** |

---

## RCA-A — false Activity liveness probe

### Claim

`test -e /proc/$ACT_PID` on the workstation cannot observe an Android
Activity PID. The abb27a65 P1 runner used that host test as death, so
the classifier returned `PEER_DIED` / `runner_invalid=YES` while ADB
still showed the Activity alive.

### Direct evidence (frozen cell, not re-run)

| Probe | Result |
|---|---|
| host `renderer-liveness.txt` | every WAIT_S sample `activity=ABSENT`; `renderer_alive_during=0` |
| host `/proc/19659` during wait | ABSENT |
| ADB `ps -A` at pre-cleanup | `activity_pre_cleanup=ALIVE expected_pid=19659` |
| X 19686 | `X3_STILL_ALIVE elapsed=12` |
| fixture | `CLIENT_OK` |
| GATEA_FATAL_HALT | NONE |

Classifier `classify_r7_p1_cell(..., renderer_alive=0)` returns `PEER_DIED`
before it can consider `activity_pre_cleanup=ALIVE`.

### Exact host `/proc` user

`run-r7-p1-abb27a65.sh` wait loop:

```text
if [ -n "${ACT_PID:-}" ] && [ -d "/proc/$ACT_PID" ] && [ -d "/proc/$X3" ]; then
  RENDERER_ALIVE_DURING=1
```

That is workstation `/proc`, not Android `/proc`. Later pre-cleanup
correctly uses `ADB shell "ps -A"` and saw ALIVE. The classifier was
fed the host-loop bit, not the ADB bit.

### Why host `/proc` cannot see the Android PID

Live workstation `/proc` mount (2026-09-18, PRoot Ubuntu):

```text
proc /proc proc rw,relatime,gid=3009,hidepid=invisible
```

`hidepid=invisible` hides other-UID `/proc/<pid>` from this user.
The experimental Activity is an Android app UID (`u0_a503`).
PRoot/Termux X3 is a same-user child, so `/proc/$X3` works.

Live contrast (not a device retry; zygote/system_server only):

| PID | identity | host `/proc` | `adb shell test -d /proc/$PID` |
|---|---|---|---|
| 1822 | zygote64 | ABSENT | EXISTS |
| 3471 | system_server | ABSENT | EXISTS |

Frozen Activity 19659 matches the same pattern.

### Authoritative future probe

```text
adb -H 127.0.0.1 -P 5038 -s "$SERIAL" shell test -d /proc/$ACT_PID
adb shell ps -A   # package + PID identity
```

Optional: `/proc/$PID/status`, `/proc/$PID/task/$TID` via ADB.

The runner must bind `activity_alive_during_wait=true|false` from that
device evidence. The classifier must not infer Android Activity death
from workstation `/proc`.

X3 may still use host `/proc/$X3` because X is a same-user process.

### Verdict

**`P1_LIVENESS_PROBE_RCA_PROVEN`**

This does **not** make the frozen cell a PASS. Construction/evidence
was INVALID. Product behavior on that cell is a separate question
(RCA-B) and does not rewrite `PEER_DIED`.

---

## RCA-B — Present completed after target fault12

### Claim

Fault12 consumed Present serial 7 and withheld that serial's
`completedSerial` publication, but X still treated serial 7 as done
because a later unrelated GPU copy published `completedSerial=8` and
`lorieGpuCopyIsDone` is a high-watermark `>=`.

### Frozen trace (immutable)

| seq | event | serial | src | dst | meaning |
|---|---|---|---|---|---|
| 54 | 30 CALLBACK | 7 | 4 | 28 | Present target |
| 56 | 35 TEST_FAULT | 7 | 12 | 2 | enum12 side=2 consume |
| 57 | 30 CALLBACK | 0 | 3 | 29 | Composite xop (no GPU serial yet) |
| 58 | 31 DIRECT_ADMIT_REJECT | 7 | 1 | 5 | reject NOT_QUIESCENT |
| 59 | 14 COMPLETED_SERIAL | 8 | 10 | 5 | later legacy completion |
| 61 | 36 PRESENT_RETIRE | 7 | 0 | 0 | waited=0 |

Same-millisecond renderer log between seq 56 and 59:

```text
Gcomp RECT ... srcTex=7 dstTex=4 ... op=2
GATEA_EVENT seq=59 role=2 event=14 ... serial=8 src=10 dst=5
Gcomp Done
GATEA_EVENT seq=61 ... event=36 serial=7 src=0
```

There **is** a later serial `>7` before event36: serial **8**.
The high-watermark hypothesis is therefore eligible. It is not
rejected for lack of a later serial.

Startup CopyArea serials 1–5 completed as event14 **before** CALLBACK
src=4. No event35 on those CopyAreas. Target arm construction
succeeded. RCA-B is not an early-CopyArea miss.

### Event14 authority

`LORIE_GATEA_EVENT_COMPLETED_SERIAL = 14` in `lorie.h`.

Producer of seq=59: renderer role=2, `gateATraceLegacyCompleted` after
`lorieGateAPublishCompleted(..., 8)` on the legacy `!gateASeen` path.
Not Gate A SUCCESS (event17). Not Present completion of serial 7
(there is **no** event14 serial=7 after event35).

Event14 serial=8 is after event35 serial=7. Different target
(src=10 dst=5, Composite FD clone id=10). Same generation=1.

### X completion predicate (abb27a65)

`InitOutput.c` `lorieGpuCopyIsDone`:

```c
return lorieGateAObserveCompleted(&pvfb->state->gpuCopyQueue.completedSerial) >= serial;
```

`lorieGpuCopyWait` polls that predicate for 2000 ms.
`lorieGpuCopyWaitForPresentOrFatal` uses that wait.

`xserver.patch` `present_gpu_copy_retire_or_fatal`:

```c
waited = (serial != 0 && lorieGpuCopyIsDone(serial)) ? 0 : 1;
lorieGateATracePresentRetire(serial, dstId, waited);
if (serial == 0 || !lorieGpuCopyIsDone(serial))
    lorieGpuCopyWaitForPresentOrFatal(serial);
```

Event36 src=0 is `waited=0`: IsDone(7) was already true at helper
entry. Wait is skipped. ACK / CompleteNotify / CLIENT_OK follow.
That matches the frozen fixture.

`lorieGateAPublishCompleted` is a store, not a max. Publishing 8
replaces the withheld 7.

### Fault12 withhold path (abb27a65)

Both renderer writers of `completedSerial` for legacy COPY:

1. `Renderer::applyPendingGpuCopies` — consume cell 12 on
   `out.lastSerial`, then `return` **before**
   `lorieGateAPublishCompleted` and **before** `notifyGpuCopyDone`.
2. `Renderer::redrawLocked` — same consume, then `return` before
   publish.

Frozen consume is the applyPending path (`rendererApplyPendingGpuCopies`
immediately before event35 seq=56 serial=7).

Gate A direct `gateAFencePublishGateA` also publishes completedSerial
(`renderer.cpp` ~964) but Present/COPY keep `gateASeen=0`, so that
writer did not run for serial 7.

### How serial 8 covered 7

After withhold of 7, Composite could not admit Gate A direct
(event31 reject code 1 = `LORIE_GATEA_REJECT_NOT_QUIESCENT` because
completed != last). Fallback FD clone scheduled a new GPU copy.
Renderer then published event14 serial=8. X IsDone(7) became
`8 >= 7`. Present helper entered with waited=0.

Source comment already recorded this watermark class of bug
(`gateATraceLegacyCompleted`, Present serial 6 vs later PUBLISH 8).

### Hypothesis status

Required for PROVEN:

- frozen later serial `>7` before event36 — **yes, serial 8**
- exact source path that later publication covers 7 — **yes,
  PublishCompleted(8) + IsDone `>=`**
- fault12 skipped publication of serial 7 — **yes, consume then return**

Not an alternate Present completion path. Event14 serial=7 after
event35 does not exist. Event36 waited=0 is helper-entry after the
watermark already covered 7.

### Qualification contract (unchanged)

Frozen R7-P1 still requires:

CALLBACK30 src=4 → event35 enum12 side=2 → target completion withheld
→ renderer stays alive → genuine 2000 ms Present wait →
`x-present-copy-wait/4`.

Judge must **not** accept waited=0 / CLIENT_OK / target completion.

### P2 impact (not executed)

Cell 13 `_exit(127)` after matching consume. High-watermark bypass
does not apply once the renderer process is dead. Liveness tooling
still matters for evidence, not for this completion predicate.
Enum13 remains Present-bound (startup CopyArea cannot consume).

### Verdict

**`P1_COMPLETION_RCA_PROVEN_HIGH_WATERMARK`**

Repair must be test-only / cell-12-only: while the consumed hold
target S is active, `lorieGpuCopyIsDone(S)` stays false even if a
later T>S stores `completedSerial=T`. Production unarmed path stays
`completedSerial >= serial`. Do not redesign production completion.
Do not change judge / timeout / ABI.
