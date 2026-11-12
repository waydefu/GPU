#!/usr/bin/env bash
# ONE stall-phase device observation on installed 27d8d1b.
# NOT B-2: no oracle, no stress100, no mixed100, no B-2 PASS/FAIL judge.
# NOT R7: TEST_FAULT unset. Timeout stays 2000. No retry.
# Workload: one p_b2_stress 1000 only, because that is the proven stall trigger.
# Usage: SERIAL=HOST:PORT CELL=.../runtime-27d8d1b/stall-obs-01 bash run-stall-obs-27d8d1b.sh
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
EXPECT_STRESS_SHA256=3e79b5cf875f5d7d05a25634983a44d9acfe67dfb885bf11f19b2cdb70e43c56
EXPECT_VERSION=1.03.01-27d8d1b-16.09.26
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"
mkdir -p "$CELL"
case "$CELL" in
  */runtime-27d8d1b/stall-obs-01) ;;
  *) echo "REFUSE CELL must be .../runtime-27d8d1b/stall-obs-01 got=$CELL"; exit 9;;
esac
if [ -f "$CELL/stall-stress1000.out" ]; then
  echo "REFUSE CELL already has stall-stress1000.out (no retry)"
  exit 9
fi

test -x "$FIX/p_b2_stress"
STRESS_SHA=$(sha256sum "$FIX/p_b2_stress" | awk '{print $1}')
test "$STRESS_SHA" = "$EXPECT_STRESS_SHA256"
echo "role=stall-obs-not-b2-not-r7 p_b2_stress_sha256=$STRESS_SHA" | tee "$CELL/preflight.txt"
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
echo "x3_pid=$X3 mode=unset role=stall-obs" | tee "$CELL/x3-pid.txt"
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
echo "ALIVE_BEFORE_STRESS pid=$X3" | tee "$CELL/alive.txt"

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

echo "cmd=$FIX/p_b2_stress 1000 role=stall-obs-not-b2" > "$CELL/command.txt"
date -Is >> "$CELL/command.txt"
set +e
"$FIX/p_b2_stress" 1000 | tee "$CELL/stall-stress1000.out"
STRESS_RC=${PIPESTATUS[0]}
set -e
date -Is >> "$CELL/command.txt"
echo "STRESS_RC=$STRESS_RC" | tee "$CELL/fixture-exit.txt"
if [ -d "/proc/$X3" ]; then echo "X3_ALIVE=yes pid=$X3" | tee -a "$CELL/alive.txt"
else echo "X3_ALIVE=no pid=$X3" | tee -a "$CELL/alive.txt"; fi

{
  echo '===STALL_PHASE==='
  grep -c 'STALL_PHASE phase=' "$CELL/logcat-follow.txt" || echo 0
  echo '===timeout==='
  grep -c 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo 0
  grep 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo NONE
  echo '===fatal==='
  grep -E 'GATEA_FATAL_HALT|x-exa-composite-wait|Fatal signal|SIGSEGV|SIGILL' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===gcomp==='
  grep -c 'Gcomp Done' "$CELL/logcat-follow.txt" || echo 0
} | tee "$CELL/telemetry-fatal-pre-teardown.txt"

ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true

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

def wall_s(ln):
    parts = ln.split()
    if len(parts) < 2 or ':' not in parts[1]:
        return None
    h, m, rest = parts[1].split(':')
    s, ms = rest.split('.')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms[:3]) / 1000.0

cell = Path(sys.argv[1])
log = (cell / 'logcat-follow.txt').read_text(errors='replace')
phase_re = re.compile(r'STALL_PHASE phase=(\S+) mono_ns=(\d+) tid=(\d+)')
phases = []
for ln in log.splitlines():
    m = phase_re.search(ln)
    if not m:
        continue
    phases.append((wall_s(ln), m.group(1), int(m.group(2)), m.group(3), ln[:240]))
timeouts = [ln for ln in log.splitlines() if 'EXA GPU composite wait timeout' in ln]
fatals = [ln for ln in log.splitlines() if 'GATEA_FATAL_HALT' in ln]
gcomp = [ln for ln in log.splitlines() if 'Gcomp Done' in ln]
assert phases, 'STALL_PHASE markers missing from logcat — instrumentation not live'
verdict = 'STALL_NOT_OBSERVED'
detail = 'stress completed without EXA wait timeout'
cutoff = wall_s(timeouts[0]) if timeouts else None
before = [p for p in phases if cutoff is None or (p[0] is not None and p[0] <= cutoff)]
if timeouts:
    last = {name: None for name in (
        'SWAP_ENTER', 'SWAP_EXIT', 'NEXT_FENCE_ENTER', 'NEXT_FENCE_EXIT')}
    for item in before:
        last[item[1]] = item
    se = last['SWAP_ENTER'][2] if last['SWAP_ENTER'] else None
    sx = last['SWAP_EXIT'][2] if last['SWAP_EXIT'] else None
    ne = last['NEXT_FENCE_ENTER'][2] if last['NEXT_FENCE_ENTER'] else None
    nx = last['NEXT_FENCE_EXIT'][2] if last['NEXT_FENCE_EXIT'] else None
    if se is not None and (sx is None or sx < se):
        verdict = 'CASE_A_SWAP'
        detail = f'SWAP_ENTER={se} with no later SWAP_EXIT before timeout'
    elif se is not None and sx is not None and (sx - se) >= 1_500_000_000:
        verdict = 'CASE_A_SWAP'
        detail = f'swap_hold_ns={sx - se}'
    elif ne is not None and (nx is None or nx < ne):
        verdict = 'CASE_B_NEXT_FENCE'
        detail = f'NEXT_FENCE_ENTER={ne} with no later NEXT_FENCE_EXIT before timeout'
    elif ne is not None and nx is not None and (nx - ne) >= 1_500_000_000:
        verdict = 'CASE_B_NEXT_FENCE'
        detail = f'next_fence_hold_ns={nx - ne}'
    elif se is not None and sx is not None and ne is not None and nx is not None:
        verdict = 'CASE_C_LOOP_OR_OTHER'
        detail = f'swap_ns={sx-se} next_fence_ns={nx-ne}'
    else:
        verdict = 'CASE_INCOMPLETE_MARKERS'
        detail = f'swap_enter={se} swap_exit={sx} nf_enter={ne} nf_exit={nx}'
out = cell / 'stall-phase-classify.txt'
out.write_text(
    f'verdict={verdict}\n'
    f'detail={detail}\n'
    f'stall_phase_count={len(phases)}\n'
    f'phases_before_timeout={len(before)}\n'
    f'timeout_count={len(timeouts)}\n'
    f'fatal_count={len(fatals)}\n'
    f'gcomp_count={len(gcomp)}\n'
    f'not_b2=1\n'
    + ('TIMEOUT ' + timeouts[0][:220] + '\n' if timeouts else 'TIMEOUT NONE\n')
    + ('FATAL ' + fatals[0][:220] + '\n' if fatals else 'FATAL NONE\n')
    + 'LAST_PHASES_BEFORE_TIMEOUT\n'
    + '\n'.join(p[4] for p in before[-12:])
    + '\n'
)
print(out.read_text())
PY

echo "STALL_OBS_COMPLETE stress_rc=$STRESS_RC (not a B-2 verdict)"
