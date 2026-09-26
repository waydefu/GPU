#!/bin/bash
# diagnostic only (not judged): what do Claude Desktop's processes look like under an automatic shard?
OUT=$1; mkdir -p "$OUT"
H=/tmp/autoshard-diag-home-$$; mkdir -p "$H/.config" "$H/.local/share" "$H/.cache"
TT=$(awk '/^TracerPid/{print $2}' /proc/self/status)
HOME=$H XDG_CONFIG_HOME=$H/.config XDG_DATA_HOME=$H/.local/share XDG_CACHE_HOME=$H/.cache DISPLAY=:99 \
  /usr/lib/claude-desktop/claude-desktop --password-store=basic --no-sandbox --disable-gpu --disable-dev-shm-usage --ozone-platform=x11 \
  > "$OUT/app.stdout" 2> "$OUT/app.stderr" &
SP=$!; sleep 10
echo "test_tracer=$TT f8-shard=$SP" > "$OUT/diag.txt"
for p in /proc/[0-9]*; do
  pid=${p#/proc/}; tp=$(awk '/^TracerPid/{print $2}' $p/status 2>/dev/null)
  [ -n "$tp" ] && [ "$tp" != 0 ] && [ "$tp" != "$TT" ] || continue
  c=$(tr '\0' '|' < $p/cmdline 2>/dev/null | cut -c1-110)
  e=$(tr '\0' '\n' < $p/environ 2>/dev/null | grep -c "^HOME=$H\$")
  el=$(tr '\0' '\n' < $p/environ 2>/dev/null | wc -l)
  case "$c" in *claude*|*Claude*|/proc/self/exe*|*crashpad*) echo "$pid tracer=$tp home_match=$e environ_lines=$el comm=$(cat $p/comm) cmd=$c" >> "$OUT/diag.txt";; esac
done
kill -TERM $SP; sleep 3; rm -rf "$H"
