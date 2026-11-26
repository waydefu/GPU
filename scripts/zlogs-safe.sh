#!/usr/bin/env bash
# zlogs-safe.sh <dir> <manifest.tsv> [--dry-run | --remove-source]
# Only use --remove-source after stopping writers and rotation for the input tree.
set -euo pipefail

MODE=
paths=()
for arg in "$@"; do
  case "$arg" in
    --dry-run|--remove-source)
      if [[ -n "$MODE" ]]; then
        echo "ERROR: choose one mode" >&2
        exit 2
      fi
      MODE=$arg ;;
    --*) echo "ERROR: unknown option $arg" >&2; exit 2 ;;
    *) paths+=("$arg") ;;
  esac
done
if (( ${#paths[@]} != 2 )); then
  echo "Usage: $0 <dir> <manifest.tsv> [--dry-run | --remove-source]" >&2
  exit 2
fi

D=$(realpath -e -- "${paths[0]}")
M=${paths[1]}
AGE=${MIN_AGE_H:-24}
ZSTD_BIN=${ZSTD_BIN:-$(command -v zstd)}
SHA256_BIN=${SHA256_BIN:-$(command -v sha256sum)}

if [[ ! -d "$D" || ! "$AGE" =~ ^[0-9]+$ || ! -x "$ZSTD_BIN" || ! -x "$SHA256_BIN" ]]; then
  echo "ERROR: invalid input directory, age, or compression tools" >&2
  exit 2
fi
manifest_dir=$(dirname -- "$M")
mkdir -p -- "$manifest_dir"
exec {lock_fd}>"$M.lock"
flock -x "$lock_fd"

if [[ -L "$M" || ( -e "$M" && ! -f "$M" ) ]]; then
  echo "ERROR: manifest must be a regular file" >&2
  exit 2
fi
if [[ ! -e "$M" && "$MODE" != --dry-run ]]; then
  printf 'path\torig_bytes\torig_sha256\tzst_bytes\n' > "$M"
fi

fingerprint() {
  [[ -f "$1" && ! -L "$1" ]] && stat -c '%d:%i:%s:%y:%z' -- "$1"
}

hash_stream() {
  "$SHA256_BIN" | awk '{print $1}'
}

archive_one() (
  local source=$1 relative=$2 archive=$1.zst snapshot hash decoded size zsize
  local temp_archive= temp_manifest=
  trap '[[ -z "$temp_archive" ]] || rm -f -- "$temp_archive"; [[ -z "$temp_manifest" ]] || rm -f -- "$temp_manifest"' EXIT

  if [[ "$relative" == *$'\t'* || "$relative" == *$'\n'* || "$relative" == *$'\r'* ]]; then
    echo "FAIL filename cannot be represented in TSV (kept source)" >&2
    return 1
  fi
  if ! snapshot=$(fingerprint "$source") || ! hash=$(hash_stream < "$source") ||
    [[ ! "$hash" =~ ^[0-9a-f]{64}$ ]]; then
    echo "FAIL sha256 orig $relative (kept source)" >&2
    return 1
  fi
  size=$(stat -c '%s' -- "$source") || return 1
  temp_archive=$(mktemp -- "$archive.tmp.XXXXXXXX") || return 1
  if ! nice -n 19 "$ZSTD_BIN" -q -9 -T3 -c -- "$source" > "$temp_archive"; then
    echo "FAIL compress $relative (kept source)" >&2
    return 1
  fi
  if ! decoded=$("$ZSTD_BIN" -dc -- "$temp_archive" | hash_stream) || [[ "$decoded" != "$hash" ]]; then
    echo "FAIL verify $relative (kept source)" >&2
    return 1
  fi
  if [[ $(fingerprint "$source") != "$snapshot" ]] ||
    ! decoded=$(hash_stream < "$source") || [[ "$decoded" != "$hash" ]] ||
    [[ $(fingerprint "$source") != "$snapshot" ]]; then
    echo "FAIL source changed $relative (kept source)" >&2
    return 1
  fi

  zsize=$(stat -c '%s' -- "$temp_archive") || return 1
  chmod --reference="$source" -- "$temp_archive" && touch -r "$source" -- "$temp_archive" || return 1
  sync -- "$temp_archive" || return 1
  temp_manifest=$(mktemp -- "$M.tmp.XXXXXXXX") || return 1
  if [[ ! -f "$M" || -L "$M" ]] || ! {
    cat -- "$M" &&
      printf '%s\t%s\t%s\t%s\n' "$relative" "$size" "$hash" "$zsize"
  } > "$temp_manifest" || ! chmod --reference="$M" -- "$temp_manifest" || ! sync -- "$temp_manifest"; then
    echo "FAIL stage manifest $relative (kept source)" >&2
    return 1
  fi
  if [[ $(fingerprint "$source") != "$snapshot" ]]; then
    echo "FAIL source changed $relative (kept source)" >&2
    return 1
  fi
  if ! ln -T -- "$temp_archive" "$archive" || ! sync -- "$(dirname -- "$archive")"; then
    echo "FAIL publish archive $relative (kept source)" >&2
    return 1
  fi
  if ! mv -T -- "$temp_manifest" "$M" || ! sync -- "$manifest_dir"; then
    echo "FAIL commit manifest $relative (kept source and archive)" >&2
    return 1
  fi
  temp_manifest=
  if [[ "$MODE" == --remove-source ]]; then
    if [[ $(fingerprint "$source") != "$snapshot" ]]; then
      echo "FAIL source changed before removal $relative (kept source and archive)" >&2
      return 1
    fi
    rm -- "$source" || return 1
  fi
  printf '%s %s\n' "$size" "$zsize"
)

list=$(mktemp)
trap 'rm -f -- "$list"' EXIT
find "$D" -xdev -type f \( -name '*.txt' -o -name '*.log' \) -size +1M -mmin "+$((AGE * 60))" -print0 > "$list"

ok=0; fail=0; skip=0; bin=0; bout=0
while IFS= read -r -d '' f; do
  relative=${f#"${D%/}"/}
  if [[ -e "$f.zst" || -L "$f.zst" ]]; then
    if [[ -f "$M" && -f "$f.zst" && ! -L "$f.zst" ]] &&
      ARCHIVE_RELATIVE="$relative" awk -F '\t' 'NR > 1 && $1 == ENVIRON["ARCHIVE_RELATIVE"] { found=1 } END { exit !found }' "$M"; then
      echo "SKIP recorded archive exists $relative.zst (kept source)"
      skip=$((skip + 1))
    else
      echo "FAIL existing archive without a usable manifest record $relative.zst (kept source)" >&2
      fail=$((fail + 1))
    fi
  elif [[ "$MODE" == --dry-run ]]; then
    echo "DRY-RUN would compress $relative"
    ok=$((ok + 1))
  elif sizes=$(archive_one "$f" "$relative"); then
    read -r size zsize <<< "$sizes"
    ok=$((ok + 1)); bin=$((bin + size)); bout=$((bout + zsize))
  else
    fail=$((fail + 1))
  fi
done < "$list"

echo "ZLOGS_SAFE ok=$ok fail=$fail skip=$skip in=$((bin / 1048576))MiB out=$((bout / 1048576))MiB"
(( fail == 0 ))
