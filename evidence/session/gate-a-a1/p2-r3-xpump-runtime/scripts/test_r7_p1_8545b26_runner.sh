#!/usr/bin/env bash
# Host-only input + Present-timeout mocks for run-r7-p1-8545b26.sh.
# VALIDATE_ONLY=1 and classifier/judge mocks only. No ADB, no mkdir of
# runtime-8545b26/r7-p1, no X3, no install, no fault12.
set -euo pipefail

RUNTIME=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime
RUNNER="$RUNTIME/run-r7-p1-8545b26.sh"
GENERIC="$RUNTIME/run-r7-one-cell-a07d66c.sh"
R710="$RUNTIME/run-r7-10-8545b26.sh"
CLASSIFY="$RUNTIME/scripts/classify_r7_p1_present_hold.py"
CLASSIFY_TEST="$RUNTIME/scripts/test_classify_r7_p1_present_hold.py"
JUDGE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py
TEST_JUDGE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
LEGAL="$RUNTIME/runtime-8545b26/r7-p1"
HIST_R710="$RUNTIME/runtime-a07d66c/r7-10"
LEGAL_R710="$RUNTIME/runtime-8545b26/r7-10"
WAIT_SRC=/root/projects/GPU加速/src/f8-ahb-gatea-r7-10-hup/scripts/test_gatea_wait_wake_class.c
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
expect_accept valid-r7-p1 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"
if [ -e "$good_root/r7-p1" ]; then
  echo "FAIL valid-r7-p1-no-mkdir destination was created"
  FAIL=$((FAIL + 1))
else
  echo "PASS valid-r7-p1-no-mkdir"
  PASS=$((PASS + 1))
fi
plan=$("${base[@]}" ROOT="$good_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present bash "$RUNNER")
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
  && echo "$plan" | grep -q 'r7_p1_trigger=0' \
  && echo "$plan" | grep -q 'r7_p2=0' \
  && echo "$plan" | grep -q 'fault12_trigger=0' \
  && echo "$plan" | grep -q 'stable_policy=read-only' \
  && echo "$plan" | grep -q 'install_policy=this runner never installs' \
  && echo "$plan" | grep -q 'fixture_sha256=fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86' \
  && echo "$plan" | grep -q 'holder_required=YES' \
  && echo "$plan" | grep -q 'live_status=ENABLED'; then
  echo "PASS valid-r7-p1-plan-bind"
  PASS=$((PASS + 1))
else
  echo "FAIL valid-r7-p1-plan-bind"
  echo "$plan" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi
if [ -e "$LEGAL" ]; then
  echo "FAIL legal-runtime-r7-p1-still-absent path exists $LEGAL"
  FAIL=$((FAIL + 1))
else
  echo "PASS legal-runtime-r7-p1-still-absent"
  PASS=$((PASS + 1))
fi
if [ -d "$HIST_R710" ] && grep -q 'x-direct-not-success reason=4' "$HIST_R710/judge.txt"; then
  echo "PASS historical-a07d66c-r7-10-intact"
  PASS=$((PASS + 1))
else
  echo "FAIL historical-a07d66c-r7-10-intact"
  FAIL=$((FAIL + 1))
fi
if [ -d "$LEGAL_R710" ] && grep -q '^R7_PASS renderer-exit-after-consume' "$LEGAL_R710/judge.txt"; then
  echo "PASS frozen-8545b26-r7-10-intact"
  PASS=$((PASS + 1))
else
  echo "FAIL frozen-8545b26-r7-10-intact"
  FAIL=$((FAIL + 1))
fi

got_fix=$(sha256sum "$FIX/p_r6_d2_present" | awk '{print $1}')
if [ "$got_fix" = fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86 ] \
  && [ "$(stat -c%s "$FIX/p_r6_d2_present")" = 72536 ]; then
  echo "PASS present-fixture-identity"
  PASS=$((PASS + 1))
else
  echo "FAIL present-fixture-identity got=$got_fix size=$(stat -c%s "$FIX/p_r6_d2_present")"
  FAIL=$((FAIL + 1))
fi

echo "== old root a07d66c =="
old_root="$TMP/runtime-a07d66c"
mkdir -p "$old_root"
expect_refuse wrong-root-a07d66c \
  "${base[@]}" ROOT="$old_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"

echo "== wrong root fdfb1ce =="
bad_root="$TMP/runtime-fdfb1ce"
mkdir -p "$bad_root"
expect_refuse wrong-root-fdfb1ce \
  "${base[@]}" ROOT="$bad_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"

echo "== wrong root 7549e36 =="
bad_root2="$TMP/runtime-7549e36"
mkdir -p "$bad_root2"
expect_refuse wrong-root-7549e36 \
  "${base[@]}" ROOT="$bad_root2" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"

echo "== wrong cell r7-10 =="
expect_refuse wrong-cell-r7-10 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong cell r7-p2 =="
expect_refuse wrong-cell-r7-p2 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-p2 FAULT=present-renderer-exit FIXTURE=present \
  bash "$RUNNER"

echo "== wrong cell r7-01 =="
expect_refuse wrong-cell-r7-01 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-01 FAULT=src-ready-miss FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong fault =="
expect_refuse wrong-fault \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-p1 FAULT=present-renderer-exit FIXTURE=present \
  bash "$RUNNER"

echo "== wrong fixture direct =="
expect_refuse wrong-fixture \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong wait =="
expect_refuse wrong-wait \
  env -u SERIAL VALIDATE_ONLY=1 WAIT_S=30 ROOT="$good_root" CELL_ID=r7-p1 \
  FAULT=present-hold-complete FIXTURE=present bash "$RUNNER"

echo "== VALIDATE_ONLY existing destination does not write =="
exist_root="$TMP/exist-vo/runtime-8545b26"
mkdir -p "$exist_root/r7-p1"
echo frozen > "$exist_root/r7-p1/keep.txt"
before=$(find "$exist_root/r7-p1" | wc -l)
expect_accept validate-only-existing-dest \
  "${base[@]}" ROOT="$exist_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"
after=$(find "$exist_root/r7-p1" | wc -l)
if [ "$before" -eq "$after" ] && [ -f "$exist_root/r7-p1/keep.txt" ]; then
  echo "PASS validate-only-existing-dest-no-write"
  PASS=$((PASS + 1))
else
  echo "FAIL validate-only-existing-dest-no-write wrote into cell"
  FAIL=$((FAIL + 1))
fi

echo "== live existing destination =="
exist_live="$TMP/exist-live/runtime-8545b26"
mkdir -p "$exist_live/r7-p1"
echo frozen > "$exist_live/r7-p1/keep.txt"
before=$(find "$exist_live/r7-p1" | wc -l)
expect_refuse existing-destination-live \
  env -u VALIDATE_ONLY SERIAL=dummy WAIT_S=12 ROOT="$exist_live" CELL_ID=r7-p1 \
  FAULT=present-hold-complete FIXTURE=present bash "$RUNNER"
after=$(find "$exist_live/r7-p1" | wc -l)
if [ "$before" -eq "$after" ] && [ -f "$exist_live/r7-p1/keep.txt" ]; then
  echo "PASS existing-destination-live-no-write"
  PASS=$((PASS + 1))
else
  echo "FAIL existing-destination-live-no-write wrote into cell"
  FAIL=$((FAIL + 1))
fi

echo "== extra selector args =="
expect_refuse extra-args \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER" r7-p2

echo "== missing SERIAL live =="
expect_refuse missing-serial-live \
  env -u SERIAL -u VALIDATE_ONLY WAIT_S=12 ROOT="$good_root" CELL_ID=r7-p1 \
  FAULT=present-hold-complete FIXTURE=present bash "$RUNNER"

echo "== generic still REVIEW_REQUIRED for r7-p1 =="
gplan=$(VALIDATE_ONLY=1 WAIT_S=12 ROOT="$TMP/runtime-a07d66c" CELL_ID=r7-p1 \
  FAULT=present-hold-complete FIXTURE=present bash "$GENERIC")
if echo "$gplan" | grep -q 'live_status=REVIEW_REQUIRED' \
  && echo "$gplan" | grep -q 'SUPPORTED_BY_MAPPING_BUT_REQUIRES_PACKET_REVIEW'; then
  echo "PASS generic-r7-p1-still-review-required"
  PASS=$((PASS + 1))
else
  echo "FAIL generic-r7-p1-still-review-required"
  echo "$gplan" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi
if [ "$(sha256sum "$GENERIC" | awk '{print $1}')" = 36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded ]; then
  echo "PASS generic-runner-unmodified"
  PASS=$((PASS + 1))
else
  echo "FAIL generic-runner-unmodified"
  FAIL=$((FAIL + 1))
fi
if [ "$(sha256sum "$R710" | awk '{print $1}')" = 690a865d1bce410cabe10dd7d1da27be89a1f53302ac932f64cc50980afc54cd ]; then
  echo "PASS r7-10-runner-unmodified"
  PASS=$((PASS + 1))
else
  echo "FAIL r7-10-runner-unmodified"
  FAIL=$((FAIL + 1))
fi
if [ "$(sha256sum "$JUDGE" | awk '{print $1}')" = fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17 ]; then
  echo "PASS judge-unmodified"
  PASS=$((PASS + 1))
else
  echo "FAIL judge-unmodified"
  FAIL=$((FAIL + 1))
fi

echo "== classifier unit tests =="
set +e
python3 "$CLASSIFY_TEST" -q
crc=$?
set -e
if [ "$crc" -eq 0 ]; then
  echo "PASS classify-unit-tests"
  PASS=$((PASS + 1))
else
  echo "FAIL classify-unit-tests rc=$crc"
  FAIL=$((FAIL + 1))
fi

echo "== frozen judge 16/16 =="
set +e
jout=$(python3 "$TEST_JUDGE" -q)
jrc=$?
set -e
if [ "$jrc" -eq 0 ]; then
  echo "PASS judge-regression-16"
  PASS=$((PASS + 1))
else
  echo "FAIL judge-regression-16 rc=$jrc"
  echo "$jout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

echo "== wait-wake architecture host binary =="
cc -O0 -o "$TMP/test_gatea_wait_wake_class" "$WAIT_SRC"
wout=$("$TMP/test_gatea_wait_wake_class")
if echo "$wout" | grep -q 'GATEA_WAIT_WAKE_CLASS=PASS'; then
  echo "PASS wait-wake-class"
  PASS=$((PASS + 1))
else
  echo "FAIL wait-wake-class"
  echo "$wout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

if [ -e /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-8545b26/r7-p1 ]; then
  echo "FAIL tooling-created-legal-r7-p1"
  FAIL=$((FAIL + 1))
else
  echo "PASS tooling-did-not-create-r7-p1"
  PASS=$((PASS + 1))
fi

echo "RESULT pass=$PASS fail=$FAIL"
if [ "$FAIL" -ne 0 ]; then
  exit 2
fi
exit 0
