#!/usr/bin/env bash
# Stage 7.6 matrix rerun (PRoot side): modes in order, each fully prepared/judged; stop at first abort.
# Usage: stage76_matrix_chain.sh PARENT_DIR MODE...   (mode 4 gets the 600 s soak, as in 7.5)
set -euo pipefail
src=$(cd "$(dirname "$0")" && pwd)
parent=$1; shift
for mode in "$@"; do
  run=$("$src/stage75_prepare.sh" "$mode" "$parent")
  echo "mode=$mode run=$run fixture_l2s=$(cat "$run/fixture-l2s-links")"
  /usr/local/bin/termux-bg-run --timeout 900 --tail 5 "$run/run-native" > "$run/native-launcher.log" 2>&1
  tail -3 "$run/native-suite.log"
  python3 -B "$run/scripts/stage75_envelope.py" "$run/ws2" /usr/bin/git "$run/r" > "$run/envelope-proot.json"
  soak=0; [ "$mode" = 4 ] && soak=600
  python3 -B "$run/scripts/stage75_matrix.py" --run "$run" --mode "$mode" --soak "$soak" > "$run/matrix.out" 2>&1 || {
    echo "mode=$mode matrix aborted"; tail -5 "$run/matrix.out"; exit 1; }
  python3 -B "$run/scripts/stage75_judge.py" "$run" "$mode" "$run/envelope-native.json" "$run/envelope-proot.json" > "$run/judge.json"
  python3 -c "import json,sys; j=json.load(open(sys.argv[1])); print('mode', j['mode'], j['verdict'], {k: j[k] for k in ('G1','G2','G3','G4','G5')}, j['measured_peak'])" "$run/judge.json"
done
