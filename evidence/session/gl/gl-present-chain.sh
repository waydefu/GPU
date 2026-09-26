#!/usr/bin/env bash
# GL-PRESENT-01 judged cells: main-01, main-02, xdbg-01 (GL-PRESENT-01-FREEZE.md §4), derived from
# electron-bench-chain.sh. Each cell waits for MemAvailable >= 4600 MB for 20 s (max 600 s), waits up to 30 s
# for any previous X3 to be gone (recording what still matched), and the chain stops at the first cell that is
# not CMD_CAPTURED. xdbg-01 adds TERMUX_X11_DEBUG=2 to X3 (server-side DRI3 import log; not a CPU cell).
#   SERIAL=<live 5038 serial> EXPECT_ROOT=<WxH measured by dry-01> [GLP_DIR=gl-present-02] bash gl/gl-present-chain.sh
# GLP_DIR (default gl-present-01) was added for GL-PRESENT-02.
# GL-PRESENT-03: after every main cell, gl_present_cellcheck.py (segment validity + per-cell tool conditions);
# CELLCHECK_FAIL stops the chain at once instead of spending the remaining cells (user rule 2026-09-26).
cd /root/projects/GPU加速/evidence/session
SERIAL=${SERIAL:?SERIAL}
EXPECT_ROOT=${EXPECT_ROOT:?EXPECT_ROOT from dry-01 x-root.txt}
GLP_DIR=${GLP_DIR:-gl-present-01}
CELL_SCRIPT=/root/projects/GPU加速/src/f8-ahb-exa-async/tests/gl_present/gl_present_cell.sh
for cell in main-01 main-02 xdbg-01; do
  E=$PWD/gl/$GLP_DIR/$cell
  [ -e "$E" ] && { echo "CHAIN_STOP exists $E"; exit 3; }
  ok=0; t=0
  while [ $ok -lt 20 ] && [ $t -lt 600 ]; do a=$(awk '/^MemAvailable:/{print int($2/1024)}' /proc/meminfo); if [ "$a" -ge 4600 ]; then ok=$((ok+1)); else ok=0; fi; sleep 1; t=$((t+1)); done
  [ $ok -lt 20 ] && { echo "CHAIN_STOP mem_wait_timeout $cell avail=$a"; exit 3; }
  for i in $(seq 1 30); do m=$(pgrep -af 'termux-x11gpu com.waydefu.x11gpu' | grep -v pgrep); [ -z "$m" ] && break; echo "pre_${cell}_x3_match t=$i $m"; sleep 1; done
  [ -n "$m" ] && { echo "CHAIN_STOP x3_present_before_$cell"; exit 2; }
  case "$cell" in
    main-*) SET=main; REP=${cell#main-}; DBG=();;
    xdbg-*) SET=xdbg; REP=${cell#xdbg-}; DBG=(TERMUX_X11_DEBUG=2);;
  esac
  echo "CELL_START $cell $(date +%T) avail=$a set=$SET"
  env "${DBG[@]}" REP=$REP SERIAL=$SERIAL GL_PRESENT_SET=$SET MODE=C KIND=cmd CMD_SCRIPT=$CELL_SCRIPT CMD_TIMEOUT=1500 \
    EXPECT_ROOT=$EXPECT_ROOT EXPECT_VERSION=1.03.01-f592241-24.09.26 \
    EXPECT_APK_SHA256=f9e35b6907df36fc4f4d5a0440147c3e9b746356776beb3217431b48fa01075c \
    EVIDENCE=$E bash gl/run-gl-bench.sh > $E.runner.log 2>&1 < /dev/null
  tail -1 $E.runner.log
  grep -q '^CMD_CAPTURED' $E.runner.log || { echo "CHAIN_STOP $cell not captured"; exit 2; }
  if [ "$SET" = main ]; then
    python3 /root/projects/GPU加速/src/f8-ahb-exa-async/tests/gl_present/gl_present_cellcheck.py "$E" > $E.cellcheck.txt 2>&1
    cat $E.cellcheck.txt
    grep -q '^CELLCHECK_OK' $E.cellcheck.txt || { echo "CHAIN_STOP $cell cellcheck"; exit 2; }
  fi
  echo "CELL_DONE $cell $(date +%T)"
done
echo CHAIN_DONE
