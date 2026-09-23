#!/usr/bin/env bash
# XFCE PRE-FREEZE ENVIRONMENT PROBE v3 — product bfb5769, X3 launched UNTRACED.
# NOT an XFCE session. Delta from v2: start-x3-untraced.sh instead of start-x3-noreset.py,
# a TracerPid==0 check on X3, an idle X round-trip sample, and the bfb5769 binding.
#
# V1-Core plan §11 forbids ANY XFCE session before V2-XFCE-DESIGN-FREEZE. This probe
# starts no XFCE component. It starts X3 + the experimental Activity exactly the way
# R10 did, and measures the facts the freeze has to pin and cannot pin by reading:
#
#   Q1  X root geometry in "native" mode on the internal panel, after the Activity bound
#   Q2  X extension list (GLX / Present / Composite / DAMAGE / XTEST) - decides which
#       xfwm4 vblank path and which xdotool verbs are even available
#   Q3  whether SurfaceFlinger --latency on the experimental layer yields frame
#       timestamps (the only candidate source for p50/p95/p99 / jank)
#   Q4  whether /sys/class/kgsl/kgsl-3d0/gpubusy is readable and moves under load
#   Q5  whether the Activity's /proc/<pid>/stat is readable for CPU time
#   Q6  thermal readout form (dumpsys thermalservice, HAL section)
#
# Workload used only to make frames exist: ONE p_r10_ledger workload (the R10 unit).
# Clean close: p_r10_ledger --mode terminate (the R10 close, 15/15 clean on dc94485).
#
#   EVIDENCE  must NOT exist     SERIAL  live-discovered host:port
# exit 3 = BLOCKED   2 = INVALID   0 = captured
set -euo pipefail

ROOT=/root/projects/GPU加速
ROOT_HARNESS=$ROOT/evidence/session/gate-a-a1/p2-r3-terminal-runtime
RUN_UNTRACED=$ROOT/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3-untraced.sh
X_RTT=$ROOT/evidence/session/gate-a-a1/p2-xfce-runtime/x_rtt.bin
R10=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/r10
SAMPLE=$R10/r10_sample.py
FIXTURE=/tmp/p_r10_ledger
EXPECT_FIXTURE_BIN_SHA=2aca8ae15d536065168b3a819de1414c5520792712ea56ce254efbdde05ae50b
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
EXPECT_PACKAGE=com.waydefu.x11gpu
EXPECT_VERSION=1.03.01-bfb5769-23.09.26
EXPECT_APK_SHA256=ff7b9309c405b07245bc352911867a66e8498464e515e09dbd645b3a1ec18472

refuse() { echo "PROBE_BLOCKED $*"; exit 3; }
invalid() { echo "PROBE_INVALID $*"; exit 2; }

EVIDENCE="${EVIDENCE:-}"
[ -n "$EVIDENCE" ] || refuse "EVIDENCE"
[ -n "${SERIAL:-}" ] || refuse "SERIAL"
[ -e "$EVIDENCE" ] && refuse "evidence_exists $EVIDENCE"
GOT=$(sha256sum "$FIXTURE" | awk '{print $1}')
[ "$GOT" = "$EXPECT_FIXTURE_BIN_SHA" ] || refuse "fixture_bin_sha $GOT"

export CELL="$EVIDENCE"
# shellcheck source=/dev/null
source "$ROOT_HARNESS/harness-lib.sh"
ADB get-state >/dev/null 2>&1 || refuse "ADB_DISCONNECTED"
ADB devices | grep -qF "$SERIAL" || refuse "serial_not_verbatim"      # V-23 / R-27
mkdir -p "$EVIDENCE"

X3=""
probe_cleanup() {
  if [ -n "${X3:-}" ] && [ -d "/proc/$X3" ]; then
    local cmd; cmd=$(tr '\0' ' ' < "/proc/$X3/cmdline" 2>/dev/null || true)
    case "$cmd" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) kill -TERM "$X3" 2>/dev/null || true
        echo "cleanup_sigterm_x3_pid=$X3 cmd=$cmd" >> "$EVIDENCE/cleanup.txt";;
    esac
  fi
  ADB shell am force-stop "$EXPECT_PACKAGE" >/dev/null 2>&1 || true
}
trap 'cleanup; probe_cleanup' EXIT

stable_json() {   # verbatim shape of the R8/R9/R10 Stable proof
  local out=$1 pid cmd
  pid=$(stabpid) || refuse "stable_pid"
  cmd=$(stab_cmd)
  echo "$cmd" | grep -q '^termux-x11 com.termux.x11 :1' || refuse "stable_cmd"
  ADB shell dumpsys package com.termux.x11 > "$out.raw" || true
  python3 - "$out" "$out.raw" "$pid" "$cmd" <<'PYEOF'
import json,re,sys
text=open(sys.argv[2],encoding="utf-8",errors="replace").read()
vn=re.search(r"versionName=(\S+)", text); vc=re.search(r"versionCode=(\d+)", text)
lu=re.search(r"lastUpdateTime=(.+)", text)
json.dump({"pid": int(sys.argv[3]), "cmdline": sys.argv[4].strip(),
           "versionName": vn.group(1) if vn else None,
           "versionCode": int(vc.group(1)) if vc else None,
           "lastUpdateTime": lu.group(1).strip() if lu else None},
          open(sys.argv[1],"w"), indent=2)
PYEOF
}
x3pid_now() {
  local p x
  for p in /proc/[0-9]*; do
    x=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$x" in "termux-x11gpu com.waydefu.x11gpu :3"*) echo "${p##*/}"; return 0;; esac
  done
  return 1
}
act_pid_now() { ADB shell pidof "$EXPECT_PACKAGE" 2>/dev/null | tr -d '\r' | awk '{print $1}'; }

# ------------------------------------------------------------------ preflight --
ADB shell dumpsys package "$EXPECT_PACKAGE" | grep -E 'versionName=' | head -1 \
  | tee "$EVIDENCE/experimental-package-pre.txt" | grep -q "versionName=$EXPECT_VERSION" \
  || refuse "version_mismatch"
INSTALLED=$(ADB shell pm path "$EXPECT_PACKAGE" | tr -d '\r' | sed -n 's/^package://p' | head -1)
GOT_APK=$(ADB shell sha256sum "$INSTALLED" | tr -d '\r' | awk '{print $1}')
echo "installed_apk_sha256=$GOT_APK" > "$EVIDENCE/installed-apk.sha256.txt"
[ "$GOT_APK" = "$EXPECT_APK_SHA256" ] || refuse "apk_sha256_mismatch $GOT_APK"
stable_json "$EVIDENCE/stable-before.json"
x3pid_now >/dev/null 2>&1 && refuse "x3_already_running"
ADB shell run-as "$EXPECT_PACKAGE" cat shared_prefs/com.waydefu.x11gpu_preferences.xml \
  > "$EVIDENCE/experimental-prefs.xml" 2>&1 || true
ADB shell wm size > "$EVIDENCE/wm-size.txt" 2>&1 || true
ADB shell dumpsys window displays > "$EVIDENCE/dumpsys-window-displays.txt" 2>&1 || true

SINCE=$(date '+%m-%d %H:%M:%S.000')
echo "logcat_since=$SINCE" > "$EVIDENCE/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$EVIDENCE/raw-logcat.txt" "$SINCE")
verify_logcat_pid "$LOGCAT_PID"

export TERMUX_X11_GATEA_PROTO=1 TERMUX_X11_GATEA_TELEMETRY=1
export TERMUX_X11_R8_ARM=1 TERMUX_X11_R8_CASE=R8-C1
env | grep -E '^TERMUX_X11_' | sort > "$EVIDENCE/env-cell.txt"

rm -f "$SUMMARY" "$RING" || true
LAUNCH_LOG=/data/data/com.termux/files/usr/tmp/x3-launch-$(basename "$EVIDENCE")-$$.log
X3_LAUNCH_LOG=$LAUNCH_LOG bash "$RUN_UNTRACED" >> "$EVIDENCE/start-x3.out" 2>&1
for i in $(seq 1 40); do X3=$(x3pid_now) && break || sleep 0.5; done
[ -n "$X3" ] || invalid "x3_missing"
tr '\0' ' ' < "/proc/$X3/cmdline" > "$EVIDENCE/x3-cmdline.txt"
grep -q -- '-noreset' "$EVIDENCE/x3-cmdline.txt" || refuse "noreset_absent"
echo "$X3" > "$EVIDENCE/x3-pid.txt"
grep -E 'TracerPid|PPid' "/proc/$X3/status" > "$EVIDENCE/x3-tracer.txt"
grep -q 'TracerPid:[[:space:]]*0$' "$EVIDENCE/x3-tracer.txt" || invalid "x3_traced"
export DISPLAY=:3

# Q1 before the Activity: the size X boots with, to show that it changes
for i in $(seq 1 20); do xdpyinfo -display :3 > "$EVIDENCE/xdpyinfo-pre-activity.txt" 2>&1 && break || sleep 0.5; done
ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' \
  >> "$EVIDENCE/am-start.out" 2>&1
sleep 6
ACT=$(act_pid_now) || ACT=""
echo "activity_pid=$ACT" > "$EVIDENCE/act-pid.txt"
[ -n "$ACT" ] || invalid "activity_missing"

# Q1 / Q2
xdpyinfo -display :3 > "$EVIDENCE/xdpyinfo.txt" 2>&1 || true
xrandr -display :3 > "$EVIDENCE/xrandr.txt" 2>&1 || true
xwininfo -display :3 -root > "$EVIDENCE/xwininfo-root.txt" 2>&1 || true
ADB shell dumpsys window windows > "$EVIDENCE/dumpsys-window-windows.txt" 2>&1 || true

# Q3 layer names
ADB shell dumpsys SurfaceFlinger --list > "$EVIDENCE/sf-list.txt" 2>&1 || true
grep -i -E 'waydefu|x11gpu|SurfaceView' "$EVIDENCE/sf-list.txt" > "$EVIDENCE/sf-list-experimental.txt" || true

# idle X round trips (untraced X, no clients but this one)
"$X_RTT" :3 250 10 > "$EVIDENCE/rtt-idle.txt" 2>&1 || true

# Q5 / Q6 / Q4 before workload
cp /proc/"$X3"/stat "$EVIDENCE/x-stat-pre.txt"
ADB shell cat /proc/"$ACT"/stat > "$EVIDENCE/act-stat-pre.txt" 2>&1 || true
ADB shell cat /sys/class/kgsl/kgsl-3d0/gpubusy > "$EVIDENCE/gpubusy-pre.txt" 2>&1 || true
ADB shell dumpsys thermalservice > "$EVIDENCE/thermal-pre.txt" 2>&1 || true
ADB shell cat /proc/loadavg > "$EVIDENCE/device-loadavg-pre.txt" 2>&1 || true
python3 "$SAMPLE" --tag P0 --serial "$SERIAL" --package "$EXPECT_PACKAGE" --x-pid "$X3" \
  --act-pid "$ACT" --summary "$SUMMARY" --ring "$RING" --out "$EVIDENCE/sample-P0.json" >/dev/null

# one R10 workload unit, gpubusy + SF latency sampled WHILE it runs
SD="$EVIDENCE/w1-state"; mkdir -p "$SD"
( timeout 180 "$FIXTURE" --display :3 --mode workload --state-dir "$SD" \
    --client-log "$EVIDENCE/w1.jsonl" > "$EVIDENCE/w1.out" 2>&1; echo $? > "$SD/rc" ) &
CPID=$!
: > "$EVIDENCE/gpubusy-during.txt"
for tag in A1 A2; do
  for i in $(seq 1 1800); do [ -f "$SD/at-$tag" ] && break; sleep 0.1; done
  [ -f "$SD/at-$tag" ] || { wait "$CPID" || true; invalid "handshake_${tag}"; }
  ADB shell cat /sys/class/kgsl/kgsl-3d0/gpubusy >> "$EVIDENCE/gpubusy-during.txt" 2>&1 || true
  touch "$SD/go-$tag"
done
wait "$CPID" || true
echo "client_rc=$(cat "$SD/rc" 2>/dev/null || echo 99)" > "$EVIDENCE/w1-rc.txt"

# Q3: try every candidate layer name for --latency.
# v2 FIX: `adb shell` reads stdin, so inside `while read` it swallowed the rest of the
# layer list and v1 queried only the first (buffer-less Background) layer. stdin is
# now </dev/null, and the BLAST layer - the one that actually receives buffers - is
# queried twice, 1 s apart, to show whether the timestamps move.
: > "$EVIDENCE/sf-latency.txt"
while IFS= read -r L; do
  name=$(echo "$L" | sed -E 's/^RequestedLayerState\{//; s/ parentId=.*$//; s/ relativeParentId=.*$//; s/ z=.*$//; s/\}$//')
  [ -n "$name" ] || continue
  { echo "=== layer: $name"; ADB shell dumpsys SurfaceFlinger --latency "\"$name\"" </dev/null 2>&1 | head -140; } \
    >> "$EVIDENCE/sf-latency.txt"
done < "$EVIDENCE/sf-list-experimental.txt"
BLAST=$(sed -n 's/^RequestedLayerState{\(.*(BLAST)#[0-9]*\) parentId=.*/\1/p' "$EVIDENCE/sf-list-experimental.txt" | head -1)
echo "blast_layer=$BLAST" > "$EVIDENCE/sf-blast-layer.txt"
if [ -n "$BLAST" ]; then
  ADB shell dumpsys SurfaceFlinger --latency "\"$BLAST\"" </dev/null > "$EVIDENCE/sf-latency-blast-1.txt" 2>&1 || true
  sleep 1
  ADB shell dumpsys SurfaceFlinger --latency "\"$BLAST\"" </dev/null > "$EVIDENCE/sf-latency-blast-2.txt" 2>&1 || true
fi

cp /proc/"$X3"/stat "$EVIDENCE/x-stat-post.txt"
ADB shell cat /proc/"$ACT"/stat > "$EVIDENCE/act-stat-post.txt" 2>&1 || true
ADB shell cat /sys/class/kgsl/kgsl-3d0/gpubusy > "$EVIDENCE/gpubusy-post.txt" 2>&1 || true
ADB shell dumpsys thermalservice > "$EVIDENCE/thermal-post.txt" 2>&1 || true
python3 "$SAMPLE" --tag P1 --serial "$SERIAL" --package "$EXPECT_PACKAGE" --x-pid "$X3" \
  --act-pid "$ACT" --summary "$SUMMARY" --ring "$RING" --out "$EVIDENCE/sample-P1.json" >/dev/null

# clean close (the R10 shape)
timeout 60 "$FIXTURE" --display :3 --mode terminate --client-log "$EVIDENCE/terminate.jsonl" \
  > "$EVIDENCE/terminate.out" 2>&1 || true
for i in $(seq 1 60); do [ -d "/proc/$X3" ] || break; sleep 0.5; done
if [ -d "/proc/$X3" ]; then echo "x_alive_after_terminate=true" > "$EVIDENCE/x-close.txt"
else echo "x_alive_after_terminate=false" > "$EVIDENCE/x-close.txt"; fi
[ -f "$SUMMARY" ] && cp -a "$SUMMARY" "$EVIDENCE/gatea-summary.txt" || : > "$EVIDENCE/gatea-summary.txt"
[ -f "$RING" ] && cp -a "$RING" "$EVIDENCE/gatea-ring.txt" || : > "$EVIDENCE/gatea-ring.txt"
sleep 2
ACT2=$(act_pid_now) || ACT2=""
echo "activity_pid_after_close=$ACT2" > "$EVIDENCE/act-pid-after-close.txt"
python3 "$SAMPLE" --tag P2 --serial "$SERIAL" --package "$EXPECT_PACKAGE" \
  ${ACT2:+--act-pid "$ACT2"} --summary "$SUMMARY" --ring "$RING" --out "$EVIDENCE/sample-P2.json" >/dev/null

sleep 1
stop_logcat "$LOGCAT_PID" || true; LOGCAT_PID=""
stable_json "$EVIDENCE/stable-after.json"
ls /tmp/.X11-unix/ > "$EVIDENCE/x11-unix-after.txt" 2>&1 || true
cp -a "$LAUNCH_LOG" "$EVIDENCE/x3-launcher.log" 2>/dev/null || true
echo "PROBE_CAPTURED evidence=$EVIDENCE"
