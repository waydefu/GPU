#!/usr/bin/env bash
# ELECTRON-BENCH-01 formal cells: rep 01 then rep 02 (ELECTRON-BENCH-01-FREEZE.md). Each rep waits for
# MemAvailable >= 4600 MB for 20 s (max 600 s); stops if a rep is not CMD_CAPTURED; before rep 02 waits up to
# 30 s for the rep-01 X3 to be gone and records whatever still matched (the gl-bench2 chain lacked this).
cd /root/projects/GPU加速/evidence/session
SERIAL=${SERIAL:?SERIAL}
for rep in 01 02; do
  E=$PWD/gl/electron-bench-01-rep$rep
  [ -e "$E" ] && { echo "CHAIN_STOP exists $E"; exit 3; }
  ok=0; t=0
  while [ $ok -lt 20 ] && [ $t -lt 600 ]; do a=$(awk '/^MemAvailable:/{print int($2/1024)}' /proc/meminfo); if [ "$a" -ge 4600 ]; then ok=$((ok+1)); else ok=0; fi; sleep 1; t=$((t+1)); done
  [ $ok -lt 20 ] && { echo "CHAIN_STOP mem_wait_timeout rep$rep avail=$a"; exit 3; }
  for i in $(seq 1 30); do m=$(pgrep -af 'termux-x11gpu com.waydefu.x11gpu' | grep -v pgrep); [ -z "$m" ] && break; echo "pre_rep${rep}_x3_match t=$i $m"; sleep 1; done
  [ -n "$m" ] && { echo "CHAIN_STOP x3_present_before_rep$rep"; exit 2; }
  echo "REP_START $rep $(date +%T) avail=$a"
  REP=$rep SERIAL=$SERIAL MODE=G KIND=cmd CMD_SCRIPT=/root/projects/GPU加速/src/f8-ahb-exa-async/tests/gl/electron_bench.sh CMD_TIMEOUT=1500 \
    EXPECT_ROOT=1200x2416 EXPECT_VERSION=1.03.01-f592241-24.09.26 \
    EXPECT_APK_SHA256=f9e35b6907df36fc4f4d5a0440147c3e9b746356776beb3217431b48fa01075c \
    EVIDENCE=$E bash gl/run-gl-bench.sh > $E.runner.log 2>&1 < /dev/null
  tail -1 $E.runner.log
  grep -q '^CMD_CAPTURED' $E.runner.log || { echo "CHAIN_STOP rep$rep not captured"; exit 2; }
  echo "REP_DONE $rep $(date +%T)"
done
echo CHAIN_DONE
