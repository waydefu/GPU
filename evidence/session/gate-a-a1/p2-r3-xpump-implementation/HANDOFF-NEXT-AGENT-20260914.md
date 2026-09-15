# Gate A P2 R3 X-pump implementation handoff — 2026-09-15

Last updated: `2026-09-15 03:02 CST (+0800)`

## 0. Authority and current verdict

Read in this order:

1. `/root/projects/GPU加速/HANDOFF.md`
2. `/root/projects/GPU加速/TEST-MATRIX.md`
3. This file
4. `/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-ci-34872266646/P2-R3-XPUMP-CI-ARTIFACT-PROVENANCE-20260915.md`
5. `/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime/HANDOFF-NEXT-AGENT-20260914.md`
6. `/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-design/GATE-A-P2-R3-XPUMP-DESIGN-20260914.md`

Current verdict:

```text
ROOT CAUSE: PROVEN — X main-thread self-wait
A1 DESIGN: PASS
A1 SOURCE: COMMITTED d9b7f60f24e722205891f1ce941816393ae4c695
LOCAL ARM64 INCREMENTAL+FULL-CLEAN: PASS (post-EINTR fix)
HOST DECODER SOCKETPAIR: PASS
PYTHON RED/GREEN: PASS
FINAL REVIEW: two blocking defects fixed (zero-body emit, multi-FD close);
              EINTR poll restart fixed against poll(2)
FORK PUSH: PASS (waydefu/termux-x11 qualification/gatea-xpump-20260914)
CI: PASS run 34872266646 workflow_dispatch first attempt
ARTIFACT: QUALIFIED (NOT INSTALLED)
INSTALL: DONE (experimental only)
R1 UNSET: PASS
R1 PROTO=0: FAIL SIGSEGV PID 21639 (OBSERVED, dalvik-jit class)
R1 PROTO=0 RERUN: PASS X 27435 (21639 NON-REPRODUCED)
R3: PASS (runtime 20260915; X 8034 consumed READY)
R2: PASS (runtime 20260915; X 28042 GATEA_EVENT=0)
R4: PASS (runtime 20260915; X 29807 1514/1514 N=8)
R5: FAIL REPRODUCED; ROOT CAUSE PROVEN (AF_UNIX tiny-record backpressure + lock-across-write repair cycle)
R5 CORRECTION: UNCOMMITTED STATIC+COMPILE PASS / fix/gatea-r5-backpressure-20260915 / 2 files +58/-32
R5 CORRECTION TESTS: RED→GREEN + decoder + X-pump + ARM64 incremental/full-clean + independent review PASS / 0 new warnings
R6–R8: CONDITIONALLY AUTHORIZED ONLY AFTER CORRECTED-ARTIFACT R5 PASS; NOT STARTED
PRODUCTION GATE A: BLOCKED
```

Runtime after this implementation file: R5 FAIL REPRODUCED on the installed APK.
See `../p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md`.
Do not open a PR. Do not push origin. Do not force. The bounded R5 source
correction is written but uncommitted; obtain explicit commit/push authorization
before shared history. R6–R8 become executable only after a corrected artifact
makes R5 PASS; do not start them on `d9b7f60`. Do not second-retry R5 on
`d9b7f60`.

## 1. Exact repositories and state

### Frozen control

```text
path:   /root/projects/GPU加速/src/f8-ahb-gatea-a1
branch: qualification/gatea-a1-microprobe-20260912
HEAD:   88e3f176d5be313b7dee058da9021cfe8d09e7de
state:  clean
runtime status: historical control; APK no longer installed
```

Do not modify this worktree. Do not retry R3 on `88e3f17`, `8479997`,
`6c7ee6f`, or `98b0011`.

### Qualified implementation worktree

```text
path:   /root/projects/GPU加速/src/f8-ahb-gatea-xpump
branch: qualification/gatea-xpump-20260914
HEAD:   d9b7f60f24e722205891f1ce941816393ae4c695
state:  clean
commit: fix(gatea): pump X-side Gate replies on the main thread
installed APK: com.waydefu.x11gpu 1.03.01-d9b7f60-14.09.26 CI 34872266646
```

### R5 correction worktree

```text
path:   /root/projects/GPU加速/src/f8-ahb-gatea-r5-fix
branch: fix/gatea-r5-backpressure-20260915
base/HEAD: d9b7f60f24e722205891f1ce941816393ae4c695
state:  dirty; exactly cmdentrypoint.cpp + renderer.cpp
status: uncommitted static+compile PASS; commit/push/CI/artifact NOT DONE
```

Authority:
`../p2-r5-backpressure-fix/GATE-A-P2-R5-STATIC-IMPLEMENTATION-20260915.md`.

Five files in the historical `d9b7f60` commit:

```text
lorie/src/main/cpp/lorie/InitOutput.c
lorie/src/main/cpp/lorie/activity.cpp
lorie/src/main/cpp/lorie/cmdentrypoint.cpp
lorie/src/main/cpp/lorie/lorie.h
lorie/src/main/cpp/lorie/renderer.cpp
5 files changed, 1245 insertions(+), 196 deletions(-)
```

## 2. What the commit does

- Record-aware nonblocking decoder (`lorieRecordDecoderNext`).
- Zero-body Gate records (`UNREGISTER_ACK` / `GENERATION_CLOSED`) and
  fixed-size legacy records emit in the same `Next` call via
  `lorieRecordDecoderEmitIfComplete()`.
- Reject-path `SCM_RIGHTS` closes every ancillary FD via
  `lorieRecordDecoderCloseAncillaryFds()`.
- X waiters call `lorieGateAPumpConnection()` instead of condvar
  self-wait on the same thread. READY/UNREGISTER DEFER; GENERATION_CLOSE
  CANCEL.
- `poll(2)` remaining milliseconds are recomputed from the absolute
  CLOCK_MONOTONIC deadline on every attempt, including EINTR.
- Activity→X writers share `lorieActivityWriterMutex`.
- ABI unchanged: frame 40, sideband 40, queue 168, direct meta 48,
  `LORIE_GATEA_WAIT_BUDGET_NS 2000000000ull`.

## 3. Qualified artifact

Authority:
`evidence/session/gate-a-a1/p2-r3-xpump-ci-34872266646/P2-R3-XPUMP-CI-ARTIFACT-PROVENANCE-20260915.md`

```text
CI run:     34872266646
APK SHA256: 255cc37d12dd052c32d2b8ba89af3029034f59f7e01b65bd61cffd50d86737a2
version:    1.03.01-d9b7f60-14.09.26
Build ID:   2b02bf139236d45aaa24a95fa8609cca0d956e7d MATCH
package:    com.waydefu.x11gpu
```

## 4. Residual non-blocking notes

These were reviewed and are not treated as commit blockers:

- Activity first-record / AHB-handle path remains blocking `ReadFull`.
- `lorieActivitySendGateFrame` still saves `errno` even on success.
- HUP-before-POLLIN can fail-stop without draining a last READY
  (matches authorized fail-stop).
- Host decoder tests do not link `QueueWorkProc` / CloseScreen.
- Independent Luna scout FAIL on pre-fix zero-body + multi-FD is
  superseded by source fixes + host tests. Post-fix scout FAIL on
  stale `poll()` EINTR timeout is superseded by the recompute loop
  (`cmdentrypoint.cpp` `lorieGateAPumpConnection`, poll(2) man-pages
  6.19). No third independent pass was run after the EINTR fix.

## 5. Next-agent stop conditions

Stop immediately and report before continuing if asked to:

- R6–R8 before corrected-artifact R5 PASS; R9–R10; extra ADB cells,
  Stable `:1`, HDMI, Production enable;
- second-retry of R5 on `d9b7f60` (authorized one-shot rerun consumed,
  FAIL REPRODUCED);
- PR, merge, origin push, force, history rewrite;
- timeout increase, retry/sleep workaround, D0b, Gate H;
- reopen P0 / P1 / P2-A / P2-B.1 / P2-B.2;
- source-fix the pump from PID 21639 (JIT class, root cause not proven).
