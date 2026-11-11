#!/usr/bin/env bash
# Host-only input + Present-timeout mocks for run-r7-p1-a4c8177.sh.
# VALIDATE_ONLY=1 and classifier/judge/C-class mocks only. No ADB, no mkdir of
# runtime-a4c8177/r7-p1; does not touch frozen runtime-abb27a65/r7-p1, no X3, no install, no fault12.
set -euo pipefail

RUNTIME=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime
RUNNER="$RUNTIME/run-r7-p1-a4c8177.sh"
HIST_P1="$RUNTIME/run-r7-p1-8545b26.sh"
GENERIC="$RUNTIME/run-r7-one-cell-a07d66c.sh"
R710="$RUNTIME/run-r7-10-8545b26.sh"
CLASSIFY_TEST="$RUNTIME/scripts/test_classify_r7_p1_a4c8177.py"
JUDGE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py
TEST_JUDGE=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py
FIX=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures
LEGAL="$RUNTIME/runtime-a4c8177/r7-p1"
FROZEN_ABB_P1="$RUNTIME/runtime-abb27a65/r7-p1"
FROZEN_ABB_RUNNER="$RUNTIME/run-r7-p1-abb27a65.sh"
LEGAL_P2="$RUNTIME/runtime-a4c8177/r7-p2"
HIST_INVALID="$RUNTIME/runtime-8545b26/r7-p1"
HIST_R710="$RUNTIME/runtime-a07d66c/r7-10"
LEGAL_R710="$RUNTIME/runtime-8545b26/r7-10"
WT=/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm
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
good_root="$TMP/runtime-a4c8177"
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
if echo "$plan" | grep -q 'expect_sha=a4c8177f4b059fddd111717255e9d23cf0e15e1e' \
  && echo "$plan" | grep -q 'expect_version=1.03.01-a4c8177-18.09.26' \
  && echo "$plan" | grep -q 'expect_version_code=15' \
  && echo "$plan" | grep -q 'expect_package=com.waydefu.x11gpu' \
  && echo "$plan" | grep -q 'expect_build_id=dcd8297497c38f6b277cc9cbdb74b2eea06dba60' \
  && echo "$plan" | grep -q 'expect_apk_sha256=91a4b74eff2c54cceba89ca3b8f8530442fa371fd7a67523eaf8bbd73c75a55c' \
  && echo "$plan" | grep -q 'expect_signer=b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1' \
  && echo "$plan" | grep -q 'ci=35295094951' \
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
if [ -e "$LEGAL_P2" ]; then
  echo "FAIL legal-runtime-r7-p2-still-absent path exists $LEGAL_P2"
  FAIL=$((FAIL + 1))
else
  echo "PASS legal-runtime-r7-p2-still-absent"
  PASS=$((PASS + 1))
fi
if [ -d "$FROZEN_ABB_P1" ] && grep -q 'PEER_DIED' "$FROZEN_ABB_P1/r7-p1-classify.txt"; then
  echo "PASS frozen-abb27a65-r7-p1-invalid-intact"
  PASS=$((PASS + 1))
else
  echo "FAIL frozen-abb27a65-r7-p1-invalid-intact"
  FAIL=$((FAIL + 1))
fi
if [ "$(sha256sum "$FROZEN_ABB_RUNNER" | awk '{print $1}')" = 95900a2d22a37877c065b007feefe07895d8dcb37661e0d3b52b27e9d4ba7098 ]; then
  echo "PASS frozen-abb27a65-p1-runner-unmodified"
  PASS=$((PASS + 1))
else
  echo "FAIL frozen-abb27a65-p1-runner-unmodified"
  FAIL=$((FAIL + 1))
fi
if [ -d "$HIST_INVALID" ] && grep -q 'NO_PRESENT_CALLBACK' "$HIST_INVALID/r7-p1-classify.txt"; then
  echo "PASS historical-8545b26-r7-p1-invalid-intact"
  PASS=$((PASS + 1))
else
  echo "FAIL historical-8545b26-r7-p1-invalid-intact"
  FAIL=$((FAIL + 1))
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
got_hold=$(sha256sum "$FIX/p_b3a_hold" | awk '{print $1}')
if [ "$got_fix" = fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86 ] \
  && [ "$(stat -c%s "$FIX/p_r6_d2_present")" = 72536 ] \
  && [ "$got_hold" = 3417abbf0855c10bfd2328e87f33518c2f7f59c42529ba157a847d3019f5b5ca ]; then
  echo "PASS present-fixture-and-holder-identity"
  PASS=$((PASS + 1))
else
  echo "FAIL present-fixture-and-holder-identity got_fix=$got_fix got_hold=$got_hold"
  FAIL=$((FAIL + 1))
fi

echo "== frozen root abb27a65 forbidden =="
old_abb="$TMP/runtime-abb27a65"
mkdir -p "$old_abb"
expect_refuse wrong-root-abb27a65 \
  "${base[@]}" ROOT="$old_abb" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"

echo "== old root 8545b26 forbidden =="
old_root="$TMP/runtime-8545b26"
mkdir -p "$old_root"
expect_refuse wrong-root-8545b26 \
  "${base[@]}" ROOT="$old_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"

echo "== old root a07d66c =="
old_root2="$TMP/runtime-a07d66c"
mkdir -p "$old_root2"
expect_refuse wrong-root-a07d66c \
  "${base[@]}" ROOT="$old_root2" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present \
  bash "$RUNNER"

echo "== wrong cell r7-p2 =="
expect_refuse wrong-cell-r7-p2 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-p2 FAULT=present-renderer-exit FIXTURE=present \
  bash "$RUNNER"

echo "== wrong cell r7-10 =="
expect_refuse wrong-cell-r7-10 \
  "${base[@]}" ROOT="$good_root" CELL_ID=r7-10 FAULT=renderer-exit-after-consume FIXTURE=direct \
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

echo "== live existing destination =="
exist_live="$TMP/exist-live/runtime-a4c8177"
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

echo "== frozen hashes =="
if [ "$(sha256sum "$HIST_P1" | awk '{print $1}')" = 46c2289dcdddd518c2e4ecb99095e3991c640fa11e92149b83d8d79f20a16ba7 ]; then
  echo "PASS historical-p1-runner-unmodified"
  PASS=$((PASS + 1))
else
  echo "FAIL historical-p1-runner-unmodified"
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

echo "== C class + wait-wake + static verifier =="
cc -O0 -o "$TMP/test_gatea_test_fault_class" "$WT/scripts/test_gatea_test_fault_class.c"
fout=$("$TMP/test_gatea_test_fault_class")
if echo "$fout" | grep -q 'GATEA_TEST_FAULT_CLASS=PASS'; then
  echo "PASS gatea-test-fault-class"
  PASS=$((PASS + 1))
else
  echo "FAIL gatea-test-fault-class"
  echo "$fout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi
cc -O0 -o "$TMP/test_gatea_wait_wake_class" "$WT/scripts/test_gatea_wait_wake_class.c"
wout=$("$TMP/test_gatea_wait_wake_class")
if echo "$wout" | grep -q 'GATEA_WAIT_WAKE_CLASS=PASS'; then
  echo "PASS wait-wake-class"
  PASS=$((PASS + 1))
else
  echo "FAIL wait-wake-class"
  echo "$wout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi
set +e
vout=$(python3 "$WT/scripts/verify_r7_p1_present_target_arm.py" "$WT")
vrc=$?
set -e
if [ "$vrc" -eq 0 ] && echo "$vout" | grep -q 'R7_P1_PRESENT_TARGET_ARM=PASS'; then
  echo "PASS present-target-arm-static"
  PASS=$((PASS + 1))
else
  echo "FAIL present-target-arm-static rc=$vrc"
  echo "$vout" | sed 's/^/  /'
  FAIL=$((FAIL + 1))
fi

if [ -e /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-a4c8177/r7-p1 ]; then
  echo "FAIL tooling-created-legal-r7-p1"
  FAIL=$((FAIL + 1))
else
  echo "PASS tooling-did-not-create-r7-p1"
  PASS=$((PASS + 1))
fi


echo "== liveness helper + no host-/proc death authority =="
set +e
python3 "$RUNTIME/scripts/test_android_activity_liveness.py" -q
lrc=$?
set -e
if [ "$lrc" -eq 0 ]; then
  echo "PASS android-activity-liveness-unit"
  PASS=$((PASS + 1))
else
  echo "FAIL android-activity-liveness-unit rc=$lrc"
  FAIL=$((FAIL + 1))
fi
if grep -n '\[ -d "/proc/\$ACT_PID" \] && \[ -d "/proc/\$X3" \]' "$RUNNER"; then
  echo "FAIL runner-still-uses-host-proc-as-alive-conjunction"
  FAIL=$((FAIL + 1))
else
  echo "PASS runner-adb-proc-not-host-conjunction"
  PASS=$((PASS + 1))
fi
if grep -q 'ADB shell "test -d /proc/\$ACT_PID"' "$RUNNER" && grep -q 'authority=adb-device-proc-and-ps' "$RUNNER"; then
  echo "PASS runner-device-authoritative-probe"
  PASS=$((PASS + 1))
else
  echo "FAIL runner-device-authoritative-probe"
  FAIL=$((FAIL + 1))
fi
if grep -q 'activity-alive-during-wait' "$RUNNER"; then
  echo "PASS runner-passes-bound-activity-alive"
  PASS=$((PASS + 1))
else
  echo "FAIL runner-passes-bound-activity-alive"
  FAIL=$((FAIL + 1))
fi
if grep -q 'liveness_authority=adb-device-proc-and-ps' <<<"$(VALIDATE_ONLY=1 WAIT_S=12 ROOT="$good_root" CELL_ID=r7-p1 FAULT=present-hold-complete FIXTURE=present bash "$RUNNER")"; then
  echo "PASS plan-liveness-authority"
  PASS=$((PASS + 1))
else
  echo "FAIL plan-liveness-authority"
  FAIL=$((FAIL + 1))
fi

echo "RESULT pass=$PASS fail=$FAIL"
if [ "$FAIL" -ne 0 ]; then
  exit 2
fi
exit 0
