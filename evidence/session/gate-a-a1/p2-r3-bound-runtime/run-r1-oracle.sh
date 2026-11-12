#!/usr/bin/env bash
# R1 OFF oracle+stress on 98b0011. Experimental :3 only.
set -euo pipefail
TADB=/data/data/com.termux/files/usr/bin/adb
S=10.193.235.219:35301
EVID=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-bound-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
ADB() {
  env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
    HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
    "$TADB" -H 127.0.0.1 -P 5038 -s "$S" "$@"
}
x3pid() {
  for p in /proc/[0-9]*; do
    x=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$x" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) echo "${p##*/}"; return 0;;
    esac
  done
  return 1
}

run_oracle() {
  local NAME="$1" MODE="$2"
  local CELL="$EVID/$NAME"
  mkdir -p "$CELL"
  echo "===== $NAME mode=$MODE ====="
  ADB shell dumpsys power | grep mWakefulness= | head -1 | tee "$CELL/screen.txt"
  ADB shell dumpsys window | grep isKeyguardShowing= | head -1 >> "$CELL/screen.txt"
  grep -q 'mWakefulness=Awake' "$CELL/screen.txt"
  grep -q 'isKeyguardShowing=false' "$CELL/screen.txt"

  rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
    /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock /tmp/x11gpu-p2a3.snap || true

  SINCE=$(ADB shell "date '+%m-%d %H:%M:%S.000'" | tr -d '\r')
  echo "logcat_since=$SINCE" | tee "$CELL/logcat-since.txt"
  # Include gatea-a1 (FATAL_HALT). Do not use a silent *:S-only filter that drops it.
  ADB logcat -v threadtime -T "$SINCE" \
    gatea-telemetry:I gatea-a1:V DEBUG:I libc:F Xlorie:I LorieNative:I gles-renderer:I \
    > "$CELL/logcat-follow.txt" 2>&1 &
  echo $! > "$CELL/logcat.pid"
  sleep 0.5

  ADB shell am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity | tee "$CELL/am-start.out"
  export GATEA_X3_LAUNCHER_LOG="$CELL/x3-launcher.raw.log"
  : > "$GATEA_X3_LAUNCHER_LOG"
  unset TERMUX_X11_GATEA_PROTO || true
  if [ "$MODE" = proto0 ]; then export TERMUX_X11_GATEA_PROTO=0; fi
  export TERMUX_X11_GATEA_TELEMETRY=1
  python3 "$RUN" | tee "$CELL/start-x3.out"
  X3=""
  for i in $(seq 1 80); do
    if X3=$(x3pid); then echo "x3_pid=$X3" | tee "$CELL/x3-pid.txt"; break; fi
    sleep 0.25
  done
  test -n "$X3"
  for i in $(seq 1 40); do
    if [ -S /data/data/com.termux/files/usr/tmp/.X11-unix/X3 ] || [ -S /tmp/.X11-unix/X3 ]; then
      echo "socket_ready i=$i"; break
    fi
    sleep 0.25
  done
  sleep 2
  if [ ! -d "/proc/$X3" ]; then
    echo "DIED_BEFORE_HOLDER pid=$X3" | tee "$CELL/alive.txt"
    ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
    return 2
  fi
  echo "ALIVE_BEFORE_ORACLE pid=$X3" | tee "$CELL/alive.txt"
  export DISPLAY=:3
  export TMPDIR=/data/data/com.termux/files/usr/tmp
  "$FIX/p_b3a_hold" > "$CELL/holder.out" 2>&1 &
  echo $! > "$CELL/holder.pid"
  sleep 0.5
  kill -0 "$(cat "$CELL/holder.pid")"
  echo '===ORACLE==='
  set +e
  "$FIX/p-b2-oracle" | tee "$CELL/oracle.out"
  ORC=${PIPESTATUS[0]}
  set -e
  echo "oracle_exit=$ORC"
  if [ "$ORC" -ne 0 ]; then
    ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
  fi
  echo '===x100==='
  "$FIX/p_b2_stress" 100 | tee "$CELL/x100.out"
  echo '===mixed100==='
  "$FIX/p_b2_stress" 100 1 | tee "$CELL/mixed100.out"
  echo '===x1000==='
  "$FIX/p_b2_stress" 1000 | tee "$CELL/x1000.out"
  if [ -d "/proc/$X3" ]; then echo "X3_ALIVE=yes pid=$X3" | tee -a "$CELL/alive.txt"
  else echo "X3_ALIVE=no pid=$X3" | tee -a "$CELL/alive.txt"; fi
  grep -E 'fail=0|RESULT|STRESS' "$CELL/oracle.out" "$CELL/x100.out" "$CELL/mixed100.out" "$CELL/x1000.out" || true

  {
    echo '===GATEA_EVENT==='
    grep -c GATEA_EVENT "$CELL/logcat-follow.txt" || echo 0
    grep GATEA_EVENT "$CELL/logcat-follow.txt" || echo NONE
    echo '===fatal==='
    grep -E 'GATEA_FATAL_HALT|Fatal signal|SIGSEGV|SIGILL' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  } | tee "$CELL/telemetry-fatal-pre-teardown.txt"

  kill "$(cat "$CELL/logcat.pid")" 2>/dev/null || true
  HPID=$(cat "$CELL/holder.pid")
  kill "$HPID" 2>/dev/null || true
  wait "$HPID" 2>/dev/null || true
  if [ -d "/proc/$X3" ]; then
    cmd=$(tr '\0' ' ' < /proc/$X3/cmdline || true)
    case "$cmd" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) kill "$X3"; echo "killed $X3";;
      *) echo "REFUSE_KILL $X3 cmd=$cmd";;
    esac
  fi
  sleep 1
  ADB shell am force-stop com.waydefu.x11gpu >/dev/null
  sleep 1
  rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
    /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock || true
  {
    echo "===residue==="
    found=0
    for p in /proc/[0-9]*; do
      x=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
      case "$x" in
        "termux-x11gpu com.waydefu.x11gpu :3"*) echo "RESIDUE ${p##*/}"; found=1;;
        "termux-x11 com.termux.x11 :1"*) echo "STABLE ${p##*/}";;
      esac
    done
    [ "$found" = 0 ] && echo NO_X3_RESIDUE
  } | tee "$CELL/teardown.txt"
  grep -q NO_X3_RESIDUE "$CELL/teardown.txt"
  grep -q 'STABLE 16085' "$CELL/teardown.txt"
  grep -q 'RESULT p-b2-oracle PASS fail=0' "$CELL/oracle.out"
  grep -q 'X3_ALIVE=yes' "$CELL/alive.txt"
  python3 - "$CELL" <<'PY'
import sys, re
from pathlib import Path
cell=Path(sys.argv[1])
tele=(cell/'telemetry-fatal-pre-teardown.txt').read_text(errors='replace')
# GATEA_EVENT count must be 0 for R1 OFF
m=re.search(r'===GATEA_EVENT===\n(\d+)', tele)
count=int(m.group(1)) if m else -1
assert count==0, tele[:2000]
assert 'GATEA_FATAL_HALT' not in tele
print('R1_OFF_TELEMETRY_OK count', count)
PY
  echo "$NAME PASS"
}

run_oracle r1-unset-oracle unset
run_oracle r1-proto0-oracle proto0
echo R1_OFF_ORACLE_STRESS_DONE
