#!/data/data/com.termux/files/usr/bin/sh
# termux-bg-run cannot pass arguments; this fixes the mode.
exec /data/data/com.termux/files/usr/bin/python3 "$(dirname "$0")/restart-stable-desktop.py" --dry-run
