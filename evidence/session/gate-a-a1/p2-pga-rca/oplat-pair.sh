#!/usr/bin/env bash
# OPLAT pair (RCA-XFCE-3 / PGA-GAP-2 step 1; N=02 is the appendix-A.3 replication): MODE G then MODE C, each once, no retry of a
# consumed capture. Detach it (setsid nohup); progress in oplat-pair.log.
set -uo pipefail
HERE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-pga-rca
: "${SERIAL:?}"
mkdir -p "$HERE/runtime-bfb5769"
for m in G C; do
  ev=$HERE/runtime-bfb5769/oplat-${m,,}-${N:-01}
  [ -e "$ev" ] && { echo "SKIP_EXISTS $ev"; continue; }
  echo "START $m $(date +%T)"
  MODE=$m SERIAL=$SERIAL EVIDENCE=$ev "$HERE/run-oplat.sh" > "$ev.runner.log" 2>&1
  rc=$?
  echo "CAPTURE $m rc=$rc $(tail -1 "$ev.runner.log")"
  [ $rc -eq 0 ] || { echo "STOP $m rc=$rc"; exit 1; }
done
echo OPLAT_PAIR_DONE
