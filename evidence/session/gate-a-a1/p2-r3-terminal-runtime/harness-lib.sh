#!/usr/bin/env bash
# Gate A P2 R3 post-drain harness library. DO NOT run this round.
# New evidence directory per commit. Never overwrite 8479997 cells.
# PID saved for logcat MUST be the adb binary after exec, not a function wrapper.

set -euo pipefail

TADB=/data/data/com.termux/files/usr/bin/adb
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
RUN=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py

: "${SERIAL:?set SERIAL to a live-fetched HOST:PORT}"
: "${CELL:?set CELL to a fresh evidence directory}"

ADB() {
  env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
    HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
    "$TADB" -H 127.0.0.1 -P 5038 -s "$SERIAL" "$@"
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

stab_cmd() {
  local p
  p=$(stabpid) || return 1
  tr '\0' ' ' < "/proc/$p/cmdline"
}

assert_display0() {
  local dump=$1
  grep -q 'com.waydefu.x11gpu/com.termux.x11.MainActivity' "$dump"
  grep -A40 'com.waydefu.x11gpu/com.termux.x11.MainActivity' "$dump" | grep -q 'displayId=0'
}

start_logcat() {
  local out=$1 since=$2
  (
    exec env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
      HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
      "$TADB" -H 127.0.0.1 -P 5038 -s "$SERIAL" logcat -v threadtime -T "$since" \
      gatea-telemetry:V gatea-a1:V LorieNative:I DEBUG:I libc:F Xlorie:I gles-renderer:I \
      > "$out" 2>&1
  ) &
  echo $!
}

verify_logcat_pid() {
  local pid=$1
  local exe cmd
  [ -d "/proc/$pid" ]
  exe=$(readlink "/proc/$pid/exe")
  [ "$exe" = "$TADB" ]
  cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline")
  case "$cmd" in
    *' -H 127.0.0.1 '*|*' -H 127.0.0.1') ;;
    *) echo "REFUSE logcat pid $pid missing -H 127.0.0.1 cmd=$cmd"; return 1;;
  esac
  case "$cmd" in
    *' -P 5038 '*|*' -P 5038') ;;
    *) echo "REFUSE logcat pid $pid missing -P 5038 cmd=$cmd"; return 1;;
  esac
  case "$cmd" in
    *logcat*) ;;
    *server*) echo "REFUSE logcat pid $pid is server"; return 1;;
    *) echo "REFUSE logcat pid $pid not logcat cmd=$cmd"; return 1;;
  esac
}

stop_logcat() {
  local pid=$1
  if [ -n "$pid" ] && [ -d "/proc/$pid" ]; then
    verify_logcat_pid "$pid"
    kill -TERM "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
  if [ -n "$pid" ] && [ -d "/proc/$pid" ]; then
    echo "STOP logcat pid $pid still alive after TERM"
    return 1
  fi
}

save_x_identity() {
  local pid=$1 dest=$2
  echo "x3_pid=$pid" > "$dest/x-identity.txt"
  tr '\0' ' ' < "/proc/$pid/cmdline" | tee -a "$dest/x-identity.txt"
  readlink "/proc/$pid/exe" | tee -a "$dest/x-identity.txt"
  cat "/proc/$pid/maps" > "$dest/x3.maps"
}

LOGCAT_PID=""
HOLDER_PID=""
cleanup() {
  local rc=$?
  if [ -n "${HOLDER_PID:-}" ]; then
    kill -TERM "$HOLDER_PID" 2>/dev/null || true
    wait "$HOLDER_PID" 2>/dev/null || true
  fi
  if [ -n "${LOGCAT_PID:-}" ]; then
    stop_logcat "$LOGCAT_PID" || true
  fi
  return "$rc"
}
trap cleanup EXIT
