#!/usr/bin/env bash
# XFCE-V6-BASELINE-01 Part B series (freeze sections 5 and 9). One command runs, in order:
#   preflight-01 (MODE=preflight, C env)  -> judged at once; anything but PROBE_SENSITIVE stops here
#   C GT GT C C GT                        -> each with rca_sampler.py (x_rtt2.glibc) + v6_probes.py
#   replacements for INVALID C/GT captures (at most 2, in the order they failed)  -> G0 once
#   series.json + part-b-judge.json (xfce_v6_judge.py part-b)
# Runner rc: 0 captured, 2 INVALID (kept, may be replaced), 3 BLOCKED / 4 X3 startup crash / 5 mem guard
# -> the series STOPS (no silent retry; rc 4 is the ART-JIT class: fail closed).
# Before every run it waits (max 10 min) for MemAvailable >= 4600 MB held 20 s.
#   SERIAL  live-discovered host:port on lane 5038      OUT  new directory (default runtime-f592241-v6)
set -uo pipefail
HERE=/root/projects/GPU加速/evidence/session/xfce-v6
V6=/root/projects/GPU加速/src/f8-ahb-exa-async/tests/xfce_v6
PGA=/root/projects/GPU加速/src/f8-ahb-exa-async/tests/pga
RUNNER=$HERE/run-xfce-v4-v6.sh
RTT=/root/build/xfce-v6/x_rtt2.glibc
: "${SERIAL:?}"
OUT=${OUT:-$HERE/runtime-f592241-v6}
[ -e "$OUT" ] && { echo "SERIES_REFUSE out_exists $OUT"; exit 3; }
mkdir -p "$OUT"
sha256sum "$0" "$RUNNER" "$V6"/*.py "$V6"/*.sh "$PGA/rca_sampler.py" "$PGA/rca_report.py" > "$OUT/series-tools.sha256.txt"
LOG=$OUT/series.log
say() { echo "$(date +%T) $*" | tee -a "$LOG"; }
CAPS=()   # "name group dir"

mem_wait() {
  local ok=0 i m
  for i in $(seq 1 600); do
    m=$(awk '/^MemAvailable/{print int($2/1024)}' /proc/meminfo)
    if [ "$m" -ge 4600 ]; then ok=$((ok + 1)); [ "$ok" -ge 20 ] && return 0; else ok=0; fi
    sleep 1
  done
  return 1
}
set_group() {
  unset TERMUX_X11_EXA_ASYNC TERMUX_X11_DISABLE_EXA_GPU TERMUX_X11_GPU_MIN_PIXELS
  case "$1" in
    C) export TERMUX_X11_DISABLE_EXA_GPU=1;;
    GT) export TERMUX_X11_GPU_MIN_PIXELS=4097;;     # the default, stated explicitly (as f592241)
    G0) export TERMUX_X11_GPU_MIN_PIXELS=0;;
    *) say "bad group $1"; exit 3;;
  esac
}
stop_series() { say "SERIES_STOP $*"; write_series; exit 3; }
write_series() {
  python3 - "$OUT/series.json" "${CAPS[@]}" <<'PY'
import json, sys
caps = [dict(zip(("name", "group", "dir"), c.split(" ", 2))) for c in sys.argv[2:]]
json.dump({"captures": caps}, open(sys.argv[1], "w"), indent=2)
PY
}
capture() {   # capture <name> <group>  -> sets RC
  local name=$1 group=$2 ev=$OUT/$1
  mem_wait || stop_series "memory never held 4600 MB for 20 s before $name"
  set_group "$group"
  python3 "$PGA/rca_sampler.py" --out "$ev.rca" --x-rtt "$RTT" --duration 900 > "$ev.rca.log" 2>&1 &
  local sp=$!
  python3 "$V6/v6_probes.py" --out "$ev.v6" --duration 900 > "$ev.v6.log" 2>&1 &
  local vp=$!
  say "START $name group=$group"
  MODE=capture VARIANT=C0 SERIAL=$SERIAL EVIDENCE=$ev EXPECT_ROOT=$EXPECT_ROOT bash "$RUNNER" > "$ev.runner.log" 2>&1
  RC=$?
  [ -d "$ev" ] && echo "rc=$RC" > "$ev/runner-exit.txt"
  wait "$sp"; wait "$vp"
  say "CAPTURE $name rc=$RC $(tail -1 "$ev.runner.log")"
  CAPS+=("$name $group $ev")
  case "$RC" in 0|2) ;; *) stop_series "runner rc=$RC at $name";; esac
}

# ---- preflight (freeze 5.2 + section 9 deviation 1)
PF=$OUT/preflight-01
mem_wait || stop_series "memory before preflight"
set_group C
say "START preflight-01"
MODE=preflight VARIANT=C0 SERIAL=$SERIAL EVIDENCE=$PF bash "$RUNNER" > "$PF.runner.log" 2>&1
RC=$?
[ -d "$PF" ] && echo "rc=$RC" > "$PF/runner-exit.txt"
say "PREFLIGHT rc=$RC $(tail -1 "$PF.runner.log")"
python3 "$V6/xfce_v6_judge.py" preflight "$PF" > "$PF/judge.json" 2>&1
PV=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['verdict'])" "$PF/judge.json" 2>/dev/null || echo JUDGE_ERROR)
say "PREFLIGHT_VERDICT $PV"
[ "$PV" = PROBE_SENSITIVE ] || stop_series "preflight $PV"
EXPECT_ROOT=$(sed -n 's/^x_root=\([0-9]*x[0-9]*\) .*/\1/p' "$PF/x-root.txt")
[ -n "$EXPECT_ROOT" ] || stop_series "preflight recorded no X root"
say "EXPECT_ROOT $EXPECT_ROOT"

# ---- judged captures, frozen order
declare -A K=([C]=0 [GT]=0)
for g in C GT GT C C GT; do K[$g]=$((K[$g] + 1)); capture "xfce-c0-${g,,}-0${K[$g]}" "$g"; done

# ---- replacements: at most 2, only for INVALID C/GT captures, in the order they failed
R=0
for c in "${CAPS[@]}"; do
  read -r name group dir <<< "$c"
  [ "$R" -ge 2 ] && break
  v=$(python3 "$V6/xfce_v6_judge.py" capture-b "$dir" "$group" | python3 -c "import json,sys;print(json.load(sys.stdin)['valid'])")
  if [ "$v" != True ]; then R=$((R + 1)); say "INVALID $name -> replacement r$R"; capture "xfce-c0-${group,,}-r$R" "$group"; fi
done

# ---- G0 (descriptive), last
capture "xfce-c0-g0-01" G0
set_group C; unset TERMUX_X11_DISABLE_EXA_GPU
write_series
python3 "$V6/xfce_v6_judge.py" part-b "$PF" "$OUT/series.json" > "$OUT/part-b-judge.json" 2>&1
say "PART_B $(python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(d.get('verdict'),d.get('B1'),d.get('B2_p50'),d.get('B2_p99'),d.get('B3'))" "$OUT/part-b-judge.json" 2>/dev/null)"
echo XFCE_V6_SERIES_DONE
