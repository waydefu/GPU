# INCIDENT 2026-09-23 16:17 — lmkd killed com.termux; Stable :1 went down with it

**Redline breached (indirectly): Stable `:1` was killed.** Not by a signal from me, but by
Android's low-memory killer reacting to a host-side analysis command I ran.

## Evidence (device event log, read after the fact)

```
09-23 16:17:09.895  killinfo: [com.termux,8415,10365,200,101,111148,259,15373988,...]
09-23 16:17:09.998  am_proc_died: [0,8415,com.termux,200,4]
```

com.termux (pid 8415) is the parent of the PRoot (20859), and through it of Stable X `:1`
(20881), the daily XFCE, Claude Desktop and the 5038 adb server - all died. The user
relaunched at ~16:22 (Stable X is now pid 7340).

## Cause

At ~16:14-16:17 I ran `xfce_collect.py` + `judge-xfce.py` on rca3-g-01 and rca3-c-01. Their
raw-logcat.txt files were 912 MB and 1.3 GB; the collector reads the whole file
(`read_text()` + a list of per-line dicts), i.e. several GB of Python heap, inside the
Termux app's process tree. lmkd chose com.termux.

Why the logs were that big: 98.5% of the lines are `GATEA_EVENT` (TELEMETRY=1 writes one
logcat line per Gate A event; `loriePrepareAccess` alone traces event 30 on every CPU access).
With X untraced it processed ~5x more work per second than the traced runs, so ~5 MB/s.

## Fixes required before ANY further analysis or device run

1. Collectors stream line by line with bounded memory, filtering by pid/tag first.
2. Every host-side analysis runs under a hard address-space cap (`prlimit --as`), so an
   overrun kills only the tool, never the Termux app.
3. Check MemAvailable before heavy work; refuse below a floor.
4. Workload runs must not capture unbounded per-event telemetry to disk (tag-filtered
   logcat; counters come from the close summary).

Nothing of mine was running after the kill (checked: no runner, sampler, series or X3).

## Fixes — done and verified (2026-09-23 16:30–16:50, fork b650982)

| # | What | Verified by |
|---|---|---|
| 1 | `xfce3/xfce_collect.py`, `oracle/judge-oracle.py`, `b3/b3_attribution.py` read the capture **one line at a time** (`iter_logcat`); GATEA_EVENT completeness via a seq bitmap (`SeqSet`) | xfce3-c1-01 (895 MB): **17 MB** peak RSS, 21.6 s, output identical field-for-field to the stored xfce-run.json of the old collector. rca3-g-01 (912 MB) identical to stored; rca3-c-01 (1.3 GB): 17 MB, 45 s. On a 65 MB sample the old collector peaked at **441 MB** (~7x the file) — the mechanism of the incident, quantified. Tests: streaming == whole-text parse incl. `\r`, `\x0c`, U+2028, invalid UTF-8; SeqSet == set semantics; mutants 24/24, 11/11, 8/8 killed |
| 2 | `tests/common/safe-run.sh`: RLIMIT_AS cap (default 1024 MB), absolute nice 19 | a 3 GB allocation dies with MemoryError at ~240 MB under `--cap-mb 256`; the phone is untouched |
| 3 | same wrapper refuses below MemAvailable 3072 MB (exit 97); `--check-only` preflight also enforces a disk floor | floor refusal exit 97 observed; every runner (XFCE V3, series, oracle, B.3, device queue, OPLAT) calls it before capture and wraps every collector/judge |
| 4 | capture size | **changed from what was promised, on evidence**: the capture was already tag-filtered; 98.5% of it is our own `gatea-telemetry` tag, which the frozen XFCE/oracle/B.3 designs need for event completeness. Dropping it would make completeness impossible by construction. Instead: the size can no longer hurt memory (1–3), and every runner refuses to start with less than 15 GB free disk |

Frozen evidence is untouched: the old judgements stand; the new collector only reproduced
them (outputs written to scratch, compared, not written back).
