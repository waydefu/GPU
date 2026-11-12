#!/usr/bin/env bash
set -u

RUNTIME="/root/projects/GPU加速/evidence/session/gate-a-a1/runtime"
LEDGER="$RUNTIME/command-ledger-20260912T113249Z.txt"

if [ "$#" -lt 2 ]; then
  printf 'usage: %s NAME COMMAND [ARG...]\n' "$0" >&2
  exit 2
fi

name="$1"
shift
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
raw="$RUNTIME/${name}-${stamp}.raw.txt"
status="$RUNTIME/${name}-${stamp}.status.txt"
cmd=""
for arg in "$@"; do
  printf -v quoted '%q' "$arg"
  cmd="${cmd}${cmd:+ }${quoted}"
done
start="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
"$@" >"$raw" 2>&1
rc=$?
end="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'start_utc=%s\nend_utc=%s\nexit_code=%s\ncommand=%s\nraw_output=%s\n' \
  "$start" "$end" "$rc" "$cmd" "$raw" >"$status"
printf '\n[%s]\nCOMMAND %s\nRAW_OUTPUT %s\nSTATUS_FILE %s\nEXIT_CODE %s\n' \
  "$start" "$cmd" "$raw" "$status" "$rc" >>"$LEDGER"
printf 'name=%s\nraw_output=%s\nstatus_file=%s\nexit_code=%s\n' \
  "$name" "$raw" "$status" "$rc"
exit "$rc"
