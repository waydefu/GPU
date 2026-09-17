# R8 implementation and qualification work packages

**PROPOSED; none executed by this documentation PR.** One writer / one isolated worktree. Source baseline `fdfb1ce44b429897eda17c43bf33fbd37afe67f3`; docs baseline `ece9f3f228b0ea2e406544c85346246559fe5095`. Newer current authority must be reconciled before execution. Do not alter frozen R6/R7 source worktrees or historical cell directories.

## Acceptance before coding

Review R8-A01…A10, the test-only extension exposure/disable contract, D's nondeterministic but fail-closed device construction, and source-bound C2/CloseScreen teardown disposition. Mark accepted decisions in a new design acceptance record, not by editing old A07. This PR alone is not an instruction to execute source/CI/device work.

Outputs under the future implementation's `tests/r8/` are new files; this planning PR creates only six docs/JSON files under `planning/r8-lifecycle-20260917/`. The exact CLI contract and cell predicates are frozen by this design's accepted revision. ABI claims are checked against real compiled sizes, not string matching.

## R8-I01 — actual oracle and host construction [L after acceptance]

Input: accepted design, both JSON specs, pinned R7 judge, source/parser/deferred queue.

Deliver:
- `judge-r8.py` raw-input parser, typed identity/three-valued fields, per-cell predicates and exact four-way exit codes.
- `test-judge-r8.py` builds complete fixtures for all53 vectors, tests the real judge; no copied look-alike.
- Host adapter links actual `gateAQueueDeferredRecord`, `gateADeferredWorkProc`, `handleLegacyRecord`/record decoder via a test compilation seam. Its synthetic existing-type records never enter Android runtime.
- Deterministic host DEFER→dispatch once, CANCEL/stale/fatal discard, record/FD ownership and failed allocation/QueueWorkProc handling. Verify no queue callback during an active waiter; existing production callback scheduling stays unchanged.
- Protocol tests: invalid/foreign/root/imported XID, malformed length, byte order, unsupported case/operation, duplicate allowed query vs exhausted mutation budget. Test resource lookup with actual pinned xserver helper semantics.
- Versioned raw input schema and examples. Unknown fields may be preserved, but missing required identity/order/state fails closed.

Allowed changes: new host tools/tests and compile-gated test adapters only. No production result/ownership fix. Stop on any real-source defect requiring semantic mutation; return one minimal trace/source proof to design review.

Verification: all53 explicit vectors evaluated with exact expected classification/reason, plus malformed/truncated JSON, missing diagnostics END, duplicate conflicting sequence and raw file hash mismatch. Negative cases must fail their intended predicate, not an unrelated parser error. Host tests remain HOST_VERIFIED, never R8 DEVICE_PASS.

## R8-I02 — registration fixture and bounded client [L after acceptance]

Allowed source locations:
- `lorie/src/main/cpp/lorie/InitOutput.c`: test-only wrapper around real buffer conversion/READY helpers; safe X-owned checkpoint function; no call to direct Prepare/Done for registration-only.
- New `lorie/.../gatea_r8_test.[ch]` plus the exact build registration location found in the complete tree: compile option default OFF; main-thread test-only X extension and bounds/access checks.
- `tests/r8/p_r8_lifecycle.c`: owned offscreen pixmaps, Picture lifetime, real Present ASYNC|COPY, survivor/observer and deterministic bounded command schedule.
- Minimal CMake wiring and test protocol header. Record exact resolved source paths in implementation report; no guessed complete-tree check from these docs excerpts.

Register control only under all activation guards; no arbitrary path/FD/memory/GL dispatch and no test command from a waiter. Validate client ownership before converting or acquiring anything. Refused lookup/descriptor returns a control error, with no silent fallback. Do not bypass gateAEnsureReady or write registry state manually.

Required host/static evidence:
- no test extension in OFF builds; malformed/unarmed/case mismatch refuses before runtime mutation;
- C4 wrapper has no reserve/unlock/submit/fallback; actual lastSubmittedSerial and queue state unchanged;
- controlled buffer slots, sequential READY, correct refusal and recovery;
- fixture releases Picture refs before final FreePixmap; no hidden retain preventing the destructor;
- client count/operation budget exactly matches cell specification.

No broad protocol/ABI change. If main-thread own-client lookup/extension initialization cannot follow the stated access contract, stop and propose the narrow correction rather than expose an unsafe backdoor.

## R8-I03 — lifetime observation and real pending guard [L after acceptance]

Allowed locations: decisive functions in InitOutput.c, renderer.cpp, cmdentrypoint.cpp, current xserver.patch; numeric pending getter in actual buffer implementation/header; test-only observation helper.

Changes:
1. Copy registry state under existing leaf locks, then log outside locks. Add an X-owner-thread read accessor for actual numeric pending, without modifying counters or object layout shared across processes.
2. Add observations specified by fixture-interface at real postconditions; no event/counter renumbering, no added shared fields.
3. At existing P1 enum14 branch call real `lorieExaDestroyPixmap` on the source private object. If it returns, emit `R8_HOOK_UNEXPECTED_RETURN` and terminate with an explicitly distinct test-failure outcome; do not forge expected fatal7. Preserve P2's real gateACloseGeneration hook. Do not change selectors1–13 or16.
4. Instrument actual Present pre-ACK/ACK-clear/idle ordering with copied identities before release. event36's waited bit stays unmodified.
5. Add X-local decoded/deferred record IDs under test compilation guard, and complete type-specific send/receive ordinals for wakeup correlation. Add cause markers at notify callers (fence-complete vs surface-loss), not synthetic payload serials.
6. Emit final clean renderer state after actual unbind and X close state with original tuple retained. Do not reorder production send/unbind or add a waiting barrier for logging.
7. Maintain role-local observation sequences. Copy counts before freed state; fatal-path diagnostics must not run normal release. For P cells, only required X fault-prefix/final observations need an END; renderer graceful END/resource zero is not a pending-fatal requirement.

Static audit: instrumentation must not feed admission, result, lifetime, queue or timeout decisions. Test14 is the only intended fault action change; normal path and all shared sizes remain unchanged. No client dispatch from wait; no additional mutex held over I/O.

Host proof: compile actual helper with guard enabled and mutation-disabled guard in isolated tests; disabling guard produces the sentinel failure, not PASS. Verify event5 precedes35, both before first publish; no false demand for a published serial in P1/P2. For postcondition observers, deliberately corrupt ordering in a test fixture and confirm the real oracle rejects.

## R8-I04 — full candidate verification [L]

Require complete product tree and exact xserver submodule. The docs snapshot is not a compilable substitute. Run:
- accepted new verifier/judge tests and actual-source lifecycle/record/helper tests;
- existing R7 support verifier, fatal classifier tests, CASE_LOOP/wait/Present retirement regressions as applicable;
- frozen R7 judge16 tests and existing new R7-04 PASS / old R7-04 expected FAIL rejudge, with original tools unchanged;
- incremental and full-clean ARM64 build, normalized xserver.patch apply/reverse on pinned submodule, ABI sizes/events/counters and OFF-mode compilation.

Bind commands, real rc, toolchain and source/submodule SHA. A token-search verifier alone does not prove source call order or memory ordering. Existing R6 verifier remains bound to its own baseline; do not weaken it to accept a later event enum.

Resolve C2/C5-full close path by source-order test before runtime: distinguish live-at-CloseScreen from client-resource retirement before CloseScreen. If needed, freeze a reviewed test-control invocation of real generation drain while resources are live **as a separate synthetic claim**, retaining real normal-close coverage; do not change server teardown to manufacture it.

Done: SOURCE_FIXED and HOST_VERIFIED report, exact allowlist diff, all required host checks, accepted runtime construction and no unresolved source-only assumptions. No device PASS.

## R8-I05 — fork CI / artifact [U][C][L]

Only after separate explicit push/CI grant:
- push new support commit to `waydefu/termux-x11` approved fork branch, never upstream;
- dispatch approved workflow exactly once; local full SHA = remote SHA = run headSHA;
- qualify full successful artifact, archive integrity, experimental package/version/signer, APK hash and embedded/unstripped ELF Build IDs;
- record support build option and absence in normal OFF build; inspect expected guard/observer markers;
- retain failure outputs, no automatic rerun.

An artifact-qualified report is not install authorization. A new support APK cannot reuse the old `runtime-fdfb1ce` evidence path or a runner hardcoded to the old version.

## R8-I06 — installation and runtime [U][D][L]

Prerequisites: R7 overall PASS or an explicit newer authority granting a changed gate order; accepted R8 design; HOST_VERIFIED; qualified exact support artifact; explicit install/read-back grant if not installed; explicit named cell/batch grant.

Before each cell: grant, live device/ADB5038/display0, package/ELF binding, tools+spec hashes, exact env, Stable before, no unrelated X3 and entire new path absent. Use `run-r8-one-cell.sh` interface from fixture-interface. The old R7 runner is not reused; its cleanup/hardcoded candidate assumptions are unsuitable.

Execute cell_order once per fresh X, no automatic retries:
C1 → C2 → C3-window → C3-disconnect → C4 → C5-full → C5-overflow → D → P1 → P2.

Only a preexisting grant explicitly naming the entire sequence permits continuation after each PASS. Any FAIL/INVALID/BLOCKED, unknown process signal, missing final observation or Stable deviation stops the batch. A new grant may name one bounded new attempt; its evidence ID is new and original remains immutable.

P1/P2: immutable judge-r7 plus supplemental R8 oracle; do not treat expected fail-stop as clean resource release. All clean cells: per-cell product predicates, meaningful resource postconditions, expected live/clean process state and renderer final observation. Record actual socket/lock and process absence after cleanup, Stable unchanged.

## R8-I07 — aggregate [R][L]

Require all ten cells PASS on the declared artifact or explicit approved lineage; fixture/judge/spec hashes; complete required observations; no forbidden release, unexpected fatal or Stable change; no X3 residue.

Write a new R8 aggregate report with per-cell evidence paths, commands/rc, target IDs and limitations. Exact result proposal:
`GATE A P2 R8 PASS / <full-source-sha>`.

Also state: this does not close R9, R10, Production Gate A, root resize, REGISTER_FAILED cleanup, general ownerRef equivalence or V1-Core. Update only a new current handoff/closure record under an appropriate docs grant; no rewriting historical FAIL or R7 packet results. Stop before R9 runtime.

## Requalification selection

| Actual diff | Required disposition |
|---|---|
| This PR: docs/JSON only | No CI/install/device/baseline rerun. Validate docs/schema/source anchors. |
| New host judge/fixture only | Host real-parser vectors; new R8 cells only after grants. No APK CI if product unchanged. |
| Compile-gated observations + test extension + fault14 real guard, normal code semantics unchanged | Full source/host/ABI/OFF proof and new artifact; R8 cells qualify new claims. Review exact diff for recorded R7 carry-forward; do not automatically rerun R7-04 or B-2. Normal-path path proof is supplied by clean C1 and affected existing host regressions, not an invented blanket device waiver. |
| Any normal direct admission/READY/result path semantic change | Scope escalates: accepted B-2 and affected R7/R6 requalification per merged master-plan table before R8 claim. |
| Actual Present ACK/retirement semantics change | Scope escalates to R6 D1/D2-inflight/D2-OOM, P1/P2 and C3 as touched; D3 for surface changes. Not permitted as “observation-only.” |
| Shared ABI, generation or ownership redesign | Stop [H]; new design and exact expanded baseline/CI/device grants. |
| Harness construction fix after INVALID | Preserve first attempt; host negative/edge tests; one separately granted fresh attempt. No changed product inference from timing alone. |

## Validation of this planning PR

Check all six relative-file links and JSON parsing; ten unique cell IDs match order;53 unique vectors target defined cells or explicit HOST-DEFER scope; mandatory decision IDs and field coverage; every runtime verdict stays NOT_RUN; source blob identities match pinned GitHub. Check docs-only diff and absence of binaries/credentials. These are documentation checks, not tests of a future R8 implementation.
