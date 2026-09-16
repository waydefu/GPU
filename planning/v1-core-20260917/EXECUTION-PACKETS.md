# V1-Core execution packets

**PROPOSED execution organization; planning only. No cell, source change, CI, install, merge or production action is authorized by this PR.**

Base: `c95b893ea161d5aacb7b633495b1751ac97182b7`. Current next qualification: **NEXT-001 — R7-05 post-draw-gl** on recorded candidate `fdfb1ce`, only after a new explicit grant.

Read [README](README.md), then only the applicable packet and its references. [AUTHORITY-INDEX](AUTHORITY-INDEX.md) resolves Axx/Sxx. [CONTRACT-DETAILS](CONTRACT-DETAILS.md) profiles and matrices are normative parts of each referencing field. [MASTER-PLAN](MASTER-PLAN.md#executor-global-hard-rules) supplies immutable safety rules and INV-A01–A18. Do not read the entire history to execute a frozen packet.

Each packet has exactly the 34 requested fields. **N/A** states why a field is not applicable. Future output names are deliverables, not existing runnable tools. A dependent [L] packet cannot run while its [H] design is unresolved. A grant may explicitly cover multiple named actions; do not ask again for actions already covered, and never infer unnamed actions from an earlier PASS.

The final field identifies the next boundary, not a grant. NEXT-037 is an exception path, not a mandatory failure or automatic retry loop. NEXT-034 is conditional; NEXT-038 follows NEXT-036 when all acceptance conditions are met. NEXT-024 explicitly separates design from its later bounded execution to prevent a design document from being called a device PASS.

| Packet | Name | Class |
|---|---|---|
| [NEXT-001](#next-001) | R7-05 post-draw-gl qualification | [U][D][L] |
| [NEXT-002](#next-002) | R7-01 src-ready-miss qualification | [U][D][L] |
| [NEXT-003](#next-003) | R7-02 dst-ready-miss qualification | [U][D][L] |
| [NEXT-004](#next-004) | R7-03 tuple-mismatch qualification | [U][D][L] |
| [NEXT-005](#next-005) | R7-06 fence-create-fail qualification | [U][D][L] |
| [NEXT-006](#next-006) | R7-07 fence-timeout qualification | [U][D][L] |
| [NEXT-007](#next-007) | R7-08 renderer-fatal-pre-fence qualification | [U][D][L] |
| [NEXT-008](#next-008) | R7-09 wrong-generation-frame qualification | [U][D][L] |
| [NEXT-009](#next-009) | R7-11 serial-wrap qualification | [U][D][L] |
| [NEXT-010](#next-010) | R7-10 renderer-exit-after-consume qualification | [U][D][L] |
| [NEXT-011](#next-011) | R7-P1 present-hold-complete qualification | [U][D][L] |
| [NEXT-012](#next-012) | R7-P2 present-renderer-exit qualification | [U][D][L] |
| [NEXT-013](#next-013) | R7 aggregate and immutable carry-forward audit | [R][L] |
| [NEXT-014](#next-014) | R8-DESIGN — resolve lifetime oracle and fixture gaps | [R][H] |
| [NEXT-015](#next-015) | R8-IMPLEMENT — reviewed support only | [U][L] |
| [NEXT-016](#next-016) | R8-VERIFY — actual source and lifecycle oracle | [R][L] |
| [NEXT-017](#next-017) | R8-CI and artifact qualification, conditional | [U][C][L] |
| [NEXT-018](#next-018) | R8-DEVICE — clean and pending lifecycle cells | [U][D][L] |
| [NEXT-019](#next-019) | R9-DESIGN — fresh sessions and stale-state recovery | [R][H] |
| [NEXT-020](#next-020) | R9-DEVICE — warm/cold recreate and recovery | [U][D][L] |
| [NEXT-021](#next-021) | R10-DESIGN — measurable resource ledger | [R][H] |
| [NEXT-022](#next-022) | R10-DEVICE — residue accounting | [U][D][L] |
| [NEXT-023](#next-023) | Gate A P2 runtime closure ledger | [R][L] |
| [NEXT-024](#next-024) | Bounded XFCE qualification design and controlled execution | [R][H] |
| [NEXT-025](#next-025) | P2-B.3 measurement design | [R][H] |
| [NEXT-026](#next-026) | P2-B.3 paired workload measurement | [U][D][L] |
| [NEXT-027](#next-027) | Production Gate A minimal V1-Core gap design | [R][H] |
| [NEXT-028](#next-028) | Production corrections — implementation and host proof | [U][L] |
| [NEXT-029](#next-029) | Production candidate CI and artifact binding | [U][C][L] |
| [NEXT-030](#next-030) | Production lifecycle and affected baseline qualification | [U][D][L] |
| [NEXT-031](#next-031) | Refresh final-candidate workload evidence | [U][D][L] |
| [NEXT-032](#next-032) | Gate H evidence decision — router only if justified | [R][L] |
| [NEXT-033](#next-033) | Conditional Gate H router design | [R][H] |
| [NEXT-034](#next-034) | Conditional router implementation and qualification pipeline | [U][L] |
| [NEXT-035](#next-035) | PROPOSED Gate W v1 and release contract freeze | [R][H] |
| [NEXT-036](#next-036) | Gate W final-artifact desktop workload qualification | [U][D][L] |
| [NEXT-037](#next-037) | Reusable failure → narrow repair → one fresh requalification | [R][H] |
| [NEXT-038](#next-038) | V1-Core acceptance and documentation freeze | [R][L] |

## NEXT-001

**PACKET ID:** NEXT-001

**NAME:** R7-05 post-draw-gl qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one post-draw-gl fault on the bound candidate. FAILED_QUIESCED; firstFailed DRAW must remain reason=2; never copy R7-04 fatal suppression onto this branch. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** A14 R7-04 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** A14 R7-04 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-05, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py post-draw-gl.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=post-draw-gl, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-05 FAULT=post-draw-gl FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=post-draw-gl, CELL="$ROOT/r7-05" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 6 PUBLISH → 10 DRAW → 35; event35 exactly once in sequence-deduplicated trace, enum/side=5 / renderer(2); matching session/generation/serial/src/dst. FAILED_QUIESCED; firstFailed DRAW must remain reason=2; never copy R7-04 fatal suppression onto this branch.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=x-direct-not-success reason=2; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS post-draw-gl`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected x-direct-not-success/2; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-05/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-05 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-002 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-002

**PACKET ID:** NEXT-002

**NAME:** R7-01 src-ready-miss qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one src-ready-miss fault on the bound candidate. Source READY miss; no texture upload or legacy fallback. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-001 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-001 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-01, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py src-ready-miss.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=src-ready-miss, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-01 FAULT=src-ready-miss FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=src-ready-miss, CELL="$ROOT/r7-01" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 6 PUBLISH → 7 CONSUME_DIRECT → 35 → 9 LOOKUP_FAIL; event35 exactly once in sequence-deduplicated trace, enum/side=1 / renderer(2); matching session/generation/serial/src/dst. Source READY miss; no texture upload or legacy fallback.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=r-gatea-DIRECT_LOOKUP_FAIL reason=2; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS src-ready-miss`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected r-gatea-DIRECT_LOOKUP_FAIL/2; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-01/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-01 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-003 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-003

**PACKET ID:** NEXT-003

**NAME:** R7-02 dst-ready-miss qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one dst-ready-miss fault on the bound candidate. Destination READY miss; bind src/dst separately, not the source-miss trace. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-002 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-002 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-02, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py dst-ready-miss.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=dst-ready-miss, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-02 FAULT=dst-ready-miss FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=dst-ready-miss, CELL="$ROOT/r7-02" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 6 → 7 → 35 → 9 LOOKUP_FAIL; event35 exactly once in sequence-deduplicated trace, enum/side=2 / renderer(2); matching session/generation/serial/src/dst. Destination READY miss; bind src/dst separately, not the source-miss trace.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=r-gatea-DIRECT_LOOKUP_FAIL reason=2; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS dst-ready-miss`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected r-gatea-DIRECT_LOOKUP_FAIL/2; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-02/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-02 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-004 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-004

**PACKET ID:** NEXT-004

**NAME:** R7-03 tuple-mismatch qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one tuple-mismatch fault on the bound candidate. PROTOCOL identity failure; older generation-reason prose is superseded by A04. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-003 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-003 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-03, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py tuple-mismatch.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=tuple-mismatch, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-03 FAULT=tuple-mismatch FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=tuple-mismatch, CELL="$ROOT/r7-03" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 6 → 7 → 35; event35 exactly once in sequence-deduplicated trace, enum/side=3 / renderer(2); matching session/generation/serial/src/dst. PROTOCOL identity failure; older generation-reason prose is superseded by A04.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=r-gatea-direct-identity reason=5; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS tuple-mismatch`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected r-gatea-direct-identity/5; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-03/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-03 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-005 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-005

**PACKET ID:** NEXT-005

**NAME:** R7-06 fence-create-fail qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one fence-create-fail fault on the bound candidate. Fence creation failure cannot publish completed or semantic success. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-004 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-004 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-06, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py fence-create-fail.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=fence-create-fail, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-06 FAULT=fence-create-fail FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=fence-create-fail, CELL="$ROOT/r7-06" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 6 → 10 DRAW → 35; event35 exactly once in sequence-deduplicated trace, enum/side=6 / renderer(2); matching session/generation/serial/src/dst. Fence creation failure cannot publish completed or semantic success.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=r-gatea-fence-create reason=3; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS fence-create-fail`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected r-gatea-fence-create/3; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-06/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-06 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-006 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-006

**PACKET ID:** NEXT-006

**NAME:** R7-07 fence-timeout qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one fence-timeout fault on the bound candidate. No event14 COMPLETED covering target S after injection; never increase 2000 ms. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-005 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-005 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-07, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py fence-timeout.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=fence-timeout, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-07 FAULT=fence-timeout FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=fence-timeout, CELL="$ROOT/r7-07" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 6 → 10 DRAW → 35; event35 exactly once in sequence-deduplicated trace, enum/side=7 / renderer(2); matching session/generation/serial/src/dst. No event14 COMPLETED covering target S after injection; never increase 2000 ms.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=r-gatea-fence-wait reason=3; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS fence-timeout`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected r-gatea-fence-wait/3; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-07/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-07 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-007 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-007

**PACKET ID:** NEXT-007

**NAME:** R7-08 renderer-fatal-pre-fence qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one renderer-fatal-pre-fence fault on the bound candidate. FATAL wins even if other completion scalars appear; no success release. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-006 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-006 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-08, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py renderer-fatal-pre-fence.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=renderer-fatal-pre-fence, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-08 FAULT=renderer-fatal-pre-fence FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=renderer-fatal-pre-fence, CELL="$ROOT/r7-08" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 6 → 7 → 35; event35 exactly once in sequence-deduplicated trace, enum/side=8 / renderer(2); matching session/generation/serial/src/dst. FATAL wins even if other completion scalars appear; no success release.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=r-test-fatal-pre-fence reason=6; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS renderer-fatal-pre-fence`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected r-test-fatal-pre-fence/6; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-08/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-08 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-008 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-008

**PACKET ID:** NEXT-008

**NAME:** R7-09 wrong-generation-frame qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one wrong-generation-frame fault on the bound candidate. May fire during READY. If runner loses pre-cleanup identity/env evidence, preserve INVALID and stop for capture design; never relaunch. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-007 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-007 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-09, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py wrong-generation-frame.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=wrong-generation-frame, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-09 FAULT=wrong-generation-frame FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=wrong-generation-frame, CELL="$ROOT/r7-09" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** first inbound Gate A frame → 35; prior PUBLISH is not required; event35 exactly once in sequence-deduplicated trace, enum/side=9 / X(1); matching session/generation/serial/src/dst. May fire during READY. If runner loses pre-cleanup identity/env evidence, preserve INVALID and stop for capture design; never relaunch.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=x-wrong-generation reason=6; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS wrong-generation-frame`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected x-wrong-generation/6; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-09/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-09 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-009 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-009

**PACKET ID:** NEXT-009

**NAME:** R7-11 serial-wrap qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one serial-wrap fault on the bound candidate. No PUBLISH serial=0. Do not require fabricated earlier publishes. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-008 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-008 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-11, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py serial-wrap.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=serial-wrap, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=serial-wrap, CELL="$ROOT/r7-11" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 35 → serial seeding/wrap guard; earlier PUBLISH is not required; event35 exactly once in sequence-deduplicated trace, enum/side=11 / X(1); matching session/generation/serial/src/dst. No PUBLISH serial=0. Do not require fabricated earlier publishes.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=x-serial-wrap reason=6; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS serial-wrap`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected x-serial-wrap/6; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-11/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-11 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-010 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-010

**PACKET ID:** NEXT-010

**NAME:** R7-10 renderer-exit-after-consume qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one renderer-exit-after-consume fault on the bound candidate. Prove renderer disappearance and X containment, rather than cleanup-created disappearance. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-009 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-009 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-10, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare, gateADoneDirect, gateAXFatal; S02 consumeGateAComposite; S03 handleGateARecord; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r3_single_direct exactly once. A05 judge-r7.py renderer-exit-after-consume.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=renderer-exit-after-consume, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=renderer-exit-after-consume, CELL="$ROOT/r7-10" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 6 → 7 → 35 → renderer exit → X HUP; event35 exactly once in sequence-deduplicated trace, enum/side=10 / renderer(2); matching session/generation/serial/src/dst. Prove renderer disappearance and X containment, rather than cleanup-created disappearance.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=x-hup reason=6; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS renderer-exit-after-consume`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected x-hup/6; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-10/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-10 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-011 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-011

**PACKET ID:** NEXT-011

**NAME:** R7-P1 present-hold-complete qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one present-hold-complete fault on the bound candidate. Withhold target COPY completion. No target idle/CompleteNotify or event34; 36 may report waited=1; preserve 2000 ms. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-010 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-010 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-P1, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 lorieGpuCopyWait; present_gpu_copy_retire_or_fatal (A09 pinned xserver patch); S02 applyPendingGpuCopiesLocked; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r6_d2_present inflight exactly once. A05 judge-r7.py present-hold-complete.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=present-hold-complete, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=present-hold-complete, CELL="$ROOT/r7-p1" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 30 CALLBACK(src=4) → 35; event35 exactly once in sequence-deduplicated trace, enum/side=12 / renderer(2); matching session/generation/serial/src/dst. Withhold target COPY completion. No target idle/CompleteNotify or event34; 36 may report waited=1; preserve 2000 ms.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=x-present-copy-wait reason=4; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS present-hold-complete`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected x-present-copy-wait/4; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-p1/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-P1 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-012 only under its own or already explicit batch grant; on failure NEXT-037 read-only triage first.

## NEXT-012

**PACKET ID:** NEXT-012

**NAME:** R7-P2 present-renderer-exit qualification

**CLASSIFICATION:** [U][D][L] — FROZEN cell; PROPOSED execution packaging.

**PURPOSE:** Qualify exactly one present-renderer-exit fault on the bound candidate. COPY consume must be constructed before death; no event34 or target ACK. INV-A01–A13, INV-A17.

**CURRENT AUTHORITY:** A01/A02 current status; A04 frozen R7 contract; A05 frozen judge; A10/A13 artifact and runner; A14 current PASS. Resolve IDs in AUTHORITY-INDEX.md.

**ENTRY STATE:** NEXT-011 CELL_PASS; R7 overall IN PROGRESS. Candidate still fdfb1ce; no preexisting experimental X3 or cell directory.

**DEPENDENCIES:** NEXT-011 CELL_PASS; PROFILE-R7 outer preflight and PROFILE-ARTIFACT binding. If source changed, NEXT-037 must freeze affected requalification before this packet can run.

**USER AUTHORIZATION REQUIRED?:** YES — explicit R7-P2, candidate, one attempt, experimental :3/display0 and cleanup grant; an already granted named batch suffices. This docs PR grants none.

**FILES TO READ:** README.md; MASTER-PLAN.md#executor-global-hard-rules; CONTRACT-DETAILS.md#profile-r7--exact-later-execution and R7 cell matrix; A01/A04/A05/A10/A12/A13. Read frozen runner before invocation.

**SOURCE SYMBOLS TO LOCATE:** S01 lorieGpuCopyWait; present_gpu_copy_retire_or_fatal (A09 pinned xserver patch); S02 applyPendingGpuCopiesLocked; S04 lorieGateATestFaultConsume. Read only.

**HARNESS / FIXTURE:** A13 run-r7-one-cell-fdfb1ce.sh; p_b3a_hold once; p_r6_d2_present inflight exactly once. A05 judge-r7.py present-renderer-exit.

**REQUIRED ARTIFACT:** fdfb1ce44b429897eda17c43bf33fbd37afe67f3 / CI 35103216566 / APK and Build ID exact PROFILE-ARTIFACT; hash shipped fixtures/judge/runner against pinned repository.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot only, com.waydefu.x11gpu :3, display0, isolated ADB 5038. X Gate A env EXACT: PROTO=1, TELEMETRY=1, TEST_FAULT=present-renderer-exit, TEST_ARM=1 (full TERMUX_X11_GATEA_ prefix); other Gate A variables absent.

**ALLOWED MUTATIONS:** Only this fresh evidence directory, temporary owned runtime processes and explicitly granted experimental cleanup. No installation when binding already matches.

**FORBIDDEN MUTATIONS:** Product source, frozen tools/evidence, Stable/:1/HDMI, timers, judge thresholds, retries and any unnamed next cell. Global hard rules apply.

**EXACT EXECUTION STEPS:** 1. Complete PROFILE-R7 outer preflight; destination absence check happens BEFORE runner. 2. In authorized F8 shell set ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce and live SERIAL. 3. Run once: `CELL_ID=r7-p2 FAULT=present-renderer-exit FIXTURE=present WAIT_S=12 ROOT="$ROOT" SERIAL="$SERIAL" bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh`. Save actual exit status. 4. Run PROFILE-R7 frozen judge command with FAULT=present-renderer-exit, CELL="$ROOT/r7-p2" and real PRE-cleanup X/signal observations. 5. Independently audit identity, signal, forbidden events and cleanup; freeze verdict. Never loop this command.

**EXPECTED EVENTS:** 30 CALLBACK(src=4) → 35 → renderer exit → X HUP; event35 exactly once in sequence-deduplicated trace, enum/side=13 / renderer(2); matching session/generation/serial/src/dst. COPY consume must be constructed before death; no event34 or target ACK.

**EXPECTED FATAL / RESULT:** Last applicable GATEA_FATAL_HALT what=x-hup reason=6; X gone by frozen 12 s runner observation; no unexpected signal. Frozen judge exit0 `R7_PASS present-renderer-exit`; X exit127 is intended but do not invent an unobservable wait status.

**FORBIDDEN SUCCESS EVENTS:** After injection: 17 SUCCESS, 18/19 RELOCK, 20 REPAIR, 21 ACK, 22 PENDING_DEC, 23 LEASE_RELEASE; later PUBLISH > target S; event32 anywhere; Present event34 anywhere. No Gcomp Done, fallback/replay or same-generation continuation.

**STATIC VERIFICATION:** Read-only verify source, runner and fixture digests; check selected row against A04/A05. No source compile needed for unchanged installed artifact.

**HOST VERIFICATION:** A05 test-judge-r7.py must remain 16/16; rejudge this captured cell via frozen CLI, not a rewritten matcher. Aggregate audit at NEXT-013; unchanged host checks can be referenced by digest.

**CI REQUIREMENTS:** N/A — no product change; use already qualified exact CI 35103216566, do not dispatch new CI.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT exact APK/signature/Build ID and installed read-back. Version string alone insufficient. Mismatch stops before fixture.

**DEVICE PRECHECK:** PROFILE-R7 steps 1–5: grant, live identity/5038, awake display0, exact artifact, Stable baseline, no X3, entire destination absent, tool hashes, exact env captured.

**PASS CRITERIA:** All frozen judge predicates plus independent binding/signal/transaction/cleanup checks; expected x-hup/6; complete recorder evidence and one hook; Stable unchanged; actual process AND socket absence. Judge PASS alone is insufficient.

**BLOCKED CRITERIA:** Missing grant/artifact/fixture; changed authority; existing destination or X3; prior cell not PASS; unresolved observation gap before start. Do not invoke runner.

**INVALID CRITERIA:** Started with wrong env/artifact, absent hook/construction/identity, required trace gaps or unknown pre-cleanup X/signal state. Preserve original evidence. A bound forbidden product event is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-p2/ (must not exist). Any authorized new attempt uses an explicitly assigned fresh suffix, never automatic overwrite.

**EVIDENCE FILES:** Full PROFILE-R7 required evidence list, including command/real rc, tool hashes, raw trace/ring/summary, pre-cleanup identity and crash audit, frozen judge rc/output, independent acceptance, teardown, Stable before/after and SHA256 manifest.

**CLEANUP:** PROFILE-R7: preserve observation before cleanup; stop only verified owned fixture/holder/logcat/X3, force-stop experimental Activity, check exact socket/lock and process absence. If X survives deadline record FAIL before TERM. No poisoned-generation probe.

**STABLE AFTER-CHECK:** Compare before/after Stable PID+cmdline+version+lastUpdateTime; no replacement or configuration change. Missing comparison blocks acceptance.

**STATE TRANSITION:** R7-P2 NOT RUN → DEVICE_VALIDATED → CELL_PASS only if complete; otherwise VALID FAIL / INVALID / BLOCKED. R7 overall stays IN PROGRESS until NEXT-013.

**STOP CONDITION:** Always stop at this cell boundary unless an existing explicit batch grant names the next cell; any failure/invalidity/unknown signal or Stable deviation freezes evidence and stops batch.

**NEXT AUTHORIZATION:** NEXT-013 read-only aggregate; no R8 runtime permission.

## NEXT-013

**PACKET ID:** NEXT-013

**NAME:** R7 aggregate and immutable carry-forward audit

**CLASSIFICATION:** [R][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** R7 aggregate and immutable carry-forward audit; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A01–A05/A10/A14–A17. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-001…012 CELL_PASS; A14 existing R7-04 PASS. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-001…012 CELL_PASS; A14 existing R7-04 PASS

**USER AUTHORIZATION REQUIRED?:** Read-only audit/tests need no new device grant. New report publication or tag requires a scoped docs/tag grant; no runtime is authorized.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A01–A05/A10/A14–A17 and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** S01 gateAXFatal/gateADoneDirect; S04 firstFailed/generationFatal; only if lineage differs

**HARNESS / FIXTURE:** N/A — read-only evidence audit; existing frozen judge/analyzer may be replayed on immutable captured inputs with real rc.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Enumerate all 13 mandatory selectors: existing 04 plus the 12 packet cells; require a one-to-one path/source/tool-hash ledger. 2. Rejudge raw new cells using A05 CLI and their observed state, not assumed zeros; replay A14 PASS and A15 expected FAIL. 3. Verify frozen order, no missing hooks, forbidden events, unexpected crashes, Stable and cleanup per cell. 4. Record accepted fdfb1ce carry-forward of 7549e36 B-2 and historical R6 separately. 5. Write R7 aggregate with exact artifact binding and exclusions 12/13/14; update a new continuation record only under docs grant.

**EXPECTED EVENTS:** 13 mandatory cells accounted; 04 already qualified, others fresh PASS; historical halt_mismatch stays FAIL. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Explicit layer-specific result from steps; N/A — no device verdict from source/host/audit alone.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Validate evidence/schema completeness and replay only relevant existing frozen judges/analyzers with pinned inputs. Do not run runtime harnesses.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** All required cells PASS with lineage and independent audits; no missing evidence or unapproved carry-forward.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-013/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** R7-AGGREGATE.md; r7-cell-ledger.json; commands/rc; hashes; old/new rejudge outputs; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** Incomplete ledger → accepted named aggregate only if every required predicate passes; otherwise BLOCKED with exact missing claims.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-014 design review; STOP before any R8 runtime.

## NEXT-014

**PACKET ID:** NEXT-014

**NAME:** R8-DESIGN — resolve lifetime oracle and fixture gaps

**CLASSIFICATION:** [R][H] — PROPOSED packet. [H] DESIGN REQUIRED; dependent implementation/runtime is blocked until accepted.

**PURPOSE:** R8-DESIGN — resolve lifetime oracle and fixture gaps; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A06–A09/A18/A21; S01–S05. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-013 R7 GATE_PASS for runtime progression; read-only design may start earlier. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-013 R7 GATE_PASS for runtime progression; read-only design may start earlier

**USER AUTHORIZATION REQUIRED?:** Read-only research needs no new grant. Documentation under an existing scoped docs grant may proceed. Architecture adoption and all subsequent source/CI/install/device stages require explicit authorization.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A06–A09/A18/A21; S01–S05 and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** S01 gateARetireBufferId, gateACloseGeneration, lorieDestroyPixmap, lorieCloseScreen; S02 gateADrainPendingControls, gateADestroyReadyImport; S03 deferred record handling; Present retirement helper

**HARNESS / FIXTURE:** Future harness delivery contract in CONTRACT-DETAILS is mandatory: exact fixture CLI/count/hash, reachable schedule, real judge CLI and negative/legal-boundary cases. No runnable tool is implied by a proposed output filename.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Read CONTRACT-DETAILS R8 matrix and all eight blockers. 2. Resolve A07 ACK/destroy conflict against A18 ownership contract; define logical send and role-bound destroy→ACK partial order without relying on late SEND telemetry. 3. Freeze C1/C2/C3-window/C3-disconnect/C4/C5-full/C5-overflow/D/P1/P2, current root occupancy and units X16/READY16/pending8. 4. Prove reachable register-only and deferred-overlap construction; forbid timing sleeps and impossible synchronous client interleave. 5. Specify live pending/root snapshot and stable final two-role summary, with no frozen ABI mutation. 6. Freeze synthetic P1 guard claim versus real destructor claim, event5 proof, exact commands/judge/negative tests per Future harness delivery contract. 7. Record explicit architecture disposition and implementation allowlist.

**EXPECTED EVENTS:** Design maps create/hold/unlock/publish/terminal/destroy/ACK for both endpoints, Present and renderer; unresolved conflict stays BLOCKED. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** DESIGN_FROZEN only after reviewed output; N/A — no runtime verdict during design. Any later runtime result must be recorded separately.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Before dependent execution, deliver and pass exact judge/sampler/fixture host tests including false-green and false-red cases. Design text alone is not HOST_VERIFIED.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Reviewed executable lifecycle-cell-spec contains every subcell, direct evidence, legal-order exceptions and negative oracle; all mandatory construction gaps closed.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-014/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** R8-DESIGN.md; lifecycle-cell-spec.json; fixture-interface.md; judge-negative-cases.json; ownership ledger; source anchors; reviewed allowlist; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → DESIGN_FROZEN after acceptance; source/device layers remain NOT RUN until independently evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-015 only after design acceptance and bounded implementation grant.

## NEXT-015

**PACKET ID:** NEXT-015

**NAME:** R8-IMPLEMENT — reviewed support only

**CLASSIFICATION:** [U][L] — PROPOSED packet. [L] only after exact design is frozen; any new architecture returns to [H].

**PURPOSE:** R8-IMPLEMENT — reviewed support only; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A04–A09/A18/A20/A21 plus accepted R8-DESIGN.md. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-014 accepted with exact file/symbol allowlist. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-014 accepted with exact file/symbol allowlist

**USER AUTHORIZATION REQUIRED?:** YES — bounded source/harness allowlist. CI, install and runtime require separately named grants even if this packet describes their later sequence.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A04–A09/A18/A20/A21 plus accepted R8-DESIGN.md and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Only symbols frozen in NEXT-014; separate fixture/judge code from S01–S05 product observability

**HARNESS / FIXTURE:** PROFILE-HOST plus exact accepted design's real-source tests/judge. Missing complete source or commands is BLOCKED, never simulate a pass.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** Only accepted implementation allowlist in independent worktree, host outputs and separately authorized stage outputs.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Create one independent worktree at accepted product SHA (or docs/harness tree if host-only). 2. Implement only frozen CLI/fixtures, pending snapshots and lifecycle judge. 3. Preserve queue168/frame40/metadata48/fault40, counters28 and append-only event identity. 4. Add real-judge negative vectors for wrong role/tuple/resource, missing prefix, early ACK/release, hook absent and legal reverse log delivery/watermark coverage. 5. Compare diff against allowlist; any new ownership/protocol requirement returns to NEXT-014. 6. Commit bounded candidate under implementation grant.

**EXPECTED EVENTS:** Source and fixtures express accepted construction; no device evidence is claimed. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Explicit layer-specific result from steps; N/A — no device verdict from source/host/audit alone.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** PROFILE-HOST and accepted targeted real-helper/parser regressions; positive, missing evidence, wrong identity, forbidden order, legal watermark/reorder and historical PASS/FAIL cases; record real rc and complete source binding.

**CI REQUIREMENTS:** Separate CI boundary only if product source changed; host/harness-only changes do not justify APK CI.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Exact accepted behavior implemented with no unreviewed lifecycle, ABI, timeout or normal-path changes; candidate and test diffs reviewable.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-015/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** implementation report; source commit/diff; fixture/judge paths and hashes; test cases; regression impact ledger; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → SOURCE_FIXED → HOST_VERIFIED; any later stages remain gated and separately evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-016 host verification; no CI/install/device authorization implied.

## NEXT-016

**PACKET ID:** NEXT-016

**NAME:** R8-VERIFY — actual source and lifecycle oracle

**CLASSIFICATION:** [R][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** R8-VERIFY — actual source and lifecycle oracle; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A05/A09/A17/A20/A21 and NEXT-014 design. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-015 committed candidate; complete pinned source/submodules. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-015 committed candidate; complete pinned source/submodules

**USER AUTHORIZATION REQUIRED?:** Read-only audit/tests need no new device grant. New report publication or tag requires a scoped docs/tag grant; no runtime is authorized.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A05/A09/A17/A20/A21 and NEXT-014 design and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Implemented lifecycle producers/consumers and all retirement/ACK/release call sites in accepted allowlist

**HARNESS / FIXTURE:** PROFILE-HOST plus exact accepted design's real-source tests/judge. Missing complete source or commands is BLOCKED, never simulate a pass.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Run PROFILE-HOST tools against full candidate, with commands appropriate to tool version. 2. Run accepted lifecycle judge's positive, forbidden-input and legal-boundary vectors against actual parser/helpers. 3. Prove missing hook, late/foreign completion, duplicate conflict and pre-terminal resource release reject; legal T>=S and log delivery reorder accept. 4. Verify invocation safety: preexisting evidence/X3 rejected before mutation and warm/cold cleanup correctly separated. 5. If product changed, perform approved incremental/full-clean compile and patch apply/reverse checks. 6. Bind all rc/toolchain/source hashes and selected baseline rerun scope.

**EXPECTED EVENTS:** Host tests prove construction and oracle boundaries, not R8 runtime PASS. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Explicit layer-specific result from steps; N/A — no device verdict from source/host/audit alone.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** PROFILE-HOST and accepted targeted real-helper/parser regressions; positive, missing evidence, wrong identity, forbidden order, legal watermark/reorder and historical PASS/FAIL cases; record real rc and complete source binding.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** All accepted verifiers/regressions pass on exact candidate; no excerpt-only static green; required compile checks complete when relevant.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-016/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** HOST-VERIFICATION.md; commands/rc; test result manifest; patch checks; source/tool hashes; requalification ledger; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** SOURCE_FIXED → HOST_VERIFIED only; no device PASS.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-017 artifact work if product changed; otherwise skip CI with no-product-diff proof and request NEXT-018 device grant.

## NEXT-017

**PACKET ID:** NEXT-017

**NAME:** R8-CI and artifact qualification, conditional

**CLASSIFICATION:** [U][C][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** R8-CI and artifact qualification, conditional; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A10/A12/A21 plus accepted candidate and PROFILE-ARTIFACT. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-016 HOST_VERIFIED; product change requires explicit fork push/CI grant. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-016 HOST_VERIFIED; product change requires explicit fork push/CI grant

**USER AUTHORIZATION REQUIRED?:** YES — exact fork push/workflow/candidate grant. Artifact read-only checks can proceed without installation grant.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A10/A12/A21 plus accepted candidate and PROFILE-ARTIFACT and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Package applicationId and embedded libXlorie.so provenance; changed safety markers from accepted design

**HARNESS / FIXTURE:** Approved debug_build.yml + PROFILE-ARTIFACT; no runtime runner.

**REQUIRED ARTIFACT:** Exact newly host-verified approved source SHA; successful workflow then qualified APK manifest.

**RUNTIME ENVIRONMENT:** Authorized fork CI environment and local artifact inspection; no device connection.

**ALLOWED MUTATIONS:** Only authorized fork branch/workflow and new artifact records; no upstream or install.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. If only harness changed, record NO APK CHANGE and retain exact existing artifact; do not dispatch CI. 2. Otherwise push authorized fork candidate and dispatch approved debug_build.yml once; bind remote/run head to local full SHA. 3. Require multi-ABI workflow success; download exact archive and inspect integrity, package com.waydefu.x11gpu, signer, APK hash, ELF Build IDs and markers. 4. Save qualified manifest; do not install. 5. A failed build remains preserved and follows source/infrastructure triage, never arbitrary rerun.

**EXPECTED EVENTS:** CI_QUALIFIED then ARTIFACT_QUALIFIED only; not INSTALLED. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** CI and artifact qualification results only; N/A — no device fatal/result.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Prerequisite host tests must bind approved SHA; inspect archives and package metadata using exact recorded commands.

**CI REQUIREMENTS:** PROFILE-ARTIFACT on exact authorized source/remote/run head; never manually dispatch outside grant.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT mandatory, including digest object distinction, signer and Build IDs; future SHA must use its own manifest.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** PROFILE-ARTIFACT all bindings valid, or documented host-only no-product-diff skip.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-017/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** CI-ARTIFACT-PROVENANCE.md; run JSON; archive/APK/ELF hash manifest; signer/package/Build ID checks; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** HOST_VERIFIED → CI_QUALIFIED → ARTIFACT_QUALIFIED; INSTALLED remains outside this step.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** Separate install grant if candidate changed, then separate NEXT-018 runtime grant; one grant may explicitly name both actions.

## NEXT-018

**PACKET ID:** NEXT-018

**NAME:** R8-DEVICE — clean and pending lifecycle cells

**CLASSIFICATION:** [U][D][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** R8-DEVICE — clean and pending lifecycle cells; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A06–A09/A12/A18 plus accepted R8 lifecycle-cell-spec. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-014 design FROZEN; NEXT-016 host PASS; NEXT-017 artifact PASS or valid skip; authorized installed binding. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-014 design FROZEN; NEXT-016 host PASS; NEXT-017 artifact PASS or valid skip; authorized installed binding

**USER AUTHORIZATION REQUIRED?:** YES — exact candidate, installed binding, named cell list/counts, device/display and cleanup. Install separately if needed; no silent retry.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A06–A09/A12/A18 plus accepted R8 lifecycle-cell-spec and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** NEXT-014 lifetime sites; Present retirement helper; S02 resource destruction/control ACK

**HARNESS / FIXTURE:** Use the exact reviewed CLI/hash from the accepted dependency spec and CONTRACT-DETAILS matrix. If not yet delivered, BLOCKED [H] DESIGN REQUIRED; no speculative runner name is executable.

**REQUIRED ARTIFACT:** Exact candidate named by grant, qualified APK/signer/embedded+unstripped Build ID and live installed read-back; current fdfb1ce binding only if still applicable.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot, com.waydefu.x11gpu :3, Android display0, isolated ADB5038; clean cells PROTO=TELEMETRY=1, fault/arm absent; fault cells only exact reviewed selector/arm pair. Performance CPU twin uses separately frozen flags.

**ALLOWED MUTATIONS:** Fresh named evidence and only reviewed owned experimental processes/cleanup; no unlisted install or settings change.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Bind accepted installed candidate and reviewed new harness/judge digests. 2. Run each frozen C1/C2/C3-window/C3-disconnect/C4/C5-full/C5-overflow/D/P1/P2 once in its designated fresh session; cell order and count must come from approved lifecycle-cell-spec, never inferred from this summary. 3. Apply CONTRACT-DETAILS R8 construction predicates: C3 waited=0 or1 legal; D must demonstrate queued deferred record; P1 must prove event5. 4. Freeze and stop at first non-PASS; no automatic overlap retry. 5. Aggregate clean retirement/recovery and synthetic guard claims separately.

**EXPECTED EVENTS:** Clean cells exact success and role-bound destroy→ACK, balanced resources; P1 x-destroy-in-lease/7 and P2 x-close-in-lease/8 without normal release. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Clean cells exact success and role-bound destroy→ACK, balanced resources; P1 x-destroy-in-lease/7 and P2 x-close-in-lease/8 without normal release. A required fault fatal is not an unexpected crash; process death caused by cleanup is never the oracle.

**FORBIDDEN SUCCESS EVENTS:** No post-fatal same-generation PUBLISH/success/relock/repair/ACK/pending decrement/lease release; no pre-terminal Present idle/release, wrong-tuple acceptance or software fallback mislabeled direct. Apply cell-specific frozen exceptions exactly.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Accepted harness/judge host-verification record must bind actual hashes; no unverified fixture substitutions.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT mandatory, including digest object distinction, signer and Build IDs; future SHA must use its own manifest.

**DEVICE PRECHECK:** A12 live identity/5038; grant; exact package+ELF binding; Stable baseline; awake/unlocked display0; no unrelated X3; fresh absent evidence path; tool hashes; exact environment; required metrics accessible or approved disposition.

**PASS CRITERIA:** All accepted mandatory subcells and independent binding/Stable/cleanup audits PASS. Synthetic P1 alone does not certify actual destructor reachability.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Wrong artifact/env/identity, missing required trace, hook or schedule not constructed, wrong method/count, lost pre-cleanup observation. Freeze attempt; proven product violation is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-018/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** Per-cell raw events/ring/summary; pending/root snapshots; judge rc; fixture commands/hashes; clean/fatal process evidence; R8 aggregate; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** Capture verdict/process state before cleanup; stop only verified owned fixture/holder/logcat/X3; preserve Activity for reviewed warm rounds only, otherwise stop experimental Activity. Verify actual X3 PID/cmdline and socket/lock absence; no broad kill.

**STABLE AFTER-CHECK:** Mandatory captured Stable PID+cmdline+package version+lastUpdateTime comparison; unchanged. Missing evidence blocks acceptance.

**STATE TRANSITION:** NOT RUN → DEVICE_VALIDATED → CELL_PASS/GATE_PASS only at complete accepted scope; failures remain immutable.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-019 recreate design; no automatic R9 execution.

## NEXT-019

**PACKET ID:** NEXT-019

**NAME:** R9-DESIGN — fresh sessions and stale-state recovery

**CLASSIFICATION:** [R][H] — PROPOSED packet. [H] DESIGN REQUIRED; dependent implementation/runtime is blocked until accepted.

**PURPOSE:** R9-DESIGN — fresh sessions and stale-state recovery; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A06–A09/A18/A21; S01–S05; CONTRACT-DETAILS R9 matrix. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-018 R8 PASS for device progression; accepted R8 tools. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-018 R8 PASS for device progression; accepted R8 tools

**USER AUTHORIZATION REQUIRED?:** Read-only research needs no new grant. Documentation under an existing scoped docs grant may proceed. Architecture adoption and all subsequent source/CI/install/device stages require explicit authorization.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A06–A09/A18/A21; S01–S05; CONTRACT-DETAILS R9 matrix and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** OsVendorInit, lorieCloseScreen, gateACloseGeneration, gateABindFromState, lorieGateABoundTuple, lorieGateAUnbindTuple, handleGateARecord; pinned xserver reset/launch flags

**HARNESS / FIXTURE:** Future harness delivery contract in CONTRACT-DETAILS is mandatory: exact fixture CLI/count/hash, reachable schedule, real judge CLI and negative/legal-boundary cases. No runnable tool is implied by a proposed output filename.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Define warm3 fresh X with same Activity PID/starttime and cold3 with experimental force-stop between rounds. 2. Trace actual same-X reset and nonce regeneration; disposition R9-3 as reachable with exact trigger or BLOCKED/explicit supported-scope decision. 3. Specify F1 stale-ready-replay synthetic old tuple after valid READY; do not claim captured-frame replay. 4. Specify F2 fresh-session exact SUCCESS immediately after F1 authorized cleanup, registry empty and nonce new. 5. Freeze no-old-completion/registry/fatal/serial/mapping acceptance, dedicated warm cleanup, judge CLI and negatives. 6. Route any source change through NEXT-015/016/017 with a new R9 allowlist and grants, not the old R8 mutation scope.

**EXPECTED EVENTS:** A reviewed R9 cell spec binds old/new mapping, nonce, generation, buffer IDs and Activity starttime; stale-frame rejection separated from valid READY. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** DESIGN_FROZEN only after reviewed output; N/A — no runtime verdict during design. Any later runtime result must be recorded separately.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Before dependent execution, deliver and pass exact judge/sampler/fixture host tests including false-green and false-red cases. Design text alone is not HOST_VERIFIED.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Every R9 mandatory claim has reachable deterministic construction, complete observation and fresh recovery; reset scope explicitly resolved.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-019/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** R9-DESIGN.md; r9-cell-spec.json; warm/cold harness CLI; judge vectors; reset disposition; source impact ledger; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → DESIGN_FROZEN after acceptance; source/device layers remain NOT RUN until independently evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** Implement/host-verify accepted harness through scoped NEXT-015–017 profiles as needed, then NEXT-020 device grant.

## NEXT-020

**PACKET ID:** NEXT-020

**NAME:** R9-DEVICE — warm/cold recreate and recovery

**CLASSIFICATION:** [U][D][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** R9-DEVICE — warm/cold recreate and recovery; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A06/A07/A12/A18 plus FROZEN R9-DESIGN. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-018 PASS; NEXT-019 accepted; R9 harness/judge HOST_VERIFIED; exact installed artifact qualified. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-018 PASS; NEXT-019 accepted; R9 harness/judge HOST_VERIFIED; exact installed artifact qualified

**USER AUTHORIZATION REQUIRED?:** YES — exact candidate, installed binding, named cell list/counts, device/display and cleanup. Install separately if needed; no silent retry.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A06/A07/A12/A18 plus FROZEN R9-DESIGN and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** NEXT-019 tuple/bind/unbind sites; S02 stale-ready-replay hook

**HARNESS / FIXTURE:** Use the exact reviewed CLI/hash from the accepted dependency spec and CONTRACT-DETAILS matrix. If not yet delivered, BLOCKED [H] DESIGN REQUIRED; no speculative runner name is executable.

**REQUIRED ARTIFACT:** Exact candidate named by grant, qualified APK/signer/embedded+unstripped Build ID and live installed read-back; current fdfb1ce binding only if still applicable.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot, com.waydefu.x11gpu :3, Android display0, isolated ADB5038; clean cells PROTO=TELEMETRY=1, fault/arm absent; fault cells only exact reviewed selector/arm pair. Performance CPU twin uses separately frozen flags.

**ALLOWED MUTATIONS:** Fresh named evidence and only reviewed owned experimental processes/cleanup; no unlisted install or settings change.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Use dedicated reviewed R9 harness, never R7 force-stop cleanup for warm rounds. 2. Execute warm3 and cold3 exactly as frozen; record X/Activity PID+starttime, nonce/gen and zero registry at each admission. 3. Execute R9-3 only under accepted reachable/reset scope. 4. Execute F1 once with exact fault env, enum16/side2, x-wrong-generation/6; legitimate initial READY is allowed. 5. After owned cleanup execute separately granted F2 once: new nonce, empty registry, exact direct success. 6. Aggregate only after each round's clean close, resource accounting and no X3 residue.

**EXPECTED EVENTS:** Normal sessions READY→PUBLISH→SUCCESS→retirement→CLOSED; F1 35→x-wrong-generation/6; F2 fresh valid success. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Normal sessions READY→PUBLISH→SUCCESS→retirement→CLOSED; F1 35→x-wrong-generation/6; F2 fresh valid success. A required fault fatal is not an unexpected crash; process death caused by cleanup is never the oracle.

**FORBIDDEN SUCCESS EVENTS:** No post-fatal same-generation PUBLISH/success/relock/repair/ACK/pending decrement/lease release; no pre-terminal Present idle/release, wrong-tuple acceptance or software fallback mislabeled direct. Apply cell-specific frozen exceptions exactly.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Accepted harness/judge host-verification record must bind actual hashes; no unverified fixture substitutions.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT mandatory, including digest object distinction, signer and Build IDs; future SHA must use its own manifest.

**DEVICE PRECHECK:** A12 live identity/5038; grant; exact package+ELF binding; Stable baseline; awake/unlocked display0; no unrelated X3; fresh absent evidence path; tool hashes; exact environment; required metrics accessible or approved disposition.

**PASS CRITERIA:** All mandatory warm/cold/reset-disposition/F1/F2 claims pass; no reused old tuple/resource state; real recovery observed.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Wrong artifact/env/identity, missing required trace, hook or schedule not constructed, wrong method/count, lost pre-cleanup observation. Freeze attempt; proven product violation is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-020/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** round ledger; raw tuple/event/summary captures; Activity identity; stale frame and F2 evidence; judge rc; R9 aggregate; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** Capture verdict/process state before cleanup; stop only verified owned fixture/holder/logcat/X3; preserve Activity for reviewed warm rounds only, otherwise stop experimental Activity. Verify actual X3 PID/cmdline and socket/lock absence; no broad kill.

**STABLE AFTER-CHECK:** Mandatory captured Stable PID+cmdline+package version+lastUpdateTime comparison; unchanged. Missing evidence blocks acceptance.

**STATE TRANSITION:** NOT RUN → DEVICE_VALIDATED → CELL_PASS/GATE_PASS only at complete accepted scope; failures remain immutable.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-021 R10 sampler design; no R10 runtime grant implied.

## NEXT-021

**PACKET ID:** NEXT-021

**NAME:** R10-DESIGN — measurable resource ledger

**CLASSIFICATION:** [R][H] — PROPOSED packet. [H] DESIGN REQUIRED; dependent implementation/runtime is blocked until accepted.

**PURPOSE:** R10-DESIGN — measurable resource ledger; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A06/A07 D-7/A09/A21; CONTRACT-DETAILS R10 checkpoints. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-020 R9 PASS for later execution; R8 live pending instrumentation verified. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-020 R9 PASS for later execution; R8 live pending instrumentation verified

**USER AUTHORIZATION REQUIRED?:** Read-only research needs no new grant. Documentation under an existing scoped docs grant may proceed. Architecture adoption and all subsequent source/CI/install/device stages require explicit authorization.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A06/A07 D-7/A09/A21; CONTRACT-DETAILS R10 checkpoints and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** S04 counter enum; S03 current registry; meta.pendingCount; rootGpuCopyPending; S02 AHB/EGLImage/texture create/destroy

**HARNESS / FIXTURE:** Future harness delivery contract in CONTRACT-DETAILS is mandatory: exact fixture CLI/count/hash, reachable schedule, real judge CLI and negative/legal-boundary cases. No runnable tool is implied by a proposed output filename.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Freeze >=5 clean rounds, PROPOSED warm3+cold2 and N=64; bind pair sizes and current root occupancy. 2. Freeze K0 bind/pre-direct, K1 after fixed repeats, K2 after frees, K3 clean close. 3. Specify permission-aware X/Activity FD, RSS/PSS, gauges18–20, balances12/13,14/15,16/17, live pending/root and socket/process capture. 4. Define equivalent-checkpoint no-monotonic-growth interpretation and raw-series report, no invented RSS threshold. 5. K3 dead X is process absence, not FD=0; preserve pre-exit summary. 6. Freeze parser CLI and missing-data negative tests; record D-7 path for inaccessible Activity FD before runtime.

**EXPECTED EVENTS:** Every metric has source, checkpoint, nullable type, units, required/diagnostic role and exact acceptance; c11 cannot stand in for current pending. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** DESIGN_FROZEN only after reviewed output; N/A — no runtime verdict during design. Any later runtime result must be recorded separately.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Before dependent execution, deliver and pass exact judge/sampler/fixture host tests including false-green and false-red cases. Design text alone is not HOST_VERIFIED.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Concrete sampler/judge ready and host-tested; known observability limitations have explicit disposition route; no invented counters/thresholds.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-021/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** R10-MEASUREMENT-SPEC.md; sampler/judge CLI+hashes; resource-schema.json; negative cases; D-7 decision template; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → DESIGN_FROZEN after acceptance; source/device layers remain NOT RUN until independently evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-022 grant only after accepted sampler and tests; any new source observation change follows scoped implementation/CI pipeline.

## NEXT-022

**PACKET ID:** NEXT-022

**NAME:** R10-DEVICE — residue accounting

**CLASSIFICATION:** [U][D][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** R10-DEVICE — residue accounting; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A06/A07/A12/A21 and accepted R10-MEASUREMENT-SPEC. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-020 PASS; NEXT-021 accepted/HOST_VERIFIED; exact qualified installed artifact. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-020 PASS; NEXT-021 accepted/HOST_VERIFIED; exact qualified installed artifact

**USER AUTHORIZATION REQUIRED?:** YES — exact candidate, installed binding, named cell list/counts, device/display and cleanup. Install separately if needed; no silent retry.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A06/A07/A12/A21 and accepted R10-MEASUREMENT-SPEC and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Read-only resource sites listed in NEXT-021

**HARNESS / FIXTURE:** Use the exact reviewed CLI/hash from the accepted dependency spec and CONTRACT-DETAILS matrix. If not yet delivered, BLOCKED [H] DESIGN REQUIRED; no speculative runner name is executable.

**REQUIRED ARTIFACT:** Exact candidate named by grant, qualified APK/signer/embedded+unstripped Build ID and live installed read-back; current fdfb1ce binding only if still applicable.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot, com.waydefu.x11gpu :3, Android display0, isolated ADB5038; clean cells PROTO=TELEMETRY=1, fault/arm absent; fault cells only exact reviewed selector/arm pair. Performance CPU twin uses separately frozen flags.

**ALLOWED MUTATIONS:** Fresh named evidence and only reviewed owned experimental processes/cleanup; no unlisted install or settings change.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Preflight then run frozen >=5 rounds once with K0/K1/K2/K3 captures, warm/cold order and N fixed in spec. 2. Compare equivalent FD checkpoints and direct live pending at K2. 3. Require tracked resource balances c12=c13,c14=c15,c16=c17 and c18=c19=c20=0 at clean K3. 4. Keep unavailable metrics null/not_observable with error/rc; inaccessible Activity FD stops for explicit D-7 decision. 5. Record RSS/PSS/threads/maps descriptively. 6. Check process AND socket absence each round; optional 4K churn requires separate grant and K in buffer slots.

**EXPECTED EVENTS:** Clean lifetime/resource retirement; no unexpected fatal; equivalent FD series without repeat-per-cycle growth; no X3 residue. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Clean lifetime/resource retirement; no unexpected fatal; equivalent FD series without repeat-per-cycle growth; no X3 residue. A required fault fatal is not an unexpected crash; process death caused by cleanup is never the oracle.

**FORBIDDEN SUCCESS EVENTS:** No post-fatal same-generation PUBLISH/success/relock/repair/ACK/pending decrement/lease release; no pre-terminal Present idle/release, wrong-tuple acceptance or software fallback mislabeled direct. Apply cell-specific frozen exceptions exactly.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Accepted harness/judge host-verification record must bind actual hashes; no unverified fixture substitutions.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT mandatory, including digest object distinction, signer and Build IDs; future SHA must use its own manifest.

**DEVICE PRECHECK:** A12 live identity/5038; grant; exact package+ELF binding; Stable baseline; awake/unlocked display0; no unrelated X3; fresh absent evidence path; tool hashes; exact environment; required metrics accessible or approved disposition.

**PASS CRITERIA:** Frozen resource predicates, pending observation, Stable and cleanup satisfied. PASS WITH OBSERVABILITY LIMITATION only with explicit D-7 decision and exact missing claim, never full PASS by zero-fill.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Wrong artifact/env/identity, missing required trace, hook or schedule not constructed, wrong method/count, lost pre-cleanup observation. Freeze attempt; proven product violation is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-022/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** raw per-round checkpoint files; resource-series.json; permission errors; counters and pending snapshots; judge rc; R10 aggregate; D-7 decision if any; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** Capture verdict/process state before cleanup; stop only verified owned fixture/holder/logcat/X3; preserve Activity for reviewed warm rounds only, otherwise stop experimental Activity. Verify actual X3 PID/cmdline and socket/lock absence; no broad kill.

**STABLE AFTER-CHECK:** Mandatory captured Stable PID+cmdline+package version+lastUpdateTime comparison; unchanged. Missing evidence blocks acceptance.

**STATE TRANSITION:** NOT RUN → DEVICE_VALIDATED → CELL_PASS/GATE_PASS only at complete accepted scope; failures remain immutable.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-023 read-only P2 closure audit.

## NEXT-023

**PACKET ID:** NEXT-023

**NAME:** Gate A P2 runtime closure ledger

**CLASSIFICATION:** [R][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** Gate A P2 runtime closure ledger; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A01–A10/A14–A18/A21; P2-CLOSURE.json. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-013/018/020/022 accepted aggregates; approved candidate carry-forward. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-013/018/020/022 accepted aggregates; approved candidate carry-forward

**USER AUTHORIZATION REQUIRED?:** Read-only audit/tests need no new device grant. New report publication or tag requires a scoped docs/tag grant; no runtime is authorized.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A01–A10/A14–A18/A21; P2-CLOSURE.json and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Only touched-symbol lineage ledger for baseline carry-forward; no source edit

**HARNESS / FIXTURE:** N/A — read-only evidence audit; existing frozen judge/analyzer may be replayed on immutable captured inputs with real rc.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Copy P2-CLOSURE.json into a fresh closure evidence directory; never overwrite the planning snapshot or historical records. 2. Resolve each required item to artifact/tool/attempt/claim and attach raw evidence or a verified immutable report plus approved carry-forward. 3. Require R0–R10 coverage including R4/R5/R6; retain accepted R5 scope limitation only for that evidence. 4. Evaluate per-cell counter consistency, zero UNEXPECTED fatal, Stable, no X3 residue and documentation completeness. 5. Keep bounded XFCE separate as V1-Core requirement. 6. Compute closure as conjunction of required satisfied items and accepted carry-forward; null/pending/blocked never pass. Publish exact gaps if not closable.

**EXPECTED EVENTS:** P2_RUNTIME_CLOSED only after full ledger; expected R7/R8-P/R9-F fatal remains legal; no Production Gate A upgrade. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Explicit layer-specific result from steps; N/A — no device verdict from source/host/audit alone.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Validate evidence/schema completeness and replay only relevant existing frozen judges/analyzers with pinned inputs. Do not run runtime harnesses.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Every required closure item satisfied with reviewed artifact binding; all limitations explicitly accepted; no pending required item.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-023/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** completed closure JSON copy; P2-CLOSURE-REPORT.md; source/carry-forward matrix; immutable evidence links+hashes; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** Incomplete ledger → accepted named aggregate only if every required predicate passes; otherwise BLOCKED with exact missing claims.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-024 bounded XFCE design/execution boundary; NEXT-025 performance design; production gap audit can proceed read-only.

## NEXT-024

**PACKET ID:** NEXT-024

**NAME:** Bounded XFCE qualification design and controlled execution

**CLASSIFICATION:** [R][H] — PROPOSED packet. [H] DESIGN REQUIRED; dependent implementation/runtime is blocked until accepted.

**PURPOSE:** Bounded XFCE qualification design and controlled execution; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A03/A07/A19/A21; MASTER-PLAN V1-Core and Gate W. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-023 P2 closed before runtime; current candidate qualified. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-023 P2 closed before runtime; current candidate qualified

**USER AUTHORIZATION REQUIRED?:** Read-only research needs no new grant. Documentation under an existing scoped docs grant may proceed. Architecture adoption and all subsequent source/CI/install/device stages require explicit authorization.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A03/A07/A19/A21; MASTER-PLAN V1-Core and Gate W and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** S01 lorieRRScreenSetSize, lorieDestroyPixmap, EXA Copy/Solid/Composite entrypoints; Present retirement

**HARNESS / FIXTURE:** Future harness delivery contract in CONTRACT-DETAILS is mandatory: exact fixture CLI/count/hash, reachable schedule, real judge CLI and negative/legal-boundary cases. No runnable tool is implied by a proposed output filename.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Freeze a small deterministic XFCE script on experimental :3/display0, compositor off/on, window create/move/overlap/normal resize/destroy, terminal/panel expose and exact pixel probes. 2. Specify current geometry/refresh, bounded duration/action counts, CPU/direct env and tuple/path observability; do not inherit historical 45s as current proof. 3. Deliver fixture, exact CLI, judge, negative missing-redraw cases and cleanup; host-verify before requesting a device grant. 4. Under a later explicit execution grant only, run the frozen script once per specified mode, stopping on first invalidity/failure. 5. Report smoke scope separately from Gate W's longer release workload.

**EXPECTED EVENTS:** PROPOSED design first; later current-artifact exact redraw/path and clean teardown with zero unexpected fatal; historical P2-A remains closed. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** DESIGN_FROZEN only after reviewed output; N/A — no runtime verdict during design. Any later runtime result must be recorded separately.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Before dependent execution, deliver and pass exact judge/sampler/fixture host tests including false-green and false-red cases. Design text alone is not HOST_VERIFIED.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Design acceptance alone yields DESIGN_FROZEN. Runtime PASS requires recorded authorized execution, oracle, resource/Stable checks and current candidate binding; never equate the two.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-024/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** XFCE-BOUNDED-SPEC.md; script/judge hash; exact counts; when authorized runtime evidence and separate verdict; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → DESIGN_FROZEN after acceptance; source/device layers remain NOT RUN until independently evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** Explicit device grant after design freeze; after bounded qualification NEXT-025/026. Gate W remains separately required.

## NEXT-025

**PACKET ID:** NEXT-025

**NAME:** P2-B.3 measurement design

**CLASSIFICATION:** [R][H] — PROPOSED packet. [H] DESIGN REQUIRED; dependent implementation/runtime is blocked until accepted.

**PURPOSE:** P2-B.3 measurement design; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A07/A19/A21; MASTER-PLAN P2-B.3. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-023 P2 closed; NEXT-024 bounded workload contract and qualification before measurement. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-023 P2 closed; NEXT-024 bounded workload contract and qualification before measurement

**USER AUTHORIZATION REQUIRED?:** Read-only research needs no new grant. Documentation under an existing scoped docs grant may proceed. Architecture adoption and all subsequent source/CI/install/device stages require explicit authorization.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A07/A19/A21; MASTER-PLAN P2-B.3 and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** S01 gateADirectTryPrepare and CPU-disable selection order; S02 direct/staging dispatch; S04 telemetry fields

**HARNESS / FIXTURE:** Future harness delivery contract in CONTRACT-DETAILS is mandatory: exact fixture CLI/count/hash, reachable schedule, real judge CLI and negative/legal-boundary cases. No runnable tool is implied by a proposed output filename.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Prove reachable modes on exact candidate: CPU with TERMUX_X11_DISABLE_EXA_GPU=1 and PROTO unset; direct with PROTO=1 and CPU-disable unset. 2. Trace-on validation twin must show intended path; only include staging/D0a if source proves a distinct selectable mode; exclude D0b. 3. Freeze 8 size buckets and mixed desktop damage, cold/reuse, common geometry, warmup and >=500 measured operations/cell, >=3 paired sessions ABBA as PROPOSED method. 4. Primary no-readback batched redraw with final exact pixels; immediate GetImage is control only. 5. Freeze trace-off primary wall timing, thermal/charging/compositor controls, paired median/p95/noise in same units, raw samples and analysis CLI. 6. Missing GPU duration remains null; validate wrong-path and incomplete-sample rejection.

**EXPECTED EVENTS:** Design distinguishes path proof, exact correctness and performance effect; no automatic speedup from old D0a data. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** DESIGN_FROZEN only after reviewed output; N/A — no runtime verdict during design. Any later runtime result must be recorded separately.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Before dependent execution, deliver and pass exact judge/sampler/fixture host tests including false-green and false-red cases. Design text alone is not HOST_VERIFIED.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Frozen reproducible experiment and actual-path proof, executable collector/analyzer with false-green/false-red cases, no unsupported telemetry claims.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-025/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** P2-B3-MEASUREMENT-SPEC.md; mode/source table; fixture+analyzer CLI/hashes; sample schema; method acceptance; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → DESIGN_FROZEN after acceptance; source/device layers remain NOT RUN until independently evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-026 explicit measurement grant after host validation.

## NEXT-026

**PACKET ID:** NEXT-026

**NAME:** P2-B.3 paired workload measurement

**CLASSIFICATION:** [U][D][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** P2-B.3 paired workload measurement; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A07/A12/A19/A21 plus accepted measurement spec. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-023 closed; NEXT-024 qualified; NEXT-025 frozen/HOST_VERIFIED. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-023 closed; NEXT-024 qualified; NEXT-025 frozen/HOST_VERIFIED

**USER AUTHORIZATION REQUIRED?:** YES — exact candidate, installed binding, named cell list/counts, device/display and cleanup. Install separately if needed; no silent retry.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A07/A12/A19/A21 plus accepted measurement spec and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Read-only mode selectors and relevant event producers from NEXT-025

**HARNESS / FIXTURE:** Use the exact reviewed CLI/hash from the accepted dependency spec and CONTRACT-DETAILS matrix. If not yet delivered, BLOCKED [H] DESIGN REQUIRED; no speculative runner name is executable.

**REQUIRED ARTIFACT:** Exact candidate named by grant, qualified APK/signer/embedded+unstripped Build ID and live installed read-back; current fdfb1ce binding only if still applicable.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot, com.waydefu.x11gpu :3, Android display0, isolated ADB5038; clean cells PROTO=TELEMETRY=1, fault/arm absent; fault cells only exact reviewed selector/arm pair. Performance CPU twin uses separately frozen flags.

**ALLOWED MUTATIONS:** Fresh named evidence and only reviewed owned experimental processes/cleanup; no unlisted install or settings change.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Bind artifact and mode configuration; collect trace-on identity/exactness twins. 2. Run only frozen paired ABBA sessions, buckets and counts; capture environmental conditions and raw timings with actual rc. 3. Validate final pixels; no reading back every primary timed operation. 4. Run pinned analyzer; report paired median/p95 and repeat-session noise in matching units. 5. Classify correctness separately from PERFORMANCE POSITIVE/NEGATIVE/INCONCLUSIVE; save path coverage and missing metrics. 6. Stop after predefined run count; no repeats until faster.

**EXPECTED EVENTS:** Exact pixels and proven target path; measured effect may be negative or inconclusive without correctness failure. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Exact pixels and proven target path; measured effect may be negative or inconclusive without correctness failure. A required fault fatal is not an unexpected crash; process death caused by cleanup is never the oracle.

**FORBIDDEN SUCCESS EVENTS:** No post-fatal same-generation PUBLISH/success/relock/repair/ACK/pending decrement/lease release; no pre-terminal Present idle/release, wrong-tuple acceptance or software fallback mislabeled direct. Apply cell-specific frozen exceptions exactly.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Accepted harness/judge host-verification record must bind actual hashes; no unverified fixture substitutions.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT mandatory, including digest object distinction, signer and Build IDs; future SHA must use its own manifest.

**DEVICE PRECHECK:** A12 live identity/5038; grant; exact package+ELF binding; Stable baseline; awake/unlocked display0; no unrelated X3; fresh absent evidence path; tool hashes; exact environment; required metrics accessible or approved disposition.

**PASS CRITERIA:** Method-complete measurement and valid correctness/path proof. Only repeatable improvement beyond measured noise supports positive performance; release predicate remains distinct.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Wrong artifact/env/identity, missing required trace, hook or schedule not constructed, wrong method/count, lost pre-cleanup observation. Freeze attempt; proven product violation is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-026/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** raw timings; paired statistics; environment ledger; trace-on path/oracle evidence; PERFORMANCE-REPORT.md; cleanup/Stable; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** Capture verdict/process state before cleanup; stop only verified owned fixture/holder/logcat/X3; preserve Activity for reviewed warm rounds only, otherwise stop experimental Activity. Verify actual X3 PID/cmdline and socket/lock absence; no broad kill.

**STABLE AFTER-CHECK:** Mandatory captured Stable PID+cmdline+package version+lastUpdateTime comparison; unchanged. Missing evidence blocks acceptance.

**STATE TRANSITION:** NOT RUN → DEVICE_VALIDATED → CELL_PASS/GATE_PASS only at complete accepted scope; failures remain immutable.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-027 production gap design; final changed candidate must refresh affected measurements at NEXT-031.

## NEXT-027

**PACKET ID:** NEXT-027

**NAME:** Production Gate A minimal V1-Core gap design

**CLASSIFICATION:** [R][H] — PROPOSED packet. [H] DESIGN REQUIRED; dependent implementation/runtime is blocked until accepted.

**PURPOSE:** Production Gate A minimal V1-Core gap design; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A07 D-1/D-2/A08/A09/A18/A21/A22; MASTER-PLAN gap audit. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** Current source and NEXT-018/020/022 findings; mutations gated after accepted design. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** Current source and NEXT-018/020/022 findings; mutations gated after accepted design

**USER AUTHORIZATION REQUIRED?:** Read-only research needs no new grant. Documentation under an existing scoped docs grant may proceed. Architecture adoption and all subsequent source/CI/install/device stages require explicit authorization.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A07 D-1/D-2/A08/A09/A18/A21/A22; MASTER-PLAN gap audit and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** S01 lorieGpuCopyWait, gateAEnsureReady, gateADirectTryPrepare, lorieRRScreenSetSize, gateARetireBufferId; S02 REGISTER_FAILED cleanup; S03 ownerRef and registry; S05 gateABindFromState

**HARNESS / FIXTURE:** Future harness delivery contract in CONTRACT-DETAILS is mandatory: exact fixture CLI/count/hash, reachable schedule, real judge CLI and negative/legal-boundary cases. No runnable tool is implied by a proposed output filename.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Build supported lifecycle state table covering connected no-surface/loss/resume, clean close/fresh warm/cold restart, capacity refusal/recovery, failed-register retirement and normal root resize. 2. Resolve D-1 accepted wait/requeue versus current immediate !lorieRendererAvailable failure; specify progress deadline and R6-D3 proof without blanket timeout expansion. 3. Prove inactive registered buffer/active pair/root lifetime against A18 ownerRef/ROOT_READY obligations; accept equivalence explicitly or design required correction. 4. Classify every historical gap CLOSED/PARTIAL/BLOCKER/DEFERABLE/OBSOLETE with source proof. 5. Exclude LRU/registration optimization unless workload demonstrates necessity. 6. Freeze per-file changes, memory order, exact regressions/negative tests and baseline carry-forward. Seamless poisoned-work replay remains excluded.

**EXPECTED EVENTS:** Minimal accepted product design; no unsupported waiver of ownership contracts; renderer death remains fail-stop then fresh session. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** DESIGN_FROZEN only after reviewed output; N/A — no runtime verdict during design. Any later runtime result must be recorded separately.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Before dependent execution, deliver and pass exact judge/sampler/fixture host tests including false-green and false-red cases. Design text alone is not HOST_VERIFIED.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Each V1-Core blocker has exact reachable failing edge, ownership-safe design and test deliverable; no unresolved ABI/lifecycle decision hidden in [L].

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-027/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** PRODUCTION-GATE-A-DESIGN.md; lifetime/release ledger; accepted equivalence decisions; implementation allowlist; requalification matrix; R6-D3 construction; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → DESIGN_FROZEN after acceptance; source/device layers remain NOT RUN until independently evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-028 separately authorized bounded source implementation.

## NEXT-028

**PACKET ID:** NEXT-028

**NAME:** Production corrections — implementation and host proof

**CLASSIFICATION:** [U][L] — PROPOSED packet. [L] only after exact design is frozen; any new architecture returns to [H].

**PURPOSE:** Production corrections — implementation and host proof; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A09/A17/A18/A20/A21 and production design. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-027 accepted exact allowlist and implementation grant. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-027 accepted exact allowlist and implementation grant

**USER AUTHORIZATION REQUIRED?:** YES — bounded source/harness allowlist. CI, install and runtime require separately named grants even if this packet describes their later sequence.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A09/A17/A18/A20/A21 and production design and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Only NEXT-027 accepted surface/root/registry/retirement sites; all ACK/release sites audited

**HARNESS / FIXTURE:** PROFILE-HOST plus exact accepted design's real-source tests/judge. Missing complete source or commands is BLOCKED, never simulate a pass.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** Only accepted implementation allowlist in independent worktree, host outputs and separately authorized stage outputs.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Create clean independent worktree at approved base. 2. Implement only necessary reviewed blockers, preserving fail-stop and narrow predicate. 3. Add regression tests on actual code for each accepted failure edge before claiming fix. 4. Execute PROFILE-HOST plus exact design regressions and memory-order/static release-site checks. 5. Select minimum affected baseline via MASTER-PLAN table; uncertain scope returns to design. 6. Commit candidate and report SOURCE_FIXED separately from HOST_VERIFIED; no CI/device yet.

**EXPECTED EVENTS:** Reviewed source correction and host proof; no production or device PASS implied. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Explicit layer-specific result from steps; N/A — no device verdict from source/host/audit alone.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** PROFILE-HOST and accepted targeted real-helper/parser regressions; positive, missing evidence, wrong identity, forbidden order, legal watermark/reorder and historical PASS/FAIL cases; record real rc and complete source binding.

**CI REQUIREMENTS:** Separate CI boundary only if product source changed; host/harness-only changes do not justify APK CI.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Accepted invariants and real-source positive/negative/edge tests pass; diff confined to allowlist and exact requalification plan approved.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-028/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** implementation+host report; commit/diff; commands/rc; static release audit; regression scope; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → SOURCE_FIXED → HOST_VERIFIED; any later stages remain gated and separately evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-029 fork CI/artifact grant.

## NEXT-029

**PACKET ID:** NEXT-029

**NAME:** Production candidate CI and artifact binding

**CLASSIFICATION:** [U][C][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** Production candidate CI and artifact binding; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A10/A21; accepted production design; PROFILE-ARTIFACT. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-028 HOST_VERIFIED; explicit fork push/CI grant. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-028 HOST_VERIFIED; explicit fork push/CI grant

**USER AUTHORIZATION REQUIRED?:** YES — exact fork push/workflow/candidate grant. Artifact read-only checks can proceed without installation grant.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A10/A21; accepted production design; PROFILE-ARTIFACT and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Candidate package/signature/ELF and required safety marker bindings

**HARNESS / FIXTURE:** Approved debug_build.yml + PROFILE-ARTIFACT; no runtime runner.

**REQUIRED ARTIFACT:** Exact newly host-verified approved source SHA; successful workflow then qualified APK manifest.

**RUNTIME ENVIRONMENT:** Authorized fork CI environment and local artifact inspection; no device connection.

**ALLOWED MUTATIONS:** Only authorized fork branch/workflow and new artifact records; no upstream or install.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Push only approved candidate to fork, never upstream. 2. Dispatch approved debug_build.yml once and bind headSHA. 3. Execute full PROFILE-ARTIFACT provenance checks; retain build failures. 4. Write immutable qualified manifest and exact installation/requalification request. 5. Do not install in this artifact packet.

**EXPECTED EVENTS:** Exact-source CI_QUALIFIED and ARTIFACT_QUALIFIED; no runtime claim. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** CI and artifact qualification results only; N/A — no device fatal/result.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Prerequisite host tests must bind approved SHA; inspect archives and package metadata using exact recorded commands.

**CI REQUIREMENTS:** PROFILE-ARTIFACT on exact authorized source/remote/run head; never manually dispatch outside grant.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT mandatory, including digest object distinction, signer and Build IDs; future SHA must use its own manifest.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Complete successful artifact binding, signer continuity and required safety markers; no stale build substitution.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-029/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** run JSON; CI/artifact report; APK+ELF hashes; package+signer+Build ID; required install manifest; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** HOST_VERIFIED → CI_QUALIFIED → ARTIFACT_QUALIFIED; INSTALLED remains outside this step.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** Separate install and NEXT-030 runtime grants.

## NEXT-030

**PACKET ID:** NEXT-030

**NAME:** Production lifecycle and affected baseline qualification

**CLASSIFICATION:** [U][D][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** Production lifecycle and affected baseline qualification; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A09/A12/A18/A21 and accepted production requalification matrix. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-029 qualified; authorized installation/read-back; NEXT-027 tests frozen; exact regression grant. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-029 qualified; authorized installation/read-back; NEXT-027 tests frozen; exact regression grant

**USER AUTHORIZATION REQUIRED?:** YES — exact candidate, installed binding, named cell list/counts, device/display and cleanup. Install separately if needed; no silent retry.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A09/A12/A18/A21 and accepted production requalification matrix and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Only NEXT-027 accepted changed semantics; Present retirement and normal root lifecycle

**HARNESS / FIXTURE:** Use the exact reviewed CLI/hash from the accepted dependency spec and CONTRACT-DETAILS matrix. If not yet delivered, BLOCKED [H] DESIGN REQUIRED; no speculative runner name is executable.

**REQUIRED ARTIFACT:** Exact candidate named by grant, qualified APK/signer/embedded+unstripped Build ID and live installed read-back; current fdfb1ce binding only if still applicable.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot, com.waydefu.x11gpu :3, Android display0, isolated ADB5038; clean cells PROTO=TELEMETRY=1, fault/arm absent; fault cells only exact reviewed selector/arm pair. Performance CPU twin uses separately frozen flags.

**ALLOWED MUTATIONS:** Fresh named evidence and only reviewed owned experimental processes/cleanup; no unlisted install or settings change.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Read back installed candidate before any fixture. 2. Execute only approved affected baseline cells in frozen order and fresh directories; stop first failure. 3. Prove surface loss/resume D3, pool full/refusal/recovery, failed registration cleanup, root resize/retirement and fresh reconnect exactly as scoped. 4. Use existing frozen judges for unchanged contracts and reviewed new judges for new claims; never edit historical judges. 5. Reconcile final R7–R10/P2 ledger and carry-forward on new artifact. 6. Mark Production Gate A only for accepted supported subset, leaving Stable untouched.

**EXPECTED EVENTS:** Normal lifecycle succeeds without early release; actual in-flight renderer loss safely fails then fresh session recovers. No old-generation replay. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Normal lifecycle succeeds without early release; actual in-flight renderer loss safely fails then fresh session recovers. No old-generation replay. A required fault fatal is not an unexpected crash; process death caused by cleanup is never the oracle.

**FORBIDDEN SUCCESS EVENTS:** No post-fatal same-generation PUBLISH/success/relock/repair/ACK/pending decrement/lease release; no pre-terminal Present idle/release, wrong-tuple acceptance or software fallback mislabeled direct. Apply cell-specific frozen exceptions exactly.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Accepted harness/judge host-verification record must bind actual hashes; no unverified fixture substitutions.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT mandatory, including digest object distinction, signer and Build IDs; future SHA must use its own manifest.

**DEVICE PRECHECK:** A12 live identity/5038; grant; exact package+ELF binding; Stable baseline; awake/unlocked display0; no unrelated X3; fresh absent evidence path; tool hashes; exact environment; required metrics accessible or approved disposition.

**PASS CRITERIA:** All required production blockers closed with device proof, affected regressions PASS and artifact-specific closure; no inferred carry-forward.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Wrong artifact/env/identity, missing required trace, hook or schedule not constructed, wrong method/count, lost pre-cleanup observation. Freeze attempt; proven product violation is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-030/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** per-cell evidence; root/pending/lifetime records; D3 output; updated closure-copy and production qualification report; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** Capture verdict/process state before cleanup; stop only verified owned fixture/holder/logcat/X3; preserve Activity for reviewed warm rounds only, otherwise stop experimental Activity. Verify actual X3 PID/cmdline and socket/lock absence; no broad kill.

**STABLE AFTER-CHECK:** Mandatory captured Stable PID+cmdline+package version+lastUpdateTime comparison; unchanged. Missing evidence blocks acceptance.

**STATE TRANSITION:** NOT RUN → DEVICE_VALIDATED → CELL_PASS/GATE_PASS only at complete accepted scope; failures remain immutable.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-031 final-candidate performance refresh.

## NEXT-031

**PACKET ID:** NEXT-031

**NAME:** Refresh final-candidate workload evidence

**CLASSIFICATION:** [U][D][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** Refresh final-candidate workload evidence; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A19/A21 and accepted final candidate/change-impact ledger. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-030 qualified final candidate; NEXT-025 frozen method. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-030 qualified final candidate; NEXT-025 frozen method

**USER AUTHORIZATION REQUIRED?:** YES — exact candidate, installed binding, named cell list/counts, device/display and cleanup. Install separately if needed; no silent retry.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A19/A21 and accepted final candidate/change-impact ledger and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Changed dispatch/lifecycle/telemetry sites used to justify scope

**HARNESS / FIXTURE:** Use the exact reviewed CLI/hash from the accepted dependency spec and CONTRACT-DETAILS matrix. If not yet delivered, BLOCKED [H] DESIGN REQUIRED; no speculative runner name is executable.

**REQUIRED ARTIFACT:** Exact candidate named by grant, qualified APK/signer/embedded+unstripped Build ID and live installed read-back; current fdfb1ce binding only if still applicable.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot, com.waydefu.x11gpu :3, Android display0, isolated ADB5038; clean cells PROTO=TELEMETRY=1, fault/arm absent; fault cells only exact reviewed selector/arm pair. Performance CPU twin uses separately frozen flags.

**ALLOWED MUTATIONS:** Fresh named evidence and only reviewed owned experimental processes/cleanup; no unlisted install or settings change.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Compare measured artifact from NEXT-026 to release candidate. 2. If identical and method unchanged, preserve explicit evidence carry-forward and do not run. 3. If changed, freeze affected cells using touched-path analysis; run authorized NEXT-026 method on final candidate, never reuse old timing under new SHA. 4. Repeat bounded XFCE only where candidate changes invalidate prior evidence. 5. Report correctness/performance separately and retain original measurements.

**EXPECTED EVENTS:** Performance and bounded workload evidence bind final candidate or reviewed carry-forward; no assumed invariance. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Performance and bounded workload evidence bind final candidate or reviewed carry-forward; no assumed invariance. A required fault fatal is not an unexpected crash; process death caused by cleanup is never the oracle.

**FORBIDDEN SUCCESS EVENTS:** No post-fatal same-generation PUBLISH/success/relock/repair/ACK/pending decrement/lease release; no pre-terminal Present idle/release, wrong-tuple acceptance or software fallback mislabeled direct. Apply cell-specific frozen exceptions exactly.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Accepted harness/judge host-verification record must bind actual hashes; no unverified fixture substitutions.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT mandatory, including digest object distinction, signer and Build IDs; future SHA must use its own manifest.

**DEVICE PRECHECK:** A12 live identity/5038; grant; exact package+ELF binding; Stable baseline; awake/unlocked display0; no unrelated X3; fresh absent evidence path; tool hashes; exact environment; required metrics accessible or approved disposition.

**PASS CRITERIA:** All release-relevant comparisons valid on final candidate, including noise/conditions/path identity and exactness; negative result is reported honestly.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Wrong artifact/env/identity, missing required trace, hook or schedule not constructed, wrong method/count, lost pre-cleanup observation. Freeze attempt; proven product violation is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-031/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** final-candidate performance report; artifact linkage; affected-cell ledger; raw data or accepted unchanged-artifact carry-forward; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** Capture verdict/process state before cleanup; stop only verified owned fixture/holder/logcat/X3; preserve Activity for reviewed warm rounds only, otherwise stop experimental Activity. Verify actual X3 PID/cmdline and socket/lock absence; no broad kill.

**STABLE AFTER-CHECK:** Mandatory captured Stable PID+cmdline+package version+lastUpdateTime comparison; unchanged. Missing evidence blocks acceptance.

**STATE TRANSITION:** NOT RUN → DEVICE_VALIDATED → CELL_PASS/GATE_PASS only at complete accepted scope; failures remain immutable.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-032 read-only Gate H evidence decision.

## NEXT-032

**PACKET ID:** NEXT-032

**NAME:** Gate H evidence decision — router only if justified

**CLASSIFICATION:** [R][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** Gate H evidence decision — router only if justified; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A07 D-6/A19/A21 and MASTER-PLAN Gate H decision model. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-031 valid final-candidate measurements; P2 closed. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-031 valid final-candidate measurements; P2 closed

**USER AUTHORIZATION REQUIRED?:** Read-only audit/tests need no new device grant. New report publication or tag requires a scoped docs/tag grant; no runtime is authorized.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A07 D-6/A19/A21 and MASTER-PLAN Gate H decision model and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Prepared path-selection order from S01; read only

**HARNESS / FIXTURE:** N/A — read-only evidence audit; existing frozen judge/analyzer may be replayed on immutable captured inputs with real rc.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Compare CPU/direct and any justified staging route across supported cold/reuse/mixed workloads. 2. Apply frozen noise and p95 rule; require repeatable meaningful crossover, not one noisy bucket. 3. If one qualified path dominates, record fixed-route rationale and ROUTER DEFERRED/NOT JUSTIFIED; do not invent threshold. 4. If crossover, enumerate candidate routing boundaries and demand NEXT-033 design. 5. If inconclusive, record lack of justification; at most one explicitly authorized method correction/repeat, never automatic. CPU dominance requires default-off/narrower release-contract decision before claiming enabled GPU value.

**EXPECTED EVENTS:** CONDITIONAL Gate H disposition: router justified, fixed route justified, or evidence insufficient. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Explicit layer-specific result from steps; N/A — no device verdict from source/host/audit alone.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Validate evidence/schema completeness and replay only relevant existing frozen judges/analyzers with pinned inputs. Do not run runtime harnesses.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Decision reproducible from bound data; no threshold or performance claim outside evidence. Inconclusive result cannot pass a release speedup requirement.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-032/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** GATE-H-DECISION.md; crossover/noise table; exact supporting data refs; default/claim disposition; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** Incomplete ledger → accepted named aggregate only if every required predicate passes; otherwise BLOCKED with exact missing claims.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-033 only if justified and authorized; otherwise NEXT-035 Gate W after accepted fixed-route/default decision.

## NEXT-033

**PACKET ID:** NEXT-033

**NAME:** Conditional Gate H router design

**CLASSIFICATION:** [R][H] — PROPOSED packet. [H] DESIGN REQUIRED; dependent implementation/runtime is blocked until accepted.

**PURPOSE:** Conditional Gate H router design; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A07/A09/A18/A19/A21; exact final source. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-032 meaningful crossover; accepted need for router. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-032 meaningful crossover; accepted need for router

**USER AUTHORIZATION REQUIRED?:** Read-only research needs no new grant. Documentation under an existing scoped docs grant may proceed. Architecture adoption and all subsequent source/CI/install/device stages require explicit authorization.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A07/A09/A18/A19/A21; exact final source and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** S01 EXA Prepare/admission order, gateADirectTryPrepare; ownership transition to RESERVED/GPU_OWNED; Present retirement

**HARNESS / FIXTURE:** Future harness delivery contract in CONTRACT-DETAILS is mandatory: exact fixture CLI/count/hash, reachable schedule, real judge CLI and negative/legal-boundary cases. No runnable tool is implied by a proposed output filename.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Freeze routing decision only before lease/unlock/publication. 2. Derive route rule from measured crossover, cold/reuse state and noise; specify OFF equivalence and tie/boundary behavior. 3. Prohibit route switching or CPU fallback after ownership transfer. 4. Specify mixed-size, cross-route ordering, exact pixels, resource accounting and worst-case/p95 comparisons versus best fixed route. 5. Freeze implementation allowlist, actual-code tests, verifier/CI/device commands and rollback-to-fixed policy. 6. If shared ABI or owner model must change, separate architecture review before implementation.

**EXPECTED EVENTS:** PROPOSED exact routing design with no new post-publication fallback or unsupported predicates. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** DESIGN_FROZEN only after reviewed output; N/A — no runtime verdict during design. Any later runtime result must be recorded separately.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Before dependent execution, deliver and pass exact judge/sampler/fixture host tests including false-green and false-red cases. Design text alone is not HOST_VERIFIED.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Frozen route predicate backed by repeatable evidence and complete safety/regression method; otherwise keep router deferred.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-033/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** GATE-H-ROUTER-DESIGN.md; predicate/boundary table; source allowlist; tests+verifier CLI; qualification scope; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → DESIGN_FROZEN after acceptance; source/device layers remain NOT RUN until independently evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-034 stage-specific source/CI/install/device grants.

## NEXT-034

**PACKET ID:** NEXT-034

**NAME:** Conditional router implementation and qualification pipeline

**CLASSIFICATION:** [U][L] — PROPOSED packet. [L] only after exact design is frozen; any new architecture returns to [H].

**PURPOSE:** Conditional router implementation and qualification pipeline; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A09/A10/A12/A18/A21 and accepted router design. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-033 accepted; separate grants for source, fork CI, install and device stages. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-033 accepted; separate grants for source, fork CI, install and device stages

**USER AUTHORIZATION REQUIRED?:** YES — bounded source/harness allowlist. CI, install and runtime require separately named grants even if this packet describes their later sequence.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A09/A10/A12/A18/A21 and accepted router design and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Only reviewed Prepare-time router and selected normal-path helpers

**HARNESS / FIXTURE:** PROFILE-HOST plus exact accepted design's real-source tests/judge. Missing complete source or commands is BLOCKED, never simulate a pass.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** Only accepted implementation allowlist in independent worktree, host outputs and separately authorized stage outputs.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Implement and host-test accepted rule in isolated worktree; OFF must match existing path. 2. Stop after HOST_VERIFIED until explicit CI grant; use PROFILE-ARTIFACT. 3. Stop before install and again before runtime unless existing grant explicitly names them. 4. Run exact ON/OFF oracle, cross-route R6, affected R7/lifecycle/R10 and mixed workload A/B from reviewed matrix in new directories. 5. Refresh final-candidate closure/performance records. 6. If no benefit or regression, stop and retain evidence; reverting to fixed route requires a reviewed candidate and grant, not silent enable/disable.

**EXPECTED EVENTS:** Separate SOURCE_FIXED/HOST_VERIFIED/CI_QUALIFIED/INSTALLED/DEVICE_VALIDATED; routing PASS only after full pipeline. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Explicit layer-specific result from steps; N/A — no device verdict from source/host/audit alone.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** PROFILE-HOST and accepted targeted real-helper/parser regressions; positive, missing evidence, wrong identity, forbidden order, legal watermark/reorder and historical PASS/FAIL cases; record real rc and complete source binding.

**CI REQUIREMENTS:** Separate CI boundary only if product source changed; host/harness-only changes do not justify APK CI.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Safety and affected correctness pass, mixed workload meets frozen performance/noise rule versus best fixed route; every stage separately evidenced.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-034/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** source/host report; artifact manifest; runtime cells; router decision; final closure/performance refresh; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → SOURCE_FIXED → HOST_VERIFIED; any later stages remain gated and separately evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-035 Gate W definition adoption, only after qualified routing or accepted fixed-route disposition.

## NEXT-035

**PACKET ID:** NEXT-035

**NAME:** PROPOSED Gate W v1 and release contract freeze

**CLASSIFICATION:** [R][H] — PROPOSED packet. [H] DESIGN REQUIRED; dependent implementation/runtime is blocked until accepted.

**PURPOSE:** PROPOSED Gate W v1 and release contract freeze; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A03/A07/A19/A21; MASTER-PLAN PROPOSED Gate W and V1-Core release contract. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** Production qualified; NEXT-032 fixed-route decision or NEXT-034 router qualification. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** Production qualified; NEXT-032 fixed-route decision or NEXT-034 router qualification

**USER AUTHORIZATION REQUIRED?:** Read-only research needs no new grant. Documentation under an existing scoped docs grant may proceed. Architecture adoption and all subsequent source/CI/install/device stages require explicit authorization.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A03/A07/A19/A21; MASTER-PLAN PROPOSED Gate W and V1-Core release contract and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Current supported EXA/Present paths, negative predicate fallback, root resize/lifecycle and frame-pacing observation boundary

**HARNESS / FIXTURE:** Future harness delivery contract in CONTRACT-DETAILS is mandatory: exact fixture CLI/count/hash, reachable schedule, real judge CLI and negative/legal-boundary cases. No runnable tool is implied by a proposed output filename.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Adopt or explicitly revise PROPOSED Gate W v1 and V1-Core acceptance before execution. 2. Freeze current display0 geometry/refresh and deterministic XFCE off/on scripts: move/resize/close, terminal/panel expose, mixed Copy/Solid/narrow Over, negative fallback and browser-like tiled damage. 3. Freeze >=10min/mode proposal with exact action counts, oracle before/after and per-action pixel references. 4. Define common frame pacing median/p95/p99/long-frame and eligible-vs-total hit-rate metrics without invented FPS target. 5. Bind final CPU/candidate comparison, R10 resource predicates and D-7 limitation disposition. 6. Deliver actual scripts/judges/negative cases, host-verify, and freeze release supported/unsupported reset and death-recovery scope. Do not add UWQHD, named-app GPU certification or broader XRender.

**EXPECTED EVENTS:** New PROPOSED contract becomes accepted only with recorded review; no historical Gate W PASS claim. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** DESIGN_FROZEN only after reviewed output; N/A — no runtime verdict during design. Any later runtime result must be recorded separately.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Before dependent execution, deliver and pass exact judge/sampler/fixture host tests including false-green and false-red cases. Design text alone is not HOST_VERIFIED.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Executable method with exact correctness/safety/stability/performance predicates, complete provenance, release/default decisions and no unresolved required metric.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-035/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** GATE-W-V1-SPEC.md; V1-CORE-RELEASE-CONTRACT.md; workload scripts/judge CLI+hashes; reference pixels; metric schema; acceptance record; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → DESIGN_FROZEN after acceptance; source/device layers remain NOT RUN until independently evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-036 explicit final-artifact workload grant.

## NEXT-036

**PACKET ID:** NEXT-036

**NAME:** Gate W final-artifact desktop workload qualification

**CLASSIFICATION:** [U][D][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** Gate W final-artifact desktop workload qualification; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A12/A21 plus frozen Gate W/V1-Core release contract. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-035 accepted/HOST_VERIFIED; final candidate installed+bound; all prerequisite gates accepted. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-035 accepted/HOST_VERIFIED; final candidate installed+bound; all prerequisite gates accepted

**USER AUTHORIZATION REQUIRED?:** YES — exact candidate, installed binding, named cell list/counts, device/display and cleanup. Install separately if needed; no silent retry.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A12/A21 plus frozen Gate W/V1-Core release contract and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Read-only final workload path and metric producers fixed by NEXT-035

**HARNESS / FIXTURE:** Use the exact reviewed CLI/hash from the accepted dependency spec and CONTRACT-DETAILS matrix. If not yet delivered, BLOCKED [H] DESIGN REQUIRED; no speculative runner name is executable.

**REQUIRED ARTIFACT:** Exact candidate named by grant, qualified APK/signer/embedded+unstripped Build ID and live installed read-back; current fdfb1ce binding only if still applicable.

**RUNTIME ENVIRONMENT:** F8 Termux/PRoot, com.waydefu.x11gpu :3, Android display0, isolated ADB5038; clean cells PROTO=TELEMETRY=1, fault/arm absent; fault cells only exact reviewed selector/arm pair. Performance CPU twin uses separately frozen flags.

**ALLOWED MUTATIONS:** Fresh named evidence and only reviewed owned experimental processes/cleanup; no unlisted install or settings change.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Validate final artifact and exact CPU/direct mode twins. 2. Execute frozen compositor off/on scripts, counts and duration once each under authorized scope; record geometry/thermal/charging and reference pixels. 3. Check per-action redraw, fallback path, exact oracle, resource trends, zero unexpected fatal/crash and clean teardown. 4. Calculate pacing/hit-rate and paired performance with real denominators and common boundary; no unobservable zero-fill. 5. Stop at first invalidity/failure, retaining logs. 6. Publish separate correctness/stability/performance verdicts against accepted contract.

**EXPECTED EVENTS:** Deterministic desktop output, valid narrow path/fallback coverage, balanced resources and workload performance satisfying accepted default claim. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Deterministic desktop output, valid narrow path/fallback coverage, balanced resources and workload performance satisfying accepted default claim. A required fault fatal is not an unexpected crash; process death caused by cleanup is never the oracle.

**FORBIDDEN SUCCESS EVENTS:** No post-fatal same-generation PUBLISH/success/relock/repair/ACK/pending decrement/lease release; no pre-terminal Present idle/release, wrong-tuple acceptance or software fallback mislabeled direct. Apply cell-specific frozen exceptions exactly.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Accepted harness/judge host-verification record must bind actual hashes; no unverified fixture substitutions.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** PROFILE-ARTIFACT mandatory, including digest object distinction, signer and Build IDs; future SHA must use its own manifest.

**DEVICE PRECHECK:** A12 live identity/5038; grant; exact package+ELF binding; Stable baseline; awake/unlocked display0; no unrelated X3; fresh absent evidence path; tool hashes; exact environment; required metrics accessible or approved disposition.

**PASS CRITERIA:** All frozen Gate W/release predicates pass on final candidate including any explicit D-7 disposition; no waived required metric.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Wrong artifact/env/identity, missing required trace, hook or schedule not constructed, wrong method/count, lost pre-cleanup observation. Freeze attempt; proven product violation is VALID FAIL, not INVALID.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-036/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** workload action log; reference/output hashes; raw pacing/timing; path counts; FD/resource series; judge rc; GATE-W-REPORT.md; Stable/cleanup; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** Capture verdict/process state before cleanup; stop only verified owned fixture/holder/logcat/X3; preserve Activity for reviewed warm rounds only, otherwise stop experimental Activity. Verify actual X3 PID/cmdline and socket/lock absence; no broad kill.

**STABLE AFTER-CHECK:** Mandatory captured Stable PID+cmdline+package version+lastUpdateTime comparison; unchanged. Missing evidence blocks acceptance.

**STATE TRANSITION:** NOT RUN → DEVICE_VALIDATED → CELL_PASS/GATE_PASS only at complete accepted scope; failures remain immutable.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** NEXT-038 final read-only acceptance then separately authorized docs/tag freeze; any failure NEXT-037 triage.

## NEXT-037

**PACKET ID:** NEXT-037

**NAME:** Reusable failure → narrow repair → one fresh requalification

**CLASSIFICATION:** [R][H] — PROPOSED packet. [H] DESIGN REQUIRED; dependent implementation/runtime is blocked until accepted.

**PURPOSE:** Reusable failure → narrow repair → one fresh requalification; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A01–A05/A09/A17/A18/A20/A21; MASTER-PLAN failure taxonomy and baseline table. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** Any failed/invalid packet; original evidence preserved. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** Any failed/invalid packet; original evidence preserved

**USER AUTHORIZATION REQUIRED?:** Read-only research needs no new grant. Documentation under an existing scoped docs grant may proceed. Architecture adoption and all subsequent source/CI/install/device stages require explicit authorization.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A01–A05/A09/A17/A18/A20/A21; MASTER-PLAN failure taxonomy and baseline table and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Only decisive failure producer/consumer/classifier and touched release sites; escalate ownership/ABI/ordering uncertainty

**HARNESS / FIXTURE:** Future harness delivery contract in CONTRACT-DETAILS is mandatory: exact fixture CLI/count/hash, reachable schedule, real judge CLI and negative/legal-boundary cases. No runnable tool is implied by a proposed output filename.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Freeze original directory/hash, command/rc, artifact/env/identity and minimal contradictory trace. 2. Classify VALID PRODUCT FAIL vs INVALID vs infrastructure/binding/observability; expected fail-stop with matching oracle is not a defect. 3. Source RCA against actual SHA; ordinary local classifier repair may be [L] after causal invariant is frozen, otherwise [H]. 4. Obtain exact narrow source/harness grant, then implement in independent worktree; actual static/host/regression tests before commit. 5. New product SHA needs separately authorized fork CI and PROFILE-ARTIFACT; harness-only repair does not. 6. Separate install/device grant identifies exactly ONE new evidence attempt; old failure and judge remain immutable. 7. Requalify affected cell exactly once plus approved touched-semantics baseline; resume ordered gate only after PASS. Another FAIL stops; no recursive automatic retry.

**EXPECTED EVENTS:** Repair report distinguishes cause/proposal/source/host/CI/artifact/install/runtime; new PASS never rewrites historical FAIL. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** DESIGN_FROZEN only after reviewed output; N/A — no runtime verdict during design. Any later runtime result must be recorded separately.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Before dependent execution, deliver and pass exact judge/sampler/fixture host tests including false-green and false-red cases. Design text alone is not HOST_VERIFIED.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** For design: complete causal packet and accepted narrow plan. For repaired qualification: fresh bound PASS plus required regressions and explicit carry-forward; stages never collapsed.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-037/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** FAILURE-TRIAGE.md; minimal trace/source proof; scoped repair design; stage-by-stage commands/rc; new attempt linkage; historical hashes; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** PROPOSED → DESIGN_FROZEN after acceptance; source/device layers remain NOT RUN until independently evidenced.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution.

**NEXT AUTHORIZATION:** Explicit grant per mutation boundary. Astra escalation only for authority conflict, new ABI/protocol/ownership/memory-order/lifecycle contract or source/device contradiction; routine frozen cells remain low-tier.

## NEXT-038

**PACKET ID:** NEXT-038

**NAME:** V1-Core acceptance and documentation freeze

**CLASSIFICATION:** [R][L] — PROPOSED packet. Only frozen/reviewed mechanics are [L].

**PURPOSE:** V1-Core acceptance and documentation freeze; preserve separate source, host, artifact, runtime and release claims.

**CURRENT AUTHORITY:** A01–A03/A10/A14–A21 plus final accepted release contract and gate reports. IDs resolve in AUTHORITY-INDEX.md; newest merged authority wins.

**ENTRY STATE:** NEXT-023 updated final-candidate P2 closure; NEXT-030 production closure; NEXT-031/032; conditional034; NEXT-035 accepted contract and NEXT-036 PASS. This planning snapshot does not assert these dependencies are already complete.

**DEPENDENCIES:** NEXT-023 updated final-candidate P2 closure; NEXT-030 production closure; NEXT-031/032; conditional034; NEXT-035 accepted contract and NEXT-036 PASS

**USER AUTHORIZATION REQUIRED?:** Read-only audit/tests need no new device grant. New report publication or tag requires a scoped docs/tag grant; no runtime is authorized.

**FILES TO READ:** README.md; MASTER-PLAN.md applicable section and global hard rules; CONTRACT-DETAILS.md applicable matrix/profile; only A01–A03/A10/A14–A21 plus final accepted release contract and gate reports and accepted dependency outputs needed for this claim. Do not reread all history.

**SOURCE SYMBOLS TO LOCATE:** Candidate touched-symbol/carry-forward ledger only; no source mutation

**HARNESS / FIXTURE:** N/A — read-only evidence audit; existing frozen judge/analyzer may be replayed on immutable captured inputs with real rc.

**REQUIRED ARTIFACT:** Pinned docs base plus exact product SHA and accepted dependency outputs; device records remain historical until a separately authorized live binding.

**RUNTIME ENVIRONMENT:** Host/read-only source environment; no ADB, APK install or device fixture during design/audit/implementation verification. Any later stage follows its separate grant.

**ALLOWED MUTATIONS:** New scoped planning/report files and temporary host test output; frozen source/evidence/tools remain immutable.

**FORBIDDEN MUTATIONS:** Stable com.termux.x11/:1, HDMI, historical evidence/judges, timeout or tolerance weakening, silent rerun, unreviewed shared ABI/ownership changes, upstream PR/push, merge/auto-merge. No stage proceeds merely because prior stage passed.

**EXACT EXECUTION STEPS:** 1. Verify every required gate/claim against final candidate or explicit justified carry-forward; reject pending/null required items. 2. Verify exact full SHA, submodules, CI head, package/signer/APK/ELF, install binding and per-cell tool hashes. 3. Confirm performance/default decision, supported reset/lifecycle, limitations and deferred scope match accepted contract. 4. Recheck no historical mutation, Stable isolation and no X3 residue from last authorized workload. 5. Produce V1-CORE-ACCEPTANCE.md and immutable release manifest only under docs grant; create tag only if explicitly authorized. 6. STOP. No APK distribution, Stable installation, production enable, merge or upstream PR is included.

**EXPECTED EVENTS:** V1_CORE_QUALIFIED/FROZEN only if all accepted predicates satisfied; otherwise named BLOCKED claims. INV-A01–A18 apply; scope-specific invariants are in the cited authority.

**EXPECTED FATAL / RESULT:** Explicit layer-specific result from steps; N/A — no device verdict from source/host/audit alone.

**FORBIDDEN SUCCESS EVENTS:** Never report a later layer PASS from this layer, omit a failed historical cell, replace missing evidence with zero, or adopt an unreviewed contract as FROZEN.

**STATIC VERIFICATION:** Check exact source/tool identity, allowed diff, INV-A01–A18 and design/source agreement; ownership/ACK ordering needs actual control-flow proof. git diff --check for any new files; no modification outside approved scope.

**HOST VERIFICATION:** Validate evidence/schema completeness and replay only relevant existing frozen judges/analyzers with pinned inputs. Do not run runtime harnesses.

**CI REQUIREMENTS:** N/A — this step does not itself dispatch CI; any required product changes route through reviewed source/host/artifact stages first.

**ARTIFACT QUALIFICATION:** N/A — no installation/artifact mutation; preserve and verify provenance of referenced evidence, never assume current live state.

**DEVICE PRECHECK:** N/A — no device action in current layer. Any explicitly described later runtime stage must perform full A12/binding/Stable/fresh-path preflight.

**PASS CRITERIA:** Complete release evidence and accepted claim scope on one candidate; all unresolved required items absent; freeze action separately authorized.

**BLOCKED CRITERIA:** Any dependency or grant absent; authoritative conflict unresolved; missing complete source/tool/fixture/metric; changed candidate without carry-forward; existing evidence destination; required design not frozen. Stop before mutation.

**INVALID CRITERIA:** Unbound input/source, missing command/rc, fabricated or incomplete evidence, wrong schema/claim mapping. Correct report without mutating originals; no promotion of uncertain results.

**EVIDENCE DIRECTORY:** PROPOSED future: evidence/session/v1-core/<full-product-sha>/next-038/<explicitly-granted-attempt-id>/; entire path must be absent. Frozen harness path constraints override this organization; record actual path in ledger. For this docs task, outputs live only in planning/v1-core-20260917/.

**EVIDENCE FILES:** V1-CORE-ACCEPTANCE.md; release-manifest.json; complete gate/carry-forward ledger; known limits and Deferred After V1-Core; include exact source/tool/command/rc identity and SHA256 manifest. Keep raw captured evidence immutable; do not add APK/ELF/secrets to docs repository.

**CLEANUP:** N/A — no runtime cleanup. Preserve all failure data; discard only confirmed own temporary outputs if needed, never restore/reset another writer's files.

**STABLE AFTER-CHECK:** N/A — no Stable/device access. For audit verify prerequisite runtime reports include bound before/after comparisons; do not claim new live verification.

**STATE TRANSITION:** Incomplete ledger → accepted named aggregate only if every required predicate passes; otherwise BLOCKED with exact missing claims.

**STOP CONDITION:** Stop at first missing/contradictory required evidence, forbidden diff, failed check or authorization boundary. No automatic retry or next-stage execution. STOP after acceptance/freeze.

**NEXT AUTHORIZATION:** STOP — distribution, deployment, Stable install, merge and future expansion require separate explicit authorization.
