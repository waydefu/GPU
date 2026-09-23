#!/usr/bin/env bash
# PGA-GAP-3 requal (plan section 13.2 step 8) - product 83d45a9 (CI 35845935317). NOT a B.3 cell.
# Workload frozen in planning-v2/pga/PGA-GAP-3-DESIGN.md: B.3 mode S (PROTO unset = D0a staging)
# on tests/pga/gap3-requal-cells.tsv = N0000 + the first 20 cells of the S order (seed 1103; on
# bfb5769 the first 10 of them registered 7.4 GB and exhausted the phone, b3-s-02).
# Adds, around the fixture, the Activity maps_count via run-as (the R10 method). mem-guard runs
# as in every runner. Verdict: tests/pga/gap3_requal.py.
#   EVIDENCE (must not exist) · SERIAL · VALIDATE_ONLY=1
# exit 3 BLOCKED · 2 INVALID capture · 5 ABORTED_MEM_GUARD · 0 captured
set -euo pipefail
ROOT=/root/projects/GPU加速
B3=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/b3
PGA=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/pga
CELLS=$PGA/gap3-requal-cells.tsv
ROOT_HARNESS=$ROOT/evidence/session/gate-a-a1/p2-r3-terminal-runtime
RUN_UNTRACED=$ROOT/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3-untraced.sh
FREEZE=$B3/b3-freeze.json
FIXTURE=/tmp/p_b3_cells
TERMINATE=/tmp/p_r10_ledger
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
EXPECT_PACKAGE=com.waydefu.x11gpu
EXPECT_VERSION=1.03.01-83d45a9-23.09.26
EXPECT_APK_SHA256=f4c98b8a7364cb553532c0caef9aae83745df694c2021a1c1c2b7631c041230f
EXPECT_TERMINATE_SHA=2aca8ae15d536065168b3a819de1414c5520792712ea56ce254efbdde05ae50b
EXPECT_ROOT=1200x2191

refuse() { echo "GAP3_BLOCKED $*"; [ -n "${EVIDENCE:-}" ] && [ -d "$EVIDENCE" ] && echo "$*" > "$EVIDENCE/BLOCKED.txt"; exit 3; }
invalid() { echo "GAP3_INVALID $*"; echo "$*" > "$EVIDENCE/INVALID-CAPTURE.txt"; exit 2; }
# requal-02 (design appendix A): GAP3_MODE=C is the no-staging control (TERMUX_X11_DISABLE_EXA_GPU=1)
MODE=${GAP3_MODE:-S}; EVIDENCE="${EVIDENCE:-}"
case "$MODE" in S|C) ;; *) refuse "bad_mode $MODE";; esac
EXPECT_CELLS_SHA=51913a094623b5a1a4cd42fe91375eb2ce0f6c3b623ba4f3c0bfecfa017efcb4
EXPECT_FIXTURE_SRC_SHA=c0e0f5a2d0c539d45806fc591f55f09cc2087c6d152df609b35c8c667a2d760f
[ "$(sha256sum "$CELLS" | awk '{print $1}')" = "$EXPECT_CELLS_SHA" ] || refuse "cells_sha"
[ "$(sha256sum "$B3/p_b3_cells.c" | awk '{print $1}')" = "$EXPECT_FIXTURE_SRC_SHA" ] || refuse "fixture_src_sha"
[ -n "$EVIDENCE" ] || refuse "EVIDENCE"
if [ "${VALIDATE_ONLY:-0}" = 1 ]; then echo "GAP3_REQUAL_RUNNER_VALIDATE_ONLY"; exit 0; fi
[ -n "${SERIAL:-}" ] || refuse "SERIAL"
[ -e "$EVIDENCE" ] && refuse "evidence_exists"
"$B3/../common/safe-run.sh" --disk-min-gb 15 --disk-path "$(dirname "$EVIDENCE")" --floor-mb 4500 --check-only || refuse "host_resources"
[ "$(sha256sum "$TERMINATE" | awk '{print $1}')" = "$EXPECT_TERMINATE_SHA" ] || refuse "terminate_fixture_sha"
cc -O2 -Wall -o "$FIXTURE" "$B3/p_b3_cells.c" -lxcb -lxcb-render || refuse "fixture_build"
SEED=$(python3 -c "import json;d=json.load(open('$FREEZE'));print(d['fixture']['order_seeds'].get('$MODE',1105))")
ITERS=20; WARMUP=3; [ "$MODE" = ATTR ] && { ITERS=3; WARMUP=1; }
# ATTR only: idle gaps around every cell so attribution windows never touch (b3_attribution V2);
# timing modes keep 0 = the fixture behaves exactly as for b3-g-01 / b3-c-01 / b3-g2-01
QUIET=0; [ "$MODE" = ATTR ] && QUIET=20

export CELL="$EVIDENCE"
# shellcheck source=/dev/null
source "$ROOT_HARNESS/harness-lib.sh"
ADB get-state >/dev/null 2>&1 || refuse "ADB_DISCONNECTED"
ADB devices | grep -qF "$SERIAL" || refuse "serial_not_verbatim"
mkdir -p "$EVIDENCE"
sha256sum "$0" "$CELLS" "$B3/p_b3_cells.c" "$FIXTURE" "$PGA/gap3_requal.py" > "$EVIDENCE/tools.sha256.txt"
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
  G|G2) export TERMUX_X11_GATEA_PROTO=1;;
  C)    export TERMUX_X11_DISABLE_EXA_GPU=1;;
  S)    ;;
  ATTR) export TERMUX_X11_GATEA_PROTO=1 TERMUX_X11_GATEA_TELEMETRY=1 TERMUX_X11_R8_ARM=1 TERMUX_X11_R8_CASE=R8-C1;;
esac
env | grep -E '^TERMUX_X11_' | sort > "$EVIDENCE/env-x3.txt" || : > "$EVIDENCE/env-x3.txt"
rm -f "$SUMMARY" "$RING" || true
LLOG=/data/data/com.termux/files/usr/tmp/x3-launch-gap3-$$.log
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

set +e
maps_now() { ADB shell run-as com.waydefu.x11gpu wc -l "/proc/$ACT/maps" </dev/null 2>/dev/null | tr -d '\r' | awk '{print $1}'; }
echo "before=$(maps_now)" > "$EVIDENCE/activity-maps.txt"
DISPLAY=:3 timeout 3600 "$FIXTURE" --cells "$CELLS" --seed "$SEED" --iters "$ITERS" \
  --warmup "$WARMUP" --noise-every 25 --x-pid "$X3" --quiet-ms "$QUIET" > "$EVIDENCE/b3-cells.out" 2>&1
echo "fixture_rc=$?" > "$EVIDENCE/fixture-rc.txt"
set -e
sleep 2   # let the renderer process the last REMOVE events
echo "after=$(maps_now)" >> "$EVIDENCE/activity-maps.txt"
ADB shell dumpsys thermalservice </dev/null > "$EVIDENCE/thermal-post.txt" 2>&1 || true
echo "activity_pid_before_end=$(act_pid_now || true)" > "$EVIDENCE/activity-pid-before-end.txt"
X_ALIVE_AFTER_FIXTURE=false; [ -d "/proc/$X3" ] && X_ALIVE_AFTER_FIXTURE=true
echo "x_alive_after_fixture=$X_ALIVE_AFTER_FIXTURE" > "$EVIDENCE/x-end.txt"
if [ "$MODE" = ATTR ]; then
  timeout 60 "$TERMINATE" --display :3 --mode terminate > "$EVIDENCE/terminate.out" 2>&1 || true
  for i in $(seq 1 60); do [ -d "/proc/$X3" ] || break; sleep 0.5; done
  [ -f "$SUMMARY" ] && cp -a "$SUMMARY" "$EVIDENCE/gatea-summary.txt" || : > "$EVIDENCE/gatea-summary.txt"
  echo "end=terminate" >> "$EVIDENCE/x-end.txt"
elif [ -d "/proc/$X3" ]; then
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
  echo "GAP3_ABORTED_MEM_GUARD evidence=$EVIDENCE $(head -1 "$EVIDENCE/MEM-GUARD-TRIPPED.txt")"
  exit 5
fi
echo "GAP3_CAPTURED mode=$MODE evidence=$EVIDENCE cells=$(grep -c '^CELL ' "$EVIDENCE/b3-cells.out")"
