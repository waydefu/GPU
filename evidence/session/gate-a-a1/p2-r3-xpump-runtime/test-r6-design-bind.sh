#!/usr/bin/env bash
# Negative binding tests for r6-design-bind.sh. No ADB.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=r6-design-bind.sh
source "$HERE/r6-design-bind.sh"

export R6_RUNTIME_ROOT=/tmp/x
mkdir -p /tmp/x /tmp/runtime-37d8393

fail=0
check() {
  local want=$1
  local got=0
  r6_design_bind >/tmp/r6-bind-out.txt 2>&1 || got=$?
  if [ "$got" -ne "$want" ]; then
    echo "FAIL want=$want got=$got VARIANT=${VARIANT:-} CELL=${CELL:-} EXPECT_VERSION=${EXPECT_VERSION:-}"
    cat /tmp/r6-bind-out.txt
    fail=1
  fi
}

VARIANT=d2-oom CELL=/tmp/runtime-37d8393/r6-d2-oom check 9
VARIANT=d2-inflight CELL=/tmp/x/runtime-9369553/r6-d2-inflight-retry2 check 9
VARIANT=d1 CELL=/tmp/x/runtime-9369553/r6-d1 check 0
VARIANT=d2-inflight CELL=/tmp/x/runtime-9369553/r6-d2-inflight-retry1 check 0
VARIANT=d2-oom CELL=/tmp/x/runtime-9369553/r6-d2-oom check 9
unset EXPECT_VERSION || true
VARIANT=d2-inflight CELL=/tmp/x/runtime-54ff35b/r6-d2-inflight check 9
EXPECT_VERSION=1.03.01-54ff35b-15.09.26
VARIANT=d2-inflight CELL=/tmp/x/runtime-54ff35b/r6-d2-inflight check 0
VARIANT=d2-oom CELL=/tmp/x/runtime-54ff35b/r6-d2-oom check 0
VARIANT=d1 CELL=/tmp/x/runtime-54ff35b/r6-d1 check 0
VARIANT=nope CELL=/tmp/x/runtime-9369553/r6-d1 check 9
VARIANT=d2-inflight CELL=/tmp/x/runtime-aNOTHEX/r6-d2-inflight check 9
EXPECT_VERSION=1.03.01-deadbee-15.09.26
VARIANT=d2-inflight CELL=/tmp/x/runtime-54ff35b/r6-d2-inflight check 9
EXPECT_VERSION=1.03.01-54ff35b-15.09.26
VARIANT=d2-inflight CELL=/tmp/elsewhere/runtime-54ff35b/r6-d2-inflight check 9

if [ "$fail" -ne 0 ]; then
  echo BIND_NEG=FAIL
  exit 1
fi
echo BIND_NEG=PASS
