#!/data/data/com.termux/files/usr/bin/bash
# apply-v8-fix1.sh — fix the first v8 apply (2026-09-26): the daily tracer came up as proot-fast8 but WITHOUT
# PROOT_F8_AUTOSHARD, because proot-distro hands proot only PROOT_NO_SECCOMP, PROOT_VERBOSE and PROOT_L2S_DIR
# (proot_distro/commands/login/__init__.py) and f8desk exported the switch itself. Now PD_PROOT_BIN points to the
# wrapper out8/auto/proot-fast8, which sets the switch and execs the real proot-fast8 (tested: a real
# `proot-distro login` through it gives a tracer with PROOT_F8_AUTOSHARD=1, comm "proot-fast8", and an
# Electron-looking exec in that session is sharded).
# Touches only f8desk and f8desk-external in Termux's bin, so it runs in Termux or inside the desktop.
# Backups: <file>.bak-20260926-v8fix1. Takes effect at the next desktop start (close "F8 工作站", open it again).
set -euo pipefail
PF=/data/data/com.termux/files/home/build/proot-fast
BIN=/data/data/com.termux/files/usr/bin
[ "$(sha256sum "$PF/out8/auto/proot-fast8" | cut -d' ' -f1)" = f1c211fd6571d29bd4cde93a2f13a49b0463c2e5b1e288e5f1dd27c27183e552 ] \
  || { echo "REFUSE: $PF/out8/auto/proot-fast8 is not the tested wrapper"; exit 3; }
for f in "$BIN/f8desk" "$BIN/f8desk-external"; do
  if [ -e "$f.bak-20260926-v8fix1" ]; then echo "SKIP $f (backup already exists: already applied?)"; continue; fi
  grep -q 'out8/bin/proot-fast8' "$f" || { echo "REFUSE: $f has no v8 block (run apply-v8-autoshard.sh first)"; exit 3; }
  cp -p "$f" "$f.bak-20260926-v8fix1"
  python3 - "$f" <<'EOF'
import sys
p = sys.argv[1]; s = open(p).read()
a = '''    if [ -x "$PF/out8/bin/proot-fast8" ] && [ -x "$PF/out8/libexec/loader" ]; then
        export PD_PROOT_BIN="$PF/out8/bin/proot-fast8"'''
b = '''    if [ -x "$PF/out8/auto/proot-fast8" ] && [ -x "$PF/out8/bin/proot-fast8" ] && [ -x "$PF/out8/libexec/loader" ]; then
        export PD_PROOT_BIN="$PF/out8/auto/proot-fast8"'''
c = '''# launcher block. Only proot-fast8 reads PROOT_F8_AUTOSHARD (proot-distro passes PROOT_* on to proot);
# shard-daemon.sh (outside every tracer) makes a shard start in ~0.1 s. Revert: <this file>.bak-20260926-v8.
if [ "${PD_PROOT_BIN:-}" = "$PF/out8/bin/proot-fast8" ]; then
    export PROOT_F8_AUTOSHARD=1 PROOT_F8_AUTOSHARD_LOG=/data/data/com.termux/files/usr/tmp/f8-shard/autoshard.log
    mkdir -p'''
d = '''# launcher block. The switch (PROOT_F8_AUTOSHARD=1 + log) is set by the wrapper out8/auto/proot-fast8: proot-distro
# hands proot only PROOT_NO_SECCOMP, PROOT_VERBOSE and PROOT_L2S_DIR, so an export here would never reach it
# (fix 1, 2026-09-26: the first v8 apply exported it here and the daily tracer came up without it).
# shard-daemon.sh (outside every tracer) makes a shard start in ~0.1 s. Revert: <this file>.bak-20260926-v8.
if [ "${PD_PROOT_BIN:-}" = "$PF/out8/auto/proot-fast8" ]; then
    mkdir -p'''
assert s.count(a) == 1 and s.count(c) == 1, p
open(p, 'w').write(s.replace(a, b).replace(c, d))
print('patched', p)
EOF
  bash -n "$f"
  diff -u "$f.bak-20260926-v8fix1" "$f" || true
done
echo "APPLY_V8_FIX1_DONE — close \"F8 工作站\" and open it again"
