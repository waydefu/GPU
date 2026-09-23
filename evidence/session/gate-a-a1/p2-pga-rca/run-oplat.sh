#!/usr/bin/env bash
# RCA-XFCE-3 / PGA-GAP-2 instrument runner - product bfb5769. NOT a qualification cell.
# Captures tests/pga/p_oplat.c (per-operation X latency) against the untraced experimental
# X on :3, in one of two product modes (same APK, only X's environment differs):
#   MODE G   TERMUX_X11_GATEA_PROTO=1              production GPU config
#   MODE C   TERMUX_X11_DISABLE_EXA_GPU=1          every EXA op on the CPU (the control)
# No telemetry, no R8 arm (a per-event liblog write would distort the timings). X is ended
# with SIGTERM by exact pid after the instrument exits - CONSTRUCTION, recorded in x-end.txt.
# Derived from p2-b3-runtime/run-b3.sh (same guards: APK sha, Stable before/after, screen
# awake + unlocked, untraced X3, exact-pid kill, host resources).
#   MODE · EVIDENCE (must not exist) · SERIAL (live 5038-lane serial) · VALIDATE_ONLY=1
# exit 3 BLOCKED (not consumed) · 2 INVALID capture · 0 captured
set -euo pipefail
ROOT=/root/projects/GPU加速
PGA=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/pga
SAFE=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/common/safe-run.sh
ROOT_HARNESS=$ROOT/evidence/session/gate-a-a1/p2-r3-terminal-runtime
RUN_UNTRACED=$ROOT/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3-untraced.sh
FIXTURE_SRC=$PGA/p_oplat.c
FIXTURE=/tmp/p_oplat
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
EXPECT_PACKAGE=com.waydefu.x11gpu
EXPECT_VERSION=1.03.01-bfb5769-23.09.26
EXPECT_APK_SHA256=ff7b9309c405b07245bc352911867a66e8498464e515e09dbd645b3a1ec18472
EXPECT_ROOT=1200x2191

refuse() { echo "OPLAT_BLOCKED $*"; [ -n "${EVIDENCE:-}" ] && [ -d "$EVIDENCE" ] && echo "$*" > "$EVIDENCE/BLOCKED.txt"; exit 3; }
invalid() { echo "OPLAT_INVALID $*"; echo "$*" > "$EVIDENCE/INVALID-CAPTURE.txt"; exit 2; }
MODE="${MODE:-}"; EVIDENCE="${EVIDENCE:-}"
case "$MODE" in G|C) ;; *) refuse "bad_mode '$MODE'";; esac
[ -n "$EVIDENCE" ] || refuse "EVIDENCE"
if [ "${VALIDATE_ONLY:-0}" = 1 ]; then echo "OPLAT_RUNNER_VALIDATE_ONLY mode=$MODE fixture_src=$(sha256sum "$FIXTURE_SRC" | cut -c1-12)"; exit 0; fi
[ -n "${SERIAL:-}" ] || refuse "SERIAL"
[ -e "$EVIDENCE" ] && refuse "evidence_exists"
"$SAFE" --disk-min-gb 15 --disk-path "$(dirname "$EVIDENCE")" --floor-mb 4500 --check-only || refuse "host_resources"
cc -O2 -Wall -o "$FIXTURE" "$FIXTURE_SRC" -lxcb -lxcb-render || refuse "fixture_build"

export CELL="$EVIDENCE"
# shellcheck source=/dev/null
source "$ROOT_HARNESS/harness-lib.sh"
ADB get-state >/dev/null 2>&1 || refuse "ADB_DISCONNECTED"
ADB devices | grep -qF "$SERIAL" || refuse "serial_not_verbatim"
mkdir -p "$EVIDENCE"
sha256sum "$0" "$FIXTURE_SRC" "$FIXTURE" "$SAFE" > "$EVIDENCE/tools.sha256.txt"
X3=""; XEND=""
b_cleanup() {
  if [ -n "${X3:-}" ] && [ -d "/proc/$X3" ]; then
    local cmd; cmd=$(tr '\0' ' ' < "/proc/$X3/cmdline" 2>/dev/null || true)
    case "$cmd" in "termux-x11gpu com.waydefu.x11gpu :3"*) kill -TERM "$X3" 2>/dev/null || true
      echo "cleanup_sigterm_x3 pid=$X3 cmd=$cmd" >> "$EVIDENCE/cleanup.txt";; esac
  fi
  ADB shell am force-stop "$EXPECT_PACKAGE" </dev/null >/dev/null 2>&1 || true
}
MG=""
# our own child, exact pid. Every step tolerates failure: under set -e a failing kill of an
# already-exited guard ended the runner after its capture (oracle-02, 2026-09-23).
mg_stop() { if [ -n "${MG:-}" ]; then kill "$MG" 2>/dev/null || true; wait "$MG" 2>/dev/null || true; fi; MG=""; return 0; }
trap 'cleanup; b_cleanup; mg_stop' EXIT
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
           "versionCode":int(g(r"versionCode=(\d+)")) if g(r"versionCode=(\d+)") else None,
           "lastUpdateTime":(g(r"lastUpdateTime=(.+)") or "").strip() or None},open(sys.argv[1],"w"),indent=2)
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

unset TERMUX_X11_GATEA_PROTO TERMUX_X11_GATEA_TELEMETRY TERMUX_X11_R8_ARM TERMUX_X11_R8_CASE \
      TERMUX_X11_DISABLE_EXA_GPU TERMUX_X11_P2A_DIAG
case "$MODE" in
  G) export TERMUX_X11_GATEA_PROTO=1;;
  C) export TERMUX_X11_DISABLE_EXA_GPU=1;;
esac
env | grep -E '^TERMUX_X11_' | sort > "$EVIDENCE/env-x3.txt" || : > "$EVIDENCE/env-x3.txt"
rm -f "$SUMMARY" "$RING" || true
LLOG=/data/data/com.termux/files/usr/tmp/x3-launch-oplat-$MODE-$$.log
X3_LAUNCH_LOG=$LLOG bash "$RUN_UNTRACED" >> "$EVIDENCE/start-x3.out" 2>&1 || refuse "untraced_launch_failed"
for i in $(seq 1 40); do X3=$(x3pid_now) && break || sleep 0.5; done
[ -n "$X3" ] || invalid "x3_missing"
echo "x3_pid=$X3" > "$EVIDENCE/x3-pid.txt"
grep -E 'TracerPid|PPid' "/proc/$X3/status" > "$EVIDENCE/x3-tracer.txt" || true
grep -q 'TracerPid:[[:space:]]*0$' "$EVIDENCE/x3-tracer.txt" || refuse "x3_traced"
# memory watchdog (INCIDENT-20260923-2-LMK-B3-S): trips -> X3 SIGTERM + force-stop -> exit 5 below
MEMGUARD=/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests/common/mem-guard.sh
"$MEMGUARD" --x3-pid "$X3" --log "$EVIDENCE/mem-guard.log" --flag "$EVIDENCE/MEM-GUARD-TRIPPED.txt" \
  --serial "$SERIAL" --floor-mb 3000 --swap-growth-mb 1536 --x3-max-mb 3072 </dev/null &
MG=$!
sha256sum "$MEMGUARD" >> "$EVIDENCE/tools.sha256.txt"
ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' >> "$EVIDENCE/am-start.out" 2>&1
sleep 6
ACT=$(act_pid_now) || ACT=""; [ -n "$ACT" ] || invalid "activity_missing"
echo "activity_pid=$ACT" > "$EVIDENCE/activity-pid.txt"
[ -d "/proc/$X3" ] || invalid "x3_startup_crash"
DISPLAY=:3 xdpyinfo > "$EVIDENCE/xdpyinfo.txt" 2>&1 || true
DIMS=$(sed -n 's/^  dimensions: *\([0-9]*x[0-9]*\) pixels.*/\1/p' "$EVIDENCE/xdpyinfo.txt")
echo "x_root=$DIMS" > "$EVIDENCE/x-root.txt"
[ "$DIMS" = "$EXPECT_ROOT" ] || refuse "x_root_size $DIMS"
ADB shell dumpsys thermalservice </dev/null > "$EVIDENCE/thermal-pre.txt" 2>&1 || true
# display refresh: the renderer paces on Choreographer, so the frame period is a covariate
ADB shell dumpsys display </dev/null 2>/dev/null | tr -d '\r' | grep -m4 -E 'mRefreshRate|renderFrameRate|mActiveSfDisplayMode|mActiveRenderFrameRate' > "$EVIDENCE/display-refresh.txt" || true
XT0=$(awk '{print $14+$15}' "/proc/$X3/stat" 2>/dev/null || echo null)

set +e
DISPLAY=:3 timeout 1800 "$FIXTURE" --rounds "${ROUNDS:-10}" --reps 10 --seed 20260923 > "$EVIDENCE/oplat.out" 2>&1
echo "fixture_rc=$?" > "$EVIDENCE/fixture-rc.txt"
set -e
XT1=$(awk '{print $14+$15}' "/proc/$X3/stat" 2>/dev/null || echo null)
echo "x_cpu_ticks_before=$XT0 x_cpu_ticks_after=$XT1" > "$EVIDENCE/x-cpu.txt"
ADB shell dumpsys thermalservice </dev/null > "$EVIDENCE/thermal-post.txt" 2>&1 || true
echo "activity_pid_before_end=$(act_pid_now || true)" > "$EVIDENCE/activity-pid-before-end.txt"
X_ALIVE_AFTER_FIXTURE=false; [ -d "/proc/$X3" ] && X_ALIVE_AFTER_FIXTURE=true
echo "x_alive_after_fixture=$X_ALIVE_AFTER_FIXTURE" > "$EVIDENCE/x-end.txt"
if [ -d "/proc/$X3" ]; then
  { echo "end=SIGTERM (construction) target_pid=$X3"; tr '\0' ' ' < "/proc/$X3/cmdline"; echo; } >> "$EVIDENCE/x-end.txt"
  kill -TERM "$X3" 2>/dev/null || true
  for i in $(seq 1 20); do [ -d "/proc/$X3" ] || break; sleep 0.5; done
fi
screen_json "$EVIDENCE/screen-post.json"
sleep 1
LA=false; [ -n "$LOGCAT_PID" ] && [ -d "/proc/$LOGCAT_PID" ] && LA=true
echo "{\"logcat_alive\": $LA}" > "$EVIDENCE/capture-end.json"
stop_logcat "$LOGCAT_PID" || true; LOGCAT_PID=""
stable_json "$EVIDENCE/stable-after.json"
cp -a "$LLOG" "$EVIDENCE/x3-launcher.log" 2>/dev/null || true
(cd "$EVIDENCE" && find . -type f ! -name sha256sums.txt | sort | xargs sha256sum > sha256sums.txt)
mg_stop
if [ -e "$EVIDENCE/MEM-GUARD-TRIPPED.txt" ]; then
  (cd "$EVIDENCE" && find . -type f ! -name sha256sums.txt | sort | xargs sha256sum > sha256sums.txt)
  echo "OPLAT_ABORTED_MEM_GUARD evidence=$EVIDENCE $(head -1 "$EVIDENCE/MEM-GUARD-TRIPPED.txt")"
  exit 5
fi
echo "OPLAT_CAPTURED mode=$MODE evidence=$EVIDENCE cases=$(grep -c '^OPLAT ' "$EVIDENCE/oplat.out")"
