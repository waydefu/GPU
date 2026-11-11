#!/usr/bin/env bash
# ONE stall-notify-function device observation on installed feeaa56.
# NOT B-2: no oracle, no stress100, no mixed100, no B-2 PASS/FAIL judge.
# NOT R7: TEST_FAULT unset. Timeout stays 2000. No retry.
# Workload: one p_b2_stress 1000 only.
# Usage: SERIAL=HOST:PORT CELL=.../runtime-feeaa56/stall-obs-01 bash run-stall-obs-feeaa56.sh
set -euo pipefail
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-terminal-runtime
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt
EXPECT_STRESS_SHA256=3e79b5cf875f5d7d05a25634983a44d9acfe67dfb885bf11f19b2cdb70e43c56
EXPECT_VERSION=1.03.01-feeaa56-16.09.26
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
  */runtime-feeaa56/stall-obs-01) ;;
  *) echo "REFUSE CELL must be .../runtime-feeaa56/stall-obs-01 got=$CELL"; exit 9;;
esac
if [ -f "$CELL/stall-stress1000.out" ]; then
  echo "REFUSE CELL already has stall-stress1000.out (no retry)"
  exit 9
fi

test -x "$FIX/p_b2_stress"
STRESS_SHA=$(sha256sum "$FIX/p_b2_stress" | awk '{print $1}')
test "$STRESS_SHA" = "$EXPECT_STRESS_SHA256"
echo "role=stall-obs-not-b2-not-r7 p_b2_stress_sha256=$STRESS_SHA" | tee "$CELL/preflight.txt"
ADB shell dumpsys package com.waydefu.x11gpu | grep -E 'versionName=|lastUpdateTime=' | head -4 | tee "$CELL/installed-package-pre.txt"
grep -q "versionName=$EXPECT_VERSION" "$CELL/installed-package-pre.txt"
ADB shell dumpsys package com.termux.x11 | grep -E 'versionCode=|versionName=|lastUpdateTime=' | head -6 | tee "$CELL/stable-package-pre.txt"
grep -q 'versionName=1.03.01-11b82d9-06.09.26' "$CELL/stable-package-pre.txt"

ADB shell dumpsys power | grep mWakefulness= | head -1 | tee "$CELL/screen.txt"
ADB shell dumpsys window | grep isKeyguardShowing= | head -1 >> "$CELL/screen.txt"
grep -q 'mWakefulness=Awake' "$CELL/screen.txt"
grep -q 'isKeyguardShowing=false' "$CELL/screen.txt"

STABLE_PRE=$(stabpid)
STABLE_CMD_PRE=$(stab_cmd)
echo "stable_pre_pid=$STABLE_PRE" | tee "$CELL/stable-pre.txt"
echo "stable_pre_cmd=$STABLE_CMD_PRE" | tee -a "$CELL/stable-pre.txt"
test -n "$STABLE_PRE"
echo "$STABLE_CMD_PRE" | grep -q '^termux-x11 com.termux.x11 :1'

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
python3 "$RUN" | tee "$CELL/start-x3.out"
X3=""
for i in $(seq 1 40); do
  if X3=$(x3pid); then break; fi
  sleep 0.5
done
test -n "$X3"
echo "x3_pid=$X3 mode=unset role=stall-obs" | tee "$CELL/x3-pid.txt"
save_x_identity "$X3" "$CELL"
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
  exit 2
fi
echo "ALIVE_BEFORE_STRESS pid=$X3" | tee "$CELL/alive.txt"

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

echo "cmd=$FIX/p_b2_stress 1000 role=stall-obs-not-b2" > "$CELL/command.txt"
date -Is >> "$CELL/command.txt"
set +e
"$FIX/p_b2_stress" 1000 | tee "$CELL/stall-stress1000.out"
STRESS_RC=${PIPESTATUS[0]}
set -e
date -Is >> "$CELL/command.txt"
echo "STRESS_RC=$STRESS_RC" | tee "$CELL/fixture-exit.txt"
if [ -d "/proc/$X3" ]; then echo "X3_ALIVE=yes pid=$X3" | tee -a "$CELL/alive.txt"
else echo "X3_ALIVE=no pid=$X3" | tee -a "$CELL/alive.txt"; fi

{
  echo '===STALL_PHASE==='
  grep -c 'STALL_PHASE phase=' "$CELL/logcat-follow.txt" || echo 0
  echo '===NOTIFY==='
  grep -c 'phase=NOTIFY_ENTER' "$CELL/logcat-follow.txt" || echo 0
  grep -c 'phase=NOTIFY_EXIT' "$CELL/logcat-follow.txt" || echo 0
  echo '===timeout==='
  grep -c 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo 0
  grep 'EXA GPU composite wait timeout' "$CELL/logcat-follow.txt" || echo NONE
  echo '===fatal==='
  grep -E 'GATEA_FATAL_HALT|x-exa-composite-wait|Fatal signal|SIGSEGV|SIGILL' "$CELL/logcat-follow.txt" "$CELL/x3-launcher.raw.log" || echo NONE
  echo '===gcomp==='
  grep -c 'Gcomp Done' "$CELL/logcat-follow.txt" || echo 0
  echo '===apply==='
  grep -c 'rendererApplyPendingGpuCopies' "$CELL/logcat-follow.txt" || echo 0
} | tee "$CELL/telemetry-fatal-pre-teardown.txt"

ADB logcat -d -v threadtime -T "$SINCE" > "$CELL/logcat-dump-unfiltered.txt" || true

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
grep -q 'lastUpdateTime=2026-09-07 22:55:03' "$CELL/stable-package-after.txt"

python3 - "$CELL" <<'PY'
import re, statistics, sys
from pathlib import Path

NS2MS = 1e-6
STALL_NS = 2_000_000_000

def wall_s(ln):
    parts = ln.split()
    if len(parts) < 2 or ':' not in parts[1]:
        return None
    h, m, rest = parts[1].split(':')
    s, ms = rest.split('.')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms[:3]) / 1000.0

phase_re = re.compile(
    r'STALL_PHASE phase=(\S+) mono_ns=(\d+) tid=(\d+)'
    r'(?: result=(-?\d+))?'
    r' completedSerial=(\d+) readIndex=(\d+) writeIndex=(\d+)'
)

cell = Path(sys.argv[1])
log = (cell / 'logcat-follow.txt').read_text(errors='replace')
unf = ''
unf_path = cell / 'logcat-dump-unfiltered.txt'
if unf_path.is_file():
    unf = unf_path.read_text(errors='replace')

events = []
for ln in log.splitlines():
    m = phase_re.search(ln)
    if not m:
        continue
    events.append({
        'wall': wall_s(ln),
        'phase': m.group(1),
        'mono': int(m.group(2)),
        'tid': m.group(3),
        'result': m.group(4),
        'cs': int(m.group(5)),
        'rd': int(m.group(6)),
        'wr': int(m.group(7)),
        'line': ln[:260],
    })
timeouts = [ln for ln in log.splitlines() if 'EXA GPU composite wait timeout' in ln]
fatals = [ln for ln in (log + '\n' + unf).splitlines() if 'GATEA_FATAL_HALT' in ln]
exa_wait = [ln for ln in log.splitlines() if 'x-exa-composite-wait' in ln]
gcomp = [ln for ln in log.splitlines() if 'Gcomp Done' in ln]
mismatches = [ln for ln in (log + '\n' + unf).splitlines() if 'PIXEL_RGB_MISMATCH' in ln]
apply_follow = sum(1 for ln in log.splitlines() if 'rendererApplyPendingGpuCopies' in ln)
apply_unf = sum(1 for ln in unf.splitlines() if 'rendererApplyPendingGpuCopies' in ln)
notify_enter_unf = sum(1 for ln in unf.splitlines() if 'phase=NOTIFY_ENTER' in ln)
notify_exit_unf = sum(1 for ln in unf.splitlines() if 'phase=NOTIFY_EXIT' in ln)

if not events:
    (cell / 'stall-phase-classify.txt').write_text(
        'verdict=DIAGNOSTIC_RUN_INVALID\n'
        'detail=STALL_PHASE markers missing from logcat — instrumentation not live\n'
        'not_b2=1\n'
    )
    print((cell / 'stall-phase-classify.txt').read_text())
    raise SystemExit(0)

counts = {}
for ev in events:
    counts[ev['phase']] = counts.get(ev['phase'], 0) + 1

pairs = {'NOTIFY': [], 'SWAP': [], 'NEXT_FENCE': []}
open_enter = {}
unmatched_exit = {'NOTIFY': 0, 'SWAP': 0, 'NEXT_FENCE': 0}
for ev in events:
    name = ev['phase']
    if name.endswith('_ENTER'):
        kind = name[:-6]
        open_enter[kind] = ev
    elif name.endswith('_EXIT'):
        kind = name[:-5]
        enter = open_enter.pop(kind, None)
        if enter is None:
            unmatched_exit[kind] = unmatched_exit.get(kind, 0) + 1
            continue
        dt = ev['mono'] - enter['mono']
        pairs[kind].append((enter, ev, dt))

def pair_stats(kind):
    dts = [p[2] for p in pairs[kind]]
    if not dts:
        return {
            'n': 0, 'min_ns': None, 'med_ns': None, 'max_ns': None,
            'max_ms': None, 'gt2000': 0,
            'unmatched_enter': int(kind in open_enter),
            'unmatched_exit': unmatched_exit.get(kind, 0),
        }
    return {
        'n': len(dts),
        'min_ns': min(dts),
        'med_ns': int(statistics.median(dts)),
        'max_ns': max(dts),
        'max_ms': round(max(dts) * NS2MS, 3),
        'gt2000': sum(1 for d in dts if d >= STALL_NS),
        'unmatched_enter': int(kind in open_enter),
        'unmatched_exit': unmatched_exit.get(kind, 0),
    }

stats = {k: pair_stats(k) for k in ('NOTIFY', 'SWAP', 'NEXT_FENCE')}
notify_enter = counts.get('NOTIFY_ENTER', 0)
notify_exit = counts.get('NOTIFY_EXIT', 0)

coverage_invalid = False
coverage_detail = ''
if apply_unf >= 10 and notify_enter == 0 and notify_enter_unf == 0:
    coverage_invalid = True
    coverage_detail = (
        'notify function-body instrumentation unexpectedly not observable '
        f'(apply_unf={apply_unf} NOTIFY_ENTER follow=0 unfiltered=0)'
    )

timeout_then_done = 0
if timeouts:
    tw = wall_s(timeouts[0])
    if tw is not None:
        timeout_then_done = sum(
            1 for ln in gcomp if (wall_s(ln) is not None and wall_s(ln) >= tw)
        )

cutoff = wall_s(timeouts[0]) if timeouts else None
before = [e for e in events if cutoff is None or (e['wall'] is not None and e['wall'] <= cutoff)]
last = {}
for e in before:
    last[e['phase']] = e

def ns(name):
    ev = last.get(name)
    return ev['mono'] if ev else None

verdict = 'STALL_NOT_OBSERVED'
detail = 'stress completed without EXA wait timeout / fatal'
if coverage_invalid:
    verdict = 'DIAGNOSTIC_RUN_INVALID'
    detail = coverage_detail
elif timeout_then_done:
    verdict = 'DIAGNOSTIC_RUN_INVALID'
    detail = f'timeout→Done regression Gcomp_Done_after_timeout={timeout_then_done}'
elif timeouts or fatals:
    ne, nx = ns('NOTIFY_ENTER'), ns('NOTIFY_EXIT')
    se, sx = ns('SWAP_ENTER'), ns('SWAP_EXIT')
    fe, fx = ns('NEXT_FENCE_ENTER'), ns('NEXT_FENCE_EXIT')
    notify_hold = (nx - ne) if (ne is not None and nx is not None and nx >= ne) else None
    swap_hold = (sx - se) if (se is not None and sx is not None and sx >= se) else None
    fence_hold = (fx - fe) if (fe is not None and fx is not None and fx >= fe) else None
    if ne is not None and (nx is None or nx < ne or (notify_hold is not None and notify_hold >= STALL_NS)):
        verdict = 'CASE_NOTIFY'
        detail = (
            f'NOTIFY_ENTER={ne} NOTIFY_EXIT={nx if nx is not None else "NOT OBSERVED"}'
            + (f' hold_ns={notify_hold}' if notify_hold is not None else '')
        )
    elif se is not None and (sx is None or sx < se or (swap_hold is not None and swap_hold >= STALL_NS)):
        verdict = 'CASE_SWAP'
        detail = (
            f'SWAP_ENTER={se} SWAP_EXIT={sx if sx is not None else "NOT OBSERVED"}'
            + (f' hold_ns={swap_hold}' if swap_hold is not None else '')
        )
    elif fe is not None and (fx is None or fx < fe or (fence_hold is not None and fence_hold >= STALL_NS)):
        verdict = 'CASE_NEXT_FENCE'
        detail = (
            f'NEXT_FENCE_ENTER={fe} NEXT_FENCE_EXIT={fx if fx is not None else "NOT OBSERVED"}'
            + (f' hold_ns={fence_hold}' if fence_hold is not None else '')
        )
    elif (
        ne is not None and nx is not None and notify_hold is not None and notify_hold < STALL_NS
        and se is not None and sx is not None and swap_hold is not None and swap_hold < STALL_NS
        and fe is not None and fx is not None and fence_hold is not None and fence_hold < STALL_NS
    ):
        verdict = 'CASE_LOOP'
        last_ev = before[-1] if before else None
        lag = None
        if last_ev:
            lag = last_ev['wr'] - last_ev['rd']
        detail = (
            f'notify_ns={notify_hold} swap_ns={swap_hold} next_fence_ns={fence_hold}'
            f' last_cs={last_ev["cs"] if last_ev else "NOT OBSERVED"}'
            f' last_rd={last_ev["rd"] if last_ev else "NOT OBSERVED"}'
            f' last_wr={last_ev["wr"] if last_ev else "NOT OBSERVED"}'
            f' lag={lag if lag is not None else "NOT OBSERVED"}'
        )
    else:
        verdict = 'DIAGNOSTIC_RUN_INVALID'
        detail = (
            f'NOTIFY_ENTER={ne} NOTIFY_EXIT={nx} SWAP_ENTER={se} SWAP_EXIT={sx}'
            f' NEXT_FENCE_ENTER={fe} NEXT_FENCE_EXIT={fx}'
        )

sf_hits = [ln for ln in unf.splitlines() if 'fromDequeueTime' in ln or 'BufferQueue' in ln]
(cell / 'surface-bufferqueue.txt').write_text(
    f'fromDequeueTime_count={sum(1 for ln in unf.splitlines() if "fromDequeueTime" in ln)}\n'
    f'BufferQueue_count={sum(1 for ln in unf.splitlines() if "BufferQueue" in ln)}\n'
    f'SurfaceFlinger_count={sum(1 for ln in unf.splitlines() if "SurfaceFlinger" in ln)}\n'
    + ('\n'.join(sf_hits[:40]) if sf_hits else 'NOT OBSERVED\n')
)

dur_lines = [
    '# STALL_PHASE interval stats — stall-obs-01 (not a B-2 verdict)',
    f'source=logcat-follow.txt parsed_events={len(events)}',
    'phase_counts ' + ' '.join(f'{k}={v}' for k, v in sorted(counts.items())),
    f'apply_follow={apply_follow} apply_unfiltered={apply_unf}',
    f'NOTIFY_unfiltered ENTER={notify_enter_unf} EXIT={notify_exit_unf}',
]
for kind in ('NOTIFY', 'SWAP', 'NEXT_FENCE'):
    st = stats[kind]
    dur_lines.append(
        f'{kind}_ENTER→EXIT n={st["n"]} min_ns={st["min_ns"]} med_ns={st["med_ns"]}'
        f' max_ns={st["max_ns"]} max_ms={st["max_ms"]} gt2000ms={st["gt2000"]}'
        f' unmatched_enter={st["unmatched_enter"]} unmatched_exit={st["unmatched_exit"]}'
    )
    if pairs[kind]:
        top = sorted(pairs[kind], key=lambda p: p[2], reverse=True)[:2]
        dur_lines.append(
            '  top_ms=' + ' '.join(f'{round(p[2]*NS2MS,3)}@cs={p[1]["cs"]}' for p in top)
        )
dur_lines += [
    f'EXA timeout count={len(timeouts)}',
    f'Gcomp Done={len(gcomp)}',
    f'fatal_count={len(fatals)}',
    f'pixel_mismatch={len(mismatches)}',
    f'timeout_then_done={timeout_then_done}',
    f'verdict={verdict}',
    'not_b2=1',
]
(cell / 'stall-phase-durations.txt').write_text('\n'.join(dur_lines) + '\n')

out = cell / 'stall-phase-classify.txt'
out.write_text(
    f'verdict={verdict}\n'
    f'detail={detail}\n'
    f'stall_phase_count={len(events)}\n'
    f'phases_before_timeout={len(before)}\n'
    f'timeout_count={len(timeouts)}\n'
    f'fatal_count={len(fatals)}\n'
    f'gcomp_count={len(gcomp)}\n'
    f'apply_follow={apply_follow}\n'
    f'apply_unfiltered={apply_unf}\n'
    f'notify_enter_follow={notify_enter}\n'
    f'notify_exit_follow={notify_exit}\n'
    f'notify_enter_unfiltered={notify_enter_unf}\n'
    f'notify_exit_unfiltered={notify_exit_unf}\n'
    f'notify_max_ms={stats["NOTIFY"]["max_ms"]}\n'
    f'swap_max_ms={stats["SWAP"]["max_ms"]}\n'
    f'next_fence_max_ms={stats["NEXT_FENCE"]["max_ms"]}\n'
    f'pixel_mismatch={len(mismatches)}\n'
    f'timeout_then_done={timeout_then_done}\n'
    f'not_b2=1\n'
    + ('TIMEOUT ' + timeouts[0][:220] + '\n' if timeouts else 'TIMEOUT NONE\n')
    + ('FATAL ' + fatals[0][:220] + '\n' if fatals else 'FATAL NONE\n')
    + 'LAST_PHASES_BEFORE_TIMEOUT\n'
    + '\n'.join(p['line'] for p in before[-16:])
    + '\n'
)
print(out.read_text())
print((cell / 'stall-phase-durations.txt').read_text())
PY

echo "STALL_OBS_COMPLETE stress_rc=$STRESS_RC (not a B-2 verdict)"
