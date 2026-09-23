#!/usr/bin/env bash
# Launch experimental f8-x11gpu :3 -noreset OUTSIDE the PRoot tracer.
#
# WHY (RCA-XFCE-2, 2026-09-23): every process started from inside this PRoot - including
# X3 when started by start-x3-noreset.py - is ptrace-traced by the single proot tracer
# (TracerPid != 0; the product logs "Tracer detected"). Under an XFCE load the traced X3
# answered a bare GetInputFocus in 15-18 ms median (0.25 ms idle) even with every EXA
# op on the CPU. Stable :1 is NOT traced (TracerPid 0): its shell forked termux-x11 and
# then exec'd proot, so proot never attached to it. Production therefore runs an
# untraced X; this launcher reproduces that topology.
#
# HOW: Termux's own app_process `am` (usr/bin/am, runs as the Termux uid) starts the
# app's internal TermuxService with ACTION com.termux.service_execute. The command then
# runs as a child of the Termux app process, outside the proot tree. Verified:
# TracerPid 0 (p2-xfce-probe/probe-03). Semantics of the X server are unchanged: the
# product's tracer check only decides whether X's own children get libtermux-exec in
# LD_PRELOAD (cmdentrypoint.cpp:458-460).
#
#   X3_LAUNCH_LOG   file for X3 stdout/stderr (must be under /data/data/com.termux/files/usr,
#                   which both sides see at the same path)
#   Every TERMUX_X11_* variable in the caller's environment is passed through verbatim.
#   Stable :1 is never touched.
set -euo pipefail
LOG=${X3_LAUNCH_LOG:?X3_LAUNCH_LOG}
case "$LOG" in /data/data/com.termux/files/usr/*) ;; *) echo "LAUNCH_REFUSE log_path_not_shared $LOG"; exit 3;; esac
# '|| true': with NO TERMUX_X11_* variable (B.3 mode S) grep exits 1 and, under pipefail,
# set -e ended this script silently (b3-s-01 BLOCKED untraced_launch_failed, 2026-09-23).
VARS=$(env | grep -E '^TERMUX_X11_[A-Z0-9_]+=[A-Za-z0-9_.:-]*$' | sort | tr '\n' ' ' || true)
# values must be plain tokens: the command travels through --esa, where ',' splits
if env | grep -E '^TERMUX_X11_' | grep -qv -E '^TERMUX_X11_[A-Z0-9_]+=[A-Za-z0-9_.:-]*$'; then
  echo "LAUNCH_REFUSE env_value_not_plain"; exit 3
fi
CMD="unset BASH_ENV ENV; exec env ${VARS}DISPLAY=:3 /data/data/com.termux/files/usr/bin/f8-x11gpu :3 -noreset >> $LOG 2>&1 < /dev/null"
case "$CMD" in *,*) echo "LAUNCH_REFUSE comma_in_command"; exit 3;; esac
echo "launch_cmd=$CMD"
/data/data/com.termux/files/usr/bin/am startservice --user 0 -n com.termux/com.termux.app.TermuxService \
  -a com.termux.service_execute -d com.termux.file:/data/data/com.termux/files/usr/bin/bash \
  --esa com.termux.execute.arguments "-c,$CMD" --ez com.termux.execute.background true
