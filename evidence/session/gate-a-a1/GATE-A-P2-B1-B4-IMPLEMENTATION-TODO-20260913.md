# Gate A P2 B1–B4 correction + telemetry — implementation TODO

Base: `82a87f4a99ae4b1d4e09d6c74a735cd40b6e73e2`
Head: `15caa00908aa9d1f1c4a78bb630aa24a93e7e4cd`
Worktree: `/root/projects/GPU加速/src/f8-ahb-gatea-a1`

Closed 2026-09-14. Authority:
`GATE-A-P2-B1-B4-IMPLEMENTATION-20260914.md`.

## Acceptance criteria

- [x] B1: direct entry advances `out.lastSerial` and `readIndex` exactly once after slot copy/consume; this remains distinct from GPU completion and semantic result.
- [x] B2: direct identity is generation-local side metadata keyed by queue slot + exact serial, release-published before queue writeIndex; lookup/tuple mismatch fail-stops and cannot enter legacy buffer/upload code.
- [x] Side metadata slot reuse requires renderer-consumed metadata; stale slot/serial match is fatal.
- [x] B3: every direct reserve requires ACTIVE/no fatal, no pair, empty queue, consumed prior entries, `completedSerial == gpuCopySerialCounter`, and no first failure.
- [x] B4 buffer retirement: READY→RETIRING, terminal wait, UNREGISTER, GL-thread reverse resource destroy, UNREGISTER_ACK, local slot release.
- [x] B4 generation close: stop new submits, terminal drain, retire every READY buffer, GENERATION_CLOSE, renderer-empty check, GENERATION_CLOSED, local generation release.
- [x] Fatal path stays separate and never performs normal retirement/release.
- [x] Experimental/default-off telemetry covers requested events/counters without changing P0 40-byte sideband or 168-byte queue entry.
- [x] Static regression verifier fails on base and passes after correction.
- [x] `git diff --check` PASS.
- [x] ARM64 incremental native build PASS.
- [x] ARM64 full-clean native build PASS.
- [x] New warnings: 0 against frozen P2 full-clean warning baseline.
- [x] Final diff review; no unrelated files, debug garbage, runtime hooks, ADB/device/Stable/HDMI actions.
- [x] Meaningful local Conventional Commit created; no push/CI/runtime.

## Evidence

- RED: `GATE-A-P2-RUNTIME-QUALIFICATION-DESIGN-20260913.md` (82a87f4 blockers).
- GREEN: `GATE-A-P2-B1-B4-IMPLEMENTATION-20260914.md`.
- Builds: `GATE-A-P2-B1-B4-NATIVE-BUILD-20260914.log`,
  `GATE-A-P2-B1-B4-NATIVE-BUILD-FULL-20260914.log`.
- Commit: `15caa00` `feat(gatea): implement B1-B4 correction + lifecycle + telemetry`.
