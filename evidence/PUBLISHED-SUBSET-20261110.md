# Published subset — 2026-11-10 documentation and handoff sync

This batch pushes the current handoffs, planning and design documents, patches, and the judgment-basis text from
evidence gate directories that changed since the last push. Local evidence is complete; this repository carries
the verdict basis only.

Published here:
- Handoffs and status documents (`HANDOFF-NEXT-SESSION-2026092*.md`, `HANDOFF-NEXT-SESSION-20260927.md`,
  `STATUS-HANDOFF-*`, `CONTINUATION.md`, `TEST-MATRIX.md`, `WORKTREE-MAP.md`, `docs/handoff/S3-*`).
- `evidence/session/**/*.md`, `*.py`, `*.sh`, `*.tsv` that are new or changed since the last push (design documents,
  gate write-ups, runner scripts, and the proot/daemon fix notes).
- Small gate verdict text under `evidence/{fence,exa,dri3,composite,baseline,present}/` (20 KB or less each).
- `evidence/control/branch-shas.txt` and `evidence/control/f8-x11gpu-launcher.sh`.
- `evidence/COMPRESSED-LOGS-20260927.{md,tsv,zlogs.sh}`: the index and tool for the zstd-compressed raw logs. Each
  `.tsv` row carries the original sha256, so a restored file can be checked against it.
- `patches/` (new or changed files only).

Deliberately NOT published (present locally, listed in the full local `sha256sums.txt`):
```
raw-logcat.txt, logcat-follow.txt, collect-input.txt, x3.maps   raw device captures; not read by any judge
*.zst                                                           zstd-compressed raw logs (see COMPRESSED-LOGS-20260927.md)
evidence/session/**/*.{txt,json,jsonl,out,log,raw,ring,status,pid,stdout,stderr}   raw run output
evidence/control/**/*.{apk,so}, evidence/control/**/logs/ and obj/                   binaries and native build logs
evidence/nonlegacy/*.{xwd,png}, evidence/x11gpu/**                                  screen captures and bulk binaries
src/, logs/, the merged markdown text file                                          product source lives in waydefu/termux-x11;
                                                                                   the merged text is a generated copy
```
Screenshots were not part of this batch. A later batch that needs one for a verdict publishes it explicitly.
