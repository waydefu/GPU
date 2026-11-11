#!/usr/bin/env bash
# Install qualified 95e6f96 APK onto experimental com.waydefu.x11gpu only.
# DOES NOT RUN unless RUN_INSTALL=YES. Never touches com.termux.x11 / :1 / HDMI.
# Usage: RUN_INSTALL=YES SERIAL=HOST:PORT CELL=.../runtime-95e6f96/r0 bash install-95e6f96.sh
set -euo pipefail

ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
APK=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r6-ci-34944171114/apk/termux-x11-universal-debug.apk
EXPECT_SHA256=60c36b4f59c38d13db6fe6c366e6f115a720ec1d6946d057b3ec41551b12f628
EXPECT_BUILDID=1188e1cabf3b78285e7e5fbedcf64f0b5e7d44f9
EXPECT_VERSION=1.03.01-95e6f96-15.09.26
EXPECT_SIZE=15238882
REMOTE=/data/local/tmp/gate-a-p2-95e6f96-34944171114.apk
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"

if [ "${RUN_INSTALL:-}" != YES ]; then
  echo "REFUSE: set RUN_INSTALL=YES after explicit install authorization"
  exit 9
fi

case "$CELL" in
  */runtime-95e6f96/r0) ;;
  *) echo "REFUSE CELL must be .../runtime-95e6f96/r0 got=$CELL"; exit 9;;
esac
mkdir -p "$CELL"
if [ -f "$CELL/pm-install-commit.raw.txt" ]; then
  echo "REFUSE CELL already has pm-install-commit.raw.txt"
  exit 9
fi

test -f "$APK"
SIZE=$(stat -c%s "$APK")
test "$SIZE" = "$EXPECT_SIZE"
LOCAL_SHA=$(sha256sum "$APK" | awk '{print $1}')
test "$LOCAL_SHA" = "$EXPECT_SHA256"
echo "local_apk_sha256=$LOCAL_SHA size=$SIZE" | tee "$CELL/local-apk.sha256.txt"

ADB shell getprop ro.product.device | tr -d '\r' | tee "$CELL/device.txt"
grep -q myron "$CELL/device.txt"
ADB shell dumpsys power | grep mWakefulness= | head -1 | tee "$CELL/screen.txt"
ADB shell dumpsys window | grep isKeyguardShowing= | head -1 >> "$CELL/screen.txt"
grep -q 'mWakefulness=Awake' "$CELL/screen.txt"
grep -q 'isKeyguardShowing=false' "$CELL/screen.txt"

{
  echo "ts=$(date -Is)"
  echo "serial=$SERIAL"
  echo "head=95e6f9602b0146ee190870f84a34aad822ef666f"
  echo "ci=34944171114"
  ADB shell getprop ro.product.model
  ADB shell getprop ro.product.device
  ADB shell getprop ro.build.version.release
  ADB shell getprop ro.build.version.sdk
  echo '===stable pre==='
  ADB shell dumpsys package com.termux.x11 | grep -E 'versionCode=|versionName=|lastUpdateTime=' | head -6
  echo '===experimental pre==='
  ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'pkg=|codePath=|versionCode=|versionName=|lastUpdateTime=' | head -12
  echo '===hdmi observe==='
  ADB shell dumpsys display | grep -E 'Display id=|mType=|mDisplayId=' | head -20 || true
} | tee "$CELL/pre-install-identity.txt"
grep -q 'versionName=1.03.01-11b82d9-06.09.26' "$CELL/pre-install-identity.txt"

STABLE_PRE=$(stabpid)
test -n "$STABLE_PRE"
echo "stable_pre_pid=$STABLE_PRE" | tee "$CELL/stable-pre.txt"
echo "stable_pre_cmd=$(stab_cmd)" | tee -a "$CELL/stable-pre.txt"
echo "$(stab_cmd)" | grep -q '^termux-x11 com.termux.x11 :1'

if X3=$(x3pid); then
  cmd=$(tr '\0' ' ' < "/proc/$X3/cmdline" || true)
  case "$cmd" in
    "termux-x11gpu com.waydefu.x11gpu :3"*) kill "$X3"; echo "killed_pre_install $X3" | tee "$CELL/killed-x3-pre.txt";;
    *) echo "REFUSE_KILL $X3 cmd=$cmd"; exit 3;;
  esac
  sleep 1
fi

ADB shell am force-stop com.waydefu.x11gpu
for i in $(seq 1 20); do
  if ! ADB shell 'ps -A' | grep -q 'com.waydefu.x11gpu'; then
    echo "waydefu_gone i=$i"
    break
  fi
  sleep 0.3
done
sleep 1

ADB push "$APK" "$REMOTE" | tee "$CELL/adb-push.txt"
ADB shell sha256sum "$REMOTE" | tee "$CELL/remote-apk.sha256.txt"
GOT=$(awk '{print $1}' "$CELL/remote-apk.sha256.txt" | tr -d '\r')
test "$GOT" = "$EXPECT_SHA256"
echo STAGED_SHA256=PASS | tee -a "$CELL/remote-apk.sha256.txt"

ADB shell pm install-create -r -t --user 0 -S "$EXPECT_SIZE" | tee "$CELL/pm-install-create.raw.txt"
SESSION=$(sed -n 's/.*\[\([0-9]*\)\].*/\1/p' "$CELL/pm-install-create.raw.txt" | head -1)
test -n "$SESSION"
echo "session=$SESSION" | tee "$CELL/pm-session.txt"
ADB shell pm install-write -S "$EXPECT_SIZE" "$SESSION" 0 "$REMOTE" | tee "$CELL/pm-install-write.raw.txt"
grep -q Success "$CELL/pm-install-write.raw.txt"
ADB shell pm install-commit "$SESSION" | tee "$CELL/pm-install-commit.raw.txt"
grep -q Success "$CELL/pm-install-commit.raw.txt"

{
  echo '===installed experimental==='
  ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'pkg=|codePath=|versionCode=|versionName=|lastUpdateTime=' | head -12
  echo '===pm path==='
  ADB shell pm path com.waydefu.x11gpu
  echo '===stable==='
  ADB shell dumpsys package com.termux.x11 | grep -E 'versionCode=|versionName=|lastUpdateTime=' | head -6
} | tee "$CELL/installed-package.txt"
grep -q "versionName=$EXPECT_VERSION" "$CELL/installed-package.txt"
grep -q 'pkg=Package{.* com.waydefu.x11gpu}' "$CELL/installed-package.txt"
grep -q 'versionName=1.03.01-11b82d9-06.09.26' "$CELL/installed-package.txt"
test "$(stabpid)" = "$STABLE_PRE"

PATH_APK=$(ADB shell pm path com.waydefu.x11gpu | tr -d '\r' | sed -n 's/^package://p')
test -n "$PATH_APK"
echo "path_apk=$PATH_APK" | tee "$CELL/pm-path.txt"
ADB pull "$PATH_APK" "$CELL/installed-base.apk" | tee "$CELL/adb-pull-base.txt"
INST_SHA=$(sha256sum "$CELL/installed-base.apk" | awk '{print $1}')
echo "installed_base_sha256=$INST_SHA" | tee "$CELL/installed-base.sha256.txt"
test "$INST_SHA" = "$EXPECT_SHA256"

unzip -p "$CELL/installed-base.apk" lib/arm64-v8a/libXlorie.so > "$CELL/installed-libXlorie.so"
readelf -n "$CELL/installed-libXlorie.so" | tee "$CELL/installed-lib-buildid.txt"
grep -q "$EXPECT_BUILDID" "$CELL/installed-lib-buildid.txt"

ADB shell rm -f "$REMOTE" || true
test "$(stabpid)" = "$STABLE_PRE"
echo INSTALL_95e6f96_BIND_PASS
