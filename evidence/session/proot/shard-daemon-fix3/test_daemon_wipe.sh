#!/data/data/com.termux/files/usr/bin/bash
# Functional test of shard-daemon fix 3. Only kills pids it started (cmdline must contain $S).
set -u
S=$1; export PATH=/data/data/com.termux/files/usr/bin:$PATH; export F8_SHARD_DAEMON_CHECK_S=1
fail=0; mine=()
ok()  { echo "PASS $*"; }
bad() { echo "FAIL $*"; fail=1; }
start() { # $1=old|new $2=base ; prints pid of the daemon that holds the lock
  F8_SHARD_BASE=$2 setsid -f "$S/$1/shard-daemon.sh" < /dev/null > /dev/null 2>&1
  for i in $(seq 50); do [ -s "$2/daemon.pid" ] && break; sleep 0.1; done
  sleep 0.2; cat "$2/daemon.pid"
}
alive() { [ -d /proc/$1 ] && tr '\0' ' ' < /proc/$1/cmdline 2>/dev/null | grep -q "$S/"; }
job() { mkdir -p "$1/20260927-$2"; printf '%s\n' "$1/20260927-$2" > "$1/ctl.fifo"; }
wipe() { find "$1" -mindepth 1 -delete; }   # what Termux does to $PREFIX/tmp

# T0 control (must be red): old daemon survives a wipe + a second start
B=$S/b0; rm -rf $B; mkdir -p $B
p1=$(start old $B); mine+=($p1); wipe $B; p2=$(start old $B); mine+=($p2); sleep 3
if alive $p1 && alive $p2 && [ "$p1" != "$p2" ]; then ok "T0 control reproduces leak (old $p1 and $p2 both alive)"; else bad "T0 control did not reproduce ($p1 $p2)"; fi

# T1 job goes through, T2 singleton, T3 no false exit over 4 checks
B=$S/b1; rm -rf $B; mkdir -p $B; : > $S/new/ran.txt
p=$(start new $B); mine+=($p)
job $B a; sleep 0.5; grep -q "$B/20260927-a" $S/new/ran.txt && ok "T1 job ran" || bad "T1 job not run"
F8_SHARD_BASE=$B "$S/new/shard-daemon.sh" < /dev/null > /dev/null 2>&1; rc=$?
[ $rc = 0 ] && [ "$(cat $B/daemon.pid)" = "$p" ] && ok "T2 second instance exits 0, pid file kept" || bad "T2 rc=$rc pid=$(cat $B/daemon.pid)"
sleep 4.5; alive $p && ok "T3 still alive after 4 checks with lock intact" || bad "T3 exited falsely"
job $B b; sleep 0.5; grep -q "$B/20260927-b" $S/new/ran.txt && ok "T3b job after timeouts ran" || bad "T3b job not run"

# T4 wipe alone -> exits within CHECK+1
wipe $B; t0=$(date +%s.%N); while alive $p; do sleep 0.1; [ $(echo "$(date +%s.%N) - $t0 > 3" | bc) = 1 ] && break; done
alive $p && bad "T4 still alive 3 s after wipe" || ok "T4 exited $(echo "$(date +%s.%N) - $t0" | bc | cut -c1-4) s after wipe"

# T5 wipe + immediate restart (the real f8desk sequence): old exits, new one serves jobs
B=$S/b5; rm -rf $B; mkdir -p $B; : > $S/new/ran.txt
p1=$(start new $B); mine+=($p1); wipe $B; p2=$(start new $B); mine+=($p2); sleep 2.5
{ ! alive $p1; } && alive $p2 && ok "T5 old $p1 gone, new $p2 alive" || bad "T5 p1 alive=$(alive $p1 && echo y) p2 alive=$(alive $p2 && echo y)"
job $B c; sleep 0.5; grep -q "$B/20260927-c" $S/new/ran.txt && ok "T5b new daemon serves jobs" || bad "T5b job not run"

# T6 only the lock file replaced (dir and FIFO kept) -> exits
rm -f $B/daemon.lock; : > $B/daemon.lock; sleep 2.5
alive $p2 && bad "T6 alive after lock replaced" || ok "T6 exited after lock file replaced"

# cleanup: only my test daemons
for q in "${mine[@]}"; do alive $q && { kill $q; echo "cleanup killed test daemon $q"; }; done
sleep 0.3; for q in "${mine[@]}"; do alive $q && bad "cleanup $q still alive"; done
[ $fail = 0 ] && echo DAEMON_FIX3_TEST_PASS || echo DAEMON_FIX3_TEST_FAIL
