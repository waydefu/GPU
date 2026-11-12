#!/usr/bin/env bash
# Exactly one R3 p_r3_single_direct on installed d9b7f60. Experimental :3 only.
# Usage: SERIAL=HOST:PORT CELL=... bash run-r3.sh
# Never rerun R3 on 88e3f17 / 8479997 / 6c7ee6f / 98b0011.
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
"$FIX/p_r3_single_direct" | tee "$CELL/r3-fixture.out"
FIX_RC=${PIPESTATUS[0]}
set -e
echo "FIXTURE_EXIT=$FIX_RC" | tee "$CELL/fixture-exit.txt"
sleep 2
if [ -d "/proc/$X3" ]; then
  echo "X3_STILL_ALIVE pid=$X3" | tee -a "$CELL/alive.txt"
else
  echo "X3_DIED_AFTER_FIXTURE" | tee -a "$CELL/alive.txt"
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
fi
if [ "$FIX_RC" -ne 0 ]; then
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
fi

{
  echo '===GATEA_EVENT==='
  grep -a GATEA_EVENT "$CELL/logcat-follow.txt" || echo NONE
  echo -n 'count='
  grep -ac GATEA_EVENT "$CELL/logcat-follow.txt" || echo 0
  echo '===fatal==='
  grep -aE 'GATEA_FATAL_HALT|Fatal signal|SIGSEGV|SIGILL' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===BIND_PEEK_HANDLE_DRAIN==='
  grep -aE 'GATEA_BIND|GATEA_PEEK|GATEA_HANDLE|GATEA_DRAIN|r-unbound-frame|VALIDATE_TERMINAL|READY_SEND|x-ready-timeout|x-pump-' "$CELL/logcat-follow.txt" || echo NONE
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

python3 - "$CELL" "$FIX_RC" <<'PY'
import sys, re
from pathlib import Path
cell=Path(sys.argv[1])
fix_rc=int(sys.argv[2])
out=(cell/'r3-fixture.out').read_text(errors='replace')
tele=(cell/'telemetry-fatal-pre-teardown.txt').read_text(errors='replace')
alive=(cell/'alive.txt').read_text(errors='replace')
dump=cell/'logcat-dump-unfiltered.txt'
blob=tele
if dump.exists():
    blob += '\n' + dump.read_text(errors='replace')
follow=(cell/'logcat-follow.txt').read_bytes().decode('utf-8', errors='replace')
events=[]
for m in re.finditer(r'GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) serial=(\d+) src=(\d+) dst=(\d+)', follow + '\n' + blob):
    events.append(tuple(int(x) for x in m.groups()))
(cell/'gatea-events.txt').write_text('\n'.join(
    f'seq={s} role={r} event={e} generation={g} serial={n} src={src} dst={dst}'
    for s,r,e,g,n,src,dst in events) + ('\n' if events else 'NONE\n'))
print('event_count', len(events))
print('fixture_rc', fix_rc)
print('fatal_halt', 'GATEA_FATAL_HALT' in follow or 'GATEA_FATAL_HALT' in blob)
print('x3_alive_after', 'X3_STILL_ALIVE' in alive)
if fix_rc != 0 or 'GATEA_FATAL_HALT' in follow or 'GATEA_FATAL_HALT' in blob or 'X3_STILL_ALIVE' not in alive:
    print('R3_FAIL')
    print(out[-2000:])
    for line in follow.splitlines():
        if 'GATEA_FATAL' in line or 'GATEA_EVENT' in line or 'VALIDATE_TERMINAL' in line or 'x-ready-timeout' in line or 'x-pump-' in line:
            print(line)
    raise SystemExit(2)
need=[1,1,2,3,4,5,6,7,8,10,11,17,18,19,20,21]
got=[e for _,_,e,_,_,_,_ in events]
i=0
for n in need:
    while i < len(got) and got[i] != n:
        i += 1
    if i >= len(got):
        print('ORDER_FAIL need', need, 'got', got)
        raise SystemExit(3)
    i += 1
assert 'RESULT p_r3_single_direct PASS' in out
assert 'PASS pixels exact_px=64 maxΔ=0' in out
print('R3_EVENT_ORDER_OK', got)
print('R3_SINGLE_DIRECT_PASS')
PY
echo R3_SINGLE_DIRECT_PASS
