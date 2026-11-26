#!/usr/bin/env bash
# zlogs-safe.sh <dir> <manifest.tsv> [--dry-run]
# Safely zstd-compress *.txt / *.log >= 1 MiB under <dir> older than MIN_AGE_H hours (default 24).
# Safety invariants:
#   1. Both original and decompressed sha256 MUST match ^[0-9a-f]{64}$ and equal each other.
#   2. Writes to a temporary file first and atomically renames only after verification passes.
#   3. No destructive test hooks in production script; failure cleans temporary output and keeps original.
set -euo pipefail

DRY_RUN=0
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    *) ARGS+=("$arg") ;;
  esac
done

if [ "${#ARGS[@]}" -lt 2 ]; then
  echo "Usage: $0 <dir> <manifest.tsv> [--dry-run]" >&2
  exit 2
fi

D="${ARGS[0]}"
M="${ARGS[1]}"
AGE="${MIN_AGE_H:-24}"
ZSTD_BIN="${ZSTD_BIN:-$(command -v zstd)}"
SHA256_BIN="${SHA256_BIN:-$(command -v sha256sum)}"

if [ ! -d "$D" ]; then
  echo "ERROR: target directory does not exist: $D" >&2
  exit 2
fi
if [ -z "$ZSTD_BIN" ] || [ ! -x "$ZSTD_BIN" ]; then
  echo "ERROR: zstd binary not executable: $ZSTD_BIN" >&2
  exit 2
fi
if [ -z "$SHA256_BIN" ] || [ ! -x "$SHA256_BIN" ]; then
  echo "ERROR: sha256sum binary not executable: $SHA256_BIN" >&2
  exit 2
fi

mkdir -p "$(dirname "$M")"
[ -f "$M" ] || printf 'path\torig_bytes\torig_sha256\tzst_bytes\n' > "$M"

is_sha256() {
  [[ "$1" =~ ^[0-9a-f]{64}$ ]]
}

ok=0; fail=0; skip=0; bin=0; bout=0
while IFS= read -r -d '' f; do
  rel=${f#"$D"/}
  if [ -e "$f.zst" ]; then
    echo "SKIP exists $rel.zst"
    skip=$((skip + 1))
    continue
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    s=$(stat -c %s "$f")
    echo "DRY-RUN would compress $rel ($s bytes)"
    ok=$((ok + 1))
    continue
  fi

  h=$("$SHA256_BIN" < "$f" | awk '{print $1}' || true)
  if ! is_sha256 "$h"; then
    echo "FAIL sha256 orig $rel (kept original)"
    fail=$((fail + 1))
    continue
  fi
  s=$(stat -c %s "$f")
  tmp="$f.zst.tmp.$$"
  rm -f -- "$tmp"

  if ! nice -n 19 "$ZSTD_BIN" -q -9 -T3 -o "$tmp" -- "$f"; then
    echo "FAIL compress $rel (kept original)"
    rm -f -- "$tmp"
    fail=$((fail + 1))
    continue
  fi

  h2=$("$ZSTD_BIN" -dc -- "$tmp" 2>/dev/null | "$SHA256_BIN" | awk '{print $1}' || true)
  if is_sha256 "$h2" && [ "$h" = "$h2" ]; then
    mv -f -- "$tmp" "$f.zst"
    z=$(stat -c %s "$f.zst")
    touch -r "$f" "$f.zst"
    rm -f -- "$f"
    printf '%s\t%s\t%s\t%s\n' "$rel" "$s" "$h" "$z" >> "$M"
    ok=$((ok + 1)); bin=$((bin + s)); bout=$((bout + z))
  else
    echo "FAIL verify $rel (kept original)"
    rm -f -- "$tmp"
    fail=$((fail + 1))
  fi
done < <(find "$D" -xdev -type f \( -name '*.txt' -o -name '*.log' \) -size +1M -mmin +$((AGE * 60)) -print0)

echo "ZLOGS_SAFE ok=$ok fail=$fail skip=$skip in=$((bin / 1048576))MiB out=$((bout / 1048576))MiB"
[ "$fail" -eq 0 ]
