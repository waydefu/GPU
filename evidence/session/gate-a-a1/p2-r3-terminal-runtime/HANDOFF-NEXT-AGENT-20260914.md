# Gate A P2 R3 terminal/observability — 交接（2026-09-14 R0–R3 runtime STOP）

給下一位：先讀本檔，再讀 `HANDOFF.md`「Next」。**不要從聊天記憶接續。**
**不要 silent-retry 本輪 R3。不要進 R4。**

```
STATUS: R0–R3 RUN — STOP AFTER R3 FAIL
HEAD: 88e3f176d5be313b7dee058da9021cfe8d09e7de
CI: 34822381586
APK INSTALLED experimental only: 1.03.01-88e3f17-14.09.26
SHA256: 7e5540a247f0a0dd1c179fc818ba2f83abd2d970fb4961588ba6f071b19b8616 MATCH
Build ID: e91c7683b3dd0ac61739f274a5eaeffaace1be12 MATCH
R1: PASS (unset + PROTO=0 oracle/stress)
R2: PASS WITH INDIRECT REJECTION EVIDENCE
R3: FAIL (VALIDATE_TERMINAL_READY then X x-ready-timeout)
R4–R10: NOT RUN
Production Gate A: BLOCKED
Stable :1 PID 16085: UNTOUCHED
HDMI: UNTOUCHED
```

Historical R3 FAIL on `8479997` is unchanged. Do not rewrite it.
This round's cells live under `runtime-88e3f17/`.

## 1. 本輪結果

Install + R1 + R2 PASS. Exactly one R3 cell FAIL.

Renderer validate ran to completion and sent READY:
`VALIDATE_TERMINAL_READY` + `GATEA_EVENT role=2 event=1` (REGISTER_READY).
X still `x-ready-timeout` reason=4 exactly 2.000s later. Fixture
`FAIL GetImage`. No new crash signal.

`8479997` silent-validate hypotheses are falsified. Remaining locus is
X-side READY consume / waiter, not EGL/tuple/image.

Authority cells: `runtime-88e3f17/`.

## 2. 權威與樹

| | |
|---|---|
| 活躍 worktree | `/root/projects/GPU加速/src/f8-ahb-gatea-a1` |
| branch | `qualification/gatea-a1-microprobe-20260912` |
| HEAD | `88e3f176d5be313b7dee058da9021cfe8d09e7de` clean |
| D0a control | `/root/projects/GPU加速/src/f8-ahb` `a6cc795` clean |
| runtime evidence | `runtime-88e3f17/` |

Closed 不准重開：P0 / P1 / P2-A / P2-B.1 / P2-B.2 / S3 / D0a。
Predicate 維持窄。禁止 `±1 UNORM` 當 PASS。

## 3. 下一位

STOP HERE. Do not retry R3 on this APK. Do not install over Stable.
Do not enable Production. Do not touch `:1` / HDMI. No PR, no merge.
No R4–R10 until a new user authorization after a proven repair.

If investigating: X demux / waiter vs Activity `conn_fd` READY write
that already logged `READY_SEND_RETURN result=1`. Do not lengthen the
2s timeout. Do not treat missing X log as hang.

## 4. Post-runtime source diagnosis — 2026-09-14

Source tracing at exact clean `88e3f17` proves the first R3 blocker:

- lorie does not call `InputThreadPreInit()`;
- `InputThreadRegisterDev()` therefore falls back to `SetNotifyFd()`;
- `handleLorieEvents()` runs from the X main loop;
- `gateAEnsureReady()` sends REGISTER and sleeps on a condvar on that same X
  main thread;
- the only READY mark/signal path requires that thread to return to the socket
  callback.

The resulting self-cycle explains the renderer READY at 17:24:02.850 and exact
2.000 s X timeout. Short-peek/demux defects remain secondary but are not the
first `88e3f17` blocker.

Design review and corrected implementation contract:

`../p2-r3-xpump-design/GATE-A-P2-R3-XPUMP-DESIGN-20260914.md`

Current boundary: the user approved the record-aware A1 implementation contract,
regression tests, ARM64 builds, fork push, multi-ABI CI, and artifact
qualification. Install/ADB/device/runtime remain unauthorized. The uploaded
copy-paste pump is not accepted unchanged because its 24-byte availability test
can enter a blocking 48-byte Gate read, it re-enters legacy X semantics inside
an active request, and it does not serialize every Activity-to-X logical writer.
