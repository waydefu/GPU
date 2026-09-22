#!/usr/bin/env bash
# R10 runner — product dc94485. ORCHESTRATES AND CAPTURES ONLY.
#
# Every judgement-relevant inference lives in tests/r10/ and is unit-tested offline.
# A runner that infers is a runner that cannot be tested without a device, and R8
# spent nine defects learning that.
#
#   MODE      noise | A | B | C
#   ROUNDS    >= 5 for noise/B/C; iterations for A
#   EVIDENCE  must NOT already exist
#   SERIAL    required unless VALIDATE_ONLY=1
#   VALIDATE_ONLY=1   zero device mutation, exits before SERIAL is read
#
# MODES (V2-R10-DESIGN §3)
#   A      one X session, one Activity, ROUNDS workload iterations
#   B      one SURVIVING Activity, ROUNDS consecutive X sessions, each ending clean.
#          Sessions 2..N exercise the warm reattach (D-06 §2.4): new X, new nonce,
#          generation 1, empty registry. NOT generation 2.
#   C      ROUNDS x (fresh Activity + fresh X), each ending clean
#   E      the two UNCLEAN endings, one round each, followed by a fresh session.
#          Judged on inheritance and residue ONLY - they release nothing by design,
#          so a leak metric taken after them measures the OS, not Gate A.
#            E1 "F"  X publishes a fatal (armed fault) -> Activity takes PRESERVE
#            E2 "H"  X is SIGKILLed with no published fatal -> Activity takes r-hup
#          The SIGKILL in E2 is CONSTRUCTION, not cleanup: r-hup is the evidence the
#          round exists to capture, and it is recorded, never suppressed.
#   noise  structurally identical to B, workload replaced by an idle hold
#
# exit 3 = BLOCKED (round not consumed)   2 = INVALID   0 = captured
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=/root/projects/GPU加速
R10=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/r10
ROOT_HARNESS=$ROOT/evidence/session/gate-a-a1/p2-r3-terminal-runtime
RUN_NORESET=$ROOT/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3-noreset.py
SAMPLE=$R10/r10_sample.py
FIXTURE=/tmp/p_r10_ledger
FIXTURE_SRC=$R10/p_r10_ledger.c
TADB=/data/data/com.termux/files/usr/bin/adb
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt

EXPECT_PACKAGE=com.waydefu.x11gpu
EXPECT_VERSION=1.03.01-dc94485-22.09.26
EXPECT_APK_SHA256=1bd8bef0909249737ea43acf0a35f3c995d941e1badbfcf370e5cd854f4bb8a3
EXPECT_HEAD=dc94485a7ef4f74cada36ea3c1d35d0aa0f48693
EXPECT_FIXTURE_SRC_SHA=7d2068bf3db1f68686e22d310c75c08a074851f1845790b38f1bfbe696d7ead0
IDLE_HOLD_MS=4000          # matches the measured wall time of one workload unit

refuse() { echo "R10_BLOCKED $*"; exit 3; }
invalid() { echo "R10_INVALID $*"; exit 2; }

MODE="${MODE:-}"; ROUNDS="${ROUNDS:-}"; EVIDENCE="${EVIDENCE:-}"
VALIDATE_ONLY="${VALIDATE_ONLY:-0}"
[ -n "$MODE" ] || refuse "MODE"
case "$MODE" in noise|A|B|C|E) ;; *) refuse "bad_mode $MODE";; esac
[ -n "$ROUNDS" ] || refuse "ROUNDS"
case "$MODE" in
  noise|B|C) [ "$ROUNDS" -ge 5 ] || refuse "rounds_below_5 $ROUNDS";;   # §9.2
esac
[ -n "$EVIDENCE" ] || refuse "EVIDENCE"

if [ "$VALIDATE_ONLY" = 1 ]; then
  echo "R10_RUNNER_DC94485_V1_VALIDATE_ONLY mode=$MODE rounds=$ROUNDS"
  exit 0
fi

[ -n "${SERIAL:-}" ] || refuse "SERIAL"
[ -e "$EVIDENCE" ] && refuse "evidence_exists $EVIDENCE"
for f in "$SAMPLE" "$FIXTURE" "$FIXTURE_SRC" "$RUN_NORESET"; do
  [ -f "$f" ] || refuse "missing_tool $f"
done
GOT=$(sha256sum "$FIXTURE_SRC" | awk '{print $1}')
[ "$GOT" = "$EXPECT_FIXTURE_SRC_SHA" ] || refuse "fixture_src_sha $GOT"

export CELL="$EVIDENCE"
# shellcheck source=harness-lib.sh
source "$ROOT_HARNESS/harness-lib.sh"

ADB get-state >/dev/null 2>&1 || refuse "ADB_DISCONNECTED"
mkdir -p "$EVIDENCE"
sha256sum "$FIXTURE" "$FIXTURE_SRC" > "$EVIDENCE/fixture.sha256.txt"

X3=""
r10_cleanup() {
  if [ -n "${X3:-}" ] && [ -d "/proc/$X3" ]; then
    local cmd; cmd=$(tr '\0' ' ' < "/proc/$X3/cmdline" 2>/dev/null || true)
    case "$cmd" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) kill -TERM "$X3" 2>/dev/null || true;;
    esac
  fi
  ADB shell am force-stop "$EXPECT_PACKAGE" >/dev/null 2>&1 || true
}
trap 'cleanup; r10_cleanup' EXIT

# stable_json — copied verbatim from the R8/R9 runners so the Stable-unchanged proof
# is byte-for-byte the same one every packet used.
stable_json() {
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

# The session tuple cannot come from the summary: a clean close zeroes both halves
# before the dump, so nonce=0 generation=0 there is the CLOSE's signature, not the
# session's identity. It has to be read from GATEA_BIND, which means the ledger needs
# to know which lines of the single streamed logcat belong to which round.
mark_logcat() { # mark_logcat <round> begin|end
  wc -l < "$EVIDENCE/raw-logcat.txt" 2>/dev/null | tr -d ' ' \
    > "$EVIDENCE/r$1/logcat-offset-$2.txt" || echo 0 > "$EVIDENCE/r$1/logcat-offset-$2.txt"
}

sample() { # sample <round> <tag> [--no-x]
  local r=$1 t=$2 nox=${3:-}
  local args=(--tag "$t" --serial "$SERIAL" --package "$EXPECT_PACKAGE"
              --summary "$SUMMARY" --ring "$RING"
              --out "$EVIDENCE/r$r/sample-$t.json")
  [ "$nox" = "--no-x" ] || args+=(--x-pid "$X3")
  local ap; ap=$(act_pid_now) || ap=""
  [ -n "$ap" ] && args+=(--act-pid "$ap")
  python3 "$SAMPLE" "${args[@]}" >/dev/null
}

# ------------------------------------------------------------------ preflight --
ADB shell dumpsys package "$EXPECT_PACKAGE" | grep -E 'versionName=' | head -1 \
  | tee "$EVIDENCE/experimental-package-pre.txt" | grep -q "versionName=$EXPECT_VERSION" \
  || refuse "version_mismatch"
INSTALLED=$(ADB shell pm path "$EXPECT_PACKAGE" | tr -d '\r' | sed -n 's/^package://p' | head -1)
[ -n "$INSTALLED" ] || refuse "apk_path_unresolved"
GOT_APK=$(ADB shell sha256sum "$INSTALLED" | tr -d '\r' | awk '{print $1}')
echo "installed_apk_sha256=$GOT_APK" > "$EVIDENCE/installed-apk.sha256.txt"
[ "$GOT_APK" = "$EXPECT_APK_SHA256" ] || refuse "apk_sha256_mismatch $GOT_APK"
printf '{"mode":"%s","rounds":%s,"source_sha":"%s","apk_sha256":"%s"}\n' \
  "$MODE" "$ROUNDS" "$EXPECT_HEAD" "$EXPECT_APK_SHA256" > "$EVIDENCE/run-binding.json"

stable_json "$EVIDENCE/stable-before.json"
x3pid_now >/dev/null 2>&1 && refuse "x3_already_running"

SINCE=$(date '+%m-%d %H:%M:%S.000')
echo "logcat_since=$SINCE" > "$EVIDENCE/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$EVIDENCE/raw-logcat.txt" "$SINCE")
verify_logcat_pid "$LOGCAT_PID"

export TERMUX_X11_GATEA_PROTO=1 TERMUX_X11_GATEA_TELEMETRY=1
export TERMUX_X11_R8_ARM=1 TERMUX_X11_R8_CASE=R8-C1   # no fault: the pairing rule in
# parseArm() does not apply, so R8 observation can stay armed. It is what registers
# the LORIE-R8-TEST extension, which --mode terminate needs for the clean close.
env | grep -E '^(TERMUX_X11_|MODE|ROUNDS)' | sort > "$EVIDENCE/env-cell.txt"

start_x() {
  rm -f "$SUMMARY" "$RING" || true
  python3 "$RUN_NORESET" >> "$EVIDENCE/start-x3.out" 2>&1
  local i
  for i in $(seq 1 40); do X3=$(x3pid_now) && break || sleep 0.5; done
  [ -n "$X3" ] || invalid "x3_missing"
  tr '\0' ' ' < "/proc/$X3/cmdline" | grep -q -- '-noreset' || refuse "noreset_absent"
}
start_activity() {
  ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' \
    >> "$EVIDENCE/am-start.out" 2>&1
  sleep 4
}
freeze_dump() { # freeze_dump <round>
  if [ -f "$SUMMARY" ]; then cp -a "$SUMMARY" "$EVIDENCE/r$1/gatea-summary.txt"; else : > "$EVIDENCE/r$1/gatea-summary.txt"; fi
  if [ -f "$RING" ]; then cp -a "$RING" "$EVIDENCE/r$1/gatea-ring.txt"; else : > "$EVIDENCE/r$1/gatea-ring.txt"; fi
}
run_client() { # run_client <round> <mode> ; answers both handshakes with a sample between
  # Split, deliberately. `local r=$1 m=$2 sd="...$r..."` expands $r against the
  # OUTER scope, which the A/B/C branches happen to have (their loop variable is
  # also called r) and the E branch does not - it died with "r: unbound variable"
  # under set -u, mid-round, in r10-e-01.
  local r=$1
  local m=$2
  local sd="$EVIDENCE/r$r/state"
  mkdir -p "$sd"
  local extra=()
  [ "$m" = idle ] && extra=(--hold-ms "$IDLE_HOLD_MS")
  ( timeout 180 "$FIXTURE" --display :3 --mode "$m" --state-dir "$sd" \
      --client-log "$EVIDENCE/r$r/client.jsonl" "${extra[@]}" \
      > "$EVIDENCE/r$r/client.out" 2>&1; echo $? > "$sd/rc" ) &
  local cpid=$! tag i
  for tag in A1 A2; do
    for i in $(seq 1 1800); do [ -f "$sd/at-$tag" ] && break; sleep 0.1; done
    [ -f "$sd/at-$tag" ] || { wait "$cpid" || true; invalid "handshake_${tag}_never_reached"; }
    sample "$r" "$tag"
    touch "$sd/go-$tag"
  done
  wait "$cpid" || true
  local rc; rc=$(cat "$sd/rc" 2>/dev/null || echo 99)
  echo "client_rc=$rc" > "$EVIDENCE/r$r/client-rc.txt"
  [ "$rc" = 0 ] || invalid "client_rc_$rc round=$r"
}
close_session() { # close_session <round>  -- the ONLY clean ending
  timeout 60 "$FIXTURE" --display :3 --mode terminate \
    --client-log "$EVIDENCE/r$1/terminate.jsonl" > "$EVIDENCE/r$1/terminate.out" 2>&1 || true
  local i
  for i in $(seq 1 60); do [ -d "/proc/$X3" ] || break; sleep 0.5; done
  if [ -d "/proc/$X3" ]; then echo "x_alive_after_terminate=true" > "$EVIDENCE/r$1/x-close.txt"
  else echo "x_alive_after_terminate=false" > "$EVIDENCE/r$1/x-close.txt"; fi
  freeze_dump "$1"
}

export DISPLAY=:3
CLIENT_MODE=workload; [ "$MODE" = noise ] && CLIENT_MODE=idle

case "$MODE" in
  A)
    mkdir -p "$EVIDENCE/r1"; mark_logcat 1 begin      # session 1 binds during start_x
    start_x; start_activity
    for r in $(seq 1 "$ROUNDS"); do
      mkdir -p "$EVIDENCE/r$r"; [ "$r" -gt 1 ] && mark_logcat "$r" begin
      sample "$r" A0
      run_client "$r" "$CLIENT_MODE"
      mark_logcat "$r" end
    done
    mkdir -p "$EVIDENCE/rclose"; X3_KEEP=$X3; close_session "close"
    ;;
  B|noise)
    mkdir -p "$EVIDENCE/r1"; mark_logcat 1 begin      # session 1 binds during start_x
    start_x; start_activity            # session 1 gets a fresh Activity
    ACT1=$(act_pid_now); echo "activity_pid_session1=$ACT1" > "$EVIDENCE/activity-pid.txt"
    for r in $(seq 1 "$ROUNDS"); do
      mkdir -p "$EVIDENCE/r$r"; [ "$r" -gt 1 ] && mark_logcat "$r" begin
      if [ "$r" -gt 1 ]; then
        start_x                        # the Activity is ALREADY running: warm reattach
        sleep 5                        # ACTION_START is re-broadcast once a second
      fi
      sample "$r" B0
      run_client "$r" "$CLIENT_MODE"
      sample "$r" B1
      close_session "$r"
      sample "$r" B3 --no-x            # X is gone; the Activity must not be
      ACTN=$(act_pid_now) || ACTN=""
      echo "activity_pid=$ACTN" > "$EVIDENCE/r$r/activity-pid.txt"
      mark_logcat "$r" end
    done
    ;;
  C)
    for r in $(seq 1 "$ROUNDS"); do
      mkdir -p "$EVIDENCE/r$r"; mark_logcat "$r" begin
      ADB shell am force-stop "$EXPECT_PACKAGE" >/dev/null 2>&1 || true
      sleep 2
      start_x; start_activity
      sample "$r" B0
      run_client "$r" "$CLIENT_MODE"
      sample "$r" B1
      close_session "$r"
      sample "$r" B3 --no-x
      echo "activity_pid=$(act_pid_now || true)" > "$EVIDENCE/r$r/activity-pid.txt"
      ls /tmp/.X11-unix/ > "$EVIDENCE/r$r/x11-unix.txt" 2>&1 || true
      mark_logcat "$r" end
    done
    ;;
  E)
    # ---- E1: the F ending. An armed fault means R8 observation must be DISARMED:
    # parseArm() hard-codes the only two legal (case, fault) pairs and sets
    # r8EnvFatal for any other case with any fault, which halts X at startup
    # (measured: r9-cold-2/attempt-01). No terminate is needed here - the fatal IS
    # the ending - so losing the extension costs nothing.
    unset TERMUX_X11_R8_ARM TERMUX_X11_R8_CASE
    export TERMUX_X11_GATEA_TEST_FAULT=renderer-fatal-pre-fence
    export TERMUX_X11_GATEA_TEST_ARM=1
    env | grep -E '^TERMUX_X11_' | sort > "$EVIDENCE/env-cell-E1.txt"
    mkdir -p "$EVIDENCE/r1"; mark_logcat 1 begin
    start_x; start_activity
    ACT_BEFORE=$(act_pid_now) || ACT_BEFORE=""
    echo "activity_pid_before=$ACT_BEFORE" > "$EVIDENCE/r1/identity-before.txt"
    echo "x_pid_before=$X3" >> "$EVIDENCE/r1/identity-before.txt"
    sample 1 B0
    # the fault fires inside the composite; the client is EXPECTED to lose the server
    timeout 120 "$FIXTURE" --display :3 --mode workload \
      --client-log "$EVIDENCE/r1/client.jsonl" > "$EVIDENCE/r1/client.out" 2>&1 || true
    sleep 4
    [ -d "/proc/$X3" ] && echo "x_alive_after=true" > "$EVIDENCE/r1/ending.txt" \
                       || echo "x_alive_after=false" > "$EVIDENCE/r1/ending.txt"
    ACT_AFTER=$(act_pid_now) || ACT_AFTER=""
    echo "activity_pid_after=$ACT_AFTER" >> "$EVIDENCE/r1/ending.txt"
    freeze_dump 1
    mark_logcat 1 end

    # ---- E2: the H ending. No fault; X is killed outright so nothing is published.
    unset TERMUX_X11_GATEA_TEST_FAULT TERMUX_X11_GATEA_TEST_ARM
    export TERMUX_X11_R8_ARM=1 TERMUX_X11_R8_CASE=R8-C1
    env | grep -E '^TERMUX_X11_' | sort > "$EVIDENCE/env-cell-E2.txt"
    mkdir -p "$EVIDENCE/r2"; mark_logcat 2 begin
    ADB shell am force-stop "$EXPECT_PACKAGE" >/dev/null 2>&1 || true; sleep 2
    start_x; start_activity
    echo "x_pid_before=$X3" > "$EVIDENCE/r2/identity-before.txt"
    echo "activity_pid_before=$(act_pid_now || true)" >> "$EVIDENCE/r2/identity-before.txt"
    sample 2 B0
    run_client 2 workload
    sample 2 B1
    # CONSTRUCTION, not cleanup: an abrupt X death with nothing published is exactly
    # the H ending, and the r-hup it produces is the evidence the round captures.
    echo "sigkill_target_pid=$X3" > "$EVIDENCE/r2/h-construction.txt"
    tr '\0' ' ' < "/proc/$X3/cmdline" >> "$EVIDENCE/r2/h-construction.txt" 2>/dev/null || true
    kill -KILL "$X3" 2>/dev/null || true
    sleep 4
    [ -d "/proc/$X3" ] && echo "x_alive_after=true" > "$EVIDENCE/r2/ending.txt" \
                       || echo "x_alive_after=false" > "$EVIDENCE/r2/ending.txt"
    echo "activity_pid_after=$(act_pid_now || true)" >> "$EVIDENCE/r2/ending.txt"
    freeze_dump 2
    mark_logcat 2 end

    # ---- E3: the fresh session that must inherit NOTHING from either ending
    mkdir -p "$EVIDENCE/r3"; mark_logcat 3 begin
    ADB shell am force-stop "$EXPECT_PACKAGE" >/dev/null 2>&1 || true; sleep 2
    start_x; start_activity
    sample 3 B0
    run_client 3 workload
    sample 3 B1
    close_session 3
    sample 3 B3 --no-x
    echo "activity_pid=$(act_pid_now || true)" > "$EVIDENCE/r3/activity-pid.txt"
    mark_logcat 3 end
    ;;
esac

sleep 1
stop_logcat "$LOGCAT_PID" || true; LOGCAT_PID=""
stable_json "$EVIDENCE/stable-after.json"
ls /tmp/.X11-unix/ > "$EVIDENCE/x11-unix-after.txt" 2>&1 || true
echo "R10_CAPTURED mode=$MODE rounds=$ROUNDS evidence=$EVIDENCE"
