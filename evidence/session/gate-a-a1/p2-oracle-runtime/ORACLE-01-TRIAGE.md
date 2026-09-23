# ORACLE-01 triage (§19) — V1 verdict FAIL_CORRECTNESS stands; classification INVALID_CONSTRUCTION

DATE 2026-09-23 · run `runtime-bfb5769/oracle-01` · judge V1 (`judge-oracle.py` sha c60da2a6… lineage, streaming b650982)
The V1 verdict file is frozen and is NOT re-judged. This note classifies it (plan §19.1 Q5).

```
V1 verdict   FAIL_CORRECTNESS
             correctness: all pass (persistent 1298 / fresh 36 / negative 7 exact, maxd 0, lifecycle balanced,
                          no fatal, X ends only by terminate, Activity survives)
             validity:    all pass (events complete 34094/34094, untraced, screen awake, Stable unchanged)
             attribution: persistent_all_direct FALSE (event5 1300 for 1298 cases) · negative_no_direct FALSE (2)
```

## Two construction defects (both found from the run's own data + source; no rerun)

1. **Judge windows overlapped.** The three phases were 17 µs apart and V1 widened every window ±5 ms, so the
   last/first event=5 lines near each boundary were counted in two phases. Strict windows on the same logcat:
   persistent **1298**, fresh **36**, negative **1** (total 1335 = every event=5 in the run, none outside phases).
2. **The "repeat" negative was not a negative.** It composited 4×4 from a 4×4 RepeatNormal source at (0,0). The
   EXA core removes a useless repeat before the driver sees the op (`exaComposite`, xserver `exa/exa_render.c:887-891`:
   "Remove repeat in source if useless"), so the driver received a plain in-slice Over a8r8g8b8→x8r8g8b8 and
   `lorieCanAccelCompositePictures` correctly accepted it. The one strict negative event=5 (+1.878 ms after
   negative BEGIN, seq 34044, src 103 / dst 104) is that case: by source the other six are rejected by the
   predicate (op≠Over, mask, dst a8r8g8b8, filter≠nearest, transform, mask/CA); by time it is the 5th case; the
   buffer ids are new negative-phase buffers.

Product behaviour on this run: 1341/1341 exact; every persistent case direct (1298/1298); every genuinely
unsupported negative stayed in software.

## Consequence

ORACLE_FROZEN_V2 (fork, this change): quiet 100 ms gaps between windows and around every negative case, one MARK
per negative case, window (BEGIN−1 ms, END] for ms-truncated stamps, "repeat" = 8×8 composite from the 4×4 source
(the repeat takes effect), and a construction check (`phase_gaps_quiet`) that makes a V1-shaped run INVALID.
Next run: `oracle-02` under V2. oracle-01 keeps its V1 verdict.
