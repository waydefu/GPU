#!/usr/bin/env bash
# V2-QUAL-ORACLE-DIRECT runner — product bfb5769, ORACLE_FROZEN_V1. CAPTURES ONLY.
# Judgement: tests/oracle/judge-oracle.py (15 tests, 9/9 mutants killed).
#
#   EVIDENCE must not exist · SERIAL live 5038-lane serial · VALIDATE_ONLY=1 = no device use
# exit 3 BLOCKED (not consumed) · 2 INVALID capture · 0 captured
set -euo pipefail
ROOT=/root/projects/GPU加速
T=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests
ORC=$T/oracle
ROOT_HARNESS=$ROOT/evidence/session/gate-a-a1/p2-r3-terminal-runtime
RUN_UNTRACED=$ROOT/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3-untraced.sh
FREEZE=$ORC/oracle-freeze.json
FIXTURE_SRC=$ORC/p_v1_oracle.c
FIXTURE=/tmp/p_v1_oracle
TERMINATE=/tmp/p_r10_ledger
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
EXPECT_PACKAGE=com.waydefu.x11gpu
EXPECT_VERSION=1.03.01-bfb5769-23.09.26
EXPECT_APK_SHA256=ff7b9309c405b07245bc352911867a66e8498464e515e09dbd645b3a1ec18472
EXPECT_TERMINATE_SHA=2aca8ae15d536065168b3a819de1414c5520792712ea56ce254efbdde05ae50b
EXPECT_FREEZE_SHA=7bd04ec740fbd14c2f4aa2298327c71aea06c268cbe8d6c9f5eb8068623b32f7
EXPECT_FIXTURE_SRC_SHA=ac2e9cc1309a2c019f7d80f985854fe651d06e3908b5bbf9df6c57792638e141
EXPECT_JUDGE_SHA=c60da2a6fec60e4747e75b2ce6163f33e820d993747e4733f1a554e273a4a3c5
EXPECT_ROOT=1200x2191

refuse() { echo "ORACLE_BLOCKED $*"; [ -n "${EVIDENCE:-}" ] && [ -d "$EVIDENCE" ] && echo "$*" > "$EVIDENCE/BLOCKED.txt"; exit 3; }
invalid() { echo "ORACLE_INVALID $*"; echo "$*" > "$EVIDENCE/INVALID-CAPTURE.txt"; exit 2; }
EVIDENCE="${EVIDENCE:-}"; [ -n "$EVIDENCE" ] || refuse "EVIDENCE"
for pair in "$FREEZE:$EXPECT_FREEZE_SHA" "$FIXTURE_SRC:$EXPECT_FIXTURE_SRC_SHA" "$ORC/judge-oracle.py:$EXPECT_JUDGE_SHA"; do
  f=${pair%:*}; want=${pair##*:}
  [ "$(sha256sum "$f" | awk '{print $1}')" = "$want" ] || refuse "frozen_file_changed $f"
done
if [ "${VALIDATE_ONLY:-0}" = 1 ]; then echo "ORACLE_RUNNER_V1_VALIDATE_ONLY"; exit 0; fi
[ -n "${SERIAL:-}" ] || refuse "SERIAL"
[ -e "$EVIDENCE" ] && refuse "evidence_exists"
[ "$(sha256sum "$TERMINATE" | awk '{print $1}')" = "$EXPECT_TERMINATE_SHA" ] || refuse "terminate_fixture_sha"
cc -O2 -Wall -o "$FIXTURE" "$FIXTURE_SRC" -lxcb -lxcb-render || refuse "fixture_build"

export CELL="$EVIDENCE"
# shellcheck source=/dev/null
source "$ROOT_HARNESS/harness-lib.sh"
ADB get-state >/dev/null 2>&1 || refuse "ADB_DISCONNECTED"
ADB devices | grep -qF "$SERIAL" || refuse "serial_not_verbatim"
mkdir -p "$EVIDENCE"
sha256sum "$0" "$FREEZE" "$FIXTURE_SRC" "$FIXTURE" "$ORC/judge-oracle.py" "$TERMINATE" > "$EVIDENCE/tools.sha256.txt"

X3=""
o_cleanup() {
  if [ -n "${X3:-}" ] && [ -d "/proc/$X3" ]; then
    local cmd; cmd=$(tr '\0' ' ' < "/proc/$X3/cmdline" 2>/dev/null || true)
    case "$cmd" in "termux-x11gpu com.waydefu.x11gpu :3"*) kill -TERM "$X3" 2>/dev/null || true
      echo "cleanup_sigterm_x3 pid=$X3" >> "$EVIDENCE/cleanup.txt";; esac
  fi
  ADB shell am force-stop "$EXPECT_PACKAGE" </dev/null >/dev/null 2>&1 || true
}
trap 'cleanup; o_cleanup' EXIT
stable_json() {
  local out=$1 pid cmd
  pid=$(stabpid) || refuse "stable_pid"; cmd=$(stab_cmd)
  echo "$cmd" | grep -q '^termux-x11 com.termux.x11 :1' || refuse "stable_cmd"
  ADB shell dumpsys package com.termux.x11 > "$out.raw" || true
  python3 - "$out" "$out.raw" "$pid" "$cmd" <<'PYEOF'
import json,re,sys
t=open(sys.argv[2],encoding="utf-8",errors="replace").read()
g=lambda p:(re.search(p,t) or [None,None])[1]
json.dump({"pid":int(sys.argv[3]),"cmdline":sys.argv[4].strip(),"versionName":g(r"versionName=(\S+)"),
           "versionCode":int(g(r"versionCode=(\d+)")) if g(r"versionCode=(\d+)") else None,"lastUpdateTime":(g(r"lastUpdateTime=(.+)") or "").strip() or None},
          open(sys.argv[1],"w"),indent=2)
PYEOF
}
screen_json() {
  local w k
  w=$(ADB shell dumpsys power </dev/null 2>/dev/null | tr -d '\r' | grep -m1 'mWakefulness=' | sed 's/.*mWakefulness=//' || true)
  k=$(ADB shell dumpsys window </dev/null 2>/dev/null | tr -d '\r' | grep -m1 'isKeyguardShowing=' | sed 's/.*isKeyguardShowing=//' || true)
  python3 -c "import json,sys;json.dump({'wakefulness':sys.argv[1] or None,'awake':sys.argv[1]=='Awake','keyguard':None if sys.argv[2]=='' else sys.argv[2]=='true'},open(sys.argv[3],'w'))" "$w" "$k" "$1"
}
x3pid_now() {
  local p x
  for p in /proc/[0-9]*; do
    x=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$x" in "termux-x11gpu com.waydefu.x11gpu :3"*) echo "${p##*/}"; return 0;; esac
  done
  return 1
}
act_pid_now() { ADB shell pidof "$EXPECT_PACKAGE" </dev/null 2>/dev/null | tr -d '\r' | awk '{print $1}'; }

# ---- preflight
ADB shell dumpsys package "$EXPECT_PACKAGE" | grep -E 'versionName=' | head -1 \
  | tee "$EVIDENCE/experimental-package-pre.txt" | grep -q "versionName=$EXPECT_VERSION" || refuse "version_mismatch"
INSTALLED=$(ADB shell pm path "$EXPECT_PACKAGE" | tr -d '\r' | sed -n 's/^package://p' | head -1)
GOT_APK=$(ADB shell sha256sum "$INSTALLED" | tr -d '\r' | awk '{print $1}')
echo "installed_apk_sha256=$GOT_APK" > "$EVIDENCE/installed-apk.sha256.txt"
[ "$GOT_APK" = "$EXPECT_APK_SHA256" ] || refuse "apk_sha256_mismatch"
stable_json "$EVIDENCE/stable-before.json"
screen_json "$EVIDENCE/screen-pre.json"
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));sys.exit(0 if d['awake'] and d['keyguard'] is False else 1)" \
  "$EVIDENCE/screen-pre.json" || refuse "screen_not_awake_or_locked"
x3pid_now >/dev/null 2>&1 && refuse "x3_already_running"
ADB shell am force-stop "$EXPECT_PACKAGE" </dev/null >/dev/null 2>&1 || true
sleep 2
SINCE=$(date '+%m-%d %H:%M:%S.000'); echo "logcat_since=$SINCE" > "$EVIDENCE/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$EVIDENCE/raw-logcat.txt" "$SINCE"); verify_logcat_pid "$LOGCAT_PID"

# ---- X3 untraced + Activity
export TERMUX_X11_GATEA_PROTO=1 TERMUX_X11_GATEA_TELEMETRY=1 TERMUX_X11_R8_ARM=1 TERMUX_X11_R8_CASE=R8-C1
unset TERMUX_X11_P2A_DIAG TERMUX_X11_DISABLE_EXA_GPU
env | grep -E '^TERMUX_X11_' | sort > "$EVIDENCE/env-x3.txt"
rm -f "$SUMMARY" "$RING" || true
LLOG=/data/data/com.termux/files/usr/tmp/x3-launch-oracle-$$.log
X3_LAUNCH_LOG=$LLOG bash "$RUN_UNTRACED" >> "$EVIDENCE/start-x3.out" 2>&1 || refuse "untraced_launch_failed"
for i in $(seq 1 40); do X3=$(x3pid_now) && break || sleep 0.5; done
[ -n "$X3" ] || invalid "x3_missing"
echo "x3_pid=$X3" > "$EVIDENCE/x3-pid.txt"
grep -E 'TracerPid|PPid' "/proc/$X3/status" > "$EVIDENCE/x3-tracer.txt" || true
grep -q 'TracerPid:[[:space:]]*0$' "$EVIDENCE/x3-tracer.txt" || refuse "x3_traced"
ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' >> "$EVIDENCE/am-start.out" 2>&1
sleep 6
ACT=$(act_pid_now) || ACT=""; [ -n "$ACT" ] || invalid "activity_missing"
echo "activity_pid=$ACT" > "$EVIDENCE/activity-pid.txt"
[ -d "/proc/$X3" ] || invalid "x3_startup_crash"
DISPLAY=:3 xdpyinfo > "$EVIDENCE/xdpyinfo.txt" 2>&1 || true
DIMS=$(sed -n 's/^  dimensions: *\([0-9]*x[0-9]*\) pixels.*/\1/p' "$EVIDENCE/xdpyinfo.txt")
echo "x_root=$DIMS" > "$EVIDENCE/x-root.txt"
if [ "$DIMS" != "$EXPECT_ROOT" ]; then
  timeout 60 "$TERMINATE" --display :3 --mode terminate > "$EVIDENCE/terminate-blocked.out" 2>&1 || true
  refuse "x_root_size $DIMS"
fi

# ---- the oracle
set +e
DISPLAY=:3 timeout 900 "$FIXTURE" > "$EVIDENCE/oracle.out" 2>&1
echo "oracle_rc=$?" > "$EVIDENCE/oracle-rc.txt"
set -e

# ---- clean close
timeout 60 "$TERMINATE" --display :3 --mode terminate --client-log "$EVIDENCE/terminate.jsonl" \
  > "$EVIDENCE/terminate.out" 2>&1 || true
for i in $(seq 1 60); do [ -d "/proc/$X3" ] || break; sleep 0.5; done
XA=false; [ -d "/proc/$X3" ] && XA=true
echo "{\"x_alive_after_terminate\": $XA}" > "$EVIDENCE/close.json"
[ -f "$SUMMARY" ] && cp -a "$SUMMARY" "$EVIDENCE/gatea-summary.txt" || : > "$EVIDENCE/gatea-summary.txt"
[ -f "$RING" ] && cp -a "$RING" "$EVIDENCE/gatea-ring.txt" || : > "$EVIDENCE/gatea-ring.txt"
sleep 2
echo "activity_pid_after_close=$(act_pid_now || true)" > "$EVIDENCE/activity-pid-after-close.txt"
screen_json "$EVIDENCE/screen-post.json"
sleep 1
LA=false; [ -n "$LOGCAT_PID" ] && [ -d "/proc/$LOGCAT_PID" ] && LA=true
echo "{\"logcat_alive\": $LA}" > "$EVIDENCE/capture-end.json"
stop_logcat "$LOGCAT_PID" || true; LOGCAT_PID=""
stable_json "$EVIDENCE/stable-after.json"
cp -a "$LLOG" "$EVIDENCE/x3-launcher.log" 2>/dev/null || true
(cd "$EVIDENCE" && find . -type f ! -name sha256sums.txt | sort | xargs sha256sum > sha256sums.txt)
echo "ORACLE_CAPTURED evidence=$EVIDENCE"
