#!/data/data/com.termux/files/usr/bin/bash
# Stage 7.5 4-way daily pilot: start the governed native daemon once (no idle exit).
# Relays are registered without --auto-start; while this daemon is down they run tools in PRoot.
# Rollback: f8_hybrid2_ctl.py disable (fallback only), or remove the client registration.
set -euo pipefail
export PATH=/data/data/com.termux/files/usr/bin
export HOME=/data/data/com.termux/files/home
export TMPDIR=/data/data/com.termux/files/usr/tmp
export PYTHONDONTWRITEBYTECODE=1
T=${0%/*}
R=$HOME/.f8hyb2
export F8_HYBRID2_BUDGET_DIR=$HOME/.f8hyb2-budget
export F8_HYBRID2_TRUSTED_GIT_ROOTS="$(cat "$T/trusted-git-roots.json")"
[ "$(awk '/^TracerPid:/{print $2}' /proc/self/status)" = 0 ] || { echo "traced: refuse" >&2; exit 5; }
(cd "$T" && sha256sum -c --quiet DEPLOYED.sha256)
[ -f "$F8_HYBRID2_BUDGET_DIR/profile" ] || { echo "budget dir not initialised" >&2; exit 6; }
[ ! -e "$R/disabled.flag" ] || { echo "disabled.flag present" >&2; exit 7; }
mkdir -p "$R/hhome" "$R/htmp"; chmod 700 "$R"
if python3 "$T/f8_hybrid2_ctl.py" --dir "$R" probe >/dev/null 2>&1; then echo already-running; exit 0; fi
rm -f "$R/ready"
setsid -f python3 "$T/f8_hybrid2_daemon.py" --socket "$R/m.sock" --pidfile "$R/d.pid" --ready "$R/ready" \
  --log "$R/audit.jsonl" --home "$R/hhome" --tmp "$R/htmp" --git-bin "$PATH/git" \
  --max-clients 4 --max-inflight 8 --idle-timeout 0 >>"$R/daemon.out" 2>&1 </dev/null
for _ in $(seq 100); do [ -e "$R/ready" ] && { echo "started pid=$(cat "$R/d.pid")"; exit 0; }; sleep 0.1; done
echo "start-timeout" >&2; tail -5 "$R/daemon.out" >&2; exit 8
