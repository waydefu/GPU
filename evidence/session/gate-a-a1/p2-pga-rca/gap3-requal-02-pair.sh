#!/usr/bin/env bash
# PGA-GAP-3 requal-02 (design appendix A): fresh S run, then fresh C control, same cells. Detach.
set -uo pipefail
HERE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-pga-rca
: "${SERIAL:?}"
for m in S C; do
  ev=$HERE/runtime-83d45a9/gap3-requal-02-${m,,}
  [ -e "$ev" ] && { echo "SKIP_EXISTS $ev"; continue; }
  echo "START $m $(date +%T)"
  GAP3_MODE=$m SERIAL=$SERIAL EVIDENCE=$ev "$HERE/run-gap3-requal.sh" > "$ev.runner.log" 2>&1
  rc=$?
  echo "CAPTURE $m rc=$rc $(tail -1 "$ev.runner.log")"
  [ $rc -eq 0 ] || { echo "STOP $m rc=$rc"; exit 1; }
done
echo GAP3_PAIR_DONE
