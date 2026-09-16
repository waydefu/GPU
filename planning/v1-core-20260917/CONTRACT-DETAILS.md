# Construction details and shared execution profiles

This file is **PROPOSED execution organization** of FROZEN Axx contracts. All profiles referenced by packets are normative parts of those packets, not permission. Paths are repository-relative unless starting `/root/projects/GPU加速`. Runtime commands are for a later authorized F8/Termux/PRoot session, **not the Windows planning host**. Nothing here has been executed on device by this PR.

## R7 cell matrix

Every row: exact X env `TERMUX_X11_GATEA_PROTO=1`, `TERMUX_X11_GATEA_TELEMETRY=1`, `TERMUX_X11_GATEA_TEST_ARM=1`, `TERMUX_X11_GATEA_TEST_FAULT=<selector>`; no other Gate A env. One fresh X and **one fixture invocation**, no repeat. Global judge requirements remain identical across rows (A04/A05). Event 35 carries `src=cell enum`, `dst=side`, `role=side` (1 X, 2 renderer), matching generation.

| Packet | Cell / selector | enum / side | Fixture argument | Construction before 35 (event IDs) | Expected final `GATEA_FATAL_HALT what` / reason | Additional oracle |
|---|---|---|---|---|---|---|
| NEXT-001 | R7-05 `post-draw-gl` | 5 / 2 | direct | PUBLISH(6) → DRAW(10) | `x-direct-not-success` / 2 | FAILED_QUIESCED; not reason=4; renderer need not exit until cleanup |
| NEXT-002 | R7-01 `src-ready-miss` | 1 / 2 | direct | PUBLISH(6) → CONSUME_DIRECT(7) | `r-gatea-DIRECT_LOOKUP_FAIL` / 2 | LOOKUP_FAIL(9), no legacy fallback |
| NEXT-003 | R7-02 `dst-ready-miss` | 2 / 2 | direct | 6 → 7 | `r-gatea-DIRECT_LOOKUP_FAIL` / 2 | destination lookup failure, no legacy fallback |
| NEXT-004 | R7-03 `tuple-mismatch` | 3 / 2 | direct | 6 → 7 | `r-gatea-direct-identity` / 5 | PROTOCOL reason, not older plan's GENERATION |
| NEXT-005 | R7-06 `fence-create-fail` | 6 / 2 | direct | 6 → DRAW(10) | `r-gatea-fence-create` / 3 | no semantic success |
| NEXT-006 | R7-07 `fence-timeout` | 7 / 2 | direct | 6 → 10 | `r-gatea-fence-wait` / 3 | no COMPLETED(14) covering `S` after injection |
| NEXT-007 | R7-08 `renderer-fatal-pre-fence` | 8 / 2 | direct | 6 → 7 | `r-test-fatal-pre-fence` / 6 | injected renderer FATAL before fence |
| NEXT-008 | R7-09 `wrong-generation-frame` | 9 / 1 | direct | first inbound Gate A frame; no publish prerequisite | `x-wrong-generation` / 6 | may fail during READY setup; don't require GetImage success |
| NEXT-009 | R7-11 `serial-wrap` | 11 / 1 | direct | seed after 35; no prior PUBLISH requirement | `x-serial-wrap` / 6 | no PUBLISH serial=0; no demand for “several earlier publishes” |
| NEXT-010 | R7-10 `renderer-exit-after-consume` | 10 / 2 | direct | 6 → 7 | `x-hup` / 6 | renderer `_exit(127)` then X HUP containment |
| NEXT-011 | R7-P1 `present-hold-complete` | 12 / 2 | present | CALLBACK(30), `src=4` | `x-present-copy-wait` / 4 | withhold COPY completion; no event34 or idle/CompleteNotify for target; event36 may show waited=1 |
| NEXT-012 | R7-P2 `present-renderer-exit` | 13 / 2 | present | CALLBACK(30), `src=4` | `x-hup` / 6 | renderer dies after COPY consume; no event34/ACK |

Direct fixture = `evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_r3_single_direct`; present = same directory `p_r6_d2_present inflight`. Holder = `p_b3a_hold`. Hash exact ELF bytes from pinned Git (not executable name only). Present fixture source is `patches/p_r6_d2_present.c`; direct fixture source is not shipped here, so bind shipped ELF/provenance and stop if missing. Expected process end in all rows: X ceases by fatal path within frozen runner `WAIT_S=12`; no SIGSEGV/SIGILL/SIGABRT. Fixture errors following X death are expected, not standalone FAIL/PASS. Renderer death itself is required for exit cells; other cells may leave Activity alive until cleanup.

FROZEN global forbidden set after 35: SEMANTIC_SUCCESS(17), RELOCK_SRC(18), RELOCK_DST(19), REPAIR(20), ACK(21), PENDING_DEC(22), LEASE_RELEASE(23); no later PUBLISH serial>S; event32 anywhere forbidden; Present event34 anywhere forbidden. No D0a fallback/replay, `Gcomp Done`, or normal same-generation continuation. The judge's role/generation checks are narrower than the prose's full transaction-binding claim: record matched S/src/dst and inspect this independently. Do not edit the frozen judge to conceal a mismatch.

R7-12/13/14 excluded from the R7 mandatory batch. Later R8-P1 uses `destroy-while-gpu-owned` enum14/side1, fatal `x-destroy-in-lease`/7. R8-P2 uses `close-while-lease` enum15/side1, fatal `x-close-in-lease`/8. R9-F1 uses `stale-ready-replay` enum16/side2, fatal `x-wrong-generation`/6. Existing judge permits these selectors, but a dedicated reviewed later-stage harness is required.

## PROFILE-R7 — exact later execution

### Read-only outer preflight (required before runner)

1. Read A01/A02/A04 and applicable packet. Confirm grant names candidate, cell(s), device/display, one attempt, permitted cleanup. If only R7-05 granted, STOP after 05 even when PASS.
2. Use A12 live identity SOP, isolated ADB 5038, `myron` / `25102PCBEG`, awake/unlocked, display0. Recheck live experimental version **and** APK SHA256/signer/ELF binding via PROFILE-ARTIFACT; no reinstallation if already matched. Do not substitute historical PID/endpoint values.
3. On workstation root, verify exact candidate SHA/worktree clean and fixture/judge/runner hashes against pinned Git. Read global hard rules. Scan `/proc` for preexisting exact X3 cmdline **before invoking runner**. If present, STOP; do not let the runner trap kill an unrelated session.
4. Compute the cell path; require **entire destination directory absent**, not merely absence of three result files. Read-only `test ! -e "$ROOT/$CELL_ID"` must pass. Historical path refusal in the runner is not safe enough because it writes INVALID into that directory. Any existing path ⇒ STOP with a report outside it.
5. Record outer preflight results in a separate fresh authorization/preflight record. No install, fixture invocation, source change or broad cleanup during preflight.

### One-cell command

`CELL_ID`, `FAULT`, `FIXTURE` below are literal values from the row; never iterate all rows without the corresponding grant. `SERIAL` is supplied by A12 live discovery, not stored in this documentation.

```bash
# Future authorized F8 shell ONLY. Example for NEXT-001.
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce
CELL_ID=r7-05
test ! -e "$ROOT/$CELL_ID" || exit 9
# Verify absence of existing experimental X3 and full artifact binding first.
CELL_ID=r7-05 FAULT=post-draw-gl FIXTURE=direct WAIT_S=12 \
ROOT="$ROOT" SERIAL="$SERIAL" \
bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh
```

Runner starts follow capture, fresh X, reads exact env from `/proc/X/environ`, waits 8 s startup, starts holder then fixture once, waits up to 12 s for X fatal exit, collects summary/ring, cleans only experimental session and invokes frozen judge. Its launch waits are harness timing, not permission to extend the product's 2000 ms terminal wait.

### Frozen judge command and independent acceptance

```bash
python3 evidence/session/gate-a-a1/p2-r7-design/judge-r7.py "$FAULT" \
  "$CELL/logcat-follow.txt" --ring "$CELL/gatea-ring.txt" \
  --summary "$CELL/gatea-summary.txt" \
  --x-alive "$OBSERVED_X_ALIVE" --exit-signal "$OBSERVED_EXIT_SIGNAL"
```

Use actual **pre-cleanup** process/signal observation, never the post-kill state. PASS requires exit 0 and exact `R7_PASS <selector>`, event35 unique after merge by sequence, complete seq starting at 0 with ring repair if needed, summary present, construction and terminal identities correct, all forbidden events absent, cleanup proven, Stable unchanged. Keep raw judge rc/output even if independent safety audit blocks the cell.

Known runner limitations to audit **without changing the frozen files**:

- Its `EXIT_SIGNAL` heuristic suppresses signal detection when any fatal marker exists. Inspect X/Activity PID-bound crash evidence independently; simultaneous fatal+signal is not acceptable.
- Its `forbidden-audit.txt` concatenates duplicate captures and counts raw event35 lines, so use the frozen judge's sequence-deduplicated stream for one-shot proof; do not demand that raw duplicate count equal 1.
- It reads package version but does not independently requalify APK/ELF; outer binding required.
- It writes “NO_X3_RESIDUE” after removing sockets and checking processes; independently record both actual socket/lock absence and PID/cmdline absence.
- R7-09 injection can happen earlier than normal fixture completion. If startup dies before the runner captures valid env/construction, preserve INVALID/INCOMPLETE and STOP; never relaunch. Design a separately approved capture-only harness correction if needed.
- Shell wrapper is double-forked; exact X exit code may not be directly reaped. Fatal marker + PID-bound crash audit and disappearance are the current contract evidence. If ambiguous, stop as observability limitation, never fabricate exit127.

Cleanup: freeze raw output first; stop this fixture/holder; if X still alive at deadline record FAIL before verified-PID TERM; stop only owned follow-logcat PID, force-stop only experimental Activity, verify process and socket residue; Stable PID/cmdline/version/lastUpdateTime before/after identical. Do not run a normal-success probe in the poisoned generation.

Required evidence files: `preflight.txt`, `command.txt` (add as new evidence if runner lacks it), artifact binding/hashes, `installed-package.txt`, `screen.txt`, `dumpsys-activity.txt`, `x-identity.txt`, `x3.maps`, `x-environ-all-termux-x11.txt`, `x-environ-gatea.txt`, `logcat-follow.txt`, `x3-launcher.raw.log`, `gatea-ring.txt`, `gatea-summary.txt`, `fixture.out`, `fixture-exit.txt`, `alive.txt`, `telemetry-fatal.txt`, `judge.txt`, `forbidden-audit.txt`, independent identity/signal/residue audit, `teardown.txt`, Stable before/after, `primary-verdict.txt`, SHA256 manifest. Never commit unfiltered sensitive device metadata/credentials; retain required raw device logs privately with digest if necessary under project evidence policy.

## PROFILE-ARTIFACT — existing candidate or future candidate

Current candidate binding (A10): full SHA `fdfb1ce44b429897eda17c43bf33fbd37afe67f3`; run `35103216566`; package `com.waydefu.x11gpu`; version `1.03.01-fdfb1ce-16.09.26`, code15; APK SHA256 `5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c`; signer `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1`; embedded/unstripped Build ID `1d6bf3cd0eb06d12804e690679211ee7f34f998e`. APK size 15299566. ZIP artifact digest is a different object.

For a changed product candidate, future grant must name source/commit, fork push and `debug_build.yml` workflow dispatch independently of install/device. Require local SHA=fork SHA=run headSha, full multi-ABI success, archive test, package identity, signer continuity, embedded/unstripped matching Build IDs, expected markers and no removed safety markers. Save exact commands/rc, JSON provenance and hashes. Installation requires a separate grant and fresh `r0` evidence path, then installed-base SHA/signer/Build ID read-back; no old r0 overwrite. Missing artifact or mismatched head is BLOCKED, not a reason to rebuild/install silently.

## PROFILE-HOST — future source/fixture verification

Read A05/A09/A17/A20 plus exact candidate source. Commands below are frozen existing tools, **only when their expected source tree is complete**. Missing xserver submodule means BLOCKED, not “verifier PASS by excerpt.” R6 `verify_r6_design_impl.py` belongs to frozen R6 only; EVENT_MAX=35 failure on R7 is expected and is not repaired by weakening it.

```bash
python3 evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py
python3 evidence/session/gate-a-a1/p2-r7-design/verify_r7_support.py "$SRC"
python3 "$SRC/scripts/verify_r7_fatal_propagation.py" "$SRC"
cc -O0 -o /tmp/test_gatea_direct_done_class "$SRC/scripts/test_gatea_direct_done_class.c"
/tmp/test_gatea_direct_done_class
```

For CASE_LOOP or retirement changes, locate exact current `verify_case_loop_wakeup.py`, `verify_exa_composite_wait.py`, `test_renderer_gpu_copy_wakeup.c`, `test-present-gpu-copy-retirement.py` via A09/A20/worktree; read invocation before running, bind test file digest. Historical snapshot contains excerpts, not every complete tool. Future support specification must provide exact missing commands; no guessed success. Run targeted positive/negative/legal-boundary tests first, then appropriate regression suite, `git diff --check`, ARM64 incremental and full-clean compile and normalized patch dry-run/apply/reverse against pinned submodule as required by A09. No production source build was run in this planning task.

## R8 construction matrix and design blockers

Mandatory design output names in NEXT-014: **PROPOSED** `R8-DESIGN.md`, `lifecycle-cell-spec.json`, `fixture-interface.md`, `judge-negative-cases.json`. Freeze actual commands, hashes and evidence locations in that reviewed output before low-tier device execution; the names do not represent existing runnable tools.

| Cell | Exact construction / resource | Acceptance / judge design obligation |
|---|---|---|
| C1 | one direct SUCCESS, FreePixmap src then dst, new distinct pair one direct | same IDs/tuple: logical UNREGISTER before GL reverse destroy before ACK/removal; both sides zero registry before new pair; exact pixels; X alive |
| C2 | one successful direct, then holder departure and clean X TERM via CloseScreen | gateAClosing forbids admission; drain all submitted work; retire every registered buffer; events27→28 and clean summary; X clean exit/no crash/fatal; NO_X3_RESIDUE |
| C3-window | PresentPixmap then DestroyWindow without awaiting CompleteNotify | event36 waited=0 **or** 1 both legal; covering completion before ACK; event32=0; no fatal; X alive; pending=0 |
| C3-disconnect | PresentPixmap then disconnect that client; keep holder | same retirement proof plus a different live client completes a subsequent direct exact SUCCESS |
| C4 | register source/destination to READY with no direct submission, then FreePixmap | `lastSubmittedSerial=0`, no terminal wait; UNREGISTER/ACK/resource balance. No shipped register-only fixture: define restricted harness seam or demonstrate reachable existing call path first |
| C5-full | fill fixed pool with distinct buffers; then clean close | **16 X slots / 16 renderer READY entries, 8 pending import entries**; count entries already occupied by root/other resources. Register sequentially to avoid conflating pending8 overflow; 8 disjoint pairs only if occupancy was truly zero |
| C5-overflow | separate fresh session, attempt the next buffer beyond measured free slots | X insert returns refusal, no lease/unlock/publish for refused pair; software/staging fallback exact and earlier READY source subsequently cleaned. Renderer-only full branch needs a distinct reachable fixture if claimed; don't fabricate it from X refusal |
| D | separate Present client causes GPU_COPY_DONE while a Gate A buffer UNREGISTER waits | prove DEFER queue nonempty/record identity during wait and eventual CompleteNotify count equals submitted Present count; if overlap not constructed, INVALID not retry-until-green; no `x-deferred-record-queue` fatal |
| P1 | hook `destroy-while-gpu-owned`, direct invocation once | enum14 side1 event35; LEASE_GPU_OWNED before hook, fatal `x-destroy-in-lease`/7; no unregister ACK or normal release. Current hook calls fatal directly, not a real DestroyPixmap; claim is synthetic guard containment only |
| P2 | hook `close-while-lease`, direct invocation once | enum15 side1 event35; active lease → `gateACloseGeneration` → `x-close-in-lease`/8; no CLOSED or normal release |

Clean cells: PROTO=TELEMETRY=1; TEST_FAULT/ARM absent. P cells: exact R7 paired env; each in a separate fresh X. Do not manufacture a direct client Destroy in the synchronous Prepare→Done interval: X cannot dispatch that request inside the wait. Present pending **is** reachable asynchronously; early completion is a legal branch, not a false red.

Design conflicts requiring explicit disposition:

1. A07 C1 describes ACK→RESOURCE_DESTROY, but A18 and current S02 require destroy before ACK. Also X SEND telemetry is emitted after send and can race renderer events; judge must use role-bound ACK-after-destroy and command/identity proof, not naïve numeric event ordering. Do not silently change A07 or A05.
2. A05 pending-hook construction checks LEASE_RESERVED(event2), while A07 semantic intent is GPU_OWNED(event5); independent R8 oracle must prove event5. P1 currently tests synthetic fatal rather than invoking the entire destructor. Distinguish those claims and design an additional reachable guard test only if required.
3. A07 capacity “K pairs” conflicts with buffer slots; freeze K unit and existing root occupancy. No LRU requirement follows from capacity alone.
4. C4 register-only and D deferred overlap lack a verified exact fixture. [H] output must show a reachable source call graph and deterministic construction without sleeps or added renderer delays.
5. `GATEA_SUMMARY` has lease/registry gauges but no live endpoint pending count; total pending decrements cannot prove pending current=0. Add a reviewed snapshot outside frozen ABI, or a proven ledger; no invented c28.
6. Source increments/decrements counters after socket sends, so X may observe ACK before renderer diagnostic decrement. Freeze a final stable summary capture that observes both sides, without accepting a racy early snapshot. Clean close summary contains zeroed tuple; retain earlier generation identity separately.
7. REGISTER_FAILED marks an entry DEAD but retire begins from READY; test failed registration cleanup in production audit rather than assuming it works. Review before adding failure construction to release qualification.
8. A18 `ownerRef` and root equivalent READY are architecture obligations. Current pair refs/root pending may be an equivalent narrow implementation, but accepting that equivalence requires a proof and review; absence cannot be dismissed as optional by this plan alone.

## R9 construction matrix

NEXT-019 freezes a dedicated harness that can preserve Activity for warm rounds. Do not reuse PROFILE-R7 cleanup for warm rounds.

| Cell | Exact rounds / identity | Required evidence |
|---|---|---|
| R9-1 | 3 fresh X, same live Activity PID; normal pair REGISTER→SUCCESS→Destroy→Close | all three nonces distinct; registry current=0 before each new admission; balance at close; NO_X3_RESIDUE each round |
| R9-2 | 3 fresh X, force-stop **experimental** Activity between rounds, record new PIDs/starttimes | same obligations; Android PID numeric reuse is disambiguated with process starttime, not guessed identity |
| R9-3 | same X reset only if source/launcher path supports it | clean CLOSED before reset, new valid tuple before admission, stale IDs/fatal/serial rejected; if source cannot regenerate nonce after close, BLOCKED or approved unsupported-scope disposition, not automatic PASS |
| R9-F1 | one `stale-ready-replay` hook session | valid READY then synthetic old nonce/gen; event35 enum16 side2; frozen judge `x-wrong-generation`/6; stale frame must not satisfy a new waiter. Hook is not replay of an actual captured prior frame |
| R9-F2 | one fresh session immediately after authorized F1 cleanup | new nonce, empty registry before admission, exact direct SUCCESS; cannot claim recovery from source alone |

No new ABI/protocol is mandated just to run warm/cold fresh processes. Actual retained-renderer or same-process reset failures may require ownership redesign; those are [H], not a generic “handle recreate” task.

## R10 checkpoints and measurable resources

Existing frozen command **families** A07 are preserved; no complete historical R10 sampler exists. NEXT-021 freezes the concrete sampler and permission-aware checks before execution. Do not run the following planning examples now.

| Metric | Collection at authorized checkpoint | Predicate |
|---|---|---|
| X FD | count `/proc/$X_PID/fd` under Termux uid; capture permission errors/exit separately | K0 vs K0 and K2 vs K2 across ≥5 rounds: no monotonic growth; A07 allowance0; missing ⇒ BLOCKED |
| Activity FD | `run-as com.waydefu.x11gpu` reading its own `/proc/$ACTIVITY_PID/fd` | same when readable; else `not_observable` and D-7 decision, not zero |
| RSS/PSS | `/proc/<pid>/status`, `dumpsys meminfo com.waydefu.x11gpu` | descriptive trend only, no invented threshold |
| registry | SUMMARY c18 X, c19 renderer | K3 zero, before new-session admission zero; bounded to actual capacity during session |
| leases | SUMMARY c20 | K3 zero; invariant no release while uncertain |
| endpoint pending / root pending | reviewed live snapshot of `meta.pendingCount` and `rootGpuCopyPending`/buffer pending | K2 zero; cumulative c11 alone insufficient |
| AHB | c12 acquire / c13 release | equal after clean retirement; process death alone not proof |
| EGLImage / texture | c14 create=c15 destroy, c16 create=c17 delete | equal for tracked Gate A imports at K3 |
| threads / mappings | `/proc/<pid>/task`, `/proc/<pid>/maps` or permission-aware equivalent | diagnostic trend/identity, no frozen numeric threshold; unavailable stays null |
| socket / X3 | exact process cmdline and known X3 socket/lock paths | absence after every round, both domains checked |

Freeze minimum 5 rounds with both warm and cold Activity, proposed 3+2, N=64 per pair; K0 bind/pre-direct, K1 after N, K2 after frees, K3 clean close. A07's no-monotonic-growth predicate is not a license for arbitrary bounded leaks: show raw series and distinguish fixed initialization plateau from repeat-per-cycle increase; ambiguous series is review/inconclusive. Do not invent an RSS megabyte threshold. Additional churn 4K is optional after basic R10, uses K in buffer slots with declared pair schedule; endpoints at 1K and 4K compare equivalent FD state.

## Future harness delivery contract

For NEXT-014/019/021/024/025/027/033/035, a design is complete only when its output names: exact source SHA/symbols; fixture CLI, count, scheduling reachability, hash/provenance; allowed mutations and memory order; event producers and tuple/serial identity; exact judge CLI; missing-signal disposition; negative and legal-boundary test vectors; cleanup and Stable checks; artifact/carry-forward matrix; and authorization granularity. An unresolved item is `[H] DESIGN REQUIRED` and prevents its dependent `[L]` packet from starting. Naming a future `run-*.sh` is not evidence it exists.

## Verification performed for this documentation PR

Only read-only existing-evidence rejudging and documentation checks. Python 3.12.7 host, `-X utf8 -B` for Windows logs. A05 unit tests 16/16 PASS; new R7-04 exit0 `R7_PASS fbo-incomplete`; historical R7-04 exit1 `R7_FAIL halt_mismatch what=x-direct-not-success reason=4`. No ADB, install, build, qualification, source mutation, CI dispatch, or historical rewrite. Final schema/link/diff checks are recorded in PR validation.

Final documentation checks on 2026-09-17: 38 numbered packets, each with exactly 34 ordered nonempty requested fields; all relative Markdown file links resolve; closure JSON parses with 22 distinct checklist items, 17 required for P2, all unverified satisfaction fields null and closure false. Frozen judge unit tests remain 16/16; both existing R7-04 evidence rejudgments retain their expected exit codes and verdicts. Only the six planning files are included in this PR. These checks validate documentation structure and retained evidence, not future runtime or proposed architecture acceptance.
