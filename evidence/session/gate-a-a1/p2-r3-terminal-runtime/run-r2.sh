#!/usr/bin/env bash
# TEMPLATE ONLY — do not execute until a new CI APK is installed.
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"
mkdir -p "$CELL"
STABLE_PRE=$(stabpid)
STABLE_CMD_PRE=$(stab_cmd)
echo "stable_pre_pid=$STABLE_PRE" | tee "$CELL/stable-pre.txt"
echo "stable_pre_cmd=$STABLE_CMD_PRE" | tee -a "$CELL/stable-pre.txt"
test -n "$STABLE_PRE"
echo "$STABLE_CMD_PRE" | grep -q '^termux-x11 com.termux.x11 :1'

ADB shell am force-stop com.waydefu.x11gpu
sleep 1
ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' | tee "$CELL/am-start.out"
ADB shell dumpsys activity activities > "$CELL/dumpsys-activity.txt"
assert_display0 "$CELL/dumpsys-activity.txt"

SINCE=$(ADB shell "date '+%m-%d %H:%M:%S.000'" | tr -d '\r')
echo "logcat_since=$SINCE" | tee "$CELL/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$CELL/logcat-follow.txt" "$SINCE")
echo "$LOGCAT_PID" > "$CELL/logcat.pid"
verify_logcat_pid "$LOGCAT_PID"

export GATEA_X3_LAUNCHER_LOG="$CELL/x3-launcher.raw.log"
: > "$GATEA_X3_LAUNCHER_LOG"
export TERMUX_X11_GATEA_PROTO=1
export TERMUX_X11_GATEA_TELEMETRY=1
export TERMUX_X11_DEBUG=1
python3 "$RUN" | tee "$CELL/start-x3.out"
X3=""
for i in $(seq 1 20); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
save_x_identity "$X3" "$CELL"

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
HDIR=/data/data/com.termux/files/home/r2-ahb-helper
set +e
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
R2_RC=${PIPESTATUS[0]}
set -e
echo "FIXTURE_EXIT=$R2_RC" | tee "$CELL/fixture-exit.txt"
test "$(stabpid)" = "$STABLE_PRE"
test "$(stab_cmd)" = "$STABLE_CMD_PRE"
{
  echo "===process residue only==="
  echo "STABLE $(stabpid)"
  if x3pid >/dev/null; then echo RESIDUE; else echo NO_X3_RESIDUE; fi
} | tee "$CELL/teardown.txt"
test "$R2_RC" -eq 0
