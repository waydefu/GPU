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
# 7bd04ec7... -> afe0ab92...: ORACLE_FROZEN_V2 (ORACLE-01-TRIAGE.md)
# afe0ab92... -> 40115b87...: ORACLE_FROZEN_V3 (event=5 completeness via c0)
EXPECT_FREEZE_SHA=40115b879d8f2e24ccebb94d2dd69851fe589e2d80d7c1b5729bf8b7d7fd69ca
# ac2e9cc1... -> de840363...: V2 fixture: quiet gaps, per-negative marks, effective repeat
EXPECT_FIXTURE_SRC_SHA=de840363eeb8a02bcb62ff18ab3848aba73a21419795cb7017f2e38924b44e32
# c60da2a6... -> streaming judge (INCIDENT-20260923); it imports xfce3/xfce_collect.py, pinned too
# b6963fe3... -> c41dc068...: V2 judge: (BEGIN-1ms, END], per-case negatives, phase_gaps_quiet
# c41dc068... -> d4f12d95...: V3 judge: event5_stream_complete
EXPECT_JUDGE_SHA=d4f12d9562b900b155403c123f12d505ac1429dabd7148ed8ac7ba310fe62bc6
EXPECT_COL_SHA=8c04d2a2c34d7063bef32ad9d4f9bdcd6898dd02e6090b78626e8bb8ad3d4028
EXPECT_ROOT=1200x2191

refuse() { echo "ORACLE_BLOCKED $*"; [ -n "${EVIDENCE:-}" ] && [ -d "$EVIDENCE" ] && echo "$*" > "$EVIDENCE/BLOCKED.txt"; exit 3; }
invalid() { echo "ORACLE_INVALID $*"; echo "$*" > "$EVIDENCE/INVALID-CAPTURE.txt"; exit 2; }
EVIDENCE="${EVIDENCE:-}"; [ -n "$EVIDENCE" ] || refuse "EVIDENCE"
for pair in "$FREEZE:$EXPECT_FREEZE_SHA" "$FIXTURE_SRC:$EXPECT_FIXTURE_SRC_SHA" "$ORC/judge-oracle.py:$EXPECT_JUDGE_SHA" "$T/xfce3/xfce_collect.py:$EXPECT_COL_SHA"; do
  f=${pair%:*}; want=${pair##*:}
  [ "$(sha256sum "$f" | awk '{print $1}')" = "$want" ] || refuse "frozen_file_changed $f"
done
if [ "${VALIDATE_ONLY:-0}" = 1 ]; then echo "ORACLE_RUNNER_V1_VALIDATE_ONLY"; exit 0; fi
[ -n "${SERIAL:-}" ] || refuse "SERIAL"
[ -e "$EVIDENCE" ] && refuse "evidence_exists"
"/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests/common/safe-run.sh" --disk-min-gb 15 --disk-path "$(dirname "$EVIDENCE")" --floor-mb 4500 --check-only || refuse "host_resources"
[ "$(sha256sum "$TERMINATE" | awk '{print $1}')" = "$EXPECT_TERMINATE_SHA" ] || refuse "terminate_fixture_sha"
cc -O2 -Wall -o "$FIXTURE" "$FIXTURE_SRC" -lxcb -lxcb-render || refuse "fixture_build"

export CELL="$EVIDENCE"
# shellcheck source=/dev/null
source "$ROOT_HARNESS/harness-lib.sh"
ADB get-state >/dev/null 2>&1 || refuse "ADB_DISCONNECTED"
ADB devices | grep -qF "$SERIAL" || refuse "serial_not_verbatim"
mkdir -p "$EVIDENCE"
sha256sum "$0" "$FREEZE" "$FIXTURE_SRC" "$FIXTURE" "$ORC/judge-oracle.py" "$T/xfce3/xfce_collect.py" "$TERMINATE" > "$EVIDENCE/tools.sha256.txt"

X3=""
o_cleanup() {
  if [ -n "${X3:-}" ] && [ -d "/proc/$X3" ]; then
    local cmd; cmd=$(tr '\0' ' ' < "/proc/$X3/cmdline" 2>/dev/null || true)
    case "$cmd" in "termux-x11gpu com.waydefu.x11gpu :3"*) kill -TERM "$X3" 2>/dev/null || true
      echo "cleanup_sigterm_x3 pid=$X3" >> "$EVIDENCE/cleanup.txt";; esac
  fi
  ADB shell am force-stop "$EXPECT_PACKAGE" </dev/null >/dev/null 2>&1 || true
}
MG=""
# our own child, exact pid. Every step tolerates failure: under set -e a failing kill of an
# already-exited guard ended the runner after its capture (oracle-02, 2026-09-23).
mg_stop() { if [ -n "${MG:-}" ]; then kill "$MG" 2>/dev/null || true; wait "$MG" 2>/dev/null || true; fi; MG=""; return 0; }
trap 'cleanup; o_cleanup; mg_stop' EXIT
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
mg_stop
if [ -e "$EVIDENCE/MEM-GUARD-TRIPPED.txt" ]; then
  (cd "$EVIDENCE" && find . -type f ! -name sha256sums.txt | sort | xargs sha256sum > sha256sums.txt)
  echo "ORACLE_ABORTED_MEM_GUARD evidence=$EVIDENCE $(head -1 "$EVIDENCE/MEM-GUARD-TRIPPED.txt")"
  exit 5
fi
echo "ORACLE_CAPTURED evidence=$EVIDENCE"
