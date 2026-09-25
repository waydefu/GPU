#!/usr/bin/env bash
# XFCE-NOTEL-01 series (evidence/session/xfce-v6/XFCE-NOTEL-01-FREEZE.md), derived from series-v6.sh (Part B).
# One command runs, in order:
#   precheck: Cursor / Hermes / ChatGPT not running (freeze section 4 item 2), else refuse
#   preflight-01 (MODE=preflight, C env, TELEMETRY=0)  -> anything but PROBE_SENSITIVE stops here
#   C GT CT | GT CT C | CT C GT                          -> runner V5 with TELEMETRY per group, + the same probes
#   replacements for INVALID captures (at most 2, same group, in the order they failed)   (no G0 in this run)
#   series.json + notel-judge.json (tests/xfce_notel/notel_judge.py series)
# Runner rc: 0 captured, 2 INVALID (kept, may be replaced), 3 BLOCKED / 4 X3 startup crash / 5 mem guard
# -> the series STOPS (no silent retry; rc 4 is the ART-JIT class: fail closed).
# Before every run it waits (max 10 min) for MemAvailable >= 4600 MB held 20 s.
#   SERIAL  live-discovered host:port on lane 5038      OUT  new directory (default runtime-f592241-v6)
set -uo pipefail
HERE=/root/projects/GPU加速/evidence/session/xfce-v6
V6=/root/projects/GPU加速/src/f8-ahb-exa-async/tests/xfce_v6
PGA=/root/projects/GPU加速/src/f8-ahb-exa-async/tests/pga
RUNNER=$HERE/run-xfce-v5-notel.sh
NOTEL=/root/projects/GPU加速/src/f8-ahb-exa-async/tests/xfce_notel
RTT=/root/build/xfce-v6/x_rtt2.glibc
: "${SERIAL:?}"
OUT=${OUT:-$HERE/runtime-f592241-notel}
[ -e "$OUT" ] && { echo "SERIES_REFUSE out_exists $OUT"; exit 3; }
mkdir -p "$OUT"
sha256sum "$0" "$RUNNER" "$V6"/*.py "$V6"/*.sh "$NOTEL"/*.py "$PGA/rca_sampler.py" "$PGA/rca_report.py" > "$OUT/series-tools.sha256.txt"
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
  unset TERMUX_X11_EXA_ASYNC TERMUX_X11_DISABLE_EXA_GPU TERMUX_X11_GPU_MIN_PIXELS TERMUX_X11_GATEA_TELEMETRY
  case "$1" in
    C) export TERMUX_X11_DISABLE_EXA_GPU=1 TELEMETRY=0;;
    GT) export TERMUX_X11_GPU_MIN_PIXELS=4097 TELEMETRY=0;;     # the default, stated explicitly (as f592241)
    CT) export TERMUX_X11_DISABLE_EXA_GPU=1 TELEMETRY=1;;
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

# ---- precheck (freeze section 4 item 2): no Cursor / Hermes / ChatGPT
python3 -c "import sys, json; sys.path.insert(0, '$V6'); import daily_sampler_v2 as V
m = V.main_processes(); json.dump(m, open('$OUT/precheck-apps.json', 'w')); sys.exit(1 if any(k in m for k in ('cursor', 'hermes', 'chatgpt')) else 0)" \
  || { say "SERIES_REFUSE apps running $(cat "$OUT/precheck-apps.json")"; exit 3; }

# ---- preflight (freeze 5.2 + section 9 deviation 1)
PF=$OUT/preflight-01
mem_wait || stop_series "memory before preflight"
set_group C
say "START preflight-01"
MODE=preflight VARIANT=C0 SERIAL=$SERIAL EVIDENCE=$PF bash "$RUNNER" > "$PF.runner.log" 2>&1
RC=$?
[ -d "$PF" ] && echo "rc=$RC" > "$PF/runner-exit.txt"
say "PREFLIGHT rc=$RC $(tail -1 "$PF.runner.log")"
python3 "$NOTEL/notel_judge.py" preflight "$PF" > "$PF/judge.json" 2>&1
PV=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['verdict'])" "$PF/judge.json" 2>/dev/null || echo JUDGE_ERROR)
say "PREFLIGHT_VERDICT $PV"
[ "$PV" = PROBE_SENSITIVE ] || stop_series "preflight $PV"
EXPECT_ROOT=$(sed -n 's/^x_root=\([0-9]*x[0-9]*\) .*/\1/p' "$PF/x-root.txt")
[ -n "$EXPECT_ROOT" ] || stop_series "preflight recorded no X root"
say "EXPECT_ROOT $EXPECT_ROOT"

# ---- judged captures, frozen order
declare -A K=([C]=0 [GT]=0 [CT]=0)
for g in C GT CT GT CT C CT C GT; do K[$g]=$((K[$g] + 1)); capture "notel-${g,,}-0${K[$g]}" "$g"; done

# ---- replacements: at most 2, only for INVALID C/GT captures, in the order they failed
R=0
for c in "${CAPS[@]}"; do
  read -r name group dir <<< "$c"
  [ "$R" -ge 2 ] && break
  v=$(python3 "$NOTEL/notel_judge.py" capture "$dir" "$group" | python3 -c "import json,sys;print(json.load(sys.stdin)['valid'])")
  if [ "$v" != True ]; then R=$((R + 1)); say "INVALID $name -> replacement r$R"; capture "notel-${group,,}-r$R" "$group"; fi
done

set_group C; unset TERMUX_X11_DISABLE_EXA_GPU TELEMETRY
write_series
python3 "$NOTEL/notel_judge.py" series "$PF" "$OUT/series.json" > "$OUT/notel-judge.json" 2>&1
say "NOTEL $(python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(d.get('verdict'),'Q1',d.get('Q1'),d.get('Q1_x3'),'N1',d.get('N1'),'N2',d.get('N2_p50'),d.get('N2_p99'),'N3',d.get('N3'))" "$OUT/notel-judge.json" 2>/dev/null)"
echo XFCE_NOTEL_SERIES_DONE
