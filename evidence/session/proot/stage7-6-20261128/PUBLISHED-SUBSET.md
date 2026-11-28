# Published subset — Stage 7.6 runs (2026-11-28)

Published:

- `security/judged/` — judged S1–S7 run `s76-sec.hcvaffxi` (candidate `c583002`): per-gate records `s76-results.redacted.jsonl`, `s76-judge.json`, `candidate`, `scripts.sha256`, `fixture-l2s-links`.
- `security/s5-attempt2/` — S5 rerun after amendment A3 (`s76-sec.fzyyr4yr`, `771bd50`, same governed scripts).
- `security/dry1-not-judged/` — DRY-1 (`s76-sec.q5fd7yyy`, candidate `f149ba5`): kept as recorded; its S3 leak found F15 and its S1 mismatch found erratum E1. Not judged.
- `security/s5-supplementary/` — the supplementary child poll; the unfiltered version is void (matched unrelated `git cat-file` processes).
- `matrix/mode{4,2,6}/` — matrix records, `judge.json`, envelopes, native regression tail, `candidate`, `scripts.sha256`, `budget-init.json`, `fixture-l2s-links` for the judged runs `s75g-m4.YUQebl`, `s75g-m2.YPlF2l`, `s75g-m6.gZ0DwI` (`771bd50`).

- `matrix/mode4-a4-rerun/` — the user-authorised mode-4 rerun under amendment A4 (`s75g-m4.G8Vp1B`, `83514c3`, same governed scripts), with the pre-run thermal settle record `a4-settle.json` and the environment note `a4-environment.txt` (external cooler attached during earlier runs, off for this one). The earlier judged HOLD run stays in `matrix/mode4/`.

Redaction: trusted-root paths of private projects outside `GPU加速` are replaced with `/root/projects/private-<sha256[:8]>` (same label for the same path). Results are otherwise unchanged.

Not published (local only, under `/data/data/com.termux/files/home/.hyb2verify.XeHE9hQd/`): route logs, daemon audit logs, fixtures, helper scripts, the aborted mode-4 attempt `s76m/s75g-m4.BW38kj` (chain tooling: PRoot envelope lacked the trusted-root variable; no cell ran) and the host-invalid mode-4 attempt `s76m/s75g-m4.U9MxFV` (C1 cycle 3: CPU 85.7 °C, then battery 48.0 °C after the one A2 rerun; chain stopped). `sha256sums.txt` lists every published file.
