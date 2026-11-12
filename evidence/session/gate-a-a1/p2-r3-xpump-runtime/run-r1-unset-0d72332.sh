#!/usr/bin/env bash
# B-2 R1 unset requalification on installed 0d72332. Experimental :3 only.
# Uses current diagnostic-capable p_b2_stress; does not change its semantics.
# Usage: SERIAL=HOST:PORT CELL=.../runtime-0d72332/r1-unset-oracle{,-rerun1} bash run-r1-unset-0d72332.sh
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
EXPECT_STRESS_SHA256=3e79b5cf875f5d7d05a25634983a44d9acfe67dfb885bf11f19b2cdb70e43c56
EXPECT_VERSION=1.03.01-0d72332-16.09.26
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"
mkdir -p "$CELL"
case "$CELL" in
  */runtime-0d72332/r1-unset-oracle|*/runtime-0d72332/r1-unset-oracle-rerun1) ;;
  *) echo "REFUSE CELL must be .../runtime-0d72332/r1-unset-oracle or ...-rerun1 got=$CELL"; exit 9;;
esac
if [ -f "$CELL/x1000.out" ]; then
  echo "REFUSE CELL already has x1000.out"
  exit 9
fi

test -x "$FIX/p_b2_stress"
STRESS_SHA=$(sha256sum "$FIX/p_b2_stress" | awk '{print $1}')
test "$STRESS_SHA" = "$EXPECT_STRESS_SHA256"
echo "p_b2_stress_sha256=$STRESS_SHA diagnostic=B2_DIAG_FAIL" | tee "$CELL/preflight.txt"
strings -a "$FIX/p_b2_stress" | grep -q 'B2_DIAG_FAIL iteration='
ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'versionName=|lastUpdateTime=' | head -4 | tee "$CELL/installed-package-pre.txt"
grep -q "versionName=$EXPECT_VERSION" "$CELL/installed-package-pre.txt"
ADB shell dumpsys package com.termux.x11 | grep -E 'versionCode=|versionName=|lastUpdateTime=' | head -6 | tee "$CELL/stable-package-pre.txt"
grep -q 'versionName=1.03.01-11b82d9-06.09.26' "$CELL/stable-package-pre.txt"

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
test "$STABLE_PRE" = 17922

rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
  /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock /tmp/x11gpu-p2a3.snap || true
rm -f "$SUMMARY" || true

ADB shell am force-stop com.waydefu.x11gpu
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
unset TERMUX_X11_GATEA_PROTO || true
unset TERMUX_X11_GATEA_TELEMETRY || true
unset TERMUX_X11_DEBUG || true
unset TERMUX_X11_GATEA_TEST_FAULT || true
unset TERMUX_X11_GATEA_TEST_ARM || true
unset TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL || true
python3 "$RUN" | tee "$CELL/start-x3.out"
X3=""
for i in $(seq 1 40); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
echo "x3_pid=$X3 mode=unset" | tee "$CELL/x3-pid.txt"
save_x_identity "$X3" "$CELL"
if tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11_GATEA' > "$CELL/x-environ-gatea.txt"; then
  :
else
  echo NO_GATEA_ENV > "$CELL/x-environ-gatea.txt"
fi
python3 - "$CELL/x-environ-gatea.txt" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
forbidden = (
    'TERMUX_X11_GATEA_TEST_FAULT',
    'TERMUX_X11_GATEA_TEST_ARM',
    'TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL',
    'TERMUX_X11_GATEA_PROTO',
    'TERMUX_X11_GATEA_TELEMETRY',
)
for name in forbidden:
    assert name not in text, name
print('ENV_UNSET_OK')
PY
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
"$FIX/p_b2_stress" 100 | tee "$CELL/x100.out"
X100_RC=${PIPESTATUS[0]}
"$FIX/p_b2_stress" 100 1 | tee "$CELL/mixed100.out"
MIXED_RC=${PIPESTATUS[0]}
echo "cmd=$FIX/p_b2_stress 1000" > "$CELL/command.txt"
date -Is >> "$CELL/command.txt"
"$FIX/p_b2_stress" 1000 | tee "$CELL/x1000.out"
X1000_RC=${PIPESTATUS[0]}
date -Is >> "$CELL/command.txt"
echo "ORACLE_RC=$ORACLE_RC X100_RC=$X100_RC MIXED_RC=$MIXED_RC X1000_RC=$X1000_RC" | tee "$CELL/fixture-exit.txt"
set -e
if [ -d "/proc/$X3" ]; then echo "X3_ALIVE=yes pid=$X3" | tee -a "$CELL/alive.txt"
else echo "X3_ALIVE=no pid=$X3" | tee -a "$CELL/alive.txt"; fi

{
  echo '===GATEA_EVENT==='
  grep -c GATEA_EVENT "$CELL/logcat-follow.txt" || echo 0
  grep GATEA_EVENT "$CELL/logcat-follow.txt" || echo NONE
  echo '===event35==='
  grep -c 'event=35' "$CELL/logcat-follow.txt" || echo 0
  echo '===fatal==='
  grep -E 'GATEA_FATAL_HALT|x-exa-composite-wait|Fatal signal|SIGSEGV|SIGILL' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===timeout==='
  grep -c 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo 0
  grep 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo NONE
  echo '===gcomp==='
  grep -c 'Gcomp Done' "$CELL/logcat-follow.txt" || echo 0
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
if [ -f "$SUMMARY" ]; then
  cp -a "$SUMMARY" "$CELL/gatea-summary.txt"
else
  echo 'SUMMARY_ABSENT' | tee "$CELL/gatea-summary.txt"
fi
{
  echo "===process residue only==="
  echo "STABLE $(stabpid)"
  if x3pid >/dev/null; then echo RESIDUE; else echo NO_X3_RESIDUE; fi
} | tee "$CELL/teardown.txt"
ADB shell dumpsys package com.termux.x11 | grep -E 'versionCode=|versionName=|lastUpdateTime=' | head -6 | tee "$CELL/stable-package-after.txt"
echo "stable_after_pid=$(stabpid)" | tee "$CELL/stable-after.txt"
echo "stable_after_cmd=$(stab_cmd)" | tee -a "$CELL/stable-after.txt"
grep -q NO_X3_RESIDUE "$CELL/teardown.txt"
grep -q "STABLE $STABLE_PRE" "$CELL/teardown.txt"
test "$(stabpid)" = "$STABLE_PRE"
grep -q 'versionName=1.03.01-11b82d9-06.09.26' "$CELL/stable-package-after.txt"
grep -q 'lastUpdateTime=2026-09-07 22:55:03' "$CELL/stable-package-after.txt"

python3 - "$CELL" <<'PY'
import re, sys
from pathlib import Path
cell = Path(sys.argv[1])
tele = (cell / 'telemetry-fatal-pre-teardown.txt').read_text(errors='replace')
log = (cell / 'logcat-follow.txt').read_text(errors='replace')
m = re.search(r'===GATEA_EVENT===\n(\d+)', tele)
count = int(m.group(1)) if m else -1
assert count == 0, tele[:2000]
assert 'GATEA_FATAL_HALT' not in tele
assert 'x-exa-composite-wait' not in tele
ev35 = len(re.findall(r'event=35\b', log))
assert ev35 == 0, ev35
timeouts = [ln for ln in log.splitlines() if 'EXA GPU composite wait timeout' in ln]
dones = [ln for ln in log.splitlines() if 'Gcomp Done' in ln]
(cell / 'timeout-done-correlate.txt').write_text(
    f'timeout_count={len(timeouts)}\ngcomp_done_count={len(dones)}\n'
    + '\n'.join(timeouts[:20]) + '\n')
# Same-ms timeout then Done is the repaired defect. Any timeout on this
# baseline cell is STOP (fail-stop expected, not PASS).
assert not timeouts, timeouts[:5]
print('R1_UNSET_TELEMETRY_OK count', count, 'timeouts', len(timeouts), 'gcomp', len(dones))
PY

test "$ORACLE_RC" -eq 0
grep -q 'ORACLE tests=1514 fail=0' "$CELL/oracle.out"
grep -q 'RESULT p-b2-oracle PASS fail=0 maxΔ=0' "$CELL/oracle.out"
grep -q 'X3_ALIVE=yes' "$CELL/alive.txt"
test "$X100_RC" -eq 0
test "$MIXED_RC" -eq 0
test "$X1000_RC" -eq 0
grep -E 'ok=100 fail=0' "$CELL/x100.out"
grep -E 'ok=100 fail=0' "$CELL/mixed100.out"
grep -E 'ok=1000 fail=0' "$CELL/x1000.out"
grep -q GATEA_SUMMARY "$CELL/gatea-summary.txt"
echo "R1 unset PASS"
