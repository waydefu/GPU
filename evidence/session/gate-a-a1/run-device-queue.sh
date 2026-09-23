#!/usr/bin/env bash
# Device queue after RCA-XFCE-2 (product bfb5769). Runs, in order, every device packet that
# is frozen and waiting, and STOPS at the first thing that is not a clean capture.
#
#   SERIAL=<live 5038 serial> ./run-device-queue.sh        (detach it: setsid nohup ... &)
#
#   1. XFCE-FREEZE-V3 series  C1 C0 C1 C0 C1 C0 (series-v3.sh stops on the first non-VALID)
#   2. V2-QUAL-ORACLE-DIRECT   one run, judged immediately
#   3. V2-B3                   ATTR, G, C, S, G2 (captured; analysis afterwards, offline)
#
# Needs: screen on and unlocked for the whole queue (~1.5 h), nobody using the phone - every
# packet brings the experimental Activity to the foreground. Stable :1 is never touched.
# Progress: ./device-queue.log (one line per step).
set -uo pipefail
: "${SERIAL:?}"
G=/root/projects/GPU加速/evidence/session/gate-a-a1
T=/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests
LOG=$G/device-queue.log
say() { echo "$(date +%T) $*" | tee -a "$LOG"; }

say "QUEUE_START serial=$SERIAL"
say "STEP xfce-v3-series"
(cd "$G/p2-xfce-runtime" && SERIAL=$SERIAL ./series-v3.sh > series-v3.log 2>&1)
tail -1 "$G/p2-xfce-runtime/series-v3.log" | tee -a "$LOG"
grep -q '^SERIES_DONE' "$G/p2-xfce-runtime/series-v3.log" || { say "QUEUE_STOP xfce_series_not_done"; exit 1; }

say "STEP oracle"
EV=$G/p2-oracle-runtime/runtime-bfb5769/oracle-01
mkdir -p "$(dirname "$EV")"
(cd "$G/p2-oracle-runtime" && SERIAL=$SERIAL EVIDENCE=$EV ./run-oracle.sh > "$EV.runner.log" 2>&1)
tail -1 "$EV.runner.log" | tee -a "$LOG"
python3 "$T/oracle/judge-oracle.py" --evidence "$EV" --freeze "$T/oracle/oracle-freeze.json" \
  --out "$EV/oracle-verdict.json" | tee -a "$LOG"

for m in ATTR G C S G2; do
  say "STEP b3 $m"
  EV=$G/p2-b3-runtime/runtime-bfb5769/b3-${m,,}-01
  mkdir -p "$(dirname "$EV")"
  (cd "$G/p2-b3-runtime" && MODE=$m SERIAL=$SERIAL EVIDENCE=$EV ./run-b3.sh > "$EV.runner.log" 2>&1)
  rc=$?
  tail -1 "$EV.runner.log" | tee -a "$LOG"
  [ $rc -eq 0 ] || { say "QUEUE_STOP b3_$m rc=$rc"; exit 1; }
done
say "QUEUE_DONE"
