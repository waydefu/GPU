#!/data/data/com.termux/files/usr/bin/bash
# apply-v8-fix2.sh (2026-09-26) — fixes found while checking the F8 widgets. Runs in Termux (or inside the desktop).
#  1. f8desk, f8desk-external: start shard-daemon.sh with `setsid -f`. Plain `setsid ... &` exec'd the daemon as a
#     child of f8desk's background subshell; that subshell then waited on the daemon forever, and the desktop's
#     proot (its parent) could never exit: the boot that started the daemon left its old tracer behind.
#  2. f8-mouse-external: find the wireless-debugging port with f8-adb-port (it was a fixed 127.0.0.1:37985, but the
#     port changes every time wireless debugging is turned on); connect like the other tools.
#  3. f8-fullscreen: pin the device (-s) after connecting, as f8-app-launcher does, and say why it stops.
#  4. f8-adb-port: print the first announced port that accepts a TCP connection (mDNS can still announce an old
#     port), and collect announcements a little longer.
#  5. Ends the old desktop tracer that (1) left behind: only the bash subshell of f8desk that is the daemon's parent,
#     and only when that subshell's parent is a proot with no tracees (exact pids, logged).
# Backups: <file>.bak-20260926-v8fix2. 1 takes effect at the next desktop start; 2-4 at once.
set -euo pipefail
BIN=/data/data/com.termux/files/usr/bin
BASE=/data/data/com.termux/files/usr/tmp/f8-shard
backup() { [ -e "$1.bak-20260926-v8fix2" ] && { echo "SKIP $1 (backup exists: already applied?)"; return 1; }; cp -p "$1" "$1.bak-20260926-v8fix2"; }

for f in "$BIN/f8desk" "$BIN/f8desk-external"; do
  backup "$f" || continue
  python3 - "$f" <<'EOF'
import sys
p = sys.argv[1]; s = open(p).read()
a = '''    [ -x "$PF/shard2/shard-daemon.sh" ] && setsid "$PF/shard2/shard-daemon.sh" > /dev/null 2>&1 < /dev/null &
'''
b = '''    # -f (fix 2): setsid always forks, so this shell does not end up waiting on the daemon (plain `setsid ... &`
    # left the desktop's proot waiting forever on that background subshell).
    [ -x "$PF/shard2/shard-daemon.sh" ] && setsid -f "$PF/shard2/shard-daemon.sh" > /dev/null 2>&1 < /dev/null
'''
assert s.count(a) == 1, p
open(p, 'w').write(s.replace(a, b)); print('patched', p)
EOF
  bash -n "$f"
done

f="$BIN/f8-mouse-external"
if backup "$f"; then
  python3 - "$f" <<'EOF'
import sys
p = sys.argv[1]; s = open(p).read()
a = '''DEVICE=127.0.0.1:37985
'''
b = '''# The wireless-debugging port changes every time it is turned on (this was a fixed 127.0.0.1:37985 before fix 2).
PORT=$(/data/data/com.termux/files/usr/bin/f8-adb-port 2>/dev/null) || {
    [ -x "$TOAST" ] && "$TOAST" "F8：找不到 Wireless ADB" >/dev/null 2>&1
    exit 1
}
DEVICE=127.0.0.1:$PORT
'''
c = '''"$ADB" connect "$DEVICE" >/dev/null 2>&1 || true
'''
d = '''fakeroot env ANDROID_NO_USE_FWMARK_CLIENT=1 "$ADB" connect "$DEVICE" >/dev/null 2>&1 || true
'''
assert s.count(a) == 1 and s.count(c) == 1, p
open(p, 'w').write(s.replace(a, b).replace(c, d)); print('patched', p)
EOF
  sh -n "$f"
fi

f="$BIN/f8-fullscreen"
if backup "$f"; then
  python3 - "$f" <<'EOF'
import sys
p = sys.argv[1]; s = open(p).read()
rep = [
('''PORT="$(f8-adb-port 2>/dev/null)" || exit 1
$ADB connect 127.0.0.1:"$PORT" >/dev/null 2>&1 || exit 1
''', '''say() { termux-toast "$1" >/dev/null 2>&1 || true; }
PORT="$(f8-adb-port 2>/dev/null)" || { say "F8：找不到 Wireless ADB"; exit 1; }
$ADB connect 127.0.0.1:"$PORT" >/dev/null 2>&1 || { say "F8：ADB 連線失敗"; exit 1; }
# with more than one adb device every unpinned call fails (fix 2; f8-app-launcher already pins)
ADB="$ADB -s 127.0.0.1:$PORT"
'''),
('''[ -n "$DISPLAY_ID" ] || exit 2
''', '''[ -n "$DISPLAY_ID" ] || { say "F8：沒有偵測到外接螢幕"; exit 2; }
'''),
('''[ -n "$COMPONENT" ] || exit 3
''', '''[ -n "$COMPONENT" ] || { say "F8：外接螢幕上沒有開著的 App"; exit 3; }
'''),
]
for a, b in rep:
    assert s.count(a) == 1, (p, a)
    s = s.replace(a, b)
open(p, 'w').write(s); print('patched', p)
EOF
  bash -n "$f"
fi

f="$BIN/f8-adb-port"
if backup "$f"; then
  python3 - "$f" <<'EOF'
import sys
p = sys.argv[1]; s = open(p).read()
a = '''while time.time() < deadline and not listener.found:
    time.sleep(0.2)
zc.close()
ports = sorted({port for _, port in listener.found})
if ports:
    print(ports[0])
    raise SystemExit(0)
raise SystemExit(1)
'''
b = '''while time.time() < deadline and not listener.found:
    time.sleep(0.2)
if listener.found:
    time.sleep(0.5)  # fix 2: let an old and the current announcement both arrive
zc.close()
ports = sorted({port for _, port in listener.found})
# fix 2: mDNS can still announce an old wireless-debugging port (2026-09-23); print the first one that accepts a
# TCP connection on this phone instead of the lowest one.
import socket
for port in ports:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            pass
    except OSError:
        continue
    print(port)
    raise SystemExit(0)
raise SystemExit(1)
'''
assert s.count(a) == 1, p
open(p, 'w').write(s.replace(a, b)); print('patched', p)
EOF
  python3 -m py_compile "$f" 2>/dev/null || python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$f"
fi

# 5. the old tracer left behind by the plain `setsid ... &`
dp=$(cat "$BASE/daemon.pid" 2>/dev/null || true)
if [ -n "$dp" ] && [ -d "/proc/$dp" ]; then
  pp=$(awk '/^PPid/{print $2}' "/proc/$dp/status")
  if [ -n "$pp" ] && tr '\0' ' ' < "/proc/$pp/cmdline" 2>/dev/null | grep -q '/bin/f8desk'; then
    gp=$(awk '/^PPid/{print $2}' "/proc/$pp/status")
    tracees=0
    for q in /proc/[0-9]*; do [ "$(awk '/^TracerPid/{print $2}' "$q/status" 2>/dev/null)" = "$gp" ] && tracees=$((tracees + 1)); done
    case "$(cat "/proc/$gp/comm" 2>/dev/null)" in proot*) isproot=1;; *) isproot=0;; esac
    if [ "$isproot" = 1 ] && [ "$tracees" = 0 ]; then
      echo "ending f8desk subshell pid=$pp ($(tr '\0' ' ' < "/proc/$pp/cmdline")) that holds old tracer pid=$gp (0 tracees)"
      kill -TERM "$pp"
      for i in 1 2 3 4 5 6 7 8 9 10; do sleep 0.3; [ -d "/proc/$gp" ] || break; done
      echo "old tracer $gp gone: $([ -d "/proc/$gp" ] && echo no || echo yes); daemon $dp alive: $([ -d "/proc/$dp" ] && echo yes || echo no)"
    else
      echo "daemon parent $pp is f8desk but its parent $gp is not an idle proot (proot=$isproot tracees=$tracees): left alone"
    fi
  else
    echo "daemon $dp is not held by an f8desk subshell: nothing to end"
  fi
fi
echo "APPLY_V8_FIX2_DONE"
