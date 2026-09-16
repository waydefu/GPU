#!/usr/bin/env bash
# One mandatory R7 cell on installed fdfb1ce. Experimental :3 only.
# Not B-2. Not historical r7-qualification-01. Not r7-04-requalification-01.
# This file does NOT authorize execution. Needs a new grant.
# Usage: SERIAL=... ROOT=.../runtime-fdfb1ce \
#        CELL_ID=r7-05 FAULT=post-draw-gl FIXTURE=direct WAIT_S=12 \
#        bash run-r7-one-cell-fdfb1ce.sh
set -euo pipefail
ROOT_HARNESS=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
JUDGE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
EXPECT_VERSION=1.03.01-fdfb1ce-16.09.26
: "${SERIAL:?}"
: "${ROOT:?}"
: "${CELL_ID:?}"
: "${FAULT:?}"
: "${FIXTURE:?}"
WAIT_S="${WAIT_S:-12}"
CELL="$ROOT/$CELL_ID"
export CELL
case "$CELL" in
  */runtime-fdfb1ce/r7-04-requalification-01)
    echo "REFUSE do not overwrite completed R7-04 requalification"; exit 9;;
  */runtime-fdfb1ce/*) ;;
  *) echo "REFUSE CELL must be under .../runtime-fdfb1ce/ got=$CELL"; exit 9;;
esac
case "$CELL_ID" in
  r7-04|r7-04-requalification-01)
    echo "REFUSE R7-04 already PASS on fdfb1ce; no retry"; exit 9;;
esac
# shellcheck source=/dev/null
source "$ROOT_HARNESS/harness-lib.sh"
FIXPID=""
X3=""
cleanup_r7() {
  local rc=$?
  if [ -n "${FIXPID:-}" ]; then
    kill -TERM "$FIXPID" 2>/dev/null || true
    wait "$FIXPID" 2>/dev/null || true
  fi
  if [ -n "${HOLDER_PID:-}" ]; then
    kill -TERM "$HOLDER_PID" 2>/dev/null || true
    wait "$HOLDER_PID" 2>/dev/null || true
  fi
  if [ -n "${LOGCAT_PID:-}" ]; then
    stop_logcat "$LOGCAT_PID" || true
  fi
  local live
  if live=$(x3pid 2>/dev/null); then
    cmd=$(tr '\0' ' ' < "/proc/$live/cmdline" 2>/dev/null || true)
    case "$cmd" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) kill "$live" 2>/dev/null || true;;
    esac
  fi
  ADB shell am force-stop com.waydefu.x11gpu >/dev/null 2>&1 || true
  rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
    /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock || true
  return "$rc"
}
trap cleanup_r7 EXIT

start_logcat() {
  local out=$1 since=$2
  (
    exec env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
      HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
      "$TADB" -H 127.0.0.1 -P 5038 -s "$SERIAL" logcat -v threadtime -T "$since" \
      gatea-telemetry:V gatea-a1:V LorieNative:I DEBUG:I libc:F Xlorie:I gles-renderer:V \
      > "$out" 2>&1
  ) &
  echo $!
}

mkdir -p "$CELL"
if [ -f "$CELL/primary-verdict.txt" ] || [ -f "$CELL/fixture.out" ] || [ -f "$CELL/logcat-follow.txt" ]; then
  echo "REFUSE $CELL_ID already has evidence"
  echo INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
fi

{
  echo "cell_id=$CELL_ID"
  echo "fault=$FAULT"
  echo "arm=1"
  echo "fixture=$FIXTURE"
  echo "wait_s=$WAIT_S"
  echo "expect_version=$EXPECT_VERSION"
} | tee "$CELL/preflight.txt"

ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'versionName=|versionCode=|lastUpdateTime=' | head -6 | tee "$CELL/installed-package.txt"
grep -q "versionName=$EXPECT_VERSION" "$CELL/installed-package.txt"
grep -q 'versionCode=15' "$CELL/installed-package.txt"

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
ADB shell dumpsys package com.termux.x11 | grep -E 'versionName=|versionCode=|lastUpdateTime=' | head -6 | tee "$CELL/stable-package-pre.txt"

if X3=$(x3pid); then
  echo "REFUSE preexisting X3 pid=$X3"
  echo INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
fi

rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
  /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock /tmp/x11gpu-p2a3.snap || true
rm -f "$SUMMARY" "$RING" || true

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
unset TERMUX_X11_DEBUG || true
unset TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL || true
unset TERMUX_X11_GATEA_A1 || true
unset TERMUX_X11_B3A_TELEMETRY || true
export TERMUX_X11_GATEA_PROTO=1
export TERMUX_X11_GATEA_TELEMETRY=1
export TERMUX_X11_GATEA_TEST_FAULT="$FAULT"
export TERMUX_X11_GATEA_TEST_ARM=1
python3 "$RUN" | tee "$CELL/start-x3.out"
X3=""
for i in $(seq 1 40); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
echo "x3_pid=$X3 cell=$CELL_ID fault=$FAULT arm=1 proto=1 telemetry=1" | tee "$CELL/x3-pid.txt"
save_x_identity "$X3" "$CELL"
tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11' | tee "$CELL/x-environ-all-termux-x11.txt" || true
tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11_GATEA' | tee "$CELL/x-environ-gatea.txt" || true
python3 - "$CELL/x-environ-gatea.txt" "$FAULT" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text() if Path(sys.argv[1]).exists() else ""
fault = sys.argv[2]
lines = [ln for ln in text.splitlines() if ln.strip()]
need = {
    "TERMUX_X11_GATEA_PROTO=1",
    "TERMUX_X11_GATEA_TELEMETRY=1",
    f"TERMUX_X11_GATEA_TEST_FAULT={fault}",
    "TERMUX_X11_GATEA_TEST_ARM=1",
}
got = set(lines)
if got != need:
    print("ENV_MISMATCH need", sorted(need), "got", sorted(got))
    raise SystemExit(9)
print("ENV_EXACT_OK")
PY

for i in $(seq 1 40); do
  if [ -S /data/data/com.termux/files/usr/tmp/.X11-unix/X3 ] || [ -S /tmp/.X11-unix/X3 ]; then
    echo "socket_ready i=$i"
    break
  fi
  sleep 0.25
done
sleep 8
if [ ! -d "/proc/$X3" ]; then
  echo "DIED_DURING_8S pid=$X3" | tee "$CELL/alive.txt"
  ADB logcat -d -v threadtime -T "$SINCE" > "$CELL/logcat-dump-unfiltered.txt" || true
  echo INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
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

: > "$CELL/fixture.out"
set +e
if [ "$FIXTURE" = present ]; then
  "$FIX/p_r6_d2_present" inflight >> "$CELL/fixture.out" 2>&1 &
else
  "$FIX/p_r3_single_direct" >> "$CELL/fixture.out" 2>&1 &
fi
FIXPID=$!
echo "$FIXPID" > "$CELL/fixture.pid"
elapsed=0
while [ "$elapsed" -lt "$WAIT_S" ]; do
  if [ ! -d "/proc/$X3" ]; then
    echo "X3_DIED_AFTER_TRIGGER elapsed=$elapsed" | tee -a "$CELL/alive.txt"
    break
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
if [ -d "/proc/$X3" ]; then
  echo "X3_STILL_ALIVE pid=$X3 elapsed=$elapsed wchan=$(cat /proc/$X3/wchan 2>/dev/null || echo gone)" | tee -a "$CELL/alive.txt"
fi
kill -TERM "$FIXPID" 2>/dev/null || true
wait "$FIXPID" 2>/dev/null
FIX_RC=$?
set -e
echo "FIXTURE_EXIT=$FIX_RC" | tee "$CELL/fixture-exit.txt"
cat "$CELL/fixture.out" || true

if [ -f "$SUMMARY" ]; then cp -a "$SUMMARY" "$CELL/gatea-summary.txt"; else echo NONE > "$CELL/gatea-summary.txt"; fi
if [ -f "$RING" ]; then cp -a "$RING" "$CELL/gatea-ring.txt"; else echo NONE > "$CELL/gatea-ring.txt"; fi

sleep 1
ADB logcat -d -v threadtime -T "$SINCE" > "$CELL/logcat-dump-unfiltered.txt" || true
{
  echo '===GATEA_EVENT==='
  grep -a GATEA_EVENT "$CELL/logcat-follow.txt" || echo NONE
  echo '===FAULT_HALT==='
  grep -aE 'GATEA_FATAL_HALT|GATEA_SUMMARY|TEST_FAULT|x-test-fault-env' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===Gcomp==='
  grep -aE 'Gcomp Done|x-exa-composite-wait|x-present-copy-wait|x-direct-not-success' "$CELL/logcat-follow.txt" "$CELL/logcat-dump-unfiltered.txt" || echo NONE
  echo '===signal==='
  grep -aE 'Fatal signal|SIGSEGV|SIGILL|SIGABRT' "$CELL/logcat-follow.txt" "$CELL/logcat-dump-unfiltered.txt" || echo NONE
} | tee "$CELL/telemetry-fatal.txt"

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
    "termux-x11gpu com.waydefu.x11gpu :3"*) kill "$X3"; echo "killed_alive_x $X3" | tee -a "$CELL/teardown.txt";;
    *) echo "REFUSE_KILL $X3 cmd=$cmd"; echo INVALID | tee "$CELL/primary-verdict.txt"; exit 9;;
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
} | tee -a "$CELL/teardown.txt"
grep -q NO_X3_RESIDUE "$CELL/teardown.txt"
grep -q "STABLE $STABLE_PRE" "$CELL/teardown.txt"
ADB shell dumpsys package com.termux.x11 | grep -E 'versionName=|lastUpdateTime=' | head -4 | tee "$CELL/stable-package-after.txt"

X_ALIVE=0
grep -q 'X3_STILL_ALIVE' "$CELL/alive.txt" && X_ALIVE=1
EXIT_SIGNAL=0
if grep -aEq 'Fatal signal (11|6|4)|SIGSEGV|SIGILL|SIGABRT' "$CELL/logcat-follow.txt" "$CELL/logcat-dump-unfiltered.txt" 2>/dev/null; then
  if ! grep -aq 'GATEA_FATAL_HALT' "$CELL/logcat-follow.txt" "$CELL/logcat-dump-unfiltered.txt" 2>/dev/null; then
    EXIT_SIGNAL=11
  fi
fi

set +e
python3 "$JUDGE" "$FAULT" "$CELL/logcat-follow.txt" \
  --ring "$CELL/gatea-ring.txt" \
  --summary "$CELL/gatea-summary.txt" \
  --x-alive "$X_ALIVE" \
  --exit-signal "$EXIT_SIGNAL" | tee "$CELL/judge.txt"
JRC=${PIPESTATUS[0]}
set -e

python3 - "$CELL" "$FAULT" <<'PY'
from pathlib import Path
import re, sys
cell = Path(sys.argv[1])
fault = sys.argv[2]
blob = (cell/'logcat-follow.txt').read_text(errors='replace')
blob += '\n' + (cell/'logcat-dump-unfiltered.txt').read_text(errors='replace')
blob += '\n' + (cell/'gatea-summary.txt').read_text(errors='replace')
blob += '\n' + (cell/'fixture.out').read_text(errors='replace')
halts = re.findall(r'GATEA_FATAL_HALT what=(\S+) reason=(\d+)', blob)
faults = re.findall(r'GATEA_EVENT seq=(\d+) role=(\d+) event=35 ', blob)
gcomp_done = len(re.findall(r'Gcomp Done', blob))
timeout_done = len(re.findall(r'timeout.?Done|EXA GPU composite wait timeout[\s\S]{0,80}Gcomp Done', blob, re.I))
exa_to = len(re.findall(r'x-exa-composite-wait|EXA GPU composite wait timeout', blob))
(cell/'forbidden-audit.txt').write_text(
    f"fault={fault}\n"
    f"event35_count={len(faults)}\n"
    f"halts={halts}\n"
    f"gcomp_done={gcomp_done}\n"
    f"exa_timeout={exa_to}\n"
    f"timeout_to_done_loose={timeout_done}\n"
    f"fixture_pass={'RESULT p_r3_single_direct PASS' in blob or 'CLIENT_OK' in blob}\n"
)
print('audit', (cell/'forbidden-audit.txt').read_text())
PY

if [ "$JRC" -eq 0 ] && [ "$X_ALIVE" -eq 0 ] && grep -q '^R7_PASS' "$CELL/judge.txt"; then
  echo PASS | tee "$CELL/primary-verdict.txt"
  exit 0
fi
if grep -q 'x-test-fault-env' "$CELL/telemetry-fatal.txt"; then
  echo INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
fi
echo FAIL | tee "$CELL/primary-verdict.txt"
exit 2
