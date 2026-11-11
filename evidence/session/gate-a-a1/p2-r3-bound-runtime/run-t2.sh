#!/usr/bin/env bash
# T2 startup 6/6 on 98b0011. Experimental :3 only. Never Stable :1.
set -euo pipefail
TADB=/data/data/com.termux/files/usr/bin/adb
S=10.193.235.219:35301
EVID=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-bound-runtime
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
teardown_cell() {
  local CELL="$1"
  local X3=""
  if [ -f "$CELL/x3-pid.txt" ]; then
    X3=$(awk -F= '/x3_pid=/{print $2}' "$CELL/x3-pid.txt" | awk '{print $1}')
  fi
  if [ -n "${X3:-}" ] && [ -d "/proc/$X3" ]; then
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
}

run_cell() {
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
  ADB shell am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity | tee "$CELL/am-start.out"
  ADB shell dumpsys activity activities > "$CELL/dumpsys-activity.txt"
  python3 - "$CELL" <<'PY'
import sys
from pathlib import Path
cell=Path(sys.argv[1])
t=(cell/'dumpsys-activity.txt').read_text(errors='replace')
d0=t.split('Display #0',1)[-1][:4000]
assert 'com.waydefu.x11gpu' in d0
assert 'state=RESUMED' in t and 'reportedDrawn=true' in t
print('ACTIVITY_DISPLAY0_OK')
PY
  export GATEA_X3_LAUNCHER_LOG="$CELL/x3-launcher.raw.log"
  : > "$GATEA_X3_LAUNCHER_LOG"
  unset TERMUX_X11_GATEA_PROTO || true
  if [ "$MODE" = proto0 ]; then export TERMUX_X11_GATEA_PROTO=0; fi
  export TERMUX_X11_GATEA_TELEMETRY=1
  python3 "$RUN" | tee "$CELL/start-x3.out"
  X3=""
  for i in $(seq 1 80); do
    if X3=$(x3pid); then echo "x3_pid=$X3 iter=$i" | tee "$CELL/x3-pid.txt"; break; fi
    sleep 0.25
  done
  if [ -z "${X3:-}" ]; then echo NO_X3_PID | tee "$CELL/x3-pid.txt"; echo FAIL_NO_PID; return 1; fi
  sleep 8
  if [ -d "/proc/$X3" ]; then echo "ALIVE_AFTER_8S pid=$X3" | tee "$CELL/alive.txt"
  else echo "DIED_WITHIN_8S pid=$X3" | tee "$CELL/alive.txt"; fi
  cp -a /tmp/x11gpu-p2a3.snap "$CELL/p2a3.snap" 2>/dev/null || true
  grep -E 'Uctx |Upid |Uraw |Ssig |Fatal signal' "$CELL/x3-launcher.raw.log" "$CELL/p2a3.snap" 2>/dev/null | tee "$CELL/crash-markers.txt" || true
  if grep -q 'DIED_WITHIN_8S' "$CELL/alive.txt" || grep -q 'Uctx ' "$CELL/crash-markers.txt" 2>/dev/null; then
    echo "$NAME CRASH_OR_DEATH"
    teardown_cell "$CELL"
    return 2
  fi
  teardown_cell "$CELL"
  echo "$NAME PASS"
}

run_cell t2-A1-unset unset
run_cell t2-B1-proto0 proto0
run_cell t2-A2-unset unset
run_cell t2-B2-proto0 proto0
run_cell t2-A3-unset unset
run_cell t2-B3-proto0 proto0
echo T2_MATRIX_6_6_DONE
