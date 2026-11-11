#!/usr/bin/env bash
# p2b3a_session.sh — one bounded Experimental :3 B3a server session.
# Scope: com.waydefu.x11gpu only. No Stable package/display command.
# Usage:
#   p2b3a_session.sh SERIAL CANDIDATE LABEL OUT WARMUP COUNT MODE REUSE BATCH COLD
# Example expected records: 1519 + (WARMUP + COUNT) * BATCH.
set -euo pipefail

if [ "$#" -ne 10 ]; then
  echo "usage: $0 SERIAL cpu|r3 LABEL OUT WARMUP COUNT MODE REUSE BATCH COLD" >&2
  exit 2
fi

SERIAL="$1"
CANDIDATE="$2"
LABEL="$3"
OUT="$4"
WARMUP="$5"
COUNT="$6"
MODE="$7"
REUSE="$8"
BATCH="$9"
COLD="${10}"
PKG="com.waydefu.x11gpu"
ACTIVITY="com.termux.x11.MainActivity"
ADB=(/data/data/com.termux/files/usr/bin/env ANDROID_NO_USE_FWMARK_CLIENT=1 /data/data/com.termux/files/usr/bin/adb -s "$SERIAL")
EXPECTED=$((1519 + (WARMUP + COUNT) * BATCH))
LPID=""
HPID=""
SERVERPID=""

case "$CANDIDATE" in cpu|r3) ;; *) echo "invalid candidate: $CANDIDATE" >&2; exit 2;; esac
for suffix in .json .csv -activity.out -display.out -launcher.log -holder.out -oracle.out -cell.out -phases.log -resources.txt -telemetry-check.txt -serverpid.txt; do
  if [ -e "${OUT}${suffix}" ]; then
    echo "refusing pre-existing output: ${OUT}${suffix}" >&2
    exit 2
  fi
done

phase() {
  printf '%s %s\n' "$(date -Is)" "$1" | tee -a "${OUT}-phases.log"
}

server_pid() {
  "${ADB[@]}" shell 'for p in /proc/[0-9]*; do x=$(tr "\000" " " < "$p/cmdline" 2>/dev/null); case "$x" in "termux-x11gpu com.waydefu.x11gpu :3"*) printf "%s\n" "${p##*/}";; esac; done' 2>/dev/null | awk 'NF { print; exit }'
}

residue_check() {
  local matches
  matches=$("${ADB[@]}" shell 'n=0; for p in /proc/[0-9]*; do x=$(tr "\000" " " < "$p/cmdline" 2>/dev/null); case "$x" in "termux-x11gpu com.waydefu.x11gpu :3"*) printf "%s:%s\n" "${p##*/}" "$x"; n=$((n+1));; esac; done; [ "$n" -eq 0 ] && echo NO_X3_RESIDUE || printf "X3_RESIDUE_COUNT=%s\n" "$n"' 2>/dev/null || true)
  printf '%s\n' "$matches" | tee -a "${OUT}-resources.txt"
  [ "$matches" = "NO_X3_RESIDUE" ]
}

sample() {
  local tag="$1" pid="$2" rss fd hold_alive rss_command fd_command
  rss_command="awk '/^VmRSS:/{print \$2}' /proc/$pid/status 2>/dev/null"
  rss=$("${ADB[@]}" shell "$rss_command" 2>/dev/null | tr -d '\r' | awk 'NF { print; exit }' || true)
  [ -n "$rss" ] || rss=NA
  fd_command="ls -1 /proc/$pid/fd 2>/dev/null | wc -l"
  fd=$("${ADB[@]}" shell "$fd_command" 2>/dev/null | tr -d '\r' | awk 'NF { print; exit }' || true)
  case "$fd" in ''|*[!0-9]*|0) fd=NA;; esac
  if [ -n "$HPID" ] && kill -0 "$HPID" 2>/dev/null; then hold_alive=1; else hold_alive=0; fi
  printf '%s rss_kb=%s fd=%s x3proc=1 serverpid=%s holder=%s\n' "$tag" "$rss" "$fd" "$pid" "$hold_alive" | tee -a "${OUT}-resources.txt"
}

cleanup() {
  rc=$?
  if [ -n "$HPID" ] && kill -0 "$HPID" 2>/dev/null; then kill "$HPID" 2>/dev/null || true; wait "$HPID" 2>/dev/null || true; fi
  if [ -n "$LPID" ] && kill -0 "$LPID" 2>/dev/null; then kill "$LPID" 2>/dev/null || true; wait "$LPID" 2>/dev/null || true; fi
  exit "$rc"
}
trap cleanup EXIT INT TERM

phase SESSION_START
printf 'serial=%s candidate=%s label=%s expected_records=%s warmup=%s count=%s mode=%s reuse=%s batch=%s cold=%s\n' \
  "$SERIAL" "$CANDIDATE" "$LABEL" "$EXPECTED" "$WARMUP" "$COUNT" "$MODE" "$REUSE" "$BATCH" "$COLD" > "${OUT}-resources.txt"

phase ACTIVITY_START
"${ADB[@]}" shell am start --display 0 -W -n "$PKG/$ACTIVITY" > "${OUT}-activity.out" 2>&1
"${ADB[@]}" shell 'dumpsys activity activities | grep -A 45 -m 1 "ActivityRecord.*com.waydefu.x11gpu/com.termux.x11.MainActivity"' > "${OUT}-display.out" 2>&1
if ! grep -q 'display=0' "${OUT}-display.out" || ! grep -q 'state=RESUMED' "${OUT}-display.out" || ! grep -q 'reportedDrawn=true' "${OUT}-display.out"; then
  phase INVALID_DISPLAY_TARGET
  exit 1
fi

phase X3_LAUNCH
if [ "$CANDIDATE" = cpu ]; then
  HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/usr/bin:/system/bin:/system/xbin DISPLAY=:3 TMPDIR=/data/data/com.termux/files/usr/tmp \
    TERMUX_X11_B3A_TELEMETRY=1 TERMUX_X11_B3A_CANDIDATE="$CANDIDATE" TERMUX_X11_B3A_OUTPUT="$OUT" TERMUX_X11_DISABLE_EXA_GPU=1 \
    /data/data/com.termux/files/usr/bin/bash -lc 'exec /data/data/com.termux/files/usr/bin/f8-x11gpu :3' > "${OUT}-launcher.log" 2>&1 &
else
  HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/usr/bin:/system/bin:/system/xbin DISPLAY=:3 TMPDIR=/data/data/com.termux/files/usr/tmp \
    TERMUX_X11_B3A_TELEMETRY=1 TERMUX_X11_B3A_CANDIDATE="$CANDIDATE" TERMUX_X11_B3A_OUTPUT="$OUT" \
    /data/data/com.termux/files/usr/bin/bash -lc 'exec /data/data/com.termux/files/usr/bin/f8-x11gpu :3' > "${OUT}-launcher.log" 2>&1 &
fi
LPID=$!
for _ in $(seq 1 80); do
  SERVERPID=$(server_pid || true)
  [ -n "$SERVERPID" ] && break
  if ! kill -0 "$LPID" 2>/dev/null; then phase X3_LAUNCH_FAILED; exit 1; fi
  sleep 1
done
if [ -z "$SERVERPID" ]; then phase X3_PID_NOT_FOUND; exit 1; fi
printf 'serverpid=%s cmdline=termux-x11gpu com.waydefu.x11gpu :3\n' "$SERVERPID" > "${OUT}-serverpid.txt"

DISPLAY=:3 /tmp/p_b3a_hold > "${OUT}-holder.out" 2>&1 &
HPID=$!
for _ in $(seq 1 20); do
  grep -q '^HOLD READY$' "${OUT}-holder.out" 2>/dev/null && break
  if ! kill -0 "$HPID" 2>/dev/null; then phase HOLDER_FAILED; exit 1; fi
  sleep 1
done
if ! grep -q '^HOLD READY$' "${OUT}-holder.out"; then phase HOLDER_TIMEOUT; exit 1; fi
sample T0_X_READY "$SERVERPID"

phase ORACLE_BEGIN
DISPLAY=:3 /data/data/com.termux/files/usr/tmp/p-b2-oracle > "${OUT}-oracle.out" 2>&1
if ! grep -Fq 'RESULT p-b2-oracle PASS fail=0 maxΔ=0' "${OUT}-oracle.out"; then phase ORACLE_FAIL; exit 1; fi
phase ORACLE_PASS
sample T1_ORACLE_PASS "$SERVERPID"

phase WARMUP_BEGIN
DISPLAY=:3 /tmp/p_b3a_cost "$LABEL" 64 64 64 64 0 0 0 0 "$WARMUP" "$COUNT" "$MODE" "$REUSE" "$BATCH" "$COLD" > "${OUT}-cell.out" 2>&1
if grep -Fq 'MISMATCH' "${OUT}-cell.out" || ! grep -Fq "CELLDONE name=$LABEL ops=$COUNT" "${OUT}-cell.out"; then phase CELL_FAIL; exit 1; fi
phase WARMUP_DONE
phase MEASURE_BEGIN
phase MEASURE_DONE
sample T2_CELL_PASS "$SERVERPID"

phase TEARDOWN_BEGIN
kill "$HPID"
wait "$HPID"
HPID=""
sample T2_HOLDER_RELEASED "$SERVERPID"
kill "$LPID"
wait "$LPID" || true
LPID=""
for _ in $(seq 1 40); do
  [ -e "${OUT}.json" ] && [ -e "${OUT}.csv" ] && break
  sleep 1
done
if [ ! -e "${OUT}.json" ] || [ ! -e "${OUT}.csv" ]; then phase TELEMETRY_MISSING; exit 1; fi
python3 - "$OUT.json" "$EXPECTED" "$CANDIDATE" > "${OUT}-telemetry-check.txt" <<'PY'
import json, sys
path, expected, candidate = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = json.load(open(path))
rows = d['records']
assert d['next_record'] == expected, (d['next_record'], expected)
assert len(rows) == expected, (len(rows), expected)
assert d['dropped_records'] == 0, d['dropped_records']
assert all(r['candidate'] == candidate for r in rows), 'candidate mismatch'
cell = rows[1519:]
assert len(cell) == expected - 1519, len(cell)
assert all(r['exact_fail'] is None and r['max_delta'] is None and r['x_nz'] is None for r in cell), 'unexpected telemetry correctness fields'
if candidate == 'r3':
    assert all(r['fallback'] == 0 for r in cell), 'R3 fallback'
else:
    assert all(r['fallback'] == 1 for r in cell), 'CPU fallback'
print(f'TELEMETRY PASS next_record={d["next_record"]} dropped={d["dropped_records"]} records={len(rows)} cell={len(cell)} candidate={candidate}')
m = d['metadata']
print('X_SERVER_ENDPOINT ' + ' '.join(f'{k}={m.get(k)}' for k in ('x_rss_start_bytes', 'x_rss_end_bytes', 'x_fd_start', 'x_fd_end')))
print('RENDERER_ENDPOINT ' + ' '.join(f'{k}={m.get(k)}' for k in ('renderer_rss_start_bytes', 'renderer_rss_end_bytes', 'renderer_fd_start', 'renderer_fd_end')))
print('TELEMETRY_CORRECTNESS=NOT_OBSERVABLE (oracle + driver first-pixel check are authoritative)')
print('QUEUE_STATE=NOT_OBSERVABLE' if all(r['queue_ns'] is None for r in cell) else 'QUEUE_STATE=OBSERVED')
PY
printf 'T3_AFTER_TEARDOWN rss_kb=NA fd=0 x3proc=0 serverpid=%s holder=0\n' "$SERVERPID" | tee -a "${OUT}-resources.txt"
if ! residue_check; then phase X3_RESIDUE; exit 1; fi
phase TEARDOWN_DONE
phase SESSION_END
trap - EXIT INT TERM
printf 'SESSION PASS label=%s expected_records=%s\n' "$LABEL" "$EXPECTED"
