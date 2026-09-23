#!/usr/bin/env bash
# Device queue 3: the rest of V2-B3 after queue 2 stopped at b3-s-01 BLOCKED (launcher bug, fixed).
# under the frozen GPU configuration it can only repeat INVALID until PGA-GAP-2 is resolved
# (planning-v2/xfce-baseline/RCA-XFCE-3.md). Runs, in order, and STOPS at the first thing
# that is not a clean capture:
#   1. V2-QUAL-ORACLE-DIRECT   one run, judged immediately (capped analysis)
#   2. V2-B3                   ATTR, G, C, S, G2 (captured; analysis afterwards, offline)
#
#   SERIAL=<live 5038 serial> ./run-device-queue-2.sh      (detach: setsid nohup ... &)
# Needs: screen on and unlocked, nobody using the phone. Stable :1 is never touched.
set -uo pipefail
: "${SERIAL:?}"
G=/root/projects/GPU加速/evidence/session/gate-a-a1
T=/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests
SAFE=$T/common/safe-run.sh
LOG=$G/device-queue-3.log
say() { echo "$(date +%T) $*" | tee -a "$LOG"; }

say "QUEUE3_START serial=$SERIAL"
"$SAFE" --disk-min-gb 20 --disk-path "$G" --check-only 2>&1 | tee -a "$LOG"
[ "${PIPESTATUS[0]}" -eq 0 ] || { say "QUEUE3_STOP host_resources"; exit 1; }

for mn in S:02 G2:01; do
  m=${mn%:*}; n=${mn#*:}
  say "STEP b3 $m ($n)"
  EV=$G/p2-b3-runtime/runtime-bfb5769/b3-${m,,}-$n
  mkdir -p "$(dirname "$EV")"
  (cd "$G/p2-b3-runtime" && MODE=$m SERIAL=$SERIAL EVIDENCE=$EV ./run-b3.sh > "$EV.runner.log" 2>&1)
  rc=$?
  tail -1 "$EV.runner.log" | tee -a "$LOG"
  [ $rc -eq 0 ] || { say "QUEUE3_STOP b3_$m rc=$rc"; exit 1; }
done
say "QUEUE3_DONE"
