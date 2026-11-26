#!/data/data/com.termux/files/usr/bin/bash
# rollback-to-fast8.sh — One-key verified rollback of out8/ back to the fast8 backup.
set -euo pipefail

MODE="dry-run"
CONFIRM_LIVE=0
PREFIX_DIR="/data/data/com.termux/files/usr"
PROOT_ROOT="/data/data/com.termux/files/home/build/proot-fast"
TARGET_OUT="${PROOT_ROOT}/out8"
BACKUP_ROOT="${PROOT_ROOT}/backups"
BACKUP_DIR=""
UBU_ROOTFS="${PREFIX_DIR}/var/lib/proot-distro/containers/ubuntu/rootfs"

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/release-files.sh"

usage() {
  cat <<'EOF'
Usage: rollback-to-fast8.sh [OPTIONS]
  --dry-run              Verify backup integrity & checksums without modifying target-out (default)
  --apply                Restore fast8 binaries into --target-out (requires --confirm-live)
  --confirm-live         Explicit acknowledgement before mutating target-out
  --target-out <dir>     Destination out8 directory (default: ~/build/proot-fast/out8)
  --backup-dir <dir>     Specific backup dir (default: read from LATEST_FAST8_BACKUP)
  --backup-root <dir>    Backup root dir (default: ~/build/proot-fast/backups)
  -h, --help             Show this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) MODE="dry-run"; shift ;;
    --apply) MODE="apply"; shift ;;
    --confirm-live) CONFIRM_LIVE=1; shift ;;
    --target-out) TARGET_OUT="$2"; shift 2 ;;
    --backup-dir) BACKUP_DIR="$2"; shift 2 ;;
    --backup-root) BACKUP_ROOT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 64 ;;
  esac
done

if [[ "$MODE" == apply ]]; then
  if [[ "$CONFIRM_LIVE" -ne 1 ]]; then
    echo "REFUSED: --apply requires --confirm-live" >&2
    exit 2
  fi
  exec {release_lock}<"$TARGET_OUT"
  flock -x "$release_lock"
fi

if [ -z "$BACKUP_DIR" ]; then
  [ -f "${BACKUP_ROOT}/LATEST_FAST8_BACKUP" ] || { echo "Missing ${BACKUP_ROOT}/LATEST_FAST8_BACKUP; specify --backup-dir" >&2; exit 3; }
  BACKUP_DIR=$(cat "${BACKUP_ROOT}/LATEST_FAST8_BACKUP")
fi

[ -d "$BACKUP_DIR" ] && [ -f "$BACKUP_DIR/backup.sha256" ] || { echo "Invalid backup dir: $BACKUP_DIR" >&2; exit 3; }
echo "=== ROLLBACK PREFLIGHT mode=$MODE backup=$BACKUP_DIR target=$TARGET_OUT ==="
verify_release_backup "$BACKUP_DIR"
if ! is_fast8 "$BACKUP_DIR"; then
  echo "REFUSED: backup binary is not 5.1.107.92-fast8" >&2
  exit 3
fi

if [ "$MODE" = "dry-run" ]; then
  echo "ROLLBACK_DRY_RUN_PASS: backup checksums verified; $TARGET_OUT untouched."
  echo "Note: Immediate per-session/desktop emergency toggles remain available without file swap:"
  echo "  F8_NO_SHARD=1 | PROOT_STAT_AT_ENTER=0 | touch ~/.f8-proot-stock"
  exit 0
fi

files=(bin/proot-fast8 libexec/loader deployed.sha256)
if [[ -f "$BACKUP_DIR/libexec/loader32" ]]; then
  files+=(libexec/loader32)
fi
if [[ -f "$BACKUP_DIR/auto/proot-fast8" && -d "$TARGET_OUT/auto" ]]; then
  files+=(auto/proot-fast8)
fi

txn=$(mktemp -d "$TARGET_OUT/.rollback.XXXXXXXX")
recover=""
trap 'finish_release_change "$?" "$txn" "$recover" "$TARGET_OUT" "${files[@]}"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

snapshot_release "$TARGET_OUT" "$txn/previous"
prepare_release_files "$BACKUP_DIR" "$txn/replacement" "${files[@]}"
recover="$txn/previous"
publish_release_files "$txn/replacement" "$TARGET_OUT" "${files[@]}"

echo "Post-rollback verification:"
verify_release_files "$BACKUP_DIR" "$TARGET_OUT" "${files[@]}"
is_fast8 "$TARGET_OUT"
if [[ -d "$UBU_ROOTFS" ]]; then
  PKG_CNT=$(exec {release_lock}<&-
    "$TARGET_OUT/bin/proot-fast8" -0 -l -r "$UBU_ROOTFS" -w / -b /proc -b /dev /usr/bin/env -i PATH=/usr/bin:/bin LC_ALL=C /bin/bash -o pipefail -c "dpkg-query -W | wc -l")
  [[ "${PKG_CNT:-0}" -gt 100 ]]
  echo "   post-rollback guest dpkg-query PASS (packages=$PKG_CNT)"
fi
recover=""
echo "ROLLBACK_PASS target=$TARGET_OUT restored_from=$BACKUP_DIR"
