#!/usr/bin/env bash
# ONE CASE_LOOP repair-validation observation on installed 7549e36.
# NOT B-2: no oracle, no stress100, no mixed100, no B-2 PASS/FAIL judge.
# NOT R7: TEST_FAULT unset. Timeout stays 2000. No retry.
# Workload: one p_b2_stress 1000 only (same family as feeaa56 stall-obs-01).
# Usage: SERIAL=HOST:PORT CELL=.../runtime-7549e36/repair-validation-01 bash run-repair-validation-7549e36.sh
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
EXPECT_STRESS_SHA256=3e79b5cf875f5d7d05a25634983a44d9acfe67dfb885bf11f19b2cdb70e43c56
EXPECT_VERSION=1.03.01-7549e36-16.09.26
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"

start_logcat() {
  local out=$1 since=$2
  (
    exec env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
      HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
      "$TADB" -H 127.0.0.1 -P 5038 -s "$SERIAL" logcat -v threadtime -T "$since" \
      gatea-telemetry:V gatea-a1:V LorieNative:I DEBUG:I libc:F Xlorie:I gles-renderer:V \
      SurfaceFlinger:V BufferQueueProducer:V BufferQueue:V libEGL:V \
      > "$out" 2>&1
  ) &
  echo $!
}

mkdir -p "$CELL"
case "$CELL" in
  */runtime-7549e36/repair-validation-01) ;;
  *) echo "REFUSE CELL must be .../runtime-7549e36/repair-validation-01 got=$CELL"; exit 9;;
esac
if [ -f "$CELL/stall-stress1000.out" ]; then
  echo "REFUSE CELL already has stall-stress1000.out (no retry)"
  exit 9
fi

test -x "$FIX/p_b2_stress"
STRESS_SHA=$(sha256sum "$FIX/p_b2_stress" | awk '{print $1}')
test "$STRESS_SHA" = "$EXPECT_STRESS_SHA256"
echo "role=case-loop-repair-validation-not-b2-not-r7 p_b2_stress_sha256=$STRESS_SHA" | tee "$CELL/preflight.txt"
ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'versionName=|lastUpdateTime=|versionCode=' | head -6 | tee "$CELL/installed-package-pre.txt"
grep -q "versionName=$EXPECT_VERSION" "$CELL/installed-package-pre.txt"
ADB shell dumpsys package com.termux.x11 | grep -E 'versionCode=|versionName=|lastUpdateTime=' | head -6 | tee "$CELL/stable-package-pre.txt"
grep -q 'versionName=1.03.01-11b82d9-06.09.26' "$CELL/stable-package-pre.txt"

ADB shell dumpsys power | grep mWakefulness= | head -1 | tee "$CELL/screen.txt"
ADB shell dumpsys window | grep isKeyguardShowing= | head -1 >> "$CELL/screen.txt"
grep -q 'mWakefulness=Awake' "$CELL/screen.txt"
grep -q 'isKeyguardShowing=false' "$CELL/screen.txt"
ADB shell dumpsys display | grep -E 'Display id=|mType=|mDisplayId=' | head -20 | tee "$CELL/hdmi-observe.txt" || true

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
unset TERMUX_X11_GATEA_A1 || true
python3 "$RUN" | tee "$CELL/start-x3.out"
X3=""
for i in $(seq 1 40); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
echo "x3_pid=$X3 mode=unset role=repair-validation" | tee "$CELL/x3-pid.txt"
save_x_identity "$X3" "$CELL"
tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11' | tee "$CELL/x-environ-all-termux-x11.txt" || true
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
    'TERMUX_X11_GATEA_A1',
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
  ADB logcat -d -v threadtime -T "$SINCE" > "$CELL/logcat-dump-unfiltered.txt" || true
  echo REPAIR_VALIDATION_INVALID > "$CELL/primary-verdict.txt"
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

echo "cmd=$FIX/p_b2_stress 1000 role=case-loop-repair-validation-not-b2" > "$CELL/command.txt"
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
  echo '===timeout==='
  grep -c 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo 0
  grep 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo NONE
  echo '===fatal==='
  grep -E 'GATEA_FATAL_HALT|x-exa-composite-wait|Fatal signal|SIGSEGV|SIGILL' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===gcomp==='
  grep -c 'Gcomp Prepare TRUE' "$CELL/logcat-follow.txt" || echo 0
  grep -c 'Gcomp RECT' "$CELL/logcat-follow.txt" || echo 0
  grep -c 'Gcomp Done' "$CELL/logcat-follow.txt" || echo 0
  echo '===apply==='
  grep -c 'rendererApplyPendingGpuCopies' "$CELL/logcat-follow.txt" || echo 0
} | tee "$CELL/telemetry-fatal-pre-teardown.txt"

ADB logcat -d -v threadtime -T "$SINCE" > "$CELL/logcat-dump-unfiltered.txt" || true

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

python3 - "$CELL" <<'PY'
import re, sys
from pathlib import Path

cell = Path(sys.argv[1])
log = (cell / 'logcat-follow.txt').read_text(errors='replace')
unf = ''
unf_path = cell / 'logcat-dump-unfiltered.txt'
if unf_path.is_file():
    unf = unf_path.read_text(errors='replace')
both = log + '\n' + unf
stress = (cell / 'stall-stress1000.out').read_text(errors='replace') if (cell / 'stall-stress1000.out').is_file() else ''
alive = (cell / 'alive.txt').read_text(errors='replace') if (cell / 'alive.txt').is_file() else ''
fx = (cell / 'fixture-exit.txt').read_text(errors='replace') if (cell / 'fixture-exit.txt').is_file() else ''
env = (cell / 'x-environ-gatea.txt').read_text(errors='replace') if (cell / 'x-environ-gatea.txt').is_file() else ''

def wall_s(ln):
    parts = ln.split()
    if len(parts) < 2 or ':' not in parts[1]:
        return None
    h, m, rest = parts[1].split(':')
    s, ms = rest.split('.')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms[:3]) / 1000.0

def lines_with(hay, needle):
    return [ln for ln in hay.splitlines() if needle in ln]

timeouts = lines_with(log, 'EXA GPU composite wait timeout')
if not timeouts:
    timeouts = lines_with(unf, 'EXA GPU composite wait timeout')
fatals = [ln for ln in both.splitlines() if 'GATEA_FATAL_HALT' in ln]
exa_wait = [ln for ln in both.splitlines() if 'x-exa-composite-wait' in ln]
gprep = lines_with(log, 'Gcomp Prepare TRUE') or lines_with(unf, 'Gcomp Prepare TRUE')
grect = lines_with(log, 'Gcomp RECT') or lines_with(unf, 'Gcomp RECT')
gdone = lines_with(log, 'Gcomp Done') or lines_with(unf, 'Gcomp Done')
apply_follow = sum(1 for ln in log.splitlines() if 'rendererApplyPendingGpuCopies' in ln)
apply_unf = sum(1 for ln in unf.splitlines() if 'rendererApplyPendingGpuCopies' in ln)
apply_lines = lines_with(log, 'rendererApplyPendingGpuCopies') or lines_with(unf, 'rendererApplyPendingGpuCopies')
pixel_rgb = [ln for ln in (both + '\n' + stress).splitlines() if 'PIXEL_RGB_MISMATCH' in ln]
pixel_x = [ln for ln in (both + '\n' + stress).splitlines() if 'PIXEL_XBYTE_MISMATCH' in ln]
diag_fail = [ln for ln in stress.splitlines() if ln.startswith('B2_DIAG_FAIL')]
fatal_signal = [ln for ln in both.splitlines() if 'Fatal signal' in ln or 'SIGSEGV' in ln or 'SIGILL' in ln]

m = re.search(r'STRESS mixed=(\d+) ok=(\d+) fail=(\d+) n=(\d+) alive=(\d+)', stress)
if not m:
    stress_ok = stress_fail = stress_n = stress_alive = None
else:
    stress_ok = int(m.group(2))
    stress_fail = int(m.group(3))
    stress_n = int(m.group(4))
    stress_alive = int(m.group(5))

x_alive_end = 'X3_ALIVE=yes' in alive
rc_m = re.search(r'STRESS_RC=(\d+)', fx)
stress_rc = int(rc_m.group(1)) if rc_m else None

# RECT → subsequent Done wall deltas (X EXA completion, includes GPU work).
rect_times = [wall_s(ln) for ln in grect]
done_times = [wall_s(ln) for ln in gdone]
rect_done = []
di = 0
for rt in rect_times:
    if rt is None:
        continue
    while di < len(done_times) and (done_times[di] is None or done_times[di] < rt):
        di += 1
    if di < len(done_times) and done_times[di] is not None:
        rect_done.append(done_times[di] - rt)
        di += 1

# RECT → next apply as consume proxy (apply has no serial; limitation).
apply_times = [wall_s(ln) for ln in apply_lines if wall_s(ln) is not None]
rect_apply = []
ai = 0
for rt in rect_times:
    if rt is None:
        continue
    while ai < len(apply_times) and apply_times[ai] < rt:
        ai += 1
    if ai < len(apply_times):
        rect_apply.append(apply_times[ai] - rt)
        ai += 1

timeout_then_done = 0
if timeouts:
    tw = wall_s(timeouts[0])
    if tw is not None:
        timeout_then_done = sum(
            1 for ln in gdone if (wall_s(ln) is not None and wall_s(ln) >= tw)
        )

gt2000_rect_done = sum(1 for d in rect_done if d >= 2.0)
gt2000_rect_apply = sum(1 for d in rect_apply if d >= 2.0)
max_rect_done = max(rect_done) if rect_done else None
max_rect_apply = max(rect_apply) if rect_apply else None

env_ok = env.strip() == 'NO_GATEA_ENV'
stall_phase_present = 'STALL_PHASE phase=' in both
notify_present = 'NOTIFY_ENTER' in both

invalid = False
invalid_reason = ''
if not env_ok:
    invalid = True
    invalid_reason = 'env contamination'
if stress_n is None:
    invalid = True
    invalid_reason = (invalid_reason + '; ' if invalid_reason else '') + 'stress summary missing'

same_family = bool(timeouts or fatals or exa_wait)
unclassified_timeout = False
if timeouts:
    # Production candidate has no STALL_PHASE; CASE_LOOP family if
    # timeout without subsequent Done (repair held) and no timeout→Done.
    unclassified_timeout = False

pixel_bad = bool(pixel_rgb or pixel_x)
complete = (
    stress_ok == 1000 and stress_fail == 0 and stress_n == 1000
    and stress_alive == 1 and x_alive_end and stress_rc == 0
)

if invalid:
    verdict = 'REPAIR_VALIDATION_INVALID'
    detail = invalid_reason
elif timeout_then_done:
    verdict = 'CASE_LOOP_REPAIR_NOT_VALIDATED'
    detail = f'TIMEOUT→DONE REGRESSION Gcomp_Done_after_timeout={timeout_then_done}'
elif pixel_bad:
    verdict = 'CASE_LOOP_REPAIR_NOT_VALIDATED'
    detail = f'pixel mismatch rgb={len(pixel_rgb)} xbyte={len(pixel_x)}'
elif same_family:
    verdict = 'CASE_LOOP_REPAIR_NOT_VALIDATED'
    detail = (
        f'x-exa-composite-wait/timeout/fatal recurred timeout={len(timeouts)} '
        f'fatal={len(fatals)} exa_wait={len(exa_wait)}'
    )
elif not complete:
    verdict = 'CASE_LOOP_REPAIR_NOT_VALIDATED'
    detail = (
        f'workload incomplete ok={stress_ok} fail={stress_fail} n={stress_n} '
        f'alive={stress_alive} x_alive_end={int(x_alive_end)} rc={stress_rc}'
    )
elif gt2000_rect_done or gt2000_rect_apply:
    verdict = 'CASE_LOOP_REPAIR_NOT_VALIDATED'
    detail = (
        f'>=2000ms consume/completion gap rect_done={gt2000_rect_done} '
        f'rect_apply={gt2000_rect_apply}'
    )
else:
    verdict = 'CASE_LOOP_REPAIR_VALIDATED'
    detail = 'one p_b2_stress 1000 completed exact, no EXA timeout/fatal, no >=2s gap'

lines = [
    f'verdict={verdict}',
    f'detail={detail}',
    'role=case-loop-repair-validation-not-b2',
    f'env_ok={int(env_ok)}',
    f'stress_rc={stress_rc}',
    f'stress_ok={stress_ok}',
    f'stress_fail={stress_fail}',
    f'stress_n={stress_n}',
    f'stress_alive={stress_alive}',
    f'x_alive_end={int(x_alive_end)}',
    f'gcomp_prepare_true={len(gprep)}',
    f'gcomp_rect={len(grect)}',
    f'gcomp_done={len(gdone)}',
    f'apply_follow={apply_follow}',
    f'apply_unfiltered={apply_unf}',
    f'rect_done_samples={len(rect_done)}',
    f'rect_done_max_s={max_rect_done}',
    f'rect_done_gt2000={gt2000_rect_done}',
    f'rect_apply_samples={len(rect_apply)}',
    f'rect_apply_max_s={max_rect_apply}',
    f'rect_apply_gt2000={gt2000_rect_apply}',
    f'timeout_count={len(timeouts)}',
    f'fatal_count={len(fatals)}',
    f'exa_wait_count={len(exa_wait)}',
    f'timeout_then_done={timeout_then_done}',
    f'pixel_rgb_mismatch={len(pixel_rgb)}',
    f'pixel_xbyte_mismatch={len(pixel_x)}',
    f'b2_diag_fail={len(diag_fail)}',
    f'fatal_signal={len(fatal_signal)}',
    f'stall_phase_present={int(stall_phase_present)}',
    f'notify_present={int(notify_present)}',
    'limitation=apply logs have no serial; RECT→apply is wall-clock proxy only',
    'not_b2=1',
]
if timeouts:
    lines.append('TIMEOUT ' + timeouts[0][:220])
else:
    lines.append('TIMEOUT NONE')
if fatals:
    lines.append('FATAL ' + fatals[0][:220])
else:
    lines.append('FATAL NONE')
(cell / 'repair-validation-classify.txt').write_text('\n'.join(lines) + '\n')
(cell / 'primary-verdict.txt').write_text(verdict + '\n')
print((cell / 'repair-validation-classify.txt').read_text())
PY

echo "REPAIR_VALIDATION_COMPLETE stress_rc=$STRESS_RC (not a B-2 verdict)"
