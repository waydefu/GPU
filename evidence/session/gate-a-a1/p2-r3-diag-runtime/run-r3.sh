#!/usr/bin/env bash
# R3 single-direct on 6c7ee6f bound-tuple repair. Experimental :3 only.
set -euo pipefail
TADB=/data/data/com.termux/files/usr/bin/adb
S=10.193.235.219:35301
EVID=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-diag-runtime
CELL=$EVID/r3-single-direct
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
mkdir -p "$CELL"
ADB() {
  env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
    HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
    "$TADB" -H 127.0.0.1 -P 5038 -s "$S" "$@"
}
x3pid() {
  for p in /proc/[0-9]*; do
    x=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$x" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) echo "${p##*/}"; return 0;;
    esac
  done
  return 1
}
stabpid() {
  for p in /proc/[0-9]*; do
    x=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$x" in
      "termux-x11 com.termux.x11 :1"*) echo "${p##*/}"; return 0;;
    esac
  done
  return 1
}

{
  echo "serial=$S artifact=6c7ee6f"
  ADB shell dumpsys power | grep mWakefulness= | head -1
  ADB shell dumpsys window | grep isKeyguardShowing | head -1
  echo "stable_pre=$(stabpid || echo MISSING)"
} | tee "$CELL/preflight.txt"
grep -q 'mWakefulness=Awake' "$CELL/preflight.txt"
grep -q 'isKeyguardShowing=false' "$CELL/preflight.txt"
test "$(stabpid)" = 16085

ADB shell am force-stop com.waydefu.x11gpu
for i in $(seq 1 20); do
  if ! ADB shell 'ps -A' | grep -q 'com.waydefu.x11gpu'; then
    echo "waydefu_gone i=$i"
    break
  fi
  sleep 0.3
done
if ADB shell 'ps -A' | grep -q 'com.waydefu.x11gpu'; then
  echo 'STOP waydefu still alive after force-stop' | tee "$CELL/STOP.txt"
  ADB shell 'ps -A' | grep waydefu | tee -a "$CELL/STOP.txt" || true
  exit 2
fi
sleep 1
rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
  /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock

ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' | tee "$CELL/am-start.out"
ADB shell dumpsys activity activities | grep -E 'waydefu|displayId|mResumed' | head -40 > "$CELL/dumpsys-activity.txt" || true

SINCE=$(ADB shell "date '+%m-%d %H:%M:%S.000'" | tr -d '\r')
echo "logcat_since=$SINCE" | tee "$CELL/logcat-since.txt"
# Include gatea-a1 FATAL. Never *:S without that tag.
ADB logcat -v threadtime -T "$SINCE" \
  gatea-telemetry:V gatea-a1:V LorieNative:I DEBUG:I libc:F Xlorie:I gles-renderer:I \
  > "$CELL/logcat-follow.txt" 2>&1 &
echo $! > "$CELL/logcat.pid"
sleep 1

export GATEA_X3_LAUNCHER_LOG="$CELL/x3-launcher.raw.log"
: > "$GATEA_X3_LAUNCHER_LOG"
export TERMUX_X11_GATEA_PROTO=1
export TERMUX_X11_GATEA_TELEMETRY=1
unset TERMUX_X11_DEBUG || true
python3 "$RUN" | tee "$CELL/start-x3.out"

X3=""
for i in $(seq 1 20); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
echo "x3_pid=$X3 proto=1 telemetry=1" | tee "$CELL/x3-pid.txt"
sleep 8
if ! kill -0 "$X3" 2>/dev/null; then
  echo "STOP x3 died during 8s" | tee "$CELL/STOP.txt"
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
  exit 2
fi
echo "ALIVE_8S pid=$X3" | tee "$CELL/alive.txt"

export DISPLAY=:3
export TMPDIR=/data/data/com.termux/files/usr/tmp
"$FIX/p_b3a_hold" > "$CELL/holder.out" 2>&1 &
echo $! > "$CELL/holder.pid"
for i in $(seq 1 20); do
  grep -q 'HOLD READY' "$CELL/holder.out" 2>/dev/null && break
  sleep 0.2
done
cat "$CELL/holder.out" | tee "$CELL/holder-ready.txt"
grep -q 'HOLD READY' "$CELL/holder.out"
kill -0 "$X3"

set +e
"$FIX/p_r3_single_direct" | tee "$CELL/r3-fixture.out"
FIX_RC=${PIPESTATUS[0]}
set -e
echo "FIXTURE_EXIT=$FIX_RC" | tee "$CELL/fixture-exit.txt"
sleep 2
if ! kill -0 "$X3" 2>/dev/null; then
  echo "X3_DIED_AFTER_FIXTURE" | tee -a "$CELL/alive.txt"
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
else
  echo "X3_STILL_ALIVE pid=$X3" | tee -a "$CELL/alive.txt"
fi
if [ "$FIX_RC" -ne 0 ]; then
  ADB logcat -v threadtime -T "$SINCE" -d > "$CELL/logcat-dump-unfiltered.txt" || true
fi

{
  echo '===GATEA_EVENT==='
  grep -a GATEA_EVENT "$CELL/logcat-follow.txt" || echo NONE
  echo -n 'count='
  grep -ac GATEA_EVENT "$CELL/logcat-follow.txt" || echo 0
  echo '===fatal==='
  grep -aE 'GATEA_FATAL_HALT|Fatal signal|SIGSEGV|SIGILL' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===BIND_PEEK_HANDLE==='
  grep -aE 'GATEA_BIND|GATEA_PEEK|GATEA_HANDLE|r-unbound-frame' "$CELL/logcat-follow.txt" || echo NONE
} | tee "$CELL/telemetry-fatal-pre-teardown.txt"

kill "$(cat "$CELL/logcat.pid")" 2>/dev/null || true
HPID=$(cat "$CELL/holder.pid")
kill "$HPID" 2>/dev/null || true
wait "$HPID" 2>/dev/null || true
if [ -d "/proc/$X3" ]; then
  cmd=$(tr '\0' ' ' < /proc/$X3/cmdline || true)
  case "$cmd" in
    "termux-x11gpu com.waydefu.x11gpu :3"*) kill "$X3"; echo "killed $X3";;
    *) echo "REFUSE_KILL $X3 cmd=$cmd";;
  esac
fi
sleep 1
ADB shell am force-stop com.waydefu.x11gpu >/dev/null
sleep 1
rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
  /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock || true
{
  echo "===residue==="
  found=0
  for p in /proc/[0-9]*; do
    x=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null) || continue
    case "$x" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) echo "RESIDUE ${p##*/}"; found=1;;
      "termux-x11 com.termux.x11 :1"*) echo "STABLE ${p##*/}";;
    esac
  done
  [ "$found" = 0 ] && echo NO_X3_RESIDUE
} | tee "$CELL/teardown.txt"
grep -q NO_X3_RESIDUE "$CELL/teardown.txt"
grep -q 'STABLE 16085' "$CELL/teardown.txt"

python3 - "$CELL" "$FIX_RC" <<'PY'
import sys, re
from pathlib import Path
cell=Path(sys.argv[1])
fix_rc=int(sys.argv[2])
out=(cell/'r3-fixture.out').read_text(errors='replace')
tele=(cell/'telemetry-fatal-pre-teardown.txt').read_text(errors='replace')
alive=(cell/'alive.txt').read_text(errors='replace')
dump=cell/'logcat-dump-unfiltered.txt'
# also search dump if follow missed
blob=tele
if dump.exists():
    blob += '\n' + dump.read_text(errors='replace')
follow=(cell/'logcat-follow.txt').read_bytes()
# decode replacing NULs
follow_txt=follow.decode('utf-8', errors='replace')
events=[]
for m in re.finditer(r'GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) serial=(\d+) src=(\d+) dst=(\d+)', follow_txt + '\n' + blob):
    events.append(tuple(int(x) for x in m.groups()))
(cell/'gatea-events.txt').write_text('\n'.join(
    f'seq={s} role={r} event={e} generation={g} serial={n} src={src} dst={dst}'
    for s,r,e,g,n,src,dst in events) + ('\n' if events else 'NONE\n'))
print('event_count', len(events))
print('fixture_rc', fix_rc)
print('fatal_halt', 'GATEA_FATAL_HALT' in follow_txt or 'GATEA_FATAL_HALT' in blob)
print('x3_alive_after', 'X3_STILL_ALIVE' in alive)
if fix_rc != 0 or 'GATEA_FATAL_HALT' in follow_txt or 'X3_STILL_ALIVE' not in alive:
    print('R3_FAIL')
    print(out[-2000:])
    # print last fatal lines
    for line in follow_txt.splitlines():
        if 'GATEA_FATAL' in line or 'GATEA_EVENT' in line:
            print(line)
    raise SystemExit(2)
# required subsequence (enum values)
# REGISTER_READY=1 x2, LEASE_RESERVED=2, UNLOCK_SRC=3, UNLOCK_DST=4,
# GPU_OWNED=5, PUBLISH=6, CONSUME=7, LOOKUP_OK=8, DRAW_SUBMIT=10,
# FENCE_SATISFIED=11, SEMANTIC_SUCCESS=17, RELOCK_SRC=18, RELOCK_DST=19,
# REPAIR=20, ACK=21
need=[1,1,2,3,4,5,6,7,8,10,11,17,18,19,20,21]
got=[e for _,_,e,_,_,_,_ in events]
i=0
for n in need:
    while i < len(got) and got[i] != n:
        i += 1
    if i >= len(got):
        print('ORDER_FAIL need', need, 'got', got)
        raise SystemExit(3)
    i += 1
assert 'RESULT p_r3_single_direct PASS' in out
assert 'PASS pixels exact_px=64 maxΔ=0' in out
print('R3_EVENT_ORDER_OK', got)
print('R3_SINGLE_DIRECT_PASS')
PY
echo R3_SINGLE_DIRECT_PASS
