#!/usr/bin/env bash
# abb27a65-only dedicated R7-P1 runner. Experimental :3 only.
# Does NOT authorize device execution, APK install, or runtime-abb27a65/r7-p1 mkdir
# from VALIDATE_ONLY. Live mode needs a separate single-cell grant.
# Does NOT retry. Does NOT run R7-P2 or any earlier R7 cell.
# Does NOT overwrite evidence. Frozen judge-r7.py is used unmodified.
# 2000 ms Present wait / ABI / selector unchanged. WAIT_S=12 is observation only.
# Historical a07d66c generic runner stays REVIEW_REQUIRED for r7-p1 and is not lifted.
# Usage (live, requires a new grant AND installed abb27a65 artifact):
#   SERIAL=... ROOT=.../runtime-abb27a65 \
#     CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present WAIT_S=12 \
#     bash run-r7-p1-abb27a65.sh
# Usage (host validation):
#   VALIDATE_ONLY=1 ROOT=.../runtime-abb27a65 \
#     CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present WAIT_S=12 \
#     bash run-r7-p1-abb27a65.sh
set -euo pipefail

HERE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime
ROOT_HARNESS=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
JUDGE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py
CLASSIFY="$HERE/scripts/classify_r7_p1_abb27a65.py"
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
EXPECT_SHA=abb27a65b029b16837fe178624a85ac18a4ba005
EXPECT_VERSION=1.03.01-abb27a6-17.09.26
EXPECT_VERSION_CODE=15
EXPECT_PACKAGE=com.waydefu.x11gpu
EXPECT_BUILD_ID=7362d978c058ee2dac4cc8e60812dc3b3785f452
EXPECT_APK_SHA256=b7baa1df5d7541efb993bf38f728846996b9c1601ad34b7f8eadd8128aa99d99
EXPECT_SIGNER=b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1
CANDIDATE_HEAD=abb27a65b029b16837fe178624a85ac18a4ba005
CANDIDATE_PARENT=8545b26b308aa60b05685f48560285350e22ee8d
CANDIDATE_CI=35253641841
FROZEN_WAIT_S=12
ALLOWED_CELL=r7-p1
ALLOWED_FAULT=present-hold-complete
ALLOWED_FIXTURE=present
ALLOWED_ROOT_BASE=runtime-abb27a65

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

if [ "$CELL_ID" != "$ALLOWED_CELL" ]; then
  refuse "CELL_ID must be $ALLOWED_CELL only got=$CELL_ID"
fi
if [ "$FAULT" != "$ALLOWED_FAULT" ]; then
  refuse "FAULT must be $ALLOWED_FAULT only got=$FAULT"
fi
if [ "$FIXTURE" != "$ALLOWED_FIXTURE" ]; then
  refuse "FIXTURE must be $ALLOWED_FIXTURE only got=$FIXTURE"
fi

ROOT="${ROOT%/}"
case "$ROOT" in
  /*) ;;
  *) refuse "ROOT must be an absolute path got=$ROOT";;
esac
ROOT_BASE="${ROOT##*/}"
if [ "$ROOT_BASE" != "$ALLOWED_ROOT_BASE" ]; then
  refuse "ROOT last component must be $ALLOWED_ROOT_BASE got=$ROOT_BASE path=$ROOT"
fi
case "$ROOT" in
  *runtime-a07d66c*|*runtime-fdfb1ce*|*runtime-7549e36*|*runtime-0d72332*|*runtime-a7528bd*|*runtime-feeaa56*|*runtime-8545b26*)
    refuse "ROOT contains a forbidden historical runtime name got=$ROOT";;
esac

CELL="$ROOT/$CELL_ID"
export CELL

TUPLE="${CELL_ID}|${FAULT}|${FIXTURE}"
LIVE_STATUS=ENABLED
FIXTURE_BIN=p_r6_d2_present
if [ "$TUPLE" != "${ALLOWED_CELL}|${ALLOWED_FAULT}|${ALLOWED_FIXTURE}" ]; then
  refuse "CELL_ID/FAULT/FIXTURE is not the abb27a65 R7-P1 tuple got=$TUPLE"
fi

print_plan() {
  cat <<EOF
VALIDATE_ONLY=$VALIDATE_ONLY
status=ACCEPT
live_status=$LIVE_STATUS
candidate_head=$CANDIDATE_HEAD
expect_sha=$EXPECT_SHA
candidate_parent=$CANDIDATE_PARENT
ci=$CANDIDATE_CI
expect_package=$EXPECT_PACKAGE
expect_version=$EXPECT_VERSION
expect_version_code=$EXPECT_VERSION_CODE
expect_build_id=$EXPECT_BUILD_ID
expect_apk_sha256=$EXPECT_APK_SHA256
expect_signer=$EXPECT_SIGNER
provenance_note=live dumpsys checks package/versionName/versionCode only; APK SHA256/signer/Build ID/CI/source SHA remain outer device-grant profile and must not be inferred from versionName alone
install_policy=this runner never installs; abb27a65 must already be INSTALLED by a separate grant; no new pm install
root=$ROOT
cell=$CELL
cell_id=$CELL_ID
fault=$FAULT
fixture=$FIXTURE
fixture_bin=$FIX/$FIXTURE_BIN
holder_bin=$FIX/p_b3a_hold
holder_invocation_max=1
holder_required=YES
holder_reason=keep experimental :3 mapped so surfaceAvailable stays true through the 2000 ms Present wait; not a direct-cell buffer owner
fixture_sha256=fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86
fixture_invocation_max=1
retry=0
auto_next=0
r7_p2=0
fault12_trigger=0
wait_s=$WAIT_S
timeout_ms=2000
timeout_policy=P1 requires genuine live-peer x-present-copy-wait/4; x-hup/6 with a live renderer is PRODUCT FAIL; WAIT_S=12 is observation only; product timeout stays 2000 ms
classifier=$CLASSIFY
judge=$JUDGE
judge_args=FAULT follow ring summary x-alive exit-signal
judge_mutation=0
timeout_mutation=0
source_mutation=0
historical_root_write=0
exit_signal_note=EXIT_SIGNAL is a logcat Fatal-signal heuristic, not waitpid; runner must not fabricate exit127
adb=0
mkdir=0
activity_launch=0
x3_launch=0
holder_exec=0
fixture_exec=0
r7_p1_trigger=0
r7_p2=0
stable_policy=read-only
hdmi_policy=observe-only
cleanup_policy=experimental X3/fixture/holder/logcat/com.waydefu.x11gpu only
env_export=TERMUX_X11_GATEA_PROTO=1 TERMUX_X11_GATEA_TELEMETRY=1 TERMUX_X11_GATEA_TEST_FAULT=$FAULT TERMUX_X11_GATEA_TEST_ARM=1
env_equality=exact set of TERMUX_X11_GATEA* from /proc/X3/environ
hup_precedence=SUCCESS wins; published generationFatal!=0 wins; peer HUP + no success + no published fatal → x-hup/6; live peer genuine Present timeout → x-present-copy-wait/4
EOF
}

if [ "$VALIDATE_ONLY" = 1 ]; then
  print_plan
  echo "VALIDATE_ONLY_OK tuple=$TUPLE live_status=$LIVE_STATUS candidate=$EXPECT_SHA"
  exit 0
fi

if [ -e "$CELL" ]; then
  refuse "destination already exists path=$CELL (no overwrite/append/suffix; historical runtime-8545b26/r7-p1 and runtime-a07d66c/* must stay frozen)"
fi

if [ "$LIVE_STATUS" != ENABLED ]; then
  refuse "SUPPORTED_BY_MAPPING_BUT_REQUIRES_PACKET_REVIEW cell=$CELL_ID tuple=$TUPLE"
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
  echo "holder_invocation_max=1"
  echo "retry=0"
  echo "auto_next=0"
  echo "wait_s=$WAIT_S"
  echo "expect_package=$EXPECT_PACKAGE"
  echo "expect_version=$EXPECT_VERSION"
  echo "expect_version_code=$EXPECT_VERSION_CODE"
  echo "expect_sha=$EXPECT_SHA"
  echo "expect_build_id=$EXPECT_BUILD_ID"
  echo "expect_apk_sha256=$EXPECT_APK_SHA256"
  echo "expect_signer=$EXPECT_SIGNER"
  echo "head=$CANDIDATE_HEAD"
  echo "parent=$CANDIDATE_PARENT"
  echo "ci=$CANDIDATE_CI"
  echo "live_status=$LIVE_STATUS"
  echo "timeout_ms=2000"
  echo "timeout_policy=this cell requires x-present-copy-wait/4 with renderer alive; x-hup/6 is not a valid P1 terminal"
  echo "provenance_note=versionName/versionCode/lastUpdateTime are live package checks only; APK SHA256/signer/Build ID remain outer qualification profile"
  echo "exit_signal_note=EXIT_SIGNAL is a logcat Fatal-signal heuristic, not waitpid; runner must not fabricate exit127"
} | tee "$CELL/preflight.txt"

ADB shell dumpsys package "$EXPECT_PACKAGE" | grep -E 'Package \[|versionName=|versionCode=|lastUpdateTime=' | head -8 | tee "$CELL/installed-package.txt"
grep -q "Package \\[$EXPECT_PACKAGE\\]" "$CELL/installed-package.txt"
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
echo "env_captured=1" | tee "$CELL/env-exact-status.txt"
echo "env_exact=1" | tee -a "$CELL/env-exact-status.txt"

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

ACT_PID=$(awk -F= '/^activity_pid=/{print $2}' "$CELL/activity-pid.txt")
{
  echo "activity_pid=$ACT_PID"
  echo "x3_pid=$X3"
  ADB shell "ps -T -A" | grep -E "com.waydefu.x11gpu|gles-renderer" || true
} | tee "$CELL/runtime-threads-pre-trigger.txt"

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

EXPECT_PRESENT_SHA=fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86
GOT_PRESENT_SHA=$(sha256sum "$FIX/p_r6_d2_present" | awk '{print $1}')
if [ "$GOT_PRESENT_SHA" != "$EXPECT_PRESENT_SHA" ]; then
  echo "REFUSE present fixture SHA mismatch got=$GOT_PRESENT_SHA need=$EXPECT_PRESENT_SHA"
  echo INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
fi
echo "fixture_sha256=$GOT_PRESENT_SHA" | tee "$CELL/fixture.sha256.txt"
: > "$CELL/fixture.out"
: > "$CELL/renderer-liveness.txt"
set +e
"$FIX/p_r6_d2_present" inflight >> "$CELL/fixture.out" 2>&1 &
FIXPID=$!
echo "$FIXPID" > "$CELL/fixture.pid"
elapsed=0
RENDERER_ALIVE_DURING=0
while [ "$elapsed" -lt "$WAIT_S" ]; do
  if [ -n "${ACT_PID:-}" ] && [ -d "/proc/$ACT_PID" ] && [ -d "/proc/$X3" ]; then
    RENDERER_ALIVE_DURING=1
    echo "ts=$(date -Is) x3=ALIVE activity=$ACT_PID ALIVE" >> "$CELL/renderer-liveness.txt"
  elif [ -n "${ACT_PID:-}" ] && [ -d "/proc/$ACT_PID" ]; then
    echo "ts=$(date -Is) x3=DEAD activity=$ACT_PID ALIVE" >> "$CELL/renderer-liveness.txt"
  else
    echo "ts=$(date -Is) activity=ABSENT" >> "$CELL/renderer-liveness.txt"
  fi
  if [ ! -d "/proc/$X3" ]; then
    echo "X3_DIED_AFTER_TRIGGER elapsed=$elapsed" | tee -a "$CELL/alive.txt"
    break
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
echo "renderer_alive_during=$RENDERER_ALIVE_DURING" | tee -a "$CELL/renderer-liveness.txt"
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
{
  echo "exit_signal_heuristic=$EXIT_SIGNAL"
  echo "x_alive=$X_ALIVE"
  echo "note=EXIT_SIGNAL is a logcat Fatal-signal heuristic, not waitpid status; not fabricated as exit127"
} | tee -a "$CELL/signal-audit.txt"

ENV_CAPTURED=1
ENV_EXACT=1
ACT_PRE=0
grep -q 'activity_pre_cleanup=ALIVE' "$CELL/pre-cleanup-process.txt" && ACT_PRE=1
RENDERER_ALIVE_DURING=0
grep -q '^renderer_alive_during=1' "$CELL/renderer-liveness.txt" && RENDERER_ALIVE_DURING=1
set +e
python3 "$CLASSIFY" \
  --mode r7-p1-cell \
  --follow "$CELL/logcat-follow.txt" \
  --dump "$CELL/logcat-dump-unfiltered.txt" \
  --ring "$CELL/gatea-ring.txt" \
  --summary "$CELL/gatea-summary.txt" \
  --env-captured "$ENV_CAPTURED" \
  --env-exact "$ENV_EXACT" \
  --renderer-alive "$RENDERER_ALIVE_DURING" \
  --activity-pre-cleanup "$ACT_PRE" \
  --out "$CELL/r7-p1-classify.txt"
CL_RC=$?
set -e
echo "classify_rc=$CL_RC" | tee "$CELL/r7-p1-classify.rc"

if grep -q '^runner_invalid=YES' "$CELL/r7-p1-classify.txt"; then
  echo INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
fi

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
blob = (cell/'logcat-follow.txt').read_text(errors='replace')
blob += '\n' + (cell/'logcat-dump-unfiltered.txt').read_text(errors='replace')
blob += '\n' + (cell/'gatea-summary.txt').read_text(errors='replace')
blob += '\n' + (cell/'fixture.out').read_text(errors='replace')
halts = re.findall(r'GATEA_FATAL_HALT what=(\S+) reason=(\d+)', blob)
hup_preserve = re.findall(r'GATEA_HUP_PRESERVE[^\n]*', blob)
faults = re.findall(r'GATEA_EVENT seq=(\d+) role=(\d+) event=35 ', blob)
gcomp_done = len(re.findall(r'Gcomp Done', blob))
timeout_done = len(re.findall(r'timeout.?Done|EXA GPU composite wait timeout[\s\S]{0,80}Gcomp Done', blob, re.I))
exa_to = len(re.findall(r'x-exa-composite-wait|EXA GPU composite wait timeout', blob))
unique = []
for rec in halts:
    if rec not in unique:
        unique.append(rec)
xhup = sum(1 for w, r in unique if w == 'x-hup')
direct4 = sum(1 for w, r in unique if w == 'x-direct-not-success' and r == '4')
exa4 = sum(1 for w, r in unique if w == 'x-exa-composite-wait' and r == '4')
present4 = sum(1 for w, r in unique if w == 'x-present-copy-wait' and r == '4')
(cell/'forbidden-audit.txt').write_text(
    f"fault={fault}\n"
    f"event35_count={len(faults)}\n"
    f"halts={halts}\n"
    f"hup_preserve={hup_preserve}\n"
    f"gcomp_done={gcomp_done}\n"
    f"exa_timeout={exa_to}\n"
    f"timeout_to_done_loose={timeout_done}\n"
    f"fixture_client_ok={'RESULT p_r6_d2_present CLIENT_OK' in blob}\n"
)
(cell/'r7-p1-oracle.txt').write_text(
    f"x_present_copy_wait_reason4={present4}\n"
    f"x_hup={xhup}\n"
    f"x_direct_not_success_reason4={direct4}\n"
    f"x_exa_composite_wait_reason4={exa4}\n"
    f"reason4_globally_forbidden=NO\n"
    f"timeout_ms=2000\n"
)
print('audit', (cell/'forbidden-audit.txt').read_text())
print('oracle', (cell/'r7-p1-oracle.txt').read_text())
PY

PRODUCT_FAIL=0
grep -q '^product_fail=YES' "$CELL/r7-p1-classify.txt" && PRODUCT_FAIL=1
ORACLE_P4=0
ORACLE_HUP=1
ORACLE_DIRECT4=1
grep -q '^x_present_copy_wait_reason4=1' "$CELL/r7-p1-oracle.txt" && ORACLE_P4=1
grep -q '^x_hup=0' "$CELL/r7-p1-oracle.txt" && ORACLE_HUP=0
grep -q '^x_direct_not_success_reason4=0' "$CELL/r7-p1-oracle.txt" && ORACLE_DIRECT4=0

if [ "$PRODUCT_FAIL" -eq 0 ] && [ "$ORACLE_P4" -eq 1 ] && [ "$ORACLE_HUP" -eq 0 ] && [ "$ORACLE_DIRECT4" -eq 0 ] \
    && [ "$JRC" -eq 0 ] && [ "$X_ALIVE" -eq 0 ] && [ "$RENDERER_ALIVE_DURING" -eq 1 ] && [ "$ACT_PRE" -eq 1 ] \
    && grep -q '^R7_PASS present-hold-complete' "$CELL/judge.txt"; then
  echo PASS | tee "$CELL/primary-verdict.txt"
  exit 0
fi
if grep -q 'x-test-fault-env' "$CELL/telemetry-fatal.txt"; then
  echo INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
fi
echo FAIL | tee "$CELL/primary-verdict.txt"
exit 2
