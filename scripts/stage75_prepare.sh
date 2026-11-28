#!/usr/bin/env bash
# Build one isolated Stage 7.5 tiered run directory (PRoot side). Usage: stage75_prepare.sh MODE PARENT_DIR
set -euo pipefail
src=$(cd "$(dirname "$0")" && pwd)
mode=$1
parent=$2
run=$(mktemp -d "$parent/s75g-m$mode.XXXXXX")
mkdir -p "$run/scripts" "$run/r" "$run/h" "$run/ws2/small" "$run/ws2/tree"
cp "$src"/f8_hybrid2_*.py "$src"/stage75_*.py "$src"/test_f8_hybrid2.py "$run/scripts/"
(cd "$run/scripts" && sha256sum -- *.py > ../scripts.sha256)
git -C "$src/.." rev-parse HEAD > "$run/candidate"
git -C "$src/.." status --porcelain -- scripts > "$run/candidate.dirty"
python3 -B - "$run/ws2" <<'PY'
import json, sys
from pathlib import Path
ws = Path(sys.argv[1])
(ws / "sample.txt").write_text("needle test fixture\n")
with (ws / "sample.jsonl").open("w") as f:
    for i in range(4100):
        f.write(json.dumps({"seq": i, "phase": "normal-cache-read", "target": "stage75", "value": "stable-input-" * 21}) + "\n")
with (ws / "corpus.txt").open("w") as f:
    for i in range(6000):
        f.write(f"needle {i:04d} " + "ordinary-text-result-" * 12 + "\n")
for i in range(20):
    (ws / "small" / f"f{i:02d}.txt").write_text(f"small {i}\n")
for d in range(24):
    sub = ws / "tree" / f"d{d:02d}"
    sub.mkdir()
    for i in range(500):
        (sub / f"f{i:03d}").touch()
PY
# Stage 7.6: the fixture repo is written by PRoot git, so its objects are link2symlink links (F13 path).
git -C "$run/ws2" init -q
git -C "$run/ws2" add -- sample.jsonl sample.txt corpus.txt
git -C "$run/ws2" -c user.name=Fixture -c user.email=fixture@example.invalid commit -qm fixture
l2s=$(find "$run/ws2/.git/objects" -type l | wc -l)
printf '%s\n' "$l2s" > "$run/fixture-l2s-links"
[ "$l2s" -gt 0 ] || { echo "fixture has no l2s objects" >&2; exit 1; }
python3 -B "$run/scripts/f8_hybrid2_budget.py" init "$run/budget" --mode "$mode" > "$run/budget-init.json"
cat > "$run/run-daemon" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -eu
export PATH=/data/data/com.termux/files/usr/bin
export PYTHONDONTWRITEBYTECODE=1
export F8_HYBRID2_TRUSTED_GIT_ROOTS='["/fixture"]'
run=${0%/*}
export F8_HYBRID2_BUDGET_DIR="$run/budget"
grep -E '^(Uid|TracerPid):' /proc/self/status
(cd "$run/scripts" && sha256sum -c --quiet ../scripts.sha256)
if [ ! -d "$run/ws2/.git" ]; then
  git -C "$run/ws2" init -q
  git -C "$run/ws2" add -- sample.jsonl sample.txt corpus.txt
  git -C "$run/ws2" -c user.name=Fixture -c user.email=fixture@example.invalid commit -qm fixture
fi
exec python3 "$run/scripts/f8_hybrid2_daemon.py" --socket "$run/r/m.sock" --pidfile "$run/r/d.pid" --ready "$run/r/ready" \
  --log "$run/r/audit.jsonl" --map "/fixture=$run/ws2" --home "$run/h" --tmp "$run/r" --git-bin "$PATH/git" \
  --max-clients 8 --max-inflight 8
EOF
cat > "$run/run-native" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Native regression suite and governed-engine envelope for the same scripts.
set -eu
export PATH=/data/data/com.termux/files/usr/bin
export PYTHONDONTWRITEBYTECODE=1 F8_HYBRID2_NATIVE=1
unset F8_HYBRID2_BUDGET_DIR F8_NO_HYBRID
run=${0%/*}
grep -E '^(Uid|TracerPid):' /proc/self/status
(cd "$run/scripts" && sha256sum -c --quiet ../scripts.sha256)
F8_HYBRID2_TRUSTED_GIT_ROOTS='["/fixture"]' python3 -B "$run/scripts/stage75_envelope.py" "$run/ws2" "$PATH/git" "$run/r" > "$run/envelope-native.json"
python3 -B "$run/scripts/test_f8_hybrid2.py" > "$run/native-suite.log" 2>&1
EOF
chmod 700 "$run/run-daemon" "$run/run-native"
printf '%s\n' "$run"
