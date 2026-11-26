#!/data/data/com.termux/files/usr/bin/bash
# Test daemon recovery after a tmp wipe using disposable old/new fixtures.
set -euo pipefail
fixture=$(cd -- "${1:?fixture directory required}" && pwd -P)
export PATH=/data/data/com.termux/files/usr/bin:$PATH
export F8_SHARD_DAEMON_CHECK_S=1

for version in old new; do
  script="$fixture/$version/shard-daemon.sh"
  if [[ ! -x "$script" ]] || ! grep -Eq '^BASE=.*F8_SHARD_BASE' "$script"; then
    echo "FAIL $version daemon fixture must accept an isolated F8_SHARD_BASE" >&2
    exit 2
  fi
done

run=$(mktemp -d -- "$fixture/wipe.XXXXXXXX")
declare -A daemons=()
fail=0
started=
ok() { echo "PASS $*"; }
bad() { echo "FAIL $*"; fail=1; }

alive() {
  local pid=$1
  [[ -r /proc/$pid/cmdline ]] && grep -Fxzq -- "${daemons[$pid]}" "/proc/$pid/cmdline" 2>/dev/null
}

wait_for_exit() {
  local pid=$1 i
  for ((i=0; i<35; i++)); do
    if ! kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
    sleep 0.1
  done
  return 1
}

finish() {
  local result=$? pid
  trap - EXIT INT TERM
  for pid in "${!daemons[@]}"; do
    if alive "$pid"; then
      if ! kill "$pid" && alive "$pid"; then
        bad "cleanup could not stop daemon $pid"
      fi
    fi
    if ! wait_for_exit "$pid"; then
      bad "cleanup daemon $pid still alive"
    fi
  done
  if (( result == 0 && fail == 0 )); then
    echo DAEMON_FIX3_TEST_PASS
    exit 0
  fi
  echo DAEMON_FIX3_TEST_FAIL
  (( result != 0 )) || result=1
  exit "$result"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

start() {
  local script="$fixture/$1/shard-daemon.sh" state=$2 i
  F8_SHARD_BASE="$state" "$script" </dev/null >>"$run/daemon.log" 2>&1 &
  started=$!
  daemons[$started]=$script
  for ((i=0; i<50; i++)); do
    if [[ -s "$state/daemon.pid" && -p "$state/ctl.fifo" ]] &&
       [[ $(<"$state/daemon.pid") == "$started" ]] && alive "$started"; then
      return 0
    fi
    kill -0 "$started" 2>/dev/null || break
    sleep 0.1
  done
  bad "$1 fixture daemon not ready: $state"
  return 1
}

job() {
  local state=$1 name=$2 label=$3 dir="$1/20260927-$2" i
  mkdir -- "$dir"
  if timeout 4 "$BASH" -c 'printf "%s\n" "$1" > "$2"' _ "$dir" "$state/ctl.fifo"; then
    for ((i=0; i<20; i++)); do
      if grep -Fxq -- "$dir" "$fixture/new/ran.txt"; then
        ok "$label job $name ran"
        return 0
      fi
      sleep 0.1
    done
  fi
  bad "$label job $name not run"
}

wipe() { find "$1" -mindepth 1 -delete; }

B=$run/b0
start old "$B"; p1=$started
wipe "$B"
start old "$B"; p2=$started
if alive "$p1" && alive "$p2" && [[ $p1 != "$p2" ]]; then
  ok "T0 control reproduced two old daemons"
else
  bad "T0 control did not reproduce"
fi

B=$run/b1
: > "$fixture/new/ran.txt"
start new "$B"; p=$started
job "$B" a T1
if F8_SHARD_BASE="$B" timeout 4 "$fixture/new/shard-daemon.sh" </dev/null >>"$run/daemon.log" 2>&1 &&
   [[ -s "$B/daemon.pid" && $(<"$B/daemon.pid") == "$p" ]] && alive "$p"; then
  ok "T2 second instance exited and kept the existing daemon"
else
  bad "T2 singleton"
fi
sleep 4.5
alive "$p" && ok "T3 daemon survived four checks" || bad "T3 daemon exited prematurely"
job "$B" b T3b
wipe "$B"
wait_for_exit "$p" && ok "T4 daemon exited after wipe" || bad "T4 daemon survived wipe"

B=$run/b5
start new "$B"; p1=$started
wipe "$B"
start new "$B"; p2=$started
if wait_for_exit "$p1" && alive "$p2"; then
  ok "T5 old daemon exited and new daemon is alive"
else
  bad "T5 restart"
fi
job "$B" c T5b
unlink "$B/daemon.lock"
: > "$B/daemon.lock"
wait_for_exit "$p2" && ok "T6 daemon exited after lock replacement" || bad "T6 daemon survived lock replacement"
