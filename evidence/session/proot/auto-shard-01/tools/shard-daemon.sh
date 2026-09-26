#!/data/data/com.termux/files/usr/bin/bash
# shard-daemon.sh — resident Termux-side helper of f8-shard v2 (AUTO-SHARD, 2026-09-26).
# f8-shard v1 started every shard through `am startservice` (TermuxService): 0.96-1.19 s per call, almost all
# of it the app_process start of `am` itself. Started once that way (f8-shard does it in the background when
# it finds no daemon), this script stays outside every proot tracer, like shard-run.sh, takes job dirs from
# <base>/ctl.fifo and starts shard-run.sh on each at once. Installed next to shard-run.sh (shard2/).
# One instance (flock on <base>/daemon.lock). It holds both ends of the FIFO, so a writer never blocks and the
# daemon never reads EOF; idle it sleeps in read(2). Every 20 jobs it prunes job dirs, keeping the newest 200.
set -u
BASE=/data/data/com.termux/files/usr/tmp/f8-shard
RUN=$(cd "$(dirname "$0")" && pwd)/shard-run.sh
mkdir -p "$BASE" || exit 3
exec 9> "$BASE/daemon.lock"
flock -n 9 || exit 0
FIFO=$BASE/ctl.fifo
[ -p "$FIFO" ] || { rm -f "$FIFO"; mkfifo -m 600 "$FIFO" || exit 3; }
exec 3<> "$FIFO" || exit 3
echo $$ > "$BASE/daemon.pid"
n=0
while read -r J <&3; do
  case "$J" in "$BASE"/2*) ;; *) continue;; esac
  case "$J" in *..*|*' '*) continue;; esac
  [ -d "$J" ] || continue
  setsid "$RUN" "$J" < /dev/null > /dev/null 2>&1 &
  n=$((n + 1))
  if [ $((n % 20)) = 0 ]; then
    ls -1dt "$BASE"/2*/ 2>/dev/null | tail -n +201 | while read -r d; do rm -rf -- "$d"; done
    # proot-fast8 opens the auto-shard log for every line (O_APPEND), so renaming it is safe
    [ "$(stat -c %s "$BASE/autoshard.log" 2>/dev/null || echo 0)" -gt 1048576 ] && mv -f "$BASE/autoshard.log" "$BASE/autoshard.log.1"
  fi
done
