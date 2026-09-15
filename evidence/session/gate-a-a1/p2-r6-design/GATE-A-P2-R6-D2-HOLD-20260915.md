# Gate A P2 R6-D2 — HOLD (do not push `54ff35b`)

Date: 2026-09-15

```text
HOLD: do not fork-push 54ff35b, do not CI, do not install, do not run D2
DEVICE: still 1.03.01-9369553-15.09.26
LOCAL FIX HEAD: 54ff35bd2e47a250c88b5c19391c22b0f6af5700 (fork ahead 1, telemetry-only)
JUDGE / BIND / NEGATIVE TESTS: UPDATED this session (host only)
D2-OOM OWNERSHIP WAIT: DESIGN CHOSEN, C NOT IMPLEMENTED
R7 / Production Gate A: NOT STARTED / BLOCKED
Stable / HDMI: UNTOUCHED
```

User review 2026-09-15: overall design HOLD. `54ff35b` telemetry direction is
correct and small, but shipping it into a new D2 cell would likely false-FAIL
on batch watermark `serial == S`, and D2-OOM on current source can PASS while
dropping GPU pending refs too early.

This packet records the blocking issues, the corrected oracle, and what was
fixed on the host. It does **not** authorize Present ownership C, fork push,
or device tests.

## 1. Blocking issues (accepted)

### 1.1 HIGH — D2-OOM early ownership release

`lorieTryScheduleGpuCopy` takes extra refs and `gpuCopyPendingInc`
(`InitOutput.c` ~1802–1824). Post-schedule `queue_vblank` fail then:

1. `PRESENT_EARLY_ACK`
2. `lorieGpuCopyAck` (pending-- and extra ref release)
3. `present_pixmap_idle`

(`present_execute.c` ~132–153, `lorieGpuCopyAck` ~1864–1876).

CPU shared-lock is `lorieNeedsGpuLock` via pending (`InitOutput.c` ~3498–3539).
Zero pending while GPU still copies is an ownership hole. `present_pixmap_idle`
also tells the client the pixmap is reusable.

Conflicts with 20260913 R6 “Require no early ACK”
(`GATE-A-P2-RUNTIME-QUALIFICATION-DESIGN-20260913.md` ~359–366). The 20260915
design made `PRESENT_EARLY_ACK` a D2-OOM PASS premise — **withdrawn**.

`gateAQueueSemanticallyQuiescent` only blocks new **direct** leases. It does
not restore Present pending/lifecycle.

Chosen architecture (not coded): reuse existing `lorieGpuCopyWait(S, 2000)`
(`InitOutput.c` ~1879–1891, already `usleep(200)`, no X-client pump). On
post-schedule requeue fail:

```text
keep pending + extra refs
bounded wait completedSerial >= S
success → lorieGpuCopyAck + pixmap_idle
timeout / renderer loss → fail-stop, do not return uncertain ownership
```

OOM cell expectation becomes:

```text
PRESENT CALLBACK serial=S
  < COMPLETED cover (renderer, same generation, serial>=S)
  < ACK / idle
  < second Composite REQUEST_ARRIVED
```

No `DIRECT_ADMIT_REJECT`. No `PRESENT_EARLY_ACK`. Second request stays in the
client socket until Present is terminal. A deferred-retirement queue is the
larger alternative; not chosen.

### 1.2 HIGH — judge could PASS with no COMPLETED

Old `judge-r6-design.py` used `until = completed_i or len(events)`. If there
was CALLBACK + REJECT and no later LEASE/PUBLISH/SUCCESS, missing COMPLETED
still printed `R6_D2_PASS`. Role and generation were not checked.

### 1.3 HIGH — `serial == S` vs batch watermark

Renderer publishes `out.lastSerial` once per drained batch
(`renderer.cpp` drain ~1573–1809; legacy complete ~1858–1859 / ~2112–2114).
`lorieGpuCopyIsDone` is already `completedSerial >= serial`.

retry1 later used software `Gcomp FDCLONE`/`RECT` then direct serial 8.
Present 6 and a legacy 7 can complete as watermark 7. Judge must accept
`serial >= S` with `role==RENDERER` and `generation==Present CALLBACK`.

The earlier claim “`>= S` still FAILs retry1” was for APK `9369553` with
**no** legacy event 14. After `54ff35b`, `>= S` is required semantics.

### 1.4 MEDIUM — logcat line order ≠ telemetry seq

`lorieGateATrace` fetch-adds `seq` then `__android_log_print`. X and renderer
are different threads. Judge now sorts by `seq`, rejects duplicates, rejects
gaps unless `gatea-ring.txt` fills them. Device ring dump is **still absent**;
a gap is FAIL (no silent-retry).

### 1.5 MEDIUM — harness 9369553 hard-bind

`run-r6-design.sh` now sources `r6-design-bind.sh`: frozen 9369553 allow-list;
new `runtime-<sha>/r6-d2-*` requires `EXPECT_VERSION`; default new D2 ELF
`2ca0957f…68a3`. **D2-OOM under `runtime-9369553/` is refused.** Negative
tests in `test-r6-design-bind.sh`. Device 512-ring dump is still **not**
wired in the harness; a `seq` gap without `gatea-ring.txt` is FAIL.

## 2. Host verification this session

```text
python3 test-judge-r6-design.py  → 15 tests OK
  false-green no COMPLETED          FAIL (required)
  wrong generation COMPLETED        FAIL
  X-role COMPLETED                  FAIL
  watermark serial 7 covers S=6     PASS
  publish before watermark          FAIL
  logcat lines reversed, seq ok     PASS
  duplicate seq                     FAIL
  gap, no ring                      FAIL
  gap filled by gatea-ring.txt      PASS
  pixels without later SUCCESS      FAIL
  OOM EARLY_ACK                     FAIL
  OOM wait-shape                    PASS
  historical r6-d1-retry5           PASS
  historical r6-d2-inflight-retry1  FAIL (cover after PUBLISH 8)
bash test-r6-design-bind.sh        → BIND_NEG=PASS
bash -n run-r6-design.sh r6-design-bind.sh  → 0
```

No ADB, no install, no fork push, no Present C.

## 3. Corrected D2 oracle (design)

### D2-INFLIGHT

```text
PRESENT_CALLBACK generation=G serial=S
  < REJECT reason=1 generation=G
  < COMPLETED role=RENDERER generation=G serial>=S
  < later direct SUCCESS generation=G serial>S
```

Cover must exist. No LEASE/PUBLISH/SUCCESS with serial>S before cover.
Software-fallback pixels alone are not PASS.

### D2-OOM (after a future ownership commit)

Superseded by `.cursor/skills/gate-a-r6-design-review/references/R6-D2-REVIEW-20260915.md`.
Simplified “cover then later REQUEST” is **not** sufficient.

```text
PRESENT REQUEST(clientSeq=C)
  < PRESENT CALLBACK(C, G, S)
PRESENT CALLBACK < PRESENT_REQUEUE_FAILED(G,S)
PRESENT CALLBACK < COMPLETED(role=RENDERER, G, T>=S)
max(REQUEUE_FAILED, COMPLETED) < PRESENT_ACK_AFTER_COMPLETED(G,S)
ACK_AFTER_COMPLETED < later target Composite REQUEST/CALLBACK
later target direct SUCCESS G, serial>S, matching destination
PRESENT_EARLY_ACK → FAIL
```

New event numbers and the exported `lorieGpuCopyWaitForPresentOrFatal`
wrapper need an explicit architecture grant. Do not repurpose event 32.

## 4. Next (needs a new explicit grant)

Host remaining (skill review; still no C): OOM branch/ACK markers in the
judge once events exist; later SUCCESS on target pair; `seq` prefix `0..max`;
anchored runtime SHA vs `EXPECT_VERSION`. Then architecture grant:

1. C: keep pending; exported wait-or-fatal; append-only REQUEUE_FAILED and
   ACK_AFTER_COMPLETED; delete early-ACK PASS. Keep `54ff35b` telemetry.
2. Static verifier: wait-or-fatal before Ack, Ack before idle.
3. Then fork push / CI / experimental install / `runtime-<newsha>/` cells.
4. STOP before R7. Do not silent-retry `9369553` D2.

Do **not** push `54ff35b` alone. This HOLD is not C authorization.

## 5. Errata 2026-09-15 22:00 — writer lane exists, this HOLD is historical

The header `D2-OOM OWNERSHIP WAIT: DESIGN CHOSEN, C NOT IMPLEMENTED` described
the 15:29 HOLD. Later the same day:

- `lorieGpuCopyWaitForPresentOrFatal` shipped on installed `95e6f96`.
- `present_gpu_copy_retire_or_fatal` exists uncommitted on
  `src/f8-ahb-gatea-r6-retire`.
- Host judge is dual-branch; lease serial=0; OOM SUCCESS after later callback.

This file stays as the historical HOLD for `54ff35b`. Current planning status
is `PLANNER-BRIEF-20260915.md`. Do not push the writer tree without a new
independent review. Do not start R7.
