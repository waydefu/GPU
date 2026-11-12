#!/data/data/com.termux/files/usr/bin/bash
# T7: daemon dies while a shard lives; a new daemon must still get the lock. Only kills pids it started.
set -u
S=$1; V=$2; export PATH=/data/data/com.termux/files/usr/bin:$PATH; export F8_SHARD_DAEMON_CHECK_S=1
B=$S/b7-$V; rm -rf $B; mkdir -p $B; : > $S/$V/ran.txt; mine=()
alive() { [ -d /proc/$1 ] && tr '\0' ' ' < /proc/$1/cmdline 2>/dev/null | grep -q "$S/\|sleep 20"; }
start() { rm -f $B/daemon.pid; F8_SHARD_BASE=$B setsid -f "$S/$V/shard-daemon.sh" < /dev/null > /dev/null 2>&1
  for i in $(seq 30); do [ -s "$B/daemon.pid" ] && break; sleep 0.1; done; sleep 0.2; cat "$B/daemon.pid" 2>/dev/null; }
a=$(start); mine+=($a)
mkdir -p $B/20260927-long; printf '%s\n' "$B/20260927-long" > $B/ctl.fifo; sleep 0.5
c=$(awk '{print $1}' $S/$V/ran.txt | head -1); mine+=($c)
echo "$V daemon=$a shard-child=$c child fds: $(ls -l /proc/$c/fd 2>/dev/null | grep -c 'f8-shard\|b7-') refs to lock/fifo"
kill $a; sleep 0.3
b=$(start); [ -n "$b" ] && mine+=($b)
if [ -n "$b" ] && alive $b; then echo "PASS T7 $V new daemon $b took the lock while shard $c lives"; r=0
else echo "FAIL T7 $V no new daemon (lock still held by shard $c)"; r=1; fi
for q in "${mine[@]}"; do [ -n "$q" ] && alive $q && kill $q; done; sleep 0.3
for q in "${mine[@]}"; do [ -n "$q" ] && alive $q && echo "LEFTOVER $q"; done
exit $r
