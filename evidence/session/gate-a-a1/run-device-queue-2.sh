#!/usr/bin/env bash
# Device queue after RCA-XFCE-3 (product bfb5769). The XFCE-FREEZE-V3 series is NOT in it:
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
LOG=$G/device-queue-2.log
say() { echo "$(date +%T) $*" | tee -a "$LOG"; }

say "QUEUE2_START serial=$SERIAL"
"$SAFE" --disk-min-gb 20 --disk-path "$G" --check-only 2>&1 | tee -a "$LOG"
[ "${PIPESTATUS[0]}" -eq 0 ] || { say "QUEUE2_STOP host_resources"; exit 1; }

say "STEP oracle"
EV=$G/p2-oracle-runtime/runtime-bfb5769/oracle-01
mkdir -p "$(dirname "$EV")"
(cd "$G/p2-oracle-runtime" && SERIAL=$SERIAL EVIDENCE=$EV ./run-oracle.sh > "$EV.runner.log" 2>&1)
rc=$?
tail -1 "$EV.runner.log" | tee -a "$LOG"
[ $rc -eq 0 ] || { say "QUEUE2_STOP oracle rc=$rc"; exit 1; }
"$SAFE" -- python3 "$T/oracle/judge-oracle.py" --evidence "$EV" --freeze "$T/oracle/oracle-freeze.json" \
  --out "$EV/oracle-verdict.json" 2>&1 | tee -a "$LOG"

for m in ATTR G C S G2; do
  say "STEP b3 $m"
  EV=$G/p2-b3-runtime/runtime-bfb5769/b3-${m,,}-01
  mkdir -p "$(dirname "$EV")"
  (cd "$G/p2-b3-runtime" && MODE=$m SERIAL=$SERIAL EVIDENCE=$EV ./run-b3.sh > "$EV.runner.log" 2>&1)
  rc=$?
  tail -1 "$EV.runner.log" | tee -a "$LOG"
  [ $rc -eq 0 ] || { say "QUEUE2_STOP b3_$m rc=$rc"; exit 1; }
done
say "QUEUE2_DONE"
