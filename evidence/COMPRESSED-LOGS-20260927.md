# Evidence logs compressed with zstd (2026-09-27)

At the user's request (F8 disk space; the Termux app had grown to ~60 GB), every `*.txt` / `*.log` of 1 MiB or more
under `evidence/` that had not been modified in the previous 24 hours was compressed **losslessly** with `zstd -9`:
275 files, 10348 MiB -> 312 MiB. Mostly raw logcat / `logcat-follow.txt` captures, which exist only locally (they are
never pushed to `waydefu/GPU`).

- Contents are byte-identical. For each file the original was deleted only after `zstd -dc <file>.zst | sha256sum`
  matched the original's sha256; any mismatch would have kept the original (0 mismatches). mtimes were kept.
- `COMPRESSED-LOGS-20260927.tsv` lists every file: path (relative to `evidence/`), original size, original sha256,
  compressed size.
- Frozen attempts are not re-judged or rewritten by this: only the storage format changed.
- Reading: `zstdcat <file>.zst | less`, or restore with `zstd -d <file>.zst` (keeps the .zst; add `--rm` to drop it).
  A `sha256sums.txt` that names a compressed file verifies after the file is restored.
- Tool: `$PREFIX/tmp/f8-shard/zlogs.sh` (Termux side). Tested first on synthetic data, including a forced-corruption
  case that had to keep its original. The first test run exposed an argument-order bug (`-o` after `--`), fixed
  before the real run; that run touched only the synthetic files.
