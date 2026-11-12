#!/usr/bin/env bash
# FIRST B-2 requalification on installed 7549e36. Experimental :3 only.
# NOT a retry of runtime-0d72332. NOT a retry of repair-validation-01.
# NOT R7. Stop after first failed mandatory stage (cleanup still runs).
# Usage: SERIAL=HOST:PORT CELL=.../runtime-7549e36/b2-requalification-01 bash run-b2-requal-7549e36.sh
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
EXPECT_STRESS_SHA256=3e79b5cf875f5d7d05a25634983a44d9acfe67dfb885bf11f19b2cdb70e43c56
EXPECT_ORACLE_SHA256=19154bf222b3c1e8c033bad2101bcd7e2f56fb23e486c4d8b6be651ca7eec726
EXPECT_VERSION=1.03.01-7549e36-16.09.26
EXPECT_APK_SHA256=45500894023208963b3b1cd51fb7f3aa61807a25e1d70b322f7a7fdad7e14bc3
EXPECT_BUILDID=4c5b7b86c18ec4e9bb14720c4615a25c1d6a8f81
EXPECT_SIGNER=b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1
# shellcheck source=harness-lib.sh
source "$ROOT/harness-lib.sh"

start_logcat() {
  local out=$1 since=$2
  (
    exec env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
      HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
      "$TADB" -H 127.0.0.1 -P 5038 -s "$SERIAL" logcat -v threadtime -T "$since" \
      gatea-telemetry:V gatea-a1:V LorieNative:I DEBUG:I libc:F Xlorie:I gles-renderer:V \
      SurfaceFlinger:V BufferQueueProducer:V BufferQueue:V libEGL:V \
      > "$out" 2>&1
  ) &
  echo $!
}

mkdir -p "$CELL"
case "$CELL" in
  */runtime-7549e36/b2-requalification-01) ;;
  *) echo "REFUSE CELL must be .../runtime-7549e36/b2-requalification-01 got=$CELL"; exit 9;;
esac
if [ -f "$CELL/oracle.out" ] || [ -f "$CELL/x1000.out" ]; then
  echo "REFUSE CELL already has oracle/x1000 evidence (no overwrite, no rerun1)"
  echo B2_REQUALIFICATION_INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
fi

test -x "$FIX/p_b2_stress"
test -x "$FIX/p-b2-oracle"
STRESS_SHA=$(sha256sum "$FIX/p_b2_stress" | awk '{print $1}')
ORACLE_SHA=$(sha256sum "$FIX/p-b2-oracle" | awk '{print $1}')
test "$STRESS_SHA" = "$EXPECT_STRESS_SHA256"
test "$ORACLE_SHA" = "$EXPECT_ORACLE_SHA256"
{
  echo "role=b2-requalification-01-not-r7-not-repair-validation"
  echo "p_b2_stress_sha256=$STRESS_SHA"
  echo "p_b2_oracle_sha256=$ORACLE_SHA"
  echo "expect_version=$EXPECT_VERSION"
} | tee "$CELL/preflight.txt"
strings -a "$FIX/p_b2_stress" | grep -q 'B2_DIAG_FAIL iteration='

ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'pkg=|codePath=|versionCode=|versionName=|lastUpdateTime=' | head -12 | tee "$CELL/installed-package-pre.txt"
grep -q "versionName=$EXPECT_VERSION" "$CELL/installed-package-pre.txt"
grep -q 'versionCode=15' "$CELL/installed-package-pre.txt"
ADB shell dumpsys package com.termux.x11 | grep -E 'versionCode=|versionName=|lastUpdateTime=' | head -6 | tee "$CELL/stable-package-pre.txt"
grep -q 'versionName=1.03.01-11b82d9-06.09.26' "$CELL/stable-package-pre.txt"

PATH_APK=$(ADB shell pm path com.waydefu.x11gpu | tr -d '\r' | sed -n 's/^package://p')
test -n "$PATH_APK"
echo "path_apk=$PATH_APK" | tee "$CELL/pm-path.txt"
ADB pull "$PATH_APK" "$CELL/installed-base.apk" | tee "$CELL/adb-pull-base.txt"
INST_SHA=$(sha256sum "$CELL/installed-base.apk" | awk '{print $1}')
echo "installed_base_sha256=$INST_SHA" | tee "$CELL/installed-base.sha256.txt"
test "$INST_SHA" = "$EXPECT_APK_SHA256"
cp -a "$CELL/installed-base.apk" /tmp/b2-7549e36-installed-base.apk
/usr/bin/apksigner verify --verbose --print-certs /tmp/b2-7549e36-installed-base.apk | tee "$CELL/installed-apksigner.txt"
grep -qi "$EXPECT_SIGNER" "$CELL/installed-apksigner.txt"
echo SIGNER_CONTINUITY=PASS | tee "$CELL/installed-signer.txt"
unzip -p "$CELL/installed-base.apk" lib/arm64-v8a/libXlorie.so > "$CELL/installed-libXlorie.so"
readelf -n "$CELL/installed-libXlorie.so" | tee "$CELL/installed-lib-buildid.txt"
grep -q "$EXPECT_BUILDID" "$CELL/installed-lib-buildid.txt"
echo PROVENANCE_BIND=PASS | tee "$CELL/provenance-bind.txt"

ADB shell dumpsys power | grep mWakefulness= | head -1 | tee "$CELL/screen.txt"
ADB shell dumpsys window | grep isKeyguardShowing= | head -1 >> "$CELL/screen.txt"
grep -q 'mWakefulness=Awake' "$CELL/screen.txt"
grep -q 'isKeyguardShowing=false' "$CELL/screen.txt"
ADB shell dumpsys display | grep -E 'Display id=|mType=|mDisplayId=' | head -20 | tee "$CELL/hdmi-observe.txt" || true

STABLE_PRE=$(stabpid)
STABLE_CMD_PRE=$(stab_cmd)
echo "stable_pre_pid=$STABLE_PRE" | tee "$CELL/stable-pre.txt"
echo "stable_pre_cmd=$STABLE_CMD_PRE" | tee -a "$CELL/stable-pre.txt"
test -n "$STABLE_PRE"
echo "$STABLE_CMD_PRE" | grep -q '^termux-x11 com.termux.x11 :1'

if X3=$(x3pid); then
  echo "REFUSE preexisting X3 pid=$X3"
  echo B2_REQUALIFICATION_INVALID | tee "$CELL/primary-verdict.txt"
  exit 9
fi

rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
  /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock /tmp/x11gpu-p2a3.snap || true
rm -f "$SUMMARY" || true

ADB shell am force-stop com.waydefu.x11gpu
sleep 1
ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' | tee "$CELL/am-start.out"
ADB shell dumpsys activity activities > "$CELL/dumpsys-activity.txt"
assert_display0 "$CELL/dumpsys-activity.txt"

SINCE=$(ADB shell "date '+%m-%d %H:%M:%S.000'" | tr -d '\r')
echo "logcat_since=$SINCE" | tee "$CELL/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$CELL/logcat-follow.txt" "$SINCE")
echo "$LOGCAT_PID" > "$CELL/logcat.pid"
for i in $(seq 1 20); do
  exe=$(readlink "/proc/$LOGCAT_PID/exe" 2>/dev/null || true)
  [ "$exe" = "$TADB" ] && break
  sleep 0.1
done
verify_logcat_pid "$LOGCAT_PID"
sleep 1

export GATEA_X3_LAUNCHER_LOG="$CELL/x3-launcher.raw.log"
: > "$GATEA_X3_LAUNCHER_LOG"
unset TERMUX_X11_GATEA_PROTO || true
unset TERMUX_X11_GATEA_TELEMETRY || true
unset TERMUX_X11_DEBUG || true
unset TERMUX_X11_GATEA_TEST_FAULT || true
unset TERMUX_X11_GATEA_TEST_ARM || true
unset TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL || true
unset TERMUX_X11_GATEA_A1 || true
python3 "$RUN" | tee "$CELL/start-x3.out"
X3=""
for i in $(seq 1 40); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
echo "x3_pid=$X3 mode=unset role=b2-requalification" | tee "$CELL/x3-pid.txt"
save_x_identity "$X3" "$CELL"
tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11' | tee "$CELL/x-environ-all-termux-x11.txt" || true
if tr '\0' '\n' < "/proc/$X3/environ" | grep '^TERMUX_X11_GATEA' > "$CELL/x-environ-gatea.txt"; then
  :
else
  echo NO_GATEA_ENV > "$CELL/x-environ-gatea.txt"
fi
python3 - "$CELL/x-environ-gatea.txt" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
forbidden = (
    'TERMUX_X11_GATEA_TEST_FAULT',
    'TERMUX_X11_GATEA_TEST_ARM',
    'TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL',
    'TERMUX_X11_GATEA_PROTO',
    'TERMUX_X11_GATEA_TELEMETRY',
    'TERMUX_X11_GATEA_A1',
)
for name in forbidden:
    assert name not in text, name
print('ENV_UNSET_OK')
PY
for i in $(seq 1 40); do
  if [ -S /data/data/com.termux/files/usr/tmp/.X11-unix/X3 ] || [ -S /tmp/.X11-unix/X3 ]; then
    echo "socket_ready i=$i"
    break
  fi
  sleep 0.25
done
sleep 2
if [ ! -d "/proc/$X3" ]; then
  echo "DIED_BEFORE_HOLDER pid=$X3" | tee "$CELL/alive.txt"
  ADB logcat -d -v threadtime -T "$SINCE" > "$CELL/logcat-dump-unfiltered.txt" || true
  echo B2_REQUALIFICATION_INVALID | tee "$CELL/primary-verdict.txt"
  exit 2
fi
echo "ALIVE_BEFORE_ORACLE pid=$X3" | tee "$CELL/alive.txt"

export DISPLAY=:3
export TMPDIR=/data/data/com.termux/files/usr/tmp
"$FIX/p_b3a_hold" > "$CELL/holder.out" 2>&1 &
HOLDER_PID=$!
echo "$HOLDER_PID" > "$CELL/holder.pid"
for i in $(seq 1 20); do
  grep -q 'HOLD READY' "$CELL/holder.out" 2>/dev/null && break
  sleep 0.2
done
grep -q 'HOLD READY' "$CELL/holder.out"

ORACLE_RC=""
X100_RC=""
MIXED_RC=""
X1000_RC=""
STOPPED_AFTER=""

x_alive() {
  [ -d "/proc/$X3" ]
}

record_stage() {
  local name=$1
  if x_alive; then echo "${name}_X_ALIVE=yes pid=$X3" | tee -a "$CELL/alive.txt"
  else echo "${name}_X_ALIVE=no pid=$X3" | tee -a "$CELL/alive.txt"; fi
}

run_cleanup_and_judge() {
  {
    echo '===GATEA_EVENT==='
    grep -c GATEA_EVENT "$CELL/logcat-follow.txt" || echo 0
    grep GATEA_EVENT "$CELL/logcat-follow.txt" || echo NONE
    echo '===event35==='
    grep -c 'event=35' "$CELL/logcat-follow.txt" || echo 0
    echo '===timeout==='
    grep -c 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo 0
    grep 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo NONE
    echo '===fatal==='
    grep -E 'GATEA_FATAL_HALT|x-exa-composite-wait|Fatal signal|SIGSEGV|SIGILL' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
    echo '===gcomp==='
    grep -c 'Gcomp Prepare TRUE' "$CELL/logcat-follow.txt" || echo 0
    grep -c 'Gcomp RECT' "$CELL/logcat-follow.txt" || echo 0
    grep -c 'Gcomp Done' "$CELL/logcat-follow.txt" || echo 0
    echo '===apply==='
    grep -c 'rendererApplyPendingGpuCopies' "$CELL/logcat-follow.txt" || echo 0
  } | tee "$CELL/telemetry-fatal-pre-teardown.txt"

  echo "ORACLE_RC=${ORACLE_RC:-NA} X100_RC=${X100_RC:-NA} MIXED_RC=${MIXED_RC:-NA} X1000_RC=${X1000_RC:-NA} STOPPED_AFTER=${STOPPED_AFTER:-none}" | tee "$CELL/fixture-exit.txt"

  test "$(stabpid)" = "$STABLE_PRE"
  test "$(stab_cmd)" = "$STABLE_CMD_PRE"

  stop_logcat "$LOGCAT_PID" || true
  LOGCAT_PID=""
  kill -TERM "$HOLDER_PID" 2>/dev/null || true
  wait "$HOLDER_PID" 2>/dev/null || true
  HOLDER_PID=""
  if [ -d "/proc/$X3" ]; then
    cmd=$(tr '\0' ' ' < /proc/$X3/cmdline || true)
    case "$cmd" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) kill "$X3"; echo "killed $X3";;
      *) echo "REFUSE_KILL $X3 cmd=$cmd"; exit 3;;
    esac
  fi
  sleep 1
  ADB shell am force-stop com.waydefu.x11gpu >/dev/null
  sleep 1
  rm -f /tmp/.X11-unix/X3 /data/data/com.termux/files/usr/tmp/.X11-unix/X3 \
    /tmp/.X3-lock /data/data/com.termux/files/usr/tmp/.X3-lock || true
  if [ -f "$SUMMARY" ]; then
    cp -a "$SUMMARY" "$CELL/gatea-summary.txt"
  else
    echo 'SUMMARY_ABSENT' | tee "$CELL/gatea-summary.txt"
  fi
  {
    echo "===process residue only==="
    echo "STABLE $(stabpid)"
    if x3pid >/dev/null; then echo RESIDUE; else echo NO_X3_RESIDUE; fi
  } | tee "$CELL/teardown.txt"
  ADB shell dumpsys package com.termux.x11 | grep -E 'versionCode=|versionName=|lastUpdateTime=' | head -6 | tee "$CELL/stable-package-after.txt"
  echo "stable_after_pid=$(stabpid)" | tee "$CELL/stable-after.txt"
  echo "stable_after_cmd=$(stab_cmd)" | tee -a "$CELL/stable-after.txt"
  grep -q NO_X3_RESIDUE "$CELL/teardown.txt"
  grep -q "STABLE $STABLE_PRE" "$CELL/teardown.txt"
  test "$(stabpid)" = "$STABLE_PRE"
  grep -q 'versionName=1.03.01-11b82d9-06.09.26' "$CELL/stable-package-after.txt"

  ADB logcat -d -v threadtime -T "$SINCE" > "$CELL/logcat-dump-unfiltered.txt" || true

  python3 - "$CELL" <<'PY'
import re, sys
from pathlib import Path
cell = Path(sys.argv[1])
log = (cell / 'logcat-follow.txt').read_text(errors='replace') if (cell / 'logcat-follow.txt').is_file() else ''
unf = (cell / 'logcat-dump-unfiltered.txt').read_text(errors='replace') if (cell / 'logcat-dump-unfiltered.txt').is_file() else ''
both = log + '\n' + unf
fx = (cell / 'fixture-exit.txt').read_text(errors='replace') if (cell / 'fixture-exit.txt').is_file() else ''
alive = (cell / 'alive.txt').read_text(errors='replace') if (cell / 'alive.txt').is_file() else ''
env = (cell / 'x-environ-gatea.txt').read_text(errors='replace') if (cell / 'x-environ-gatea.txt').is_file() else ''
teardown = (cell / 'teardown.txt').read_text(errors='replace') if (cell / 'teardown.txt').is_file() else ''
oracle = (cell / 'oracle.out').read_text(errors='replace') if (cell / 'oracle.out').is_file() else ''
x100 = (cell / 'x100.out').read_text(errors='replace') if (cell / 'x100.out').is_file() else ''
mixed = (cell / 'mixed100.out').read_text(errors='replace') if (cell / 'mixed100.out').is_file() else ''
x1000 = (cell / 'x1000.out').read_text(errors='replace') if (cell / 'x1000.out').is_file() else ''
prov = (cell / 'provenance-bind.txt').read_text(errors='replace') if (cell / 'provenance-bind.txt').is_file() else ''

def wall_s(ln):
    parts = ln.split()
    if len(parts) < 2 or ':' not in parts[1]:
        return None
    h, m, rest = parts[1].split(':')
    s, ms = rest.split('.')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms[:3]) / 1000.0

def lines_with(hay, needle):
    return [ln for ln in hay.splitlines() if needle in ln]

def stress_tuple(text):
    m = re.search(r'STRESS mixed=(\d+) ok=(\d+) fail=(\d+) n=(\d+) alive=(\d+)', text)
    if not m:
        return None
    return tuple(int(m.group(i)) for i in range(1, 6))

def rc_of(name):
    m = re.search(rf'{name}=(\d+|NA)', fx)
    return m.group(1) if m else 'NA'

timeouts = lines_with(log, 'EXA GPU composite wait timeout') or lines_with(unf, 'EXA GPU composite wait timeout')
fatals = [ln for ln in both.splitlines() if 'GATEA_FATAL_HALT' in ln]
exa_wait = [ln for ln in both.splitlines() if 'x-exa-composite-wait' in ln]
gprep = lines_with(log, 'Gcomp Prepare TRUE') or lines_with(unf, 'Gcomp Prepare TRUE')
grect = lines_with(log, 'Gcomp RECT') or lines_with(unf, 'Gcomp RECT')
gdone = lines_with(log, 'Gcomp Done') or lines_with(unf, 'Gcomp Done')
apply_lines = lines_with(log, 'rendererApplyPendingGpuCopies') or lines_with(unf, 'rendererApplyPendingGpuCopies')
pixel_rgb = [ln for ln in (both + '\n' + x100 + mixed + x1000 + oracle).splitlines() if 'PIXEL_RGB_MISMATCH' in ln]
pixel_x = [ln for ln in (both + '\n' + x100 + mixed + x1000 + oracle).splitlines() if 'PIXEL_XBYTE_MISMATCH' in ln]
fatal_signal = [ln for ln in both.splitlines() if 'Fatal signal' in ln or 'SIGSEGV' in ln or 'SIGILL' in ln]
gatea_event = len(re.findall(r'GATEA_EVENT', log))
ev35 = len(re.findall(r'event=35\b', log))

rect_times = [wall_s(ln) for ln in grect]
done_times = [wall_s(ln) for ln in gdone]
rect_done = []
di = 0
for rt in rect_times:
    if rt is None:
        continue
    while di < len(done_times) and (done_times[di] is None or done_times[di] < rt):
        di += 1
    if di < len(done_times) and done_times[di] is not None:
        rect_done.append(done_times[di] - rt)
        di += 1
apply_times = [wall_s(ln) for ln in apply_lines if wall_s(ln) is not None]
rect_apply = []
ai = 0
for rt in rect_times:
    if rt is None:
        continue
    while ai < len(apply_times) and apply_times[ai] < rt:
        ai += 1
    if ai < len(apply_times):
        rect_apply.append(apply_times[ai] - rt)
        ai += 1

timeout_then_done = 0
if timeouts:
    tw = wall_s(timeouts[0])
    if tw is not None:
        timeout_then_done = sum(1 for ln in gdone if wall_s(ln) is not None and wall_s(ln) >= tw)

gt2000_rd = sum(1 for d in rect_done if d >= 2.0)
gt2000_ra = sum(1 for d in rect_apply if d >= 2.0)
max_rd = max(rect_done) if rect_done else None
max_ra = max(rect_apply) if rect_apply else None

om = re.search(r'ORACLE tests=(\d+) fail=(\d+) exact_px_acc=(\d+) ±1_px=(\d+) Xnz=(\d+) maxΔ=(\d+)', oracle)
oracle_ok = bool(om and om.group(1) == '1514' and om.group(2) == '0' and om.group(4) == '0' and om.group(5) == '0' and om.group(6) == '0' and 'RESULT p-b2-oracle PASS fail=0 maxΔ=0' in oracle)
st100 = stress_tuple(x100)
stmix = stress_tuple(mixed)
st1000 = stress_tuple(x1000)
x100_ok = bool(st100 and st100 == (0, 100, 0, 100, 1) and rc_of('X100_RC') == '0')
mixed_ok = bool(stmix and stmix == (1, 100, 0, 100, 1) and rc_of('MIXED_RC') == '0')
x1000_ok = bool(st1000 and st1000 == (0, 1000, 0, 1000, 1) and rc_of('X1000_RC') == '0')
env_ok = env.strip() == 'NO_GATEA_ENV'
prov_ok = 'PROVENANCE_BIND=PASS' in prov
residue_ok = 'NO_X3_RESIDUE' in teardown
oracle_ran = (cell / 'oracle.out').is_file()
x100_ran = (cell / 'x100.out').is_file()
mixed_ran = (cell / 'mixed100.out').is_file()
x1000_ran = (cell / 'x1000.out').is_file()

timeout_class = 'NONE'
if timeouts:
    # Production candidate: classify from consume vs timeout.
    timeout_class = 'UNCLASSIFIED_TIMEOUT'
    if gt2000_ra or (st1000 and st1000[4] == 0 and timeouts):
        timeout_class = 'CASE_LOOP_REGRESSION'
    # If apply continued through the serial window, different class.
    if max_ra is not None and max_ra < 2.0 and timeouts:
        timeout_class = 'NEW_TIMEOUT_CLASS'

invalid = False
invalid_reason = ''
if not prov_ok:
    invalid, invalid_reason = True, 'provenance bind missing'
if not env_ok:
    invalid, invalid_reason = True, (invalid_reason + '; ' if invalid_reason else '') + 'env contamination'
if not residue_ok:
    invalid, invalid_reason = True, (invalid_reason + '; ' if invalid_reason else '') + 'X3 residue'

if invalid:
    verdict = 'B2_REQUALIFICATION_INVALID'
    detail = invalid_reason
elif timeout_then_done:
    verdict = 'B2_REQUALIFICATION_BLOCKED'
    detail = f'TIMEOUT→DONE REGRESSION count={timeout_then_done}'
elif timeouts or fatals or exa_wait:
    verdict = 'B2_REQUALIFICATION_BLOCKED'
    detail = f'timeout/fatal class={timeout_class} timeout={len(timeouts)} fatal={len(fatals)}'
elif pixel_rgb or pixel_x:
    verdict = 'B2_REQUALIFICATION_BLOCKED'
    detail = f'pixel mismatch rgb={len(pixel_rgb)} xbyte={len(pixel_x)}'
elif gatea_event != 0 or ev35 != 0:
    verdict = 'B2_REQUALIFICATION_BLOCKED'
    detail = f'unexpected GATEA_EVENT={gatea_event} event35={ev35}'
elif not (oracle_ran and x100_ran and mixed_ran and x1000_ran and oracle_ok and x100_ok and mixed_ok and x1000_ok):
    verdict = 'B2_REQUALIFICATION_BLOCKED'
    detail = (
        f'stage fail oracle_ok={int(oracle_ok)} x100_ok={int(x100_ok)} '
        f'mixed_ok={int(mixed_ok)} x1000_ok={int(x1000_ok)} stopped={re.search(r"STOPPED_AFTER=(\\S+)", fx).group(1) if re.search(r"STOPPED_AFTER=(\\S+)", fx) else "NA"}'
    )
elif gt2000_rd or gt2000_ra:
    verdict = 'B2_REQUALIFICATION_BLOCKED'
    detail = f'>=2000ms gap rect_done={gt2000_rd} rect_apply={gt2000_ra}'
elif fatal_signal:
    verdict = 'B2_REQUALIFICATION_BLOCKED'
    detail = 'fatal signal'
else:
    verdict = 'B2_REQUALIFICATION_PASS'
    detail = 'oracle 1514/1514 + stress100 + mixed100 + stress1000 exact; no timeout/fatal'

lines = [
    f'verdict={verdict}',
    f'detail={detail}',
    'role=b2-requalification-01',
    f'env_ok={int(env_ok)}',
    f'prov_ok={int(prov_ok)}',
    f'oracle_ok={int(oracle_ok)}',
    f'x100_ok={int(x100_ok)}',
    f'mixed_ok={int(mixed_ok)}',
    f'x1000_ok={int(x1000_ok)}',
    f'st100={st100}',
    f'stmix={stmix}',
    f'st1000={st1000}',
    f'gcomp_prepare_true={len(gprep)}',
    f'gcomp_rect={len(grect)}',
    f'gcomp_done={len(gdone)}',
    f'apply={len(apply_lines)}',
    f'rect_done_samples={len(rect_done)}',
    f'rect_done_max_s={max_rd}',
    f'rect_done_gt2000={gt2000_rd}',
    f'rect_apply_samples={len(rect_apply)}',
    f'rect_apply_max_s={max_ra}',
    f'rect_apply_gt2000={gt2000_ra}',
    f'timeout_count={len(timeouts)}',
    f'fatal_count={len(fatals)}',
    f'exa_wait_count={len(exa_wait)}',
    f'timeout_then_done={timeout_then_done}',
    f'timeout_class={timeout_class}',
    f'pixel_rgb_mismatch={len(pixel_rgb)}',
    f'pixel_xbyte_mismatch={len(pixel_x)}',
    f'gatea_event={gatea_event}',
    f'event35={ev35}',
    f'fatal_signal={len(fatal_signal)}',
    'limitation=apply logs have no serial; RECT→apply is wall-clock proxy only',
    'not_r7=1',
]
if om:
    lines.append(f'oracle_line={om.group(0)}')
if timeouts:
    lines.append('TIMEOUT ' + timeouts[0][:220])
else:
    lines.append('TIMEOUT NONE')
if fatals:
    lines.append('FATAL ' + fatals[0][:220])
else:
    lines.append('FATAL NONE')
(cell / 'b2-classify.txt').write_text('\n'.join(lines) + '\n')
(cell / 'primary-verdict.txt').write_text(verdict + '\n')
print((cell / 'b2-classify.txt').read_text())
PY
}

echo "cmd=$FIX/p-b2-oracle" > "$CELL/command-oracle.txt"
date -Is | tee -a "$CELL/command-oracle.txt"
set +e
"$FIX/p-b2-oracle" | tee "$CELL/oracle.out"
ORACLE_RC=${PIPESTATUS[0]}
set -e
date -Is | tee -a "$CELL/command-oracle.txt"
record_stage ORACLE
if ! x_alive || [ "$ORACLE_RC" -ne 0 ] || ! grep -q 'ORACLE tests=1514 fail=0' "$CELL/oracle.out" || ! grep -q 'RESULT p-b2-oracle PASS fail=0 maxΔ=0' "$CELL/oracle.out"; then
  STOPPED_AFTER=oracle
  run_cleanup_and_judge
  echo "B2_STOPPED_AFTER_ORACLE rc=$ORACLE_RC"
  exit 0
fi

echo "cmd=$FIX/p_b2_stress 100" > "$CELL/command-x100.txt"
date -Is | tee -a "$CELL/command-x100.txt"
set +e
"$FIX/p_b2_stress" 100 | tee "$CELL/x100.out"
X100_RC=${PIPESTATUS[0]}
set -e
date -Is | tee -a "$CELL/command-x100.txt"
record_stage X100
if ! x_alive || [ "$X100_RC" -ne 0 ] || ! grep -E 'ok=100 fail=0' "$CELL/x100.out"; then
  STOPPED_AFTER=stress100
  run_cleanup_and_judge
  echo "B2_STOPPED_AFTER_STRESS100 rc=$X100_RC"
  exit 0
fi

echo "cmd=$FIX/p_b2_stress 100 1" > "$CELL/command-mixed100.txt"
date -Is | tee -a "$CELL/command-mixed100.txt"
set +e
"$FIX/p_b2_stress" 100 1 | tee "$CELL/mixed100.out"
MIXED_RC=${PIPESTATUS[0]}
set -e
date -Is | tee -a "$CELL/command-mixed100.txt"
record_stage MIXED100
if ! x_alive || [ "$MIXED_RC" -ne 0 ] || ! grep -E 'ok=100 fail=0' "$CELL/mixed100.out"; then
  STOPPED_AFTER=mixed100
  run_cleanup_and_judge
  echo "B2_STOPPED_AFTER_MIXED100 rc=$MIXED_RC"
  exit 0
fi

echo "cmd=$FIX/p_b2_stress 1000" > "$CELL/command.txt"
date -Is | tee -a "$CELL/command.txt"
set +e
"$FIX/p_b2_stress" 1000 | tee "$CELL/x1000.out"
X1000_RC=${PIPESTATUS[0]}
set -e
date -Is | tee -a "$CELL/command.txt"
record_stage X1000
if ! x_alive || [ "$X1000_RC" -ne 0 ] || ! grep -E 'ok=1000 fail=0' "$CELL/x1000.out"; then
  STOPPED_AFTER=stress1000
  run_cleanup_and_judge
  echo "B2_STOPPED_AFTER_STRESS1000 rc=$X1000_RC"
  exit 0
fi

STOPPED_AFTER=complete
run_cleanup_and_judge
echo "B2_REQUALIFICATION_SEQUENCE_COMPLETE"
