#!/usr/bin/env bash
# a07d66c-only dedicated R7-11 serial-wrap runner. Experimental :3 only.
# Does NOT authorize device execution. Needs a separate single-cell grant.
# Does NOT retry. Does NOT run the next cell. Does NOT overwrite evidence.
# Frozen judge-r7.py is used unmodified. No timeout/ABI/selector change.
# Does NOT modify run-r7-one-cell-a07d66c.sh.
#
# R7-11 seeds gpuCopySerialCounter=UINT64_MAX AFTER event35 in
# gateADirectPublishRect, then the next ++ wraps to 0 and gateAXFatal
# x-serial-wrap/6 (noreturn) BEFORE PUBLISH. Fixture is required once.
# Early X death before that publish attempt is INVALID, not PASS.
# PUBLISH serial=0 is product FAIL even if the halt string is correct.
#
# Host validation:
#   VALIDATE_ONLY=1 ROOT=.../runtime-a07d66c \
#     CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct WAIT_S=12 \
#     bash run-r7-11-a07d66c.sh
# Live (requires a new grant):
#   SERIAL=... ROOT=.../runtime-a07d66c \
#     CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct WAIT_S=12 \
#     bash run-r7-11-a07d66c.sh
set -euo pipefail

ROOT_HARNESS=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
JUDGE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py
CLASSIFY=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/scripts/classify_r7_11_serial_wrap.py
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
EXPECT_VERSION=1.03.01-a07d66c-17.09.26
EXPECT_VERSION_CODE=15
CANDIDATE_HEAD=a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82
CANDIDATE_PARENT=fdfb1ce44b429897eda17c43bf33fbd37afe67f3
CANDIDATE_CI=35171333149
FROZEN_WAIT_S=12
TADB=/data/data/com.termux/files/usr/bin/adb

refuse() {
  echo "REFUSE $*"
  exit 9
}

if [ "$#" -ne 0 ]; then
  refuse "extra arguments not allowed; one CELL_ID/FAULT/FIXTURE via env only got=$*"
fi

VALIDATE_ONLY="${VALIDATE_ONLY:-0}"
case "$VALIDATE_ONLY" in
  0|1) ;;
  *) refuse "VALIDATE_ONLY must be 0 or 1 got=$VALIDATE_ONLY";;
esac

[ -n "${ROOT:-}" ] || refuse "ROOT required"
[ -n "${CELL_ID:-}" ] || refuse "CELL_ID required"
[ -n "${FAULT:-}" ] || refuse "FAULT required"
[ -n "${FIXTURE:-}" ] || refuse "FIXTURE required"

if [ "$VALIDATE_ONLY" != 1 ]; then
  [ -n "${SERIAL:-}" ] || refuse "SERIAL required for live mode"
fi

WAIT_S="${WAIT_S:-$FROZEN_WAIT_S}"
if [ "$WAIT_S" != "$FROZEN_WAIT_S" ]; then
  refuse "WAIT_S must be $FROZEN_WAIT_S got=$WAIT_S"
fi

token_ok() {
  local v=$1
  case "$v" in
    ''|*[[:space:]]*|*,*|*/*|*..*) return 1;;
  esac
  return 0
}

token_ok "$CELL_ID" || refuse "CELL_ID must be a single token got=$CELL_ID"
token_ok "$FAULT" || refuse "FAULT must be a single token got=$FAULT"
token_ok "$FIXTURE" || refuse "FIXTURE must be a single token got=$FIXTURE"

case "$CELL_ID" in
  r7-11) ;;
  r7-01|r7-02|r7-03|r7-04|r7-05|r7-06|r7-07|r7-08|r7-09|r7-10|r7-p1|r7-p2)
    refuse "CELL_ID=$CELL_ID is not this dedicated R7-11 runner; use run-r7-one-cell-a07d66c.sh or a dedicated packet";;
  r7-04-requalification-01|r7-05-requalification-01)
    refuse "CELL_ID=$CELL_ID is a frozen requalification cell";;
  r7-12|r7-13|r7-14)
    refuse "CELL_ID=$CELL_ID is not authorized on this runner";;
  *) refuse "CELL_ID not r7-11 got=$CELL_ID";;
esac

ROOT="${ROOT%/}"
case "$ROOT" in
  /*) ;;
  *) refuse "ROOT must be an absolute path got=$ROOT";;
esac
ROOT_BASE="${ROOT##*/}"
if [ "$ROOT_BASE" != runtime-a07d66c ]; then
  refuse "ROOT last component must be runtime-a07d66c got=$ROOT_BASE path=$ROOT"
fi
case "$ROOT" in
  *runtime-fdfb1ce*|*runtime-7549e36*|*runtime-0d72332*|*runtime-a7528bd*|*runtime-feeaa56*)
    refuse "ROOT contains a forbidden historical runtime name got=$ROOT";;
esac

CELL="$ROOT/$CELL_ID"
export CELL

TUPLE="${CELL_ID}|${FAULT}|${FIXTURE}"
LIVE_STATUS=""
FIXTURE_BIN=""
case "$TUPLE" in
  "r7-11|serial-wrap|direct")
    LIVE_STATUS=ENABLED
    FIXTURE_BIN=p_r3_single_direct
    ;;
  *)
    refuse "CELL_ID/FAULT/FIXTURE is not the frozen R7-11 tuple got=$TUPLE"
    ;;
esac

if [ -e "$CELL" ]; then
  refuse "destination already exists path=$CELL (caller must choose a new CELL_ID; no overwrite/append/suffix)"
fi

print_plan() {
  cat <<EOF
VALIDATE_ONLY=$VALIDATE_ONLY
status=ACCEPT
live_status=$LIVE_STATUS
candidate_head=$CANDIDATE_HEAD
candidate_parent=$CANDIDATE_PARENT
ci=$CANDIDATE_CI
expect_version=$EXPECT_VERSION
expect_version_code=$EXPECT_VERSION_CODE
provenance_note=versionName/versionCode/lastUpdateTime are live package checks only; APK SHA256/signer/Build ID remain outer qualification profile
root=$ROOT
cell=$CELL
cell_id=$CELL_ID
fault=$FAULT
fixture=$FIXTURE
fixture_bin=$FIX/$FIXTURE_BIN
holder_bin=$FIX/p_b3a_hold
fixture_invocation_max=1
fixture_required=YES
holder_invocation_max=1
holder_required=YES
retry=0
auto_next=0
wait_s=$WAIT_S
judge=$JUDGE
classify=$CLASSIFY
no_serial0=YES
prior_publish_required=NO
seed_after_event35=YES
production_serial_default_unmodified=YES
early_fail_policy=fixture-required-wrap
died_during_8s_without_fixture=INVALID
injection_reachability=YES_GATEA_DIRECT_PUBLISH_RECT
env_capture=immediate_on_pid_discovery_before_maps
exit_signal_note=EXIT_SIGNAL is a logcat Fatal-signal heuristic, not waitpid; runner must not fabricate exit127
adb=0
mkdir=0
activity_launch=0
x3_launch=0
fixture_exec=0
stable_policy=read-only
hdmi_policy=observe-only
cleanup_policy=experimental X3/fixture/holder/logcat/com.waydefu.x11gpu only
env_export=TERMUX_X11_GATEA_PROTO=1 TERMUX_X11_GATEA_TELEMETRY=1 TERMUX_X11_GATEA_TEST_FAULT=$FAULT TERMUX_X11_GATEA_TEST_ARM=1
env_equality=exact set of TERMUX_X11_GATEA* from /proc/X3/environ
EOF
}

if [ "$VALIDATE_ONLY" = 1 ]; then
  print_plan
  echo "VALIDATE_ONLY_OK tuple=$TUPLE live_status=$LIVE_STATUS"
  exit 0
fi

if [ "$LIVE_STATUS" != ENABLED ]; then
  refuse "R7-11 live_status is not ENABLED tuple=$TUPLE"
fi

# shellcheck source=/dev/null
source "$ROOT_HARNESS/harness-lib.sh"
FIXPID=""
X3=""
HOLDER_PID=""
LOGCAT_PID=""
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
  local live cmd
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
  echo "fixture_bin=$FIXTURE_BIN"
  echo "fixture_invocation_max=1"
  echo "fixture_required=YES"
  echo "holder_invocation_max=1"
  echo "holder_required=YES"
  echo "retry=0"
  echo "auto_next=0"
  echo "wait_s=$WAIT_S"
  echo "expect_version=$EXPECT_VERSION"
  echo "expect_version_code=$EXPECT_VERSION_CODE"
  echo "head=$CANDIDATE_HEAD"
  echo "parent=$CANDIDATE_PARENT"
  echo "ci=$CANDIDATE_CI"
  echo "live_status=$LIVE_STATUS"
  echo "early_fail_policy=fixture-required-wrap"
  echo "no_serial0=YES"
  echo "prior_publish_required=NO"
  echo "seed_after_event35=YES"
  echo "provenance_note=versionName/versionCode/lastUpdateTime are live package checks only; APK SHA256/signer/Build ID remain outer qualification profile"
  echo "exit_signal_note=EXIT_SIGNAL is a logcat Fatal-signal heuristic, not waitpid; runner must not fabricate exit127"
} | tee "$CELL/preflight.txt"

ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'versionName=|versionCode=|lastUpdateTime=' | head -6 | tee "$CELL/installed-package.txt"
grep -q "versionName=$EXPECT_VERSION" "$CELL/installed-package.txt"
grep -q "versionCode=$EXPECT_VERSION_CODE" "$CELL/installed-package.txt"

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
python3 - "$CELL/dumpsys-activity.txt" "$CELL/activity-pid.txt" <<'PY'
from pathlib import Path
import re, sys
text = Path(sys.argv[1]).read_text(errors="replace")
m = re.search(
    r"app=ProcessRecord\{[^ ]+ (\d+):com\.waydefu\.x11gpu/",
    text,
)
if not m:
    raise SystemExit("no waydefu ProcessRecord")
Path(sys.argv[2]).write_text(f"activity_pid={m.group(1)}\n")
print(f"activity_pid={m.group(1)}")
PY

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
while IFS= read -r name; do
  [ -n "$name" ] || continue
  unset "$name" || true
done < <(env | awk -F= '/^TERMUX_X11_GATEA_/ {print $1}' || true)
unset TERMUX_X11_DEBUG || true
unset TERMUX_X11_B3A_TELEMETRY || true
export TERMUX_X11_GATEA_PROTO=1
export TERMUX_X11_GATEA_TELEMETRY=1
export TERMUX_X11_GATEA_TEST_FAULT="$FAULT"
export TERMUX_X11_GATEA_TEST_ARM=1
python3 "$RUN" | tee "$CELL/start-x3.out"

ENV_CAPTURED=0
ENV_EXACT=0
X3=""
for i in $(seq 1 200); do
  if X3=$(x3pid); then
    echo "x3_pid=$X3 cell=$CELL_ID fault=$FAULT arm=1 proto=1 telemetry=1 discovered_i=$i" | tee "$CELL/x3-pid.txt"
    {
      echo "discovered_i=$i"
      echo "socket_present_at_discovery=NO"
      if [ -S /data/data/com.termux/files/usr/tmp/.X11-unix/X3 ] || [ -S /tmp/.X11-unix/X3 ]; then
        echo "socket_present_at_discovery=YES"
      fi
    } | tee "$CELL/startup-observability.txt"
    # Environ first. Maps/identity are slower and must not win the race.
    if [ -r "/proc/$X3/environ" ]; then
      tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11' | tee "$CELL/x-environ-all-termux-x11.txt" || true
      tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11_GATEA' | tee "$CELL/x-environ-gatea.txt" || true
      ENV_CAPTURED=1
      {
        echo "x3_pid=$X3"
        tr '\0' ' ' < "/proc/$X3/cmdline" 2>/dev/null || true
        readlink "/proc/$X3/exe" 2>/dev/null || true
      } | tee "$CELL/x-identity.txt" >/dev/null
      cat "/proc/$X3/maps" > "$CELL/x3.maps" 2>/dev/null || true
      break
    fi
  fi
  sleep 0.1
done

if [ -z "$X3" ] || [ "$ENV_CAPTURED" != 1 ]; then
  echo "ENV_CAPTURE_FAILED x3=${X3:-NONE}" | tee "$CELL/env-capture.txt"
  ADB logcat -d -v threadtime -T "$SINCE" > "$CELL/logcat-dump-unfiltered.txt" || true
  echo INVALID | tee "$CELL/primary-verdict.txt"
  echo "note=cannot fabricate ENV_EXACT when /proc/X/environ was unread" | tee -a "$CELL/env-capture.txt"
  exit 9
fi

set +e
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
ENV_RC=$?
set -e
if [ "$ENV_RC" -ne 0 ]; then
  echo INVALID | tee "$CELL/primary-verdict.txt"
  echo "ENV_MISMATCH_INVALID pid=$X3" | tee -a "$CELL/env-capture.txt"
  exit 9
fi
ENV_EXACT=1
echo "ENV_CAPTURED=1 ENV_EXACT=1 pid=$X3" | tee "$CELL/env-capture.txt"

for i in $(seq 1 40); do
  if [ ! -d "/proc/$X3" ]; then
    echo "X3_DIED_BEFORE_SOCKET i=$i" | tee -a "$CELL/startup-observability.txt"
    break
  fi
  if [ -S /data/data/com.termux/files/usr/tmp/.X11-unix/X3 ] || [ -S /tmp/.X11-unix/X3 ]; then
    echo "socket_ready i=$i" | tee -a "$CELL/startup-observability.txt"
    break
  fi
  sleep 0.25
done

DIED_BEFORE_STARTUP_DEADLINE=0
FIXTURE_REACHED=0
HOLDER_REACHED=0
export DISPLAY=:3
export TMPDIR=/data/data/com.termux/files/usr/tmp
: > "$CELL/holder.out"
: > "$CELL/fixture.out"
echo "NOT_REACHED" > "$CELL/fixture-status.txt"
echo "NOT_REACHED" > "$CELL/holder-status.txt"
elapsed=0
while [ "$elapsed" -lt "$WAIT_S" ]; do
  if [ ! -d "/proc/$X3" ]; then
    echo "X3_DIED_DURING_OBSERVE elapsed=$elapsed" | tee -a "$CELL/alive.txt"
    if [ "$elapsed" -lt 8 ] && [ "$FIXTURE_REACHED" != 1 ]; then
      DIED_BEFORE_STARTUP_DEADLINE=1
      echo "died_before_startup_deadline=1 elapsed=$elapsed fixture_reached=$FIXTURE_REACHED" | tee -a "$CELL/alive.txt"
    fi
    break
  fi
  if grep -aq 'GATEA_FATAL_HALT what=x-serial-wrap reason=6' "$CELL/logcat-follow.txt" 2>/dev/null; then
    echo "EXPECTED_FATAL_SEEN elapsed=$elapsed" | tee -a "$CELL/alive.txt"
  elif [ -z "${HOLDER_PID:-}" ]; then
    "$FIX/p_b3a_hold" > "$CELL/holder.out" 2>&1 &
    HOLDER_PID=$!
    echo "$HOLDER_PID" > "$CELL/holder.pid"
    echo "holder_started elapsed=$elapsed pid=$HOLDER_PID" | tee "$CELL/holder-status.txt"
  elif grep -q 'HOLD READY' "$CELL/holder.out" 2>/dev/null; then
    HOLDER_REACHED=1
    if [ -z "${FIXPID:-}" ]; then
      set +e
      "$FIX/p_r3_single_direct" >> "$CELL/fixture.out" 2>&1 &
      FIXPID=$!
      set -e
      echo "$FIXPID" > "$CELL/fixture.pid"
      echo "fixture_started elapsed=$elapsed pid=$FIXPID" | tee "$CELL/fixture-status.txt"
      FIXTURE_REACHED=1
    fi
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
if [ -d "/proc/$X3" ]; then
  echo "X3_STILL_ALIVE pid=$X3 elapsed=$elapsed wchan=$(cat /proc/$X3/wchan 2>/dev/null || echo gone)" | tee -a "$CELL/alive.txt"
  DIED_BEFORE_STARTUP_DEADLINE=0
elif [ "$elapsed" -ge "$WAIT_S" ] && [ "$DIED_BEFORE_STARTUP_DEADLINE" != 1 ]; then
  echo "X3_DIED_AFTER_OBSERVE_WINDOW elapsed=$elapsed" | tee -a "$CELL/alive.txt"
fi
if grep -q 'HOLD READY' "$CELL/holder.out" 2>/dev/null; then
  HOLDER_REACHED=1
fi
if [ -n "${FIXPID:-}" ]; then
  FIXTURE_REACHED=1
fi

if [ -n "${FIXPID:-}" ]; then
  set +e
  kill -TERM "$FIXPID" 2>/dev/null || true
  wait "$FIXPID" 2>/dev/null
  FIX_RC=$?
  set -e
  echo "FIXTURE_EXIT=$FIX_RC" | tee "$CELL/fixture-exit.txt"
else
  echo "FIXTURE_EXIT=NOT_REACHED" | tee "$CELL/fixture-exit.txt"
fi
cat "$CELL/fixture.out" || true
cat "$CELL/holder.out" || true

if [ -f "$SUMMARY" ]; then cp -a "$SUMMARY" "$CELL/gatea-summary.txt"; else echo NONE > "$CELL/gatea-summary.txt"; fi
if [ -f "$RING" ]; then cp -a "$RING" "$CELL/gatea-ring.txt"; else echo NONE > "$CELL/gatea-ring.txt"; fi

ACT_PID=$(awk -F= '/^activity_pid=/{print $2}' "$CELL/activity-pid.txt")
{
  echo "ts=$(date -Is)"
  if [ -d "/proc/$X3" ]; then echo "x_pre_cleanup=ALIVE pid=$X3"; else echo "x_pre_cleanup=DEAD pid=$X3"; fi
  if ADB shell "ps -A" | grep -q "com.waydefu.x11gpu"; then
    echo "activity_pre_cleanup=ALIVE expected_pid=$ACT_PID"
    ADB shell "ps -A" | grep "com.waydefu.x11gpu" || true
  else
    echo "activity_pre_cleanup=ABSENT expected_pid=$ACT_PID"
  fi
} | tee "$CELL/pre-cleanup-process.txt"

{
  echo "x3_pid=$X3"
  if [ -d "/proc/$X3" ]; then
    echo "x3_proc=ALIVE"
    echo "x3_cmdline=$(tr '\0' ' ' < "/proc/$X3/cmdline" 2>/dev/null || true)"
  else
    echo "x3_proc=DEAD"
  fi
  echo "note=PID-bound process existence before cleanup; Fatal-signal lines are copied below; EXIT_SIGNAL remains a logcat heuristic, not waitpid, and must not be fabricated as exit127"
  echo "===fatal_markers==="
  grep -aE 'GATEA_FATAL_HALT|Fatal signal|SIGSEGV|SIGILL|SIGABRT' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" 2>/dev/null || echo NONE
} | tee "$CELL/signal-audit.txt"

sleep 1
ADB logcat -d -v threadtime -T "$SINCE" > "$CELL/logcat-dump-unfiltered.txt" || true
{
  echo '===GATEA_EVENT==='
  grep -a GATEA_EVENT "$CELL/logcat-follow.txt" || echo NONE
  echo '===FAULT_HALT==='
  grep -aE 'GATEA_FATAL_HALT|GATEA_SUMMARY|GATEA_HUP_PRESERVE|TEST_FAULT|x-test-fault-env' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===Gcomp==='
  grep -aE 'Gcomp Done|x-exa-composite-wait|x-present-copy-wait|x-direct-not-success' "$CELL/logcat-follow.txt" "$CELL/logcat-dump-unfiltered.txt" || echo NONE
  echo '===signal==='
  grep -aE 'Fatal signal|SIGSEGV|SIGILL|SIGABRT' "$CELL/logcat-follow.txt" "$CELL/logcat-dump-unfiltered.txt" || echo NONE
} | tee "$CELL/telemetry-fatal.txt"

X_ALIVE=0
grep -q 'X3_STILL_ALIVE' "$CELL/alive.txt" 2>/dev/null && X_ALIVE=1
if [ ! -d "/proc/$X3" ]; then
  X_ALIVE=0
fi

set +e
python3 "$CLASSIFY" \
  --follow "$CELL/logcat-follow.txt" \
  --dump "$CELL/logcat-dump-unfiltered.txt" \
  --ring "$CELL/gatea-ring.txt" \
  --summary "$CELL/gatea-summary.txt" \
  --x-alive "$X_ALIVE" \
  --env-captured "$ENV_CAPTURED" \
  --env-exact "$ENV_EXACT" \
  --died-before-startup-deadline "$DIED_BEFORE_STARTUP_DEADLINE" \
  --fixture-reached "$FIXTURE_REACHED" \
  --holder-reached "$HOLDER_REACHED" \
  --out "$CELL/serial-wrap-classify.txt"
CL_RC=$?
set -e
echo "classify_rc=$CL_RC died_before_startup_deadline=$DIED_BEFORE_STARTUP_DEADLINE x_alive=$X_ALIVE fixture_reached=$FIXTURE_REACHED holder_reached=$HOLDER_REACHED" | tee "$CELL/serial-wrap-classify.rc"

test "$(stabpid)" = "$STABLE_PRE"
test "$(stab_cmd)" = "$STABLE_CMD_PRE"

stop_logcat "$LOGCAT_PID" || true
LOGCAT_PID=""
if [ -n "${HOLDER_PID:-}" ]; then
  kill -TERM "$HOLDER_PID" 2>/dev/null || true
  wait "$HOLDER_PID" 2>/dev/null || true
  HOLDER_PID=""
fi
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

if grep -q '^runner_invalid=YES' "$CELL/serial-wrap-classify.txt"; then
  echo INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
fi

EXIT_SIGNAL=0
if grep -aEq 'Fatal signal (11|6|4)|SIGSEGV|SIGILL|SIGABRT' "$CELL/logcat-follow.txt" "$CELL/logcat-dump-unfiltered.txt" 2>/dev/null; then
  if ! grep -aq 'GATEA_FATAL_HALT' "$CELL/logcat-follow.txt" "$CELL/logcat-dump-unfiltered.txt" 2>/dev/null; then
    EXIT_SIGNAL=11
  fi
fi
{
  echo "exit_signal_heuristic=$EXIT_SIGNAL"
  echo "x_alive=$X_ALIVE"
  echo "note=EXIT_SIGNAL is a logcat Fatal-signal heuristic, not waitpid status; not fabricated as exit127"
} | tee -a "$CELL/signal-audit.txt"

set +e
python3 "$JUDGE" "$FAULT" "$CELL/logcat-follow.txt" \
  --ring "$CELL/gatea-ring.txt" \
  --summary "$CELL/gatea-summary.txt" \
  --x-alive "$X_ALIVE" \
  --exit-signal "$EXIT_SIGNAL" | tee "$CELL/judge.txt"
JRC=${PIPESTATUS[0]}
set -e
{
  echo "judge=$JUDGE"
  echo "fault=$FAULT"
  echo "follow=$CELL/logcat-follow.txt"
  echo "ring=$CELL/gatea-ring.txt"
  echo "summary=$CELL/gatea-summary.txt"
  echo "x_alive=$X_ALIVE"
  echo "exit_signal=$EXIT_SIGNAL"
  echo "judge_rc=$JRC"
} | tee "$CELL/judge-cmd.txt"

python3 - "$CELL" "$FAULT" <<'PY'
from pathlib import Path
import re, sys
cell = Path(sys.argv[1])
fault = sys.argv[2]
follow = (cell/'logcat-follow.txt').read_text(errors='replace')
dump = (cell/'logcat-dump-unfiltered.txt').read_text(errors='replace')
ring = (cell/'gatea-ring.txt').read_text(errors='replace')
blob = follow + '\n' + dump + '\n' + (cell/'gatea-summary.txt').read_text(errors='replace')
blob += '\n' + (cell/'fixture.out').read_text(errors='replace')
pat = re.compile(
    r"GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) "
    r"serial=(\d+) src=(\d+) dst=(\d+)"
)
by = {}
for m in pat.finditer(follow + "\n" + dump + "\n" + ring):
    rec = dict(seq=int(m.group(1)), role=int(m.group(2)), event=int(m.group(3)),
               gen=int(m.group(4)), serial=int(m.group(5)), src=int(m.group(6)),
               dst=int(m.group(7)))
    by[rec["seq"]] = rec
events = [by[k] for k in sorted(by)]
serial0 = [e for e in events if e["event"] == 6 and e["serial"] == 0]
pub_all = [e for e in events if e["event"] == 6]
faults = [e for e in events if e["event"] == 35]
halts = re.findall(r'GATEA_FATAL_HALT what=(\S+) reason=(\d+)', blob)
hup_preserve = re.findall(r'GATEA_HUP_PRESERVE[^\n]*', blob)
gcomp_done = len(re.findall(r'Gcomp Done', blob))
timeout_done = len(re.findall(r'timeout.?Done|EXA GPU composite wait timeout[\s\S]{0,80}Gcomp Done', blob, re.I))
exa_to = len(re.findall(r'x-exa-composite-wait|EXA GPU composite wait timeout', blob))
(cell/'forbidden-audit.txt').write_text(
    f"fault={fault}\n"
    f"event35_count={len(faults)}\n"
    f"halts={halts}\n"
    f"hup_preserve={hup_preserve}\n"
    f"gcomp_done={gcomp_done}\n"
    f"exa_timeout={exa_to}\n"
    f"timeout_to_done_loose={timeout_done}\n"
    f"publish_serial0={len(serial0)}\n"
    f"publish_all={len(pub_all)}\n"
    f"fixture_pass={'RESULT p_r3_single_direct PASS' in blob or 'CLIENT_OK' in blob}\n"
    f"fixture_required=YES\n"
    f"fixture_pass_required=NO\n"
)
oracle = "FAIL" if serial0 else "PASS"
(cell/'no-serial0-oracle.txt').write_text(
    f"publish_event6_serial0={len(serial0)}\n"
    f"publish_event6_all={len(pub_all)}\n"
    f"serial0_events={serial0}\n"
    f"oracle={oracle}\n"
)
(cell/'serial-state-audit.txt').write_text(
    "counter_before_hook=source-proven X-local gpuCopySerialCounter; "
    "C static zero-init default 0; legacy COPY/SOLID ++ sites do not consume "
    "serial-wrap and are not device-observed here\n"
    "event35=lorieGateATestFaultConsume CAS consumed 0->1 then EVENT 35 "
    "role=X serial_arg=0 cell=11; does not allocate a serial\n"
    "seed_action=source-proven pvfb->gpuCopySerialCounter=UINT64_MAX only if consume returned 1\n"
    "seed_value_device_observed=NOT_AVAILABLE\n"
    "next_increment=source-proven ++gpuCopySerialCounter immediately after seed\n"
    "wrap_detection=source-proven if (++counter == 0) gateAXFatal x-serial-wrap FAIL_GENERATION\n"
    "fatal=GATEA_FATAL_HALT what=x-serial-wrap reason=6\n"
    "publish_after_wrap=unreachable; gateAXFatal is noreturn before entry->serial and EVENT_PUBLISH\n"
    f"device_observed_publish_serial0={len(serial0)}\n"
    "do_not_invent_observed_UINT64_MAX=YES\n"
)
print('audit', (cell/'forbidden-audit.txt').read_text())
print('no-serial0', (cell/'no-serial0-oracle.txt').read_text())
PY

if grep -q '^product_fail=YES' "$CELL/serial-wrap-classify.txt"; then
  echo FAIL | tee "$CELL/primary-verdict.txt"
  exit 2
fi
if grep -q '^publish_event6_serial0=' "$CELL/no-serial0-oracle.txt" && grep -q '^oracle=FAIL' "$CELL/no-serial0-oracle.txt"; then
  echo FAIL | tee "$CELL/primary-verdict.txt"
  exit 2
fi
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
