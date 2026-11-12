#!/data/data/com.termux/files/usr/bin/bash
# zlogs.sh <dir> <manifest.tsv> — losslessly zstd-compress *.txt / *.log >= 1 MiB under <dir> that are older than
# MIN_AGE_H hours (default 24). Each original is removed only after `zstd -dc file.zst | sha256sum` equals the
# original's sha256; otherwise the .zst is removed and the original kept. TEST_CORRUPT=<substring> truncates the
# .zst of matching paths before verification (tests only: proves the gate keeps the original).
set -u
D=$1; M=$2; AGE=${MIN_AGE_H:-24}
P=/data/data/com.termux/files/usr/bin
ok=0; fail=0; skip=0; bin=0; bout=0
[ -f "$M" ] || printf 'path\torig_bytes\torig_sha256\tzst_bytes\n' > "$M"
while IFS= read -r -d '' f; do
  rel=${f#"$D"/}
  if [ -e "$f.zst" ]; then echo "SKIP exists $rel.zst"; skip=$((skip+1)); continue; fi
  h=$($P/sha256sum < "$f" | cut -d' ' -f1); s=$(stat -c %s "$f")
  if ! nice -n 19 $P/zstd -q -9 -T3 -o "$f.zst" -- "$f"; then echo "FAIL compress $rel"; rm -f -- "$f.zst"; fail=$((fail+1)); continue; fi
  case "$f" in *${TEST_CORRUPT:-/nonexistent/}*) truncate -s 100 "$f.zst";; esac
  h2=$($P/zstd -dc -- "$f.zst" 2>/dev/null | $P/sha256sum | cut -d' ' -f1)
  if [ "$h" = "$h2" ]; then
    z=$(stat -c %s "$f.zst"); touch -r "$f" "$f.zst"; rm -f -- "$f"
    printf '%s\t%s\t%s\t%s\n' "$rel" "$s" "$h" "$z" >> "$M"; ok=$((ok+1)); bin=$((bin+s)); bout=$((bout+z))
  else
    echo "FAIL verify $rel (kept original)"; rm -f -- "$f.zst"; fail=$((fail+1))
  fi
done < <(find "$D" -xdev -type f \( -name '*.txt' -o -name '*.log' \) -size +1M -mmin +$((AGE*60)) -print0)
echo "ZLOGS ok=$ok fail=$fail skip=$skip in=$((bin/1048576))MiB out=$((bout/1048576))MiB"
