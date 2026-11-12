#!/usr/bin/env bash
# One design-complete R6 cell. Historical runtime-9369553 cells are frozen.
# New APK: EXPECT_VERSION=1.03.01-<sha>-… CELL=…/runtime-<sha>/r6-d2-inflight
# Usage: SERIAL=HOST:PORT VARIANT=d1 CELL=.../runtime-9369553/r6-d1 bash run-r6-design.sh
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
JUDGE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/judge-r6-design.py
BIND=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/r6-design-bind.sh
EXPECT_D1_SHA256=e74776f3c85c8595e068d705f7f29a4555a407abd76054ffa4db4cac5afe1197
# shellcheck source=r6-design-bind.sh
source "$BIND"
r6_design_bind
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"
mkdir -p "$CELL"
if [ -f "$CELL/r6-fixture.out" ]; then
  echo "REFUSE CELL already has r6-fixture.out"
  exit 9
fi

if [ "$VARIANT" = d1 ]; then
  test -x "$FIX/p_r6_d1_queued"
  FIX_SHA=$(sha256sum "$FIX/p_r6_d1_queued" | awk '{print $1}')
  test "$FIX_SHA" = "$EXPECT_D1_SHA256"
else
  test -x "$FIX/p_r6_d2_present"
  FIX_SHA=$(sha256sum "$FIX/p_r6_d2_present" | awk '{print $1}')
  test "$FIX_SHA" = "$EXPECT_D2_SHA256"
fi
echo "fixture_sha256=$FIX_SHA variant=$VARIANT" | tee "$CELL/fixture.sha256.txt"

ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'versionName=|lastUpdateTime=' | head -4 | tee "$CELL/installed-package-pre.txt"
grep -q "versionName=${EXPECT_VERSION}" "$CELL/installed-package-pre.txt"

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
if [ "$VARIANT" = d2-oom ]; then
  export TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1
else
  unset TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL || true
fi
python3 "$RUN" | tee "$CELL/start-x3.out"
X3=""
for i in $(seq 1 40); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
echo "x3_pid=$X3 variant=$VARIANT proto=1 telemetry=1 watchdog_stall=45s watchdog_max=60s" | tee "$CELL/x3-pid.txt"
save_x_identity "$X3" "$CELL"
tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11_GATEA' | tee "$CELL/x-environ-gatea.txt"
if [ "$VARIANT" = d2-oom ]; then
  grep -qx 'TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1' "$CELL/x-environ-gatea.txt"
else
  if grep -q 'TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=' "$CELL/x-environ-gatea.txt"; then
    echo "REFUSE oom env set on non-oom cell"; exit 9
  fi
fi
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

: > "$CELL/r6-fixture.out"
set +e
if [ "$VARIANT" = d1 ]; then
  "$FIX/p_r6_d1_queued" >> "$CELL/r6-fixture.out" 2>&1 &
else
  MODE=inflight
  [ "$VARIANT" = d2-oom ] && MODE=oom
  "$FIX/p_r6_d2_present" "$MODE" >> "$CELL/r6-fixture.out" 2>&1 &
fi
FIXPID=$!
echo "$FIXPID" > "$CELL/fixture.pid"
stall=0
last_sz=-1
elapsed=0
WATCHDOG_STALL=45
WATCHDOG_MAX=60
while kill -0 "$FIXPID" 2>/dev/null; do
  sz=$(wc -c < "$CELL/r6-fixture.out" | tr -d ' ')
  if grep -q 'RESULT p_r6_' "$CELL/r6-fixture.out" 2>/dev/null; then
    break
  fi
  if [ "$sz" -eq "$last_sz" ]; then
    stall=$((stall + 1))
  else
    stall=0
    last_sz=$sz
    tail -1 "$CELL/r6-fixture.out" || true
  fi
  if [ "$stall" -ge "$WATCHDOG_STALL" ]; then
    {
      echo "WATCHDOG_STALL_S=$WATCHDOG_STALL fixture_pid=$FIXPID x3=$X3"
      echo "x_wchan=$(cat /proc/$X3/wchan 2>/dev/null || echo gone)"
      echo "x_state=$(awk '/^State:/{print}' /proc/$X3/status 2>/dev/null || true)"
      echo "fix_wchan=$(cat /proc/$FIXPID/wchan 2>/dev/null || echo gone)"
      echo "last_fixture=$(tail -3 "$CELL/r6-fixture.out" | tr '\n' ' | ')"
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
cat "$CELL/r6-fixture.out"
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
  echo '===R6 events==='
  grep -aE 'event=(29|30|31|32|33|34) ' "$CELL/logcat-follow.txt" || echo NONE
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

python3 "$JUDGE" "$CELL" "$VARIANT" "$FIX_RC"
echo R6_DESIGN_CELL_PASS "$VARIANT"
