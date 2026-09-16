# Gate A P2 R7-04 fatal-propagation repair — 2026-09-16

Source RCA + semantic repair for historical R7-04 FAIL on `7549e36`.
**No device install. No R7-04 rerun. Judge and contract unchanged.**

## Verdict (source/host)

Repair SHA **`fdfb1ce44b429897eda17c43bf33fbd37afe67f3`** is SOURCE/HOST verified
and CI **35103216566** ARTIFACT QUALIFIED. Device remains **`7549e36` INSTALLED**.
New candidate is **NOT INSTALLED**. Historical R7 stays **BLOCKED**.
Production Gate A stays **BLOCKED**.

## Frozen authority (unchanged)

| Item | Status |
|---|---|
| R6 `0f1e546` | PASS / frozen |
| RCA-1 `0d72332` | FIXED / DEVICE-PROVEN |
| CASE_LOOP `7549e36` | DEVICE-VALIDATED (parent of this repair) |
| B-2 `runtime-7549e36/b2-requalification-02/` | PASS |
| Historical R7-04 on `7549e36` | valid FAIL `halt_mismatch` (not INVALID) |
| R7-04 expected last halt | `r-gatea-DIRECT_LOOKUP_FAIL` reason=2 |
| `judge-r7.py` | unmodified; old evidence still FAILs |
| EXA wait | 2000 ms |
| CASE_LOOP idle recheck | 8 ms CLOCK_MONOTONIC |
| ABI | no size/layout/enum/event change |

## Historical R7-04 observation (`7549e36`, not rewritten)

- Selector `fbo-incomplete`, arm 1, `p_r3_single_direct`, X **31122**
- Env exactly `PROTO=1 TELEMETRY=1 TEST_FAULT=fbo-incomplete TEST_ARM=1`
- Serial **5**; event 35 seq=31 src=4 dst=2 once after LOOKUP_OK
- Renderer halt `GATEA_FATAL_HALT what=r-gatea-DIRECT_LOOKUP_FAIL reason=2`
- X halt 3 ms later `GATEA_FATAL_HALT what=x-direct-not-success reason=4`
- SUMMARY already `generationFatal=2 fatalReason=2` on both dumps
- Forbidden success: Gcomp Done=0, ACK=0, event 32=0, later PUBLISH=0
- Frozen judge last-halt → `R7_FAIL halt_mismatch`

Re-ran frozen `judge-r7.py` against
`runtime-7549e36/r7-qualification-01/r7-04/logcat-follow.txt` after this
repair: still **`R7_FAIL halt_mismatch what=x-direct-not-success reason=4`**.

## Source RCA (exact)

1. **Fault fires** in `Renderer::consumeGateAComposite` after LOOKUP_OK:
   `lorieGateATestFaultConsume(..., LORIE_GATEA_TEST_FBO_INCOMPLETE)` returns
   true → `return 3` (`renderer.cpp`).
2. **Caller maps return ≠ 0 to FATAL DRAW**:
   `gateARendererFatal(..., "r-gatea-DIRECT_LOOKUP_FAIL", LORIE_GATEA_FAIL_DRAW=2, serial, ...)`.
3. **`gateARendererFatal`** does `lorieGateAPublishFatal(&st->gateA, 2)`
   (sticky `generationFatal` CAS, first wins), event 16, SUMMARY, then
   `lorieGateAFatalHalt("r-gatea-DIRECT_LOOKUP_FAIL", 2)` and `_exit(127)`.
   Renderer process is dead. Shared `generationFatal` remains **2**.
4. **X `gateADoneDirect`** waits `gateAWaitTerminal(lastSerial)`.
   `lorieGateADeriveResult` sees `fatal != 0` → `LORIE_GATEA_RESULT_FATAL=3`.
5. **Pre-repair classification** (the defect):
   ```
   reason = (r == FAILED_QUIESCED) ? firstFailureCode : FAIL_TIMEOUT;
   if (reason == 0) reason = FAIL_TIMEOUT;
   gateAXFatal("x-direct-not-success", reason, serial);
   ```
   `RESULT_FATAL` is not QUIESCED, so reason is **hardcoded `LORIE_GATEA_FAIL_TIMEOUT=4`**.
6. **`gateAXFatal` always emitted a halt** with the *argument* reason.
   `PublishFatal(4)` loses the CAS (`generationFatal` stays 2), but
   `lorieGateAFatalHalt("x-direct-not-success", 4)` still logs. Judge uses
   **last** `GATEA_FATAL_HALT` → mismatch.
7. Authoritative identity **was already available to X** via
   `lorieGateAObserveFatal(&st->gateA)` / `generationFatal`. No ABI gap.
8. The second X halt is **destructive to qualification identity**, not
   required for fail-stop: success/ACK/Done were already skipped; X only
   needed to terminate without a conflicting halt. Genuine timeout
   (`publishedFatal==0`) may still use reason 4.

R7-05 `FAILED_QUIESCED` is a different `DeriveResult` arm (`firstFailed`
with `generationFatal==0`) and still needs `x-direct-not-success` reason=2.

## Repair (narrow, no ABI)

Preferred hierarchy: **use existing sticky `generationFatal`**.

1. `lorieGateAClassifyDirectDone` (`lorie_gatea_done_class.h`):
   - SUCCESS → success path
   - QUIESCED → firstFailureCode (or TIMEOUT if code word is 0)
   - FATAL + published ≠ 0 → PRESERVE published reason (R7-04: 2)
   - FATAL + published == 0 → TIMEOUT 4
   - never maps FATAL onto SUCCESS
2. `gateADoneDirect` uses the classifier; non-SUCCESS still calls
   `gateAXFatal("x-direct-not-success", reason, serial)` (QUIESCED / genuine
   timeout). PRESERVE reason is the published fatal; `gateAXFatal` then
   refuses to emit a second halt.
3. `gateAXFatal`: if `ObserveFatal() != 0`, dump `x-observe-fatal` and
   `_exit(127)` **without** `GATEA_FATAL_HALT`. Fresh fatals still publish
   and halt.

Fail-stop of the success path is unchanged: non-SUCCESS never reaches
relock / repair / ACK / pending-- / lease release / Gcomp Done.

2000 ms `gateAWaitTerminal` / `lorieGpuCopyWait(..., 2000)` unchanged.
8 ms CASE_LOOP cap unchanged. Test-fault default-off unchanged.

## Cross-consumer audit

| Consumer | Same anti-pattern? | Action |
|---|---|---|
| `gateADoneDirect` | SAME BUG | classifier |
| `gateAXFatal` | SAME family (always halt) | preserve if published |
| `lorieGpuCopyWaitForPresentOrFatal` | related: timeout → `gateAXFatal` TIMEOUT; would overwrite if published | wait unchanged; preserve covers published case. No speculative Present rewrite. |
| `lorieGpuCopyWaitForCompositeOrFatal` | related, same helper | wait unchanged; preserve covers published case |
| Copy/Solid Done | NOT APPLICABLE unless they share `gateAXFatal` after a published fatal | no opportunistic timeout cleanup |
| `gateAWaitForReply` | related: `gateAXFatal(what, publishedFatal)` used to emit a second halt with a different `what` | preserve skips the extra halt |
| `lorieGateADeriveResult` | SAFE BY DESIGN (fatal first) | none |
| `cmdentrypoint` `x-hup` | NOT APPLICABLE (R7-10; no PublishFatal) | none |

## ABI

**NO ABI CHANGE.** `sizeof(LorieGateAProtocol)==40`, offsets, event max 37,
counter max 28, mmap `sizeof(*state)`, protocol version, test-fault 40-byte
block all unchanged.

## Diff

```text
worktree: src/f8-ahb-gatea-case-loop
branch:   fix/gatea-r7-fatal-propagation-20260916
parent:   7549e3667ec03b8b5e50d2e5befe03065840bbd9
new SHA:  fdfb1ce44b429897eda17c43bf33fbd37afe67f3
```

Files:

- `lorie/src/main/cpp/lorie/lorie_gatea_done_class.h` (new)
- `lorie/src/main/cpp/lorie/lorie.h` (include classifier)
- `lorie/src/main/cpp/lorie/InitOutput.c` (`gateAXFatal` + `gateADoneDirect`)
- `scripts/verify_r7_fatal_propagation.py` (new)
- `scripts/test_gatea_direct_done_class.c` (new)

## Host/static verification (this task)

| Check | Result |
|---|---|
| `verify_r7_fatal_propagation.py` | PASS |
| `verify_exa_composite_wait.py` | PASS |
| `verify_case_loop_wakeup.py` | PASS |
| host `test_gatea_direct_done_class` | PASS (A/B/C/D) |
| UBSan of that host test | PASS |
| ASan of that host test | NOT RUN — PRoot ASan `kSpaceBeg` mmap CHECK failed |
| TSan | NOT RUN — no new concurrent memory access; PRoot mapping historically fatal |
| `test-judge-r7.py` | 16/16 PASS (judge unmodified) |
| historical `judge-r7.py` on `7549e36` r7-04 follow | FAIL `halt_mismatch` (required) |
| `verify_r7_support.py` on this worktree | FileNotFound `xserver/present/present_vblank.c` (submodule not populated) |
| `verify_r7_support.py` proxy (this lorie + patched present from `a7528bd`) | PASS |
| NDK aarch64 clang compile of classifier | PASS |
| CASE_LOOP host wakeup `fixed` | PASS waited_ms=10 |
| `git diff --check` | PASS |
| fork CI `35103216566` | success; headSha `fdfb1ce`; Nightly skipped |
| APK SHA256 | `5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c` |
| Build ID | `1d6bf3cd0eb06d12804e690679211ee7f34f998e` (embedded == unstripped) |
| signer | `b6da0148…ee5e1` continuity PASS |
| package | `com.waydefu.x11gpu` `1.03.01-fdfb1ce-16.09.26` |

## Device

New repair candidate is **NOT INSTALLED**.
No runtime qualification was executed in this task.
Device remains `7549e36` unless independently changed outside this task.
