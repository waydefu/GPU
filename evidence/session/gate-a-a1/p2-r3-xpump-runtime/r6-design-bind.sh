# r6-design-bind.sh — CELL / VARIANT / fixture SHA / versionName gates.
# Sourced by run-r6-design.sh. No ADB. Historical 9369553 cells stay frozen.

r6_design_bind() {
  local run_sha ver_sha cell_abs root_abs
  if [ -z "${VARIANT:-}" ]; then
    echo "REFUSE VARIANT unset"
    return 9
  fi
  if [ -z "${CELL:-}" ]; then
    echo "REFUSE CELL unset"
    return 9
  fi
  case "$VARIANT" in
    d1|d2-inflight|d2-oom) ;;
    *) echo "REFUSE VARIANT=$VARIANT"; return 9;;
  esac
  case "$CELL" in
    *runtime-37d8393*|*runtime-d9b7f60*) echo "REFUSE will not write historical cells"; return 9;;
  esac

  R6_RUNTIME_ROOT="${R6_RUNTIME_ROOT:-/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime}"
  cell_abs=$(readlink -f "$CELL" 2>/dev/null || python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$CELL")
  root_abs=$(readlink -f "$R6_RUNTIME_ROOT" 2>/dev/null || python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$R6_RUNTIME_ROOT")
  case "$cell_abs" in
    "$root_abs"/*) ;;
    *) echo "REFUSE CELL not under R6_RUNTIME_ROOT cell=$cell_abs root=$root_abs"; return 9;;
  esac

  if [[ ! "$CELL" =~ /runtime-([0-9a-f]{7,40})/ ]]; then
    echo "REFUSE runtime dir not anchored hex 7-40 got=$CELL"
    return 9
  fi
  run_sha="${BASH_REMATCH[1]}"

  case "$CELL" in
    */runtime-9369553/r6-d1|*/runtime-9369553/r6-d1-retry1|*/runtime-9369553/r6-d1-retry2|*/runtime-9369553/r6-d1-retry3|*/runtime-9369553/r6-d1-retry4|*/runtime-9369553/r6-d1-retry5|*/runtime-9369553/r6-d2-inflight|*/runtime-9369553/r6-d2-inflight-retry1)
      if [ "$VARIANT" = d2-oom ]; then
        echo "REFUSE D2-OOM on frozen APK 9369553"
        return 9
      fi
      EXPECT_VERSION="${EXPECT_VERSION:-1.03.01-9369553-15.09.26}"
      if [ "$VARIANT" != d1 ]; then
        EXPECT_D2_SHA256="${EXPECT_D2_SHA256:-ffce391049cc17c86eadd243f52f8b875e91bd842849c3ea5bc76b0bf63ab068}"
      fi
      ;;
    */runtime-9369553/*)
      echo "REFUSE no new cells under runtime-9369553 got=$CELL"
      return 9
      ;;
    */runtime-[0-9a-f]*/r6-d1|*/runtime-[0-9a-f]*/r6-d1-retry[0-9]*|*/runtime-[0-9a-f]*/r6-d2-inflight|*/runtime-[0-9a-f]*/r6-d2-inflight-retry[0-9]*|*/runtime-[0-9a-f]*/r6-d2-oom)
      if [ -z "${EXPECT_VERSION:-}" ]; then
        echo "REFUSE EXPECT_VERSION unset for new runtime dir"
        return 9
      fi
      EXPECT_D2_SHA256="${EXPECT_D2_SHA256:-fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86}"
      ;;
    *) echo "REFUSE CELL got=$CELL"; return 9;;
  esac

  if [[ ! "$EXPECT_VERSION" =~ ^1\.03\.01-([0-9a-f]{7,40})- ]]; then
    echo "REFUSE EXPECT_VERSION sha got=$EXPECT_VERSION"
    return 9
  fi
  ver_sha="${BASH_REMATCH[1]}"
  if [ "$run_sha" != "$ver_sha" ]; then
    echo "REFUSE runtime SHA vs EXPECT_VERSION run=$run_sha ver=$ver_sha"
    return 9
  fi

  case "$VARIANT" in
    d1) echo "$CELL" | grep -Eq '/r6-d1(-retry[0-9]+)?$' || { echo "CELL/VARIANT mismatch"; return 9; } ;;
    d2-inflight) echo "$CELL" | grep -Eq '/r6-d2-inflight(-retry[0-9]+)?$' || { echo "CELL/VARIANT mismatch"; return 9; } ;;
    d2-oom) echo "$CELL" | grep -q '/r6-d2-oom$' || { echo "CELL/VARIANT mismatch"; return 9; } ;;
  esac
  return 0
}
