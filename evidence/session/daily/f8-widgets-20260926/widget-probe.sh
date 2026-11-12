#!/data/data/com.termux/files/usr/bin/bash
# read-only probe for the F8 widgets (2026-09-26), adb server on the isolated port 5038
export ANDROID_ADB_SERVER_PORT=5038
P=/data/data/com.termux/files/usr/bin
"$P/adb" disconnect >/dev/null 2>&1
s=$(date +%s%N); PORT=$("$P/f8-adb-port"); rc=$?; echo "f8-adb-port rc=$rc port=$PORT ms=$(( ($(date +%s%N)-s)/1000000 ))"
[ -n "$PORT" ] || exit 0
python3 /data/data/com.termux/files/usr/tmp/f8-shard/adbd-check.py $PORT
fakeroot env ANDROID_NO_USE_FWMARK_CLIENT=1 "$P/adb" connect 127.0.0.1:$PORT
A="$P/adb -s 127.0.0.1:$PORT"
echo "--- displays:"; $A shell dumpsys display | grep 'mBaseDisplayInfo=DisplayInfo' | sed -n 's/.*DisplayInfo{"\([^"]*\)", displayId \([0-9]*\).*type \([A-Z]*\).*real \([0-9]* x [0-9]*\).*/id=\2 type=\3 real=\4 name=\1/p'
echo "--- mice / pointer devices:"; $A shell dumpsys input | grep -E '^  Device [0-9]+: ' | grep -iE 'mouse|logitech|M350|pointer|touchpad' 
echo "--- external viewport:"; $A shell dumpsys input | grep -m2 'Viewport EXTERNAL'
echo "--- top resumed per display:"; $A shell dumpsys activity activities | grep -E '^Display #|topResumedActivity=' | head -8
echo "--- settings:"; for k in force_desktop_mode_on_external_displays enable_freeform_support; do echo "$k=$($A shell settings get global $k)"; done
echo PROBE_DONE
