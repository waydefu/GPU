#!/usr/bin/env bash
# Host-only input + HUP-containment mock tests for run-r7-10-8545b26.sh.
# VALIDATE_ONLY=1 and classifier mocks only. No ADB, no mkdir of
# runtime-8545b26/r7-10, no X3, no install.
set -euo pipefail

RUNTIME=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime
RUNNER="$RUNTIME/run-r7-10-8545b26.sh"
GENERIC="$RUNTIME/run-r7-one-cell-a07d66c.sh"
CLASSIFY="$RUNTIME/scripts/classify_r7_10_hup_containment.py"
JUDGE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py
LEGAL="$RUNTIME/runtime-8545b26/r7-10"
HIST="$RUNTIME/runtime-a07d66c/r7-10"
PASS=0
FAIL=0
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

expect_refuse() {
  local name=$1
  shift
  local out rc
  set +e
  out=$("$@" 2>&1)
  rc=$?
  set -e
  if [ "$rc" -eq 9 ] && echo "$out" | grep -q '^REFUSE'; then
    echo "PASS $name rc=$rc"
    PASS=$((PASS + 1))
    return 0
  fi
  echo "FAIL $name expected REFUSE/exit 9 got rc=$rc"
  echo "$out" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
}

expect_accept() {
  local name=$1
  shift
  local out rc
  set +e
  out=$("$@" 2>&1)
  rc=$?
  set -e
  if [ "$rc" -eq 0 ] && echo "$out" | grep -q 'VALIDATE_ONLY_OK' && echo "$out" | grep -q 'status=ACCEPT'; then
    echo "PASS $name rc=$rc"
    PASS=$((PASS + 1))
    return 0
  fi
  echo "FAIL $name expected ACCEPT/exit 0 got rc=$rc"
  echo "$out" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
}

base=(env -u SERIAL -u ADB_TRACE VALIDATE_ONLY=1 WAIT_S=12)
good_root="$TMP/runtime-8545b26"
mkdir -p "$good_root"

echo "== correct tuple =="
expect_accept valid-r7-10 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct \
  bash "$RUNNER"
if [ -e "$good_root/r7-10" ]; then
  echo "FAIL valid-r7-10-no-mkdir destination was created"
  FAIL=$((FAIL + 1))
else
  echo "PASS valid-r7-10-no-mkdir"
  PASS=$((PASS + 1))
fi
plan=$("${base[@]}" ROOT="$good_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct bash "$RUNNER")
if echo "$plan" | grep -q 'expect_sha=8545b26b308aa60b05685f48560285350e22ee8d' \
  && echo "$plan" | grep -q 'expect_version=1.03.01-8545b26-17.09.26' \
  && echo "$plan" | grep -q 'expect_package=com.waydefu.x11gpu' \
  && echo "$plan" | grep -q 'expect_build_id=50a4078b940d982e1ca1484cac6dd2bf2abe7b0a' \
  && echo "$plan" | grep -q 'timeout_ms=2000' \
  && echo "$plan" | grep -q 'retry=0' \
  && echo "$plan" | grep -q 'auto_next=0' \
  && echo "$plan" | grep -q 'adb=0' \
  && echo "$plan" | grep -q 'mkdir=0' \
  && echo "$plan" | grep -q 'activity_launch=0' \
  && echo "$plan" | grep -q 'x3_launch=0' \
  && echo "$plan" | grep -q 'holder_exec=0' \
  && echo "$plan" | grep -q 'fixture_exec=0' \
  && echo "$plan" | grep -q 'r7_10_trigger=0' \
  && echo "$plan" | grep -q 'stable_policy=read-only' \
  && echo "$plan" | grep -q 'install_policy=this runner never installs'; then
  echo "PASS valid-r7-10-plan-bind"
  PASS=$((PASS + 1))
else
  echo "FAIL valid-r7-10-plan-bind"
  echo "$plan" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi
if [ -e "$LEGAL" ]; then
  echo "FAIL legal-runtime-r7-10-still-absent path exists $LEGAL"
  FAIL=$((FAIL + 1))
else
  echo "PASS legal-runtime-r7-10-still-absent"
  PASS=$((PASS + 1))
fi
if [ -d "$HIST" ] && grep -q 'x-direct-not-success reason=4' "$HIST/judge.txt"; then
  echo "PASS historical-r7-10-intact"
  PASS=$((PASS + 1))
else
  echo "FAIL historical-r7-10-intact"
  FAIL=$((FAIL + 1))
fi

echo "== old root a07d66c =="
old_root="$TMP/runtime-a07d66c"
mkdir -p "$old_root"
expect_refuse wrong-root-a07d66c \
  "${base[@]}" ROOT="$old_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong root fdfb1ce =="
bad_root="$TMP/runtime-fdfb1ce"
mkdir -p "$bad_root"
expect_refuse wrong-root-fdfb1ce \
  "${base[@]}" ROOT="$bad_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong root 7549e36 =="
bad_root2="$TMP/runtime-7549e36"
mkdir -p "$bad_root2"
expect_refuse wrong-root-7549e36 \
  "${base[@]}" ROOT="$bad_root2" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong cell r7-11 =="
expect_refuse wrong-cell-r7-11 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong cell r7-01 =="
expect_refuse wrong-cell-r7-01 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-01 FAULT=src-ready-miss FIXTURE=direct \
  bash "$RUNNER"

echo "== future cell r7-p1 =="
expect_refuse wrong-cell-r7-p1 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"

echo "== wrong fault =="
expect_refuse wrong-fault \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-10 FAULT=post-draw-gl FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong fixture =="
expect_refuse wrong-fixture \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=present \
  bash "$RUNNER"

echo "== wrong wait =="
expect_refuse wrong-wait \
  env -u SERIAL VALIDATE_ONLY=1 WAIT_S=30 ROOT="$good_root" CELL_ID=r7-10 \
  FAULT=renderer-exit-after-consume FIXTURE=direct bash "$RUNNER"

echo "== VALIDATE_ONLY existing destination does not write =="
exist_root="$TMP/exist-vo/runtime-8545b26"
mkdir -p "$exist_root/r7-10"
echo frozen > "$exist_root/r7-10/keep.txt"
before=$(find "$exist_root/r7-10" | wc -l)
expect_accept validate-only-existing-dest \
  "${base[@]}" ROOT="$exist_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct \
  bash "$RUNNER"
after=$(find "$exist_root/r7-10" | wc -l)
if [ "$before" -eq "$after" ] && [ -f "$exist_root/r7-10/keep.txt" ]; then
  echo "PASS validate-only-existing-dest-no-write"
  PASS=$((PASS + 1))
else
  echo "FAIL validate-only-existing-dest-no-write wrote into cell"
  FAIL=$((FAIL + 1))
fi

echo "== live existing destination =="
exist_live="$TMP/exist-live/runtime-8545b26"
mkdir -p "$exist_live/r7-10"
echo frozen > "$exist_live/r7-10/keep.txt"
before=$(find "$exist_live/r7-10" | wc -l)
expect_refuse existing-destination-live \
  env -u VALIDATE_ONLY SERIAL=dummy WAIT_S=12 ROOT="$exist_live" CELL_ID=r7-10 \
  FAULT=renderer-exit-after-consume FIXTURE=direct bash "$RUNNER"
after=$(find "$exist_live/r7-10" | wc -l)
if [ "$before" -eq "$after" ] && [ -f "$exist_live/r7-10/keep.txt" ]; then
  echo "PASS existing-destination-live-no-write"
  PASS=$((PASS + 1))
else
  echo "FAIL existing-destination-live-no-write wrote into cell"
  FAIL=$((FAIL + 1))
fi

echo "== extra selector args =="
expect_refuse extra-args \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct \
  bash "$RUNNER" r7-11

echo "== missing SERIAL live =="
expect_refuse missing-serial-live \
  env -u SERIAL -u VALIDATE_ONLY WAIT_S=12 ROOT="$good_root" CELL_ID=r7-10 \
  FAULT=renderer-exit-after-consume FIXTURE=direct bash "$RUNNER"

echo "== expected x-hup/6 mock =="
mkdir -p "$TMP/expected"
cat > "$TMP/expected/follow.txt" <<'EOF'
I gatea-telemetry: GATEA_EVENT seq=0 role=1 event=6 generation=1 serial=5 src=1 dst=2
I gatea-telemetry: GATEA_EVENT seq=1 role=2 event=7 generation=1 serial=5 src=1 dst=2
I gatea-telemetry: GATEA_EVENT seq=2 role=2 event=35 generation=1 serial=5 src=10 dst=2
F gatea-a1: GATEA_FATAL_HALT what=x-hup reason=6
I gatea-a1: GATEA_SUMMARY where=x-hup nonce=1 generation=1 nextSequence=3 overflow=0 firstFailed=0 generationFatal=6 fatalReason=6
EOF
set +e
cout=$(python3 "$CLASSIFY" --mode r7-10-cell --follow "$TMP/expected/follow.txt" \
  --env-captured 1 --env-exact 1 --out "$TMP/expected/classify.txt")
crc=$?
jout=$(python3 "$JUDGE" renderer-exit-after-consume "$TMP/expected/follow.txt" --x-alive 0 --exit-signal 0)
jrc=$?
set -e
if [ "$crc" -eq 0 ] \
  && grep -q '^classification=EXPECTED_HUP' "$TMP/expected/classify.txt" \
  && grep -q '^continue_judge=YES' "$TMP/expected/classify.txt" \
  && grep -q '^product_fail=NO' "$TMP/expected/classify.txt" \
  && grep -q '^x_hup_reason6=1' "$TMP/expected/classify.txt" \
  && grep -q '^x_direct_not_success_reason4=0' "$TMP/expected/classify.txt" \
  && [ "$jrc" -eq 0 ] && echo "$jout" | grep -q '^R7_PASS renderer-exit-after-consume'; then
  echo "PASS expected-hup-continue-judge"
  PASS=$((PASS + 1))
else
  echo "FAIL expected-hup-continue-judge crc=$crc jrc=$jrc"
  echo "$cout" | sed 's/^/  /'
  echo "$jout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== historical reason4 regression =="
mkdir -p "$TMP/bug"
cat > "$TMP/bug/follow.txt" <<'EOF'
I gatea-telemetry: GATEA_EVENT seq=0 role=1 event=6 generation=1 serial=5 src=1 dst=2
I gatea-telemetry: GATEA_EVENT seq=1 role=2 event=7 generation=1 serial=5 src=1 dst=2
I gatea-telemetry: GATEA_EVENT seq=2 role=2 event=35 generation=1 serial=5 src=10 dst=2
F gatea-a1: GATEA_FATAL_HALT what=x-direct-not-success reason=4
I gatea-a1: GATEA_SUMMARY where=x-direct-not-success nonce=1 generation=1
EOF
set +e
cout=$(python3 "$CLASSIFY" --mode r7-10-cell --follow "$TMP/bug/follow.txt" \
  --env-captured 1 --env-exact 1 --out "$TMP/bug/classify.txt")
crc=$?
jout=$(python3 "$JUDGE" renderer-exit-after-consume "$TMP/bug/follow.txt" --x-alive 0 --exit-signal 0)
jrc=$?
set -e
if [ "$crc" -eq 2 ] \
  && grep -q '^classification=HISTORICAL_REASON4' "$TMP/bug/classify.txt" \
  && grep -q '^product_fail=YES' "$TMP/bug/classify.txt" \
  && grep -q '^continue_judge=YES' "$TMP/bug/classify.txt" \
  && [ "$jrc" -ne 0 ] && echo "$jout" | grep -q 'halt_mismatch'; then
  echo "PASS historical-reason4-product-fail"
  PASS=$((PASS + 1))
else
  echo "FAIL historical-reason4-product-fail crc=$crc jrc=$jrc"
  echo "$cout" | sed 's/^/  /'
  echo "$jout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== published fatal then later HUP overwrite =="
mkdir -p "$TMP/overwrite"
cat > "$TMP/overwrite/follow.txt" <<'EOF'
F gatea-a1: GATEA_FATAL_HALT what=r-test-fatal-pre-fence reason=6
F gatea-a1: GATEA_FATAL_HALT what=x-hup reason=6
EOF
set +e
cout=$(python3 "$CLASSIFY" --mode hup-precedence --follow "$TMP/overwrite/follow.txt" \
  --out "$TMP/overwrite/classify.txt")
crc=$?
set -e
if [ "$crc" -eq 2 ] \
  && grep -q '^classification=HUP_PRECEDENCE_OVERWRITE' "$TMP/overwrite/classify.txt" \
  && grep -q '^product_fail=YES' "$TMP/overwrite/classify.txt"; then
  echo "PASS hup-precedence-overwrite"
  PASS=$((PASS + 1))
else
  echo "FAIL hup-precedence-overwrite crc=$crc"
  echo "$cout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== published fatal preserved across later HUP diagnostic =="
mkdir -p "$TMP/preserve"
cat > "$TMP/preserve/follow.txt" <<'EOF'
F gatea-a1: GATEA_FATAL_HALT what=r-test-fatal-pre-fence reason=6
I gatea-a1: GATEA_HUP_PRESERVE published=6 peer=dead
EOF
set +e
cout=$(python3 "$CLASSIFY" --mode hup-precedence --follow "$TMP/preserve/follow.txt" \
  --out "$TMP/preserve/classify.txt")
crc=$?
set -e
if [ "$crc" -eq 0 ] \
  && grep -q '^classification=HUP_PRECEDENCE_PRESERVE' "$TMP/preserve/classify.txt" \
  && grep -q '^product_fail=NO' "$TMP/preserve/classify.txt" \
  && grep -q '^first_halt=r-test-fatal-pre-fence/6' "$TMP/preserve/classify.txt" \
  && grep -q '^last_halt=r-test-fatal-pre-fence/6' "$TMP/preserve/classify.txt"; then
  echo "PASS hup-precedence-preserve"
  PASS=$((PASS + 1))
else
  echo "FAIL hup-precedence-preserve crc=$crc"
  echo "$cout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== genuine live-peer timeout remains valid architecture =="
mkdir -p "$TMP/timeout"
cat > "$TMP/timeout/follow.txt" <<'EOF'
I gatea-telemetry: GATEA_EVENT seq=0 role=1 event=6 generation=1 serial=5 src=1 dst=2
F gatea-a1: GATEA_FATAL_HALT what=x-direct-not-success reason=4
I gatea-a1: GATEA_SUMMARY where=x-direct-not-success nonce=1 generation=1
EOF
set +e
cout=$(python3 "$CLASSIFY" --mode timeout-architecture --follow "$TMP/timeout/follow.txt" \
  --out "$TMP/timeout/classify.txt")
crc=$?
set -e
if [ "$crc" -eq 0 ] \
  && grep -q '^classification=GENUINE_TIMEOUT_NOT_R7_10' "$TMP/timeout/classify.txt" \
  && grep -q '^product_fail=NO' "$TMP/timeout/classify.txt" \
  && grep -q '^reason4_globally_forbidden=NO' "$TMP/timeout/classify.txt" \
  && grep -q '^r7_10_construction=NO' "$TMP/timeout/classify.txt"; then
  echo "PASS genuine-timeout-not-globally-forbidden"
  PASS=$((PASS + 1))
else
  echo "FAIL genuine-timeout-not-globally-forbidden crc=$crc"
  echo "$cout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== generic a07d66c runner still bound to a07d66c =="
gplan=$(env -u SERIAL VALIDATE_ONLY=1 WAIT_S=12 ROOT="$old_root" \
  CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct bash "$GENERIC")
if echo "$gplan" | grep -q 'candidate_head=a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82' \
  && echo "$gplan" | grep -q 'expect_version=1.03.01-a07d66c-17.09.26' \
  && echo "$gplan" | grep -q 'live_status=ENABLED'; then
  echo "PASS generic-still-a07d66c-bound"
  PASS=$((PASS + 1))
else
  echo "FAIL generic-still-a07d66c-bound"
  echo "$gplan" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

if [ -e "$LEGAL" ]; then
  echo "FAIL legal-runtime-r7-10-absent-after path exists $LEGAL"
  FAIL=$((FAIL + 1))
else
  echo "PASS legal-runtime-r7-10-absent-after"
  PASS=$((PASS + 1))
fi

echo
echo "INPUT_ORACLE_PASS=$PASS FAIL=$FAIL"
if [ "$FAIL" -ne 0 ]; then
  exit 2
fi
exit 0
