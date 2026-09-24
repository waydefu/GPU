# Published subset — 2026-09-24 GL / Electron batch

Covers `evidence/session/gl/` and `evidence/session/gate-a-a1/p2-pga-rca/runtime-f592241-gl/` (the GL-BENCH /
GL-FEAS cells). Local evidence is complete; this repository carries the verdict basis only. Every run directory keeps
its full local `sha256sums.txt`; files listed there but absent here were deliberately not published:

```
raw-logcat.txt          full device logcat (1.7-48 MB per cell); not read by any judge
```

Screenshots (`*.png`) ARE published here: the ELECTRON-BENCH judge reads the V2 screenshots (`screenshot_ok`).

Batch contents:
- GL-FEASIBILITY-01, GLIBC-RUNNER-EVAL-01, MESA-KGSL-UBUNTU-BUILD-01 (Mesa 26.0.6 Turnip KGSL + Zink for the Ubuntu guest).
- GL-BENCH-01 (touch-invalidated) and GL-BENCH-02: `GL_GPU_BENEFIT`, `VK_GPU_BENEFIT` (4-5x faster, 0.1-0.18x CPU per frame).
- ELECTRON-GPU-PROBE (ANGLE exits when libpci finds no /proc/bus/pci; `libnopci.so` shim) and
  ELECTRON-BENCH-01 (Cursor, GPU vs --disable-gpu): `ELECTRON_GPU_NO_BENEFIT` (CPU -3.5%, bar 20%).
- INCIDENT-20260924-X3-EXA-BUG-FATAL (swiping the experimental app away = Gate A `x-hup/6` design halt; an initial
  misreading as EXA FatalError is corrected in the document) and two RCAs of the `EXA bug: devPrivate.ptr` warning
  (written by background sessions; their verdict tables were read, the bodies were not fully reviewed).
- Runner `run-gl-bench.sh` (KIND=cmd), pocket-mode prefs helper `exp-pocket-prefs.sh`.
