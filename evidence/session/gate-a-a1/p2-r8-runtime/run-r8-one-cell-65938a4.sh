#!/usr/bin/env bash
# 65938a4 R8 one-cell live runner. Experimental :3 / com.waydefu.x11gpu only.
# VALIDATE_ONLY=1 performs zero device mutation.
# Usage live:
#   SERIAL=HOST:PORT CELL_ID=R8-C1 EVIDENCE=.../r8-c1/attempt-01 \
#     bash run-r8-one-cell-65938a4.sh
set -euo pipefail

HERE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r8-runtime
ROOT_HARNESS=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
SRC=/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
FIXTURE=/tmp/p_r8_lifecycle
SPEC="$SRC/tests/r8/lifecycle-cell-spec.json"
JUDGE="$SRC/tests/r8/judge-r8.py"
COLLECT="$SRC/tests/r8/collect-r8.py"
MANIFEST="$HERE/runtime-65938a4/r8-runtime-tooling-manifest.json"
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
EXPECT_HEAD=65938a447639fce2adae61a15a2d8348e7c6455f
EXPECT_VERSION=1.03.01-65938a4-18.09.26
EXPECT_VERSION_CODE=15
EXPECT_PACKAGE=com.waydefu.x11gpu
EXPECT_BUILD_ID=21770f736570ae13b7635d7765c3d8470b40cfa7
EXPECT_APK_SHA256=b88f12ecdb6a6fb9bf8db724b4dbee5ac363cb863f8246bc15ac08bc20c31a6c
EXPECT_SIGNER=b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1
EXPECT_FIXTURE_SHA=d3910436ca6489a991725f5293d915286c04b911f4526b95d84ce7cbfb200493
EXPECT_CI=35311343984

refuse() { echo "R8_BLOCKED $*"; exit 3; }

VALIDATE_ONLY="${VALIDATE_ONLY:-0}"
CELL_ID="${CELL_ID:-}"
EVIDENCE="${EVIDENCE:-}"
[ -n "$CELL_ID" ] || refuse "CELL_ID"
[ -n "$EVIDENCE" ] || refuse "EVIDENCE"
case "$CELL_ID" in
  R8-C1|R8-C2|R8-C3-window|R8-C3-disconnect|R8-C4|R8-C5-full|R8-C5-overflow|R8-D|R8-P1|R8-P2) ;;
  *) refuse "bad_cell $CELL_ID";;
esac
if [ "$VALIDATE_ONLY" = 1 ]; then
  echo "R8_LIVE_RUNNER_VALIDATE_ONLY $CELL_ID"
  exit 0
fi
[ -n "${SERIAL:-}" ] || refuse "SERIAL"
if [ -e "$EVIDENCE" ]; then
  refuse "evidence_exists $EVIDENCE"
fi
mkdir -p "$EVIDENCE"
# shellcheck source=harness-lib.sh
source "$ROOT_HARNESS/harness-lib.sh"

GOT_FIX=$(sha256sum "$FIXTURE" | awk '{print $1}')
[ "$GOT_FIX" = "$EXPECT_FIXTURE_SHA" ] || refuse "fixture_sha $GOT_FIX"
cp "$MANIFEST" "$EVIDENCE/manifest.json"
echo "grant R8-amendment-65938a4 cell=$CELL_ID" > "$EVIDENCE/grant-reference.txt"

{
  echo "source_sha=$EXPECT_HEAD"
  echo "apk_sha256=$EXPECT_APK_SHA256"
  echo "build_id=$EXPECT_BUILD_ID"
  echo "signer=$EXPECT_SIGNER"
  echo "ci=$EXPECT_CI"
  echo "versionName=$EXPECT_VERSION"
} > "$EVIDENCE/artifact-binding.txt"
python3 - "$EVIDENCE" "$EXPECT_HEAD" "$EXPECT_APK_SHA256" "$EXPECT_BUILD_ID" "$EXPECT_SIGNER" <<'PY'
import json,sys
from pathlib import Path
d=Path(sys.argv[1])
json.dump({
  "source_sha": sys.argv[2], "apk_sha256": sys.argv[3],
  "build_id": sys.argv[4], "signer": sys.argv[5]
}, open(d/"artifact-binding.json","w"), indent=2)
PY

dumpsys_pkg() {
  ADB shell dumpsys package "$1" | grep -E 'versionName=|versionCode=|lastUpdateTime=' | head -6
}

stable_json() {
  local out=$1 pid cmd vn vc lu
  pid=$(stabpid) || refuse "stable_pid"
  cmd=$(stab_cmd)
  echo "$cmd" | grep -q '^termux-x11 com.termux.x11 :1' || refuse "stable_cmd"
  ADB shell dumpsys package com.termux.x11 > "$out.raw" || true
  python3 - "$out" "$out.raw" "$pid" "$cmd" <<'PY'
import json,re,sys
text=open(sys.argv[2],encoding="utf-8",errors="replace").read()
vn=re.search(r"versionName=(\S+)", text)
vc=re.search(r"versionCode=(\d+)", text)
lu=re.search(r"lastUpdateTime=(.+)", text)
json.dump({
  "pid": int(sys.argv[3]), "cmdline": sys.argv[4].strip(),
  "versionName": vn.group(1) if vn else None,
  "versionCode": int(vc.group(1)) if vc else None,
  "lastUpdateTime": lu.group(1).strip() if lu else None,
}, open(sys.argv[1],"w"), indent=2)
print("stable_pid", sys.argv[3])
PY
}

stable_json "$EVIDENCE/stable-before.json"
ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'versionName=|versionCode=' | head -4 | tee "$EVIDENCE/experimental-package-pre.txt"
grep -q "versionName=$EXPECT_VERSION" "$EVIDENCE/experimental-package-pre.txt" || refuse "version_mismatch"
dumpsys_pkg com.termux.x11 | tee "$EVIDENCE/stable-package-pre.txt"

ADB shell getprop ro.product.device | tr -d '\r' | tee "$EVIDENCE/device.txt"
grep -q myron "$EVIDENCE/device.txt"
ADB shell dumpsys power | grep mWakefulness= | head -1 | tee "$EVIDENCE/screen.txt"
ADB shell dumpsys window | grep isKeyguardShowing= | head -1 >> "$EVIDENCE/screen.txt"
grep -q 'mWakefulness=Awake' "$EVIDENCE/screen.txt"
grep -q 'isKeyguardShowing=false' "$EVIDENCE/screen.txt"
ADB shell dumpsys display | grep -E 'uniqueId=|mType=|Display id=' | head -20 | tee "$EVIDENCE/hdmi-observe.txt" || true

if X3=$(x3pid); then
  echo "REFUSE preexisting X3 pid=$X3" | tee "$EVIDENCE/preexisting-x3.txt"
  refuse "preexisting_x3"
fi
printf '{"observed":true,"substituted_from_cleanup":false,"unsafe_prestart":false,"artifact_mismatch":false}\n' \
  > "$EVIDENCE/preflight.json"

rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
  /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock || true
rm -f "$SUMMARY" "$RING" || true
ADB shell am force-stop com.waydefu.x11gpu
sleep 1
ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' | tee "$EVIDENCE/am-start.out"
ADB shell dumpsys activity activities > "$EVIDENCE/dumpsys-activity.txt"
assert_display0 "$EVIDENCE/dumpsys-activity.txt"

SINCE=$(ADB shell "date '+%m-%d %H:%M:%S.000'" | tr -d '\r')
echo "logcat_since=$SINCE" | tee "$EVIDENCE/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$EVIDENCE/raw-logcat.txt" "$SINCE")
echo "$LOGCAT_PID" > "$EVIDENCE/logcat.pid"
for i in $(seq 1 20); do
  exe=$(readlink "/proc/$LOGCAT_PID/exe" 2>/dev/null || true)
  [ "$exe" = "$TADB" ] && break
  sleep 0.1
done
verify_logcat_pid "$LOGCAT_PID"

export GATEA_X3_LAUNCHER_LOG="$EVIDENCE/x3-launcher.raw.log"
: > "$GATEA_X3_LAUNCHER_LOG"
while IFS= read -r name; do
  [ -n "$name" ] || continue
  unset "$name" || true
done < <(env | awk -F= '/^TERMUX_X11_GATEA_|^TERMUX_X11_R8_/ {print $1}' || true)
unset TERMUX_X11_DEBUG || true
unset TERMUX_X11_B3A_TELEMETRY || true
export TERMUX_X11_GATEA_PROTO=1
export TERMUX_X11_GATEA_TELEMETRY=1
export TERMUX_X11_R8_ARM=1
export TERMUX_X11_R8_CASE="$CELL_ID"
unset TERMUX_X11_GATEA_TEST_FAULT TERMUX_X11_GATEA_TEST_ARM TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL || true
if [ "$CELL_ID" = "R8-P1" ]; then
  export TERMUX_X11_GATEA_TEST_FAULT=destroy-while-gpu-owned
  export TERMUX_X11_GATEA_TEST_ARM=1
fi
if [ "$CELL_ID" = "R8-P2" ]; then
  export TERMUX_X11_GATEA_TEST_FAULT=close-while-lease
  export TERMUX_X11_GATEA_TEST_ARM=1
fi
env | sort > "$EVIDENCE/env.txt"
python3 "$RUN" | tee "$EVIDENCE/start-x3.out"
X3=""
for i in $(seq 1 40); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3" || refuse "x3_missing"
echo "x3_pid=$X3" | tee "$EVIDENCE/x3-pid.txt"
save_x_identity "$X3" "$EVIDENCE"
tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11' | tee "$EVIDENCE/x-environ-all-termux-x11.txt" || true
python3 - "$EVIDENCE/x-environ-all-termux-x11.txt" "$CELL_ID" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text() if Path(sys.argv[1]).exists() else ""
cell = sys.argv[2]
got = {ln for ln in text.splitlines() if ln.startswith("TERMUX_X11_GATEA_") or ln.startswith("TERMUX_X11_R8_")}
need = {
    "TERMUX_X11_GATEA_PROTO=1",
    "TERMUX_X11_GATEA_TELEMETRY=1",
    "TERMUX_X11_R8_ARM=1",
    f"TERMUX_X11_R8_CASE={cell}",
}
if cell == "R8-P1":
    need |= {"TERMUX_X11_GATEA_TEST_FAULT=destroy-while-gpu-owned", "TERMUX_X11_GATEA_TEST_ARM=1"}
elif cell == "R8-P2":
    need |= {"TERMUX_X11_GATEA_TEST_FAULT=close-while-lease", "TERMUX_X11_GATEA_TEST_ARM=1"}
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
  refuse "x3_died_during_ready"
fi
echo "ALIVE_8S pid=$X3" | tee "$EVIDENCE/alive.txt"

export DISPLAY=:3
export TMPDIR=/data/data/com.termux/files/usr/tmp
HOLD=0
case "$CELL_ID" in
  R8-C2|R8-C5-full) HOLD=1;;
esac
set +e
if [ "$HOLD" = 1 ]; then
  "$FIXTURE" --display :3 --cell "$CELL_ID" --spec "$SPEC" --client-log "$EVIDENCE/fixture.jsonl" \
    > "$EVIDENCE/fixture.stdout" 2>"$EVIDENCE/fixture.stderr" &
  FIXPID=$!
  echo "$FIXPID" > "$EVIDENCE/fixture.pid"
  for i in $(seq 1 40); do
    grep -q 'CLIENT_HOLD' "$EVIDENCE/fixture.jsonl" 2>/dev/null && break
    grep -q 'CLIENT_HOLD' "$EVIDENCE/fixture.stdout" 2>/dev/null && break
    sleep 0.25
  done
  if ! grep -q 'CLIENT_HOLD' "$EVIDENCE/fixture.jsonl" "$EVIDENCE/fixture.stdout" 2>/dev/null; then
    echo "NO_CLIENT_HOLD" | tee "$EVIDENCE/hold-status.txt"
  else
    echo "CLIENT_HOLD" | tee "$EVIDENCE/hold-status.txt"
  fi
  if [ -d "/proc/$X3" ]; then
    kill -TERM "$X3" || true
    echo "requested_TERM pid=$X3" | tee "$EVIDENCE/requested-term.txt"
  fi
  wait "$FIXPID" 2>/dev/null
  FIX_RC=$?
else
  timeout 20 "$FIXTURE" --display :3 --cell "$CELL_ID" --spec "$SPEC" --client-log "$EVIDENCE/fixture.jsonl" \
    > "$EVIDENCE/fixture.stdout" 2>"$EVIDENCE/fixture.stderr"
  FIX_RC=$?
  if [ -d "/proc/$X3" ] && [ "$CELL_ID" != "R8-P1" ] && [ "$CELL_ID" != "R8-P2" ]; then
    kill -TERM "$X3" || true
    echo "requested_TERM pid=$X3" | tee "$EVIDENCE/requested-term.txt"
    for i in $(seq 1 20); do
      [ ! -d "/proc/$X3" ] && break
      sleep 0.25
    done
  fi
fi
set -e
echo "FIXTURE_EXIT=$FIX_RC" | tee "$EVIDENCE/fixture-exit.txt"

sleep 1
if [ -f "$SUMMARY" ]; then cp -a "$SUMMARY" "$EVIDENCE/gatea-summary.txt"; else echo NONE > "$EVIDENCE/gatea-summary.txt"; fi
if [ -f "$RING" ]; then cp -a "$RING" "$EVIDENCE/gatea-ring.txt"; else echo NONE > "$EVIDENCE/gatea-ring.txt"; fi
kill -TERM "$LOGCAT_PID" 2>/dev/null || true
wait "$LOGCAT_PID" 2>/dev/null || true

{
  if [ -d "/proc/$X3" ]; then echo "x_pre_cleanup=ALIVE pid=$X3"; else echo "x_pre_cleanup=DEAD pid=$X3"; fi
} | tee "$EVIDENCE/pre-cleanup-process.txt"
python3 - "$EVIDENCE" <<'PY'
import json,sys
from pathlib import Path
d=Path(sys.argv[1])
text=(d/"pre-cleanup-process.txt").read_text()
json.dump({
  "observed": True,
  "substituted_from_cleanup": False,
  "x_pre_cleanup": "ALIVE" if "ALIVE" in text else "DEAD",
}, open(d/"pre-cleanup-process-state.json","w"), indent=2)
PY

python3 "$COLLECT" --raw "$EVIDENCE/raw-logcat.txt" \
  --out-x "$EVIDENCE/x-observations.jsonl" \
  --out-r "$EVIDENCE/renderer-observations.jsonl" \
  --completeness "$EVIDENCE/completeness.json" || true
if [ -f "$EVIDENCE/gatea-ring.txt" ]; then
  python3 "$COLLECT" --raw "$EVIDENCE/gatea-ring.txt" \
    --out-x "$EVIDENCE/x-observations-ring.jsonl" \
    --out-r "$EVIDENCE/renderer-observations-ring.jsonl" \
    --completeness "$EVIDENCE/completeness-ring.json" || true
  cat "$EVIDENCE/x-observations-ring.jsonl" >> "$EVIDENCE/x-observations.jsonl" 2>/dev/null || true
  cat "$EVIDENCE/renderer-observations-ring.jsonl" >> "$EVIDENCE/renderer-observations.jsonl" 2>/dev/null || true
fi

if live=$(x3pid 2>/dev/null); then
  cmd=$(tr '\0' ' ' < "/proc/$live/cmdline" || true)
  case "$cmd" in
    "termux-x11gpu com.waydefu.x11gpu :3"*) kill -TERM "$live" || true; sleep 1;;
  esac
fi
ADB shell am force-stop com.waydefu.x11gpu >/dev/null 2>&1 || true
sleep 1
if x3pid >/dev/null; then echo RESIDUE | tee "$EVIDENCE/x3-residue.txt"; else echo NO_X3_RESIDUE | tee "$EVIDENCE/x3-residue.txt"; fi

stable_json "$EVIDENCE/stable-after.json"
python3 "$JUDGE" --manifest "$EVIDENCE/manifest.json" --spec "$SPEC" \
  --evidence "$EVIDENCE" --cell "$CELL_ID" --output "$EVIDENCE/judge.json" \
  | tee "$EVIDENCE/judge.stdout"
echo $? > "$EVIDENCE/judge.rc"
exit "$(cat "$EVIDENCE/judge.rc")"
