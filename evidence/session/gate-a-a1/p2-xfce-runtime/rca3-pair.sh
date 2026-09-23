#!/usr/bin/env bash
# RCA pair for the xfce3-c1-01 failure (untraced X3 via the V3 runner) (NOT baseline runs, never pooled with them).
# Same frozen V2 workload (variant C1), two arms, each with tests/pga/rca_sampler.py:
#   G  exactly as frozen (PROTO=1, EXA GPU on)
#   C  TERMUX_X11_DISABLE_EXA_GPU=1 (every EXA op on the CPU) - the control
# The runner itself is unchanged; the extra variable reaches X by inheritance and is
# recorded in env-x3.txt.
set -uo pipefail
HERE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-xfce-runtime
PGA=/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests/pga
RTT=${RTT:?path to built x_rtt}
: "${SERIAL:?}"
for arm in ${ARMS:-G C}; do
  ev=$HERE/runtime-bfb5769/rca3-${arm,,}-01
  [ -e "$ev" ] && { echo "SKIP_EXISTS $ev"; continue; }
  python3 "$PGA/rca_sampler.py" --out "$ev.rca" --x-rtt "$RTT" --duration 900 > "$ev.rca.log" 2>&1 &
  SP=$!
  echo "START $arm $(date +%T)"
  if [ "$arm" = C ]; then export TERMUX_X11_DISABLE_EXA_GPU=1; else unset TERMUX_X11_DISABLE_EXA_GPU; fi
  VARIANT=C1 SERIAL=$SERIAL EVIDENCE=$ev "$HERE/run-xfce-v3.sh" > "$ev.runner.log" 2>&1
  rc=$?
  wait $SP
  echo "CAPTURE $arm rc=$rc $(tail -1 "$ev.runner.log")"
done
unset TERMUX_X11_DISABLE_EXA_GPU
echo RCA_PAIR_DONE
