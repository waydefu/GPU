# Gate A A1 marker execution — 2026-09-12 (HEAD 4196798, run 34694695463)

## STATUS

ONE controlled Experimental `:3` launch on display 0 with marker APK
(`5ad7d2c6…c90`). Probe completed all 9 runs. No crash. Teardown complete.
No retry was performed.

## EVIDENCE

- PRECALL present (`20:57:20.491`, PID 23546) → caller reached probe call boundary.
- ENTRY present (same second, same PID) → PROBE_BODY_CONFIRMED: YES (CASE 3).
- CONTROL (RGBX, value 2): 3/3 SHADER_SAMPLE_EXACT, exact_fail_pixels=0, maxΔ=0.
- BGRA_CANDIDATE (value 5): 3/3 SHADER_SAMPLE_EXACT, exact_fail_pixels=0, maxΔ=0.
  actual_rgba == expected_rgba on every run (e.g. `13273B4F,596D7183,97A9BDC1,D7E3F1FB`).
  No black, no channel swap, no other mismatch. Zero ALLOC/LOCK/EGL/GL/FBO/shader failures.
- RGBA_DIAGNOSTIC (value 1): 3/3 SHADER_SAMPLE_EXACT.
- Aggregate: runs=9, all *_FAIL counters 0, all *_EXACT 3. state_restore_error=0x0000.
  DIRECT_FBO_DIAGNOSTIC=SKIPPED (source-declared).
- No Fatal signal in the collection window. X `:3` (PID 23546) survived the probe.
- Teardown: `am force-stop` exit 0; lingering host X (ppid=1, exact allowed cmdline)
  killed by exact PID; post-scan Stable only (PID 14862 `:1 -legacy-drawing`);
  `:3` unreachable afterwards; no restart. HDMI untouched.
- Raw: `marker/runtime/m6-crash-logcat-main-since-*.raw.txt` (lines 847-848 markers,
  930-979 runs+aggregate), `m6-x3-launcher.raw.log`, `m7-*` teardown files.

## VERDICT

- A1 byte/import/shader-sampling microprobe: PASS
  (RGBX 3/3 exact + BGRA 3/3 exact, deterministic, zero-error pipeline).
- Production Gate A: NOT PASS (separate phase; ownership/fence/lifecycle unreviewed).
- Earlier PID 21238 startup SIGSEGV: ROOT CAUSE STILL UNKNOWN. This clean 9/9 run
  does not explain it and is not merged with it. It stands as observed / non-reproduced
  in this iteration. No second launch was performed to chase it.

## NEXT (one action only)

Propose ownership/fence/lifecycle architecture review before any production Gate A
prototype. Do NOT implement production EXA/Composite integration in the same motion.
AWAIT explicit authorization; no further runtime.
