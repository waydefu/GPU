#!/usr/bin/env bash
# R9 one-cell runner V2 — product dc94485, cell set frozen at 2 (F1, F2).
#
# V2 2026-09-22. Two changes, both forced by source proof, neither optional:
#   1. R9-COLD-2 is gone. Its expected fatal x-bump-unterminal needs a SECOND
#      lorieActivityConnected() with generation != 0, and no X process can reach one
#      (planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md). Passing CELL_ID=R9-COLD-2 is
#      now refused here, and judge-r9.py refuses it again independently.
#   2. The fixture is tests/r9/p_r9_boundary, not tests/r8/p_r8_lifecycle. R9 must
#      run with TERMUX_X11_R8_ARM UNSET (see the launch block below), and with R8
#      disarmed the LORIE-R8-TEST extension is never registered, so the R8 fixture
#      aborts on its first request. p_r9_boundary uses no extension at all: one
#      ordinary XCB PictOpOver composite is the entire Gate A direct trigger.
#
# Division of labour, deliberate: this script ORCHESTRATES and CAPTURES only. Every
# judgement-relevant inference lives in tests/r9/r9_evidence.py, which is unit-tested
# offline (20 tests). A runner that infers is a runner that cannot be tested without
# a device, and R8 spent nine defects learning that.
#
# Environment-driven, no flags, same shape as the R8 runner:
#   CELL_ID  R9-F1 | R9-F2
#   EVIDENCE must NOT already exist
#   SERIAL   required unless VALIDATE_ONLY=1
#   VALIDATE_ONLY=1  zero device mutation, exits before SERIAL is even read
#
# exit 3 = R9_BLOCKED (attempt NOT consumed)   exit 2 = R9_INVALID   else judge rc
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=/root/projects/GPU加速
R9=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/r9
R8=$ROOT/src/f8-ahb-gatea-r7-p1-arm/tests/r8
ROOT_HARNESS=$ROOT/evidence/session/gate-a-a1/p2-r3-terminal-runtime
RUN_NORESET=$ROOT/evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3-noreset.py
SPEC=$R9/r9-lifecycle-cell-spec.json
JUDGE=$R9/judge-r9.py
DERIVE=$R9/r9_evidence.py
COLLECT=$R8/collect-r8.py
MANIFEST=$ROOT/evidence/session/gate-a-a1/p2-r8-runtime/runtime-dc94485/r8-runtime-tooling-manifest-dc94485.json
FIXTURE=/tmp/p_r9_boundary
FIXTURE_SRC=$R9/p_r9_boundary.c
TADB=/data/data/com.termux/files/usr/bin/adb
# The X server runs HERE, in the PRoot rootfs, not on the device side of adb, so
# its dump sink is a LOCAL path. Reading it with `adb shell cat` reaches the
# device's own Termux tmp and finds nothing: every R9 attempt before this fix
# captured an empty gatea-ring.txt. (The R8 runner always used a local cp.)
RING=/data/data/com.termux/files/usr/tmp/gatea-ring.txt
SUMMARY=/data/data/com.termux/files/usr/tmp/gatea-summary.txt

EXPECT_HEAD=dc94485a7ef4f74cada36ea3c1d35d0aa0f48693
EXPECT_VERSION=1.03.01-dc94485-22.09.26
EXPECT_PACKAGE=com.waydefu.x11gpu
EXPECT_BUILD_ID=bc993eee0c4420b9721801b06d7183ed53de487b
EXPECT_APK_SHA256=1bd8bef0909249737ea43acf0a35f3c995d941e1badbfcf370e5cd854f4bb8a3
EXPECT_SIGNER=b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1
EXPECT_FIXTURE_SHA=c5ca4786a21f84a196a254c1a9144ffdb9d5b89bc56ed19e155249bbe9624694
EXPECT_FIXTURE_SRC_SHA=b2103b23696ce3b9c5b267605246ccc971847bcf1f5cf3d41287810534ee2531
EXPECT_CI=35673085569

refuse() { echo "R9_BLOCKED $*"; exit 3; }
invalid() { echo "R9_INVALID $*"; exit 2; }

VALIDATE_ONLY="${VALIDATE_ONLY:-0}"
CELL_ID="${CELL_ID:-}"
EVIDENCE="${EVIDENCE:-}"
[ -n "$CELL_ID" ] || refuse "CELL_ID"
[ -n "$EVIDENCE" ] || refuse "EVIDENCE"
case "$CELL_ID" in
  R9-F1|R9-F2) ;;
  R9-COLD-2|R9-COLD-1|R9-COLD-3|R9-WARM-1|R9-WARM-2|R9-WARM-3)
    refuse "cell_removed_source_proven_not_constructible $CELL_ID";;
  *) refuse "bad_cell $CELL_ID";;
esac

# arming is by NAME, never by number: gateATestCellFromName returns 0 for anything
# unknown and the X server then fatal-halts with x-test-fault-env before the cell
# runs, spending an attempt on nothing.
FAULT_NAME=""
case "$CELL_ID" in
  R9-F1)     FAULT_NAME=stale-ready-replay;;
  R9-F2)     FAULT_NAME="";;
esac

if [ "$VALIDATE_ONLY" = 1 ]; then
  echo "R9_LIVE_RUNNER_DC94485_V2_VALIDATE_ONLY $CELL_ID fault=${FAULT_NAME:-none}"
  exit 0
fi

[ -n "${SERIAL:-}" ] || refuse "SERIAL"
[ -e "$EVIDENCE" ] && refuse "evidence_exists $EVIDENCE"
for f in "$SPEC" "$JUDGE" "$DERIVE" "$COLLECT" "$MANIFEST" "$RUN_NORESET"; do
  [ -f "$f" ] || refuse "missing_tool $f"
done

export CELL="$EVIDENCE"
# shellcheck source=harness-lib.sh
source "$ROOT_HARNESS/harness-lib.sh"

ADB get-state >/dev/null 2>&1 || refuse "ADB_DISCONNECTED"
mkdir -p "$EVIDENCE"

X3=""
r9_cleanup() {
  if [ -n "${X3:-}" ] && [ -d "/proc/$X3" ]; then
    local cmd; cmd=$(tr '\0' ' ' < "/proc/$X3/cmdline" 2>/dev/null || true)
    case "$cmd" in
      "termux-x11gpu com.waydefu.x11gpu :3"*) kill -TERM "$X3" 2>/dev/null || true;;
    esac
  fi
  ADB shell am force-stop "$EXPECT_PACKAGE" >/dev/null 2>&1 || true
}
trap 'cleanup; r9_cleanup' EXIT

# stable_json lives in the R8 runner, not harness-lib. Copied verbatim so the
# Stable-unchanged proof is byte-for-byte the same one R7/R8 used.
stable_json() {
  local out=$1 pid cmd
  pid=$(stabpid) || refuse "stable_pid"
  cmd=$(stab_cmd)
  echo "$cmd" | grep -q '^termux-x11 com.termux.x11 :1' || refuse "stable_cmd"
  ADB shell dumpsys package com.termux.x11 > "$out.raw" || true
  python3 - "$out" "$out.raw" "$pid" "$cmd" <<'PYEOF'
import json,re,sys
text=open(sys.argv[2],encoding="utf-8",errors="replace").read()
vn=re.search(r"versionName=(\S+)", text)
vc=re.search(r"versionCode=(\d+)", text)
lu=re.search(r"lastUpdateTime=(.+)", text)
json.dump({
  "pid": int(sys.argv[3]), "cmdline": sys.argv[4].strip(),
  "versionName": vn.group(1) if vn else None,
  "versionCode": int(vc.group(1)) if vc else None,
  "lastUpdateTime": lu.group(1).strip() if lu else None,
}, open(sys.argv[1],"w"), indent=2)
print("stable_pid", sys.argv[3])
PYEOF
}

# ---------------------------------------------------------------- preflight ----
GOT_FIX=$(sha256sum "$FIXTURE" | awk '{print $1}')
[ "$GOT_FIX" = "$EXPECT_FIXTURE_SHA" ] || refuse "fixture_sha $GOT_FIX"
GOT_SRC=$(sha256sum "$FIXTURE_SRC" | awk '{print $1}')
[ "$GOT_SRC" = "$EXPECT_FIXTURE_SRC_SHA" ] || refuse "fixture_src_sha $GOT_SRC"
printf 'binary %s\nsource %s\n' "$GOT_FIX" "$GOT_SRC" > "$EVIDENCE/fixture.sha256.txt"
cp "$MANIFEST" "$EVIDENCE/manifest.json"
python3 - "$EVIDENCE" "$EXPECT_HEAD" "$EXPECT_APK_SHA256" "$EXPECT_BUILD_ID" "$EXPECT_SIGNER" <<'PY'
import json, sys
from pathlib import Path
d = Path(sys.argv[1])
(d / "artifact-binding.json").write_text(json.dumps({
    "source_sha": sys.argv[2], "apk_sha256": sys.argv[3],
    "build_id": sys.argv[4], "signer": sys.argv[5],
}, indent=2) + "\n")
PY

ADB shell dumpsys package "$EXPECT_PACKAGE" | grep -E 'versionName=' | head -2 \
  | tee "$EVIDENCE/experimental-package-pre.txt"
grep -q "versionName=$EXPECT_VERSION" "$EVIDENCE/experimental-package-pre.txt" \
  || refuse "version_mismatch"
INSTALLED_APK=$(ADB shell pm path "$EXPECT_PACKAGE" | tr -d '\r' | sed -n 's/^package://p' | head -1)
[ -n "$INSTALLED_APK" ] || refuse "apk_path_unresolved"
GOT_APK=$(ADB shell sha256sum "$INSTALLED_APK" | tr -d '\r' | awk '{print $1}')
echo "installed_apk_sha256=$GOT_APK" | tee "$EVIDENCE/installed-apk.sha256.txt"
[ "$GOT_APK" = "$EXPECT_APK_SHA256" ] || refuse "apk_sha256_mismatch got=$GOT_APK"

stable_json "$EVIDENCE/stable-before.json"
if x3pid >/dev/null 2>&1; then refuse "x3_already_running"; fi

# Both files are rewritten whole by lorieGateADumpSummary and survive process death,
# so anything left over is the PREVIOUS cell's. Remove them, exactly as the R8 runner
# does, or a cell that never dumps would be judged on its predecessor's ring.
rm -f "$SUMMARY" "$RING" || true
SINCE=$(date '+%m-%d %H:%M:%S.000')
echo "logcat_since=$SINCE" | tee "$EVIDENCE/logcat-since.txt"
LOGCAT_PID=$(start_logcat "$EVIDENCE/raw-logcat.txt" "$SINCE")
verify_logcat_pid "$LOGCAT_PID"

# ------------------------------------------------------------------ launch ----
export TERMUX_X11_GATEA_PROTO=1
export TERMUX_X11_GATEA_TELEMETRY=1
# TERMUX_X11_R8_ARM / _CASE are deliberately NOT set for fault-driven cells.
# parseArm() in lorie_r8_obs.c hard-codes the allowed (case, fault) pairs:
#     R8-P1 <-> destroy-while-gpu-owned
#     R8-P2 <-> close-while-lease
#     any other case + ANY fault -> r8EnvFatal -> x-r8-env halt at startup
# R9's faults are neither, so arming R8 observation kills X before the cell runs
# (measured: r9-cold-2/attempt-01, GATEA_FATAL_HALT what=x-r8-env reason=5).
# Leaving R8_ARM unset is safe and sufficient:
#   - parseArm returns 0 immediately without setting r8EnvFatal, so no halt
#   - the test fault arms independently; it needs PROTO + TELEMETRY + a valid
#     NAME + TEST_ARM=1, and never R8_ARM (InitOutput.c)
#   - the armed guard in lorieR8ObsTuple is `role[0] == 'x'` ONLY, so renderer
#     records - including D-02's epoch records - still flow
# The cost is that the X-side R8_OBS stream is absent. judge-r9.py reads no x rows
# for any of the three cells, the halt token comes from logcat directly, and the
# ring and summary come from files, so nothing the judge needs is lost.
if [ -n "$FAULT_NAME" ]; then
  export TERMUX_X11_GATEA_TEST_FAULT="$FAULT_NAME"
  export TERMUX_X11_GATEA_TEST_ARM=1
else
  # no fault: the R8 pairing rule does not apply, so the full X-side stream is
  # available and worth having
  export TERMUX_X11_R8_ARM=1
  export TERMUX_X11_R8_CASE=R8-C1
fi
env | sort > "$EVIDENCE/env.txt"

python3 "$RUN_NORESET" | tee "$EVIDENCE/start-x3.out"
for _ in $(seq 1 40); do X3=$(x3pid) && break || sleep 0.5; done
[ -n "$X3" ] || refuse "x3_missing"
echo "x3_pid=$X3" | tee "$EVIDENCE/x3-pid.txt"
save_x_identity "$X3" "$EVIDENCE"
tr '\0' ' ' < "/proc/$X3/cmdline" | grep -q -- '-noreset' \
  || refuse "noreset_absent_in_cmdline"

snap() { # snap <tag>; captures the raw /proc stat lines the derivation parses
  cp "/proc/$X3/stat" "$EVIDENCE/x-stat-$1" 2>/dev/null || : > "$EVIDENCE/x-stat-$1"
  # `pidof` exits 1 when the process is gone, and `set -o pipefail` turns that into
  # a failed assignment, which `set -e` turns into an aborted run. R9-F1 halts X and
  # the Activity goes with it, so "gone" is the EXPECTED state at snap-after time:
  # the absence must be recorded, not fatal. (Measured: r9-f1/attempt-01 captured the
  # correct x-wrong-generation halt and was then lost here, before stable-after.json.)
  local ap; ap=$(ADB shell pidof "$EXPECT_PACKAGE" 2>/dev/null | tr -d '\r' | awk '{print $1}') || ap=""
  if [ -n "$ap" ]; then
    ADB shell cat "/proc/$ap/stat" 2>/dev/null | tr -d '\r' > "$EVIDENCE/act-stat-$1" || : > "$EVIDENCE/act-stat-$1"
  else
    : > "$EVIDENCE/act-stat-$1"
  fi
  ls "/proc/$X3/fd" 2>/dev/null | wc -l > "$EVIDENCE/x-fdcount-$1" || echo 0 > "$EVIDENCE/x-fdcount-$1"
  # Q9-F1 needs the TABLE, not just its size: getXConnection neither closes nor
  # unregisters the previous conn_fd, so a rebind can leave two registered and
  # nothing in the product reports it. The count alone cannot answer that.
  ls -l "/proc/$X3/fd" 2>/dev/null > "$EVIDENCE/x-fdlist-$1" || : > "$EVIDENCE/x-fdlist-$1"
}

ADB shell 'am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity' \
  | tee "$EVIDENCE/am-start.out"
sleep 3
snap before

# ------------------------------------------------------------------ client ----
export DISPLAY=:3
set +e
timeout 40 "$FIXTURE" --display :3 --cell "$CELL_ID" \
  --client-log "$EVIDENCE/fixture.jsonl" \
  > "$EVIDENCE/fixture.stdout" 2>"$EVIDENCE/fixture.stderr"
FIX_RC=$?
set -e
echo "FIXTURE_EXIT=$FIX_RC" | tee "$EVIDENCE/fixture-exit.txt"

X_ALIVE_AFTER=unknown
# F1 is EXPECTED to halt X (x-wrong-generation); F2 is expected to leave it running.
# Record which, as an observation, and never as a verdict: judge-r9.py takes the halt
# identity from logcat, not from this line.
sleep 2
if [ -d "/proc/$X3" ]; then X_ALIVE_AFTER=true; else X_ALIVE_AFTER=false; fi
echo "x_alive_after_cell=$X_ALIVE_AFTER" | tee "$EVIDENCE/x-survival.txt"
snap after

# ---------------------------------------------- why there is no clean close ----
# An earlier V2 draft ended R9-F2 with `kill -TERM $X3`, to force
# lorieGateADumpSummary(where=x-close-screen) and so obtain the c25/c26 registry
# counters that empty_registry_both_sides seemed to need. Measured on
# r9-f2/attempt-01: it does not work and it actively harms the cell.
#   * SIGTERM does not reach CloseScreen in this build. X's last line was at
#     14:48:14.928 and the next Gate A line is the RENDERER's, so there was no
#     X_CLOSE_ENTER, no "Server stopped", no dump - the process was simply killed.
#   * It made the renderer fatal: GATEA_FATAL_HALT what=r-hup reason=6, which
#     judge_f2 correctly reads as UNEXPECTED_FATAL_IN_FRESH_SESSION.
# The counters were never the right source anyway. The live telemetry stream carries
# REGISTER_READY (event 1) and UNREGISTER_ACK (event 25) per buffer id and per role,
# so "registry empty on both sides" is read directly from what this session did,
# with no dump and no shutdown. r9_evidence.registry_state() does that.

# ------------------------------------------------------------------ freeze ----
# lorieGateADumpSummary writes BOTH files, and it only runs on a fatal, a clean
# close or a terminate. A cell that leaves X healthy (R9-F2) therefore produces
# neither, and that is correct, not a capture failure: the same events are in logcat
# live under the gatea-telemetry tag, which is also immune to ring overflow.
# judge-r9.ring_events() unions the two sources.
if [ -f "$SUMMARY" ]; then cp -a "$SUMMARY" "$EVIDENCE/gatea-summary.txt"; else : > "$EVIDENCE/gatea-summary.txt"; fi
if [ -f "$RING" ]; then cp -a "$RING" "$EVIDENCE/gatea-ring.txt"; else : > "$EVIDENCE/gatea-ring.txt"; fi
sleep 1
stop_logcat "$LOGCAT_PID" || true
LOGCAT_PID=""
cat "$EVIDENCE/raw-logcat.txt" "$EVIDENCE/gatea-ring.txt" "$EVIDENCE/gatea-summary.txt" \
  > "$EVIDENCE/collect-input.txt" 2>/dev/null || true
python3 "$COLLECT" --raw "$EVIDENCE/collect-input.txt" \
  --out-x "$EVIDENCE/x-observations.jsonl" \
  --out-r "$EVIDENCE/renderer-observations.jsonl" \
  --completeness "$EVIDENCE/completeness.json"
stable_json "$EVIDENCE/stable-after.json"

# F1's PASS is not necessarily attempt-01: an attempt consumed INVALID keeps its
# number and the next one takes the next (policy.frozen_attempt_policy). Resolve the
# attempt that actually carries a PASS verdict, and use that SAME directory for both
# the precondition and the "before" half of the F1 -> F2 identity boundary, so the
# two can never disagree about which run F2 is measured against.
PREV=""
if [ "$CELL_ID" = "R9-F2" ]; then
  PREV=$(python3 - "$EVIDENCE" <<'PY'
import json, sys
from pathlib import Path
d = Path(sys.argv[1])
hit = ""
base = d.parent.parent / "r9-f1"
for a in (sorted(base.glob("attempt-*")) if base.is_dir() else []):
    j = a / "judge.json"
    if not j.is_file():
        continue
    try:
        if json.loads(j.read_text()).get("verdict") == "R9_PASS":
            hit = str(a)          # last PASS wins; there should be exactly one
    except json.JSONDecodeError:
        continue
print(hit)
PY
)
  python3 - "$EVIDENCE" "$PREV" <<'PY'
import json, sys
from pathlib import Path
d, prev = Path(sys.argv[1]), sys.argv[2]
# §8.8: F2 is BLOCKED without F1's expected fatal, never INVALID or FAIL, and
# manufacturing another fatal to satisfy it is forbidden. The verdict is read from
# F1's own judge.json; this script never looks at a logcat.
ok = False
src = prev or "NO_PASSING_R9-F1_ATTEMPT"
if prev:
    j = json.loads((Path(prev) / "judge.json").read_text())
    ok = j.get("verdict") == "R9_PASS"
(d / "f1-precondition.json").write_text(
    json.dumps({"f1_expected_fatal_observed": ok, "source": src}, indent=2) + "\n")
PY
fi

# ------------------------------------------------------------------ derive ----
# F2's identity boundary is the F1 -> F2 boundary, so its "before" half must come
# from F1's OWN captures. F1's after-snapshot is empty by design (X halted), so the
# half that is passed is F1's before-snapshot: a real capture of F1's live session.
PREV_ARGS=()
if [ "$CELL_ID" = "R9-F2" ] && [ -n "$PREV" ]; then
  PREV_ARGS=(--prev-x-stat "$PREV/x-stat-before"
             --prev-act-stat "$PREV/act-stat-before"
             --prev-x-fdlist "$PREV/x-fdlist-before"
             --prev-raw "$PREV/raw-logcat.txt")
  echo "prev_evidence=$PREV" | tee "$EVIDENCE/prev-evidence.txt"
fi
python3 "$DERIVE" --evidence "$EVIDENCE" --cell "$CELL_ID" "${PREV_ARGS[@]}" \
  --x-stat-before "$EVIDENCE/x-stat-before" --x-stat-after "$EVIDENCE/x-stat-after" \
  --x-fdlist-before "$EVIDENCE/x-fdlist-before" --x-fdlist-after "$EVIDENCE/x-fdlist-after" \
  --act-stat-before "$EVIDENCE/act-stat-before" --act-stat-after "$EVIDENCE/act-stat-after" \
  --x-alive-after "$X_ALIVE_AFTER" --fd-had-prev unknown \
  | tee "$EVIDENCE/derive.out"

# ------------------------------------------------------------------- judge ----
set +e
python3 "$JUDGE" --manifest "$EVIDENCE/manifest.json" --spec "$SPEC" \
  --evidence "$EVIDENCE" --cell "$CELL_ID" --output "$EVIDENCE/judge.json" \
  | tee "$EVIDENCE/judge.stdout"
JUDGE_RC=${PIPESTATUS[0]}
set -e
echo "$JUDGE_RC" > "$EVIDENCE/judge.rc"
exit "$JUDGE_RC"
