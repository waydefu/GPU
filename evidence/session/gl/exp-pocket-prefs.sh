#!/bin/bash
# Pocket mode for the EXPERIMENTAL app only (com.waydefu.x11gpu) while a long bench runs with the
# phone in a bag. Never touches Stable com.termux.x11.
#   apply   save current values to $STATE, then: extra-key bar hidden (its ESC key would quit the
#           benchmark), swipe-down / back do nothing (a stray swipe would bring the bar back or pop the
#           soft keyboard), screen kept on without charging: "never" sets FLAG_KEEP_SCREEN_ON on the
#           experimental window while X is connected (MainActivity.applyScreenIdleTimeout); the system
#           10-min timeout and Stable are untouched. (User asked for this, 2026-09-24.)
#   restore write the saved values back, then delete $STATE.
#   show    print the four values.
# Prevention only: stray touches can still reach X, so the bench script also records the touchscreen
# and invalidates any segment that saw a touch.
set -euo pipefail
unset LD_LIBRARY_PATH LD_PRELOAD
AM=/system/bin/am
ACTION=com.termux.x11.CHANGE_PREFERENCE
PKG=com.waydefu.x11gpu
STATE=${STATE:-/root/projects/GPU加速/evidence/session/gl/exp-pocket-prefs.saved}
KEYS="showAdditionalKbd swipeDownAction backButtonAction screenIdleTimeout"

# </dev/null: am reads stdin; inside the restore loop it swallowed the rest of $STATE, so only the
# first key was restored (2026-09-24 first restore; corrected by hand, see exp-pocket-prefs.saved.NOTE)
bc() { "$AM" broadcast --user 0 --include-stopped-packages -a "$ACTION" -p "$PKG" "$@" </dev/null 2>&1; }
current() { bc -e list null | tr -d '\r' | sed -n "s/^.*\"$1\"=\"\([^\"]*\)\".*$/\1/p" | head -1; }
set_one() {   # key value
  local out; out=$(bc -e "$1" "$2")
  case "$out" in *"result=1"*|*"can not be set"*) echo "SET_FAILED $1=$2: $out" >&2; return 1;; esac
  [ "$(current "$1")" = "$2" ] || { echo "VERIFY_FAILED $1 is '$(current "$1")' want '$2'" >&2; return 1; }
  echo "set $1=$2"
}

case "${1:-}" in
  show) for k in $KEYS; do echo "$k=$(current "$k")"; done ;;
  apply)
    [ -e "$STATE" ] && { echo "REFUSE: $STATE exists (already applied?); restore first" >&2; exit 3; }
    for k in $KEYS; do v=$(current "$k"); [ -n "$v" ] || { echo "REFUSE: cannot read $k" >&2; exit 3; }; printf '%s\t%s\n' "$k" "$v"; done > "$STATE.tmp"
    mv "$STATE.tmp" "$STATE"; echo "saved -> $STATE"; cat "$STATE"
    set_one showAdditionalKbd false
    set_one swipeDownAction "no action"
    set_one backButtonAction "no action"
    set_one screenIdleTimeout "Never (keep screen on)" ;;
  restore)
    [ -f "$STATE" ] || { echo "REFUSE: no $STATE" >&2; exit 3; }
    while IFS=$'\t' read -r k v; do
      # the list query prints display names; the receiver accepts entries as well as values
      set_one "$k" "$v"
    done < "$STATE"
    rm -f "$STATE"; echo restored ;;
  *) echo "usage: $0 apply|restore|show" >&2; exit 2 ;;
esac
