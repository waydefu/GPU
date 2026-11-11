#!/usr/bin/env bash
# PGA-GAP-2 async prototype XFCE comparison (planning-v2/pga/PGA-GAP-2-ASYNC-XFCE-FREEZE.md).
# One capture per ORDER entry (ARM-REP), variant VARIANT, product PRODUCT (default 11b3b79), each with rca_sampler.
# Arms: G, GA (+EXA_ASYNC), C (+DISABLE_EXA_GPU), GAT (GA + GPU_MIN_PIXELS=4097), GT (GPU_MIN_PIXELS=4097),
#       G0 (GPU_MIN_PIXELS=0: routing off, for f592241+ where 4097 is the default).
# Stops at the first capture that did not end XFCE_CAPTURED.
set -uo pipefail
HERE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-xfce-runtime
PGA=/root/projects/GPU加速/src/f8-ahb-exa-async/tests/pga
RTT=${RTT:?path to built x_rtt}
: "${SERIAL:?}" "${VARIANT:?C0 or C1}"
PRODUCT=${PRODUCT:-11b3b79}
RUNNER=$HERE/run-xfce-v3-$PRODUCT.sh
ORDER=${ORDER:-G-01 GA-01 C-01 C-02 GA-02 G-02}
mkdir -p "$HERE/runtime-$PRODUCT"
for item in $ORDER; do
  arm=${item%-*}; rep=${item#*-}
  ev=$HERE/runtime-$PRODUCT/xfce-${VARIANT,,}-${arm,,}-$rep
  [ -e "$ev" ] && { echo "SKIP_EXISTS $ev"; continue; }
  unset TERMUX_X11_EXA_ASYNC TERMUX_X11_DISABLE_EXA_GPU TERMUX_X11_GPU_MIN_PIXELS
  case "$arm" in GA) export TERMUX_X11_EXA_ASYNC=1;; GAT) export TERMUX_X11_EXA_ASYNC=1 TERMUX_X11_GPU_MIN_PIXELS=4097;;
    C) export TERMUX_X11_DISABLE_EXA_GPU=1;; G) ;;
    GT) export TERMUX_X11_GPU_MIN_PIXELS=4097;;          # f592241+: same as the default, stated explicitly
    G0) export TERMUX_X11_GPU_MIN_PIXELS=0;;             # f592241+: routing off = old behaviour
    *) echo "bad arm $arm"; exit 3;; esac
  python3 "$PGA/rca_sampler.py" --out "$ev.rca" --x-rtt "$RTT" --duration 900 > "$ev.rca.log" 2>&1 &
  SP=$!
  echo "START $item $(date +%T)"
  VARIANT=$VARIANT SERIAL=$SERIAL EVIDENCE=$ev "$RUNNER" > "$ev.runner.log" 2>&1
  rc=$?
  wait $SP
  echo "CAPTURE $item rc=$rc $(tail -1 "$ev.runner.log")"
  tail -1 "$ev.runner.log" | grep -q '^XFCE_CAPTURED' || { echo "SERIES_STOP at $item"; break; }
done
unset TERMUX_X11_EXA_ASYNC TERMUX_X11_DISABLE_EXA_GPU TERMUX_X11_GPU_MIN_PIXELS
echo XFCE_ASYNC_SERIES_DONE
