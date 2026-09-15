# Gate A P2 R3 record-aware X-pump implementation TODO — 2026-09-14

Base: `88e3f176d5be313b7dee058da9021cfe8d09e7de`

Authorization: source implementation, regression tests, ARM64 incremental/full-clean build, fork push, multi-ABI CI, and artifact qualification. No install, ADB, device, or runtime.

## Acceptance criteria

- [ ] Isolated writer worktree starts from exact clean base.
- [ ] RED proves the X self-wait and current blocking/demux defects.
- [ ] Decoder handles partial Gate prefix/header/body incrementally without blocking.
- [ ] Decoder handles fixed, variable-payload, and ancillary-FD legacy records with explicit ownership.
- [ ] READY/REGISTER_FAILED/UNREGISTER_ACK/GENERATION_CLOSED dispatch exactly once.
- [ ] READY and UNREGISTER waits defer legacy semantics until the current request returns.
- [ ] GENERATION_CLOSE consumes and cancels deferred legacy semantics, freeing payloads and closing FDs.
- [ ] Each waiter retains its own monotonic 2000 ms deadline.
- [ ] Activity-side callback drain cannot block after consuming one Gate frame.
- [ ] Every Activity-process→X logical writer and fd close/rebind follows one serialization/identity contract.
- [ ] PROTO unset/0 behavior remains equivalent.
- [ ] Wire header 40, sideband 40, queue entry 168, direct metadata 48, ownership, fence, predicate, and fallback semantics remain unchanged.
- [ ] Regression matrix GREEN, including mixed legacy/Gate, partial reads, variable payload, FD, HUP/error, close/rebind, duplicate/invalid frames.
- [ ] `git diff --check` PASS.
- [ ] ARM64 incremental native build PASS.
- [ ] ARM64 full-clean native build PASS.
- [ ] New warnings = 0 versus fresh base build.
- [ ] Final diff review completed.
- [ ] Atomic Conventional Commits created.
- [ ] Local HEAD = fork remote HEAD = CI headSha.
- [ ] Multi-ABI CI PASS.
- [ ] APK, ZIP, signer, and embedded/unstripped Build ID qualification PASS (formal zipalign may remain explicitly BLOCKED).
- [ ] Handoff/evidence synchronized; historical R3 evidence unchanged.
- [ ] Runtime remains NOT RUN; Stable and HDMI untouched.

## Evidence

Implementation and verification evidence will be written under this directory without overwriting `runtime-88e3f17/`.
