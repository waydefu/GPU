# Gate A P2 Artifact B / R7 support design freeze — 2026-09-16

```
STATUS: B-0 FROZEN by Sol High under the 2026-09-16 R7 execution contract
BASE: 0f1e54699d0b11a781f2c044fbc77505f8a53bd8 (frozen R6 qualification SHA)
WORKTREE: src/f8-ahb-gatea-r7
BRANCH: qualification/gatea-r7-20260916
R8–R10: NOT AUTHORIZED TO RUN
Gate H: HOLD
Production Gate A: BLOCKED
Stable :1 / HDMI: forbidden
```

Authority snapshot (phone Documents, SHA256
`c34c336297b971c81cc073dfb0c178f239389972b9f3992b0f7a381856fbb116`):
`GATE-A-R6檢查與R7-R10-GateH計畫書-20260915.md` in this directory.

This freeze does **not** mutate the R6 worktree or rewrite historical R6 evidence.

## PRE-EDIT VERDICT: READY

Exact R7 purpose, cells, fault-hook semantics, telemetry, and R6 invariants
are identified below. Remaining UNKNOWN items are listed and are not used as
assumptions.

## 1. What R7 proves

After a Present/direct GPU copy is **published**, every authorized injected
failure fail-stops. After event 35:

- no SEMANTIC_SUCCESS, RELOCK, REPAIR, ACK, PENDING_DEC, LEASE_RELEASE
- no later PUBLISH with serial > S
- no event 32
- Present cells: no event 34
- no D0a fallback / replay
- same generation does not continue normally
- X dies via fatal `_exit(127)`, not a crash signal

Unset env must leave normal R6 behavior unchanged.

R7 does **not** enable Production Gate A. R7 does **not** implement D-1=(b)
stall-vs-loss (that was an R6 G2 item; `0f1e546` still treats
`!lorieRendererAvailable()` as immediate wait failure). Folding D-1 into R7
would change product Present-wait behavior and is out of scope.

## 2. Mandatory R7 runtime cells (this authorization)

Run order (計畫書 §4.2): 04 → 05 → 01 → 02 → 03 → 06 → 07 → 08 → 09 → 11 →
10 → P1 → P2.

| Cell | env value | side | frozen terminal from **source** |
|---|---|---|---|
| R7-04 | `fbo-incomplete` | renderer | FATAL `r-gatea-DIRECT_LOOKUP_FAIL` reason=2 (`FAIL_DRAW`). **Conflict:** 計畫書 table says FAILED_QUIESCED; `consumeGateAComposite` return 3 currently shares the lookup-fail fatal. R7 does not reclassify. Distinguish from R7-01 by LOOKUP_OK then 35 then FBO return. |
| R7-05 | `post-draw-gl` | renderer | FAILED_QUIESCED via `firstFailed` DRAW; X `x-direct-not-success` reason=2 |
| R7-01 | `src-ready-miss` | renderer | FATAL `r-gatea-DIRECT_LOOKUP_FAIL` reason=2; event 9 LOOKUP_FAIL |
| R7-02 | `dst-ready-miss` | renderer | same what/reason; dst miss |
| R7-03 | `tuple-mismatch` | renderer | FATAL `r-gatea-direct-identity` reason=5 (`FAIL_PROTOCOL`). Table said GENERATION; consume-time identity mismatch in source is PROTOCOL. |
| R7-06 | `fence-create-fail` | renderer | FATAL `r-gatea-fence-create` reason=3 |
| R7-07 | `fence-timeout` | renderer | FATAL `r-gatea-fence-wait` reason=3; **no** `completedSerial >= S` |
| R7-08 | `renderer-fatal-pre-fence` | renderer | FATAL `r-test-fatal-pre-fence` reason=6 after CONSUME_DIRECT |
| R7-09 | `wrong-generation-frame` | X | FATAL `x-wrong-generation` reason=6 on first inbound Gate A frame |
| R7-11 | `serial-wrap` | X | FATAL `x-serial-wrap` reason=6; no `PUBLISH` with serial=0. Seed `gpuCopySerialCounter=UINT64_MAX` after 35 so the next `++` wraps. Table’s “few PUBLISH then wrap” is incompatible with the single-direct fixture; frozen oracle does not require those extra PUBLISH events. |
| R7-10 | `renderer-exit-after-consume` | renderer | renderer `_exit(127)` after CONSUME_DIRECT; X `x-hup` reason=6 |
| R7-P1 | `present-hold-complete` | renderer | skip COPY `completedSerial` publish; X `x-present-copy-wait` reason=4; event 34=0 |
| R7-P2 | `present-renderer-exit` | renderer | renderer `_exit(127)` after consuming a COPY slot; X `x-hup`; event 34=0 |

R7-12 / R7-13 / R7-14 remain in the **allow-list** (Artifact B is R7–R10
support) but **must not be executed** under this authorization.

| Hook (not run) | env value | frozen source what |
|---|---|---|
| R7-12 | `destroy-while-gpu-owned` | `x-destroy-in-lease` reason=7 |
| R7-13 | `close-while-lease` | `x-close-in-lease` reason=8 (already in `gateACloseGeneration`) |
| R7-14 | `stale-ready-replay` | `x-wrong-generation` reason=6 |

## 3. Fault hook

Env (X process only):

```text
TERMUX_X11_GATEA_TEST_FAULT=<exact cell>
TERMUX_X11_GATEA_TEST_ARM=1
```

Refuse startup (`x-test-fault-env` / `FAIL_PROTOCOL`) if any of:

- only one of FAULT/ARM is set
- cell not in the allow-list
- PROTO is not exact `1` or TELEMETRY is not exact `1`
- `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL` is set

Renderer **must not** `getenv` the fault. X publishes a 40-byte tail block on
`lorie_shared_server_state` after mmap:

```text
struct LorieGateATestFault {
    uint32_t magic;             /* 0x47374146 'G7AF' */
    uint32_t version;           /* 1 */
    uint32_t cell;              /* enum 1..16 */
    uint32_t armed;             /* 1 if valid pair */
    uint32_t consumed;          /* CAS 0→1 */
    uint32_t pad;
    uint64_t targetGeneration;  /* 0 = first matching site */
    uint64_t targetOrdinal;     /* 0 = first matching site */
};
sizeof == 40
offsetof(targetGeneration) == 24
```

Existing offsets (queue 168 / sideband 40 / direct 48 / telemetry) stay
unchanged. mmap uses `sizeof(*state)` on both X and renderer from the same APK.

One-shot: CAS `consumed` 0→1, **then** event 35, **then** the replacement.

Faults replace a result. No sleep/delay. Timeout cells withhold
`completedSerial` or take the existing fence-timeout branch.

Unset: `armed=0`; every site returns immediately after loading `armed`.

## 4. Events (append-only)

1–34 frozen. Event 32 remains uncalled.

| id | name | src | dst |
|---|---|---|---|
| 35 | `TEST_FAULT_FIRED` | cell enum | side (`1` X / `2` renderer) |
| 36 | `PRESENT_RETIRE` | waited 0/1 | dst buffer id (0 if root/NULL) |

Event 37 `LEASE_BIND` is **not** added (J-2 optional).

`LORIE_GATEA_EVENT_MAX == 37`. Counter ABI stays 28.

Event 36 is emitted in `present_gpu_copy_retire_or_fatal` **before** wait, so
a timeout fatal can still leave waited=1 in the ring.

## 5. SUMMARY + ring

Logcat tag `gatea-a1`:

```text
GATEA_SUMMARY where=<id> nonce=… generation=… nextSequence=… overflow=… firstFailed=… generationFatal=… fatalReason=… c0=… … c27=…
```

X also writes (Termux uid):

```text
/data/data/com.termux/files/usr/tmp/gatea-summary.txt
/data/data/com.termux/files/usr/tmp/gatea-ring.txt
```

Ring lines reuse the existing `GATEA_EVENT seq=…` format. Renderer file writes
are best-effort and may fail (APK uid); logcat + X HUP dump are the authority
for fatal cells.

Dump points: `gateAXFatal`, `gateARendererFatal`, `gateAFatalFromInput`,
`x-hup`, clean `lorieCloseScreen`, and renderer `_exit` cells before `_exit`.

## 6. Judge

New `judge-r7.py`. PASS requires 計畫書 §4.3. Host negatives first.

R6 `verify_r6_design_impl.py` still forbids `TEST_FAULT` and
`EVENT_MAX==35`. That verifier is **frozen against `0f1e546` only**. The R7
tree uses `verify_r7_support.py`. Ownership retirement tests still run on the
R7 tree.

## 7. R6 invariants preserved

- `present_gpu_copy_retire_or_fatal` remains the only Present ACK site
- completion watermark `T>=S` unchanged
- event 32 still unused
- exact pixels unchanged
- unarmed path must not ACK/release early
- R6 OOM env must not combine with R7 env

## 8. B-2 requalification on the new APK (before R7 cells)

計畫書 D-5: R1–R4 required; R5 + R6-D1 also. TEST env must be unset.
Additional: event 35 count = 0; `GATEA_SUMMARY` present on clean close.

If any of those FAIL: do not start R7 cells.

This execution contract authorizes Artifact B source + host + fork CI +
experimental install + the mandatory R7 cells. It does **not** authorize R8+.

## 9. UNKNOWN (not assumed)

- Whether Activity FD is readable (`run-as`) — R10 only
- Whether D-1=(b) will later change Present wait — not this artifact
- Exact client-seq binding of LEASE — still absent; not event 37
- Whether R7-04 should later become FAILED_QUIESCED — product change, not R7

## 10. Host implementation (2026-09-16)

Worktree `src/f8-ahb-gatea-r7` / `qualification/gatea-r7-20260916` contains Artifact B
source. Frozen R6 worktree `0f1e546` was not mutated.

Host evidence:

- `verify_r7_support.py` PASS
- `test-present-gpu-copy-retirement.py` PASS
- `test-judge-r7.py` 16/16 PASS
- `verify_r6_design_impl.py` on this tree FAIL as required (`EVENT_MAX==35` /
  no `TEST_FAULT`)
- NDK arm64 compile of `present_vblank.c` / `InitOutput.c` / `renderer.cpp` /
  `cmdentrypoint.cpp` rc=0 (existing warning fingerprint only)
- `xserver.patch` applies on submodule `65d790bd`

Runtime / CI / install / B-2 requal / R7 cells: not in this host packet.
Do not treat the installed R6 APK as R7-qualified. Stop before R8.
