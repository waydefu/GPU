#!/usr/bin/env bash
# Exactly one corrected-artifact R5 on installed 37d8393. Does not overwrite
# runtime-d9b7f60/r5-ahb-cycles/ or r5-ahb-cycles-rerun1/. No R6.
# Usage: SERIAL=HOST:PORT CELL=.../runtime-37d8393/r5-ahb-cycles bash run-r5-corrected.sh
# Silent logcat default + 45s stall / 300s max watchdog.
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
EXPECT_FIXTURE_SHA256=ba3a92d6c97cdce0ad8ca53feb544ff060f4b3f54a12be75969b76cdb319c828
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"
case "$CELL" in
  */runtime-37d8393/r5-ahb-cycles) ;;
  *) echo "REFUSE CELL must be .../runtime-37d8393/r5-ahb-cycles got=$CELL"; exit 9;;
esac
case "$CELL" in
  *runtime-d9b7f60*) echo "REFUSE will not write d9b7f60 R5 cells"; exit 9;;
esac
mkdir -p "$CELL"
if [ -f "$CELL/r5-fixture.out" ]; then
  echo "REFUSE CELL already has r5-fixture.out"
  exit 9
fi
test -x "$FIX/p_r5_ahb_cycles"
FIX_SHA=$(sha256sum "$FIX/p_r5_ahb_cycles" | awk '{print $1}')
test "$FIX_SHA" = "$EXPECT_FIXTURE_SHA256"
ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'versionName=|lastUpdateTime=' | head -4 | tee "$CELL/installed-package-pre-r5.txt"
grep -q 'versionName=1.03.01-37d8393-15.09.26' "$CELL/installed-package-pre-r5.txt"

start_logcat() {
  local out=$1 since=$2
  (
    exec env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
      HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
      "$TADB" -H 127.0.0.1 -P 5038 -s "$SERIAL" logcat -v threadtime -T "$since" \
      gatea-telemetry:V gatea-a1:V LorieNative:I '*:S' \
      > "$out" 2>&1
  ) &
  echo $!
}

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
echo "x3_pid=$X3 proto=1 telemetry=1 logcat=silent-default watchdog_stall=45s watchdog_max=300s" | tee "$CELL/x3-pid.txt"
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

: > "$CELL/r5-fixture.out"
set +e
"$FIX/p_r5_ahb_cycles" >> "$CELL/r5-fixture.out" 2>&1 &
FIXPID=$!
echo "$FIXPID" > "$CELL/fixture.pid"
stall=0
last_sz=-1
elapsed=0
WATCHDOG_STALL=45
WATCHDOG_MAX=300
while kill -0 "$FIXPID" 2>/dev/null; do
  sz=$(wc -c < "$CELL/r5-fixture.out" | tr -d ' ')
  if grep -q 'RESULT p_r5_ahb_cycles' "$CELL/r5-fixture.out" 2>/dev/null; then
    break
  fi
  if [ "$sz" -eq "$last_sz" ]; then
    stall=$((stall + 1))
  else
    stall=0
    last_sz=$sz
    tail -1 "$CELL/r5-fixture.out" || true
  fi
  if [ "$stall" -ge "$WATCHDOG_STALL" ]; then
    {
      echo "WATCHDOG_STALL_S=$WATCHDOG_STALL fixture_pid=$FIXPID x3=$X3"
      echo "x_wchan=$(cat /proc/$X3/wchan 2>/dev/null || echo gone)"
      echo "x_state=$(awk '/^State:/{print}' /proc/$X3/status 2>/dev/null || true)"
      echo "fix_wchan=$(cat /proc/$FIXPID/wchan 2>/dev/null || echo gone)"
      echo "last_fixture=$(tail -3 "$CELL/r5-fixture.out" | tr '\n' ' | ')"
    } | tee "$CELL/watchdog.txt"
    kill -TERM "$FIXPID" 2>/dev/null || true
    sleep 1
    kill -KILL "$FIXPID" 2>/dev/null || true
    break
  fi
  if [ "$elapsed" -ge "$WATCHDOG_MAX" ]; then
    echo "WATCHDOG_MAX_S=$WATCHDOG_MAX" | tee "$CELL/watchdog.txt"
    kill -TERM "$FIXPID" 2>/dev/null || true
    sleep 1
    kill -KILL "$FIXPID" 2>/dev/null || true
    break
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
wait "$FIXPID" 2>/dev/null
FIX_RC=$?
set -e
echo "FIXTURE_EXIT=$FIX_RC" | tee "$CELL/fixture-exit.txt"
cat "$CELL/r5-fixture.out"
sleep 2
if [ -d "/proc/$X3" ]; then
  echo "X3_STILL_ALIVE pid=$X3" | tee -a "$CELL/alive.txt"
else
  echo "X3_DIED_AFTER_FIXTURE" | tee -a "$CELL/alive.txt"
fi

{
  echo -n 'GATEA_EVENT_COUNT='
  grep -ac GATEA_EVENT "$CELL/logcat-follow.txt" || echo 0
  echo '===fatal==='
  grep -aE 'GATEA_FATAL_HALT|Fatal signal|SIGSEGV|SIGILL|x-ready-timeout' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===BIND==='
  grep -a 'GATEA_BIND' "$CELL/logcat-follow.txt" | head -5 || echo NONE
  echo '===last5 GATEA==='
  grep -a GATEA_EVENT "$CELL/logcat-follow.txt" | tail -5 || echo NONE
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
import re, sys
from pathlib import Path
from collections import Counter
cell=Path(sys.argv[1])
fix_rc=int(sys.argv[2])
out=(cell/'r5-fixture.out').read_text(errors='replace') if (cell/'r5-fixture.out').exists() else ''
follow=(cell/'logcat-follow.txt').read_bytes().decode('utf-8', errors='replace')
c=Counter(); pubs=[]; last=None
pat=re.compile(r'GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) serial=(\d+) src=(\d+) dst=(\d+)')
for m in pat.finditer(follow):
    t=tuple(int(x) for x in m.groups())
    last=t
    c[t[2]]+=1
    if t[2]==6:
        pubs.append((t[4], t[5], t[6]))
n=c[6]
serials=[p[0] for p in pubs]
summary='\n'.join([
    f'fixture_rc={fix_rc}',
    f'event_lines={sum(c.values())}',
    f'N_publish={n}',
    f'consume={c[7]} lookup={c[8]} draw={c[10]} fence={c[11]}',
    f'completed={c[14]} success={c[17]} ack={c[21]} lease_release={c[23]} repair={c[20]} relock_dst={c[19]}',
    f'firstFailed={c[15]} genFatal={c[16]} lookup_fail={c[9]} fence_timeout={c[12]} fence_error={c[13]}',
    f'unique_publish_serials={len(set(serials))}',
    f'pair_unique={len(set((s,d) for _,s,d in pubs)) if pubs else 0}',
    f'last={last}',
    f'counts={dict(sorted(c.items()))}',
])+'\n'
(cell/'gatea-event-counts.txt').write_text(summary)
print(summary, end='')
passed = (
    fix_rc == 0
    and 'RESULT p_r5_ahb_cycles PASS' in out
    and all(f'CHECKPOINT n={cp} fail_acc=0' in out for cp in (1, 16, 64, 256, 1024, 4096))
    and n == 4096
    and c[7]==n and c[8]==n and c[10]==n and c[11]==n and c[14]==n and c[17]==n and c[21]==n and c[23]==n
    and c[15]==0 and c[16]==0 and c[9]==0 and c[12]==0 and c[13]==0
    and len(set(serials))==n and serials==sorted(serials) and n>0
    and all(serials[i] < serials[i+1] for i in range(n-1))
    and len(set((s,d) for _,s,d in pubs))==1
    and 'GATEA_FATAL_HALT' not in follow and 'x-ready-timeout' not in follow
)
if passed:
    print('R5_EVENT_COUNTERS_OK N', n)
    print('R5_AHB_CYCLES_CORRECTED_PASS')
    raise SystemExit(0)
print('R5_AHB_CYCLES_CORRECTED_FAIL')
raise SystemExit(2)
PY
echo R5_AHB_CYCLES_CORRECTED_PASS
