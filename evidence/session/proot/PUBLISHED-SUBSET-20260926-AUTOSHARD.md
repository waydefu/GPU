# Published subset — 2026-09-26 evening (X3-DIRECT-FEAS-01..03, AUTO-SHARD-01)

Covers:
- `evidence/session/gl/X3-DIRECT-FEAS-RESULT.md` and `evidence/session/gl/x3-direct-feas/`: freezes, probe sources,
  raw probe outputs and `sha256-before-run.txt` (the probe binaries themselves stay local; rebuild from the
  sources with the command in the result doc).
- `evidence/session/proot/AUTO-SHARD-01-FREEZE.md`, `AUTO-SHARD-01-RESULT.md`, `proot-fast8-autoshard.patch` and
  `evidence/session/proot/auto-shard-01/`: every judged and dry attempt (`rules-01`, `real-01` frozen FAIL,
  `real-dry-01`, `real-dry-02`, `real-02`, `test_shard-v2`, `test_shard-final`), the tool snapshot `tools/`
  (+ `tools.sha256`), the apply fix `apply-fix1/` and the diagnostic `diag-claude-setproctitle/`.
- `HANDOFF-NEXT-SESSION-20260926-AUTOSHARD.md`.

The fork branch holding the shard tools (`feat/exa-async-proto-20260923`, `tests/tracer_shard/`) is local-only;
`auto-shard-01/tools/` is the snapshot of exactly what was run and installed.

Deliberately not published:

```
auto-shard-01/diag-claude-setproctitle/diag.txt   filtered: the local file also lists the command lines of the
                                                  user's own running Claude Code, Serena and shell processes.
                                                  Kept here: the test instance (tracer 2725) and the user's
                                                  daily Claude Desktop lines, which are what the result cites.
```

No raw logcat and no file over 100 KB in this batch (no device run was made).

Verdicts:
- X3-DIRECT-FEAS-01 `DMABUF_IMPORT_UNAVAILABLE` (Android EGL/GLES cannot sample a client dma-buf: no zero copy).
- X3-DIRECT-FEAS-02 `VK_DMABUF_GPU_COPY_FAIL` (frozen: the Adreno driver asks +5300 bytes for external resources).
- X3-DIRECT-FEAS-03 `VK_DMABUF_GPU_COPY_OK` (system Vulkan GPU-copies a dma-buf into an X3-style AHB, exact pixels).
- AUTO-SHARD-01 `AUTOSHARD_RULES_PASS` (rules-01 + real-02; real-01 `AUTOSHARD_REAL_FAIL` frozen, tool defect).
  Applied to the daily desktop the same evening; the first apply did not switch it on (proot-distro drops
  non-whitelisted PROOT_* variables) and fix 1 (wrapper `out8/auto/proot-fast8`) did, verified live.
