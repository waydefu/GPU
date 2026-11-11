#!/usr/bin/env bash
# Exactly one R4 1514 production-path oracle on installed d9b7f60. Experimental :3 only.
# Usage: SERIAL=HOST:PORT CELL=... bash run-r4.sh
# Requires prior R3 PASS on this APK. Do not start R5 from this script.
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"
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
for i in $(seq 1 20); do
  if ! ADB shell 'ps -A' | grep -q 'com.waydefu.x11gpu'; then
    echo "waydefu_gone i=$i"
    break
  fi
  sleep 0.3
done
sleep 1
ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' | tee "$CELL/am-start.out"
ADB shell dumpsys activity activities > "$CELL/dumpsys-activity.txt"
assert_display0 "$CELL/dumpsys-activity.txt"

SINCE=$(ADB shell "date '+%m-%d %H:%M:%S.000'" | tr -d '\r')
echo "logcat_since=$SINCE" | tee "$CELL/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$CELL/logcat-follow.txt" "$SINCE")
echo "$LOGCAT_PID" > "$CELL/logcat.pid"
for i in $(seq 1 20); do
  exe=$(readlink "/proc/$LOGCAT_PID/exe" 2>/dev/null || true)
  [ "$exe" = "$TADB" ] && break
  sleep 0.1
done
verify_logcat_pid "$LOGCAT_PID"
sleep 1

export GATEA_X3_LAUNCHER_LOG="$CELL/x3-launcher.raw.log"
: > "$GATEA_X3_LAUNCHER_LOG"
export TERMUX_X11_GATEA_PROTO=1
export TERMUX_X11_GATEA_TELEMETRY=1
unset TERMUX_X11_DEBUG || true
python3 "$RUN" | tee "$CELL/start-x3.out"
X3=""
for i in $(seq 1 40); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
echo "x3_pid=$X3 proto=1 telemetry=1" | tee "$CELL/x3-pid.txt"
save_x_identity "$X3" "$CELL"
for i in $(seq 1 40); do
  if [ -S /data/data/com.termux/files/usr/tmp/.X11-unix/X3 ] || [ -S /tmp/.X11-unix/X3 ]; then
    echo "socket_ready i=$i"
    break
  fi
  sleep 0.25
done
sleep 8
if [ ! -d "/proc/$X3" ]; then
  echo "STOP x3 died during 8s pid=$X3" | tee "$CELL/STOP.txt"
  echo "DIED_DURING_8S pid=$X3" | tee "$CELL/alive.txt"
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
  exit 2
fi
echo "ALIVE_8S pid=$X3" | tee "$CELL/alive.txt"

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
sleep 2
if [ -d "/proc/$X3" ]; then
  echo "X3_STILL_ALIVE pid=$X3" | tee -a "$CELL/alive.txt"
else
  echo "X3_DIED_AFTER_FIXTURE" | tee -a "$CELL/alive.txt"
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
fi
if [ "$ORACLE_RC" -ne 0 ]; then
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
fi

{
  echo -n 'GATEA_EVENT_COUNT='
  grep -ac GATEA_EVENT "$CELL/logcat-follow.txt" || echo 0
  echo '===fatal==='
  grep -aE 'GATEA_FATAL_HALT|Fatal signal|SIGSEGV|SIGILL|x-ready-timeout' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===BIND==='
  grep -a 'GATEA_BIND' "$CELL/logcat-follow.txt" | head -5 || echo NONE
} | tee "$CELL/telemetry-fatal-pre-teardown.txt"

test "$(stabpid)" = "$STABLE_PRE"
test "$(stab_cmd)" = "$STABLE_CMD_PRE"

stop_logcat "$LOGCAT_PID" || true
if [ -n "$LOGCAT_PID" ] && [ -d "/proc/$LOGCAT_PID" ]; then
  if verify_logcat_pid "$LOGCAT_PID"; then
    kill -KILL "$LOGCAT_PID" 2>/dev/null || true
  fi
fi
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
grep -q 'X3_STILL_ALIVE' "$CELL/alive.txt"
test "$ORACLE_RC" -eq 0
grep -q 'RESULT p-b2-oracle PASS fail=0' "$CELL/oracle.out"

python3 - "$CELL" <<'PY'
import re, sys
from pathlib import Path
from collections import Counter
cell=Path(sys.argv[1])
out=(cell/'oracle.out').read_text(errors='replace')
assert 'RESULT p-b2-oracle PASS fail=0' in out
assert 'maxΔ=0' in out
follow=(cell/'logcat-follow.txt').read_bytes().decode('utf-8', errors='replace')
tele=(cell/'telemetry-fatal-pre-teardown.txt').read_text(errors='replace')
assert 'GATEA_FATAL_HALT' not in follow and 'GATEA_FATAL_HALT' not in tele
assert 'x-ready-timeout' not in follow
events=[]
for m in re.finditer(r'GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) serial=(\d+) src=(\d+) dst=(\d+)', follow):
    events.append(tuple(int(x) for x in m.groups()))
# 6 PUBLISH 7 CONSUME 8 LOOKUP 10 DRAW 11 FENCE 14 COMPLETED 17 SUCCESS 21 ACK
# 15 FIRST_FAILED 16 GENERATION_FATAL
c=Counter(e[2] for e in events)
n=c[6]
summary='\n'.join([
    f'event_lines={len(events)}',
    f'N_publish={n}',
    f'consume={c[7]} lookup={c[8]} draw={c[10]} fence={c[11]}',
    f'completed={c[14]} success={c[17]} ack={c[21]}',
    f'firstFailed={c[15]} genFatal={c[16]}',
    f'counts={dict(sorted(c.items()))}',
])+'\n'
(cell/'gatea-event-counts.txt').write_text(summary)
print(summary, end='')
if n < 1:
    print('R4_FAIL no direct PUBLISH')
    raise SystemExit(2)
if not (c[7]==n and c[8]==n and c[10]==n and c[11]==n and c[14]==n and c[17]==n and c[21]==n):
    print('R4_FAIL counter mismatch vs N', n)
    raise SystemExit(3)
if c[15] != 0 or c[16] != 0:
    print('R4_FAIL firstFailed/fatal')
    raise SystemExit(4)
print('R4_EVENT_COUNTERS_OK N', n)
print('R4_PRODUCTION_ORACLE_PASS')
PY
echo R4_PRODUCTION_ORACLE_PASS
