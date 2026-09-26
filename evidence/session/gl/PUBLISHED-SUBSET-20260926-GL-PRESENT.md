# Published subset — 2026-09-26 GL-PRESENT batch (mainline #3 step 1)

Covers `evidence/session/gl/gl-present-01/`, `gl-present-02/`, `gl-present-03/`, their freeze / result documents
(`GL-PRESENT-0{1,2,3}-{FREEZE,RESULT}.md`), `gl-present-chain.sh`, and the tool source snapshot
`gl-present-tools-8423f0a/` (fork `feat/exa-async-proto-20260923` is local-only; build with its `build.sh`).
Local evidence is complete; this repository carries the verdict basis only. Every cell keeps its full local
`sha256sums.txt`; files listed there but absent here were deliberately not published:

```
raw-logcat.txt          full device logcat of each cell (not read by any judge; may contain other people's
                        Bluetooth addresses). xdbg-01's DRI3 witness lines are read from it by the judge:
                        the judge's view of them is kept in judge.txt / judge.json (xdbg_witness).
```

Batch verdicts:
- GL-PRESENT-01 `GL_PRESENT_INVALID` (J0 rule defect: glx-off swapchain set-up imports counted as presenting).
- GL-PRESENT-02 `GL_PRESENT_INVALID` (02's own rule defect: vk-off empty protocol histogram read as missing;
  plus one empty focus read in rep2 vk-off).
- GL-PRESENT-03 `PRESENT_COST_IS_X3_PER_PIXEL_COPY`: VK and GLX hand DRI3 LINEAR buffers to X3 and X3 copies them
  per frame on its main thread (cost scales with pixels); EGL/Zink `PATH_NOT_PRESENTED` (black window).
Non-judged cells kept for the record: `gl-present-01/dry-01` (BLOCKED x_root_size), `dry-01-r2`, `diag-egl-01`.
