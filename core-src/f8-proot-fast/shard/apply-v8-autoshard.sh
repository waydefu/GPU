#!/bin/bash
# apply-v8-autoshard.sh — switch the daily desktop to automatic shards
# (GPU加速/evidence/session/proot/AUTO-SHARD-01-RESULT.md: AUTOSHARD_RULES_PASS, 2026-09-26).
# Run it INSIDE the desktop (an Ubuntu terminal). It
#  1. installs f8-shard v2 as /usr/local/bin/f8-shard (backup .bak-20260926-v1). The existing launcher blocks
#     (Cursor, Hermes, ChatGPT, hermes-chrome) keep working and start in ~0.1 s instead of ~1 s once the
#     daemon runs; proot-fast8 uses the same file for automatic shards;
#  2. puts proot-fast8 first in the PD_PROOT_BIN block of f8desk and f8desk-external and, when it is picked,
#     exports PROOT_F8_AUTOSHARD=1 (+ its log) and starts shard-daemon.sh (backups .bak-20260926-v8).
# Takes effect at the next desktop start (close "F8 工作站", open it again); nothing running now is touched.
# Revert: copy each .bak-20260926-* back, or "F8 設定" -> stock proot (it ignores the auto-shard variables).
set -euo pipefail
PF=/data/data/com.termux/files/home/build/proot-fast
S2=$PF/shard2
BIN=/data/data/com.termux/files/usr/bin
want() { [ "$(sha256sum "$1" | cut -d' ' -f1)" = "$2" ] || { echo "REFUSE: $1 is not the tested file"; exit 3; }; }
want "$PF/out8/bin/proot-fast8" 10121cc433473db826c75d84a703d989114cb3d2eff4baf7cfd0ebdc912bdbe5
want "$S2/f8-shard" 7158e011aa07db1c4b5031dd64b3e2529e6aace3c99445768bda830d96fa2e3d
want "$S2/shard-run.sh" 03a249873b4e29a04546d78ab96fbb1a4b4f04330f104c168dcbc9d490a35955
want "$S2/shard-daemon.sh" a07eae435c52fe7e11b40cf88cf72f65a8e2e9285100e65a5d3f72c40c05146c
[ -x "$PF/out8/libexec/loader" ] || { echo "REFUSE: no $PF/out8/libexec/loader"; exit 3; }
[ -d /usr/local/bin ] && [ -e /usr/local/bin/f8-shard ] || { echo "REFUSE: run this inside the desktop (no /usr/local/bin/f8-shard here)"; exit 3; }

# 1. f8-shard v2
[ -e /usr/local/bin/f8-shard.bak-20260926-v1 ] || cp -p /usr/local/bin/f8-shard /usr/local/bin/f8-shard.bak-20260926-v1
install -m 755 "$S2/f8-shard" /usr/local/bin/f8-shard
echo "installed f8-shard v2 (backup /usr/local/bin/f8-shard.bak-20260926-v1)"

# 2. f8desk, f8desk-external
for f in "$BIN/f8desk" "$BIN/f8desk-external"; do
  if [ -e "$f.bak-20260926-v8" ]; then echo "SKIP $f (backup already exists: already applied?)"; continue; fi
  cp -p "$f" "$f.bak-20260926-v8"
  python3 - "$f" <<'EOF'
import sys
p = sys.argv[1]; s = open(p).read()
a = '''    if [ -x "$PF/out7/bin/proot-fast7" ] && [ -x "$PF/out7/libexec/loader" ]; then
        export PD_PROOT_BIN="$PF/out7/bin/proot-fast7"
    elif'''
b = '''    if [ -x "$PF/out8/bin/proot-fast8" ] && [ -x "$PF/out8/libexec/loader" ]; then
        export PD_PROOT_BIN="$PF/out8/bin/proot-fast8"
    elif [ -x "$PF/out7/bin/proot-fast7" ] && [ -x "$PF/out7/libexec/loader" ]; then
        export PD_PROOT_BIN="$PF/out7/bin/proot-fast7"
    elif'''
c = '''        export PD_PROOT_BIN="$PF/out2/bin/proot-fast2"
    fi
fi
'''
d = c + '''# v8 (2026-09-26, GPU加速/evidence/session/proot/AUTO-SHARD-01-RESULT.md): v7 + automatic shards. An execve of an
# Electron/Chromium binary or of a terminal emulator gets a proot tracer of its own through f8-shard v2, with no
# launcher block. Only proot-fast8 reads PROOT_F8_AUTOSHARD (proot-distro passes PROOT_* on to proot);
# shard-daemon.sh (outside every tracer) makes a shard start in ~0.1 s. Revert: <this file>.bak-20260926-v8.
if [ "${PD_PROOT_BIN:-}" = "$PF/out8/bin/proot-fast8" ]; then
    export PROOT_F8_AUTOSHARD=1 PROOT_F8_AUTOSHARD_LOG=/data/data/com.termux/files/usr/tmp/f8-shard/autoshard.log
    mkdir -p /data/data/com.termux/files/usr/tmp/f8-shard
    [ -x "$PF/shard2/shard-daemon.sh" ] && setsid "$PF/shard2/shard-daemon.sh" > /dev/null 2>&1 < /dev/null &
fi
'''
e = '''# proot-distro honours PD_PROOT_BIN. Order: v7, else v6,'''
f = '''# proot-distro honours PD_PROOT_BIN. Order: v8, else v7, else v6,'''
assert s.count(a) == 1 and s.count(c) == 1 and s.count(e) == 1, p
open(p, 'w').write(s.replace(a, b).replace(c, d).replace(e, f))
print('patched', p)
EOF
  bash -n "$f"
  diff -u "$f.bak-20260926-v8" "$f" || true
done
echo "APPLY_V8_DONE — close \"F8 工作站\" and open it again to start the desktop on proot-fast8"
