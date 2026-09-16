#!/usr/bin/env bash
set -euo pipefail
KIT="$(cd "$(dirname "$0")/.." && pwd)"
J="$KIT/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py"
NEW="$KIT/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-04-requalification-01"
OLD="$KIT/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-7549e36/r7-qualification-01/r7-04"

echo '=== new fdfb1ce R7-04 (expect R7_PASS) ==='
new_out=$(python3 "$J" fbo-incomplete "$NEW/logcat-follow.txt" \
  --ring "$NEW/gatea-ring.txt" --summary "$NEW/gatea-summary.txt" \
  --x-alive 0 --exit-signal 0)
printf '%s\n' "$new_out"
case "$new_out" in
  'R7_PASS fbo-incomplete') ;;
  *) echo "UNEXPECTED_NEW $new_out"; exit 2;;
esac

echo '=== historical 7549e36 R7-04 (expect R7_FAIL halt_mismatch) ==='
set +e
old_out=$(python3 "$J" fbo-incomplete "$OLD/logcat-follow.txt" \
  --ring "$OLD/gatea-ring.txt" --summary "$OLD/gatea-summary.txt" \
  --x-alive 0 --exit-signal 0)
old_rc=$?
set -e
printf '%s\n' "$old_out"
if [ "$old_rc" -eq 0 ]; then
  echo 'UNEXPECTED_HISTORICAL_PASS'
  exit 2
fi
case "$old_out" in
  'R7_FAIL halt_mismatch what=x-direct-not-success reason=4') ;;
  *) echo "UNEXPECTED_OLD $old_out"; exit 2;;
esac

echo '=== test-judge-r7.py ==='
python3 "$KIT/evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py"

echo 'HANDOFF_KIT_REJUDGE=PASS'
