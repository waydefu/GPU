# Gate A P2 R6-D2 — missing EVENT_COMPLETED serial S

Date: 2026-09-15

```text
ROOT CAUSE: PROVEN (source + retry1 logcat)
FIX SOURCE: COMMITTED 54ff35bd2e47a250c88b5c19391c22b0f6af5700
  branch qualification/gatea-r6-20260915 (base 9369553 / rollback 37d8393)
DEVICE APK: still 1.03.01-9369553-15.09.26 (CI 34926730189)
FORK PUSH / CI / INSTALL / NEW D2 CELL: HOLD — GATE-A-P2-R6-D2-HOLD-20260915.md
D2-OOM: NOT RUN
R7 / Production Gate A: NOT STARTED / BLOCKED
Stable / HDMI: UNTOUCHED
```

This packet binds the D2-INFLIGHT-retry1 FAIL, the official Present/XCB
text used for the fixture, the judge contract, and the renderer telemetry
fix. It does not rewrite frozen 9369553 cells.

Authority this supersedes for the D2 COMPLETED question only:

- `../p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md` “possible grants 1/2”
- `../p2-r3-xpump-runtime/runtime-9369553/r6-d2-inflight-retry1/FAIL-PUBLISH-BEFORE-COMPLETED-20260915.md`
  (cell FAIL remains; classification below)

## 1. Binding

| Item | Value |
|---|---|
| Device (installed) | `com.waydefu.x11gpu` `1.03.01-9369553-15.09.26` |
| Device HEAD / CI | `936955397619091b48c8e717f28b2cd187d79065` / **34926730189** |
| APK SHA256 | `02baccbfd745dffcaa62699452c386710d5a7cf1b63217ea293141e06d98af7f` |
| Build ID | `82136dd9ebd230b8bf6d655f334ac40e4be998a8` |
| Worktree | `/root/projects/GPU加速/src/f8-ahb-gatea-r6` |
| Local HEAD (fix) | `54ff35bd2e47a250c88b5c19391c22b0f6af5700` |
| Rollback SHA | `37d839323255b4830d657da3bcbf7f616bc78ad3` |
| Frozen control | `src/f8-ahb-gatea-a1` `88e3f17` |
| D1 PASS cell | `runtime-9369553/r6-d1-retry5/` X **16168** ELF `e74776f3…1197` |
| D2 FAIL cells (keep) | `r6-d2-inflight/` X 17596; `r6-d2-inflight-retry1/` X **20856** |

## 2. Two serial namespaces (do not mix)

| Namespace | Retry1 value | Who emits | Judge / fixture |
|---|---|---|---|
| PresentPixmap **client** serial | `1` | `xcb_present_pixmap(..., PRESENT_SERIAL, ...)` | PresentCompleteNotify.serial echoes this (`presentproto`) |
| Gate A **GPU** serial S | `6` | `lorieTryScheduleGpuCopy` → CALLBACK xop=4 | Judge `EVENT_COMPLETED` (event **14**) must **cover** S: `role==RENDERER`, same generation, `serial >= S` (batch watermark). Exact `== S` is **not** required after `54ff35b`. |

Retry1 ELF `ffce3910…b068` used Present options `ASYNC\|COPY` and client serial 1.
CALLBACK serial 6 is the GPU copy watermark, not the PresentPixmap serial.

Changing the **9369553** judge to `serial >= S` still FAILs retry1: the only
COMPLETED is serial **8** at seq 41, **after** PUBLISH serial 8 at seq 36,
and that APK never emits event 14 for Present 6. After `54ff35b`, a legal
legacy batch watermark is `COMPLETED serial=7` covering Present `S=6`; the
HOLD judge therefore uses `>= S` **and** requires the cover **before** later
direct LEASE/PUBLISH/SUCCESS.

## 3. Retry1 evidence (PROVEN)

Cell: `../p2-r3-xpump-runtime/runtime-9369553/r6-d2-inflight-retry1/`

```text
seq 19 PresentPixmap REQUEST
seq 20 CALLBACK Present xop=4 serial=6
seq 21 Composite REQUEST
seq 23 DIRECT_ADMIT_REJECT reason=1 serial=6
seq 26 later Composite REQUEST
seq 36 PUBLISH serial=8
seq 41 COMPLETED serial=8
seq 42 SUCCESS serial=8
```

| Claim | Label |
|---|---|
| Present CALLBACK before Composite (vs first inflight cell) | **PROVEN** |
| DIRECT_ADMIT_REJECT reason=1 | **PROVEN** |
| EVENT_COMPLETED serial=6 in follow logcat | **ABSENT** |
| Later Composite admitted (PUBLISH serial=8) | **PROVEN** |
| `completedSerial` advanced enough for quiescence | **INFERRED** from admission (`gateAQueueSemanticallyQuiescent` requires `completed==last`) |
| Present protocol CompleteNotify observed | **NOT INSTRUMENTED** on retry1 (fixture did not SelectInput) |

Judge (`judge-r6-design.py`):

```text
present_cb = first event 30 with src=XOP_PRESENT(4)
S = present_cb.serial
completed_i = first event 14 after present_cb with serial == S
FAIL if LEASE/PUBLISH/SUCCESS with serial > S in (present_cb, completed_i)
```

`EV_COMPLETED = 14` matches `LORIE_GATEA_EVENT_COMPLETED_SERIAL` in `lorie.h`
(enum after `FENCE_ERROR`).

## 4. Source root cause (PROVEN)

Present GPU copies are `LORIE_GPU_OP_COPY`. `applyPendingGpuCopiesLocked`
sets `out.gateASeen = 1` only on the **direct COMPOSITE** metadata path.

`present_execute.c` (~111–136) traces CALLBACK **when the copy is scheduled**,
then `queue_vblank` and **returns** (`gpu_copy_pending`). Dispatch continues.
That is why immediate Composite can REJECT (retry1 seq 23) while GPU work is
still in flight — design-correct for D2-INFLIGHT.

When the renderer later fences the legacy batch:

| Path | `9369553` behavior | `54ff35b` |
|---|---|---|
| `gateAFencePublishGateA` (`gateASeen`) | `PublishCompleted` + EVENT 14 | unchanged |
| `applyPendingGpuCopies` `!gateASeen` | `PublishCompleted` **only** | + `gateATraceLegacyCompleted` |
| `redrawLocked` `!gateASeen` | `PublishCompleted` **only** | + `gateATraceLegacyCompleted` |

`lorieGateATrace` no-ops unless `lorieGateATelemetryPublished()` (`lorie.h`
~1569–1576: bound nonce/generation and published enable word). D2 cells run
`TERMUX_X11_GATEA_TELEMETRY=1`, so the missing event is not “telemetry off”.

Admission of the later Composite uses **`completedSerial`**, not the trace
(`InitOutput.c` `gateAQueueSemanticallyQuiescent` ~2275–2295: `wi==ri` and
`completed==last`). So retry1’s later Composite is protocol-plausible
**post-quiescence**. The D2 FAIL is **observability**: event 14 never logged
for serial 6.

Fence wait / publish order / ABI / Gate A fence budget: **unchanged**.
`EGL_FOREVER` remains on the legacy path. Design §8 “not in scope:
`renderer.cpp` fence order” still holds; the expansion is **telemetry after
the existing `PublishCompleted`**.

Helper (worktree `renderer.cpp`):

- `gateATraceLegacyCompleted` ~937–947
- standalone publish ~1858–1859
- redraw publish ~2112–2114
- legacy `lastSrcId`/`lastDstId` filled at consume ~1798–1800

Static: `verify_r6_design_impl.py` → `R6_DESIGN_IMPL=PASS` on `54ff35b`.

## 5. Official / installed headers (bound 2026-09-15)

Stuck once on CompleteNotify wait + XGE delivery; used current official
Present text and the workstation XCB headers. GitLab `presentproto` /
`libxcb` raw pages returned 403 / Anubis; **cgit + local headers** are the
bind used here.

### 5.1 presentproto 1.0

- URL: https://cgit.freedesktop.org/xorg/proto/presentproto/tree/presentproto.txt
- Mirror of https://gitlab.freedesktop.org/xorg/proto/presentproto
- Blob: `fdaf658e23bd7015b5f400e68ebc0ec6382d214d`
- Title: “The Present Extension Version 1.0” 2013-6-6 Keith Packard

Quotes used (not blogs, not mailing-list patches as authority):

1. **PresentPixmap serial** is an arbitrary client value **returned in
   PresentCompleteNotify** so the client can associate event and request.
2. **PresentOptionAsync** + `target-msc <= current msc`: perform as soon as
   possible, not necessarily waiting for the next vblank.
3. **PresentOptionCopy**: pixmap is idle / idle-fence triggered as soon as
   the operation occurs (copy, not flip).
4. **After the presentation occurs**, PresentCompleteNotify with kind
   PresentCompleteKindPixmap is generated.
5. **PresentSelectInput** creates/modifies an event context for a window
   (`eventMask` includes PresentCompleteNotifyMask).
6. CompleteNotify is an **XGE** event (`type` 35); `serial` is the value from
   the generating PresentPixmap.

Workstation XCB matches:

| Symbol (`/usr/include/xcb/present.h`) | Value |
|---|---|
| `XCB_PRESENT_OPTION_ASYNC` | 1 |
| `XCB_PRESENT_OPTION_COPY` | 2 |
| `XCB_PRESENT_EVENT_COMPLETE_NOTIFY` | 1 |
| `XCB_PRESENT_EVENT_MASK_COMPLETE_NOTIFY` | 2 |

Packages: `libxcb1` / `libxcb-present0` / `-dev` **1.15-1ubuntu2** arm64.

### 5.2 libxcb special XGE queue

`/usr/include/xcb/xcb.h` (same 1.15):

- `xcb_register_for_special_xge(c, ext, eid, stamp)`
- `xcb_poll_for_special_event` / `xcb_wait_for_special_event`
- `xcb_unregister_for_special_event`

Fixture: `PresentSelectInput` + register XGE **before** PresentPixmap;
**do not** wait CompleteNotify before the racing Composite; wait **after**
that Composite, then later oracle Composite. Round-trip
`xcb_get_input_focus` in the poll loop so the socket is read into the
special queue (poll-only without a round-trip can sit on an empty XGE list).

`xcb_wait_for_special_event` is documented to block until one arrives; the
fixture uses a **2 s** monotonic poll instead of an unbounded wait (harness
watchdog is 45/60 s).

### 5.3 Why D1 retry4 lacked Present CALLBACK (already used, restated)

`present_execute.c` traces xop=4 only on the `lorieTryScheduleGpuCopy`
success path. `options=0` queues `target_msc = crtc_msc+1`; client
disconnect can cancel the vblank so `present_execute_copy` never runs the
GPU path. Official `ASYNC|COPY` is why D1-retry5 and D2-retry1 got CALLBACK.

## 6. Fixture (host, not in the APK repo)

Do not edit `patches/p_r6_cross_op.c`. Historical D2 ELFs stay in their cells.

| | SHA256 |
|---|---|
| retry1 source `6b7e8277…4ec8` | (cell) |
| retry1 ELF | `ffce391049cc17c86eadd243f52f8b875e91bd842849c3ea5bc76b0bf63ab068` |
| new source `patches/p_r6_d2_present.c` | `c4e8a680a457f54ba1d0c612c82fb692336b1e69b0276b02b2e7f7cd32a13c9a` |
| new ELF `fixtures/p_r6_d2_present` | `2ca0957fb373178d7e0163cfbe6ce9b01916b2a771b4e0fccacfc0c33bd168a3` |

`cc -O2 -o p_r6_d2_present p_r6_d2_present.c -lxcb -lxcb-render -lxcb-present` exit 0.

New ELF waits CompleteNotify **after** immediate Composite only. That is
option 1 (later oracle after Present protocol completion). It **cannot**
green the judge on APK `9369553`: event 14 for GPU serial S is still never
emitted. Option 1 is useful **after** `54ff35b` is installed.

## 7. Falsified / rejected alternatives

| Hypothesis | Result |
|---|---|
| Silent-retry D2-retry1 ELF on `9369553` | **FORBIDDEN** (same missing event 14) |
| Judge-only (`serial >= S`) on APK `9369553` | **REJECTED** — COMPLETED 8 still after PUBLISH 8; no event 14 for S |
| Judge `serial >= S` after `54ff35b` telemetry | **REQUIRED** watermark; still needs cover-before-later-direct (HOLD 2026-09-15) |
| Wait CompleteNotify **before** immediate Composite | **REJECTED** — would destroy the in-flight REJECT race |
| Change fence order / `EGL_FOREVER` / ABI / counters | **REJECTED** — not the defect |
| Patch C for ART JIT `0x4800xxxx` | **FORBIDDEN** (unrelated; D1-retry2) |
| Pump X clients inside `gateAWaitTerminal` | **FORBIDDEN** |

## 8. HOLD — do not push `54ff35b` as the next D2 APK

C telemetry is not on the device. **Do not** fork-push `54ff35b` for a new
D2 cell. Blocking issues and the corrected oracle:
`GATE-A-P2-R6-D2-HOLD-20260915.md`.

Host judge/bind were updated in that HOLD session. Present wait C is
**not** in this packet. A later grant must add wait/fail-stop, then a **new**
commit, then CI / `runtime-<newsha>/`.

Do not silent-retry `9369553` D2. STOP before R7.

## 9. Design-complete R6 status after this packet

| Cell | APK | Result |
|---|---|---|
| D1 | `9369553` | **PASS** retry5 (historical) |
| D2-INFLIGHT | `9369553` | **FAIL** retry1 (historical; root cause proven) |
| D2-OOM | — | **NOT RUN** |
| Design-complete R6 (all three on one installed APK) | — | **NOT PASS** |
