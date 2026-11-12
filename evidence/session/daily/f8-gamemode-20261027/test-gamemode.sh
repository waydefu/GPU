#!/bin/bash
# Fake-adb test of f8-gamemode. Usage: test-gamemode.sh <script under test>
# Every external tool is a stub that appends to $CALLS; each case asserts on that trace.
set -u
SUT=$1
FIX=/root/projects/GPU加速/evidence/session/daily/f8-gamemode-20261003
W=$(mktemp -d); B=$W/bin; mkdir -p $B
export CALLS=$W/calls
stub() { printf '#!/bin/sh\n%s\n' "$2" > "$B/$1"; chmod +x "$B/$1"; }
stub termux-toast 'echo "TOAST $*" >> $CALLS'
stub f8stop       'echo "F8STOP" >> $CALLS'
stub f8-adb-port  '[ -n "$FAKE_PORT" ] && echo "$FAKE_PORT"'
stub fakeroot     'exec "$@"'
stub am           'echo "AM $*" >> $CALLS'
# FAKE_DIALOG: one char per sheet in order, y = first item chosen, n = cancelled
stub termux-dialog 'n=$(cat $CALLS.dlg 2>/dev/null || echo 0); echo $((n+1)) > $CALLS.dlg
c=$(printf %s "$FAKE_DIALOG" | cut -c$((n+1))); echo "DIALOG" >> $CALLS
[ "$c" = y ] && echo "{\"code\":0,\"index\":0}" || echo "{\"code\":-2}"'
stub adb '[ "$1" = -s ] && shift 2
case "$1" in
  connect) echo "ADB connect" >> $CALLS ;;
  kill-server) echo "ADB kill-server" >> $CALLS ;;
  get-state) echo "ADB get-state" >> $CALLS; [ "$FAKE_STATE" = device ] && echo device || { echo "error: device unauthorized" >&2; exit 1; } ;;
  shell) shift; echo "ADB shell $*" | head -c 60 >> $CALLS; echo >> $CALLS
    case "$*" in
      "dumpsys input") cat "$FAKE_DUMP" ;;
      *"settings put global adb_wifi_enabled 1"*) [ "$FAKE_WRITE" = ok ] || { echo "SecurityException" >&2; exit 255; } ;;
      setsid*) echo HANDOFF >> $CALLS ;;
    esac ;;
esac'
ln -s /usr/bin/jq $B/jq

FAIL=0
run() {  # run <name> <port> <state> <write> <dump> <dialog>
    : > $CALLS; rm -f $CALLS.dlg
    F8_BIN=$B F8_GAMEMODE_LOG=$W/log PATH=$B:$PATH FAKE_PORT=$2 FAKE_STATE=$3 FAKE_WRITE=$4 \
        FAKE_DUMP=$FIX/fixture-dump-$5.txt FAKE_DIALOG=$6 bash "$SUT" >/dev/null 2>&1
    CUR=$1
}
has()  { grep -qF -- "$1" $CALLS || { echo "FAIL [$CUR] missing: $1"; FAIL=1; }; }
hasnt(){ ! grep -qF -- "$1" $CALLS || { echo "FAIL [$CUR] unexpected: $1"; FAIL=1; }; }

run no-port "" device ok clean y
has "無線偵錯沒開"; has "拔掉外接滑鼠"; has "AM start"; has "ADB kill-server"; hasnt HANDOFF; hasnt "ADB shell"

run unauthorized 46691 unauthorized ok clean y
has "ADB get-state"; has "配對可能過期"; has "拔掉外接滑鼠"; hasnt "dumpsys"; hasnt HANDOFF; has "AM start"

run write-denied 46691 device deny clean y
has "dumpsys input"; has "安全設定"; hasnt "拔掉外接滑鼠"; hasnt HANDOFF; has "AM start"; has "ADB kill-server"

run all-ok 46691 device ok clean y
has HANDOFF; has "2 秒後關閉"; hasnt "AM start"; hasnt "ADB kill-server"

run mouse-cancel 46691 device ok mouse yn
has "dumpsys input"; hasnt HANDOFF; hasnt "AM start"; hasnt "settings put"; hasnt TOAST

run first-cancel 46691 device ok clean n
hasnt "ADB"; hasnt HANDOFF; hasnt TOAST

rm -rf $W
[ $FAIL = 0 ] && echo "ALL PASS: $SUT" || { echo "SOME FAIL: $SUT"; exit 1; }
