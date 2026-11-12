#!/usr/bin/env bash
# Host-only input-matrix tests for run-r7-one-cell-a07d66c.sh.
# VALIDATE_ONLY=1 only. No ADB, no mkdir of runtime-a07d66c/r7-01, no X3.
set -euo pipefail

RUNTIME=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime
RUNNER="$RUNTIME/run-r7-one-cell-a07d66c.sh"
LEGAL="$RUNTIME/runtime-a07d66c/r7-01"
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

echo "== valid r7-01 =="
expect_accept valid-r7-01 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-01 FAULT=src-ready-miss FIXTURE=direct \
  bash "$RUNNER"
if [ -e "$good_root/r7-01" ]; then
  echo "FAIL valid-r7-01-no-mkdir destination was created"
  FAIL=$((FAIL + 1))
else
  echo "PASS valid-r7-01-no-mkdir"
  PASS=$((PASS + 1))
fi
if [ -e "$LEGAL" ]; then
  echo "FAIL legal-runtime-r7-01-still-absent path exists $LEGAL"
  FAIL=$((FAIL + 1))
else
  echo "PASS legal-runtime-r7-01-still-absent"
  PASS=$((PASS + 1))
fi

echo "== wrong fault =="
expect_refuse wrong-fault \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-01 FAULT=dst-ready-miss FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong fixture =="
expect_refuse wrong-fixture \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-01 FAULT=src-ready-miss FIXTURE=present \
  bash "$RUNNER"

echo "== wrong root fdfb1ce =="
bad_root="$TMP/runtime-fdfb1ce"
mkdir -p "$bad_root"
expect_refuse wrong-root \
  "${base[@]}" ROOT="$bad_root" CELL_ID=r7-01 FAULT=src-ready-miss FIXTURE=direct \
  bash "$RUNNER"

echo "== completed r7-05 =="
expect_refuse completed-r7-05 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-05 FAULT=post-draw-gl FIXTURE=direct \
  bash "$RUNNER"

echo "== completed r7-04 =="
expect_refuse completed-r7-04 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-04 FAULT=fbo-incomplete FIXTURE=direct \
  bash "$RUNNER"

echo "== wrong wait =="
expect_refuse wrong-wait \
  env -u SERIAL VALIDATE_ONLY=1 WAIT_S=30 ROOT="$good_root" CELL_ID=r7-01 \
  FAULT=src-ready-miss FIXTURE=direct bash "$RUNNER"

echo "== missing CELL_ID =="
expect_refuse missing-cell-id \
  env -u SERIAL -u CELL_ID VALIDATE_ONLY=1 WAIT_S=12 ROOT="$good_root" \
  FAULT=src-ready-miss FIXTURE=direct bash "$RUNNER"

echo "== missing FAULT =="
expect_refuse missing-fault \
  env -u SERIAL -u FAULT VALIDATE_ONLY=1 WAIT_S=12 ROOT="$good_root" \
  CELL_ID=r7-01 FIXTURE=direct bash "$RUNNER"

echo "== missing ROOT =="
expect_refuse missing-root \
  env -u SERIAL -u ROOT VALIDATE_ONLY=1 WAIT_S=12 CELL_ID=r7-01 \
  FAULT=src-ready-miss FIXTURE=direct bash "$RUNNER"

echo "== missing SERIAL live =="
expect_refuse missing-serial-live \
  env -u SERIAL -u VALIDATE_ONLY WAIT_S=12 ROOT="$good_root" CELL_ID=r7-01 \
  FAULT=src-ready-miss FIXTURE=direct bash "$RUNNER"

echo "== existing destination =="
exist_root="$TMP/exist/runtime-a07d66c"
mkdir -p "$exist_root/r7-01"
before=$(find "$exist_root/r7-01" | wc -l)
expect_refuse existing-destination \
  "${base[@]}" ROOT="$exist_root" CELL_ID=r7-01 FAULT=src-ready-miss FIXTURE=direct \
  bash "$RUNNER"
after=$(find "$exist_root/r7-01" | wc -l)
if [ "$before" -eq "$after" ]; then
  echo "PASS existing-destination-no-write"
  PASS=$((PASS + 1))
else
  echo "FAIL existing-destination-no-write wrote into cell"
  FAIL=$((FAIL + 1))
fi

echo "== extra selector args =="
expect_refuse extra-args \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-01 FAULT=src-ready-miss FIXTURE=direct \
  bash "$RUNNER" r7-02

echo "== review-required mapping still validates =="
expect_accept review-r7-09 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-09 FAULT=wrong-generation-frame FIXTURE=direct \
  bash "$RUNNER"

echo "== legal runtime r7-01 still absent after all tests =="
if [ -e "$LEGAL" ]; then
  echo "FAIL legal-runtime-r7-01-final path exists $LEGAL"
  FAIL=$((FAIL + 1))
else
  echo "PASS legal-runtime-r7-01-final"
  PASS=$((PASS + 1))
fi

echo
echo "PASS=$PASS FAIL=$FAIL"
if [ "$FAIL" -ne 0 ]; then
  exit 2
fi
echo "MAPPING_TESTS_PASS"
exit 0
