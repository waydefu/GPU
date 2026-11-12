#!/usr/bin/env bash
# Host-only input + serial-wrap mock tests for run-r7-11-a07d66c.sh.
# VALIDATE_ONLY=1 and classifier mocks only. No ADB, no mkdir of runtime-a07d66c/r7-11, no X3.
set -euo pipefail

RUNTIME=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime
RUNNER="$RUNTIME/run-r7-11-a07d66c.sh"
GENERIC="$RUNTIME/run-r7-one-cell-a07d66c.sh"
CLASSIFY="$RUNTIME/scripts/classify_r7_11_serial_wrap.py"
LEGAL="$RUNTIME/runtime-a07d66c/r7-11"
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
good_root="$TMP/runtime-a07d66c"
mkdir -p "$good_root"

echo "== correct tuple =="
expect_accept valid-r7-11 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct \
  bash "$RUNNER"
if [ -e "$good_root/r7-11" ]; then
  echo "FAIL valid-r7-11-no-mkdir destination was created"
  FAIL=$((FAIL + 1))
else
  echo "PASS valid-r7-11-no-mkdir"
  PASS=$((PASS + 1))
fi
plan=$("${base[@]}" ROOT="$good_root" CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct bash "$RUNNER")
if echo "$plan" | grep -q 'fixture_required=YES' \
  && echo "$plan" | grep -q 'no_serial0=YES' \
  && echo "$plan" | grep -q 'prior_publish_required=NO' \
  && echo "$plan" | grep -q 'seed_after_event35=YES' \
  && echo "$plan" | grep -q 'died_during_8s_without_fixture=INVALID' \
  && echo "$plan" | grep -q 'adb=0' \
  && echo "$plan" | grep -q 'mkdir=0' \
  && echo "$plan" | grep -q 'x3_launch=0'; then
  echo "PASS valid-r7-11-plan-serial-wrap"
  PASS=$((PASS + 1))
else
  echo "FAIL valid-r7-11-plan-serial-wrap"
  echo "$plan" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi
if [ -e "$LEGAL" ]; then
  echo "FAIL legal-runtime-r7-11-still-absent path exists $LEGAL"
  FAIL=$((FAIL + 1))
else
  echo "PASS legal-runtime-r7-11-still-absent"
  PASS=$((PASS + 1))
fi

echo "== wrong fault =="
expect_refuse wrong-fault \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-11 FAULT=wrong-generation-frame FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong fixture =="
expect_refuse wrong-fixture \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=present \
  bash "$RUNNER"

echo "== wrong cell r7-09 =="
expect_refuse wrong-cell-r7-09 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-09 FAULT=serial-wrap FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong cell r7-08 =="
expect_refuse wrong-cell-r7-08 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-08 FAULT=renderer-fatal-pre-fence FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong cell r7-10 =="
expect_refuse wrong-cell-r7-10 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong cell r7-p1 =="
expect_refuse wrong-cell-r7-p1 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"

echo "== wrong cell r7-p2 =="
expect_refuse wrong-cell-r7-p2 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-p2 FAULT=present-renderer-exit FIXTURE=present \
  bash "$RUNNER"

echo "== wrong root fdfb1ce =="
bad_root="$TMP/runtime-fdfb1ce"
mkdir -p "$bad_root"
expect_refuse wrong-root-fdfb1ce \
  "${base[@]}" ROOT="$bad_root" CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong root 7549e36 =="
bad_root2="$TMP/runtime-7549e36"
mkdir -p "$bad_root2"
expect_refuse wrong-root-7549e36 \
  "${base[@]}" ROOT="$bad_root2" CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong wait =="
expect_refuse wrong-wait \
  env -u SERIAL VALIDATE_ONLY=1 WAIT_S=30 ROOT="$good_root" CELL_ID=r7-11 \
  FAULT=serial-wrap FIXTURE=direct bash "$RUNNER"

echo "== existing destination =="
exist_root="$TMP/exist/runtime-a07d66c"
mkdir -p "$exist_root/r7-11"
echo frozen > "$exist_root/r7-11/keep.txt"
before=$(find "$exist_root/r7-11" | wc -l)
expect_refuse existing-destination \
  "${base[@]}" ROOT="$exist_root" CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct \
  bash "$RUNNER"
after=$(find "$exist_root/r7-11" | wc -l)
if [ "$before" -eq "$after" ] && [ -f "$exist_root/r7-11/keep.txt" ]; then
  echo "PASS existing-destination-no-write"
  PASS=$((PASS + 1))
else
  echo "FAIL existing-destination-no-write wrote into cell"
  FAIL=$((FAIL + 1))
fi

echo "== extra selector args =="
expect_refuse extra-args \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct \
  bash "$RUNNER" r7-09

echo "== missing SERIAL live =="
expect_refuse missing-serial-live \
  env -u SERIAL -u VALIDATE_ONLY WAIT_S=12 ROOT="$good_root" CELL_ID=r7-11 \
  FAULT=serial-wrap FIXTURE=direct bash "$RUNNER"

echo "== generic still REVIEW_REQUIRED for r7-11 =="
gplan=$(env -u SERIAL VALIDATE_ONLY=1 WAIT_S=12 ROOT="$good_root" \
  CELL_ID=r7-11 FAULT=serial-wrap FIXTURE=direct bash "$GENERIC")
if echo "$gplan" | grep -q 'live_status=REVIEW_REQUIRED' \
  && echo "$gplan" | grep -q 'SUPPORTED_BY_MAPPING_BUT_REQUIRES_PACKET_REVIEW'; then
  echo "PASS generic-review-required-unlifted"
  PASS=$((PASS + 1))
else
  echo "FAIL generic-review-required-unlifted"
  echo "$gplan" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== expected wrap mock =="
mkdir -p "$TMP/expected"
cat > "$TMP/expected/follow.txt" <<'EOF'
I gatea-telemetry: GATEA_EVENT seq=0 role=1 event=2 generation=1 serial=0 src=0 dst=0
I gatea-telemetry: GATEA_EVENT seq=1 role=1 event=35 generation=1 serial=0 src=11 dst=1
I gatea-telemetry: GATEA_EVENT seq=2 role=1 event=16 generation=1 serial=0 src=0 dst=0
F gatea-a1: GATEA_FATAL_HALT what=x-serial-wrap reason=6
I gatea-a1: GATEA_SUMMARY where=x-serial-wrap nonce=1 generation=1 nextSequence=3 overflow=0 firstFailed=0 generationFatal=6 fatalReason=6 c0=0 c1=0 c2=0 c3=0 c4=0 c5=0 c6=0 c7=0 c8=0 c9=0 c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 c16=1 c17=0 c18=0 c19=0 c20=0 c21=0 c22=0 c23=0 c24=1 c25=0 c26=0 c27=0
EOF
set +e
cout=$(python3 "$CLASSIFY" --follow "$TMP/expected/follow.txt" --x-alive 0 \
  --env-captured 1 --env-exact 1 --fixture-reached 1 --holder-reached 1 \
  --out "$TMP/expected/classify.txt")
crc=$?
set -e
if [ "$crc" -eq 0 ] \
  && grep -q 'classification=EXPECTED_WRAP' "$TMP/expected/classify.txt" \
  && grep -q 'publish_serial0=0' "$TMP/expected/classify.txt" \
  && grep -q 'continue_judge=YES' "$TMP/expected/classify.txt" \
  && grep -q 'runner_invalid=NO' "$TMP/expected/classify.txt"; then
  echo "PASS expected-wrap-accept"
  PASS=$((PASS + 1))
else
  echo "FAIL expected-wrap-accept rc=$crc"
  echo "$cout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== serial0 leaked mock =="
mkdir -p "$TMP/serial0"
cat > "$TMP/serial0/follow.txt" <<'EOF'
I gatea-telemetry: GATEA_EVENT seq=0 role=1 event=35 generation=1 serial=0 src=11 dst=1
I gatea-telemetry: GATEA_EVENT seq=1 role=1 event=6 generation=1 serial=0 src=0 dst=0
I gatea-telemetry: GATEA_EVENT seq=2 role=1 event=16 generation=1 serial=0 src=0 dst=0
F gatea-a1: GATEA_FATAL_HALT what=x-serial-wrap reason=6
I gatea-a1: GATEA_SUMMARY where=x-serial-wrap nonce=1 generation=1 nextSequence=3 overflow=0 firstFailed=0 generationFatal=6 fatalReason=6 c0=0 c1=0 c2=0 c3=0 c4=0 c5=0 c6=0 c7=0 c8=0 c9=0 c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 c16=1 c17=0 c18=0 c19=0 c20=0 c21=0 c22=0 c23=0 c24=1 c25=0 c26=0 c27=0
EOF
set +e
s0out=$(python3 "$CLASSIFY" --follow "$TMP/serial0/follow.txt" --x-alive 0 \
  --env-captured 1 --env-exact 1 --fixture-reached 1 --holder-reached 1 \
  --out "$TMP/serial0/classify.txt")
s0rc=$?
set -e
if [ "$s0rc" -eq 2 ] \
  && grep -q 'classification=SERIAL0_LEAKED' "$TMP/serial0/classify.txt" \
  && grep -q 'product_fail=YES' "$TMP/serial0/classify.txt"; then
  echo "PASS serial0-leaked-product-fail"
  PASS=$((PASS + 1))
else
  echo "FAIL serial0-leaked-product-fail rc=$s0rc"
  echo "$s0out" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== wrong terminal mock =="
mkdir -p "$TMP/wrong"
cat > "$TMP/wrong/follow.txt" <<'EOF'
I gatea-telemetry: GATEA_EVENT seq=0 role=1 event=35 generation=1 serial=0 src=11 dst=1
I gatea-telemetry: GATEA_EVENT seq=1 role=1 event=16 generation=1 serial=0 src=0 dst=0
F gatea-a1: GATEA_FATAL_HALT what=x-hup reason=6
I gatea-a1: GATEA_SUMMARY where=x-hup nonce=1 generation=1 nextSequence=2 overflow=0 firstFailed=0 generationFatal=6 fatalReason=6 c0=0 c1=0 c2=0 c3=0 c4=0 c5=0 c6=0 c7=0 c8=0 c9=0 c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 c16=1 c17=0 c18=0 c19=0 c20=0 c21=0 c22=0 c23=0 c24=1 c25=0 c26=0 c27=0
EOF
set +e
wout=$(python3 "$CLASSIFY" --follow "$TMP/wrong/follow.txt" --x-alive 0 \
  --env-captured 1 --env-exact 1 --fixture-reached 1 --holder-reached 1 \
  --out "$TMP/wrong/classify.txt")
wrc=$?
set -e
if [ "$wrc" -eq 2 ] \
  && grep -q 'classification=WRONG_TERMINAL' "$TMP/wrong/classify.txt" \
  && grep -q 'product_fail=YES' "$TMP/wrong/classify.txt"; then
  echo "PASS wrong-terminal-x-hup"
  PASS=$((PASS + 1))
else
  echo "FAIL wrong-terminal-x-hup rc=$wrc"
  echo "$wout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== no event35 mock =="
mkdir -p "$TMP/no35"
cat > "$TMP/no35/follow.txt" <<'EOF'
I gatea-telemetry: GATEA_EVENT seq=0 role=1 event=16 generation=1 serial=0 src=0 dst=0
F gatea-a1: GATEA_FATAL_HALT what=x-serial-wrap reason=6
I gatea-a1: GATEA_SUMMARY where=x-serial-wrap nonce=1 generation=1 nextSequence=1 overflow=0 firstFailed=0 generationFatal=6 fatalReason=6 c0=0 c1=0 c2=0 c3=0 c4=0 c5=0 c6=0 c7=0 c8=0 c9=0 c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 c16=1 c17=0 c18=0 c19=0 c20=0 c21=0 c22=0 c23=0 c24=1 c25=0 c26=0 c27=0
EOF
set +e
n35out=$(python3 "$CLASSIFY" --follow "$TMP/no35/follow.txt" --x-alive 0 \
  --env-captured 1 --env-exact 1 --fixture-reached 1 --holder-reached 1 \
  --out "$TMP/no35/classify.txt")
n35rc=$?
set -e
if [ "$n35rc" -eq 9 ] \
  && grep -q 'classification=NO_EVENT35' "$TMP/no35/classify.txt" \
  && grep -q 'runner_invalid=YES' "$TMP/no35/classify.txt"; then
  echo "PASS no-event35-invalid"
  PASS=$((PASS + 1))
else
  echo "FAIL no-event35-invalid rc=$n35rc"
  echo "$n35out" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== repeated seed mock =="
mkdir -p "$TMP/repeat"
cat > "$TMP/repeat/follow.txt" <<'EOF'
I gatea-telemetry: GATEA_EVENT seq=0 role=1 event=35 generation=1 serial=0 src=11 dst=1
I gatea-telemetry: GATEA_EVENT seq=1 role=1 event=35 generation=1 serial=0 src=11 dst=1
I gatea-telemetry: GATEA_EVENT seq=2 role=1 event=16 generation=1 serial=0 src=0 dst=0
F gatea-a1: GATEA_FATAL_HALT what=x-serial-wrap reason=6
I gatea-a1: GATEA_SUMMARY where=x-serial-wrap nonce=1 generation=1 nextSequence=3 overflow=0 firstFailed=0 generationFatal=6 fatalReason=6 c0=0 c1=0 c2=0 c3=0 c4=0 c5=0 c6=0 c7=0 c8=0 c9=0 c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 c16=1 c17=0 c18=0 c19=0 c20=0 c21=0 c22=0 c23=0 c24=1 c25=0 c26=0 c27=0
EOF
set +e
repout=$(python3 "$CLASSIFY" --follow "$TMP/repeat/follow.txt" --x-alive 0 \
  --env-captured 1 --env-exact 1 --fixture-reached 1 --holder-reached 1 \
  --out "$TMP/repeat/classify.txt")
reprc=$?
set -e
if [ "$reprc" -eq 9 ] \
  && grep -q 'classification=REPEATED_SEED' "$TMP/repeat/classify.txt" \
  && grep -q 'runner_invalid=YES' "$TMP/repeat/classify.txt"; then
  echo "PASS repeated-seed-invalid"
  PASS=$((PASS + 1))
else
  echo "FAIL repeated-seed-invalid rc=$reprc"
  echo "$repout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== legal runtime r7-11 still absent after all tests =="
if [ -e "$LEGAL" ]; then
  echo "FAIL legal-runtime-r7-11-final path exists $LEGAL"
  FAIL=$((FAIL + 1))
else
  echo "PASS legal-runtime-r7-11-final"
  PASS=$((PASS + 1))
fi

echo
echo "PASS=$PASS FAIL=$FAIL"
if [ "$FAIL" -ne 0 ]; then
  exit 2
fi
echo "R7_11_MAPPING_TESTS_PASS"
exit 0
