#!/usr/bin/env bash
# R1 OFF oracle+stress on d9b7f60. Experimental :3 only.
# Usage: SERIAL=HOST:PORT CELL=... MODE=unset|proto0 bash run-r1-off.sh
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"
: "${MODE:?unset or proto0}"
mkdir -p "$CELL"

ADB shell dumpsys power | grep mWakefulness= | head -1 | tee "$CELL/screen.txt"
ADB shell dumpsys window | grep isKeyguardShowing= | head -1 >> "$CELL/screen.txt"
grep -q 'mWakefulness=Awake' "$CELL/screen.txt"
grep -q 'isKeyguardShowing=false' "$CELL/screen.txt"

STABLE_PRE=$(stabpid)
STABLE_CMD_PRE=$(stab_cmd)
echo "stable_pre_pid=$STABLE_PRE" | tee "$CELL/stable-pre.txt"
echo "stable_pre_cmd=$STABLE_CMD_PRE" | tee -a "$CELL/stable-pre.txt"
test -n "$STABLE_PRE"
echo "$STABLE_CMD_PRE" | grep -q '^termux-x11 com.termux.x11 :1'

rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
  /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock /tmp/x11gpu-p2a3.snap || true

ADB shell am force-stop com.waydefu.x11gpu
sleep 1
ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' | tee "$CELL/am-start.out"
ADB shell dumpsys activity activities > "$CELL/dumpsys-activity.txt"
assert_display0 "$CELL/dumpsys-activity.txt"

SINCE=$(ADB shell "date '+%m-%d %H:%M:%S.000'" | tr -d '\r')
echo "logcat_since=$SINCE" | tee "$CELL/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$CELL/logcat-follow.txt" "$SINCE")
echo "$LOGCAT_PID" > "$CELL/logcat.pid"
# exec() in the logcat helper can still look like bash for one scheduler
# slice; wait until the pid is the native adb binary before verifying.
for i in $(seq 1 20); do
  exe=$(readlink "/proc/$LOGCAT_PID/exe" 2>/dev/null || true)
  [ "$exe" = "$TADB" ] && break
  sleep 0.1
done
verify_logcat_pid "$LOGCAT_PID"
sleep 1

export GATEA_X3_LAUNCHER_LOG="$CELL/x3-launcher.raw.log"
: > "$GATEA_X3_LAUNCHER_LOG"
unset TERMUX_X11_GATEA_PROTO || true
unset TERMUX_X11_GATEA_TELEMETRY || true
unset TERMUX_X11_DEBUG || true
if [ "$MODE" = proto0 ]; then
  export TERMUX_X11_GATEA_PROTO=0
  export TERMUX_X11_GATEA_TELEMETRY=1
fi
python3 "$RUN" | tee "$CELL/start-x3.out"
X3=""
for i in $(seq 1 40); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
echo "x3_pid=$X3 mode=$MODE" | tee "$CELL/x3-pid.txt"
save_x_identity "$X3" "$CELL"
for i in $(seq 1 40); do
  if [ -S /data/data/com.termux/files/usr/tmp/.X11-unix/X3 ] || [ -S /tmp/.X11-unix/X3 ]; then
    echo "socket_ready i=$i"
    break
  fi
  sleep 0.25
done
sleep 2
if [ ! -d "/proc/$X3" ]; then
  echo "DIED_BEFORE_HOLDER pid=$X3" | tee "$CELL/alive.txt"
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
  exit 2
fi
echo "ALIVE_BEFORE_ORACLE pid=$X3" | tee "$CELL/alive.txt"

export DISPLAY=:3
export TMPDIR=/data/data/com.termux/files/usr/tmp
"$FIX/p_b3a_hold" > "$CELL/holder.out" 2>&1 &
HOLDER_PID=$!
echo "$HOLDER_PID" > "$CELL/holder.pid"
for i in $(seq 1 20); do
  grep -q 'HOLD READY' "$CELL/holder.out" 2>/dev/null && break
  sleep 0.2
done
grep -q 'HOLD READY' "$CELL/holder.out"

set +e
"$FIX/p-b2-oracle" | tee "$CELL/oracle.out"
ORACLE_RC=${PIPESTATUS[0]}
set -e
echo "FIXTURE_EXIT=$ORACLE_RC" | tee "$CELL/fixture-exit.txt"
"$FIX/p_b2_stress" 100 | tee "$CELL/x100.out"
"$FIX/p_b2_stress" 100 1 | tee "$CELL/mixed100.out"
"$FIX/p_b2_stress" 1000 | tee "$CELL/x1000.out"
if [ -d "/proc/$X3" ]; then echo "X3_ALIVE=yes pid=$X3" | tee -a "$CELL/alive.txt"
else echo "X3_ALIVE=no pid=$X3" | tee -a "$CELL/alive.txt"; fi

{
  echo '===GATEA_EVENT==='
  grep -c GATEA_EVENT "$CELL/logcat-follow.txt" || echo 0
  grep GATEA_EVENT "$CELL/logcat-follow.txt" || echo NONE
  echo '===fatal==='
  grep -E 'GATEA_FATAL_HALT|Fatal signal|SIGSEGV|SIGILL' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
} | tee "$CELL/telemetry-fatal-pre-teardown.txt"

test "$(stabpid)" = "$STABLE_PRE"
test "$(stab_cmd)" = "$STABLE_CMD_PRE"

stop_logcat "$LOGCAT_PID" || true
LOGCAT_PID=""
kill -TERM "$HOLDER_PID" 2>/dev/null || true
wait "$HOLDER_PID" 2>/dev/null || true
HOLDER_PID=""
if [ -d "/proc/$X3" ]; then
  cmd=$(tr '\0' ' ' < /proc/$X3/cmdline || true)
  case "$cmd" in
    "termux-x11gpu com.waydefu.x11gpu :3"*) kill "$X3"; echo "killed $X3";;
    *) echo "REFUSE_KILL $X3 cmd=$cmd"; exit 3;;
  esac
fi
sleep 1
ADB shell am force-stop com.waydefu.x11gpu >/dev/null
sleep 1
rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
  /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock || true
{
  echo "===process residue only==="
  echo "STABLE $(stabpid)"
  if x3pid >/dev/null; then echo RESIDUE; else echo NO_X3_RESIDUE; fi
} | tee "$CELL/teardown.txt"
grep -q NO_X3_RESIDUE "$CELL/teardown.txt"
grep -q "STABLE $STABLE_PRE" "$CELL/teardown.txt"
test "$ORACLE_RC" -eq 0
grep -q 'X3_ALIVE=yes' "$CELL/alive.txt"
python3 - "$CELL" <<'PY'
import sys, re
from pathlib import Path
cell=Path(sys.argv[1])
tele=(cell/'telemetry-fatal-pre-teardown.txt').read_text(errors='replace')
m=re.search(r'===GATEA_EVENT===\n(\d+)', tele)
count=int(m.group(1)) if m else -1
assert count==0, tele[:2000]
assert 'GATEA_FATAL_HALT' not in tele
print('R1_OFF_TELEMETRY_OK count', count)
PY
echo "R1 $MODE PASS"
