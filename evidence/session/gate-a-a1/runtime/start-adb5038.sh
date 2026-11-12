#!/usr/bin/env bash
set -u
RUNTIME="/root/projects/GPU加速/evidence/session/gate-a-a1/runtime"
LOG="$RUNTIME/r1-adb5038-server.raw.txt"
PIDFILE="$RUNTIME/r1-adb5038-server.pid"
if [ -e "$PIDFILE" ]; then
  printf 'refusing pre-existing pidfile=%s\n' "$PIDFILE" >&2
  exit 2
fi
nohup env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
  HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1 \
  /data/data/com.termux/files/usr/bin/adb -L tcp:5038 server nodaemon \
  >"$LOG" 2>&1 &
pid=$!
printf '%s\n' "$pid" >"$PIDFILE"
printf 'server_pid=%s\nlistener=tcp:5038\nlog=%s\n' "$pid" "$LOG"
