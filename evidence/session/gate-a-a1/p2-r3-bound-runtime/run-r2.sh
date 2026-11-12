#!/usr/bin/env bash
# R2 imported-AHB rejection on 98b0011. Experimental :3 only.
set -euo pipefail
TADB=/data/data/com.termux/files/usr/bin/adb
S=10.193.235.219:35301
EVID=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-bound-runtime
CELL=$EVID/r2-imported-reject
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
HDIR=/data/data/com.termux/files/home/r2-ahb-helper
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
mkdir -p "$CELL"
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
stabpid() {
  for p in /proc/[0-9]*; do
    x=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$x" in
      "termux-x11 com.termux.x11 :1"*) echo "${p##*/}"; return 0;;
    esac
  done
  return 1
}

{
  echo "serial=$S"
  echo "artifact=98b0011"
  echo "screen_pre:"
  ADB shell dumpsys power | grep mWakefulness= | head -1
  ADB shell dumpsys window | grep isKeyguardShowing | head -1
  echo "stable_pre=$(stabpid || echo MISSING)"
} | tee "$CELL/preflight.txt"
grep -q 'mWakefulness=Awake' "$CELL/preflight.txt"
grep -q 'isKeyguardShowing=false' "$CELL/preflight.txt"
STAB=$(stabpid || true)
if [ "$STAB" != 16085 ]; then
  echo "STOP stable pid changed: $STAB" | tee "$CELL/STOP.txt"
  exit 2
fi

ADB shell am force-stop com.waydefu.x11gpu
sleep 1
rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
  /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock
if x3pid >/dev/null; then
  echo "STOP x3 still present after force-stop" | tee "$CELL/STOP.txt"
  exit 2
fi

ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' | tee "$CELL/am-start.out"
ADB shell dumpsys activity activities | grep -E 'waydefu|displayId|mResumed' | head -40 > "$CELL/dumpsys-activity.txt" || true

SINCE=$(ADB shell "date '+%m-%d %H:%M:%S.000'" | tr -d '\r')
echo "logcat_since=$SINCE" | tee "$CELL/logcat-since.txt"
ADB logcat -v threadtime -T "$SINCE" \
  LorieNative:V gatea-telemetry:I gatea-a1:V DEBUG:I libc:F Xlorie:I \
  > "$CELL/logcat-follow.txt" 2>&1 &
echo $! > "$CELL/logcat.pid"
sleep 1

export GATEA_X3_LAUNCHER_LOG="$CELL/x3-launcher.raw.log"
: > "$GATEA_X3_LAUNCHER_LOG"
export TERMUX_X11_GATEA_PROTO=1
export TERMUX_X11_GATEA_TELEMETRY=1
# Presence-sensitive: enables lorieServerDebugEnabled DRI3 import log.
export TERMUX_X11_DEBUG=1
python3 "$RUN" | tee "$CELL/start-x3.out"

X3=""
for i in $(seq 1 20); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
if [ -z "$X3" ]; then
  echo "STOP no x3 pid" | tee "$CELL/STOP.txt"
  exit 2
fi
echo "x3_pid=$X3 proto=1 telemetry=1" | tee "$CELL/x3-pid.txt"
sleep 8
if ! kill -0 "$X3" 2>/dev/null; then
  echo "STOP x3 died during 8s alive" | tee "$CELL/STOP.txt"
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
  exit 2
fi
echo "ALIVE_8S pid=$X3" | tee "$CELL/alive.txt"

export DISPLAY=:3
export TMPDIR=/data/data/com.termux/files/usr/tmp
"$FIX/p_b3a_hold" > "$CELL/holder.out" 2>&1 &
echo $! > "$CELL/holder.pid"
sleep 0.5
kill -0 "$(cat "$CELL/holder.pid")"
kill -0 "$X3"

/data/data/com.termux/files/usr/bin/bash -lc "
set -e
export HOME=/data/data/com.termux/files/home
export PREFIX=/data/data/com.termux/files/usr
export PATH=/data/data/com.termux/files/usr/bin:/system/bin
export LD_LIBRARY_PATH=$HDIR/libs
export DISPLAY=:3
export TMPDIR=/data/data/com.termux/files/usr/tmp
export ANDROID_DATA=/data
export ANDROID_ROOT=/system
export CLASSPATH=$HDIR/classes.dex
export LD_PRELOAD=
exec /system/bin/app_process -Xnoimage-dex2oat $HDIR R2AhbHelp
" | tee "$CELL/r2-fixture-appprocess.out"
echo APP_EXIT=${PIPESTATUS[0]}
kill -0 "$X3" && echo X3_ALIVE | tee -a "$CELL/alive.txt"

{
  echo '===GATEA_EVENT==='
  grep -c GATEA_EVENT "$CELL/logcat-follow.txt" || echo 0
  grep GATEA_EVENT "$CELL/logcat-follow.txt" || echo NONE
  echo '===DRI3 import==='
  grep -h 'imported AHardwareBuffer, modifier 1255' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" | tee "$CELL/dri3-import-lines.txt" || true
  grep -c 'imported AHardwareBuffer, modifier 1255' "$CELL/dri3-import-lines.txt" || echo 0
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
grep -q 'RESULT p_r2_imported_ahb PASS both-cells exact maxΔ=0' "$CELL/r2-fixture-appprocess.out"
python3 - "$CELL" <<'PY'
import sys, re
from pathlib import Path
cell=Path(sys.argv[1])
out=(cell/'r2-fixture-appprocess.out').read_text()
assert 'PASS cell1-imported-src exact_px=64 maxΔ=0 got0=00804000' in out
assert 'PASS cell2-imported-dst exact_px=64 maxΔ=0 got0=00804000' in out
assert 'modifier=1255' in out
tele=(cell/'telemetry-fatal-pre-teardown.txt').read_text(errors='replace')
m=re.search(r'===GATEA_EVENT===\n(\d+)', tele)
count=int(m.group(1)) if m else -1
assert count==0, tele[:2000]
dri=(cell/'dri3-import-lines.txt').read_text(errors='replace') if (cell/'dri3-import-lines.txt').exists() else ''
n=len([ln for ln in dri.splitlines() if 'imported AHardwareBuffer, modifier 1255' in ln])
assert n>=2, dri[:2000] or tele[:2000]
assert 'GATEA_FATAL_HALT' not in tele
print('R2_OK events', count, 'imports', n)
PY
echo R2_IMPORTED_REJECT_PASS
