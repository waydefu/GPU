#!/usr/bin/env bash
# Install PGA-GAP-3 fix APK 83d45a9 (CI 35845935317) onto experimental
# com.waydefu.x11gpu only. DOES NOT RUN unless RUN_INSTALL=YES.
# Never touches com.termux.x11 / :1 / HDMI.
# Usage: RUN_INSTALL=YES SERIAL=HOST:PORT CELL=.../artifact-83d45a9/install bash install-83d45a9.sh
set -euo pipefail

ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
APK=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-pga-artifact/artifact-83d45a9/ci-35845935317/termux-x11-universal-debug.apk
EXPECT_SHA256=f4c98b8a7364cb553532c0caef9aae83745df694c2021a1c1c2b7631c041230f
EXPECT_BUILDID=67e8ad53fb3c03c34cdb4d5e84ccef5571859810
EXPECT_VERSION=1.03.01-83d45a9-23.09.26
EXPECT_SIZE=15381026
EXPECT_SIGNER=b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1
EXPECT_HEAD=83d45a92a98ba092f236c873b8bae419c10060ff
EXPECT_PARENT=bfb576940ded333f49d29a8910a785f8d680261c
EXPECT_CI=35845935317
REMOTE=/data/local/tmp/gate-a-pga-83d45a9-35845935317.apk
APK_FOR_SIGNER=/tmp/pga-83d45a9-termux-x11-universal-debug.apk
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"

if [ "${RUN_INSTALL:-}" != YES ]; then
  echo "REFUSE: set RUN_INSTALL=YES after explicit install authorization"
  exit 9
fi

case "$CELL" in
  */artifact-83d45a9/install) ;;
  *) echo "REFUSE CELL must be .../artifact-83d45a9/install got=$CELL"; exit 9;;
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

cp -a "$APK" "$APK_FOR_SIGNER"
COPY_SHA=$(sha256sum "$APK_FOR_SIGNER" | awk '{print $1}')
test "$COPY_SHA" = "$EXPECT_SHA256"
/usr/bin/aapt dump badging "$APK" | tee "$CELL/aapt-dump.stdout.txt"
grep -q "package: name='com.waydefu.x11gpu'" "$CELL/aapt-dump.stdout.txt"
grep -q "versionCode='15'" "$CELL/aapt-dump.stdout.txt"
grep -q "versionName='$EXPECT_VERSION'" "$CELL/aapt-dump.stdout.txt"
/usr/bin/apksigner verify --verbose --print-certs "$APK_FOR_SIGNER" \
  | tee "$CELL/local-apksigner.txt"
grep -qi "$EXPECT_SIGNER" "$CELL/local-apksigner.txt"
unzip -p "$APK" lib/arm64-v8a/libXlorie.so > "$CELL/local-libXlorie.so"
readelf -n "$CELL/local-libXlorie.so" | tee "$CELL/local-lib-buildid.txt"
grep -q "$EXPECT_BUILDID" "$CELL/local-lib-buildid.txt"
echo PRE_INSTALL_ARTIFACT_BIND=PASS | tee "$CELL/pre-install-artifact-bind.txt"

ADB shell getprop ro.product.device | tr -d '\r' | tee "$CELL/device.txt"
grep -q myron "$CELL/device.txt"
ADB shell dumpsys power | grep mWakefulness= | head -1 | tee "$CELL/screen.txt"
ADB shell dumpsys window | grep isKeyguardShowing= | head -1 >> "$CELL/screen.txt"
grep -q 'mWakefulness=Awake' "$CELL/screen.txt"
grep -q 'isKeyguardShowing=false' "$CELL/screen.txt"

{
  echo "ts=$(date -Is)"
  echo "serial=$SERIAL"
  echo "head=$EXPECT_HEAD"
  echo "ci=$EXPECT_CI"
  echo "parent=$EXPECT_PARENT"
  echo "role=83d45a9-pga-gap3-install"
  ADB shell getprop ro.product.model
  ADB shell getprop ro.product.device
  ADB shell getprop ro.build.version.release
  ADB shell getprop ro.build.version.sdk
  echo '===stable pre==='
  ADB shell dumpsys package com.termux.x11 | grep -E 'versionCode=|versionName=|lastUpdateTime=' | head -6
  echo '===experimental pre==='
  ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'pkg=|codePath=|versionCode=|versionName=|lastUpdateTime=' | head -12
  echo '===hdmi observe==='
  ADB shell dumpsys display | grep -E 'uniqueId=|mType=|Display id=' | head -20 || true
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

cp -a "$CELL/installed-base.apk" /tmp/pga-83d45a9-installed-base.apk
/usr/bin/apksigner verify --verbose --print-certs /tmp/pga-83d45a9-installed-base.apk \
  | tee "$CELL/installed-apksigner.txt"
grep -qi "$EXPECT_SIGNER" "$CELL/installed-apksigner.txt"
echo SIGNER_CONTINUITY=PASS | tee "$CELL/installed-signer.txt"

unzip -p "$CELL/installed-base.apk" lib/arm64-v8a/libXlorie.so > "$CELL/installed-libXlorie.so"
readelf -n "$CELL/installed-libXlorie.so" | tee "$CELL/installed-lib-buildid.txt"
grep -q "$EXPECT_BUILDID" "$CELL/installed-lib-buildid.txt"
strings -a "$CELL/installed-libXlorie.so" > "$CELL/installed-lib-strings.txt"
grep -F 'LORIE-R8-TEST' "$CELL/installed-lib-strings.txt" >/dev/null
grep -F 'R8_OBS' "$CELL/installed-lib-strings.txt" >/dev/null
grep -F 'x-destroy-in-lease' "$CELL/installed-lib-strings.txt" >/dev/null
grep -F 'x-close-in-lease' "$CELL/installed-lib-strings.txt" >/dev/null
grep -F 'P1_DESTRUCTOR_CALL' "$CELL/installed-lib-strings.txt" >/dev/null
grep -F 'GATEA_HUP_PRESERVE' "$CELL/installed-lib-strings.txt" >/dev/null
grep -F 'R8_OBS_POST_END' "$CELL/installed-lib-strings.txt" >/dev/null
grep -F 'TERMUX_X11_P2A_DIAG' "$CELL/installed-lib-strings.txt" >/dev/null   # PGA-GAP-1 gate compiled in
grep -F 'R_SURFACE_QUIESCED' "$CELL/installed-lib-strings.txt" >/dev/null
grep -F '"op":"TERMINATE"' "$CELL/installed-lib-strings.txt" >/dev/null
if grep -F 'STALL_PHASE phase=' "$CELL/installed-lib-strings.txt" >/dev/null; then
  echo "REFUSE installed lib has diagnostic STALL_PHASE (wrong APK family)"
  exit 9
fi
{
  echo R8_TEST_NAME_STRING=PASS
  echo R8_OBS_STRING=PASS
  echo X_DESTROY_IN_LEASE_STRING=PASS
  echo X_CLOSE_IN_LEASE_STRING=PASS
  echo P1_DESTRUCTOR_CALL_STRING=PASS
  echo R8_OBS_POST_END_STRING=PASS
  echo R_SURFACE_QUIESCED_STRING=PASS
  echo R8_TERMINATE_OP_STRING=PASS
  echo DIAGNOSTIC_STALL_PHASE_ABSENT=PASS
  echo PGA_GAP1_FLAG_STRING=PASS
  echo expect_head=$EXPECT_HEAD
  echo expect_ci=$EXPECT_CI
} | tee "$CELL/installed-marker-strings.txt"

ADB shell rm -f "$REMOTE" || true
test "$(stabpid)" = "$STABLE_PRE"
echo INSTALL_83D45A9_BIND_PASS | tee "$CELL/install-bind-pass.txt"
