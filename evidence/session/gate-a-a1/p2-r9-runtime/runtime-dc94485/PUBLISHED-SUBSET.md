# What is in this directory, and what is not

`sha256sums.txt` is the **complete** local evidence manifest: 283 files plus the
runner. Three kinds of capture are deliberately **not** published here, matching the
convention the R8 evidence in this repo already follows (no `raw-logcat.txt` appears
anywhere under `p2-r8-runtime`):

```
raw-logcat.txt      0.7-2.1 MB per attempt, ~10 MB total. The windowed device log.
collect-input.txt   byte-identical concatenation of raw-logcat + ring + summary.
x3.maps             ~250 KB per attempt, the X process address-space map.
env.txt             replaced by env-cell.txt.
```

`env-cell.txt` carries the variables the cell is actually about — `CELL_ID`,
`DISPLAY`, and every `TERMUX_X11_*` — and drops the rest of the runner's environment,
which is Claude Code session state (`CLAUDE_CODE_SESSION_ID`, OAuth scopes, tracing
headers, D-Bus and SSH agent sockets) with no evidential value and no business being
in a public repo. No credential was found in any of it; it is omitted because it is
irrelevant, not because it is dangerous.

Everything a verdict rests on IS here: `judge.json`, `judge.stdout`, `judge.rc`,
`identity-boundaries.jsonl`, `stale-replay.json`, `registry-fresh.json`,
`x-observations.jsonl`, `renderer-observations.jsonl`, `gatea-ring.txt`,
`gatea-summary.txt`, `fixture.jsonl`, `artifact-binding.json`, `manifest.json`,
`installed-apk.sha256.txt`, `stable-before.json` / `stable-after.json`, the `/proc`
snapshots and the fd tables.

To verify the published subset:

```bash
grep -vE '/(raw-logcat\.txt|collect-input\.txt|x3\.maps|env\.txt)$' \
  runtime-dc94485/sha256sums.txt | sha256sum -c
```

Run it from `evidence/session/gate-a-a1/p2-r9-runtime/`. Every remaining line must
pass. The omitted files are still hashed in `sha256sums.txt`, so the local set they
came from is pinned even though the bytes are not republished.

Note on `gatea-ring.txt` and `gatea-summary.txt`: several attempts have these empty,
and that is correct. `lorieGateADumpSummary` writes them only on a fatal, a clean
close or a terminate, so a cell that leaves X healthy produces neither. The same
events are in the live `gatea-telemetry` stream, which is what `judge-r9.py`'s
`ring_events()` and `r9_evidence.registry_state()` read. See `V2-R9-AGG.md`.
