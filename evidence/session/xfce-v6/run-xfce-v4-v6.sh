#!/usr/bin/env bash
# XFCE runner V4 for XFCE-V6-BASELINE-01 (evidence/session/xfce-v6/XFCE-V6-BASELINE-01-FREEZE.md, tool T4).
# Derived from run-xfce-v3-f592241.sh; the product binding, choreography, variant and manifest are UNCHANGED.
# V4 adds only: (1) client-tracer.json + refuse unless the runner shell is traced by proot-fast6 without
# its off switches; (2) xfce-session-tracer.json once the session is ready; (3) a touch recorder over the
# whole capture -> touch.json; (4) EXPECT_ROOT from the environment (the preflight records it);
# (5) MODE=preflight: X3 up, no XFCE, preflight_probe.py (3 x 1000 ms GrabServer) instead of the session.
# Probes (rca_sampler.py with x_rtt2.glibc, v6_probes.py) are started by series-v6.sh, as before.
#   MODE      capture (default) | preflight
#   EXPECT_ROOT  WxH, required for MODE=capture
# --- V3 header follows ---
# XFCE runner V3 derived for product f592241 (from run-xfce-v3-709dfac.sh; only the binding differs) (EXA async prototype; PGA-GAP-2-ASYNC-XFCE-FREEZE.md).
# Only the product binding and the exit trap differ from run-xfce-v3.sh (bfb5769, kept unchanged).
# Original header: XFCE baseline runner V3 — product bfb5769, XFCE-FREEZE-V3: X3 launched UNTRACED
# (start-x3-untraced.sh, RCA-XFCE-2) and the screen checked before and after.
# ORCHESTRATES AND CAPTURES ONLY. Derived from run-xfce.sh (V1, kept unchanged for the
# dc94485 record); differences: tests/xfce2, the V2 binding, TERMUX_X11_P2A_DIAG unset.
#
# Every judgement lives in tests/xfce/ (xfce_collect.py -> judge-xfce.py) and is
# unit-tested offline with controls that are proven to go red (mutation_check.py).
#
#   VARIANT   C1 (xfwm4 compositor on) | C0 (off - the daily :1 setting)
#   EVIDENCE  must NOT already exist
#   SERIAL    live-discovered host:port on lane 5038 (required unless VALIDATE_ONLY=1)
#   VALIDATE_ONLY=1   zero device mutation, exits before SERIAL is read
#
# Sequence (freeze p10 / p11):
#   preflight -> X3 -noreset + Activity -> root size check (BLOCK if wrong) -> K0
#   -> fresh XFCE session (dbus-run-session, isolated HOME/XDG, frozen xfconf overlay)
#   -> ready -> settle -> K1 -> choreo.py (150 s frozen schedule) -> K2
#   -> xfce4-session-logout --logout --fast -> K3 (X alive, no clients)
#   -> p_r10_ledger --mode terminate (the R10 clean close) -> K4 -> captured
#
# exit 3 = BLOCKED (run NOT consumed)   2 = INVALID capture   0 = captured
#      4 = X3_STARTUP_CRASH: X died before any XFCE process existed. Not consumed, but
#          it IS evidence (xfce-c1-02: the known VM-JIT class, PC 0x4800229c in
#          dalvik-jit-code-cache) and is kept, never deleted.
set -euo pipefail

ROOT=/root/projects/GPU加速
XFCE=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/xfce3
R10=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/r10
ROOT_HARNESS=$ROOT/evidence/session/gate-a-a1/p2-r3-terminal-runtime
RUN_UNTRACED=$ROOT/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3-untraced.sh
X3_LAUNCHER_LOG=$ROOT/evidence/session/gate-a-a1/p2-runtime-phase1/r0/x3-launcher.raw.log
SAMPLE=$R10/r10_sample.py
FREEZE=$XFCE/xfce-design-freeze.json
MANIFEST=$XFCE/FROZEN-SHA256SUMS
FIXTURE=/tmp/p_r10_ledger
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt

EXPECT_PACKAGE=com.waydefu.x11gpu
EXPECT_VERSION=1.03.01-f592241-24.09.26
EXPECT_APK_SHA256=f9e35b6907df36fc4f4d5a0440147c3e9b746356776beb3217431b48fa01075c
EXPECT_HEAD=f592241dfab5ba2913a89d5d3b45f2b03ebffb65
EXPECT_FIXTURE_BIN_SHA=2aca8ae15d536065168b3a819de1414c5520792712ea56ce254efbdde05ae50b
# 79e733cd... -> 66e37b23...: streaming collector + safe-run.sh (INCIDENT-20260923), same freeze
# 66e37b23... -> cdae546d...: + mem-guard.sh (INCIDENT-20260923-2), same freeze
EXPECT_MANIFEST_SHA=cdae546de616de21011103510ddbac7fe77fd41866427ef8d0c290cdb283e559
MODE="${MODE:-capture}"
EXPECT_ROOT="${EXPECT_ROOT:-}"
V6=$ROOT/src/f8-ahb-exa-async/tests/xfce_v6
V6_TRACER_SHA=2d5596dce6ae3a978658a66902cf121a34b8062480958b5750caba61feda2eab
TOUCH_DEV=/dev/input/event7   # focaltech_ts, as tests/gl/gl_bench.sh

refuse() { echo "XFCE_BLOCKED $*"; [ -n "${EVIDENCE:-}" ] && [ -d "$EVIDENCE" ] && echo "$*" > "$EVIDENCE/BLOCKED.txt"; exit 3; }
invalid() { echo "XFCE_INVALID $*"; echo "$*" > "$EVIDENCE/INVALID-CAPTURE.txt"; exit 2; }

VARIANT="${VARIANT:-}"; EVIDENCE="${EVIDENCE:-}"; VALIDATE_ONLY="${VALIDATE_ONLY:-0}"
case "$VARIANT" in C1|C0) ;; *) refuse "bad_variant '$VARIANT'";; esac
case "$MODE" in capture) [ -n "$EXPECT_ROOT" ] || refuse "EXPECT_ROOT";; preflight) ;; *) refuse "bad_mode '$MODE'";; esac
[ -n "$EVIDENCE" ] || refuse "EVIDENCE"
GOT=$(sha256sum "$MANIFEST" | awk '{print $1}')
[ "$GOT" = "$EXPECT_MANIFEST_SHA" ] || refuse "frozen_manifest_sha $GOT"
( cd "$XFCE" && sha256sum --quiet -c "$MANIFEST" ) || refuse "frozen_file_changed"
if [ "$VALIDATE_ONLY" = 1 ]; then
  echo "XFCE_RUNNER_V4_VALIDATE_ONLY mode=$MODE variant=$VARIANT manifest=$GOT"
  exit 0
fi

[ -n "${SERIAL:-}" ] || refuse "SERIAL"
[ -e "$EVIDENCE" ] && refuse "evidence_exists $EVIDENCE"
# host resources (INCIDENT-20260923): the capture is ~0.9 GB and every analysis shares the
# phone with Stable / the daily desktop
"/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests/common/safe-run.sh" --disk-min-gb 15 --disk-path "$(dirname "$EVIDENCE")" --floor-mb 4500 --check-only \
  || refuse "host_resources"
GOT=$(sha256sum "$FIXTURE" | awk '{print $1}')
[ "$GOT" = "$EXPECT_FIXTURE_BIN_SHA" ] || refuse "fixture_bin_sha $GOT"
# Derived run (not a baseline): the freeze binds the product tree to bfb5769, so
# product_tree_unchanged_since_binding cannot hold for 11b3b79. Accept exactly that one failure;
# any other failing check still refuses (PGA-GAP-2-ASYNC-XFCE-FREEZE.md, deviation 1).
VXS_OUT=$(python3 "$XFCE/verify-xfce-support.py" 2>&1) || {
  VXS_FAILS=$(printf '%s\n' "$VXS_OUT" | grep '^FAIL ' | awk '{print $2}' | sort -u | tr '\n' ' ')
  [ "$VXS_FAILS" = "product_tree_unchanged_since_binding " ] || refuse "verify_xfce_support $VXS_FAILS"
}

export CELL="$EVIDENCE"
# shellcheck source=/dev/null
source "$ROOT_HARNESS/harness-lib.sh"
ADB get-state >/dev/null 2>&1 || refuse "ADB_DISCONNECTED"
ADB devices | grep -qF "$SERIAL" || refuse "serial_not_verbatim"          # V-23 / R-27
mkdir -p "$EVIDENCE"
python3 "$XFCE/verify-xfce-support.py" > "$EVIDENCE/verify-xfce-support.txt" 2>&1 || true
sha256sum "$0" "$MANIFEST" "$FIXTURE" "$V6"/*.py "$V6"/*.sh > "$EVIDENCE/tools.sha256.txt"
# V4 (1): the client tracer (every XFCE client of this run inherits it). Not proot-fast6, or one of its
# off switches set -> BLOCKED before anything is consumed (freeze section 4, items 1-2).
python3 "$V6/tracer_ident.py" --pid $$ --out "$EVIDENCE/client-tracer.json" >/dev/null
python3 - "$EVIDENCE/client-tracer.json" "$V6_TRACER_SHA" <<'PYEOF2' || refuse "client_tracer_not_v6 $(tr -d '\n' < "$EVIDENCE/client-tracer.json")"
import json,sys
d=json.load(open(sys.argv[1])); env=d.get("proot_env") or {}
bad=env.get("PROOT_STAT_AT_ENTER")=="0" or env.get("PROOT_KOMPAT_FULL")=="1" or env.get("PROOT_BWRAP_COMPAT")=="1"
sys.exit(0 if d.get("tracer_pid") and d.get("tracer_sha256")==sys.argv[2] and d.get("proot_env") is not None and not bad else 1)
PYEOF2

RUN_ID="$(date +%Y%m%d%H%M%S)-$$"
RUN_ROOT=/tmp/xfce-x3-run-$RUN_ID
STATE=$RUN_ROOT/state
X3=""; ACT=""; POLLER=""; SESSION_LAUNCHER=""

# ---------------------------------------------------------------- helpers --
stable_json() {   # byte-for-byte the R8/R9/R10 Stable proof
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
screen_json() { # screen_json <out>  (wakefulness + keyguard, as the install scripts check them)
  local w k
  w=$(ADB shell dumpsys power </dev/null 2>/dev/null | tr -d '\r' | grep -m1 'mWakefulness=' | sed 's/.*mWakefulness=//' || true)
  k=$(ADB shell dumpsys window </dev/null 2>/dev/null | tr -d '\r' | grep -m1 'isKeyguardShowing=' | sed 's/.*isKeyguardShowing=//' || true)
  python3 -c "import json,sys;json.dump({'wakefulness':sys.argv[1] or None,'awake':sys.argv[1]=='Awake','keyguard':None if sys.argv[2]=='' else sys.argv[2]=='true'},open(sys.argv[3],'w'))" "$w" "$k" "$1"
}
act_pid_now() { ADB shell pidof "$EXPECT_PACKAGE" </dev/null 2>/dev/null | tr -d '\r' | awk '{print $1}'; }

# V4 (3): touch recorder, as tests/gl/gl_bench.sh. Started directly (never inside $(...)) so TOUCH_REC
# is the adb process itself (env execs it); any EV_KEY/EV_ABS line counts; a dead recorder -> null.
TOUCH_REC=""; TOUCH_SELFTEST=false
touch_start() {
  : > "$EVIDENCE/touch-getevent.txt"
  env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
    HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
    "$TADB" -H 127.0.0.1 -P 5038 -s "$SERIAL" shell getevent "$TOUCH_DEV" </dev/null > "$EVIDENCE/touch-getevent.txt" 2>&1 &
  TOUCH_REC=$!
  sleep 2
  if [ -d "/proc/$TOUCH_REC" ] && ! grep -qiE 'could not|denied|error|no such' "$EVIDENCE/touch-getevent.txt"; then
    TOUCH_SELFTEST=true; fi
}
touch_stop() {
  [ -n "$TOUCH_REC" ] || return 0
  local alive=false n
  [ -d "/proc/$TOUCH_REC" ] && alive=true
  kill "$TOUCH_REC" 2>/dev/null || true; wait "$TOUCH_REC" 2>/dev/null || true
  echo "touch_recorder_stopped pid=$TOUCH_REC" >> "$EVIDENCE/cleanup.txt"
  TOUCH_REC=""
  n=$(grep -cE '^000[13] ' "$EVIDENCE/touch-getevent.txt" || true)
  $alive && n=${n:-0} || n=null
  printf '{"selftest": %s, "events": %s}\n' "$TOUCH_SELFTEST" "$n" > "$EVIDENCE/touch.json"
}

# Processes of THIS session, found by the run id in their environment - robust against
# daemons that reparent away from the session tree, and blind to the daily :1 XFCE.
ours() {
  local p
  for p in /proc/[0-9]*; do
    [ -r "$p/environ" ] || continue
    if tr '\0' '\n' < "$p/environ" 2>/dev/null | grep -qx "XFCE_RUN_ID=$RUN_ID"; then
      echo "${p##*/} $(cat "$p/comm" 2>/dev/null)"
    fi
  done
}
clients_json() { # clients_json <out>
  ours | python3 -c '
import json,sys
d={}
for ln in sys.stdin:
    pid,_,comm=ln.strip().partition(" ")
    d.setdefault(comm,[]).append(int(pid))
out={k:(v[0] if len(v)==1 else sorted(v)) for k,v in d.items()}
json.dump(out,open(sys.argv[1],"w"),indent=2,sort_keys=True)' "$1"
}

ksample() { # ksample <K> [--no-x]
  # Declarations split on purpose: `local k=$1 args=(...$k...)` expands $k against the
  # OUTER scope before local runs - the exact bug that killed r10-e-01 mid-round.
  local k=$1
  local nox=${2:-}
  local args=(--tag "$k" --serial "$SERIAL" --package "$EXPECT_PACKAGE"
              --summary "$SUMMARY" --ring "$RING" --out "$EVIDENCE/k-$k.json")
  [ "$nox" = "--no-x" ] || args+=(--x-pid "$X3")
  [ -n "$ACT" ] && args+=(--act-pid "$ACT")
  python3 "$SAMPLE" "${args[@]}" </dev/null >/dev/null
  local xs="" as="" la gb th
  [ "$nox" = "--no-x" ] || xs=$(cat "/proc/$X3/stat" 2>/dev/null || true)
  [ -n "$ACT" ] && as=$(ADB shell cat "/proc/$ACT/stat" </dev/null 2>/dev/null | tr -d '\r' || true)
  la=$(ADB shell cat /proc/loadavg </dev/null 2>/dev/null | tr -d '\r' || true)
  gb=$(ADB shell cat /sys/class/kgsl/kgsl-3d0/gpubusy </dev/null 2>/dev/null | tr -d '\r' || true)
  th=$(ADB shell dumpsys thermalservice </dev/null 2>/dev/null | tr -d '\r' | grep -m1 '^Thermal Status' || true)
  python3 - "$EVIDENCE/k-$k-extra.json" "$xs" "$as" "$la" "$gb" "$th" "$(date +%s.%N)" <<'PYEOF'
import json,sys
o,xs,as_,la,gb,th,ep=sys.argv[1:8]
json.dump({"x_stat": xs or None, "act_stat": as_ or None, "device_loadavg": la or None,
           "gpubusy": gb or None, "thermal_status": th or None, "epoch_s": float(ep)},
          open(o,"w"), indent=2)
PYEOF
}

start_poller() { # SF latency + gpubusy every 2 s, thermal every 30 s, until the stop flag
  local blast=$1
  : > "$EVIDENCE/sf-polls.txt"; : > "$EVIDENCE/gpubusy-polls.txt"; : > "$EVIDENCE/thermal-polls.txt"
  (
    # a poll that fails is a missing poll, never a dead poller: the parent's
    # errexit + pipefail must not reach in here
    set +e +o pipefail
    i=0
    while [ ! -e "$STATE/stop-poller" ]; do
      { echo "=== poll $(date +%s.%N)"
        ADB shell dumpsys SurfaceFlinger --latency "\"$blast\"" </dev/null 2>&1 | tr -d '\r'; } \
        >> "$EVIDENCE/sf-polls.txt"
      echo "$(date +%s.%N) $(ADB shell cat /sys/class/kgsl/kgsl-3d0/gpubusy </dev/null 2>/dev/null | tr -d '\r')" \
        >> "$EVIDENCE/gpubusy-polls.txt"
      if [ $((i % 15)) -eq 0 ]; then
        { echo "=== poll $(date +%s.%N)"; ADB shell dumpsys thermalservice </dev/null 2>&1 | tr -d '\r'; } \
          >> "$EVIDENCE/thermal-polls.txt"
      fi
      i=$((i + 1))
      sleep 2
    done
  ) &
  POLLER=$!
  echo "poller_pid=$POLLER" > "$EVIDENCE/poller.txt"
}
stop_poller() {
  [ -n "$POLLER" ] || return 0
  touch "$STATE/stop-poller"
  local i
  for i in $(seq 1 40); do [ -d "/proc/$POLLER" ] || break; sleep 0.25; done
  if [ -d "/proc/$POLLER" ]; then kill -TERM "$POLLER" 2>/dev/null || true
    echo "poller_sigterm pid=$POLLER" >> "$EVIDENCE/cleanup.txt"; fi
  wait "$POLLER" 2>/dev/null || true
  POLLER=""
}

# X's stderr (FatalError text, the Uctx/Ssig crash handler dump) goes to ONE launcher
# log shared by every run; keep only this run's bytes, from the offset taken at start.
LAUNCHER_OFF=""
save_launcher_segment() {
  [ -n "$LAUNCHER_OFF" ] && [ -f "$X3_LAUNCHER_LOG" ] || return 0
  [ -f "$EVIDENCE/x3-launcher.log" ] && return 0
  tail -c +"$((LAUNCHER_OFF + 1))" "$X3_LAUNCHER_LOG" > "$EVIDENCE/x3-launcher.log" 2>/dev/null || true
}
xfce_cleanup() {
  local rc=$?
  stop_poller || true
  touch_stop || true
  if [ -n "$RUN_ID" ]; then
    local left; left=$(ours || true)
    if [ -n "$left" ]; then
      echo "abort_leftovers:" >> "$EVIDENCE/cleanup.txt"; echo "$left" >> "$EVIDENCE/cleanup.txt"
      echo "$left" | awk '{print $1}' | while read -r p; do kill -TERM "$p" 2>/dev/null || true; done
    fi
  fi
  if [ -n "${X3:-}" ] && [ -d "/proc/$X3" ]; then
    local cmd; cmd=$(tr '\0' ' ' < "/proc/$X3/cmdline" 2>/dev/null || true)
    case "$cmd" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) kill -TERM "$X3" 2>/dev/null || true
        echo "cleanup_sigterm_x3 pid=$X3 cmd=$cmd" >> "$EVIDENCE/cleanup.txt";;
    esac
  fi
  ADB shell am force-stop "$EXPECT_PACKAGE" </dev/null >/dev/null 2>&1 || true
  save_launcher_segment
  if [ -d "$STATE" ] && [ ! -d "$EVIDENCE/state" ]; then
    mkdir -p "$EVIDENCE/state"; cp -a "$STATE/." "$EVIDENCE/state/" 2>/dev/null || true
  fi
  [ -d "$RUN_ROOT" ] && rm -rf "$RUN_ROOT"
  return "$rc"
}
MG=""
# our own child, exact pid. Every step tolerates failure: under set -e a failing kill of an
# already-exited guard ended the runner after its capture (oracle-02, 2026-09-23).
mg_stop() { if [ -n "${MG:-}" ]; then kill "$MG" 2>/dev/null || true; wait "$MG" 2>/dev/null || true; fi; MG=""; return 0; }
# cleanup returns the exit status; under set -e a non-zero one ended the trap before xfce_cleanup /
# mg_stop (opstream-g-01, 2026-09-23). Run every step regardless.
trap 'cleanup || true; xfce_cleanup || true; mg_stop' EXIT

# ---------------------------------------------------------------- preflight --
for pkg in $(python3 -c "import json;print(' '.join(json.load(open('$FREEZE'))['pinned_packages']))"); do
  want=$(python3 -c "import json;print(json.load(open('$FREEZE'))['pinned_packages']['$pkg'])")
  have=$(dpkg-query -W -f '${Version}' "$pkg" 2>/dev/null || echo MISSING)
  echo "$pkg $have" >> "$EVIDENCE/host-packages.txt"
  [ "$have" = "$want" ] || refuse "package_version $pkg have=$have want=$want"
done
ADB shell dumpsys package "$EXPECT_PACKAGE" | grep -E 'versionName=' | head -1 \
  | tee "$EVIDENCE/experimental-package-pre.txt" | grep -q "versionName=$EXPECT_VERSION" \
  || refuse "version_mismatch"
INSTALLED=$(ADB shell pm path "$EXPECT_PACKAGE" | tr -d '\r' | sed -n 's/^package://p' | head -1)
[ -n "$INSTALLED" ] || refuse "apk_path_unresolved"
GOT_APK=$(ADB shell sha256sum "$INSTALLED" | tr -d '\r' | awk '{print $1}')
echo "installed_apk_sha256=$GOT_APK" > "$EVIDENCE/installed-apk.sha256.txt"
[ "$GOT_APK" = "$EXPECT_APK_SHA256" ] || refuse "apk_sha256_mismatch $GOT_APK"
ADB shell run-as "$EXPECT_PACKAGE" cat shared_prefs/com.waydefu.x11gpu_preferences.xml \
  > "$EVIDENCE/experimental-prefs.xml" 2>&1 || true
grep -q 'name="displayResolutionMode">native<' "$EVIDENCE/experimental-prefs.xml" \
  || refuse "resolution_mode_not_native"
# `grep -c` prints 0 AND exits 1 on no match; without the remote `|| true` that exit
# code came back through adb, pipefail tripped the local `|| echo x`, and EXT became
# "0<newline>x" - xfce-c1-01 was BLOCKED by exactly that (runner bug, not consumed).
EXT=$(ADB shell "dumpsys display | grep -c 'type EXTERNAL' || true" | tr -d '\r')
echo "external_displays=$EXT" > "$EVIDENCE/displays.txt"
[ "$EXT" = 0 ] || refuse "external_display_connected $EXT"
stable_json "$EVIDENCE/stable-before.json"
echo "stable_pid=$(stabpid)" > "$EVIDENCE/stable-pid.txt"
screen_json "$EVIDENCE/screen-pre.json"
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));sys.exit(0 if d['awake'] and d['keyguard'] is False else 1)" "$EVIDENCE/screen-pre.json" \
  || refuse "screen_not_awake_or_locked $(cat "$EVIDENCE/screen-pre.json")"
x3pid_now >/dev/null 2>&1 && refuse "x3_already_running"
touch_start
[ "$TOUCH_SELFTEST" = true ] || refuse "touch_recorder_selftest $(head -c 200 "$EVIDENCE/touch-getevent.txt")"
MANIFEST_SHA=$(sha256sum "$MANIFEST" | awk '{print $1}')
FREEZE_SHA=$(sha256sum "$FREEZE" | awk '{print $1}')
RUNNER_SHA=$(sha256sum "$0" | awk '{print $1}')
printf '{"mode":"%s","variant":"%s","source_sha":"%s","apk_sha256":"%s","freeze_sha256":"%s","manifest_sha256":"%s","runner_sha256":"%s","run_id":"%s"}\n' \
  "$MODE" "$VARIANT" "$EXPECT_HEAD" "$EXPECT_APK_SHA256" "$FREEZE_SHA" "$MANIFEST_SHA" "$RUNNER_SHA" "$RUN_ID" \
  > "$EVIDENCE/run-binding.json"

# fresh Activity every run (freeze runs.each_run_fresh)
ADB shell am force-stop "$EXPECT_PACKAGE" </dev/null >/dev/null 2>&1 || true
sleep 2

SINCE=$(date '+%m-%d %H:%M:%S.000')
echo "logcat_since=$SINCE" > "$EVIDENCE/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$EVIDENCE/raw-logcat.txt" "$SINCE")
# start_logcat forks a subshell that then execs adb; verify_logcat_pid checks /proc/<pid>/exe at once
# and, under set -e, a not-yet-exec'd pid ended the runner silently (xfce-c0-gat-01, 709dfac). Give
# the exec up to 2 s; verify_logcat_pid itself is unchanged.
for _ in $(seq 1 20); do [ "$(readlink "/proc/$LOGCAT_PID/exe" 2>/dev/null)" = "$TADB" ] && break; sleep 0.1; done
verify_logcat_pid "$LOGCAT_PID" || refuse "logcat_not_verified"

export TERMUX_X11_GATEA_PROTO=1 TERMUX_X11_GATEA_TELEMETRY=1
export TERMUX_X11_R8_ARM=1 TERMUX_X11_R8_CASE=R8-C1
unset TERMUX_X11_P2A_DIAG          # the product, not the diagnostic build (PGA-GAP-1)
env | grep -E '^TERMUX_X11_' | sort > "$EVIDENCE/env-x3.txt"

rm -f "$SUMMARY" "$RING" || true
X3_LAUNCHER_LOG=/data/data/com.termux/files/usr/tmp/x3-launch-$RUN_ID.log
LAUNCHER_OFF=0
echo "launcher_log=$X3_LAUNCHER_LOG" > "$EVIDENCE/launcher-offset.txt"
X3_LAUNCH_LOG=$X3_LAUNCHER_LOG bash "$RUN_UNTRACED" >> "$EVIDENCE/start-x3.out" 2>&1 || refuse "untraced_launch_failed"
for i in $(seq 1 40); do X3=$(x3pid_now) && break || sleep 0.5; done
[ -n "$X3" ] || invalid "x3_missing"
echo "x3_pid=$X3" > "$EVIDENCE/x3-pid.txt"
grep -E 'TracerPid|PPid' "/proc/$X3/status" > "$EVIDENCE/x3-tracer.txt" || true
grep -q 'TracerPid:[[:space:]]*0$' "$EVIDENCE/x3-tracer.txt" || refuse "x3_traced $(tr '\n' ' ' < "$EVIDENCE/x3-tracer.txt")"
# memory watchdog (INCIDENT-20260923-2-LMK-B3-S): trips -> X3 SIGTERM + force-stop -> exit 5 below
MEMGUARD=/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests/common/mem-guard.sh
"$MEMGUARD" --x3-pid "$X3" --log "$EVIDENCE/mem-guard.log" --flag "$EVIDENCE/MEM-GUARD-TRIPPED.txt" \
  --serial "$SERIAL" --floor-mb 3000 --swap-growth-mb 1536 --x3-max-mb 3072 </dev/null &
MG=$!
sha256sum "$MEMGUARD" >> "$EVIDENCE/tools.sha256.txt"
tr '\0' ' ' < "/proc/$X3/cmdline" > "$EVIDENCE/x3-cmdline.txt"
grep -q -- '-noreset' "$EVIDENCE/x3-cmdline.txt" || refuse "noreset_absent"
ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' \
  >> "$EVIDENCE/am-start.out" 2>&1
sleep 6
ACT=$(act_pid_now) || ACT=""
[ -n "$ACT" ] || invalid "activity_missing"
echo "activity_pid=$ACT" > "$EVIDENCE/activity-pid.txt"
if [ ! -d "/proc/$X3" ]; then
  save_launcher_segment
  echo "x3_died_before_xfce pid=$X3" > "$EVIDENCE/X3-STARTUP-CRASH.txt"
  grep -m3 -E '^(Uctx|Upid|Ssig) ' "$EVIDENCE/x3-launcher.log" >> "$EVIDENCE/X3-STARTUP-CRASH.txt" 2>/dev/null || true
  echo "XFCE_X3_STARTUP_CRASH pid=$X3"
  exit 4
fi

# ---------------------------------------------------------------- root size --
DISPLAY=:3 xdpyinfo > "$EVIDENCE/xdpyinfo.txt" 2>&1 || true
DIMS=$(sed -n 's/^  dimensions: *\([0-9]*x[0-9]*\) pixels.*/\1/p' "$EVIDENCE/xdpyinfo.txt")
echo "x_root=$DIMS expect=${EXPECT_ROOT:-preflight}" > "$EVIDENCE/x-root.txt"
if [ "$MODE" = capture ] && [ "$DIMS" != "$EXPECT_ROOT" ]; then
  # BLOCKED before XFCE: close X the clean way so nothing is left behind
  timeout 60 "$FIXTURE" --display :3 --mode terminate > "$EVIDENCE/terminate-blocked.out" 2>&1 || true
  refuse "x_root_size $DIMS"
fi
DISPLAY=:3 xset s off -dpms >> "$EVIDENCE/xset.out" 2>&1 || true
DISPLAY=:3 xset q > "$EVIDENCE/xset-q.txt" 2>&1 || true

# SF layer for this Activity instance (the #id changes every instance)
ADB shell dumpsys SurfaceFlinger --list </dev/null 2>/dev/null | tr -d '\r' \
  | grep -F 'com.waydefu.x11gpu' > "$EVIDENCE/sf-list.txt" || true
BLAST=$(sed -n 's/^RequestedLayerState{\(.*(BLAST)#[0-9]*\) parentId=.*/\1/p' "$EVIDENCE/sf-list.txt" | head -1)
echo "blast_layer=$BLAST" > "$EVIDENCE/sf-blast-layer.txt"

mkdir -p "$RUN_ROOT"/{home,config,cache,data,runtime,state}
chmod 700 "$RUN_ROOT/runtime"
[ -n "$BLAST" ] && start_poller "$BLAST"
ksample K0

if [ "$MODE" = capture ]; then
# ---------------------------------------------------------------- session --
XC=$RUN_ROOT/config/xfce4/xfconf/xfce-perchannel-xml
mkdir -p "$XC" "$RUN_ROOT/config/autostart"
cp "$XFCE/config/xfwm4-$VARIANT.xml" "$XC/xfwm4.xml"
cp "$XFCE/config/xfce4-session.xml" "$XFCE/config/xfce4-panel.xml" "$XFCE/config/xfce4-terminal.xml" "$XC/"
for d in /etc/xdg/autostart/*.desktop; do
  printf '[Desktop Entry]\nHidden=true\n' > "$RUN_ROOT/config/autostart/$(basename "$d")"
done
( cd "$RUN_ROOT/config" && find . -type f | sort | xargs sha256sum ) > "$EVIDENCE/run-config.sha256.txt"
ls /etc/xdg/autostart/ > "$EVIDENCE/autostart-hidden.txt"

SESSION_ENV=(env -i PATH=/usr/local/bin:/usr/bin:/bin DISPLAY=:3
  HOME="$RUN_ROOT/home" XDG_CONFIG_HOME="$RUN_ROOT/config" XDG_CACHE_HOME="$RUN_ROOT/cache"
  XDG_DATA_HOME="$RUN_ROOT/data" XDG_RUNTIME_DIR="$RUN_ROOT/runtime"
  LANG=C.UTF-8 LC_ALL=C.UTF-8 NO_AT_BRIDGE=1 XFCE_RUN_ID="$RUN_ID" XFCE_STATE="$STATE")
printf '%s\n' "${SESSION_ENV[@]}" > "$EVIDENCE/session-env.txt"
setsid "${SESSION_ENV[@]}" dbus-run-session -- "$XFCE/session_wrapper.sh" \
  > "$EVIDENCE/xfce-session.log" 2>&1 < /dev/null &
SESSION_LAUNCHER=$!
echo "dbus_run_session_pid=$SESSION_LAUNCHER" > "$EVIDENCE/session-launcher.txt"

T_START=$(date +%s.%N); READY=0; WM=0; PANEL=0; DESK=0
for i in $(seq 1 180); do
  DISPLAY=:3 xprop -root _NET_SUPPORTING_WM_CHECK 2>/dev/null | grep -q 'window id' && WM=1 || WM=0
  DISPLAY=:3 xdotool search --onlyvisible --classname xfce4-panel >/dev/null 2>&1 && PANEL=1 || PANEL=0
  DISPLAY=:3 xdotool search --classname xfdesktop >/dev/null 2>&1 && DESK=1 || DESK=0
  if [ "$WM$PANEL$DESK" = 111 ]; then READY=1; break; fi
  sleep 0.5
done
WAITED=$(python3 -c "import time;print(round(time.time()-$T_START,3))")
printf '{"ready":%s,"waited_s":%s,"wm":%s,"panel":%s,"desktop":%s}\n' \
  "$([ $READY = 1 ] && echo true || echo false)" "$WAITED" "$WM" "$PANEL" "$DESK" \
  > "$EVIDENCE/session-ready.json"

if [ "$READY" = 1 ]; then
  # V4 (2): the :3 session's tracer must be the runner's (judged by xfce_v6_judge.py)
  XS_PID=$(ours | awk '$2 == "xfce4-session" {print $1; exit}' || true)
  if [ -n "$XS_PID" ]; then python3 "$V6/tracer_ident.py" --pid "$XS_PID" --out "$EVIDENCE/xfce-session-tracer.json" >/dev/null || true
  else echo '{"tracer_pid": null, "why": "xfce4-session not found"}' > "$EVIDENCE/xfce-session-tracer.json"; fi
  sleep "$(python3 -c "import json;print(json.load(open('$FREEZE'))['p01_duration']['settle_after_ready_s'])")"
  clients_json "$EVIDENCE/xfce-clients-K1.json"
  ksample K1
  DBUS_ADDR=$(cat "$STATE/dbus-address" 2>/dev/null || true)
  echo "dbus_address=$DBUS_ADDR" > "$EVIDENCE/dbus-address.txt"
  set +e
  "${SESSION_ENV[@]}" DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" python3 "$XFCE/choreo.py" \
    --freeze "$FREEZE" --state-dir "$STATE/choreo" --log "$EVIDENCE/steps.jsonl" \
    --term-load "$XFCE/term_load.sh" > "$EVIDENCE/choreo.out" 2>&1 < /dev/null
  echo "choreo_rc=$?" > "$EVIDENCE/choreo-rc.txt"
  set -e
  clients_json "$EVIDENCE/xfce-clients-K2.json"
  ksample K2

  # ---- logout (freeze p10)
  T_LO=$(date +%s.%N)
  "${SESSION_ENV[@]}" DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" xfce4-session-logout --logout --fast \
    > "$EVIDENCE/logout.out" 2>&1 < /dev/null || true
  LO_OK=false
  for i in $(seq 1 90); do
    if [ -z "$(ours)" ]; then LO_OK=true; break; fi
    sleep 0.5
  done
  LEFT=$(ours | tr '\n' ';' || true)
  LO_W=$(python3 -c "import time;print(round(time.time()-$T_LO,3))")
  python3 -c "import json,sys;json.dump({'ok':sys.argv[1]=='true','waited_s':float(sys.argv[2]),'leftovers':[x for x in sys.argv[3].split(';') if x]},open(sys.argv[4],'w'),indent=2)" \
    "$LO_OK" "$LO_W" "$LEFT" "$EVIDENCE/logout.json"
else
  echo '{"ok":false,"waited_s":null,"leftovers":["session_never_ready"]}' > "$EVIDENCE/logout.json"
  # INVALID run: nothing to preserve. Stop our own session processes by exact pid
  # (recorded) so the terminate below does not tear down live clients.
  { echo "session_never_ready_kill:"; ours; } >> "$EVIDENCE/cleanup.txt"
  ours | awk '{print $1}' | while read -r p; do kill -TERM "$p" 2>/dev/null || true; done
  sleep 3
fi
SL_RC=0; wait "$SESSION_LAUNCHER" 2>/dev/null || SL_RC=$?
echo "dbus_run_session_exit=$SL_RC" >> "$EVIDENCE/session-launcher.txt"
[ -z "$(ours)" ] || { echo "leftovers_after_logout:" >> "$EVIDENCE/cleanup.txt"; ours >> "$EVIDENCE/cleanup.txt"; }

else
  # MODE=preflight (freeze 5.2 + section 9 deviation 1): no session; probes + 3 x 1000 ms GrabServer
  set +e
  python3 "$V6/preflight_probe.py" --out "$EVIDENCE" --display :3 > "$EVIDENCE/preflight-probe.out" 2>&1
  echo "preflight_probe_rc=$?" > "$EVIDENCE/preflight-probe-rc.txt"
  set -e
fi

ksample K3
stop_poller

# ---------------------------------------------------------------- clean close --
timeout 60 "$FIXTURE" --display :3 --mode terminate --client-log "$EVIDENCE/terminate.jsonl" \
  > "$EVIDENCE/terminate.out" 2>&1 || true
for i in $(seq 1 60); do [ -d "/proc/$X3" ] || break; sleep 0.5; done
XA=false; [ -d "/proc/$X3" ] && XA=true
echo "{\"x_alive_after_terminate\": $XA}" > "$EVIDENCE/close.json"
if [ -f "$SUMMARY" ]; then cp -a "$SUMMARY" "$EVIDENCE/gatea-summary.txt"; else : > "$EVIDENCE/gatea-summary.txt"; fi
if [ -f "$RING" ]; then cp -a "$RING" "$EVIDENCE/gatea-ring.txt"; else : > "$EVIDENCE/gatea-ring.txt"; fi
sleep 2
ACT_AFTER=$(act_pid_now) || ACT_AFTER=""
echo "activity_pid_after_close=$ACT_AFTER" > "$EVIDENCE/activity-pid-after-close.txt"
if [ "$XA" = false ]; then ksample K4 --no-x; else ksample K4; fi

# ---------------------------------------------------------------- end --
touch_stop
screen_json "$EVIDENCE/screen-post.json"
sleep 1
LA=false; [ -n "$LOGCAT_PID" ] && [ -d "/proc/$LOGCAT_PID" ] && LA=true
echo "{\"logcat_alive\": $LA}" > "$EVIDENCE/capture-end.json"
stop_logcat "$LOGCAT_PID" || true; LOGCAT_PID=""
stable_json "$EVIDENCE/stable-after.json"
ls /tmp/.X11-unix/ > "$EVIDENCE/x11-unix-after.txt" 2>&1 || true
mkdir -p "$EVIDENCE/state"
cp -a "$STATE/." "$EVIDENCE/state/" 2>/dev/null || true
mg_stop
if [ -e "$EVIDENCE/MEM-GUARD-TRIPPED.txt" ]; then
  (cd "$EVIDENCE" && find . -type f ! -name sha256sums.txt | sort | xargs sha256sum > sha256sums.txt)
  echo "XFCE_ABORTED_MEM_GUARD evidence=$EVIDENCE $(head -1 "$EVIDENCE/MEM-GUARD-TRIPPED.txt")"
  exit 5
fi
echo "XFCE_CAPTURED mode=$MODE variant=$VARIANT evidence=$EVIDENCE"
