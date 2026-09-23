#!/usr/bin/env bash
# XFCE-FREEZE-V3 series driver: frozen order, judge after every capture, stop on the
# first consumed non-VALID (plan §19). Not-consumed outcomes (runner exit 3 BLOCKED,
# exit 4 X3_STARTUP_CRASH) get ONE retry of the same variant (triage protocol).
set -uo pipefail
HERE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-xfce-runtime
XF=/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests/xfce3
RT=$HERE/runtime-bfb5769; mkdir -p "$RT"
# every analysis runs capped, never below the memory floor (INCIDENT-20260923)
SAFE=/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm/tests/common/safe-run.sh
: "${SERIAL:?}"
ORDER=(C1 C0 C1 C0 C1 C0)
declare -A N=([C1]=0 [C0]=0)
for v in "${ORDER[@]}"; do
  tries=0
  while :; do
    N[$v]=$((N[$v] + 1)); n=$(printf %02d "${N[$v]}")
    ev=$RT/xfce3-${v,,}-$n
    while [ -e "$ev" ]; do       # never reuse a directory (earlier attempts stay frozen)
      N[$v]=$((N[$v] + 1)); n=$(printf %02d "${N[$v]}"); ev=$RT/xfce3-${v,,}-$n
    done
    "$SAFE" --disk-min-gb 15 --disk-path "$RT" --check-only || { echo "STOP host_resources"; exit 1; }
    echo "START $v $ev $(date +%T)"
    VARIANT=$v SERIAL=$SERIAL EVIDENCE=$ev "$HERE/run-xfce-v3.sh" > "$ev.runner.log" 2>&1
    rc=$?
    echo "CAPTURE rc=$rc $(tail -1 "$ev.runner.log")"
    if [ $rc -eq 3 ] || [ $rc -eq 4 ]; then
      tries=$((tries + 1))
      [ $tries -le 1 ] && continue
      echo "STOP not_consumed_twice $v"; exit 1
    fi
    [ $rc -eq 0 ] || { echo "STOP runner_rc=$rc"; exit 1; }
    (cd "$ev" && find . -type f ! -name sha256sums.txt | sort | xargs sha256sum > sha256sums.txt)
    "$SAFE" -- python3 "$XF/xfce_collect.py" --evidence "$ev" --freeze "$XF/xfce-design-freeze.json" --out "$ev/xfce-run.json" \
      || { echo "STOP collect_failed_or_refused $ev"; exit 1; }
    "$SAFE" -- python3 "$XF/judge-xfce.py" --run "$ev/xfce-run.json" --freeze "$XF/xfce-design-freeze.json" --out "$ev/xfce-verdict.json"
    jrc=$?
    [ -s "$ev/xfce-verdict.json" ] || { echo "STOP judge_failed_or_refused jrc=$jrc $ev"; exit 1; }
    echo "VERDICT $v $n jrc=$jrc $(python3 -c "import json;d=json.load(open('$ev/xfce-verdict.json'));print(d['verdict'],d['failed'],d['findings'])")"
    [ $jrc -eq 0 ] || { echo "STOP verdict_not_valid $ev"; exit 1; }
    break
  done
done
echo "SERIES_DONE"
